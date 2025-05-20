import asyncio
import sys
import os
from sqlalchemy import text

# Add the parent directory to sys.path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.db.session import db_manager

async def cleanup_users_table():
    async with db_manager.SessionLocal() as session:
        try:
            # Make sure we have phone column
            print("Checking users.phone column...")
            result = await session.execute(text("SELECT column_name FROM information_schema.columns WHERE table_name='users' AND column_name='phone'"))
            phone_column = result.fetchall()
            
            if not phone_column:
                print("Adding phone column...")
                await session.execute(text("ALTER TABLE users ADD COLUMN phone VARCHAR NULL"))
                print("Phone column added.")
            else:
                print("Phone column already exists.")
            
            # Check if we have email verification columns to remove
            print("\nChecking for columns to remove...")
            result = await session.execute(text("SELECT column_name FROM information_schema.columns WHERE table_name='users' AND column_name IN ('email_verification_token', 'email_verified', 'email_verification_sent_at')"))
            columns_to_remove = result.fetchall()
            
            if columns_to_remove:
                print(f"Found {len(columns_to_remove)} columns to remove: {[col[0] for col in columns_to_remove]}")
                
                # Remove the constraint if it exists
                try:
                    await session.execute(text("ALTER TABLE users DROP CONSTRAINT IF EXISTS users_email_verification_token_key"))
                    print("Dropped constraint users_email_verification_token_key")
                except Exception as e:
                    print(f"Error dropping constraint: {e}")
                
                # Remove columns
                for col in columns_to_remove:
                    try:
                        await session.execute(text(f"ALTER TABLE users DROP COLUMN {col[0]}"))
                        print(f"Dropped column {col[0]}")
                    except Exception as e:
                        print(f"Error dropping column {col[0]}: {e}")
            else:
                print("No columns to remove.")
            
            await session.commit()
            print("\nCleanup completed successfully!")
            
        except Exception as e:
            print(f"Error: {e}")
            await session.rollback()
            raise

if __name__ == "__main__":
    asyncio.run(cleanup_users_table())