import asyncio
import logging
from concurrent.futures import ThreadPoolExecutor
from functools import partial
from typing import Optional, Union
from uuid import UUID

from app.services.document_processing_service import document_processing_service
from app.services.file_extraction_service import file_extraction_service

logger = logging.getLogger(__name__)

class FileIndexingService:
    def __init__(self, max_workers=5):
        self.executor = ThreadPoolExecutor(max_workers=max_workers)
        self.active_tasks = set()

    async def index_drive_files(
        self, 
        service,  # OneDrive or Google Drive service
        access_token: str, 
        refresh_token: Optional[str] = None,
        owner_id: Optional[Union[str, UUID]] = None
    ):
        try:
            # Run the indexing in a separate thread to prevent blocking
            loop = asyncio.get_running_loop()
            files = await loop.run_in_executor(
                self.executor, 
                partial(
                    service.list_files, 
                    access_token=access_token, 
                    refresh_token=refresh_token
                )
            )

            # Process files with concurrent tasks
            tasks = []
            for file in files:
                task = asyncio.create_task(
                    self._process_file(service, access_token, refresh_token, owner_id, file)
                )
                tasks.append(task)
                self.active_tasks.add(task)
                task.add_done_callback(self.active_tasks.discard)

            # Wait for all tasks with a timeout
            done, pending = await asyncio.wait(tasks, timeout=300)  # 5-minute global timeout

            # Handle any tasks that timed out
            for p in pending:
                p.cancel()

            # Collect results
            processed_files = [t for t in done if not t.exception()]
            failed_files = [t for t in done if t.exception()]

            return {
                'total_files': len(files),
                'processed_files': len(processed_files),
                'failed_files': len(failed_files)
            }

        except Exception as e:
            logger.error(f"File indexing error: {e}")
            raise

    async def _process_file(
        self,
        service,
        access_token: str,
        refresh_token: Optional[str],
        owner_id: Optional[Union[str, UUID]],
        file: dict
    ):
        try:
            logger.info(f"Processing file {file.get('name')} for owner {owner_id}")

            # Use the service's process_file method
            result = await service.process_file(
                access_token=access_token,
                refresh_token=refresh_token,
                owner_id=owner_id,
                file=file
            )

            logger.info(f"Successfully processed file {file.get('name')} for owner {owner_id}")
            return result
        except Exception as e:
            logger.error(f"Error processing file {file.get('name')} for owner {owner_id}: {e}")
            import traceback
            logger.error(traceback.format_exc())
            raise

# Create a singleton instance
file_indexing_service = FileIndexingService()
