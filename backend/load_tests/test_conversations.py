import asyncio
import aiohttp
import time
import random
import uuid
from datetime import datetime
import logging
import traceback
import sys

# Configure logging
logging.basicConfig(
    level=logging.INFO, 
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('conversation_stress_test.log')
    ]
)
logger = logging.getLogger(__name__)

# Test users configuration
TEST_USERS = [
    {"username": f"testuser_{i}", "password": f"TestPassword{i}!", "email": f"testuser_{i}@example.com"}
    for i in range(1, 11)
]

# Specific base URL with port
BASE_URL = "http://dev.cyberiad.ai:8001"

# Endpoint configurations
AUTH_ENDPOINT = "/api/auth/token"
CONVERSATIONS_ENDPOINT = "/api/conversations"

class ConversationTester:
    def __init__(self, session, user, test_duration=600):
        self.session = session
        self.user = user
        self.access_token = None
        self.test_duration = test_duration
        self.start_time = time.time()
        
        # Tracking for detailed diagnostics
        self.login_attempts = 0
        self.login_successes = 0
        self.conversation_attempts = 0
        self.conversation_successes = 0
        self.deletion_attempts = 0
        self.deletion_successes = 0
        self.total_errors = 0
        self.created_conversations = []

    def _log_critical_error(self, message):
        """Log a critical error with maximum visibility"""
        error_message = f"🚨🚨🚨 CRITICAL ERROR 🚨🚨🚨\n{message}\n{'='*50}"
        logger.error(error_message)
        print("\033[91m" + error_message + "\033[0m")  # Red color in terminal

    async def login(self):
        """Attempt to log in a user"""
        self.login_attempts += 1
        try:
            login_url = f"{BASE_URL}{AUTH_ENDPOINT}"
            async with self.session.post(
                login_url, 
                data={
                    "username": self.user['username'],
                    "password": self.user['password']
                }
            ) as response:
                if response.status != 200:
                    self._log_critical_error(
                        f"LOGIN FAILED for {self.user['username']}\n"
                        f"Status: {response.status}\n"
                        f"Response: {await response.text()}"
                    )
                    return False

                response_data = await response.json()
                self.access_token = response_data.get('access_token')
                self.login_successes += 1
                return True

        except Exception as e:
            self._log_critical_error(f"Login exception for {self.user['username']}: {e}")
            return False

    async def create_conversation(self):
        """Create a conversation with random parameters"""
        if not self.access_token:
            return None

        self.conversation_attempts += 1
        try:
            # Generate unique set of participants, excluding current user
            all_users = [user for user in TEST_USERS if user['email'] != self.user['email']]
            random.shuffle(all_users)
            
            # Select up to 2 additional participants
            participants = random.sample(all_users, min(2, len(all_users)))

            # Random conversation generation
            conversation_data = {
                "title": f"Stress Test Conversation {uuid.uuid4()}",
                "description": f"Automated stress test conversation for {self.user['username']}",
                "agent_types": random.sample(
                    ["MODERATOR", "SUMMARIZER", "QA", "RESEARCHER"], 
                    k=random.randint(0, 3)
                ),
                "participants": [
                    {"email": p['email'], "name": p['username']} for p in participants
                ]
            }

            headers = {"Authorization": f"Bearer {self.access_token}"}
            
            async with self.session.post(
                f"{BASE_URL}{CONVERSATIONS_ENDPOINT}", 
                json=conversation_data,
                headers=headers
            ) as response:
                response_text = await response.text()
                if response.status != 200:
                    self._log_critical_error(
                        f"CONVERSATION CREATION FAILED for {self.user['username']}\n"
                        f"Status: {response.status}\n"
                        f"Participants: {conversation_data['participants']}\n"
                        f"Response: {response_text}"
                    )
                    return None

                try:
                    response_data = await response.json()
                    conversation_id = response_data.get('id')
                    
                    if not conversation_id:
                        self._log_critical_error(
                            f"NO CONVERSATION ID RETURNED for {self.user['username']}\n"
                            f"Response: {response_text}"
                        )
                        return None

                    self.conversation_successes += 1
                    return conversation_id
                except Exception as parse_error:
                    self._log_critical_error(
                        f"FAILED TO PARSE CONVERSATION RESPONSE for {self.user['username']}\n"
                        f"Response: {response_text}\n"
                        f"Parse Error: {parse_error}"
                    )
                    return None

        except Exception as e:
            self._log_critical_error(
                f"Conversation creation exception for {self.user['username']}: {e}"
            )
            return None

    async def delete_conversation(self, conversation_id):
        """Delete a specific conversation"""
        if not self.access_token or not conversation_id:
            return False

        self.deletion_attempts += 1
        try:
            headers = {"Authorization": f"Bearer {self.access_token}"}
            
            async with self.session.delete(
                f"{BASE_URL}{CONVERSATIONS_ENDPOINT}/{conversation_id}", 
                headers=headers
            ) as response:
                if response.status != 204:
                    self._log_critical_error(
                        f"CONVERSATION DELETION FAILED for {self.user['username']}\n"
                        f"Conversation ID: {conversation_id}\n"
                        f"Status: {response.status}\n"
                        f"Response: {await response.text()}"
                    )
                    return False

                self.deletion_successes += 1
                return True

        except Exception as e:
            self._log_critical_error(
                f"Conversation deletion exception for {self.user['username']}: {e}"
            )
            return False

    async def run_test_cycle(self):
        """Continuous conversation creation and deletion cycle"""
        while time.time() - self.start_time < self.test_duration:
            try:
                # Login
                if not await self.login():
                    await asyncio.sleep(random.uniform(1, 3))
                    continue

                # Create multiple conversations
                num_conversations = random.randint(1, 5)
                created_conversations = []
                
                for _ in range(num_conversations):
                    conversation_id = await self.create_conversation()
                    if conversation_id:
                        created_conversations.append(conversation_id)
                    
                    # Random wait between conversation creations
                    await asyncio.sleep(random.uniform(0.5, 2))

                # Wait a bit before deleting
                await asyncio.sleep(random.uniform(2, 5))

                # Delete all created conversations
                for conv_id in created_conversations:
                    await self.delete_conversation(conv_id)
                    
                    # Small wait between deletions
                    await asyncio.sleep(random.uniform(0.5, 1.5))

                # Random wait before next cycle
                await asyncio.sleep(random.uniform(1, 3))

            except Exception as e:
                logger.error(f"Test cycle error for {self.user['username']}: {e}")
                logger.error(traceback.format_exc())
                await asyncio.sleep(1)

    def get_diagnostics(self):
        """Generate detailed diagnostics for this user tester"""
        return {
            "username": self.user['username'],
            "login_attempts": self.login_attempts,
            "login_successes": self.login_successes,
            "conversation_attempts": self.conversation_attempts,
            "conversation_successes": self.conversation_successes,
            "deletion_attempts": self.deletion_attempts,
            "deletion_successes": self.deletion_successes,
            "total_errors": self.total_errors,
            "login_success_rate": self.login_successes / self.login_attempts if self.login_attempts > 0 else 0,
            "conversation_success_rate": self.conversation_successes / self.conversation_attempts if self.conversation_attempts > 0 else 0,
            "deletion_success_rate": self.deletion_successes / self.deletion_attempts if self.deletion_attempts > 0 else 0
        }

async def main():
    """Main test runner"""
    logger.info(f"Starting conversation stress test for {len(TEST_USERS)} users")
    
    # Create a single session to be shared
    async with aiohttp.ClientSession() as session:
        # Create testers for each user
        testers = [
            ConversationTester(session, user) for user in TEST_USERS
        ]

        # Run all testers concurrently
        await asyncio.gather(
            *[tester.run_test_cycle() for tester in testers]
        )

        # Print detailed diagnostics
        logger.info("\n📊 Test Diagnostics 📊")
        for tester in testers:
            diag = tester.get_diagnostics()
            logger.info(f"User: {diag['username']}")
            for key, value in diag.items():
                if key != 'username':
                    logger.info(f"  {key}: {value}")
            logger.info("---")

    logger.info("Conversation stress test completed")

if __name__ == "__main__":
    # Run the async main function
    asyncio.run(main())
