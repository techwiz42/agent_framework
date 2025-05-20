from typing import List, Dict, Any, Optional
from uuid import UUID
import logging
import traceback
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from langchain_openai import OpenAIEmbeddings, ChatOpenAI
import chromadb
from chromadb.config import Settings
from chromadb.utils import embedding_functions
from openai import BadRequestError
from app.core.config import settings
from app.models.domain.models import Thread

logger = logging.getLogger(__name__)

# Define consistent ChromaDB settings
CHROMA_SETTINGS = Settings(
    anonymized_telemetry=False,
    allow_reset=True,
    is_persistent=True
)

class RAGQueryService:
    _instance = None
    _client = None
    
    # Constants for text chunking
    MAX_TOKENS = 8000  # Keep below OpenAI's 8192 limit
    CHARS_PER_TOKEN = 4  # Conservative estimate
    MAX_CHUNK_SIZE = MAX_TOKENS * CHARS_PER_TOKEN  # ~32000 chars
    OVERLAP_SIZE = 500  # Overlap between chunks to maintain context
    
    # Token estimation constants
    SPECIAL_TOKENS = {
        " ": 0.3,  # Spaces often combine with next token
        "\n": 1.0, # Newlines are usually separate tokens
        "\\": 1.0, # Escapes are usually separate tokens
        ",": 0.3,  # Punctuation often combines
        ".": 0.3,
        "!": 0.3,
        "?": 0.3
    }

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(RAGQueryService, cls).__new__(cls)
        return cls._instance

    def __init__(self):
        if not hasattr(self, 'initialized'):
            self._initialize_components()
            self.initialized = True

    def _initialize_components(self):
        """Initialize RAG components."""
        try:
            # Initialize embeddings and LLM
            self.embeddings = OpenAIEmbeddings(
                openai_api_key=settings.OPENAI_API_KEY,
                model="text-embedding-3-large"
            )
            
            self.llm = ChatOpenAI(
                model_name="gpt-4-turbo-preview",
                temperature=0,
                openai_api_key=settings.OPENAI_API_KEY
            )

            # Initialize ChromaDB client (singleton)
            if RAGQueryService._client is None:
                RAGQueryService._client = self._initialize_chroma_client()

            logger.info("RAG components initialized successfully")
            
        except Exception as e:
            logger.error(f"Error initializing RAG components: {e}")
            logger.error(traceback.format_exc())
            raise

    def _estimate_tokens(self, text: str) -> int:
        """Estimate the number of tokens in a text string.
        This is a simple estimation - actual tokens may vary but this helps prevent hitting limits."""
        # Base estimate: 1 token per 4 characters on average
        estimated_tokens = len(text) / self.CHARS_PER_TOKEN
        
        # Adjust for special tokens
        for char, weight in self.SPECIAL_TOKENS.items():
            estimated_tokens += text.count(char) * weight
            
        return int(estimated_tokens)

    def _chunk_text(self, text: str) -> List[str]:
        """Split text into overlapping chunks based on estimated token count."""
        chunks = []
        start = 0
        text_length = len(text)

        while start < text_length:
            # Calculate end position for current chunk
            end = start + self.MAX_CHUNK_SIZE
            
            # If this isn't the last chunk, try to break at a sentence or paragraph
            if end < text_length:
                # Look for natural break points
                break_points = [
                    text.rfind('\n\n', start, end),  # Paragraph break
                    text.rfind('. ', start, end),    # Sentence break
                    text.rfind('? ', start, end),    # Question mark
                    text.rfind('! ', start, end),    # Exclamation mark
                    text.rfind('\n', start, end),    # Line break
                    text.rfind(' ', start, end)      # Word break
                ]
                
                # Use the first valid break point found
                for point in break_points:
                    if point != -1:
                        end = point + 1
                        break

            # Add the chunk
            chunks.append(text[start:end].strip())
            
            # Move start position back by overlap size unless this is the last chunk
            start = end - self.OVERLAP_SIZE if end < text_length else end

        return chunks

    async def query_knowledge(
        self,
        owner_id: UUID,
        query_text: str,
        thread_id: Optional[UUID] = None,
        k: int = 30
    ) -> Dict[str, Any]:
        """Query the RAG system with proactive token management."""
        try:
            # Debug logging
            logger.info(f"RAG Query: owner_id={owner_id}, query='{query_text[:50]}...', thread_id={thread_id}")

            # Ensure we have a valid client
            if not self._client:
                self._client = self._initialize_chroma_client()
                logger.info("Initialized ChromaDB client")

            # Get collection for owner
            collection = self._get_collection(owner_id)
            logger.info(f"Got collection for owner {owner_id}")

            # Log collection count
            count = collection.count()
            logger.info(f"Collection has {count} documents")

            # Estimate tokens in query text
            estimated_tokens = self._estimate_tokens(query_text)
            logger.info(f"Estimated tokens: {estimated_tokens}")

            if estimated_tokens > self.MAX_TOKENS:
                logger.info(f"Query text estimated at {estimated_tokens} tokens, splitting into chunks")
                # Proactively split into chunks
                chunks = self._chunk_text(query_text)
                all_results = {"documents": [], "metadatas": [], "distances": []}

                # Only filter by document type, not thread_id
                where_clause = {"source_type": "document"}
                logger.info(f"Using where clause: {where_clause}")

                for chunk in chunks:
                    logger.info(f"Querying chunk: '{chunk[:30]}...'")
                    chunk_results = collection.query(
                        query_texts=[chunk],
                        n_results=k // len(chunks),  # Distribute k across chunks
                        where=where_clause,
                        include=["documents", "metadatas", "distances"]
                    )
                    logger.info(f"Chunk results: {len(chunk_results.get('documents', []))} documents")
                    all_results["documents"].extend(chunk_results["documents"])
                    all_results["metadatas"].extend(chunk_results["metadatas"])
                    all_results["distances"].extend(chunk_results["distances"])

                results = all_results
            else:
                # Query with full text if under token limit
                # Only filter by document type, not thread_id
                where_clause = {"source_type": "document"}
                logger.info(f"Using where clause: {where_clause}")

                logger.info(f"Querying with full text: '{query_text[:50]}...'")
                results = collection.query(
                    query_texts=[query_text],
                    n_results=k,
                    where=where_clause,
                    include=["documents", "metadatas", "distances"]
                )
                logger.info(f"Query raw results: {len(results.get('documents', []))} documents")

            # Filter for unique results
            unique_results = self._filter_unique_results(results)

            logger.info(f"Query successful: {len(unique_results['documents'])} unique results found")
            return unique_results

        except Exception as e:
            logger.error(f"Error in query_knowledge: {e}")
            logger.error(traceback.format_exc())
            # Return empty results instead of raising
            return {
                "documents": [],
                "metadatas": [],
                "distances": []
            }

    def _initialize_chroma_client(self) -> chromadb.PersistentClient:
        """Initialize ChromaDB client with consistent settings."""
        try:
            # Use class-level singleton pattern for client
            if RAGQueryService._client is not None:
                return RAGQueryService._client

            logger.info(f"Initializing ChromaDB client at {settings.CHROMA_PERSIST_DIR}")
            
            # Create new client with consistent settings
            client = chromadb.PersistentClient(
                path=settings.CHROMA_PERSIST_DIR,
                settings=CHROMA_SETTINGS
            )

            logger.info("ChromaDB client initialized successfully")
            return client

        except ValueError as ve:
            if "already exists" in str(ve):
                logger.warning("Attempting to reuse existing ChromaDB instance")
                # Try to connect to existing instance
                try:
                    client = chromadb.PersistentClient(
                        path=settings.CHROMA_PERSIST_DIR,
                        settings=CHROMA_SETTINGS
                    )
                    return client
                except Exception as e:
                    logger.error(f"Failed to connect to existing ChromaDB instance: {e}")
                    raise
            raise
        except Exception as e:
            logger.error(f"Error initializing ChromaDB client: {e}")
            raise

    def _get_collection(self, owner_id: UUID):
        """Get or create collection for owner with error handling."""
        try:
            collection_name = f"o{str(owner_id).replace('-', '')}"[:63]
            logger.info(f"Getting collection '{collection_name}' for owner {owner_id}")
            embedding_function = self._create_embedding_function()

            # Get existing collection or create new one
            try:
                logger.info(f"Attempting to get existing collection '{collection_name}'")
                collection = self._client.get_collection(
                    name=collection_name,
                    embedding_function=embedding_function
                )
                logger.info(f"Retrieved existing collection '{collection_name}'")
            except (ValueError, chromadb.errors.InvalidCollectionException) as e:
                # Collection doesn't exist, create it
                logger.info(f"Collection '{collection_name}' not found: {str(e)}")
                logger.info(f"Creating new collection '{collection_name}'")
                collection = self._client.create_collection(
                    name=collection_name,
                    embedding_function=embedding_function
                )
                logger.info(f"Created new collection '{collection_name}'")

            # Log the collection metadata and count
            try:
                count = collection.count()
                metadata = collection.metadata
                logger.info(f"Collection '{collection_name}' has {count} documents and metadata: {metadata}")
            except Exception as e:
                logger.warning(f"Error getting collection stats: {e}")

            return collection

        except Exception as e:
            logger.error(f"Error getting collection for owner {owner_id}: {e}")
            logger.error(traceback.format_exc())
            raise

    def _create_embedding_function(self):
        """Create OpenAI embedding function with retry logic."""
        return embedding_functions.OpenAIEmbeddingFunction(
            api_key=settings.OPENAI_API_KEY,
            model_name="text-embedding-3-large"
        )

    def _filter_unique_results(self, results: Dict[str, Any]) -> Dict[str, Any]:
        """Filter for unique documents while maintaining relevance order."""
        unique_docs = []
        unique_metadatas = []
        unique_distances = []
        seen_doc_ids = set()

        for doc, meta, dist in zip(
            results["documents"],
            results["metadatas"],
            results["distances"]
        ):
            # Ensure we're working with lists
            docs = doc if isinstance(doc, list) else [doc]
            metas = meta if isinstance(meta, list) else [meta]
            dists = dist if isinstance(dist, list) else [dist]
            
            for doc_item, meta_item, dist_item in zip(docs, metas, dists):
                doc_id = meta_item.get('document_id')
                if doc_id and doc_id not in seen_doc_ids:
                    seen_doc_ids.add(doc_id)
                    unique_docs.append(doc_item)
                    unique_metadatas.append(meta_item)
                    unique_distances.append(dist_item)

        return {
            "documents": unique_docs,
            "metadatas": unique_metadatas,
            "distances": unique_distances
        }

# Create singleton instance
rag_query_service = RAGQueryService()
