import pytest
import chromadb
from uuid import UUID
from app.services.rag.storage_service import RAGStorageService
from chromadb.utils import embedding_functions

@pytest.fixture
def storage_service():
    service = RAGStorageService()
    service.client = chromadb.PersistentClient(path="./test_data/")
    service.openai_ef = embedding_functions.DefaultEmbeddingFunction()
    return service

@pytest.mark.asyncio
async def test_text_splitting_and_embedding(storage_service):
    thread_id = UUID("12345678-1234-5678-1234-567812345678")
    owner_id = UUID("87654321-4321-8765-4321-876543210987")
    
    long_text = "test content " * 100  # Long enough to force chunking
    metadata = {"source": "test_doc"}
    
    chunk_ids = await storage_service.add_texts(
        thread_id=thread_id,
        owner_id=owner_id,
        texts=[long_text],
        metadatas=[metadata]
    )
    
    print(f"Generated chunk IDs: {chunk_ids}")
    
    collection = await storage_service.get_collection(thread_id, owner_id)
    result = collection.get(ids=chunk_ids)
    
    print(f"Retrieved chunks: {result['documents']}")
    
    assert len(result['documents']) > 1
    for chunk in result['documents']:
        assert isinstance(chunk, str)
        assert len(chunk.strip()) > 0

@pytest.mark.asyncio
async def test_semantic_search(storage_service):
    thread_id = UUID("12345678-1234-5678-1234-567812345678")
    owner_id = UUID("87654321-4321-8765-4321-876543210987")
    
    texts = [
        "The cat sat on the mat",
        "Python programming",
        "Weather patterns"
    ]
    
    await storage_service.add_texts(
        thread_id=thread_id,
        owner_id=owner_id,
        texts=texts,
        metadatas=[{"index": i} for i in range(len(texts))]
    )
    
    results = await storage_service.query_collection(
        thread_id=thread_id,
        owner_id=owner_id,
        query_text="feline pets",
        n_results=1
    )
    
    print(f"Query results: {results}")
    
    assert len(results['documents']) > 0
    assert any("cat" in doc.lower() for doc in results['documents'])

@pytest.mark.asyncio
async def test_cross_collection_isolation(storage_service):
    thread1_id = UUID("12345678-1234-5678-1234-567812345678")
    thread2_id = UUID("87654321-4321-8765-4321-876543210987")
    owner_id = UUID("11111111-2222-3333-4444-555555555555")
    
    await storage_service.add_texts(
        thread_id=thread1_id,
        owner_id=owner_id,
        texts=["Collection one text"]
    )
    
    await storage_service.add_texts(
        thread_id=thread2_id,
        owner_id=owner_id,
        texts=["Collection two text"]
    )
    
    results1 = await storage_service.query_collection(
        thread_id=thread1_id,
        owner_id=owner_id,
        query_text="one",
        n_results=1
    )
    
    results2 = await storage_service.query_collection(
        thread_id=thread2_id,
        owner_id=owner_id,
        query_text="two",
        n_results=1
    )
    
    print(f"Thread 1 query results: {results1}")
    print(f"Thread 2 query results: {results2}")
    
    assert len(results1['documents']) > 0
    assert len(results2['documents']) > 0
    assert "one" in results1['documents'][0].lower()
    assert "two" in results2['documents'][0].lower()

@pytest.mark.asyncio
async def test_conversation_context(storage_service):
    thread_id = UUID("12345678-1234-5678-1234-567812345678")
    owner_id = UUID("87654321-4321-8765-4321-876543210987")
    
    conversation = [
        "User: The weather is nice",
        "Assistant: Yes, it's sunny today",
        "User: Will it rain?",
        "Assistant: No rain forecast"
    ]
    
    await storage_service.add_texts(
        thread_id=thread_id,
        owner_id=owner_id,
        texts=conversation,
        metadatas=[{"type": "message"} for _ in conversation]
    )
    
    results = await storage_service.query_collection(
        thread_id=thread_id,
        owner_id=owner_id,
        query_text="What about rain?",
        n_results=2
    )
    
    print(f"Conversation query results: {results}")
    
    assert len(results['documents']) > 0
    assert any("rain" in text.lower() for text in results['documents'])
