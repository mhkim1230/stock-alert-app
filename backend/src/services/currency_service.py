import logging
import re
from typing import Dict, Optional, Union

import aiohttp
from bs4 import BeautifulSoup

from src.config.settings import settings


class CurrencyService:
    def __init__(self) -> None:
        self.logger = logging.getLogger(__name__)

    async def get_exchange_rate(
        self, base_currency: str, target_currency: str
    ) -> Optional[Dict[str, Union[float, str]]]:
        rate = await self._fetch_naver_detail_rate(base_currency, target_currency)
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
