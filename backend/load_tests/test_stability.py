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

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('websocket_stress_test.log', mode='w')
    ]
)
logger = logging.getLogger(__name__)

TEST_USERS = [
    {"username": f"testuser_{i}", "password": f"TestPassword{i}!", "email": f"testuser_{i}@example.com"}
    for i in range(1, 11)  
]

BASE_URL = "http://dev.cyberiad.ai:8001"
WEBSOCKET_URL = "ws://dev.cyberiad.ai:8001/ws/conversations"

class WebSocketTester:
    def __init__(self, user, test_duration=300):  # 5 minutes per phase
        self.user = user
        self.test_duration = test_duration
        self.start_time = time.time()
        self.rate_multiplier = 1.0  # Will increase by 20% each successful phase
        
        # Metrics tracking
        self.login_attempts = 0
        self.login_successes = 0
        self.websocket_connections = 0
        self.websocket_messages_sent = 0
        self.websocket_messages_received = 0
        self.total_errors = 0
        self.test_cycles = 0
        self.conversation_id = None

    def _log_critical_error(self, message):
        error_message = f"🚨🚨🚨 CRITICAL ERROR 🚨🚨🚨\n{message}\n{'='*50}"
        logger.error(error_message)
        print("\033[91m" + error_message + "\033[0m")

    async def login(self, session):
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
                
                if access_token:
                    self.login_successes += 1
                    logger.debug(f"Successful login for {self.user['username']}")
                
                return access_token

        except Exception as e:
            self._log_critical_error(f"Login exception for {self.user['username']}: {e}")
            logger.error(traceback.format_exc())
            return None

    async def create_conversation(self, session, token):
        try:
            headers = {"Authorization": f"Bearer {token}"}
            
            conversation_data = {
                "title": f"Stability Test Conversation - {self.user['username']}",
                "description": "Automated stability testing",
                "agent_types": ["MODERATOR"]
            }
            
            logger.debug(f"Creating conversation for {self.user['username']}")
            async with session.post(
                f"{BASE_URL}/api/conversations",
                json=conversation_data,
                headers=headers
            ) as response:
                if response.status not in [200, 201]:
                    response_text = await response.text()
                    self._log_critical_error(
                        f"CONVERSATION CREATION FAILED for {self.user['username']}\n"
                        f"Status: {response.status}\n"
                        f"Response: {response_text}"
                    )
                    return None

                response_data = await response.json()
                return response_data.get('id')

        except Exception as e:
            self._log_critical_error(f"Conversation creation error for {self.user['username']}: {e}")
            logger.error(traceback.format_exc())
            return None

    async def test_websocket(self, token, conversation_id):
        connection_id = str(uuid.uuid4())
        try:
            ws_url = (
                f"{WEBSOCKET_URL}/{conversation_id}?"
                f"token={token}&"
                f"connection_id={connection_id}"
            )
            
            async with websockets.connect(ws_url) as websocket:
                self.websocket_connections += 1
                logger.info(f"WebSocket connected for {self.user['username']}")

                message_types = [
                    self._generate_chat_message,
                    self._generate_typing_status,
                    self._generate_privacy_message
                ]

                test_start = time.time()
                message_cycles = 0
                while time.time() - test_start < self.test_duration * self.rate_multiplier:
                    try:
                        message_generator = random.choice(message_types)
                        message = message_generator()

                        await websocket.send(json.dumps(message))
                        self.websocket_messages_sent += 1
                        logger.debug(f"Sent {message['type']} message")

                        try:
                            response = await asyncio.wait_for(
                                websocket.recv(), 
                                timeout=15.0
                            )
                            self.websocket_messages_received += 1
                            logger.debug("Received response")
                        except asyncio.TimeoutError:
                            logger.warning("Response timeout")
                            break

                        await asyncio.sleep(random.uniform(1.0, 3.0))
                        message_cycles += 1

                    except Exception as msg_error:
                        logger.error(f"Message error: {msg_error}")
                        self.total_errors += 1
                        await asyncio.sleep(1)

        except Exception as e:
            self._log_critical_error(f"WebSocket error for {self.user['username']}: {e}")
            logger.error(traceback.format_exc())
            self.total_errors += 1

    def _generate_chat_message(self):
        messages = [
            f"Hello from {self.user['username']}!",
            f"Test message {uuid.uuid4()}",
            "@MODERATOR Please help me",
            "?",
            ">This is a quoted message"
        ]
        return {
            "type": "message",
            "content": random.choice(messages)
        }

    def _generate_typing_status(self):
        return {
            "type": "typing_status",
            "is_typing": random.choice([True, False])
        }

    def _generate_privacy_message(self):
        return {
            "type": "set_privacy",
            "is_private": random.choice([True, False])
        }

    async def run_test_phase(self):
        try:
            async with aiohttp.ClientSession() as session:
                # Login
                token = await self.login(session)
                if not token:
                    return False

                # Create conversation if needed
                if not self.conversation_id:
                    self.conversation_id = await self.create_conversation(session, token)
                    if not self.conversation_id:
                        return False

                # Test WebSocket for full phase duration
                start_time = time.time()
                initial_errors = self.total_errors
                initial_messages = self.websocket_messages_sent

                await self.test_websocket(token, self.conversation_id)
                
                # Check stability criteria:
                # 1. Phase completed full duration
                phase_time = time.time() - start_time
                if phase_time < self.test_duration:
                    logger.error(f"Phase ended early after {phase_time:.1f}s")
                    return False

                # 2. Error rate below threshold 
                new_errors = self.total_errors - initial_errors
                new_messages = self.websocket_messages_sent - initial_messages
                error_rate = new_errors / max(1, new_messages)
                if error_rate > 0.05:  # More than 5% errors
                    logger.error(f"Too many errors: {error_rate:.1%}")
                    return False

                # 3. Message success rate above threshold
                success_rate = self.websocket_messages_received / max(1, self.websocket_messages_sent)
                if success_rate < 0.95:  # Less than 95% success
                    logger.error(f"Success rate too low: {success_rate:.1%}") 
                    return False

                self.test_cycles += 1
                return True

        except Exception as e:
            logger.error(f"Test phase error: {e}")
            logger.error(traceback.format_exc())
            return False

    def get_diagnostics(self):
        return {
            "username": self.user['username'],
            "login_attempts": self.login_attempts,
            "login_successes": self.login_successes,
            "test_cycles": self.test_cycles,
            "websocket_connections": self.websocket_connections,
            "messages_sent": self.websocket_messages_sent,
            "messages_received": self.websocket_messages_received,
            "errors": self.total_errors,
            "conversation_id": self.conversation_id,
            "success_rate": self.websocket_messages_received / max(1, self.websocket_messages_sent)
        }

async def main():
    logger.info(f"Starting WebSocket stability test with {len(TEST_USERS)} users")
    
    testers = [WebSocketTester(user) for user in TEST_USERS]
    max_stable_rate = 1.0

    while True:
        # Run test phase with all testers
        phase_results = await asyncio.gather(
            *[tester.run_test_phase() for tester in testers]
        )
        
        # Check if phase was successful
        if all(phase_results):
            current_rate = testers[0].rate_multiplier
            max_stable_rate = current_rate
            logger.info(f"Phase successful at rate multiplier {current_rate:.2f}")
            
            # Increase rate by 20%
            for tester in testers:
                tester.rate_multiplier *= 1.2
        else:
            logger.info(f"Maximum stable rate found: {max_stable_rate:.2f}x base rate")
            break

        # Print diagnostics for each tester
        logger.info("\n📊 Tester Diagnostics 📊")
        for tester in testers:
            diag = tester.get_diagnostics()
            logger.info(f"\nUser: {diag['username']}")
            for key, value in diag.items():
                if key != 'username':
                    logger.info(f"  {key}: {value}")

    logger.info("Stability test completed")

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nTest interrupted by user")
