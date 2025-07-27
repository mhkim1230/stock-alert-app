import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from sqlalchemy.orm import Session
from sqlalchemy import and_, cast, Float, literal, func, or_, text
from decimal import Decimal
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.engine import Result

from ..services.currency_service import CurrencyService
from ..services.naver_stock_service import naver_stock_service  # 네이버 서비스 사용
from ..services.news_service import NewsService
from ..config.logging_config import get_logger
from ..models.database import CurrencyAlert, StockAlert, NewsAlert, User, AsyncSessionLocal
from ..services.stock_service import StockService
from ..services.notification_service import NotificationService
from ..utils.logging_decorator import log_function

logger = logging.getLogger(__name__)

class AlertScheduler:
    """알림 스케줄러"""
    
    def __init__(self, 
                 stock_service: Optional[StockService] = None,
                 currency_service: Optional[CurrencyService] = None,
                 news_service: Optional[NewsService] = None,
                 notification_service: Optional[NotificationService] = None):
        """초기화"""
        self.stock_service = stock_service or StockService()
        self.currency_service = currency_service or CurrencyService()
        self.news_service = news_service or NewsService()
        self.notification_service = notification_service or NotificationService()
        self.is_running = False
        self._task = None
        self.check_interval = 300  # 5분
        logger.info("알림 스케줄러 초기화 완료")
    
    async def start(self):
        """스케줄러 시작"""
        if self.is_running:
            logger.warning("스케줄러가 이미 실행 중입니다")
            return

        self.is_running = True
        self._task = asyncio.create_task(self._run_scheduler())
        logger.info(f"알림 스케줄러 시작 (간격: {self.check_interval}초)")
    
    async def _run_scheduler(self):
        """스케줄러 실행"""
        while self.is_running:
            try:
                async with AsyncSessionLocal() as db:
                    await self._check_alerts(db)
            except Exception as e:
                logger.error(f"스케줄러 실행 중 오류: {str(e)}")
            
            await asyncio.sleep(self.check_interval)
    
    async def stop(self):
        """스케줄러 중지"""
        if not self.is_running:
            return
        
        self.is_running = False
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
        logger.info("알림 스케줄러가 정상적으로 종료되었습니다")
    
    async def _check_alerts(self, db: AsyncSession):
        """모든 알림 체크"""
        try:
            await self._check_stock_alerts(db)
            await self._check_currency_alerts(db)
            await self._check_news_alerts(db)
        except Exception as e:
            logger.error(f"알림 체크 중 오류: {str(e)}")
    
    @log_function(log_args=True)
    async def _check_stock_alerts(self, db: AsyncSession):
        """주식 알림 체크"""
        try:
            # SQLite 호환 방식으로 쿼리 수정
            current_time = datetime.utcnow()
            result: Result = await db.execute(
                text("""
                    SELECT * FROM STOCK_ALERT 
                    WHERE is_active = 1
                """)
            )
            alerts = result.fetchall()

            triggered_count = 0
            for alert in alerts:
                try:
                    # 주식 가격 조회
                    stock_info = await self.stock_service.get_stock_price(alert.stock_symbol)
                    if not stock_info or not isinstance(stock_info, dict):
                        logger.error(f"주식 정보 조회 실패: {alert.stock_symbol}")
                        continue

                    current_price = float(stock_info.get('price', 0))
                    if current_price <= 0:
                        logger.error(f"유효하지 않은 주식 가격: {alert.stock_symbol} - {current_price}")
                        continue

                    # 알림 조건 체크
                    target_price = float(alert.target_price)
                    should_trigger = False

                    if alert.condition == 'above' and current_price >= target_price:
                        should_trigger = True
                    elif alert.condition == 'below' and current_price <= target_price:
                        should_trigger = True
                    elif alert.condition == 'equal' and abs(current_price - target_price) < 0.01:
                        should_trigger = True

                    if should_trigger:
                        # 알림 전송
                        await self.notification_service.send_stock_alert(
                            user_id=alert.user_id,
                            alert_id=alert.id,
                            symbol=alert.stock_symbol,
                            current_price=current_price,
                            target_price=target_price,
                            condition=alert.condition
                        )
                        triggered_count += 1

                        # 알림 상태 업데이트
                        await db.execute(
                            text("""
                                UPDATE STOCK_ALERT 
                                SET triggered_at = :current_time,
                                    last_checked = :current_time,
                                    is_active = 0
                                WHERE id = :alert_id
                            """),
                            {"current_time": current_time, "alert_id": alert.id}
                        )
                    else:
                        # 마지막 체크 시간만 업데이트
                        await db.execute(
                            text("""
                                UPDATE STOCK_ALERT 
                                SET last_checked = :current_time 
                                WHERE id = :alert_id
                            """),
                            {"current_time": current_time, "alert_id": alert.id}
                        )
                    
                    await db.commit()

                except Exception as e:
                    logger.error(f"주식 알림 처리 중 오류: {alert.stock_symbol} - {str(e)}")
                    continue

            logger.info(f"주식 알림 {len(alerts)}개 확인 중")
            return triggered_count

        except Exception as e:
            logger.error(f"주식 알림 체크 중 오류: {str(e)}")
            return 0
    
    async def _check_currency_alerts(self, db: AsyncSession):
        """환율 알림 체크"""
        result: Result = await db.execute(
            text("""
                SELECT * FROM CURRENCY_ALERT 
                WHERE is_active = 1
            """)
        )
        alerts = result.fetchall()
        
        for alert in alerts:
            try:
                current_rate = await self.currency_service.get_exchange_rate(
                    str(alert.base_currency),
                    str(alert.target_currency)
                )
                if current_rate is None:
                    continue
                
                target_rate = float(str(alert.target_rate))
                condition = str(alert.condition)
                
                triggered = False
                if condition == "above" and current_rate >= target_rate:
                    triggered = True
                elif condition == "below" and current_rate <= target_rate:
                    triggered = True
                elif condition == "equal" and current_rate == target_rate:
                    triggered = True
                
                if triggered:
                    # 알림 상태 업데이트
                    await db.execute(
                        text("""
                            UPDATE CURRENCY_ALERT 
                            SET is_active = 0, 
                                triggered_at = CURRENT_TIMESTAMP,
                                last_checked = CURRENT_TIMESTAMP
                            WHERE id = :alert_id
                        """),
                        {"alert_id": alert.id}
                    )
                    await db.commit()
                    
                    # TODO: 알림 전송
                    print(f"환율 알림 발생: {alert.base_currency}/{alert.target_currency} - {current_rate}")
            
            except Exception as e:
                print(f"환율 알림 체크 오류: {e}")
    
    @log_function(log_args=True)
    async def _check_news_alerts(self, db: AsyncSession):
        """뉴스 알림 체크"""
        try:
            current_time = datetime.utcnow()
            result: Result = await db.execute(
                text("""
                    SELECT * FROM NEWS_ALERT 
                    WHERE is_active = 1
                """)
            )
            alerts = result.fetchall()

            triggered_count = 0
            for alert in alerts:
                try:
                    # 뉴스 검색 및 알림 처리
                    news_items = await self.news_service.search_news(alert.keywords)
                    if news_items:
                        # 알림 전송
                        await self.notification_service.send_news_alert(
                            user_id=alert.user_id,
                            alert_id=alert.id,
                            keywords=alert.keywords,
                            news_items=news_items
                        )
                        triggered_count += 1

                    # 마지막 체크 시간 업데이트
                    await db.execute(
                        text("""
                            UPDATE NEWS_ALERT 
                            SET last_checked = :current_time 
                            WHERE id = :alert_id
                        """),
                        {"current_time": current_time, "alert_id": alert.id}
                    )
                    await db.commit()

                except Exception as e:
                    logger.error(f"뉴스 알림 처리 중 오류: {alert.keywords} - {str(e)}")
                    continue

            logger.info(f"뉴스 알림 {len(alerts)}개 확인 중")
            return triggered_count

        except Exception as e:
            logger.error(f"뉴스 알림 체크 중 오류: {str(e)}")
            return 0

    async def get_scheduler_status(self) -> Dict[str, Any]:
        """스케줄러 상태 조회"""
        return {
            "is_running": self.is_running,
            "check_interval": self.check_interval,
            "last_check": datetime.now().isoformat()
        }

# 전역 APNs 알림 스케줄러 인스턴스
unified_alert_scheduler = AlertScheduler()