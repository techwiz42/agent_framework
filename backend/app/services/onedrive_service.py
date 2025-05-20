import logging
import aiohttp
from typing import Union, Optional, Dict, Any, List
from uuid import UUID
from datetime import datetime
from fastapi import HTTPException

from app.services.document_processing_service import document_processing_service
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

    async def process_file(
        self,
        access_token: str,
        file_data: Dict[str, Any],
        owner_id: Union[str, UUID]
    ) -> bool:
        """Process a single OneDrive file."""
        try:
            logger.info(f"Processing file: {file_data}")
            # Extract the download URL correctly
            download_url = file_data.get('@microsoft.graph.downloadUrl')
            if not download_url:
                logger.error(f"No download URL for file {file_data.get('name')}")
                return False

            # Get file content using the download URL without auth header
            file_content = await self.make_request(
                download_url,
                access_token,
                return_raw=True,
                is_download=True  # Indicates this is a download URL request
            )

            if not file_content:
                logger.error(f"No content downloaded for file {file_data.get('name')}")
                return False

            # Process the document
            await document_processing_service.process_document(
                file_content=file_content,
                file_metadata={
                    'filename': file_data['name'],
                    'file_id': file_data['id'],
                    'mime_type': file_data.get('mimeType', 'application/octet-stream'),
                    'web_url': file_data.get('webUrl'),
                    'modified_at': datetime.utcnow().isoformat(),
                    'source': 'onedrive'
                },
                owner_id=owner_id
            )

            logger.info(f"Successfully processed file {file_data['name']}")
            return True

        except OneDriveError as e:
            logger.error(f"OneDrive error processing file {file_data.get('name', 'unknown')}: {str(e)}")
            raise
        except Exception as e:
            logger.error(f"Error processing file {file_data.get('name', 'unknown')}: {str(e)}")
            return False

    async def process_files(
        self,
        access_token: str,
        files: List[Dict[str, Any]],
        owner_id: Union[str, UUID]
    ) -> Dict[str, int]:
        """Process multiple OneDrive files."""
        processed_count = 0
        failed_count = 0

        for file in files:
            try:
                success = await self.process_file(
                    access_token=access_token,
                    file_data=file,
                    owner_id=owner_id
                )
                
                if success:
                    processed_count += 1
                else:
                    failed_count += 1
                    
            except OneDriveError as e:
                if e.error_type == "token_expired":
                    raise  # Propagate token expiration up
                failed_count += 1
                continue
            except Exception:
                failed_count += 1
                continue

        return {
            "processed_count": processed_count,
            "failed_count": failed_count
        }

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
