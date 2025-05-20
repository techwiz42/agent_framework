import asyncio
import sys
import os
from sqlalchemy import text

# Add the parent directory to sys.path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.db.session import db_manager

async def add_phone_column():
    async with db_manager.SessionLocal() as session:
        # Check if phone column exists
        try:
            result = await session.execute(text("SELECT column_name FROM information_schema.columns WHERE table_name='users' AND column_name='phone'"))
            columns = result.fetchall()
            
            if not columns:
                print("Adding 'phone' column to users table...")
                await session.execute(text("ALTER TABLE users ADD COLUMN phone VARCHAR NULL"))
                await session.commit()
                print("Column added successfully!")
            else:
                print("Phone column already exists.")
        except Exception as e:
            print(f"Error: {e}")
            await session.rollback()
            raise

if __name__ == "__main__":
    asyncio.run(add_phone_column())