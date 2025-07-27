#!/usr/bin/env python3
"""
푸시 알림 시스템 테스트 스크립트
"""

import asyncio
import sys
import os
from datetime import datetime

# 프로젝트 루트 경로 추가
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from src.services.notification_service import notification_service
from src.services.alert_scheduler import unified_alert_scheduler
from src.models.database import (
    initialize_database, close_database, 
    User, DeviceToken, StockAlert, CurrencyAlert, NewsAlert
)
from src.config.logging_config import get_logger

logger = get_logger(__name__)

async def test_notification_service():
    """알림 서비스 기본 기능 테스트"""
    print("=== 푸시 알림 서비스 테스트 시작 ===\n")
    
    try:
        # 데이터베이스 초기화
        print("1. 데이터베이스 초기화...")
        initialize_database()
        print("✅ 데이터베이스 초기화 완료\n")
        
        # 테스트 사용자 생성 또는 조회
        print("2. 테스트 사용자 생성...")
        test_user, created = User.get_or_create(
            username="test_user",
            defaults={
                "email": "test@example.com",
                "password_hash": "test_password_hash",
                "is_active": True
            }
        )
        print(f"✅ 테스트 사용자: {test_user.username} (ID: {test_user.id})\n")
        
        # 테스트 디바이스 토큰 등록
        print("3. 디바이스 토큰 등록 테스트...")
        test_device_token = "test_device_token_12345"
        success = await notification_service.register_device_token(
            user_id=test_user.id,
            device_token=test_device_token,
            platform="iOS"
        )
        print(f"✅ 디바이스 토큰 등록: {'성공' if success else '실패'}\n")
        
        # 테스트 푸시 알림 전송
        print("4. 테스트 푸시 알림 전송...")
        success = await notification_service.send_push_notification(
            user_id=test_user.id,
            title="테스트 알림",
            body="푸시 알림 시스템 테스트입니다.",
            extra_data={"test": True, "timestamp": str(datetime.now())}
        )
        print(f"✅ 푸시 알림 전송: {'성공' if success else '실패'}\n")
        
        # 테스트 알림 생성
        print("5. 테스트 알림 생성...")
        
        # 주식 알림 생성
        stock_alert = StockAlert.create(
            user=test_user.id,
            stock_symbol="AAPL",
            target_price=150.0,
            condition="above",
            is_active=True
        )
        print(f"✅ 주식 알림 생성: AAPL > $150.0")
        
        # 환율 알림 생성
        currency_alert = CurrencyAlert.create(
            user=test_user.id,
            base_currency="USD",
            target_currency="KRW",
            target_rate=1300.0,
            condition="above",
            is_active=True
        )
        print(f"✅ 환율 알림 생성: USD/KRW > 1300.0")
        
        # 뉴스 알림 생성
        news_alert = NewsAlert.create(
            user=test_user.id,
            keywords="Apple, iPhone, 애플",
            is_active=True
        )
        print(f"✅ 뉴스 알림 생성: 키워드 'Apple, iPhone, 애플'\n")
        
        # 스케줄러 상태 확인
        print("6. 스케줄러 상태 확인...")
        scheduler_status = await unified_alert_scheduler.get_scheduler_status()
        print(f"✅ 스케줄러 실행 상태: {scheduler_status['is_running']}")
        print(f"✅ 활성 알림 개수:")
        print(f"   - 주식 알림: {scheduler_status['active_alerts']['stock']}개")
        print(f"   - 환율 알림: {scheduler_status['active_alerts']['currency']}개")
        print(f"   - 뉴스 알림: {scheduler_status['active_alerts']['news']}개\n")
        
        # 개별 알림 체크 테스트
        print("7. 개별 알림 체크 테스트...")
        
        # 주식 알림 체크
        stock_alerts = await unified_alert_scheduler.check_stock_alerts()
        print(f"✅ 주식 알림 체크 완료: {len(stock_alerts)}개 트리거됨")
        
        # 환율 알림 체크
        currency_alerts = await unified_alert_scheduler.check_currency_alerts()
        print(f"✅ 환율 알림 체크 완료: {len(currency_alerts)}개 트리거됨")
        
        # 뉴스 알림 체크
        news_alerts = await unified_alert_scheduler.check_news_alerts()
        print(f"✅ 뉴스 알림 체크 완료: {len(news_alerts)}개 트리거됨\n")
        
        print("=== 모든 테스트 완료 ===")
        print("✅ 푸시 알림 시스템이 정상적으로 작동합니다!")
        
    except Exception as e:
        print(f"❌ 테스트 중 오류 발생: {e}")
        logger.error(f"테스트 오류: {e}", exc_info=True)
        
    finally:
        # 데이터베이스 연결 종료
        close_database()
        print("\n🔚 데이터베이스 연결 종료")

async def test_scheduler_performance():
    """스케줄러 성능 테스트"""
    print("\n=== 스케줄러 성능 테스트 ===")
    
    try:
        initialize_database()
        
        # 다수의 테스트 알림 생성
        print("1. 대량 테스트 알림 생성...")
        
        test_user, _ = User.get_or_create(
            username="perf_test_user",
            defaults={
                "email": "perf@example.com",
                "password_hash": "test_hash",
                "is_active": True
            }
        )
        
        # 10개의 주식 알림 생성
        for i in range(10):
            StockAlert.create(
                user=test_user.id,
                stock_symbol=f"TEST{i:02d}",
                target_price=100.0 + i,
                condition="above",
                is_active=True
            )
        
        # 10개의 환율 알림 생성
        currencies = ["EUR", "JPY", "GBP", "AUD", "CAD", "CHF", "CNY", "SEK", "NOK", "NZD"]
        for i, currency in enumerate(currencies):
            CurrencyAlert.create(
                user=test_user.id,
                base_currency="USD",
                target_currency=currency,
                target_rate=1.0 + i * 0.1,
                condition="above",
                is_active=True
            )
        
        print("✅ 대량 테스트 알림 생성 완료")
        
        # 성능 측정
        print("2. 스케줄러 성능 측정...")
        
        start_time = datetime.now()
        
        # 모든 알림 체크
        await asyncio.gather(
            unified_alert_scheduler.check_stock_alerts(),
            unified_alert_scheduler.check_currency_alerts(),
            unified_alert_scheduler.check_news_alerts()
        )
        
        end_time = datetime.now()
        execution_time = (end_time - start_time).total_seconds()
        
        print(f"✅ 전체 알림 체크 완료")
        print(f"⏱️  실행 시간: {execution_time:.2f}초")
        
        # 스케줄러 상태 재확인
        status = await unified_alert_scheduler.get_scheduler_status()
        print(f"📊 최종 활성 알림 개수:")
        print(f"   - 주식: {status['active_alerts']['stock']}개")
        print(f"   - 환율: {status['active_alerts']['currency']}개")
        print(f"   - 뉴스: {status['active_alerts']['news']}개")
        
    except Exception as e:
        print(f"❌ 성능 테스트 중 오류: {e}")
        
    finally:
        close_database()

def main():
    """메인 테스트 함수"""
    print("🚀 푸시 알림 시스템 테스트 시작\n")
    
    # 기본 기능 테스트
    asyncio.run(test_notification_service())
    
    # 성능 테스트
    asyncio.run(test_scheduler_performance())
    
    print("\n🎉 모든 테스트 완료!")

if __name__ == "__main__":
    main() 