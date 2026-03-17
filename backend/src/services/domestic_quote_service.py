import logging
import math
import time
from typing import Any, Dict, List, Optional

from src.config.settings import settings
from src.services.naver_stock_service import NaverStockService


class DomesticQuoteService:
    def __init__(self, naver_service: Optional[NaverStockService] = None) -> None:
        self.logger = logging.getLogger(__name__)
        self.naver = naver_service or NaverStockService()
        self.quote_cache: Dict[str, Dict[str, Any]] = {}
        self.quote_cache_ttl = min(settings.CACHE_TIMEOUT, 20)

    async def get_quote(self, symbol: str) -> Optional[Dict[str, Any]]:
        normalized_symbol = str(symbol or "").strip().upper()
        if not normalized_symbol or not normalized_symbol.isdigit():
            return None

        cached = self._get_cached_quote(normalized_symbol)
        if cached:
            return cached

        quote = await self._fetch_direct_quote(normalized_symbol)
        if quote:
            self._save_cached_quote(normalized_symbol, quote)
            return quote

        quote = await self._fetch_search_fallback(normalized_symbol)
        if quote:
            self._save_cached_quote(normalized_symbol, quote)
        return quote

    async def enrich_search_results(self, items: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        enriched: List[Dict[str, Any]] = []
        for item in items:
            symbol = str(item.get("symbol") or "").upper()
            if not symbol.isdigit():
                enriched.append(item)
                continue
            if item.get("source") != "naver_search_card" and item.get("change_percent") is not None and item.get("price") is not None:
                enriched.append(item)
                continue

            detailed = await self._fetch_direct_quote(symbol)
            if not detailed:
                enriched.append(item)
                continue

            enriched.append(
                {
                    **item,
                    "name": detailed.get("name") or item.get("name") or symbol,
                    "market": detailed.get("market") or item.get("market"),
                    "price": detailed.get("price") if detailed.get("price") is not None else item.get("price"),
                    "change": detailed.get("change"),
                    "change_percent": detailed.get("change_percent"),
                    "currency": detailed.get("currency") or item.get("currency") or "KRW",
                    "source": detailed.get("source") or item.get("source") or "naver_dynamic_parsing",
                }
            )
        return enriched

    async def _fetch_direct_quote(self, symbol: str) -> Optional[Dict[str, Any]]:
        detailed = await self.naver._get_korean_stock_by_code(symbol)
        if not detailed:
            return None
        return {
            "symbol": symbol,
            "name": str(detailed.get("name") or detailed.get("name_kr") or symbol),
            "market": detailed.get("market"),
            "price": self._coerce_float(detailed.get("current_price") or detailed.get("price")),
            "change": self._coerce_float(detailed.get("change")),
            "change_percent": self._coerce_float(detailed.get("change_percent")),
            "currency": detailed.get("currency", "KRW"),
            "source": detailed.get("source", "naver_dynamic_parsing"),
        }

    async def _fetch_search_fallback(self, symbol: str) -> Optional[Dict[str, Any]]:
        results = await self.naver.search_stock(symbol)
        exact = next((item for item in results if str(item.get("symbol") or "").upper() == symbol), None)
        if not exact:
            return None

        price = self._coerce_float(exact.get("current_price") or exact.get("price"))
        if price is None:
            return None

        return {
            "symbol": symbol,
            "name": str(exact.get("name") or exact.get("stock_name") or symbol),
            "market": exact.get("market"),
            "price": price,
            "change": self._coerce_float(exact.get("change")),
            "change_percent": self._coerce_float(exact.get("change_percent") or exact.get("changeRate")),
            "currency": exact.get("currency", "KRW"),
            "source": exact.get("source", "naver_search_card"),
        }

    def _get_cached_quote(self, symbol: str) -> Optional[Dict[str, Any]]:
        cached = self.quote_cache.get(symbol)
        if not cached:
            return None
        if time.time() > cached["expires_at"]:
            self.quote_cache.pop(symbol, None)
            return None
        return dict(cached["data"])

    def _save_cached_quote(self, symbol: str, quote: Dict[str, Any]) -> None:
        self.quote_cache[symbol] = {
            "data": dict(quote),
            "expires_at": time.time() + self.quote_cache_ttl,
        }

    @staticmethod
    def _truncate_percent(value: float) -> float:
        if value >= 0:
            return math.floor(value * 100) / 100
        return math.ceil(value * 100) / 100

    @staticmethod
    def _coerce_float(value: Any) -> Optional[float]:
        if value is None or value == "":
            return None
        if isinstance(value, (int, float)):
            return float(value)
        cleaned = (
            str(value)
            .replace(",", "")
            .replace("%", "")
            .replace("$", "")
            .replace("₩", "")
            .strip()
        )
        try:
            return float(cleaned)
        except ValueError:
            return None
