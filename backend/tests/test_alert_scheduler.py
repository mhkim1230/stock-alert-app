import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pytest
from sqlalchemy.orm import Session
from src.models.database import engine, Base, User, StockAlert, CurrencyAlert, NewsAlert
from src.services.alert_scheduler import AlertScheduler
from src.services.stock_service import StockService
from src.services.currency_service import CurrencyService
from src.services.news_service import NewsService
from src.services.auth_service import AuthService
from datetime import datetime
import uuid
import asyncio
from typing import Optional, Dict, Tuple, List, Any
from sqlalchemy import literal

class MockStockService:
    """Mock stock service for testing"""
    def __init__(self, price_map: Optional[Dict[str, float]] = None):
        self.price_map = price_map or {"AAPL": 150.0, "GOOGL": 2800.0}
    
    async def get_stock_price(self, symbol: str) -> Optional[float]:
        return self.price_map.get(symbol)

class MockCurrencyService:
    """Mock currency service for testing"""
    def __init__(self, rate_map: Optional[Dict[Tuple[str, str], float]] = None):
        self.rate_map = rate_map or {("USD", "KRW"): 1200.0}
    
    async def get_exchange_rate(self, base_currency: str, target_currency: str) -> Optional[float]:
        return self.rate_map.get((base_currency, target_currency))

class MockNewsService:
    """Mock news service for testing"""
    def __init__(self, news_map: Optional[Dict[str, List[Dict[str, str]]]] = None):
        self.news_map = news_map or {
            "AI": [{"title": "AI News 1"}, {"title": "AI News 2"}],
            "Crypto": [{"title": "Crypto News 1"}]
        }
    
    async def search_news(self, keywords: str) -> List[Dict[str, Any]]:
        return self.news_map.get(keywords, [])

@pytest.fixture
def db_session():
    """Database session fixture"""
    session = Session(engine)
    try:
        yield session
    finally:
        session.close()

@pytest.fixture
def mock_services():
    """Mock services fixture"""
    return {
        "stock": MockStockService(),
        "currency": MockCurrencyService(),
        "news": MockNewsService()
    }

@pytest.fixture
def alert_scheduler(mock_services):
    """AlertScheduler fixture"""
    return AlertScheduler(
        stock_service=mock_services["stock"],
        currency_service=mock_services["currency"],
        news_service=mock_services["news"]
    )

@pytest.fixture
async def test_user(db_session):
    """Create a test user"""
    auth_service = AuthService()
    username = f"testuser_{uuid.uuid4().hex[:8]}"
    email = f"test_{uuid.uuid4().hex[:8]}@example.com"
    password = "testpassword123"
    
    user = await auth_service.register(db_session, username, email, password)
    return user

async def test_stock_alert_trigger(db_session, alert_scheduler, test_user):
    """Test stock alert triggering"""
    try:
        # Create stock alert
        alert = StockAlert(
            user_id=test_user.id,
            stock_symbol="AAPL",
            target_price=140.0,  # Below current mock price (150.0)
            condition="above",
            is_active=1
        )
        db_session.add(alert)
        db_session.commit()
        
        # Check alerts
        await alert_scheduler._check_stock_alerts(db_session)
        
        # Verify alert was triggered
        updated_alert = db_session.query(StockAlert).filter_by(id=alert.id).first()
        assert updated_alert is not None
        assert updated_alert.is_active == 0
        assert updated_alert.triggered_at is not None
        
        print("✅ Stock alert trigger test passed")
        
    except Exception as e:
        print(f"❌ Stock alert trigger test failed: {str(e)}")
        raise

async def test_currency_alert_trigger(db_session, alert_scheduler, test_user):
    """Test currency alert triggering"""
    try:
        # Create currency alert
        alert = CurrencyAlert(
            user_id=test_user.id,
            base_currency="USD",
            target_currency="KRW",
            target_rate=1100.0,  # Below current mock rate (1200.0)
            condition="above",
            is_active=1
        )
        db_session.add(alert)
        db_session.commit()
        
        # Check alerts
        await alert_scheduler._check_currency_alerts(db_session)
        
        # Verify alert was triggered
        updated_alert = db_session.query(CurrencyAlert).filter_by(id=alert.id).first()
        assert updated_alert is not None
        assert updated_alert.is_active == 0
        assert updated_alert.triggered_at is not None
        
        print("✅ Currency alert trigger test passed")
        
    except Exception as e:
        print(f"❌ Currency alert trigger test failed: {str(e)}")
        raise

async def test_news_alert_trigger(db_session, alert_scheduler, test_user):
    """Test news alert triggering"""
    try:
        # Create news alert
        alert = NewsAlert(
            user_id=test_user.id,
            keywords="AI",
            is_active=1
        )
        db_session.add(alert)
        db_session.commit()
        
        # Check alerts
        await alert_scheduler._check_news_alerts(db_session)
        
        # Verify alert was updated
        updated_alert = db_session.query(NewsAlert).filter_by(id=alert.id).first()
        assert updated_alert is not None
        assert updated_alert.last_checked is not None
        
        print("✅ News alert trigger test passed")
        
    except Exception as e:
        print(f"❌ News alert trigger test failed: {str(e)}")
        raise

async def test_scheduler_start_stop(db_session, alert_scheduler):
    """Test scheduler start/stop functionality"""
    try:
        # Start scheduler
        await alert_scheduler.start(db_session)
        assert alert_scheduler.is_running is True
        assert alert_scheduler.db is not None
        
        # Stop scheduler
        await alert_scheduler.stop()
        assert alert_scheduler.is_running is False
        assert alert_scheduler.db is None
        
        print("✅ Scheduler start/stop test passed")
        
    except Exception as e:
        print(f"❌ Scheduler start/stop test failed: {str(e)}")
        raise

async def run_scheduler_tests():
    """Run all scheduler tests"""
    session = Session(engine)
    mock_services = {
        "stock": MockStockService(),
        "currency": MockCurrencyService(),
        "news": MockNewsService()
    }
    alert_scheduler = AlertScheduler(
        stock_service=mock_services["stock"],
        currency_service=mock_services["currency"],
        news_service=mock_services["news"]
    )
    
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
        await test_stock_alert_trigger(session, alert_scheduler, test_user)
        await test_currency_alert_trigger(session, alert_scheduler, test_user)
        await test_news_alert_trigger(session, alert_scheduler, test_user)
        await test_scheduler_start_stop(session, alert_scheduler)
        
        # Clean up
        session.delete(test_user)
        session.commit()
        
    finally:
        session.close()

if __name__ == "__main__":
    asyncio.run(run_scheduler_tests()) 