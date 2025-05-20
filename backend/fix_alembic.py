import asyncio
import sys
import os
from sqlalchemy import text

# Add the parent directory to sys.path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.db.session import db_manager

async def fix_alembic_version():
    async with db_manager.SessionLocal() as session:
        try:
            # Check current alembic version
            result = await session.execute(text("SELECT version_num FROM alembic_version"))
            version = result.scalar()
            print(f"Current alembic version: {version}")
            
            if version == '2199999eebd5':
                # Update alembic version to reflect our manual migration
                await session.execute(text("UPDATE alembic_version SET version_num = 'cleanup_migration'"))
                await session.commit()
                print("Updated alembic version to: cleanup_migration")
            else:
                print(f"Unexpected version: {version} - no update performed")
            
        except Exception as e:
            print(f"Error: {e}")
            await session.rollback()
            raise

if __name__ == "__main__":
    asyncio.run(fix_alembic_version())