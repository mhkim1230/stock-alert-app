import logging
import re
from typing import Dict, Optional, Union
from urllib.parse import urlencode

import aiohttp
from bs4 import BeautifulSoup

from src.config.settings import settings


class CurrencyService:
    def __init__(self) -> None:
        self.logger = logging.getLogger(__name__)

    async def get_exchange_rate(
        self, base_currency: str, target_currency: str
    ) -> Optional[Dict[str, Union[float, str]]]:
        base = base_currency.upper()
        target = target_currency.upper()

        if base == target:
            return {
                "base_currency": base,
                "target_currency": target,
                "rate": 1.0,
                "source": "direct",
            }

        rate = await self._fetch_naver_detail_rate(base, target)
        if rate and rate > 0:
            return {
                "base_currency": base,
                "target_currency": target,
                "rate": float(rate),
                "source": "naver",
            }

        rate = await self._fetch_frankfurter_rate(base, target)
        if rate and rate > 0:
            return {
                "base_currency": base,
                "target_currency": target,
                "rate": float(rate),
                "source": "frankfurter",
            }

        return None

    async def _fetch_frankfurter_rate(self, base_currency: str, target_currency: str) -> Optional[float]:
        query = urlencode({"base": base_currency.upper(), "symbols": target_currency.upper()})
        url = f"https://api.frankfurter.dev/v1/latest?{query}"
        try:
            async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=settings.request_timeout)) as session:
                async with session.get(url) as response:
                    if response.status != 200:
                        return None
                    data = await response.json()
                    rates = data.get("rates") or {}
                    result = rates.get(target_currency.upper())
                    if result is None:
                        return None
                    return float(result)
        except Exception as exc:
            self.logger.warning("Frankfurter FX fallback failed: %s", exc)
            return None

    async def _fetch_naver_detail_rate(self, base_currency: str, target_currency: str) -> Optional[float]:
        if target_currency.upper() != "KRW":
            return None

        market_codes = {
            "USD": "FX_USDKRW",
            "EUR": "FX_EURKRW",
            "JPY": "FX_JPYKRW",
            "CNY": "FX_CNYKRW",
            "GBP": "FX_GBPKRW",
        }
        sane_ranges = {
            "USD": (1000, 1700),
            "EUR": (1200, 2000),
            "JPY": (7, 15),
            "CNY": (120, 260),
            "GBP": (1400, 2300),
        }

        base = base_currency.upper()
        code = market_codes.get(base)
        if not code:
            return None

        url = f"https://finance.naver.com/marketindex/exchangeDetail.naver?marketindexCd={code}"
        try:
            async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=settings.request_timeout)) as session:
                async with session.get(url, headers={"User-Agent": "Mozilla/5.0"}) as response:
                    if response.status != 200:
                        return None
                    html = await response.text()
        except Exception as exc:
            self.logger.warning("Naver FX detail fetch failed: %s", exc)
            return None

        soup = BeautifulSoup(html, "html.parser")
        node = soup.select_one("p.no_today")
        if node is None:
            return None

        text = node.get_text("", strip=True)
        match = re.search(r"(\d[\d,]*\.\d+)", text)
        if not match:
            return None

        try:
            rate = float(match.group(1).replace(",", ""))
        except ValueError:
            return None

        min_rate, max_rate = sane_ranges[base]
        if not (min_rate <= rate <= max_rate):
            self.logger.warning("Naver FX rate out of sane range: %s %s->%s", rate, base, target_currency.upper())
            return None
        return rate
