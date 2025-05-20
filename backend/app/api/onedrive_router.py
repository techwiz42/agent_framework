from fastapi import APIRouter, Depends, HTTPException
from typing import Dict, Any, List
from pydantic import BaseModel, Field
from app.core.security import auth_manager
from app.services.onedrive_service import onedrive_service, OneDriveError
import logging

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/onedrive", tags=["onedrive"])

class Microsoft(BaseModel):
    downloadUrl: str

class OneDriveFile(BaseModel):
    id: str
    name: str
    mimeType: str
    webUrl: str | None = None
    microsoft: Dict[str, Any] | None = Field(None, alias='@microsoft')

    class Config:
        populate_by_name = True
        allow_population_by_field_name = True

class IngestRequest(BaseModel):
    onedrive_token: str
    files: List[OneDriveFile]

    class Config:
        populate_by_name = True

@router.post("/ingest")
async def ingest_onedrive_files(
    request: IngestRequest,
    current_user = Depends(auth_manager.get_current_user)
):
    """
    Process and ingest files from OneDrive.
    """
    try:
        logger.info(f"Processing files: {request.files}")
        # Map files to format expected by service
        files_to_process = []
        for file in request.files:
            try:
                mapped_file = {
                    'id': file.id,
                    'name': file.name,
                    'mimeType': file.mimeType,
                    'webUrl': file.webUrl,
                    '@microsoft.graph.downloadUrl': file.microsoft['downloadUrl'] if file.microsoft else None
                }
                if not mapped_file['@microsoft.graph.downloadUrl']:
                    logger.warning(f"No download URL for file {file.name}")
                    continue
                files_to_process.append(mapped_file)
            except Exception as e:
                logger.error(f"Error mapping file {file.name}: {str(e)}")
                continue

        if not files_to_process:
            return {
                "status": "error",
                "message": "No valid files to process",
                "processed_count": 0,
                "failed_count": len(request.files)
            }

        # Process the files
        stats = await onedrive_service.process_files(
            access_token=request.onedrive_token,
            files=files_to_process,
            owner_id=current_user.id
        )
        
        return {
            "status": "success",
            "processed_count": stats["processed_count"],
            "failed_count": stats["failed_count"],
            "message": f"Processed {stats['processed_count']} files successfully"
        }

    except OneDriveError as e:
        logger.error(f"OneDrive error: {str(e)}")
        raise HTTPException(
            status_code=e.status_code,
            detail={
                "error": {
                    "type": e.error_type,
                    "message": e.message,
                    "original_error": e.original_error
                }
            }
        )
    
    except Exception as e:
        logger.exception("Unexpected error processing OneDrive files")
        raise HTTPException(
            status_code=500,
            detail={
                "error": {
                    "type": "unexpected_error",
                    "message": "An unexpected error occurred while processing files",
                    "original_error": str(e)
                }
            }
        )

@router.get("/validate-token")
async def validate_token(
    token: str,
    current_user = Depends(auth_manager.get_current_user)
):
    """
    Validate an OneDrive access token.
    """
    try:
        is_valid = await onedrive_service.validate_token(token)
        return {
            "valid": is_valid,
            "message": "Token is valid" if is_valid else "Token has expired"
        }
    
    except OneDriveError as e:
        raise HTTPException(
            status_code=e.status_code,
            detail={
                "error": {
                    "type": e.error_type,
                    "message": e.message,
                    "original_error": e.original_error
                }
            }
        )
    
    except Exception as e:
        logger.exception("Error validating token")
        raise HTTPException(
            status_code=500,
            detail={
                "error": {
                    "type": "validation_error",
                    "message": "Failed to validate token",
                    "original_error": str(e)
                }
            }
        )
