import os
import sys
import json
import argparse
from uuid import UUID
from dotenv import load_dotenv
import chromadb
from chromadb.config import Settings
from chromadb.utils import embedding_functions
import asyncio
from sqlalchemy import select, Column, String, UUID as SQLAlchemyUUID
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker, declarative_base
from datetime import datetime

Base = declarative_base()

class User(Base):
    __tablename__ = "users"
    
    id = Column(SQLAlchemyUUID(as_uuid=True), primary_key=True)
    username = Column(String, unique=True, index=True)

def setup_env():
    """Load production environment variables."""
    env_path = '/etc/cyberiad/.env'
    if not os.path.exists(env_path):
        print(f"Error: Environment file not found at {env_path}")
        sys.exit(1)
    load_dotenv(env_path)

async def get_user_id(username: str) -> UUID:
    """Get user ID from username using database."""
    database_url = os.getenv('DATABASE_URL')
    if not database_url:
        print("Error: DATABASE_URL not found in environment")
        sys.exit(1)

    engine = create_async_engine(database_url)
    async_session = sessionmaker(
        engine, class_=AsyncSession, expire_on_commit=False
    )

    try:
        async with async_session() as session:
            result = await session.execute(
                select(User.id).where(User.username == username)
            )
            user_id = result.scalar_one_or_none()
            
            if not user_id:
                print(f"Error: No user found with username '{username}'")
                sys.exit(1)
                
            return user_id
            
    except Exception as e:
        print(f"Error querying database: {e}")
        sys.exit(1)
    finally:
        await engine.dispose()

def get_collection_name(owner_id: UUID) -> str:
    """Generate valid ChromaDB collection name."""
    owner_str = str(owner_id) if not isinstance(owner_id, str) else owner_id
    clean_owner = owner_str.replace('-', '')
    return f"o{clean_owner}"[:63]

def init_chroma():
    """Initialize ChromaDB with production settings."""
    chroma_dir = '/etc/cyberiad/data/chroma_db'
    if not os.path.exists(chroma_dir):
        print(f"Error: ChromaDB directory not found at {chroma_dir}")
        sys.exit(1)

    try:
        openai_ef = embedding_functions.OpenAIEmbeddingFunction(
            api_key=os.getenv('OPENAI_API_KEY'),
            model_name="text-embedding-ada-002"
        )

        client = chromadb.PersistentClient(
            path=chroma_dir,
            settings=Settings(
                anonymized_telemetry=False,
                allow_reset=True
            )
        )
        return client, openai_ef
    except Exception as e:
        print(f"Error initializing ChromaDB: {e}")
        sys.exit(1)

def query_rag(client, ef, owner_id: UUID, query_text: str, limit: int = 5):
    """Query the RAG system and return results."""
    try:
        collection_name = get_collection_name(owner_id)
        print(f"Querying collection: {collection_name}")
        
        collection = client.get_collection(
            name=collection_name,
            embedding_function=ef
        )
        where_clause = {
           "$and": [
                {"source_type": "document"},
                {"owner_id": str(owner_id)}
            ]
        }
        claws = {"source_type": "document"}
        results = collection.query(
            query_texts=[query_text],
            n_results=limit,
            where=claws,
            include=["documents", "metadatas", "distances"]
        )

        return results

    except Exception as e:
        print(f"Error querying RAG: {e}")
        return None

async def main():
    parser = argparse.ArgumentParser(description='Test RAG retrieval in production')
    parser.add_argument('username', help='Username of the owner to query')
    parser.add_argument('query', help='Query text to search for')
    parser.add_argument('--limit', type=int, default=5, help='Number of results to return')
    args = parser.parse_args()

    # Setup and initialize
    setup_env()
    client, ef = init_chroma()

    # Get owner_id from username
    owner_id = await get_user_id(args.username)
    print(f"\nFound user ID: {owner_id} for username: {args.username}")

    # Query RAG
    results = query_rag(client, ef, owner_id, args.query, args.limit)
    
    if not results:
        print("No results found or error occurred")
        sys.exit(1)

    # Print results
    print("\nRAG Query Results:")
    print(f"Query: '{args.query}'")
    print(f"Username: {args.username}")
    print(f"Owner ID: {owner_id}")
    print("\nFound Documents:")
    
    for idx, (doc, meta, dist) in enumerate(zip(
        results['documents'][0],
        results['metadatas'][0],
        results['distances'][0]
    )):
        print(f"\n--- Result {idx + 1} ---")
        print(f"Distance Score: {dist:.4f}")
        print("\nMetadata:")
        print(json.dumps(meta, indent=2))
        print("\nContent Preview:")
        print(doc[:500] + "..." if len(doc) > 500 else doc)
        print("\n" + "-"*50)

if __name__ == "__main__":
    asyncio.run(main())
