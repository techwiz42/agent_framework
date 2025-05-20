import asyncio
import aiohttp
import json
from typing import List, Dict

BASE_URL = "http://dev.cyberiad.ai:8001"

async def create_user(session: aiohttp.ClientSession, user_num: int) -> bool:
    username = f"testuser_{user_num}"
    password = f"TestPassword{user_num}!"
    email = f"testuser_{user_num}@example.com"
    
    register_url = f"{BASE_URL}/api/auth/register"
    try:
        async with session.post(register_url, json={
            "username": username,
            "email": email,
            "password": password
        }) as response:
            if response.status == 200:
                print(f"Created user {username}")
                return True
            print(f"Failed to create {username}: {await response.text()}")
            return False
    except Exception as e:
        print(f"Error creating {username}: {e}")
        return False

async def verify_email(session: aiohttp.ClientSession, email: str, token: str) -> bool:
    verify_url = f"{BASE_URL}/api/auth/verify-email/{token}"
    try:
        async with session.get(verify_url) as response:
            return response.status == 200
    except Exception as e:
        print(f"Error verifying {email}: {e}")
        return False

async def create_test_users(start: int, end: int):
    async with aiohttp.ClientSession() as session:
        for i in range(start, end + 1):
            await create_user(session, i)
            await asyncio.sleep(1)  # Rate limit

async def main():
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('start', type=int)
    parser.add_argument('end', type=int)
    args = parser.parse_args()

    await create_test_users(args.start, args.end)

if __name__ == "__main__":
    asyncio.run(main())
