import os
import uuid
import logging
import tempfile
import traceback
from typing import Dict, Any, Optional, Union
from datetime import datetime

from app.services.file_extraction_service import file_extraction_service
from app.services.rag.storage_service import rag_storage_service

logger = logging.getLogger(__name__)

class DocumentProcessingService:
    async def process_document(
        self, 
        file_content: bytes, 
        file_metadata: Dict[str, Any],
        owner_id: Optional[Union[str, uuid.UUID]] = None,
        source: str = 'unknown'
    ) -> Dict[str, Any]:
        """
        Comprehensive document processing workflow.
        
        Steps:
        1. Validate inputs
        2. Determine file type and validate
        3. Extract text content
        4. Store in vector database
        5. Return processing result
        """
        try:
            # Validate inputs
            if not file_content:
                logger.warning("Empty file content. Skipping processing.")
                return {"status": "error", "message": "Empty file content"}
            
            if not owner_id:
                logger.warning("No owner ID provided. Skipping processing.")
                return {"status": "error", "message": "Missing owner ID"}
            
            # Prepare metadata with robust filename handling
            document_id = file_metadata.get('file_id') or str(uuid.uuid4())
            filename = file_metadata.get('filename', 'Untitled Document')
            source_name = file_metadata.get('source', 'unknown')
            
            # Ensure meaningful source name
            if source_name == 'unknown' and filename != 'Untitled Document':
                source_name = filename
            
            mime_type = file_metadata.get('mime_type', 'unknown')
            
            # Create a temporary file for extraction
            with tempfile.NamedTemporaryFile(
                delete=False, 
                suffix=self._get_file_extension(file_metadata)
            ) as temp_file:
                temp_file.write(file_content)
                temp_file.flush()
                temp_file_path = temp_file.name
            
            try:
                # Validate mime type
                if not file_extraction_service.is_supported_mime_type(mime_type):
                    logger.warning(f"Unsupported mime type: {mime_type}")
                    return {"status": "error", "message": "Unsupported file type"}
                
                # Extract text
                extracted_text = await file_extraction_service.extract_text_for_type(
                    temp_file_path, 
                    mime_type
                )
                
                # Sanitize text
                if not extracted_text:
                    logger.warning(f"No text extracted from {filename}")
                    return {"status": "error", "message": "No text could be extracted"}
                
                sanitized_text = file_extraction_service.sanitize_text(extracted_text)
                
                # Prepare metadata for storage
                metadata = {
                    'document_id': document_id,
                    'filename': filename,
                    'name': source_name,  # Add this for document search
                    'mime_type': mime_type,
                    'source': source,
                    'source_type': 'document',
                    'web_url': file_metadata.get('web_url'),
                    'modified_at': file_metadata.get('modified_at') or datetime.utcnow().isoformat(),
                    'ingested_at': datetime.utcnow().isoformat()
                }
                
                # Store in vector database
                chunk_ids = await rag_storage_service.add_texts(
                    owner_id=owner_id,
                    texts=[sanitized_text],
                    metadatas=[metadata]
                )
                
                return {
                    "status": "success",
                    "document_id": document_id,
                    "filename": filename,
                    "chunks_processed": len(chunk_ids),
                    "chunk_ids": chunk_ids
                }
            
            finally:
                # Clean up temporary file
                try:
                    os.unlink(temp_file_path)
                except Exception as cleanup_error:
                    logger.error(f"Error cleaning up temp file: {cleanup_error}")
        
        except Exception as e:
            logger.error(f"Document processing error: {e}")
            logger.error(traceback.format_exc())
            return {
                "status": "error", 
                "message": f"Processing failed: {str(e)}"
            }

    def _get_file_extension(self, metadata: Dict[str, Any]) -> str:
        """
        Determine appropriate file extension based on mime type.
        
        Provides a consistent way to assign file extensions for temporary files.
        Includes support for Google Workspace and other common mime types.
        """
        mime_to_extension = {
            # Standard Office/PDF Formats
            'application/pdf': '.pdf',
            'application/vnd.openxmlformats-officedocument.wordprocessingml.document': '.docx',
            'application/msword': '.doc',
            'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet': '.xlsx',
            'application/vnd.ms-excel': '.xls',
            'application/vnd.ms-powerpoint': '.ppt',
            'application/vnd.openxmlformats-officedocument.presentationml.presentation': '.pptx',
            
            # Text-based Formats
            'text/csv': '.csv',
            'text/plain': '.txt',
            'text/markdown': '.md',
            'text/html': '.html',
            'application/json': '.json',
            
            # Google Workspace Mime Types
            'application/vnd.google-apps.document': '.gdoc',
            'application/vnd.google-apps.spreadsheet': '.gsheet',
            'application/vnd.google-apps.presentation': '.gslides',
            'application/vnd.google-apps.drawing': '.gdraw',
            'application/vnd.google-apps.form': '.gform',
            'application/vnd.google-apps.script': '.gs',
            'application/vnd.google-apps.map': '.gmaps',
            'application/vnd.google-apps.site': '.gsite',
            
            # Additional Common Formats
            'application/rtf': '.rtf',
            'text/rtf': '.rtf',
            'application/x-yaml': '.yaml',
            'text/yaml': '.yaml'
        }
        
        return mime_to_extension.get(metadata.get('mime_type', ''), '.txt')

# Singleton instance
document_processing_service = DocumentProcessingService()
