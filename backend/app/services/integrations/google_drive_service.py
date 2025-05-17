from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseDownload
from googleapiclient.errors import HttpError
from typing import List, Dict, Any, Optional, Union
from uuid import UUID
import logging
import io
import traceback
from fastapi import HTTPException
import aiohttp
import json
from datetime import datetime

from app.core.config import settings

logger = logging.getLogger(__name__)

SCOPES = ['https://www.googleapis.com/auth/drive.readonly']

SUPPORTED_MIME_TYPES = [
    'text/plain',
    'text/csv',
    'application/pdf',
    'application/vnd.google-apps.document',
    'application/vnd.google-apps.spreadsheet',
    'application/msword',
    'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
    'application/vnd.ms-excel',
    'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
    'application/json',
    'text/html',
    'text/markdown'
]

class GoogleDriveService:
    def __init__(self):
        self.SUPPORTED_MIME_TYPES = SUPPORTED_MIME_TYPES
    
    async def refresh_token(self, refresh_token: str) -> dict:
        """Refresh access token using refresh token"""
        try:
            logger.info(f"Attempting to refresh token, refresh_token first 5 chars: {refresh_token[:5]}...")
            async with aiohttp.ClientSession() as session:
                # Use relative path for API call
                async with session.post(
                    '/api/oauth/google/refresh',
                    json={'refresh_token': refresh_token},
                    headers={'Content-Type': 'application/json'}
                ) as response:
                    if not response.ok:
                        error_text = await response.text()
                        logger.error(f"Failed to refresh token: Status {response.status}, {error_text}")
                        raise Exception(f'Failed to refresh token: {error_text}')
                    
                    token_data = await response.json()
                    logger.info(f"Token refreshed successfully. Keys in response: {token_data.keys()}")
                    return token_data
        except Exception as e:
            logger.error(f"Error refreshing token: {e}")
            raise

    async def validate_access_token(self, access_token: str) -> bool:
        """Validate the access token by making a simple Google Drive API call."""
        try:
            logger.info(f"Validating access token, first 10 chars: {access_token[:10]}...")
            credentials = Credentials(token=access_token)
            service = build('drive', 'v3', credentials=credentials)
            # Make a simple API call to test the token
            result = service.files().list(pageSize=1).execute()
            logger.info("Token validation successful")
            return True
        except Exception as e:
            logger.error(f"Token validation failed: {e}")
            return False


    async def list_files(
        self, 
        access_token: str, 
        refresh_token: Optional[str] = None,
        folder_id: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        async def make_request_with_refresh():
            nonlocal access_token
            try:
                logger.info(f"Listing files with access token (first 10 chars): {access_token[:10]}...")
                
                # Validate the token first
                is_valid = await self.validate_access_token(access_token)
                if not is_valid and refresh_token:
                    logger.info("Access token invalid, attempting refresh")
                    token_data = await self.refresh_token(refresh_token)
                    access_token = token_data['access_token']
                    logger.info(f"Using new access token (first 10 chars): {access_token[:10]}...")
                
                credentials = Credentials(token=access_token)
                service = build('drive', 'v3', credentials=credentials)
    
                # Construct query to filter files in the specific folder
                query = f"'{folder_id}' in parents" if folder_id else "trashed = false"
                logger.info(f"Using query: {query}")
            
                results = []
                page_token = None
            
                while True:
                    try:
                        logger.info("Making Google Drive API list files request")
                        response = service.files().list(
                            q=query,
                            spaces='drive',
                            pageSize=1000,
                            fields='nextPageToken, files(id, name, mimeType, modifiedTime, webViewLink)',
                            pageToken=page_token
                        ).execute()
                        
                        logger.info(f"Files API response received, items: {len(response.get('files', []))}")
                    except HttpError as e:
                        if e.resp.status == 401 and refresh_token:  # Token expired
                            logger.info("Token expired during API call, attempting to refresh")
                            token_data = await self.refresh_token(refresh_token)
                            access_token = token_data['access_token']
                            logger.info(f"Token refreshed successfully, new token first 10 chars: {access_token[:10]}...")
                            return await make_request_with_refresh()
                        logger.error(f"Google API error: {e.resp.status} - {e._get_reason()}")
                        raise
                
                    files = response.get('files', [])
                    logger.info(f"Retrieved {len(files)} files from Google Drive")
                    
                    filtered_files = [
                        {
                            'id': f['id'],
                            'name': f['name'],
                            'webUrl': f.get('webViewLink', ''),
                            'type': 'file',
                            'mimeType': f['mimeType']
                        }
                        for f in files
                        if f.get('mimeType') in SUPPORTED_MIME_TYPES
                    ]
                    
                    logger.info(f"Filtered to {len(filtered_files)} supported files")
                
                    results.extend(filtered_files)
                    page_token = response.get('nextPageToken')
                
                    if not page_token:
                        break
        
                return results
         
            except Exception as e:
                logger.error(f"Error listing Google Drive files: {e}")
                traceback.print_exc()
                return []

        return await make_request_with_refresh()

    async def download_file(
        self, 
        access_token: str, 
        refresh_token: Optional[str] = None,
        file_id: str = None,
        mime_type: str = None
    ) -> bytes:
        """Download a single file from Google Drive."""
        if not file_id:
            logger.warning("No file ID provided to download")
            return None

        async def download_with_refresh():
            nonlocal access_token, refresh_token
            try:
                logger.info(f"Downloading file {file_id} with access token (first 10 chars): {access_token[:10]}...")
                credentials = Credentials(token=access_token)
                service = build('drive', 'v3', credentials=credentials)

                try:
                    # Handle Google Docs/Sheets - export as appropriate format
                    if mime_type in ['application/vnd.google-apps.document', 'application/vnd.google-apps.spreadsheet']:
                        export_mime_type = 'text/plain' if mime_type == 'application/vnd.google-apps.document' else 'text/csv'
                        logger.info(f"Exporting Google file as {export_mime_type}")
                        request = service.files().export_media(fileId=file_id, mimeType=export_mime_type)
                    else:
                        # For other files, use standard media download
                        logger.info("Using standard media download")
                        request = service.files().get_media(fileId=file_id)
                    
                    fh = io.BytesIO()
                    downloader = MediaIoBaseDownload(fh, request)
                    done = False
                    
                    logger.info("Starting download...")
                    while not done:
                        try:
                            status, done = downloader.next_chunk()
                            logger.info(f"Download progress: {int(status.progress() * 100)}%")
                        except HttpError as e:
                            if e.resp.status == 401 and refresh_token:  # Token expired
                                logger.info("Token expired during download, attempting to refresh")
                                token_data = await self.refresh_token(refresh_token)
                                access_token = token_data['access_token']
                                logger.info("Token refreshed successfully")
                                return await download_with_refresh()
                            logger.error(f"Download error: {e.resp.status} - {e._get_reason()}")
                            raise
                    
                    fh.seek(0)
                    file_content = fh.read()
                    logger.info(f"Downloaded {len(file_content)} bytes")
                    return file_content

                except HttpError as download_error:
                    if download_error.resp.status == 401 and refresh_token:  # Token expired
                        logger.info("Token expired during API call, attempting to refresh")
                        token_data = await self.refresh_token(refresh_token)
                        access_token = token_data['access_token']
                        logger.info("Token refreshed successfully")
                        return await download_with_refresh()
                    logger.error(f"Error downloading file {file_id}: {download_error.resp.status} - {download_error._get_reason()}")
                    raise

            except Exception as e:
                if isinstance(e, HttpError) and e.resp.status == 401 and refresh_token:  # Token expired
                    logger.info("Token expired in credentials, attempting to refresh")
                    token_data = await self.refresh_token(refresh_token)
                    access_token = token_data['access_token']
                    logger.info("Token refreshed successfully")
                    return await download_with_refresh()
                logger.error(f"Unexpected error during download: {str(e)}")
                raise

        return await download_with_refresh()

    async def process_file(
        self, 
        access_token: str, 
        refresh_token: Optional[str] = None,
        owner_id: Union[str, UUID] = None, 
        file: dict = None
    ):
        """Process a single Google Drive file to be implemented by the document processor."""
        if not file:
            logger.warning("No file provided to process")
            return

        try:
            logger.info(f"Processing file {file['id']} - {file['name']}")
            
            file_content = await self.download_file(
                access_token=access_token,
                refresh_token=refresh_token,
                file_id=file['id'],
                mime_type=file['mimeType']
            )
            
            if not file_content:
                logger.warning(f"No content retrieved for file {file['id']}")
                return

            # Process the document using document processing service
            # This will be implemented separately
            logger.info(f"File {file['name']} downloaded successfully. Size: {len(file_content)} bytes")
            
            # Return file content and metadata for further processing
            return {
                'content': file_content,
                'metadata': {
                    'filename': file['name'],
                    'file_id': file['id'],
                    'mime_type': file['mimeType'],
                    'web_url': file.get('webUrl', ''),
                    'modified_at': datetime.utcnow().isoformat(),
                    'source': 'google_drive'
                }
            }
            
        except Exception as e:
            logger.error(f"Error processing file {file.get('name', 'unknown')}: {str(e)}")
            traceback.print_exc()
            raise

google_drive_service = GoogleDriveService()