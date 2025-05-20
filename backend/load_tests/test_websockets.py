import asyncio
import aiohttp
import websockets
import random
import uuid
import json
import time
import logging
import traceback
import sys

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,  # Changed to DEBUG for more verbose output
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('websocket_stress_test.log', mode='w')
    ]
)
logger = logging.getLogger(__name__)

# Test users configuration
TEST_USERS = [
    {"username": f"testuser_{i}", "password": f"TestPassword{i}!", "email": f"testuser_{i}@example.com"}
    for i in range(1, 31)
]

# Server configuration
BASE_URL = "http://dev.cyberiad.ai:8001"
WEBSOCKET_URL = "ws://dev.cyberiad.ai:8001/ws/conversations"

class WebSocketTester:
    def __init__(self, user, test_duration=300):
        self.user = user
        self.test_duration = test_duration
        self.start_time = time.time()
        
        # Tracking for detailed diagnostics
        self.login_attempts = 0
        self.login_successes = 0
        self.websocket_connections = 0
        self.websocket_messages_sent = 0
        self.websocket_messages_received = 0
        self.total_errors = 0
        self.test_cycles = 0
        # Store user's conversation for repeated testing
        self.conversation_id = None
        # Store access token for cleanup
        self.access_token = None

    def _log_critical_error(self, message):
        """Log a critical error with maximum visibility"""
        error_message = f"🚨🚨🚨 CRITICAL ERROR 🚨🚨🚨\n{message}\n{'='*50}"
        logger.error(error_message)
        print("\033[91m" + error_message + "\033[0m")  # Red color in terminal

    async def login(self, session):
        """Obtain authentication token"""
        self.login_attempts += 1
        try:
            login_url = f"{BASE_URL}/api/auth/token"
            logger.debug(f"Attempting login for {self.user['username']} at {login_url}")
            async with session.post(
                login_url, 
                data={
                    "username": self.user['username'],
                    "password": self.user['password']
                }
            ) as response:
                logger.debug(f"Login response status: {response.status}")
                
                if response.status != 200:
                    response_text = await response.text()
                    self._log_critical_error(
                        f"LOGIN FAILED for {self.user['username']}\n"
                        f"Status: {response.status}\n"
                        f"Response: {response_text}"
                    )
                    return None

                response_data = await response.json()
                access_token = response_data.get('access_token')
                
                if not access_token:
                    logger.error(f"No access token received for {self.user['username']}")
                    return None
                
                self.login_successes += 1
                self.access_token = access_token  # Store token for cleanup
                logger.debug(f"Successful login for {self.user['username']}")
                return access_token

        except Exception as e:
            self._log_critical_error(f"Login exception for {self.user['username']}: {e}")
            logger.error(traceback.format_exc())
            return None

    async def create_conversation(self, session, token):
        """Create a conversation for the user"""
        try:
            headers = {"Authorization": f"Bearer {token}"}
            conversation_url = f"{BASE_URL}/api/conversations"
            
            # Create conversation with minimal participants
            conversation_data = {
                "title": f"WebSocket Stress Test Conversation for {self.user['username']}",
                "description": f"Automated conversation for WebSocket testing",
                "agent_types": ["MODERATOR"]
            }
            
            logger.debug(f"Creating conversation for {self.user['username']}")
            async with session.post(
                conversation_url, 
                json=conversation_data,
                headers=headers
            ) as response:
                logger.debug(f"Conversation creation response status: {response.status}")
                
                if response.status not in [200, 201]:
                    response_text = await response.text()
                    self._log_critical_error(
                        f"CONVERSATION CREATION FAILED for {self.user['username']}\n"
                        f"Status: {response.status}\n"
                        f"Response: {response_text}"
                    )
                    return None

                response_data = await response.json()
                conversation_id = response_data.get('id')
                
                logger.info(f"Successfully created conversation {conversation_id} for {self.user['username']}")
                return conversation_id

        except Exception as e:
            self._log_critical_error(f"Conversation creation exception for {self.user['username']}: {e}")
            logger.error(traceback.format_exc())
            return None

    async def test_websocket(self, token, conversation_id):
        """Perform WebSocket stress testing for a conversation"""
        connection_id = str(uuid.uuid4())
        try:
            # Construct WebSocket URL with query parameters
            ws_url = (
                f"{WEBSOCKET_URL}/{conversation_id}?"
                f"token={token}&"
                f"connection_id={connection_id}"
            )

            logger.debug(f"Attempting WebSocket connection: {ws_url}")
            
            # Add a connection timeout
            async with websockets.connect(ws_url, open_timeout=30) as websocket:
                self.websocket_connections += 1
                logger.info(f"WebSocket connected for {self.user['username']} to conversation {conversation_id}")
                
                # Wait a moment after connection to ensure server is ready
                await asyncio.sleep(1)
                
                # First, try to receive any initial messages from the server
                try:
                    initial_message = await asyncio.wait_for(websocket.recv(), timeout=2.0)
                    self.websocket_messages_received += 1
                    logger.debug(f"Received initial message for {self.user['username']}: {initial_message[:100]}...")
                except asyncio.TimeoutError:
                    logger.debug(f"No initial message received for {self.user['username']}")

                # Message types and generation functions
                message_types = [
                    self._generate_chat_message,
                    self._generate_typing_status,
                    self._generate_privacy_message
                ]

                test_start = time.time()
                message_cycles = 0
                while time.time() - test_start < 300 and message_cycles < 5:  # Limit to 5 minutes or 5 messages
                    try:
                        # Randomly choose message type
                        message_generator = random.choice(message_types)
                        message = message_generator()

                        # Send message
                        await websocket.send(json.dumps(message))
                        self.websocket_messages_sent += 1
                        message_cycles += 1
                        logger.debug(f"Sent {message['type']} message for {self.user['username']}")

                        # Wait longer after sending a message to let server process it
                        await asyncio.sleep(random.uniform(1.0, 3.0))

                        # Check for incoming messages with a more generous timeout
                        try:
                            message = await asyncio.wait_for(
                                websocket.recv(), 
                                timeout=10.0
                            )
                            self.websocket_messages_received += 1
                            logger.debug(f"Received message for {self.user['username']}")
                        except asyncio.TimeoutError:
                            # No message received, continue
                            logger.debug(f"No message received for {self.user['username']}")
                            pass
                        
                        # Add small pause between message cycles
                        await asyncio.sleep(2.0)

                    except Exception as msg_error:
                        logger.error(f"Message sending error for {self.user['username']}: {msg_error}")
                        self.total_errors += 1
                        await asyncio.sleep(5)

                logger.info(f"WebSocket test completed for {self.user['username']}: {message_cycles} messages")

        except Exception as e:
            self._log_critical_error(f"WebSocket error for {self.user['username']}: {e}")
            logger.error(traceback.format_exc())
            self.total_errors += 1

    async def delete_user(self, session):
        """Delete the test user after testing is complete"""
        if not self.access_token:
            logger.warning(f"No access token available to delete user {self.user['username']}")
            return False
        
        try:
            # We're assuming there's an admin API endpoint to delete users
            # Adjust the URL and method according to your actual API
            headers = {"Authorization": f"Bearer {self.access_token}"}
            delete_url = f"{BASE_URL}/api/admin/users/{self.user['username']}"
            
            logger.info(f"Attempting to delete test user: {self.user['username']}")
            async with session.delete(delete_url, headers=headers) as response:
                if response.status in [200, 204]:
                    logger.info(f"Successfully deleted user: {self.user['username']}")
                    return True
                else:
                    response_text = await response.text()
                    logger.warning(
                        f"Failed to delete user {self.user['username']}\n"
                        f"Status: {response.status}\n"
                        f"Response: {response_text}"
                    )
                    return False
        except Exception as e:
            logger.error(f"Error deleting user {self.user['username']}: {e}")
            logger.error(traceback.format_exc())
            return False

    def _generate_chat_message(self):
        """Generate a random chat message"""
        message_variants = [
            f"Hello from {self.user['username']}!",
            f"Random test message: {uuid.uuid4()}",
            "@MODERATOR Please help me",
            "?",  # Help command
            ">This is a quoted message"
        ]
        return {
            "type": "message",
            "content": random.choice(message_variants)
        }

    def _generate_typing_status(self):
        """Generate a typing status update"""
        return {
            "type": "typing_status",
            "is_typing": random.choice([True, False])
        }

    def _generate_privacy_message(self):
        """Generate a privacy setting message"""
        return {
            "type": "set_privacy",
            "is_private": random.choice([True, False])
        }

    async def run_test_cycle(self):
        """Full test cycle: login, create conversation, test WebSocket"""
        logger.debug(f"Starting test cycle for {self.user['username']}")
        while time.time() - self.start_time < self.test_duration:
            try:
                async with aiohttp.ClientSession() as session:
                    # Login
                    token = await self.login(session)
                    if not token:
                        logger.debug(f"Login failed for {self.user['username']}, retrying...")
                        await asyncio.sleep(5)
                        continue

                    # Create conversation if not already created
                    if not self.conversation_id:
                        self.conversation_id = await self.create_conversation(session, token)
                        if not self.conversation_id:
                            logger.debug(f"Conversation creation failed for {self.user['username']}, retrying...")
                            await asyncio.sleep(5)
                            continue

                    # Test WebSocket with the created conversation
                    await self.test_websocket(token, self.conversation_id)
                    
                    # Increment test cycles
                    self.test_cycles += 1

                    # Increased pause between test cycles
                    await asyncio.sleep(random.uniform(10, 20))

            except Exception as e:
                logger.error(f"Error in test cycle for {self.user['username']}: {e}")
                logger.error(traceback.format_exc())
                await asyncio.sleep(5)

    def get_diagnostics(self):
        """Generate detailed diagnostics for this user tester"""
        return {
            "username": self.user['username'],
            "login_attempts": self.login_attempts,
            "login_successes": self.login_successes,
            "test_cycles": self.test_cycles,
            "websocket_connections": self.websocket_connections,
            "websocket_messages_sent": self.websocket_messages_sent,
            "websocket_messages_received": self.websocket_messages_received,
            "total_errors": self.total_errors,
            "conversation_id": self.conversation_id,
            "login_success_rate": self.login_successes / self.login_attempts if self.login_attempts > 0 else 0,
            "message_success_rate": self.websocket_messages_received / self.websocket_messages_sent if self.websocket_messages_sent > 0 else 0
        }

