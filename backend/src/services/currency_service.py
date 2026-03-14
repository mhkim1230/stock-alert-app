import logging
from typing import Dict, Optional, Union

import aiohttp

from src.config.settings import settings
from src.services.naver_stock_service import NaverStockService


class CurrencyService:
    def __init__(self) -> None:
        self.logger = logging.getLogger(__name__)
        self.naver = NaverStockService()

    async def get_exchange_rate(
        self, base_currency: str, target_currency: str
    ) -> Optional[Dict[str, Union[float, str]]]:
        rate = await self.naver.get_exchange_rate(base_currency, target_currency)
        if rate and rate > 0:
            return {
                "base_currency": base_currency.upper(),
                "target_currency": target_currency.upper(),
                "rate": float(rate),
                "source": "naver",
            }

        url = f"https://api.exchangerate.host/convert?from={base_currency.upper()}&to={target_currency.upper()}"
        try:
            async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=settings.request_timeout)) as session:
                async with session.get(url) as response:
                    if response.status != 200:
                        return None
                    data = await response.json()
                    result = data.get("result")
                    if result is None:
                        return None
                    return {
                        "base_currency": base_currency.upper(),
                        "target_currency": target_currency.upper(),
                        "rate": float(result),
                        "source": "exchangerate.host",
                    }
        except Exception as exc:
            self.logger.warning("Exchange rate fallback failed: %s", exc)
            return None
