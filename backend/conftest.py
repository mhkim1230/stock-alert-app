import pytest
import os
import tempfile
from unittest.mock import Mock, MagicMock
from src.models.database import database, User, CurrencyAlert, StockAlert, NewsAlert, NotificationLog, DeviceToken

@pytest.fixture(scope="session")
def test_database():
    """테스트용 임시 SQLite 데이터베이스 설정"""
    # 임시 데이터베이스 파일 생성
    temp_db = tempfile.NamedTemporaryFile(delete=False, suffix='.db')
    temp_db.close()
    
    # 기존 데이터베이스 연결을 임시 데이터베이스로 변경
    database.init(':memory:')  # 메모리 데이터베이스 사용
    
    try:
        # 테이블 생성
        database.create_tables([
            User, DeviceToken, 
            CurrencyAlert, StockAlert, 
            NewsAlert, NotificationLog
        ])
        
        yield database
        
    finally:
        # 테스트 후 정리
        database.close()
        try:
            os.unlink(temp_db.name)
        except:
            pass

@pytest.fixture
def mock_external_apis():
    """외부 API 호출을 Mock으로 대체"""
    # YFinance Mock
    mock_yf = MagicMock()
    mock_ticker = MagicMock()
    mock_history = MagicMock()
    mock_history.empty = False
    mock_history.iloc = MagicMock()
    mock_history.iloc.__getitem__ = MagicMock(return_value={'Close': 150.25})
    mock_ticker.history.return_value = mock_history
    mock_yf.Ticker.return_value = mock_ticker
    
    # HTTP 요청 Mock
    mock_response = MagicMock()
    mock_response.json.return_value = {'rates': {'USD': 1, 'KRW': 1300}}
    mock_response.status_code = 200
    
    return {
        'yfinance': mock_yf,
        'requests_response': mock_response
    }

@pytest.fixture
def sample_user(test_database):
    """테스트용 샘플 사용자 생성"""
    user = User.create(
        username='testuser',
        email='test@example.com',
        password_hash='hashed_password',
        is_active=True
    )
    return user 