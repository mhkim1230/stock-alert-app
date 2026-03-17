import logging
import math
import time
from typing import Any, Dict, List, Optional

import aiohttp
import requests

from src.config.settings import settings
from src.services.naver_stock_service import NaverStockService


class GlobalQuoteService:
    def __init__(self, naver_service: Optional[NaverStockService] = None) -> None:
        self.logger = logging.getLogger(__name__)
        self.naver = naver_service or NaverStockService()
        self.quote_cache: Dict[str, Dict[str, Any]] = {}
        self.quote_cache_ttl = min(settings.CACHE_TIMEOUT, 20)

    async def get_quote(self, symbol: str) -> Optional[Dict[str, Any]]:
        normalized_symbol = str(symbol or "").strip().upper()
        if not normalized_symbol or normalized_symbol.isdigit():
            return None

        cached = self._get_cached_quote(normalized_symbol)
        if cached:
            return cached

        quote = await self._fetch_yahoo_quote(normalized_symbol)
        if quote:
            self._save_cached_quote(normalized_symbol, quote)
            return quote

        quote = await self._fetch_naver_fallback(normalized_symbol)
        if quote:
            self._save_cached_quote(normalized_symbol, quote)
        return quote

    async def enrich_search_results(self, items: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        enriched: List[Dict[str, Any]] = []
        for item in items:
            symbol = str(item.get("symbol") or "").upper()
            if not symbol or symbol.isdigit():
                enriched.append(item)
                continue

            quote = await self._fetch_yahoo_quote(symbol)
            if not quote:
                enriched.append(item)
                continue

            enriched.append(
                {
                    **item,
                    "name": quote.get("name") or item.get("name") or symbol,
                    "market": quote.get("market") or item.get("market"),
                    "price": quote.get("price") if quote.get("price") is not None else item.get("price"),
                    "change": quote.get("change"),
                    "change_percent": quote.get("change_percent"),
                    "currency": quote.get("currency") or item.get("currency") or "USD",
                    "source": quote.get("source") or item.get("source") or f"yahoo_quote:{symbol}",
                }
            )
        return enriched

    async def _fetch_naver_fallback(self, symbol: str) -> Optional[Dict[str, Any]]:
        detailed = await self.naver._get_world_stock_by_symbol(symbol)
        if not detailed:
            return None
        return {
            "symbol": symbol,
            "name": str(detailed.get("name") or detailed.get("name_kr") or symbol),
            "market": detailed.get("market"),
            "price": self._coerce_float(detailed.get("current_price") or detailed.get("price")),
            "change": self._coerce_float(detailed.get("change")),
            "change_percent": self._coerce_float(detailed.get("change_percent")),
            "currency": detailed.get("currency", "USD"),
            "source": detailed.get("source", "naver_world_dynamic_parsing"),
        }

    async def _fetch_yahoo_quote(self, symbol: str) -> Optional[Dict[str, Any]]:
        chart_url = (
            "https://query1.finance.yahoo.com/v8/finance/chart/"
            f"{symbol}?range=2d&interval=1m&includePrePost=false"
        )
        timeout = aiohttp.ClientTimeout(total=settings.request_timeout)
        payload = None

        try:
            async with aiohttp.ClientSession(timeout=timeout) as session:
                async with session.get(chart_url, headers={"User-Agent": "Mozilla/5.0"}) as response:
                    if response.status == 200:
                        payload = await response.json()
                    else:
                        self.logger.warning("Yahoo chart quote fetch failed: %s %s", symbol, response.status)
        except Exception as exc:
            self.logger.warning("Yahoo chart quote fetch error for %s: %s", symbol, exc)

        if payload is None:
            try:
                response = requests.get(chart_url, headers={"User-Agent": "Mozilla/5.0"}, timeout=settings.request_timeout)
                if response.status_code == 200:
                    payload = response.json()
                else:
                    self.logger.warning("Yahoo chart quote requests fallback failed: %s %s", symbol, response.status_code)
            except Exception as exc:
                self.logger.warning("Yahoo chart quote requests fallback error for %s: %s", symbol, exc)
                payload = None

        chart_result = (((payload or {}).get("chart") or {}).get("result") or [None])[0]
        if not chart_result:
            fallback_url = (
                "https://query1.finance.yahoo.com/v8/finance/chart/"
                f"{symbol}?range=5d&interval=1d&includePrePost=false"
            )
            try:
                async with aiohttp.ClientSession(timeout=timeout) as session:
                    async with session.get(fallback_url, headers={"User-Agent": "Mozilla/5.0"}) as response:
                        if response.status == 200:
                            payload = await response.json()
                        else:
                            self.logger.warning("Yahoo chart daily fallback failed: %s %s", symbol, response.status)
                            payload = None
            except Exception as exc:
                self.logger.warning("Yahoo chart daily fallback error for %s: %s", symbol, exc)
                payload = None

            if payload is None:
                try:
                    response = requests.get(fallback_url, headers={"User-Agent": "Mozilla/5.0"}, timeout=settings.request_timeout)
                    if response.status_code != 200:
                        return None
                    payload = response.json()
                except Exception:
                    return None
            chart_result = (((payload or {}).get("chart") or {}).get("result") or [None])[0]

        if not chart_result:
            return None

        meta = chart_result.get("meta") or {}
        price = self._coerce_float(meta.get("regularMarketPrice"))
        previous_close = self._extract_previous_regular_close(chart_result)
        if previous_close in (None, 0):
            previous_close = self._coerce_float(meta.get("regularMarketPreviousClose") or meta.get("chartPreviousClose") or meta.get("previousClose"))
        if price is None or previous_close in (None, 0):
            return None

        change_value = price - previous_close
        change_percent = self._truncate_percent((change_value / previous_close) * 100)
        return {
            "name": meta.get("shortName") or meta.get("instrumentType") or symbol,
            "price": price,
            "change": round(change_value, 4),
            "change_percent": change_percent,
            "currency": meta.get("currency", "USD"),
            "market": self._normalize_yahoo_market(meta.get("exchangeName")),
            "source": f"yahoo_quote:{symbol}",
        }

    def _extract_previous_regular_close(self, chart_result: Dict[str, Any]) -> Optional[float]:
        quote = (((chart_result.get("indicators") or {}).get("quote") or [None])[0]) or {}
        closes = quote.get("close") or []
        if not closes:
            return None

        values: List[float] = []
        for value in closes:
            coerced = self._coerce_float(value)
            if coerced is not None:
                values.append(coerced)

        if len(values) >= 2:
            return values[-2]
        if len(values) == 1:
            return values[0]
        return None

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
    def _normalize_yahoo_market(exchange_name: Optional[str]) -> Optional[str]:
        mapping = {
            "NMS": "NASDAQ",
            "NGM": "NASDAQ",
            "NYQ": "NYSE",
            "ASE": "AMEX",
            "NASDAQGS": "NASDAQ",
            "NASDAQGM": "NASDAQ",
            "NASDAQCM": "NASDAQ",
            "NEW YORK STOCK EXCHANGE": "NYSE",
            "NASDAQ": "NASDAQ",
        }
        if not exchange_name:
            return None
        return mapping.get(str(exchange_name).upper(), str(exchange_name).upper())

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
