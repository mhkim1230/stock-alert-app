import sys
import os
import logging
from typing import List, Dict, Any
import asyncio

# 프로젝트 루트 경로 추가
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.models.database import (
    database,
    User, DeviceToken, 
    CurrencyAlert, StockAlert, 
    NewsAlert, NotificationLog,
    Base, initialize_database
)
from src.services.auth_service import AuthService

# 로깅 설정
logging.basicConfig(
    level=logging.INFO, 
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def create_initial_users() -> List[User]:
    """
    초기 사용자 생성
    
    :return: 생성된 사용자 목록
    """
    auth_service = AuthService()
    initial_users = [
        {
            'username': 'admin',
            'email': 'admin@stockalert.com',
            'password': 'AdminPass123!'
        },
        {
            'username': 'testuser',
            'email': 'testuser@stockalert.com', 
            'password': 'TestUser456!'
        }
    ]
    
    created_users = []
    for user_data in initial_users:
        try:
            # 사용자 생성
            user = User.create(
                username=user_data['username'],
                email=user_data['email'],
                password_hash=auth_service.get_password_hash(user_data['password']),
                is_active=True
            )
            created_users.append(user)
            logger.info(f"사용자 생성: {user.username}")
        except Exception as e:
            logger.error(f"사용자 생성 실패: {user_data['username']} - {e}")
    
    return created_users

def create_sample_alerts(users: List[User]):
    """
    샘플 알림 생성
    
    :param users: 알림을 생성할 사용자 목록
    """
    # 환율 알림 샘플
    currency_alerts = [
        {
            'user': users[0],
            'base_currency': 'USD',
            'target_currency': 'KRW',
            'target_rate': 1300.00,
            'condition': 'above'
        },
        {
            'user': users[1],
            'base_currency': 'EUR',
            'target_currency': 'USD',
            'target_rate': 1.10,
            'condition': 'below'
        }
    ]
    
    # 주식 알림 샘플
    stock_alerts = [
        {
            'user': users[0],
            'stock_symbol': 'AAPL',
            'target_price': 200.00,
            'condition': 'above'
        },
        {
            'user': users[1],
            'stock_symbol': 'GOOGL',
            'target_price': 150.00,
            'condition': 'below'
        }
    ]
    
    # 뉴스 알림 샘플
    news_alerts = [
        {
            'user': users[0],
            'keywords': '기술,혁신,스타트업',
            'is_active': True
        },
        {
            'user': users[1],
            'keywords': '금융,투자,경제',
            'is_active': True
        }
    ]
    
    try:
        # 환율 알림 생성
        for alert_data in currency_alerts:
            CurrencyAlert.create(**alert_data)
        logger.info("환율 알림 샘플 생성 완료")
        
        # 주식 알림 생성
        for alert_data in stock_alerts:
            StockAlert.create(**alert_data)
        logger.info("주식 알림 샘플 생성 완료")
        
        # 뉴스 알림 생성
        for alert_data in news_alerts:
            NewsAlert.create(**alert_data)
        logger.info("뉴스 알림 샘플 생성 완료")
    
    except Exception as e:
        logger.error(f"알림 샘플 생성 중 오류 발생: {e}")

async def run_migrations():
    """
    데이터베이스 마이그레이션 및 초기 데이터 설정
    """
    try:
        # 데이터베이스 초기화
        await initialize_database()
        
        # 초기 사용자 생성
        initial_users = create_initial_users()
        
        # 샘플 알림 생성
        create_sample_alerts(initial_users)
        
        logger.info("마이그레이션 및 초기 데이터 설정 완료")
    
    except Exception as e:
        logger.error(f"마이그레이션 중 오류 발생: {e}")
    
    finally:
        # 데이터베이스 연결 종료
        await database['engine'].dispose()

if __name__ == "__main__":
    asyncio.run(run_migrations()) 