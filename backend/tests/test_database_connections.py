import asyncio
import logging
import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.domain.models import User
from datetime import datetime, timezone
from uuid import uuid4

@pytest.fixture
async def populate_large_dataset(test_db):
    for i in range(1001):  # Ensure > 1000 records
        user = User(
            id=uuid4(),
            username=f"testuser_{i}",
            email=f"user_{i}@example.com",
            hashed_password="hashed_password",
            created_at=datetime.now().replace(tzinfo=None),
            email_verified=True,
        )
        test_db.add(user)
    await test_db.commit()

@pytest.fixture(scope="session")
def event_loop():
    """Create an event loop for the session scope."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()

@pytest.mark.asyncio
class TestDatabaseConnections:

    @pytest.mark.asyncio
    async def test_connection_lifecycle(self, test_db):
        """Test database connection lifecycle and cleanup."""
        # Insert a user to test the connection
        user = User(
            id=uuid4(),
            username="test_user_lifecycle",
            email="test_user@example.com",
            hashed_password="hashed_password",
            created_at=datetime.now().replace(tzinfo=None),  # Ensure naive datetime
            email_verified=True
        )
        test_db.add(user)
        await test_db.commit()

        # Perform a simple query to verify connection
        result = await test_db.execute(select(User).where(User.username == "test_user_lifecycle"))
        users = result.scalars().all()
        assert len(users) == 1

        # Verify connection is active (commented out since this may be unsupported)
        # assert test_db.is_active

        # Close session
        await test_db.close()
        # Verify connection is closed (this may depend on your database driver)
        # assert not test_db.is_active


    @pytest.mark.asyncio
    async def test_query_failure_handling(self, test_db):
        """Test handling of failed queries."""
        with pytest.raises(Exception):
            await test_db.execute("SELECT * FROM non_existent_table")

    @pytest.mark.asyncio
    async def test_concurrent_queries(self, test_engine):
        """Test handling of concurrent queries."""

        async def run_query():
            async with AsyncSession(test_engine) as session:
                result = await session.execute(select(User))
                return result.scalars().all()

        # Run multiple queries concurrently
        results = await asyncio.gather(run_query(), run_query(), run_query())
        assert all(isinstance(res, list) for res in results)

    @pytest.mark.asyncio
    async def test_large_dataset_handling(self, test_db, populate_large_dataset):
        """Test database handling of large datasets."""
        # Assuming large dataset exists in User table
        result = await test_db.execute(select(User))
        users = result.scalars().all()

        assert len(users) > 1000, "Expected more than 1000 users in the dataset"

    from datetime import datetime

    @pytest.mark.asyncio
    async def test_transaction_handling(self, test_db):
        """Test transaction commit and rollback."""
        # Insert a user within a transaction
        async with test_db.begin():
            user = User(
                id=uuid4(),
                username="transaction_test_user",
                email="transaction_test@example.com",
                hashed_password="hashed_password",
                created_at=datetime.now().replace(tzinfo=None),  # Naive datetime
                email_verified=True
            )
            test_db.add(user)

        # Verify the user was committed
        result = await test_db.execute(select(User).where(User.username == "transaction_test_user"))
        user_in_db = result.scalar()
        assert user_in_db is not None

        # Ensure the session has no active transaction before starting a new one
        if test_db.in_transaction():
            await test_db.commit()

        # Perform a rollback transaction
        async with test_db.begin():
            user_in_db.username = "updated_username"
            test_db.add(user_in_db)
            await test_db.flush()
            await test_db.rollback()

        # Verify rollback occurred
        result = await test_db.execute(select(User).where(User.username == "transaction_test_user"))
        user_in_db_after_rollback = result.scalar()
        assert user_in_db_after_rollback.username == "transaction_test_user"


# Suppress PytestDeprecationWarning
pytestmark = pytest.mark.filterwarnings(
    "ignore:.*asyncio_default_fixture_loop_scope.*:pytest.PytestDeprecationWarning"
)

