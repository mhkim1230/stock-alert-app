from datetime import datetime, timezone
from typing import Dict

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.models.database import CurrencyAlert, NewsAlert, StockAlert


class AlertService:
    def __init__(self, stock_service, currency_service, news_service, notification_service) -> None:
        self.stock_service = stock_service
        self.currency_service = currency_service
        self.news_service = news_service
        self.notification_service = notification_service

    async def run_checks(self, db: AsyncSession) -> Dict[str, int]:
        checked = 0
        triggered = 0

        stock_alerts = list((await db.execute(select(StockAlert).where(StockAlert.is_active.is_(True)))).scalars())
        for alert in stock_alerts:
            checked += 1
            quote = await self.stock_service.get_stock_quote(alert.stock_symbol)
            if quote and self._matches(quote["price"], alert.target_price, alert.condition):
                alert.is_active = False
                alert.triggered_at = datetime.now(timezone.utc)
                await db.commit()
                await self.notification_service.send_push_to_all(
                    db,
                    title=f"Stock Alert: {alert.stock_symbol}",
                    body=f"{alert.stock_symbol} hit {quote['price']}",
                    alert_type="stock",
                    alert_id=alert.id,
                    extra_data={"symbol": alert.stock_symbol, "price": quote["price"]},
                )
                triggered += 1

        currency_alerts = list((await db.execute(select(CurrencyAlert).where(CurrencyAlert.is_active.is_(True)))).scalars())
        for alert in currency_alerts:
            checked += 1
            rate = await self.currency_service.get_exchange_rate(alert.base_currency, alert.target_currency)
            if rate and self._matches(float(rate["rate"]), alert.target_rate, alert.condition):
                alert.is_active = False
                alert.triggered_at = datetime.now(timezone.utc)
                await db.commit()
                await self.notification_service.send_push_to_all(
                    db,
                    title=f"Currency Alert: {alert.base_currency}/{alert.target_currency}",
                    body=f"{alert.base_currency}/{alert.target_currency} hit {rate['rate']}",
                    alert_type="currency",
                    alert_id=alert.id,
                    extra_data=rate,
                )
                triggered += 1

        news_alerts = list((await db.execute(select(NewsAlert).where(NewsAlert.is_active.is_(True)))).scalars())
        for alert in news_alerts:
            checked += 1
            articles = await self.news_service.get_latest_news(query=alert.keywords, limit=3)
            alert.last_checked = datetime.now(timezone.utc)
            if articles:
                alert.is_active = False
                alert.triggered_at = datetime.now(timezone.utc)
                await db.commit()
                await self.notification_service.send_push_to_all(
                    db,
                    title=f"News Alert: {alert.keywords}",
                    body=articles[0]["title"],
                    alert_type="news",
                    alert_id=alert.id,
                    extra_data={"keywords": alert.keywords, "article_count": len(articles)},
                )
                triggered += 1
            else:
                await db.commit()

        return {"checked": checked, "triggered": triggered}

    @staticmethod
    def _matches(current: float, target: float, condition: str) -> bool:
        if condition == "above":
            return current > target
        if condition == "below":
            return current < target
        return current == target
