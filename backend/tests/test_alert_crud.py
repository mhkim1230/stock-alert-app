import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pytest
from sqlalchemy.orm import Session
from src.models.database import engine, Base, User, StockAlert, CurrencyAlert, NewsAlert, Watchlist
from src.services.alert_service import AlertService
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
def alert_service():
    """AlertService fixture"""
    return AlertService()

@pytest.fixture
async def test_user(db_session):
    """Create a test user"""
    auth_service = AuthService()
    username = f"testuser_{uuid.uuid4().hex[:8]}"
    email = f"test_{uuid.uuid4().hex[:8]}@example.com"
    password = "testpassword123"
    
    user = await auth_service.register(db_session, username, email, password)
    return user

@pytest.mark.asyncio
async def test_stock_alert_crud(db_session, alert_service, test_user):
    """Test stock alert CRUD operations"""
    try:
        user = await test_user
        # Create stock alert
        stock_alert = await alert_service.create_stock_alert(
            db_session,
            user_id=user.id,
            symbol="AAPL",
            target_price=150.0,
            condition="above"
        )
        
        assert stock_alert is not None
        assert stock_alert.stock_symbol == "AAPL"
        assert float(stock_alert.target_price) == 150.0
        assert stock_alert.condition == "above"
        
        # Get alerts
        alerts = await alert_service.get_alerts(db_session, user.id)
        assert len(alerts["stock_alerts"]) > 0
        
        # Delete alert
        await alert_service.delete_alert(db_session, stock_alert.id, "stock")
        
        # Verify deletion
        alerts = await alert_service.get_alerts(db_session, user.id)
        assert len([a for a in alerts["stock_alerts"] if a.id == stock_alert.id]) == 0
        
        print("✅ Stock alert CRUD test passed")
        
    except Exception as e:
        print(f"❌ Stock alert CRUD test failed: {str(e)}")
        raise

@pytest.mark.asyncio
async def test_currency_alert_crud(db_session, alert_service, test_user):
    """Test currency alert CRUD operations"""
    try:
        user = await test_user
        # Create currency alert
        currency_alert = await alert_service.create_currency_alert(
            db_session,
            user_id=user.id,
            base_currency="USD",
            target_currency="KRW",
            target_rate=1200.0,
            condition="below"
        )
        
        assert currency_alert is not None
        assert currency_alert.base_currency == "USD"
        assert currency_alert.target_currency == "KRW"
        assert float(currency_alert.target_rate) == 1200.0
        assert currency_alert.condition == "below"
        
        # Get alerts
        alerts = await alert_service.get_alerts(db_session, user.id)
        assert len(alerts["currency_alerts"]) > 0
        
        # Delete alert
        await alert_service.delete_alert(db_session, currency_alert.id, "currency")
        
        # Verify deletion
        alerts = await alert_service.get_alerts(db_session, user.id)
        assert len([a for a in alerts["currency_alerts"] if a.id == currency_alert.id]) == 0
        
        print("✅ Currency alert CRUD test passed")
        
    except Exception as e:
        print(f"❌ Currency alert CRUD test failed: {str(e)}")
        raise

@pytest.mark.asyncio
async def test_news_alert_crud(db_session, alert_service, test_user):
    """Test news alert CRUD operations"""
    try:
        user = await test_user
        # Create news alert
        news_alert = await alert_service.create_news_alert(
            db_session,
            user_id=user.id,
            keywords="AI, Machine Learning"
        )
        
        assert news_alert is not None
        assert news_alert.keywords == "AI, Machine Learning"
        
        # Get alerts
        alerts = await alert_service.get_alerts(db_session, user.id)
        assert len(alerts["news_alerts"]) > 0
        
        # Delete alert
        await alert_service.delete_alert(db_session, news_alert.id, "news")
        
        # Verify deletion
        alerts = await alert_service.get_alerts(db_session, user.id)
        assert len([a for a in alerts["news_alerts"] if a.id == news_alert.id]) == 0
        
        print("✅ News alert CRUD test passed")
        
    except Exception as e:
        print(f"❌ News alert CRUD test failed: {str(e)}")
        raise

@pytest.mark.asyncio
async def test_watchlist_crud(db_session, alert_service, test_user):
    """Test watchlist CRUD operations"""
    try:
        user = await test_user
        # Add to watchlist
        watchlist_item = await alert_service.add_to_watchlist(
            db_session,
            user_id=user.id,
            symbol="GOOGL"
        )
        
        assert watchlist_item is not None
        assert watchlist_item.symbol == "GOOGL"
        
        # Get watchlist
        watchlist = await alert_service.get_watchlist(db_session, user.id)
        assert len(watchlist) > 0
        assert any(item.symbol == "GOOGL" for item in watchlist)
        
        # Remove from watchlist
        await alert_service.remove_from_watchlist(db_session, user.id, "GOOGL")
        
        # Verify removal
        watchlist = await alert_service.get_watchlist(db_session, user.id)
        assert not any(item.symbol == "GOOGL" for item in watchlist)
        
        print("✅ Watchlist CRUD test passed")
        
    except Exception as e:
        print(f"❌ Watchlist CRUD test failed: {str(e)}")
        raise

async def run_alert_tests():
    """Run all alert tests"""
    session = Session(engine)
    alert_service = AlertService()
    
    try:
        # Create test user
        auth_service = AuthService()
        test_user = await auth_service.register(
            session,
            username=f"testuser_{uuid.uuid4().hex[:8]}",
            email=f"test_{uuid.uuid4().hex[:8]}@example.com",
            password="testpassword123"
        )
        
        # Run tests
        await test_stock_alert_crud(session, alert_service, test_user)
        await test_currency_alert_crud(session, alert_service, test_user)
        await test_news_alert_crud(session, alert_service, test_user)
        await test_watchlist_crud(session, alert_service, test_user)
        
        # Clean up
        session.delete(test_user)
        session.commit()
        
    finally:
        session.close()

if __name__ == "__main__":
    asyncio.run(run_alert_tests()) 