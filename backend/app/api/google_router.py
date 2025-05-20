from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Dict, Any
from pydantic import BaseModel
from app.db.session import db_manager
from app.core.security import auth_manager
from app.services.file_indexing_service import file_indexing_service
from app.services.google_drive_service import google_drive_service
from app.core.progress_manager import progress_manager
from datetime import datetime
import traceback
import logging
import requests
from googleapiclient.discovery import build
from google.oauth2.credentials import Credentials
from googleapiclient.errors import HttpError

logger = logging.getLogger(__name__)

# IMPORTANT: Use the prefix that worked in your debug tests
router = APIRouter(prefix="/google", tags=["google"])

class GoogleAccessToken(BaseModel):
    access_token: str

@router.post("/ingest")
async def ingest_google_drive_folder(
    data: Dict[str, Any],
    current_user = Depends(auth_manager.get_current_user)
):
    logger.info("Handling /google/ingest request")
    try:
        access_token = data.get('access_token')
        refresh_token = data.get('refresh_token')
        files = data.get('files', [])

        if not access_token:
            raise HTTPException(status_code=400, detail="Access token is required")

        total_files = len(files)
        processed_files = 0
        failed_files = 0

        # Process each file
        for file in files:
            try:
                await google_drive_service.process_file(
                    access_token=access_token,
                    refresh_token=refresh_token,
                    owner_id=current_user.id,
                    file=file
                )
                processed_files += 1
            except Exception as file_error:
                logger.error(f"Error processing file {file.get('name')}: {file_error}")
                failed_files += 1

        return {
            "status": "completed",
            "stats": {
                "total_files": total_files,
                "processed_files": processed_files,
                "failed_files": failed_files
            }
        }
        
    except Exception as e:
        logger.error(f"Error processing Google Drive files: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/files")
async def list_drive_files(
    token: GoogleAccessToken,
    folder_id: str = "root",
    current_user = Depends(auth_manager.get_current_user)
):
    """List available Google Drive files."""
    logger.info("Handling /google/files request with token")
    try:
        # Use the EXACT same approach that worked in the test-direct endpoint
        credentials = Credentials(token=token.access_token)
        
        # Create a service with minimal API configuration
        service = build('drive', 'v3', credentials=credentials)
        
        # Use the same query approach as the successful test
        try:
            logger.info(f"Querying files in folder: {folder_id or 'root'}")
            query = f"'{folder_id}' in parents" if folder_id and folder_id != "root" else "trashed = false"
            
            response = service.files().list(
                q=query,
                pageSize=100,
                fields='nextPageToken, files(id, name, mimeType, modifiedTime, webViewLink)',
            ).execute()
            
            files = response.get('files', [])
            logger.info(f"Retrieved {len(files)} files from Google Drive")
            
            # Filter to supported types
            filtered_files = [
                {
                    'id': f['id'],
                    'name': f['name'],
                    'webUrl': f.get('webViewLink', ''),
                    'type': 'file',
                    'mimeType': f['mimeType']
                }
                for f in files
                if f.get('mimeType') in google_drive_service.SUPPORTED_MIME_TYPES
            ]
            
            logger.info(f"Filtered to {len(filtered_files)} supported files")
            
            return {
                "files": filtered_files
            }
            
        except HttpError as e:
            error_details = e._get_reason() if hasattr(e, '_get_reason') else str(e)
            status_code = e.resp.status if hasattr(e, 'resp') and hasattr(e.resp, 'status') else 500
            
            logger.error(f"Google Drive API error: {status_code} - {error_details}")
            logger.error(f"Full error: {str(e)}")
            
            raise HTTPException(
                status_code=status_code, 
                detail=f"Google Drive API error: {error_details}"
            )
                
    except Exception as e:
        logger.exception(f"Unexpected error listing Google Drive files: {e}")
        raise HTTPException(status_code=500, detail=f"Error accessing Google Drive: {str(e)}")

@router.post("/test-direct")
async def test_google_drive_direct(token: GoogleAccessToken):
    """Test Google Drive API directly with minimal dependencies"""
    logger.info("Handling /google/test-direct request")
    try:
        import json
        
        logger.info(f"Testing direct access with token (first 10 chars): {token.access_token[:10]}...")
        
        # Create minimal credentials
        credentials = Credentials(token=token.access_token)
        
        # Try different versions of the Drive API
        versions = ['v3', 'v2']
        results = {}
        
        for version in versions:
            try:
                logger.info(f"Testing Drive API {version}")
                service = build('drive', version, credentials=credentials)
                
                # Try a minimal API call
                if version == 'v3':
                    response = service.files().list(pageSize=1).execute()
                    file_count = len(response.get('files', []))
                    logger.info(f"Drive API {version} success: found {file_count} files")
                    results[version] = {
                        "success": True,
                        "file_count": file_count
                    }
                else:
                    response = service.files().list(maxResults=1).execute()
                    file_count = len(response.get('items', []))
                    logger.info(f"Drive API {version} success: found {file_count} files")
                    results[version] = {
                        "success": True,
                        "file_count": file_count
                    }
            except Exception as e:
                logger.error(f"Drive API {version} error: {str(e)}")
                results[version] = {
                    "success": False,
                    "error": str(e)
                }
        
        # Try to get user info
        try:
            user_service = build('oauth2', 'v2', credentials=credentials)
            user_info = user_service.userinfo().get().execute()
            logger.info(f"User info: {user_info}")
            results["user_info"] = {
                "success": True,
                "email": user_info.get('email'),
                "name": user_info.get('name')
            }
        except Exception as e:
            logger.error(f"User info error: {str(e)}")
            results["user_info"] = {
                "success": False,
                "error": str(e)
            }
        
        return {
            "token_prefix": token.access_token[:10] + "...",
            "results": results
        }
    except Exception as e:
        logger.exception(f"Error in direct test: {str(e)}")
        return {"error": str(e)}

# Add a new endpoint that's a simpler version of the files endpoint
@router.post("/simple-files")
async def simple_list_files(token: GoogleAccessToken):
    """Ultra-simple files listing for testing"""
    logger.info("Handling /google/simple-files request")
    try:
        credentials = Credentials(token=token.access_token)
        service = build('drive', 'v3', credentials=credentials)
        
        response = service.files().list(pageSize=10).execute()
        files = response.get('files', [])
        
        logger.info(f"Simple files endpoint found {len(files)} files")
        
        return {
            "files": [
                {
                    "id": f["id"],
                    "name": f["name"],
                    "mimeType": f["mimeType"]
                }
                for f in files
            ]
        }
    except Exception as e:
        logger.exception(f"Error in simple files listing: {e}")
        raise HTTPException(status_code=500, detail=str(e))
