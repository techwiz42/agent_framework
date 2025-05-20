import asyncio
import logging
import os
from pathlib import Path
from uuid import UUID
import chromadb
from chromadb.config import Settings
from chromadb.utils import embedding_functions
from dotenv import load_dotenv

# Load environment variables

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def get_chroma_client():
    """Initialize ChromaDB client matching application configuration."""
    chroma_persist_dir = '/etc/cyberiad/data/chroma_db'
    if not chroma_persist_dir:
        raise ValueError("CHROMA_PERSIST_DIR not found in environment variables")
        
    logger.info(f"Initializing ChromaDB with persist_dir: {chroma_persist_dir}")
    
    client = chromadb.PersistentClient(
        path=chroma_persist_dir,
        settings=Settings(
            anonymized_telemetry=False,
            allow_reset=True
        )
    )
    
    return client

async def inspect_collections(owner_id: UUID = None):
    """Inspect ChromaDB collections and their contents."""
    try:
        client = get_chroma_client()
        embedding_function = embedding_functions.OpenAIEmbeddingFunction(
            api_key='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',
            model_name="text-embedding-3-large"
        )

        # Try direct database inspection
        logger.info(f"ChromaDB persist directory content:")
        for root, dirs, files in os.walk('/etc/cyberiad/data/chroma_db'):
            logger.info(f"\nDirectory: {root}")
            for f in files:
                full_path = os.path.join(root, f)
                size = os.path.getsize(full_path)
                logger.info(f"File: {f} - Size: {size} bytes")

        # Get collection names (new API)
        collection_names = client.list_collections()
        logger.info(f"\nFound {len(collection_names)} collections:")
        
        for collection_name in collection_names:
            try:
                logger.info(f"\nInspecting collection: {collection_name}")
                
                # Get collection instance
                collection = client.get_collection(
                    name=collection_name,
                    embedding_function=embedding_function
                )
                
                count = collection.count()
                logger.info(f"Document count: {count}")
                
                if count > 0:
                    # Get a sample of documents
                    sample = collection.get(
                        limit=3,
                        include=['documents', 'metadatas']
                    )
                    
                    logger.info("\nSample documents:")
                    for i, (doc, meta) in enumerate(zip(sample['documents'], sample['metadatas'])):
                        logger.info(f"\nDocument {i + 1}:")
                        logger.info(f"Metadata: {meta}")
                        logger.info(f"Content preview: {doc[:200]}...")

                    # Try a basic query without any filters
                    logger.info("\nTesting basic query without filters...")
                    query_result = collection.query(
                        query_texts=["test query"],
                        n_results=1,
                        include=['documents', 'metadatas', 'distances']
                    )
                    
                    if query_result['documents'][0]:
                        logger.info("Query successful - collection is queryable")
                        logger.info(f"Query metadata: {query_result['metadatas'][0][0]}")
                    else:
                        logger.warning("Query returned no results")
                        
            except Exception as e:
                logger.error(f"Error inspecting collection {collection_name}: {e}")
                continue

        # If looking for specific owner and no collections found, try direct access
        if owner_id and len(collection_names) == 0:
            collection_name = f"o{str(owner_id).replace('-', '')}"[:63]
            try:
                logger.info(f"\nAttempting direct access to collection: {collection_name}")
                collection = client.get_collection(
                    name=collection_name,
                    embedding_function=embedding_function
                )
                count = collection.count()
                logger.info(f"Successfully accessed collection. Count: {count}")
            except Exception as e:
                logger.error(f"Error accessing collection directly: {e}")

    except Exception as e:
        logger.error(f"Error during collection inspection: {e}")
        raise

if __name__ == "__main__":
    asyncio.run(inspect_collections('a58364743834408380379464be334af9'))
