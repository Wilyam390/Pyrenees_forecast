"""
Test configuration and fixtures.
"""
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from app.db import Base, get_session
from app.main import app

TEST_DATABASE_URL = "sqlite:///:memory:"

@pytest.fixture(scope="function", autouse=True)
def setup_test_database():
    """
    Create a fresh test database for each test function.
    This fixture runs automatically for all tests.
    """
    engine = create_engine(
        TEST_DATABASE_URL,
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    
    Base.metadata.create_all(bind=engine)
    
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    
    def override_get_session():
        try:
            db = TestingSessionLocal()
            yield db
        finally:
            db.close()
    
    app.dependency_overrides[get_session] = override_get_session
    
    yield

    Base.metadata.drop_all(bind=engine)
    app.dependency_overrides.clear()