import asyncio
import sys
import os
from sqlalchemy import text

# Add the parent directory to sys.path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.db.session import db_manager

async def check_users_schema():
    async with db_manager.SessionLocal() as session:
        try:
            # Check users table schema
            result = await session.execute(text("""
                SELECT column_name, data_type, is_nullable
                FROM information_schema.columns
                WHERE table_name='users'
                ORDER BY ordinal_position
            """))
            columns = result.fetchall()
            
            print("Users table schema:")
            for column in columns:
                print(f"Column: {column[0]}, Type: {column[1]}, Nullable: {column[2]}")
        
        except Exception as e:
            print(f"Error: {e}")
            await session.rollback()
            raise

if __name__ == "__main__":
    asyncio.run(check_users_schema())