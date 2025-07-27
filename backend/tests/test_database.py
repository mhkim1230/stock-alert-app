import sys
import os
import pytest
import uuid
from datetime import datetime, timedelta

# 프로젝트 루트 경로를 시스템 경로에 추가
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from src.models.database import (
    User, 
    CurrencyAlert,
    StockAlert,
    NewsAlert,
    NotificationLog,
    DeviceToken,
    initialize_database,
    database
)
from src.services.database_service import DatabaseService

@pytest.fixture(scope="module")
def setup_database():
    """테스트용 데이터베이스 설정"""
    # 테스트 데이터베이스 초기화
    initialize_database()
    
    # 데이터베이스 연결
    db = get_db()
    db.connect()
    
    yield db
    
    # 테스트 후 데이터베이스 연결 종료
    db.close()

@pytest.fixture(scope='module')
def setup_test_database():
    """테스트용 데이터베이스 설정"""
    # 테스트 데이터베이스 경로 설정
    test_db_path = os.path.join(
        os.path.dirname(os.path.dirname(__file__)), 
        'test_stock_alert.db'
    )
    
    # 기존 테스트 데이터베이스 삭제
    if os.path.exists(test_db_path):
        os.remove(test_db_path)
    
    # 데이터베이스 연결 및 테이블 생성
    database.initialize(database)
    database.connect()
    database.create_tables([
        User, Stock, StockAlert, 
        CurrencyAlert, NewsAlert, NotificationLog
    ])
    
    yield
    
    # 테스트 후 데이터베이스 정리
    database.drop_tables([
        User, Stock, StockAlert, 
        CurrencyAlert, NewsAlert, NotificationLog
    ])
    database.close()

@pytest.fixture
def sample_user(setup_test_database):
    """샘플 사용자 생성"""
    return User.create(
        username='testuser',
        email='test@example.com',
        password_hash='hashed_password',
        is_active=True
    )

def test_user_creation(setup_database):
    """사용자 생성 테스트"""
    # 새로운 사용자 생성
    user = DatabaseService.create_user(
        username="testuser", 
        email="test@example.com", 
        password="testpassword"
    )
    
    # 사용자 검증
    assert user is not None
    assert user.username == "testuser"
    assert user.email == "test@example.com"
    assert DatabaseService.verify_password("testpassword", user.password_hash)

def test_duplicate_user_creation(setup_database):
    """중복 사용자 생성 방지 테스트"""
    # 첫 번째 사용자 생성
    DatabaseService.create_user(
        username="uniqueuser", 
        email="unique@example.com", 
        password="testpassword"
    )
    
    # 동일한 이메일로 사용자 생성 시도 (예외 발생 예상)
    with pytest.raises(ValueError, match="이미 존재하는 이메일 또는 사용자명입니다."):
        DatabaseService.create_user(
            username="anotheruser", 
            email="unique@example.com", 
            password="anotherpassword"
        )

def test_user_authentication(setup_database):
    """사용자 인증 테스트"""
    # 사용자 생성
    DatabaseService.create_user(
        username="authuser", 
        email="auth@example.com", 
        password="correctpassword"
    )
    
    # 올바른 자격 증명으로 인증
    authenticated_user = DatabaseService.authenticate_user(
        email="auth@example.com", 
        password="correctpassword"
    )
    assert authenticated_user is not None
    
    # 잘못된 비밀번호로 인증 시도
    failed_auth = DatabaseService.authenticate_user(
        email="auth@example.com", 
        password="wrongpassword"
    )
    assert failed_auth is None

def test_stock_watchlist_management(setup_database):
    """주식 관심 종목 관리 테스트"""
    # 사용자 생성
    user = DatabaseService.create_user(
        username="watchlistuser", 
        email="watchlist@example.com", 
        password="testpassword"
    )
    
    # 주식 관심 종목 추가
    DatabaseService.add_stock_to_watchlist(user.id, "AAPL")
    DatabaseService.add_stock_to_watchlist(user.id, "GOOGL")
    
    # 사용자의 관심 종목 조회
    watchlist = DatabaseService.get_user_stock_watchlist(user.id)
    assert set(watchlist) == {"AAPL", "GOOGL"}
    
    # 주식 관심 종목 제거
    DatabaseService.remove_stock_from_watchlist(user.id, "AAPL")
    
    # 제거 후 관심 종목 조회
    updated_watchlist = DatabaseService.get_user_stock_watchlist(user.id)
    assert updated_watchlist == ["GOOGL"]

def test_stock_creation(sample_user):
    """주식 모델 생성 테스트"""
    stock = Stock.create(
        user=sample_user,
        symbol='AAPL',
        name='Apple Inc.',
        current_price=150.25,
        target_price=160.00
    )
    
    assert stock.symbol == 'AAPL'
    assert stock.name == 'Apple Inc.'
    assert float(stock.current_price) == 150.25
    assert float(stock.target_price) == 160.00
    assert stock.user == sample_user

def test_stock_alert_creation(sample_user):
    """주식 알림 생성 테스트"""
    stock = Stock.create(
        user=sample_user,
        symbol='GOOGL',
        name='Alphabet Inc.'
    )
    
    stock_alert = StockAlert.create(
        user=sample_user,
        stock=stock,
        alert_type='price_above',
        threshold=200.00
    )
    
    assert stock_alert.user == sample_user
    assert stock_alert.stock == stock
    assert stock_alert.alert_type == 'price_above'
    assert float(stock_alert.threshold) == 200.00

def test_currency_alert_creation(sample_user):
    """환율 알림 생성 테스트"""
    currency_alert = CurrencyAlert.create(
        user=sample_user,
        base_currency='USD',
        target_currency='KRW',
        alert_type='rate_above',
        threshold=1300.00
    )
    
    assert currency_alert.user == sample_user
    assert currency_alert.base_currency == 'USD'
    assert currency_alert.target_currency == 'KRW'
    assert currency_alert.alert_type == 'rate_above'
    assert float(currency_alert.threshold) == 1300.00

def test_news_alert_creation(sample_user):
    """뉴스 알림 생성 테스트"""
    news_alert = NewsAlert.create(
        user=sample_user,
        keywords='stock,market,tech',
        categories='business,technology'
    )
    
    assert news_alert.user == sample_user
    assert news_alert.keywords == 'stock,market,tech'
    assert news_alert.categories == 'business,technology'

def test_notification_log_creation(sample_user):
    """알림 로그 생성 테스트"""
    notification = NotificationLog.create(
        user=sample_user,
        alert_type='stock',
        message='AAPL stock price reached target'
    )
    
    assert notification.user == sample_user
    assert notification.alert_type == 'stock'
    assert notification.message == 'AAPL stock price reached target'
    assert notification.is_read is False

def test_model_update_timestamp(sample_user):
    """모델 업데이트 타임스탬프 테스트"""
    original_updated_at = sample_user.updated_at
    
    # 약간의 시간 지연
    import time
    time.sleep(0.1)
    
    sample_user.username = 'updateduser'
    sample_user.save()
    
    assert sample_user.username == 'updateduser'
    assert sample_user.updated_at > original_updated_at 