async def cleanup_test_users(testers):
    """Clean up all test users after testing is complete"""
    logger.info("Starting cleanup of test users...")
    deleted_count = 0
    failed_count = 0
    
    # Try to delete each test user
    async with aiohttp.ClientSession() as session:
        for tester in testers:
            if await tester.delete_user(session):
                deleted_count += 1
            else:
                failed_count += 1
    
    logger.info(f"User cleanup completed: {deleted_count} users deleted, {failed_count} deletion failures")
    return deleted_count, failed_count

async def main():
    """Main test runner"""
    logger.info(f"Starting WebSocket stress test for {len(TEST_USERS)} users")
    
    # Track start time
    overall_start_time = time.time()
    
    # Create testers for each user
    testers = [
        WebSocketTester(user) for user in TEST_USERS
    ]

    try:
        # Run all testers concurrently
        await asyncio.gather(
            *[tester.run_test_cycle() for tester in testers]
        )

        # Calculate overall test duration
        overall_test_duration = time.time() - overall_start_time

        # Aggregate total results
        total_login_attempts = 0
        total_login_successes = 0
        total_test_cycles = 0
        total_websocket_connections = 0
        total_websocket_messages_sent = 0
        total_websocket_messages_received = 0
        total_errors = 0

        # Collect and print individual diagnostics
        logger.info("\n📊 Individual User Diagnostics 📊")
        for tester in testers:
            diag = tester.get_diagnostics()
            logger.info(f"User: {diag['username']}")
            for key, value in diag.items():
                if key != 'username':
                    logger.info(f"  {key}: {value}")
            logger.info("---")

            # Aggregate totals
            total_login_attempts += diag['login_attempts']
            total_login_successes += diag['login_successes']
            total_test_cycles += diag['test_cycles']
            total_websocket_connections += diag['websocket_connections']
            total_websocket_messages_sent += diag['websocket_messages_sent']
            total_websocket_messages_received += diag['websocket_messages_received']
            total_errors += diag['total_errors']

        # Calculate overall performance metrics
        overall_login_success_rate = total_login_successes / total_login_attempts if total_login_attempts > 0 else 0
        overall_message_success_rate = total_websocket_messages_received / total_websocket_messages_sent if total_websocket_messages_sent > 0 else 0
        message_rate = total_websocket_messages_sent / overall_test_duration if overall_test_duration > 0 else 0

        # Print overall results
        logger.info("\n🌐 Overall WebSocket Stress Test Results 🌐")
        logger.info(f"Total Test Duration: {overall_test_duration:.2f} seconds")
        logger.info(f"Total Login Attempts: {total_login_attempts}")
        logger.info(f"Total Login Successes: {total_login_successes}")
        logger.info(f"Login Success Rate: {overall_login_success_rate:.2%}")
        logger.info(f"Total WebSocket Connections: {total_websocket_connections}")
        logger.info(f"Total WebSocket Messages Sent: {total_websocket_messages_sent}")
        logger.info(f"Total WebSocket Messages Received: {total_websocket_messages_received}")
        logger.info(f"WebSocket Message Success Rate: {overall_message_success_rate:.2%}")
        logger.info(f"WebSocket Message Rate: {message_rate:.2f} messages/second")
        logger.info(f"Total Errors: {total_errors}")
    
    finally:
        # Always attempt to clean up users, even if tests fail
        logger.info("\n🧹 Starting Test User Cleanup 🧹")
        deleted_count, failed_count = await cleanup_test_users(testers)
        logger.info(f"Cleanup Summary: {deleted_count}/{len(testers)} users deleted successfully")
        if failed_count > 0:
            logger.warning(f"⚠️ Failed to delete {failed_count} test users")

if __name__ == "__main__":
    # Additional websockets library requirements
    import websockets
    
    # Install Ctrl+C handler
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nTest interrupted by user.")
        print("Attempting user cleanup after interruption...")
        asyncio.run(cleanup_test_users([WebSocketTester(user) for user in TEST_USERS]))
