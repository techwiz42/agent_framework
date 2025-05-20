import pytest
from uuid import UUID
from pathlib import Path
from app.services.rag.ingestion_service import DataIngestionManager
from app.services.rag.storage_service import RAGStorageService
from fastapi import UploadFile
from sqlalchemy import select
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from app.core.config import settings
from app.models.domain.models import Message, Thread, ThreadParticipant, User, Base
from chromadb.utils import embedding_functions

@pytest.fixture
def storage_service():
    service = RAGStorageService()
    service.client.reset()
    service.openai_ef = embedding_functions.DefaultEmbeddingFunction()
    return service

@pytest.fixture
async def db_session():
    engine = create_async_engine(settings.TEST_DATABASE_URL)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    async with async_session() as session:
        yield session

@pytest.fixture
async def test_user(db_session):
    user = User(
        id=UUID("87654321-4321-8765-4321-876543210987"), 
        email="test@example.com",
        hashed_password="test"
    )
    db_session.add(user)
    await db_session.commit()
    return user

@pytest.fixture
async def test_thread(db_session, test_user):
    thread = Thread(
        id=UUID("12345678-1234-5678-1234-567812345678"),
        title="Test Thread",
        owner_id=test_user.id
    )
    db_session.add(thread)
    await db_session.commit()
    return thread

@pytest.fixture
async def db_session():
    engine = create_async_engine(settings.TEST_DATABASE_URL)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)
    
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    async with async_session() as session:
        yield session

@pytest.fixture
def storage_service():
    service = RAGStorageService()
    service.client.reset()
    service.openai_ef = embedding_functions.DefaultEmbeddingFunction()
    return service

@pytest.mark.asyncio
async def test_ingest_conversation_history(
        db_session,
        batch_size: int = 100
    ):
        """Ingest historical conversation messages into RAG."""
        try:
            thread_id = UUID("12345678-1234-5678-1234-567812345678")
            # Get conversation messages
            messages = await db_session.execute(
                select(Message)
                .where(Message.thread_id == thread_id)
                .order_by(Message.created_at.asc())
            )
            messages = messages.scalars().all()
            
            # Process messages in batches
            for i in range(0, len(messages), batch_size):
                batch = messages[i:i + batch_size]
                
                # Format messages with metadata
                formatted_texts = []
                for msg in batch:
                    # Validate agent_id
                    if msg.agent_id:
                        agent_exists = await db.execute(
                            select(ThreadAgent.id).where(ThreadAgent.id == msg.agent_id)
                        )
                        if not agent_exists.scalars().first():
                            raise ValueError(f"Agent {msg.agent_id} does not exist.")

                        sender = f"[{msg.message_metadata.get('agent_type', 'AGENT')}]"
                    else:
                        sender = f"[{msg.message_metadata.get('participant_name', 'USER')}]"
                    
                    formatted_texts.append({
                        'content': f"{sender}: {msg.content}",
                        'metadata': {
                            'message_id': str(msg.id),
                            'created_at': msg.created_at.isoformat(),
                            'source': 'conversation_history'
                        }
                    })
                
                # Add to vector store
                await self.rag_service.add_texts(
                    thread_id=thread_id,
                    texts=[t['content'] for t in formatted_texts],
                    metadatas=[t['metadata'] for t in formatted_texts]
                )
            
        except Exception as e:
            raise


@pytest.mark.asyncio
async def test_ingest_document(storage_service, db_session):
    # Create user and thread first
    user = User(
        id=UUID("87654321-4321-8765-4321-876543210987"),
        email="test@example.com",
        hashed_password="test"
    )
    db_session.add(user)
    await db_session.commit()

    thread = Thread(
        id=UUID("12345678-1234-5678-1234-567812345678"),
        title="Test Thread",
        owner_id=user.id
    )
    db_session.add(thread)
    await db_session.commit()

    test_file_path = Path("test_doc.txt")
    test_file_path.write_text("Test document content for RAG ingestion system.")
    
    try:
        with open(test_file_path, 'rb') as f:
            file = UploadFile(filename="test_doc.txt", file=f)
            ingestion_manager = DataIngestionManager(storage_service)
            result = await ingestion_manager.ingest_document(
                db=db_session,
                thread_id=thread.id,
                file=file
            )

        assert result['chunk_count'] > 0
        
        query_result = await storage_service.query_collection(
            thread_id=thread.id,
            owner_id=user.id,
            query_text="test document",
            n_results=1
        )
        assert len(query_result['documents']) > 0
        assert "test document" in query_result['documents'][0].lower()
    finally:
        test_file_path.unlink()

@pytest.mark.asyncio
async def test_ingest_urls(storage_service, db_session, test_thread):
    thread_id = test_thread.id

    import nltk
    nltk.download('punkt_tab')
    
    urls = ["https://example.com"]
    ingestion_manager = DataIngestionManager(storage_service)
    result = await ingestion_manager.ingest_urls(
        db=db_session,
        thread_id=thread_id,
        urls=urls
    )
    
    assert result['document_count'] >= 0
