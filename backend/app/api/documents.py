from fastapi import APIRouter, File, UploadFile, HTTPException, Depends
from fastapi.responses import JSONResponse
from typing import Dict, Any
import tempfile
import os
import magic
import traceback

from app.core.security import auth_manager
from app.services.file_extraction_service import file_extraction_service

router = APIRouter()

# Configuration
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB

# In your documents.py file, modify the parse_document endpoint:

@router.post("/parse-document")
async def parse_document(
    file: UploadFile = File(...),
    current_user = Depends(auth_manager.get_current_user)
) -> Dict[str, Any]:
    """
    Universal document parser endpoint using FileExtractionService.
    """
    try:
        # Check file size
        file_content = await file.read()
        if len(file_content) == 0:
            raise HTTPException(status_code=400, detail="Empty file content")

        if len(file_content) > MAX_FILE_SIZE:
            raise HTTPException(
                status_code=400,
                detail=f"File size exceeds maximum limit of {MAX_FILE_SIZE/1024/1024}MB"
            )

        # Create a temporary file for extraction
        with tempfile.NamedTemporaryFile(
            delete=False,
            suffix=os.path.splitext(file.filename)[1]
        ) as temp_file:
            temp_file.write(file_content)
            temp_file.flush()
            temp_file_path = temp_file.name

        try:
            # Detect MIME type
            mime_type = magic.from_buffer(file_content, mime=True)

            # If a generic MIME type is detected, try extension-based detection
            if mime_type in ['text/plain', 'application/octet-stream']:
                extension_mime = file_extraction_service.get_mime_type_for_extension(file.filename)
                if extension_mime:
                    mime_type = extension_mime

            # Log the detected MIME type (optional, for debugging)
            print(f"Detected MIME type for {file.filename}: {mime_type}")

            # Validate MIME type
            if not file_extraction_service.is_supported_mime_type(mime_type):
                raise HTTPException(
                    status_code=400,
                    detail=f"Unsupported file type: {mime_type}"
                )

            # Detect programming language if applicable
            detected_language = file_extraction_service.get_language_for_extension(file.filename)
            
            # Extract text
            extracted_text = await file_extraction_service.extract_text_for_type(
                temp_file_path, 
                mime_type,
                preserve_formatting=True
            )
            
            # Sanitize text
            sanitized_text = file_extraction_service.sanitize_text(extracted_text)
            
            # Optional: Generate text chunks
            text_chunks = file_extraction_service.chunk_text(sanitized_text)
            
            return {
                "text": sanitized_text,
                "text_chunks": text_chunks,
                "metadata": {
                    "filename": file.filename,
                    "mime_type": mime_type,
                    "programming_language": detected_language,
                    "size": len(file_content),
                    "text_length": len(sanitized_text),
                    "chunk_count": len(text_chunks)
                }
            }
        
        finally:
            # Clean up temporary file
            try:
                os.unlink(temp_file_path)
            except Exception as cleanup_error:
                traceback.print_exc()

    except HTTPException:
        raise
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Unexpected document processing error: {str(e)}")

@router.get("/supported-formats")
async def get_supported_formats():
    """Return list of supported file formats and their size limits."""
    return {
        "max_file_size_mb": MAX_FILE_SIZE / 1024 / 1024,
        "supported_formats": {
            "documents": {
                "pdf": ".pdf - Adobe PDF documents",
                "word": [".doc - Microsoft Word", ".docx - Microsoft Word (Modern)"],
                "excel": [".xls - Microsoft Excel", ".xlsx - Microsoft Excel (Modern)", ".csv - Comma Separated Values"],
                "text": [".txt - Plain Text", ".rtf - Rich Text Format", ".md - Markdown"],
                "other": [".json - JSON", ".html - HTML", ".xml - XML"]
            },
            "programming_languages": {
                "python": [".py - Python Source Code", ".pyw - Python Script"],
                "java": ".java - Java Source Code",
                "cpp": [".cpp - C++ Source Code", ".h - C++ Header"],
                "c": ".c - C Source Code",
                "csharp": ".cs - C# Source Code",
                "javascript": [".js - JavaScript", ".jsx - React JavaScript"],
                "typescript": [".ts - TypeScript", ".tsx - React TypeScript"],
                "ruby": ".rb - Ruby Source Code",
                "php": ".php - PHP Source Code",
                "go": ".go - Go Source Code",
                "rust": ".rs - Rust Source Code",
                "swift": ".swift - Swift Source Code",
                "kotlin": [".kt - Kotlin Source Code", ".kts - Kotlin Script"],
                "scala": ".scala - Scala Source Code",
                "perl": ".pl - Perl Source Code",
                "haskell": [".hs - Haskell Source Code", ".lhs - Literate Haskell"],
                "lua": ".lua - Lua Source Code",
                "shell": [".sh - Shell Script", ".bash - Bash Script", ".zsh - Zsh Script"],
                "sql": ".sql - SQL Script"
            }
        }
    }
