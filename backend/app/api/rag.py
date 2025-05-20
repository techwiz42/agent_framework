from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional
from uuid import UUID
from pydantic import BaseModel

from app.db.session import db_manager
from app.core.security import auth_manager
from app.services.rag import rag_storage_service
from app.services.rag.query_service import rag_query_service
import logging

router = APIRouter()
logger = logging.getLogger(__name__)

class RAGQuery(BaseModel):
    query: str
    k: Optional[int] = 4

class RAGToggle(BaseModel):
    enabled: bool

# No longer need to invalidate caches as we're not using Redis anymore

@router.post("/threads/{thread_id}/ingest/document")
async def ingest_document(
    thread_id: UUID,
    file: UploadFile = File(...),
    db: AsyncSession = Depends(db_manager.get_session),
    current_user = Depends(auth_manager.get_current_user)
):
    """Ingest a document into the RAG system."""
    try:
        # Read file content
        content = await file.read()
        
        # Verify thread ownership
        thread = await db_manager.get_thread(db, thread_id)
        if not thread:
            raise HTTPException(
                status_code=404,
                detail="Thread not found"
            )
        if thread.owner_id != current_user.id:
            raise HTTPException(
                status_code=403,
                detail="Not authorized to modify this thread"
            )

        # Process document
        document_ids = await rag_storage_service.add_texts(
            thread_id=UUID(thread_id),
            owner_id=UUID(current_user.id),
            texts=[content.decode('utf-8')],
            metadatas=[{
                "source": file.filename,
                "type": "document",
                "mime_type": file.content_type
            }]
        )

        # No longer need to prefetch queries since we're not using Redis cache

        return {
            "status": "success",
            "document_ids": document_ids,
            "filename": file.filename
        }

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error processing document: {str(e)}"
        )

@router.post("/threads/{thread_id}/enable")
async def enable_thread_rag(
    thread_id: UUID,
    toggle: RAGToggle,
    db: AsyncSession = Depends(db_manager.get_session),
    current_user = Depends(auth_manager.get_current_user)
):
    """Enable or disable RAG for a thread."""
    try:
        # Verify thread ownership
        thread = await db_manager.get_thread(db, thread_id)
        if not thread:
            raise HTTPException(
                    status_code=404,
                    detail=f"Thread owner not found"
                )
        # Verify thread ownership
        thread = await db_manager.get_thread(db, thread_id)
        if not thread:
            raise HTTPException(status_code=404, detail="Thread not found")
        if thread.owner_id != current_user.id:
            raise HTTPException(
                status_code=403,
                detail="Not authorized to modify this thread"
            )

        if toggle.enabled:
            collection = await rag_storage_service.initialize_thread_collection(
                thread_id=thread_id,
                owner_id=current_user.id
            )

            # No longer need to invalidate caches since we're not using Redis

            return {
                "status": "enabled",
                "collection_name": collection.name if collection else None
            }
        else:
            await rag_storage_service.delete_collection(
                thread_id=thread_id,
                owner_id=current_user.id
            )

            # No longer need to invalidate caches since we're not using Redis

            return {"status": "disabled"}

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to toggle RAG: {str(e)}"
        )

@router.post("/threads/{thread_id}/query")
async def query_thread_knowledge(
    thread_id: UUID,
    query: RAGQuery,
    db: AsyncSession = Depends(db_manager.get_session),
    current_user = Depends(auth_manager.get_current_user)
):
    """Query thread knowledge base."""
    try:
        # Verify thread access
        thread = await db_manager.get_thread(db, thread_id)
        if not thread:
            raise HTTPException(status_code=404, detail="Thread not found")

        # Check if user is owner or participant
        is_participant = await db_manager.is_thread_participant(
            db,
            thread_id,
            current_user.email
        )
        if thread.owner_id != current_user.id and not is_participant:
            raise HTTPException(
                status_code=403,
                detail="Not authorized to query this thread"
            )

        # Execute query using regular query service
        # Documents belong to the owner, not specific threads
        results = await rag_query_service.query_knowledge(
            owner_id=thread.owner_id,  # Always use owner_id for collection
            query_text=query.query,
            k=query.k
        )

        return {
            "results": results.get("documents", []),
            "metadatas": results.get("metadatas", []),
            "scores": results.get("distances", [])
        }

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error querying knowledge base: {str(e)}"
        )

@router.get("/threads/{thread_id}/status")
async def get_rag_status(
    thread_id: UUID,
    db: AsyncSession = Depends(db_manager.get_session),
    current_user = Depends(auth_manager.get_current_user)
):
    """Get RAG status and statistics for a thread."""
    try:
        # Verify thread access
        thread = await db_manager.get_thread(db, thread_id)
        if not thread:
            raise HTTPException(status_code=404, detail="Thread not found")

        # Check if user is owner or participant
        is_participant = await db_manager.is_thread_participant(
            db,
            thread_id,
            current_user.email
        )
        if thread.owner_id != current_user.id and not is_participant:
            raise HTTPException(
                status_code=403,
                detail="Not authorized to view this thread"
            )

        # Get collection stats
        stats = await rag_storage_service.get_collection_stats(
            thread_id=thread_id,
            owner_id=thread.owner_id  # Always use owner_id for collection
        )

        return stats

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error getting RAG status: {str(e)}"
        )
                         
