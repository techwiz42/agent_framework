import asyncio
import sys
import os
from sqlalchemy import text

# Add the parent directory to sys.path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.db.session import db_manager

async def check_alembic_table():
    async with db_manager.SessionLocal() as session:
        try:
            # Check if alembic_version table exists
            result = await session.execute(text("SELECT EXISTS (SELECT FROM information_schema.tables WHERE table_name = 'alembic_version')"))
            table_exists = result.scalar()
            
            if table_exists:
                print("alembic_version table exists")
                
                # Check if there are any rows
                result = await session.execute(text("SELECT COUNT(*) FROM alembic_version"))
                count = result.scalar()
                print(f"Row count: {count}")
                
                if count > 0:
                    # Get the version
                    result = await session.execute(text("SELECT version_num FROM alembic_version"))
                    versions = result.fetchall()
                    print(f"Versions: {versions}")
                else:
                    # Create the version entry
                    print("Creating version entry...")
                    await session.execute(text("INSERT INTO alembic_version (version_num) VALUES ('cleanup_migration')"))
                    await session.commit()
                    print("Version entry created with value 'cleanup_migration'")
            else:
                print("alembic_version table does not exist, creating it...")
                await session.execute(text("""
                    CREATE TABLE alembic_version (
                        version_num VARCHAR(32) NOT NULL, 
                        PRIMARY KEY (version_num)
                    )
                """))
                await session.execute(text("INSERT INTO alembic_version (version_num) VALUES ('cleanup_migration')"))
                await session.commit()
                print("alembic_version table created with version 'cleanup_migration'")
            
        except Exception as e:
            print(f"Error: {e}")
            await session.rollback()
            raise

if __name__ == "__main__":
    asyncio.run(check_alembic_table())