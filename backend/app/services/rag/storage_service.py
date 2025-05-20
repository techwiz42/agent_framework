from typing import List, Dict, Any, Optional, Union
from uuid import UUID, uuid4
import logging
from datetime import datetime
import os
import humanize
from langchain_openai import OpenAIEmbeddings
from langchain.text_splitter import RecursiveCharacterTextSplitter
import chromadb
from chromadb.utils import embedding_functions
from chromadb.config import Settings
from sqlalchemy.ext.asyncio import AsyncSession
import traceback
from app.core.config import settings

logger = logging.getLogger(__name__)

# Default values if not in settings
DEFAULT_CHUNK_SIZE = 500
DEFAULT_CHUNK_OVERLAP = 75  # Must be less than chunk size

class RAGStorageService:
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(RAGStorageService, cls).__new__(cls)
        return cls._instance
        
    def __init__(self):
        if not hasattr(self, 'initialized'):
            self._initialize_components()
            self.initialized = True

    def _initialize_components(self):
        """Initialize RAG components with new ChromaDB client."""
        logger.info("Initializing ChromaDB client...")
        try:
            chunk_size = int(getattr(settings, 'RAG_CHUNK_SIZE', DEFAULT_CHUNK_SIZE))
            chunk_overlap = int(getattr(settings, 'RAG_CHUNK_OVERLAP', DEFAULT_CHUNK_OVERLAP))
    
            if chunk_overlap >= chunk_size:
                logger.warning(
                    f"Chunk overlap ({chunk_overlap}) must be less than chunk size ({chunk_size}). "
                    f"Setting overlap to {chunk_size // 4}"
                )
                chunk_overlap = chunk_size // 4

            self.openai_ef = embedding_functions.OpenAIEmbeddingFunction(
                api_key=settings.OPENAI_API_KEY,
                model_name="text-embedding-3-large"
            )
    
            self.client = chromadb.PersistentClient(
                path=settings.CHROMA_PERSIST_DIR,
                settings=Settings(
                    anonymized_telemetry=False,
                    allow_reset=True
                )
            )
    
            self.text_splitter = RecursiveCharacterTextSplitter(
                chunk_size=chunk_size,
                chunk_overlap=chunk_overlap,
                length_function=len,
                separators=["\n\n", "\n", " ", ""]
            )
      
            logger.info(
                f"Initialized RAG storage service with chunk_size={chunk_size}, "
                f"chunk_overlap={chunk_overlap}"
            )
        except Exception as e:
            logger.error(f"ChromaDB init failed: {e}", exc_info=True)
            traceback.print_exc()

    def _get_collection_name(self, owner_id: UUID) -> str:
        """Generate valid ChromaDB collection name."""
        # Ensure we have string representation
        owner_str = str(owner_id) if not isinstance(owner_id, str) else owner_id

        # Clean the ID
        clean_owner = owner_str.replace('-', '')

        # Create collection name - now using owner ID only
        name = f"o{clean_owner}"

        # Ensure length constraint
        collection_name = name[:63]

        # Debug log the collection name
        logger.info(f"Using collection name '{collection_name}' for owner_id '{owner_id}'")

        return collection_name

    def _calculate_directory_size(self, directory: str) -> int:
        """Calculate total size of a directory in bytes."""
        total_size = 0
        for dirpath, dirnames, filenames in os.walk(directory):
            for filename in filenames:
                filepath = os.path.join(dirpath, filename)
                try:
                    total_size += os.path.getsize(filepath)
                except (OSError, IOError) as e:
                    logger.error(f"Error getting size of {filepath}: {e}")
        return total_size

    async def initialize_collection(
        self,
        owner_id: UUID
    ) -> Any:
        """Create or get collection for owner."""
        try:
            collection_name = self._get_collection_name(owner_id)
            collection = self.client.get_or_create_collection(
                name=collection_name,
                embedding_function=self.openai_ef,
                metadata={"owner_id": str(owner_id)}
            )
            logger.info(f"Initialized collection for owner {owner_id}")
            return collection
        except Exception as e:
            traceback.print_exc()
            logger.error(f"Error initializing collection: {e}")
            raise

    async def get_collection(
        self,
        owner_id: Any,  # Allow any type for owner_id
        create_if_missing: bool = True
    ) -> Any:
        """Get owner's collection with optional creation."""
        try:
            # Handle case where owner_id is a SQLAlchemy session
            if hasattr(owner_id, 'execute'):
                logger.warning(f"Owner ID was incorrectly passed a database session")
                return None
        
            collection_name = self._get_collection_name(owner_id)

            if create_if_missing:
                collection = self.client.get_or_create_collection(
                    name=collection_name,
                    embedding_function=self.openai_ef,
                    metadata={"owner_id": str(owner_id)}
                )
            else:
                collection = self.client.get_collection(
                    name=collection_name,
                    embedding_function=self.openai_ef
                )
            return collection
        
        except Exception as e:
            logger.error(f"Error getting collection: {e}")
            if not create_if_missing:
                return None
            raise

    async def add_texts(
        self,
        owner_id: Union[UUID, str],
        texts: List[str],
        metadatas: Optional[List[Dict[str, Any]]] = None,
        thread_id: Optional[UUID] = None,
        file_contents: Optional[List[bytes]] = None
    ) -> List[str]:
        """
        Add texts to ChromaDB collection with optional document processing.
        """
        logger.info(f"Adding texts for owner={owner_id}, thread={thread_id}, count={len(texts)}")
        try:
            # Lazily import document processing service to avoid circular import
            from app.services.document_processing_service import document_processing_service
        
            # Ensure owner_id is UUID
            if isinstance(owner_id, str):
                owner_id = UUID(owner_id)
        
            # Prepare metadata and process documents if file contents are provided
            if file_contents:
                processed_documents = []
                processed_metadatas = []
            
                for idx, (text, metadata, file_content) in enumerate(
                    zip(
                        texts, 
                        metadatas or [{}] * len(texts), 
                        file_contents
                    )
                ):
                    # If file content is provided, use document processing service
                    if file_content:
                        processing_result = await document_processing_service.process_document(
                            file_content=file_content,
                            file_metadata=metadata,
                            owner_id=owner_id
                        )
                    
                        if processing_result['status'] == 'success':
                            # Use processed text or fallback to original
                            processed_text = text or processing_result.get('text', '')
                            processed_documents.append(processed_text)
                            processed_metadatas.append(metadata)
                        else:
                            logger.warning(f"Document processing failed for item {idx}")
                    else:
                        processed_documents.append(text)
                        processed_metadatas.append(metadata)
            
                texts = processed_documents
                metadatas = processed_metadatas
        
            # Proceed with standard text addition
            metadatas = metadatas or [{}] * len(texts)
            collection_name = self._get_collection_name(owner_id)
            collection = self.client.get_or_create_collection(
                name=collection_name,
                embedding_function=self.openai_ef,
                metadata={
                    "owner_id": owner_id.hex
                }
            )
  
            all_chunks = []
            all_metadatas = []
            all_ids = []

            for i, text in enumerate(texts):
                chunks = self.text_splitter.split_text(text)
                logger.debug(f"Text {i}: split into {len(chunks)} chunks")
                chunk_ids = [str(uuid4()) for _ in chunks]
                base_metadata = {
                    k: str(v) if not isinstance(v, (str, int, float, bool)) else v
                    for k, v in metadatas[i].items()
                }
                # Add thread_id to metadata only if provided
                if thread_id:
                    base_metadata['thread_id'] = str(thread_id)
                for idx, _ in enumerate(chunks):
                    metadata = {
                        **base_metadata,
                        'chunk_index': idx,
                        'total_chunks': len(chunks),
                        'owner_id': owner_id.hex,
                        'source_type': base_metadata.get('source_type', 'document'),  # Default to document
                        'filename': base_metadata.get('filename', base_metadata.get('source', 'unknown')),
                        'mime_type': base_metadata.get('mime_type', base_metadata.get('mimeType', 'unknown'))
                    }
                    all_metadatas.append(metadata)
                all_chunks.extend(chunks)
                all_ids.extend(chunk_ids)

            if all_chunks:
                logger.info(f"Adding {len(all_chunks)} total chunks to collection")
                collection.add(
                    documents=all_chunks,
                    ids=all_ids,
                    metadatas=all_metadatas
                )
                logger.info("Successfully added chunks to collection")
            return all_ids

        except Exception as e:
            logger.error(f"Error adding texts: {str(e)}", exc_info=True)
            traceback.print_exc()
            raise

    async def get_collection(
        self,
        owner_id: Any,  # Allow any type for owner_id
        create_if_missing: bool = True
    ) -> Any:
        """Get owner's collection with optional creation."""
        try:
            # Handle case where owner_id is a SQLAlchemy session
            if hasattr(owner_id, 'execute'):
                logger.warning(f"Owner ID was incorrectly passed a database session")
                return None
            
            collection_name = self._get_collection_name(owner_id)

            if create_if_missing:
                collection = self.client.get_or_create_collection(
                    name=collection_name,
                    embedding_function=self.openai_ef,
                    metadata={"owner_id": str(owner_id)}
                )
            else:
                collection = self.client.get_collection(
                    name=collection_name,
                    embedding_function=self.openai_ef
                )
            return collection
            
        except Exception as e:
            logger.error(f"Error getting collection: {e}")
            if not create_if_missing:
                return None
            raise

    async def query_collection(
        self,
        owner_id: UUID,
        query_text: str,
        n_results: int = 4,
        where_metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Query collection with security verification."""
        try:
            collection = await self.get_collection(owner_id, create_if_missing=False)  
            query_params = {
                "query_texts": [query_text],
                "n_results": n_results,
                "include": ["documents", "metadatas", "distances"]
            }
            
            if where_metadata:
                query_params["where"] = where_metadata
            
            results = collection.query(**query_params)
            
            formatted_results = {
                "documents": results["documents"][0],
                "metadatas": results["metadatas"][0],
                "distances": results["distances"][0]
            }
            
            return formatted_results
            
        except Exception as e:
            logger.error(f"Error querying collection: {e}")
            raise

    async def get_collection_stats(self) -> Dict[str, Any]:
        """Get enhanced collection statistics including storage usage."""
        try:
            collection_names = self.client.list_collections()
            logger.info(f"Found {len(collection_names)} collections")
        
            stats = {
                "total_collections": len(collection_names),
                "total_documents": 0,
                "unique_users": set(),
                "debug_data": [],
                "storage": {
                    "total_bytes": 0,
                    "human_readable": "0 B",
                    "by_collection": {}
                }
            }

            # Calculate total storage size
            total_size = self._calculate_directory_size(settings.CHROMA_PERSIST_DIR)
            stats["storage"]["total_bytes"] = total_size
            stats["storage"]["human_readable"] = humanize.naturalsize(total_size)

            for name in collection_names:
                try:
                    collection = self.client.get_collection(name)
                    metadata = collection.metadata
                    count = collection.count()
                    stats["total_documents"] += count

                    # Calculate collection-specific storage
                    collection_dir = os.path.join(settings.CHROMA_PERSIST_DIR, name)
                    if os.path.exists(collection_dir):
                        collection_size = self._calculate_directory_size(collection_dir)
                        stats["storage"]["by_collection"][name] = {
                            "bytes": collection_size,
                            "human_readable": humanize.naturalsize(collection_size)
                        }

                    debug_entry = {
                        "name": name,
                        "count": count,
                        "metadata": metadata,
                        "storage": stats["storage"]["by_collection"].get(name, {
                            "bytes": 0,
                            "human_readable": "0 B"
                        })
                    }

                    if metadata:
                        owner_id = metadata.get("owner_id")
                    
                        logger.info(
                            f"Collection {name}:\n"
                            f"  Documents: {count}\n"
                            f"  Owner ID: {owner_id}\n"
                            f"  Storage Size: {debug_entry['storage']['human_readable']}\n"
                            f"  Raw Metadata: {metadata}"
                        )
 
                        if owner_id:
                            stats["unique_users"].add(owner_id)
                            debug_entry["owner_id"] = owner_id
                        else:
                            logger.warning(f"Missing owner_id in metadata for collection {name}")
                    else:
                        logger.warning(f"No metadata for collection {name}")

                    stats["debug_data"].append(debug_entry)

                except Exception as e:
                    logger.error(f"Error processing collection {name}: {e}")
                    logger.error(traceback.format_exc())
                    stats.setdefault("errors", 0)
                    stats["errors"] += 1

            # Convert sets to counts
            stats["total_users"] = len(stats["unique_users"])
            
            # Remove internal tracking
            del stats["unique_users"]
        
            logger.info("Final stats:")
            logger.info(f"  Collections: {stats['total_collections']}")
            logger.info(f"  Documents: {stats['total_documents']}")
            logger.info(f"  Users: {stats['total_users']}")
            logger.info(f"  Total Storage: {stats['storage']['human_readable']}")
        
            return stats

        except Exception as e:
            logger.error(f"Error getting collection stats: {e}")
            logger.error(traceback.format_exc())
            return {
                "total_collections": 0,
                "total_documents": 0,
                "total_users": 0,
                "storage": {
                    "total_bytes": 0,
                    "human_readable": "0 B",
                    "by_collection": {}
                },
                "errors": 1,
                "error": str(e)
            }

    async def verify_health(self) -> bool:
        """Verify the health of the RAG storage service."""
        try:
            stats = await self.get_collection_stats()
            if str(stats.get("errors", 1)) == str(0):
                logger.info("RAG storage service is healthy")
                return True
            else:
                logger.warning("RAG storage service health check failed")
                return False
        
        except Exception as e:
            traceback.print_exc()
            logger.error(f"Error during RAG health check: {e}")
            return False

    async def cleanup(self):
        """Perform cleanup of unused collections."""
        try:
            collection_names = self.client.list_collections()
            for name in collection_names:
                collection = self.client.get_collection(name)
                metadata = collection.metadata or {}
                owner_id = metadata.get("owner_id")
                    
                if not owner_id:
                    logger.info(f"Deleting orphaned collection {name}")
                    self.client.delete_collection(name)
        except Exception as e:
            logger.error(f"Error during RAG cleanup: {e}")
            traceback.print_exc()

    async def delete_collection(self, owner_id: UUID):
        """Delete a collection for an owner."""
        try:
            collection_name = self._get_collection_name(owner_id)
            self.client.delete_collection(collection_name)
            logger.info(f"Deleted collection for owner {owner_id}")
        except Exception as e:
            logger.error(f"Error deleting collection: {e}")
            raise

# Create singleton instance
rag_storage_service = RAGStorageService()
