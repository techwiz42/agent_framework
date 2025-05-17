import logging
import aiohttp
from typing import Union, Optional, Dict, Any, List
from uuid import UUID
from datetime import datetime
from fastapi import HTTPException

from app.core.config import settings

logger = logging.getLogger(__name__)

SUPPORTED_MIME_TYPES = [
    'text/plain',
    'text/csv',
    'application/pdf',
    'application/msword',
    'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
    'application/vnd.ms-excel',
    'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
    'application/json',
    'text/html',
    'text/markdown'
]

class OneDriveError(Exception):
    def __init__(self, error_type: str, message: str, status_code: int = 500, original_error: Optional[str] = None):
        self.error_type = error_type
        self.message = message
        self.status_code = status_code
        self.original_error = original_error
        super().__init__(self.message)

class OneDriveService:
    base_graph_url = "https://graph.microsoft.com/v1.0"

    async def make_request(
        self,
        url: str,
        access_token: str,
        method: str = "GET",
        data: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None,
        return_raw: bool = False,
        is_download: bool = False
    ) -> Any:
        """Make a request to the Microsoft Graph API or download URL with error handling."""
        try:
            if is_download:
                # For download URLs, don't include the default headers
                base_headers = headers or {}
            else:
                # For Graph API requests, include the authorization header
                base_headers = {
                    "Authorization": f"Bearer {access_token}",
                    "Accept": "application/json"
                }
                if headers:
                    base_headers.update(headers)

            async with aiohttp.ClientSession() as session:
                async with session.request(
                    method,
                    url,
                    headers=base_headers,
                    json=data if method in ["POST", "PUT", "PATCH"] else None
                ) as response:
                    if response.status == 401:
                        error_text = await response.text()
                        logger.error(f"Authentication error: {error_text}")
                        raise OneDriveError(
                            error_type="token_expired",
                            message="Access token has expired",
                            status_code=401,
                            original_error=error_text
                        )
                    
                    if not response.ok:
                        error_text = await response.text()
                        logger.error(f"Request failed with status {response.status}: {error_text}")
                        raise OneDriveError(
                            error_type="request_failed",
                            message=f"Request failed with status {response.status}",
                            status_code=response.status,
                            original_error=error_text
                        )

                    return await response.read() if return_raw else await response.json()

        except OneDriveError:
            raise
        except Exception as e:
            logger.exception("Unexpected error in OneDrive request")
            raise OneDriveError(
                error_type="unexpected_error",
                message=str(e),
                status_code=500,
                original_error=str(e)
            )
            
    async def list_files(
        self,
        access_token: str,
        folder_id: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """List files in OneDrive, optionally filtered by folder."""
        try:
            # Determine the API endpoint based on whether a folder ID is provided
            endpoint = f"{self.base_graph_url}/me/drive/root/children"
            if folder_id:
                if folder_id == "root":
                    endpoint = f"{self.base_graph_url}/me/drive/root/children"
                else:
                    endpoint = f"{self.base_graph_url}/me/drive/items/{folder_id}/children"
            
            logger.info(f"Listing OneDrive files from endpoint: {endpoint}")
            
            # Make the request to Microsoft Graph API
            response = await self.make_request(endpoint, access_token)
            
            # Extract and filter files
            files = response.get("value", [])
            logger.info(f"Retrieved {len(files)} items from OneDrive")
            
            # Filter to only include supported file types
            supported_files = []
            for item in files:
                # Skip folders
                if item.get("folder"):
                    continue
                    
                # For OneDrive, we need to get the contentType or file extension
                file_name = item.get("name", "")
                file_extension = file_name.split(".")[-1].lower() if "." in file_name else ""
                
                # Simple mime type mapping
                mime_map = {
                    "txt": "text/plain",
                    "csv": "text/csv",
                    "pdf": "application/pdf",
                    "doc": "application/msword",
                    "docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                    "xls": "application/vnd.ms-excel",
                    "xlsx": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    "json": "application/json",
                    "html": "text/html",
                    "htm": "text/html",
                    "md": "text/markdown"
                }
                
                # Get mime type from file extension
                mime_type = mime_map.get(file_extension, "application/octet-stream")
                
                # Only include supported mime types
                if mime_type in SUPPORTED_MIME_TYPES:
                    supported_files.append({
                        'id': item.get('id'),
                        'name': item.get('name'),
                        'webUrl': item.get('webUrl', ''),
                        'type': 'file',
                        'mimeType': mime_type
                    })
            
            logger.info(f"Filtered to {len(supported_files)} supported files")
            return supported_files
            
        except OneDriveError:
            raise
        except Exception as e:
            logger.error(f"Error listing OneDrive files: {e}")
            raise OneDriveError(
                error_type="list_files_error",
                message=f"Failed to list OneDrive files: {str(e)}",
                status_code=500
            )

    async def download_file(
        self,
        access_token: str,
        file_id: str
    ) -> bytes:
        """Download a file from OneDrive."""
        try:
            logger.info(f"Downloading file from OneDrive: {file_id}")
            
            # First get the file metadata to get the download URL
            file_info_endpoint = f"{self.base_graph_url}/me/drive/items/{file_id}"
            file_info = await self.make_request(file_info_endpoint, access_token)
            
            # Check if we have a download URL
            download_url = file_info.get('@microsoft.graph.downloadUrl')
            if not download_url:
                logger.error(f"No download URL for file {file_id}")
                raise OneDriveError(
                    error_type="download_url_missing",
                    message="Download URL not available for file",
                    status_code=404
                )
            
            # Download the file content
            file_content = await self.make_request(
                download_url,
                access_token,
                return_raw=True,
                is_download=True  # Indicates this is a download URL request
            )
            
            logger.info(f"Downloaded {len(file_content)} bytes from OneDrive")
            return file_content
            
        except OneDriveError:
            raise
        except Exception as e:
            logger.error(f"Error downloading file from OneDrive: {e}")
            raise OneDriveError(
                error_type="download_error",
                message=f"Failed to download file: {str(e)}",
                status_code=500
            )

    async def process_file(
        self,
        access_token: str,
        file_data: Dict[str, Any],
        owner_id: Union[str, UUID]
    ) -> Dict:
        """Process a single OneDrive file."""
        try:
            logger.info(f"Processing file: {file_data.get('name')}")
            
            # Download the file
            file_content = await self.download_file(
                access_token=access_token,
                file_id=file_data['id']
            )

            if not file_content:
                logger.error(f"No content downloaded for file {file_data.get('name')}")
                return None

            # Return file content and metadata for further processing
            return {
                'content': file_content,
                'metadata': {
                    'filename': file_data['name'],
                    'file_id': file_data['id'],
                    'mime_type': file_data.get('mimeType', 'application/octet-stream'),
                    'web_url': file_data.get('webUrl'),
                    'modified_at': datetime.utcnow().isoformat(),
                    'source': 'onedrive'
                }
            }

        except OneDriveError:
            logger.error(f"OneDrive error processing file {file_data.get('name', 'unknown')}")
            raise
        except Exception as e:
            logger.error(f"Error processing file {file_data.get('name', 'unknown')}: {str(e)}")
            return None

    async def validate_token(self, access_token: str) -> bool:
        """Validate an OneDrive access token by making a test request."""
        try:
            await self.make_request(
                f"{self.base_graph_url}/me",
                access_token
            )
            return True
        except OneDriveError as e:
            if e.error_type == "token_expired":
                return False
            raise
        except Exception:
            return False

# Global service instance
onedrive_service = OneDriveService()