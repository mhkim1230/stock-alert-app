from datetime import datetime
from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from src.models.database import StockAlert, CurrencyAlert, NewsAlert, Watchlist

class AlertService:
    """알림 서비스"""
    
    def __init__(self):
        """초기화"""
        pass
    
    async def create_stock_alert(self, db: AsyncSession, user_id: str, symbol: str, target_price: float, condition: str) -> StockAlert:
        """주식 알림 생성"""
        alert = StockAlert(
            user_id=user_id,
            stock_symbol=symbol,
            target_price=target_price,
            condition=condition
        )
        db.add(alert)
        await db.commit()
        await db.refresh(alert)
        return alert
    
    async def create_currency_alert(self, db: AsyncSession, user_id: str, base_currency: str, target_currency: str, target_rate: float, condition: str) -> CurrencyAlert:
        """환율 알림 생성"""
        alert = CurrencyAlert(
            user_id=user_id,
            base_currency=base_currency,
            target_currency=target_currency,
            target_rate=target_rate,
            condition=condition
        )
        db.add(alert)
        await db.commit()
        await db.refresh(alert)
        return alert
    
    async def create_news_alert(self, db: AsyncSession, user_id: str, keywords: str) -> NewsAlert:
        """뉴스 알림 생성"""
        alert = NewsAlert(
            user_id=user_id,
            keywords=keywords
        )
        db.add(alert)
        await db.commit()
        await db.refresh(alert)
        return alert
    
    async def get_alerts(self, db: AsyncSession, user_id: str) -> dict:
        """사용자의 모든 알림 조회"""
        stock_alerts_result = await db.execute(
            select(StockAlert).where(
                StockAlert.user_id == user_id,
                StockAlert.is_active == True
            )
        )
        stock_alerts = stock_alerts_result.scalars().all()

        currency_alerts_result = await db.execute(
            select(CurrencyAlert).where(
                CurrencyAlert.user_id == user_id,
                CurrencyAlert.is_active == True
            )
        )
        currency_alerts = currency_alerts_result.scalars().all()

        news_alerts_result = await db.execute(
            select(NewsAlert).where(
                NewsAlert.user_id == user_id,
                NewsAlert.is_active == True
            )
        )
        news_alerts = news_alerts_result.scalars().all()
        
        return {
            "stock_alerts": stock_alerts,
            "currency_alerts": currency_alerts,
            "news_alerts": news_alerts
        }
    
    async def delete_alert(self, db: AsyncSession, alert_id: str, alert_type: str) -> None:
        """알림 삭제"""
        if alert_type == "stock":
            result = await db.execute(
                select(StockAlert).where(StockAlert.id == alert_id)
            )
            alert = result.scalar_one_or_none()
        elif alert_type == "currency":
            result = await db.execute(
                select(CurrencyAlert).where(CurrencyAlert.id == alert_id)
            )
            alert = result.scalar_one_or_none()
        elif alert_type == "news":
            result = await db.execute(
                select(NewsAlert).where(NewsAlert.id == alert_id)
            )
            alert = result.scalar_one_or_none()
        else:
            raise ValueError("Invalid alert type")
        
        if not alert:
            raise ValueError("Alert not found")
        
        await db.delete(alert)
        await db.commit()
    
    async def add_to_watchlist(self, db: AsyncSession, user_id: str, symbol: str) -> Watchlist:
        """관심 종목 추가"""
        item = Watchlist(
            user_id=user_id,
            symbol=symbol
        )
        db.add(item)
        await db.commit()
        await db.refresh(item)
        return item
    
    async def get_watchlist(self, db: AsyncSession, user_id: str) -> List[Watchlist]:
        """관심 종목 목록 조회"""
        result = await db.execute(
            select(Watchlist).where(Watchlist.user_id == user_id)
        )
        return list(result.scalars().all())
    
    async def remove_from_watchlist(self, db: AsyncSession, user_id: str, symbol: str) -> None:
        """관심 종목 삭제"""
        result = await db.execute(
            select(Watchlist).where(
                Watchlist.user_id == user_id,
                Watchlist.symbol == symbol
            )
        )
        item = result.scalar_one_or_none()
        
        if item:
            await db.delete(item)
            await db.commit() 