import asyncio
import sys
import os
from sqlalchemy import text

# Add the parent directory to sys.path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.db.session import db_manager

async def verify_constraints():
    async with db_manager.SessionLocal() as session:
        try:
            print("Verifying foreign key constraints with cascade behavior...\n")
            
            query = """
            SELECT
                tc.table_name, 
                kcu.column_name,
                ccu.table_name AS foreign_table_name,
                ccu.column_name AS foreign_column_name,
                rc.delete_rule
            FROM 
                information_schema.table_constraints AS tc 
                JOIN information_schema.key_column_usage AS kcu
                    ON tc.constraint_name = kcu.constraint_name
                    AND tc.table_schema = kcu.table_schema
                JOIN information_schema.constraint_column_usage AS ccu
                    ON ccu.constraint_name = tc.constraint_name
                    AND ccu.table_schema = tc.table_schema
                JOIN information_schema.referential_constraints AS rc
                    ON rc.constraint_name = tc.constraint_name
            WHERE tc.constraint_type = 'FOREIGN KEY'
            ORDER BY tc.table_name, kcu.column_name;
            """
            
            result = await session.execute(text(query))
            constraints = result.fetchall()
            
            print(f"Found {len(constraints)} foreign key constraints:")
            print("=" * 80)
            print(f"{'Table':<25} {'Column':<20} {'References':<25} {'On Delete':<10}")
            print("-" * 80)
            
            for row in constraints:
                table_name = row[0]
                column_name = row[1]
                foreign_table = row[2]
                foreign_column = row[3]
                delete_rule = row[4]
                
                print(f"{table_name:<25} {column_name:<20} {foreign_table}.{foreign_column:<25} {delete_rule:<10}")
            
            print("=" * 80)
            
        except Exception as e:
            print(f"Error: {e}")
            await session.rollback()
            raise

if __name__ == "__main__":
    asyncio.run(verify_constraints())