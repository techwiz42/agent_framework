from typing import List, Dict, Any, Optional, BinaryIO
from uuid import UUID
import asyncio
import logging
from datetime import datetime
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from langchain.text_splitter import RecursiveCharacterTextSplitter
from fastapi import UploadFile, HTTPException
import magic
import PyPDF2
import docx2txt
from io import BytesIO
from app.models.domain.models import Message, Thread

logger = logging.getLogger(__name__)

class DataIngestionManager:
    def __init__(self, rag_service):
        self.rag_service = rag_service
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=500,
            chunk_overlap=750,
            length_function=len
        )

    async def ingest_conversation_history(
        self,
        db: AsyncSession,
        thread_id: UUID,
        batch_size: int = 100
    ):
        """Ingest historical conversation messages into RAG."""
        try:
            # Retrieve the thread to get owner_id
            thread_result = await db.execute(
                select(Thread).where(Thread.id == thread_id)
            )
            thread = thread_result.scalars().first()
            if not thread:
                logger.error(f"Thread {thread_id} not found")
                return

            # Get conversation messages
            messages = await db.execute(
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
                    # Format based on sender type
                    if msg.agent_id:
                        sender = f"[{msg.message_metadata.get('agent_type', 'AGENT')}]"
                    else:
                        sender = f"[{msg.message_metadata.get('participant_name', 'USER')}]"
                    
                    formatted_texts.append({
                        'content': f"{sender}: {msg.content}",
                        'metadata': {
                            'source_type': 'message',
                            'message_id': str(msg.id),
                            'created_at': msg.created_at.isoformat(),
                            'source': 'conversation_history'
                        }
                    })
                
                # Add to vector store with thread-specific context
                await self.rag_service.add_texts(
                    owner_id=thread.owner_id,
                    thread_id=thread_id,
                    texts=[t['content'] for t in formatted_texts],
                    metadatas=[t['metadata'] for t in formatted_texts]
                )
            
            logger.info(f"Ingested {len(messages)} messages for thread {thread_id}")
            
        except Exception as e:
            logger.error(f"Error ingesting conversation history: {e}")
            raise

    async def ingest_document(
        self,
        owner_id: UUID,  # Direct owner_id parameter
        file: UploadFile,
        document_type: Optional[str] = None
    ):
        """Process and ingest a document file."""
        try:
            content = await file.read()
            
            # Detect mime type if not provided
            mime_type = document_type or magic.from_buffer(content, mime=True)
            
            # Extract text based on document type
            text_content = await self._extract_text(content, mime_type, file.filename)
            
            # Split text into chunks
            chunks = self.text_splitter.split_text(text_content)
            
            # Prepare metadata
            base_metadata = {
                'source_type': 'document',
                'source': file.filename,
                'mime_type': mime_type,
                'ingested_at': datetime.utcnow().isoformat()
            }
            
            # Add chunks to vector store directly with owner_id
            await self.rag_service.add_texts(
                owner_id=owner_id,
                texts=chunks,
                metadatas=[{
                    **base_metadata,
                    'chunk_index': i,
                    'total_chunks': len(chunks)
                } for i in range(len(chunks))]
            )
            
            logger.info(f"Ingested document {file.filename} for owner {owner_id}")
            
            return {
                'filename': file.filename,
                'mime_type': mime_type,
                'chunk_count': len(chunks)
            }
            
        except Exception as e:
            logger.error(f"Error ingesting document: {e}")
            raise

    async def ingest_urls(
        self,
        owner_id: UUID,  # Changed from thread_id to owner_id
        urls: List[str]
    ):
        """Ingest content from provided URLs."""
        try:
            from langchain.document_loaders import UnstructuredURLLoader
            
            # Load content from URLs
            loader = UnstructuredURLLoader(urls=urls)
            documents = await asyncio.to_thread(loader.load)
            
            # Process each document
            for doc in documents:
                chunks = self.text_splitter.split_text(doc.page_content)
                
                # Prepare metadata
                base_metadata = {
                    'source_type': 'document',
                    'source': doc.metadata.get('source', 'unknown'),
                    'title': doc.metadata.get('title', 'untitled'),
                    'ingested_at': datetime.utcnow().isoformat()
                }
                
                # Add to vector store with owner_id
                await self.rag_service.add_texts(
                    owner_id=owner_id,
                    texts=chunks,
                    metadatas=[{
                        **base_metadata,
                        'chunk_index': i,
                        'total_chunks': len(chunks)
                    } for i in range(len(chunks))]
                )
            
            logger.info(f"Ingested {len(documents)} URLs for owner {owner_id}")
            
            return {
                'processed_urls': urls,
                'document_count': len(documents)
            }
            
        except Exception as e:
            logger.error(f"Error ingesting URLs: {e}")
            raise

    async def _extract_text(
        self,
        content: bytes,
        mime_type: str,
        filename: str
    ) -> str:
        """Extract text content from various file types."""
        try:
            if mime_type == 'application/pdf':
                return await self._process_pdf(content)
            elif mime_type == 'application/vnd.openxmlformats-officedocument.wordprocessingml.document':
                return await self._process_docx(content)
            elif mime_type.startswith('text/'):
                return content.decode('utf-8')
            else:
                raise ValueError(f"Unsupported file type: {mime_type}")
                
        except Exception as e:
            logger.error(f"Error extracting text from {filename}: {e}")
            raise

    async def _process_pdf(self, content: bytes) -> str:
        """Extract text from PDF file."""
        try:
            pdf_file = BytesIO(content)
            reader = PyPDF2.PdfReader(pdf_file)
            
            text_content = []
            for page in reader.pages:
                text_content.append(page.extract_text())
            
            return "\n".join(text_content)
            
        except Exception as e:
            logger.error(f"Error processing PDF: {e}")
            raise

    async def _process_docx(self, content: bytes) -> str:
        """Extract text from DOCX file."""
        try:
            docx_file = BytesIO(content)
            text_content = docx2txt.process(docx_file)
            return text_content
            
        except Exception as e:
            logger.error(f"Error processing DOCX: {e}")
            raise

# Create singleton instance
ingestion_manager = DataIngestionManager
