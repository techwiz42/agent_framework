import asyncio
import logging
from sqlalchemy import select, text
from app.db.session import AsyncSessionLocal, ThreadAgent, Thread

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def check_threads_and_agents():
    """Check for thread agents in the database."""
    try:
        async with AsyncSessionLocal() as db:
            # Check threads
            thread_query = select(Thread).order_by(Thread.created_at.desc()).limit(5)
            thread_result = await db.execute(thread_query)
            threads = thread_result.scalars().all()
            
            print("\nMost recent threads:")
            print("===================")
            for thread in threads:
                print(f"Thread ID: {thread.id}, Title: {thread.title}, Owner: {thread.owner_id}")
            
            # Check thread agents
            agent_query = select(ThreadAgent).order_by(ThreadAgent.created_at.desc()).limit(10)
            agent_result = await db.execute(agent_query)
            agents = agent_result.scalars().all()
            
            print("\nMost recent thread agents:")
            print("========================")
            for agent in agents:
                print(f"Thread ID: {agent.thread_id}, Agent Type: {agent.agent_type}")
            
            # Check thread agent counts
            count_query = text("""
                SELECT COUNT(*), agent_type 
                FROM thread_agents 
                GROUP BY agent_type 
                ORDER BY COUNT(*) DESC
            """)
            count_result = await db.execute(count_query)
            counts = count_result.all()
            
            print("\nAgent type counts:")
            print("=================")
            for count, agent_type in counts:
                print(f"{agent_type}: {count}")
                
            # Check for threads without agents
            no_agent_query = text("""
                SELECT t.id, t.title 
                FROM threads t 
                LEFT JOIN thread_agents ta ON t.id = ta.thread_id 
                WHERE ta.id IS NULL 
                LIMIT 5
            """)
            no_agent_result = await db.execute(no_agent_query)
            no_agents = no_agent_result.all()
            
            print("\nThreads with no agents:")
            print("=====================")
            if no_agents:
                for thread_id, title in no_agents:
                    print(f"Thread ID: {thread_id}, Title: {title}")
            else:
                print("All threads have agents assigned.")
            
    except Exception as e:
        logger.error(f"Error checking threads and agents: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(check_threads_and_agents())