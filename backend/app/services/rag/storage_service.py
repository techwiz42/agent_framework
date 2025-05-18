import logging
from typing import Dict, List, Any, Optional, Union
import uuid
import json
from datetime import datetime

from app.core.config import settings
from app.core.text_splitter import SemanticTextSplitter

logger = logging.getLogger(__name__)

class RAGStorageService:
    """
    Stub implementation of the RAG storage service.
    This implementation mimics the interface of the real RAG storage service
    but doesn't actually store or retrieve data from ChromaDB.
    It logs operations and returns appropriate stub responses.
    """
    
    def __init__(self):
        """Initialize the RAG storage service."""
        self.text_splitter = SemanticTextSplitter(
            max_chunk_size=settings.RAG_CHUNK_SIZE,
            min_chunk_size=settings.RAG_CHUNK_SIZE // 5
        )
        self.collections = {}  # Mock store for collections
        self.embeddings = {}   # Mock store for document embeddings
        logger.info("Initialized RAG Storage Service (stub implementation)")
    
    async def create_collection(self, collection_name: str, owner_id: Optional[str] = None) -> str:
        """
        Create a new collection for document storage.
        
        Args:
            collection_name: Name of the collection
            owner_id: Optional owner ID to associate with the collection
            
        Returns:
            Collection ID
        """
        collection_id = str(uuid.uuid4())
        self.collections[collection_id] = {
            "name": collection_name,
            "owner_id": owner_id,
            "created_at": datetime.now().isoformat(),
            "documents": [],
            "metadata": {
                "document_count": 0,
                "total_chunks": 0
            }
        }
        
        logger.info(f"Created collection: {collection_name} (ID: {collection_id}, Owner: {owner_id})")
        return collection_id
    
    async def get_or_create_collection(self, collection_name: str, owner_id: Optional[str] = None) -> str:
        """
        Get an existing collection or create a new one if it doesn't exist.
        
        Args:
            collection_name: Name of the collection
            owner_id: Optional owner ID to associate with the collection
            
        Returns:
            Collection ID
        """
        # Search for existing collection
        for coll_id, coll_data in self.collections.items():
            if coll_data["name"] == collection_name and coll_data["owner_id"] == owner_id:
                logger.info(f"Found existing collection: {collection_name} (ID: {coll_id})")
                return coll_id
        
        # Create new collection if not found
        return await self.create_collection(collection_name, owner_id)
    
    async def delete_collection(self, collection_id: str) -> bool:
        """
        Delete a collection and all its documents.
        
        Args:
            collection_id: ID of the collection to delete
            
        Returns:
            True if successful, False otherwise
        """
        if collection_id in self.collections:
            collection_name = self.collections[collection_id]["name"]
            del self.collections[collection_id]
            logger.info(f"Deleted collection: {collection_name} (ID: {collection_id})")
            return True
        
        logger.warning(f"Collection not found for deletion: {collection_id}")
        return False
    
    async def add_document(self, 
                          collection_id: str, 
                          document_text: str, 
                          metadata: Dict[str, Any],
                          document_id: Optional[str] = None) -> str:
        """
        Add a document to a collection, chunking it and generating embeddings.
        
        Args:
            collection_id: ID of the collection to add document to
            document_text: Text content of the document
            metadata: Document metadata (author, source, etc.)
            document_id: Optional document ID, will be generated if not provided
            
        Returns:
            Document ID
        """
        if collection_id not in self.collections:
            logger.error(f"Collection not found: {collection_id}")
            raise ValueError(f"Collection not found: {collection_id}")
        
        # Generate document ID if not provided
        doc_id = document_id or str(uuid.uuid4())
        
        # Add document metadata
        full_metadata = metadata.copy()
        full_metadata["document_id"] = doc_id
        full_metadata["added_at"] = datetime.now().isoformat()
        
        # Split document into chunks
        chunks = self.text_splitter.split_text(document_text, full_metadata)
        chunk_ids = [str(uuid.uuid4()) for _ in chunks]
        
        # Store document info
        self.collections[collection_id]["documents"].append({
            "document_id": doc_id,
            "metadata": full_metadata,
            "chunk_count": len(chunks),
            "chunk_ids": chunk_ids
        })
        
        # Update collection metadata
        self.collections[collection_id]["metadata"]["document_count"] += 1
        self.collections[collection_id]["metadata"]["total_chunks"] += len(chunks)
        
        logger.info(f"Added document to collection {collection_id}: {doc_id} (chunks: {len(chunks)})")
        logger.debug(f"Document metadata: {json.dumps(metadata)}")
        
        return doc_id
    
    async def delete_document(self, collection_id: str, document_id: str) -> bool:
        """
        Delete a document from a collection.
        
        Args:
            collection_id: ID of the collection containing the document
            document_id: ID of the document to delete
            
        Returns:
            True if successful, False otherwise
        """
        if collection_id not in self.collections:
            logger.error(f"Collection not found: {collection_id}")
            return False
        
        # Find document in collection
        documents = self.collections[collection_id]["documents"]
        for i, doc in enumerate(documents):
            if doc["document_id"] == document_id:
                # Update collection metadata
                self.collections[collection_id]["metadata"]["document_count"] -= 1
                self.collections[collection_id]["metadata"]["total_chunks"] -= doc["chunk_count"]
                
                # Remove document
                removed_doc = documents.pop(i)
                logger.info(f"Deleted document from collection {collection_id}: {document_id}")
                return True
        
        logger.warning(f"Document not found for deletion: {document_id} in collection {collection_id}")
        return False
    
    async def search_documents(self, 
                              collection_id: str, 
                              query: str, 
                              k: int = None,
                              filter_criteria: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """
        Search for documents in a collection based on semantic similarity.
        
        Args:
            collection_id: ID of the collection to search
            query: Search query text
            k: Number of results to return (default from settings)
            filter_criteria: Optional metadata filter criteria
            
        Returns:
            List of search results with document chunks and metadata
        """
        if collection_id not in self.collections:
            logger.error(f"Collection not found: {collection_id}")
            return []
        
        k = k or settings.RAG_DEFAULT_RETRIEVAL_K
        logger.info(f"Searching collection {collection_id} for: '{query}' (k={k}, filters={filter_criteria})")
        
        # Return stub search results
        max_results = min(k, len(self.collections[collection_id]["documents"]))
        
        # If no documents, return empty results
        if max_results == 0:
            return []
        
        results = []
        for i in range(max_results):
            # Get a document from the collection (cyclically if needed)
            doc_index = i % len(self.collections[collection_id]["documents"])
            doc = self.collections[collection_id]["documents"][doc_index]
            
            # Create a mock search result
            results.append({
                "id": doc["chunk_ids"][0] if doc["chunk_ids"] else str(uuid.uuid4()),
                "text": f"Mock chunk content for document {doc['document_id']} containing terms from '{query}'",
                "metadata": doc["metadata"],
                "score": 0.9 - (0.1 * i),  # Decreasing scores for subsequent results
                "document_id": doc["metadata"]["document_id"]
            })
        
        return results
    
    async def get_collection_stats(self, collection_id: str) -> Dict[str, Any]:
        """
        Get statistics for a collection.
        
        Args:
            collection_id: ID of the collection
            
        Returns:
            Dictionary with collection statistics
        """
        if collection_id not in self.collections:
            logger.error(f"Collection not found: {collection_id}")
            return {}
        
        collection = self.collections[collection_id]
        
        return {
            "collection_id": collection_id,
            "name": collection["name"],
            "owner_id": collection["owner_id"],
            "created_at": collection["created_at"],
            "document_count": collection["metadata"]["document_count"],
            "total_chunks": collection["metadata"]["total_chunks"],
            "size_bytes": 0  # Stub implementation doesn't track actual size
        }
    
    async def list_collections(self, owner_id: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        List all collections, optionally filtered by owner.
        
        Args:
            owner_id: Optional owner ID to filter collections
            
        Returns:
            List of collection information dictionaries
        """
        result = []
        
        for coll_id, coll_data in self.collections.items():
            # Filter by owner if specified
            if owner_id and coll_data["owner_id"] != owner_id:
                continue
                
            result.append({
                "collection_id": coll_id,
                "name": coll_data["name"],
                "owner_id": coll_data["owner_id"],
                "created_at": coll_data["created_at"],
                "document_count": coll_data["metadata"]["document_count"]
            })
        
        logger.info(f"Listed {len(result)} collections" + (f" for owner {owner_id}" if owner_id else ""))
        return result
    
    async def list_documents(self, collection_id: str) -> List[Dict[str, Any]]:
        """
        List all documents in a collection.
        
        Args:
            collection_id: ID of the collection
            
        Returns:
            List of document information dictionaries
        """
        if collection_id not in self.collections:
            logger.error(f"Collection not found: {collection_id}")
            return []
        
        result = []
        for doc in self.collections[collection_id]["documents"]:
            metadata = doc["metadata"]
            result.append({
                "document_id": doc["document_id"],
                "title": metadata.get("title", "Untitled Document"),
                "source": metadata.get("source", "unknown"),
                "added_at": metadata.get("added_at"),
                "chunk_count": doc["chunk_count"],
                "metadata": metadata
            })
        
        logger.info(f"Listed {len(result)} documents in collection {collection_id}")
        return result
    
    async def update_document_metadata(self, 
                                      collection_id: str, 
                                      document_id: str, 
                                      metadata: Dict[str, Any]) -> bool:
        """
        Update metadata for a document.
        
        Args:
            collection_id: ID of the collection containing the document
            document_id: ID of the document to update
            metadata: New metadata dictionary (will be merged with existing)
            
        Returns:
            True if successful, False otherwise
        """
        if collection_id not in self.collections:
            logger.error(f"Collection not found: {collection_id}")
            return False
        
        # Find document in collection
        for doc in self.collections[collection_id]["documents"]:
            if doc["document_id"] == document_id:
                # Update metadata (merge with existing)
                doc["metadata"].update(metadata)
                doc["metadata"]["updated_at"] = datetime.now().isoformat()
                
                logger.info(f"Updated metadata for document {document_id} in collection {collection_id}")
                return True
        
        logger.warning(f"Document not found for metadata update: {document_id} in collection {collection_id}")
        return False
    
    async def get_document(self, collection_id: str, document_id: str) -> Optional[Dict[str, Any]]:
        """
        Get a document from a collection.
        
        Args:
            collection_id: ID of the collection containing the document
            document_id: ID of the document to retrieve
            
        Returns:
            Document information or None if not found
        """
        if collection_id not in self.collections:
            logger.error(f"Collection not found: {collection_id}")
            return None
        
        # Find document in collection
        for doc in self.collections[collection_id]["documents"]:
            if doc["document_id"] == document_id:
                logger.info(f"Retrieved document {document_id} from collection {collection_id}")
                return {
                    "document_id": doc["document_id"],
                    "metadata": doc["metadata"],
                    "chunk_count": doc["chunk_count"]
                }
        
        logger.warning(f"Document not found: {document_id} in collection {collection_id}")
        return None

# Initialize the singleton instance
rag_storage_service = RAGStorageService()