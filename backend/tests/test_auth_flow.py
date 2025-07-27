import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pytest
from sqlalchemy.orm import Session
from src.models.database import engine, Base, User
from src.services.auth_service import AuthService
from datetime import datetime
import uuid
import asyncio

@pytest.fixture
def db_session():
    """Database session fixture"""
    session = Session(engine)
    try:
        yield session
    finally:
        session.close()

@pytest.fixture
def auth_service():
    """AuthService fixture"""
    return AuthService()

@pytest.fixture
def test_user_data():
    """Test user data fixture"""
    return {
        "username": f"testuser_{uuid.uuid4().hex[:8]}",
        "email": f"test_{uuid.uuid4().hex[:8]}@example.com",
        "password": "testpassword123"
    }

async def test_user_registration(db_session, auth_service, test_user_data):
    """Test user registration"""
    try:
        # Register new user
        user = await auth_service.register(
            db_session,
            username=test_user_data["username"],
            email=test_user_data["email"],
            password=test_user_data["password"]
        )
        
        assert user is not None
        assert user.username == test_user_data["username"]
        assert user.email == test_user_data["email"]
        
        # Verify password is hashed
        assert user.password_hash != test_user_data["password"]
        
        print("✅ User registration test passed")
        return user
        
    except Exception as e:
        print(f"❌ User registration test failed: {str(e)}")
        raise

async def test_user_login(db_session, auth_service, test_user_data):
    """Test user login"""
    try:
        # Try to login
        access_token = await auth_service.authenticate_user(
            db_session,
            username=test_user_data["username"],
            password=test_user_data["password"]
        )
        
        assert access_token is not None
        print("✅ User login test passed")
        return access_token
        
    except Exception as e:
        print(f"❌ User login test failed: {str(e)}")
        raise

async def test_token_verification(db_session, auth_service, access_token):
    """Test token verification"""
    try:
        # Verify token
        user = await auth_service.verify_token(db_session, access_token)
        
        assert user is not None
        assert user.username is not None
        print("✅ Token verification test passed")
        
    except Exception as e:
        print(f"❌ Token verification test failed: {str(e)}")
        raise

async def test_invalid_login(db_session, auth_service):
    """Test invalid login attempts"""
    try:
        # Try to login with invalid credentials
        with pytest.raises(ValueError):
            await auth_service.authenticate_user(
                db_session,
                username="nonexistent",
                password="wrongpassword"
            )
        print("✅ Invalid login test passed")
        
    except Exception as e:
        print(f"❌ Invalid login test failed: {str(e)}")
        raise

async def run_auth_tests():
    """Run all authentication tests"""
    session = Session(engine)
    auth_service = AuthService()
    test_data = {
        "username": f"testuser_{uuid.uuid4().hex[:8]}",
        "email": f"test_{uuid.uuid4().hex[:8]}@example.com",
        "password": "testpassword123"
    }
    
    try:
        # Run tests in sequence
        user = await test_user_registration(session, auth_service, test_data)
        access_token = await test_user_login(session, auth_service, test_data)
        await test_token_verification(session, auth_service, access_token)
        await test_invalid_login(session, auth_service)
        
        # Clean up
        session.delete(user)
        session.commit()
        
    finally:
        session.close()

if __name__ == "__main__":
    asyncio.run(run_auth_tests()) 