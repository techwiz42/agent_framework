import asyncio
import logging
import json
import sys
from app.services.redis.redis_service import redis_service
from app.services.redis.worker import Queues
from uuid import uuid4, UUID
from datetime import datetime

logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

async def process_task_manually(task_data):
    """Process the task manually to debug the handler."""
    logger.info(f"Processing task manually: {json.dumps(task_data)[:200]}...")
    
    # Import the worker components
    from app.services.redis.agent_task_worker import agent_task_worker
    
    # Process the task directly using the handler
    logger.info("Calling agent_task_worker.process_agent_task...")
    try:
        await agent_task_worker.process_agent_task(task_data)
        logger.info("✅ Task processing completed successfully")
        return True
    except Exception as e:
        logger.error(f"❌ Error processing task: {e}")
        import traceback
        traceback.print_exc()
        return False

async def debug_worker():
    """Debug the worker by creating and manually processing a test task."""
    try:
        # Create a unique conversation ID for testing
        conversation_id = str(uuid4())
        
        # Create a test agent task
        test_agent_task = {
            "task_type": "agent_response",
            "conversation_id": conversation_id,
            "thread_id": conversation_id,
            "owner_id": str(uuid4()),
            "user_email": "debug@example.com",
            "message_content": "This is a debug test message",
            "agent_types": ["MODERATOR"],
            "privacy_enabled": False,
            "timestamp": datetime.utcnow().isoformat(),
            "mention": None
        }
        
        logger.info("=== WORKER DEBUG TEST ===")
        logger.info(f"Test conversation ID: {conversation_id}")
        
        # Process the task manually
        logger.info("Manually processing task...")
        await process_task_manually(test_agent_task)
        
    except Exception as e:
        logger.error(f"Error in debug process: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(debug_worker())