import asyncio
import sys
import os
from sqlalchemy import text

# Add the parent directory to sys.path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.db.session import db_manager

async def update_foreign_keys():
    async with db_manager.SessionLocal() as session:
        try:
            print("Updating foreign keys with CASCADE/SET NULL options...")
            
            # Thread.owner_id FK -> users.id
            try:
                await session.execute(text("ALTER TABLE threads DROP CONSTRAINT IF EXISTS threads_owner_id_fkey"))
                await session.execute(text("ALTER TABLE threads ADD CONSTRAINT threads_owner_id_fkey FOREIGN KEY (owner_id) REFERENCES users(id) ON DELETE CASCADE"))
                print("Updated threads.owner_id -> users.id (CASCADE)")
            except Exception as e:
                print(f"Error updating threads.owner_id constraint: {e}")
            
            # Message FKs
            try:
                await session.execute(text("ALTER TABLE messages DROP CONSTRAINT IF EXISTS messages_thread_id_fkey"))
                await session.execute(text("ALTER TABLE messages ADD CONSTRAINT messages_thread_id_fkey FOREIGN KEY (thread_id) REFERENCES threads(id) ON DELETE CASCADE"))
                print("Updated messages.thread_id -> threads.id (CASCADE)")
            except Exception as e:
                print(f"Error updating messages.thread_id constraint: {e}")
            
            try:
                await session.execute(text("ALTER TABLE messages DROP CONSTRAINT IF EXISTS messages_participant_id_fkey"))
                await session.execute(text("ALTER TABLE messages ADD CONSTRAINT messages_participant_id_fkey FOREIGN KEY (participant_id) REFERENCES thread_participants(id) ON DELETE SET NULL"))
                print("Updated messages.participant_id -> thread_participants.id (SET NULL)")
            except Exception as e:
                print(f"Error updating messages.participant_id constraint: {e}")
            
            try:
                await session.execute(text("ALTER TABLE messages DROP CONSTRAINT IF EXISTS messages_agent_id_fkey"))
                await session.execute(text("ALTER TABLE messages ADD CONSTRAINT messages_agent_id_fkey FOREIGN KEY (agent_id) REFERENCES thread_agents(id) ON DELETE SET NULL"))
                print("Updated messages.agent_id -> thread_agents.id (SET NULL)")
            except Exception as e:
                print(f"Error updating messages.agent_id constraint: {e}")
            
            try:
                await session.execute(text("ALTER TABLE messages DROP CONSTRAINT IF EXISTS messages_parent_id_fkey"))
                await session.execute(text("ALTER TABLE messages ADD CONSTRAINT messages_parent_id_fkey FOREIGN KEY (parent_id) REFERENCES messages(id) ON DELETE SET NULL"))
                print("Updated messages.parent_id -> messages.id (SET NULL)")
            except Exception as e:
                print(f"Error updating messages.parent_id constraint: {e}")
            
            # MessageInfo FK
            try:
                await session.execute(text("ALTER TABLE message_info DROP CONSTRAINT IF EXISTS message_info_message_id_fkey"))
                await session.execute(text("ALTER TABLE message_info ADD CONSTRAINT message_info_message_id_fkey FOREIGN KEY (message_id) REFERENCES messages(id) ON DELETE CASCADE"))
                print("Updated message_info.message_id -> messages.id (CASCADE)")
            except Exception as e:
                print(f"Error updating message_info.message_id constraint: {e}")
            
            # Update alembic version to reflect our changes
            try:
                await session.execute(text("UPDATE alembic_version SET version_num = 'add_cascade_deletes'"))
                print("Updated alembic_version to 'add_cascade_deletes'")
            except Exception as e:
                print(f"Error updating alembic version: {e}")
            
            await session.commit()
            print("\nForeign key updates completed successfully!")
            
        except Exception as e:
            print(f"Error: {e}")
            await session.rollback()
            raise

if __name__ == "__main__":
    asyncio.run(update_foreign_keys())