import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from fastapi.testclient import TestClient
from core.database.database import Base, get_db
from backend.main import app
from core.database import models

# Use an in-memory SQLite database for testing
TEST_SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"
engine = create_engine(
    TEST_SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Create all tables in the test database
Base.metadata.create_all(bind=engine)

@pytest.fixture
def db():
    db = TestingSessionLocal()
    # Delete all existing data
    db.query(models.BinPutOut).delete()
    db.query(models.Bin).delete()
    db.query(models.BinDayReplacement).delete()
    db.query(models.Schedule).delete()
    db.commit()

    try:
        yield db
    finally:
        db.close()

@pytest.fixture
def client(db):
    def override_get_db():
        try:
            yield db
        finally:
            db.close()
    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()
