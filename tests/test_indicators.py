import pytest
from fastapi.testclient import TestClient
from main import app
from models import User, Subscription, SubscriptionTier
from database import get_db
from sqlalchemy.orm import sessionmaker
from sqlalchemy import create_engine
from sqlalchemy.pool import StaticPool
import os

# Test database setup
SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def override_get_db():
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()

# Fixtures
@pytest.fixture(scope="module")
def test_client():
    # Create test database tables
    from database import Base
    Base.metadata.create_all(bind=engine)
    
    # Override the database dependency
    app.dependency_overrides[get_db] = override_get_db
    
    with TestClient(app) as client:
        yield client
    
    # Clean up
    Base.metadata.drop_all(bind=engine)

@pytest.fixture(scope="module")
def test_user():
    db = next(override_get_db())
    
    # Create test user
    user = User(
        username="testuser",
        email="test@example.com",
        hashed_password="$2b$12$EixZaYVK1fsbw1ZfbX3OXePaWxn96p36WQoeG6Lruj3vjPGga31lW"  # password: test123
    )
    db.add(user)
    db.commit()
    
    # Create subscription
    subscription = Subscription(
        user_id=user.id,
        tier=SubscriptionTier.PREMIUM
    )
    db.add(subscription)
    db.commit()
    
    return user

def test_get_sma(test_client, test_user):
    # Get auth token
    response = test_client.post(
        "/api/auth/token",
        data={"username": "testuser", "password": "test123"}
    )
    assert response.status_code == 200
    token = response.json()["access_token"]
    
    # Test SMA endpoint
    response = test_client.get(
        "/api/indicators/sma?symbol=AAPL&period=20",
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 200
    data = response.json()
    assert "sma" in data
    assert len(data["sma"]) > 0

def test_get_rsi(test_client, test_user):
    # Get auth token
    response = test_client.post(
        "/api/auth/token",
        data={"username": "testuser", "password": "test123"}
    )
    assert response.status_code == 200
    token = response.json()["access_token"]
    
    # Test RSI endpoint
    response = test_client.get(
        "/api/indicators/rsi?symbol=AAPL&period=14",
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 200
    data = response.json()
    assert "rsi" in data
    assert len(data["rsi"]) > 0

# Add more test cases for other indicators and edge cases
