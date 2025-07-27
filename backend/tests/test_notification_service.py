import os
import asyncio
import unittest
from unittest.mock import patch, MagicMock, AsyncMock
from datetime import datetime, timedelta

from src.services.notification_service import NotificationService
from src.services.alert_scheduler import AlertScheduler
from src.models.database import (
    User, Stock, StockAlert, 
    CurrencyAlert, NewsAlert, 
    NotificationLog, database
)

class TestNotificationService(unittest.TestCase):
    def setUp(self):
        """각 테스트 전 설정"""
        # 테스트 데이터베이스 테이블 생성
        database.connect()
        database.create_tables([
            User, Stock, StockAlert, 
            CurrencyAlert, NewsAlert, 
            NotificationLog
        ])

        # 샘플 사용자 생성
        self.user = User.create(
            username='testuser',
            email='test@example.com',
            password_hash='hashed_password',
            is_active=True
        )

    def tearDown(self):
        """각 테스트 후 정리"""
        # 테이블 삭제 및 데이터베이스 연결 종료
        database.drop_tables([
            User, Stock, StockAlert, 
            CurrencyAlert, NewsAlert, 
            NotificationLog
        ])
        database.close()

    def _create_mock_notification_service(self):
        """모의 알림 서비스 생성"""
        with patch('src.services.notification_service.NewsService') as MockNewsService, \
             patch('src.services.notification_service.StockService') as MockStockService, \
             patch('src.services.notification_service.CurrencyService') as MockCurrencyService:
            
            # 모의 서비스 설정
            mock_news_service = MockNewsService.return_value
            mock_stock_service = MockStockService.return_value
            mock_currency_service = MockCurrencyService.return_value
            
            # 알림 서비스 생성
            service = NotificationService(
                news_api_key='test_api_key', 
                stock_service=mock_stock_service,
                currency_service=mock_currency_service
            )
            
            return service, {
                'news_service': mock_news_service,
                'stock_service': mock_stock_service,
                'currency_service': mock_currency_service
            }

    def test_stock_alert_condition_above(self):
        """주식 가격 이상 알림 조건 테스트"""
        service, mocks = self._create_mock_notification_service()
        
        # 테스트용 주식 및 알림 생성
        stock = Stock.create(
            user=self.user,
            symbol='AAPL',
            name='Apple Inc.',
            current_price=150.00
        )
        
        stock_alert = StockAlert.create(
            user=self.user,
            stock=stock,
            alert_type='price_above',
            threshold=140.00
        )
        
        # 모의 주식 데이터 설정
        mocks['stock_service'].get_stock_data.return_value = {
            'symbol': 'AAPL',
            'current_price': 150.25
        }
        
        # 알림 확인 (비동기 메서드 처리)
        alerts = asyncio.run(service.check_stock_alerts())
        
        self.assertEqual(len(alerts), 1)
        alert = alerts[0]
        self.assertEqual(alert['stock_symbol'], 'AAPL')
        self.assertIn('notification_id', alert)

    def test_currency_alert_condition_above(self):
        """환율 이상 알림 조건 테스트"""
        service, mocks = self._create_mock_notification_service()
        
        # 테스트용 환율 알림 생성
        currency_alert = CurrencyAlert.create(
            user=self.user,
            base_currency='USD',
            target_currency='KRW',
            alert_type='rate_above',
            threshold=1250.00
        )
        
        # 모의 환율 데이터 설정
        mocks['currency_service'].get_exchange_rate.return_value = 1260.50
        
        # 알림 확인 (비동기 메서드 처리)
        alerts = asyncio.run(service.check_currency_alerts())
        
        self.assertEqual(len(alerts), 1)
        alert = alerts[0]
        self.assertEqual(alert['currency_pair'], 'USD/KRW')
        self.assertIn('notification_id', alert)

    def test_news_alert_keyword_match(self):
        """뉴스 키워드 알림 테스트"""
        service, mocks = self._create_mock_notification_service()
        
        # 테스트용 뉴스 알림 생성
        news_alert = NewsAlert.create(
            user=self.user,
            keywords='stock,market',
            categories='business'
        )
        
        # 모의 뉴스 데이터 설정 (키워드 및 비즈니스 포함)
        mocks['news_service'].get_news_by_category.return_value = [
            {
                'title': 'Stock Market Trends in Business Sector',
                'description': 'Latest developments in the stock market and business world',
                'link': 'http://example.com/news1',
                'published_at': '2023-01-01T00:00:00Z'
            }
        ]
        
        # 알림 확인 (비동기 메서드 처리)
        alerts = asyncio.run(service.check_news_alerts())
        
        self.assertEqual(len(alerts), 1)
        alert = alerts[0]
        self.assertEqual(alert['news_count'], 1)
        self.assertIn('notification_id', alert)

    def test_alert_scheduler_basic_functionality(self):
        """알림 스케줄러 기본 기능 테스트"""
        service, _ = self._create_mock_notification_service()
        
        # 알림 스케줄러 생성
        scheduler = AlertScheduler(service, interval=1)
        
        # 모의 process_all_alerts 메서드 설정
        async def mock_process_all_alerts():
            return {
                'stock_alerts': [],
                'currency_alerts': [],
                'news_alerts': []
            }
        
        with patch.object(service, 'process_all_alerts', side_effect=mock_process_all_alerts):
            # 비동기 함수로 스케줄러 시작 및 중지 테스트
            async def test_scheduler():
                start_task = asyncio.create_task(scheduler.start())
                
                # 잠시 대기
                await asyncio.sleep(0.5)
                
                # 스케줄러 중지
                scheduler.stop()
                
                # 작업 완료 대기
                await start_task
                
                # 스케줄러 상태 확인
                self.assertFalse(scheduler.is_running)
            
            # 테스트 실행
            asyncio.run(test_scheduler())

if __name__ == '__main__':
    unittest.main() 