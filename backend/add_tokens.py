import asyncio
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.session import db_manager  
from app.models.domain.models import User

async def add_tokens(username: str, tokens: int):
    async with db_manager.SessionLocal() as db:
        result = await db.execute(
            select(User).where(User.username == username)  
        )
        user = result.scalar_one_or_none()

        if not user:
            print(f"User {username} not found")
            return
        
        if user.tokens_purchased is not None:
            user.tokens_purchased += tokens
        else:
            user.tokens_purchased = tokens
        if user.tokens_consumed is None:
            user.tokens_consumed = 0
        await db.commit()
        print(f"Added {tokens} tokens to user {username}")

if __name__ == "__main__":
    username = input("Enter username: ")
    tokens = int(input("Enter number of tokens to add: "))
    asyncio.run(add_tokens(username, tokens))
