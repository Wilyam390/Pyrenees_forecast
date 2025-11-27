"""
Test configuration and fixtures.
"""
import pytest
import pytest_asyncio
import asyncio
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.pool import StaticPool
from app.db import Base, get_session
from app.main import app

# Use in-memory async SQLite for tests
TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"

# Module-level engine and session
test_engine = None
TestingSessionLocal = None

@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    try:
        loop = asyncio.get_running_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
    yield loop
    loop.close()

@pytest_asyncio.fixture(scope="function", autouse=True)
async def setup_database():
    """
    Set up a fresh test database before each test.
    This runs automatically for every test function.
    """
    global test_engine, TestingSessionLocal
    
    # Create async engine
    test_engine = create_async_engine(
        TEST_DATABASE_URL,
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
        echo=False,
    )
    
    # Create tables
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    # Create session maker
    TestingSessionLocal = async_sessionmaker(
        test_engine,
        class_=AsyncSession,
        expire_on_commit=False,
    )
    
    # Override dependency
    async def override_get_session():
        async with TestingSessionLocal() as session:
            yield session
    
    app.dependency_overrides[get_session] = override_get_session
    
    yield
    
    # Cleanup
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    
    await test_engine.dispose()
    app.dependency_overrides.clear()