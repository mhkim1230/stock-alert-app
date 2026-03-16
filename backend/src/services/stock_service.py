import logging
import time
from typing import Any, Dict, List, Optional
import asyncio
import aiohttp
import requests

from src.config.settings import settings
from src.services.naver_stock_service import NaverStockService


class StockService:
    def __init__(self) -> None:
        self.logger = logging.getLogger(__name__)
        self.naver = NaverStockService()
        self.quote_cache: Dict[str, Dict[str, Any]] = {}
        self.quote_cache_ttl = min(settings.CACHE_TIMEOUT, 20)

    async def search_stocks(self, query: str) -> List[Dict[str, Any]]:
        results = await self.naver.search_stock(query)
        normalized: List[Dict[str, Any]] = []
        for item in results:
            price = self._coerce_float(item.get("current_price") or item.get("price"))
            if price is None:
                continue
            raw_change_percent = item.get("change_percent")
            if raw_change_percent is None:
                raw_change_percent = item.get("changeRate")
            normalized.append(
                {
                    "symbol": str(item.get("symbol") or item.get("code") or query).upper(),
                    "name": str(item.get("name") or item.get("stock_name") or query),
                    "market": item.get("market"),
                    "price": price,
                    "change": self._coerce_float(item.get("change")),
                    "change_percent": self._coerce_float(raw_change_percent),
                    "currency": item.get("currency", "KRW"),
                    "source": item.get("source", "naver"),
                }
            )
        normalized = await self._enrich_domestic_quotes(normalized)
        return await self._enrich_global_quotes(normalized)

    async def get_stock_quote(self, symbol: str) -> Optional[Dict[str, Any]]:
        normalized_symbol = str(symbol or "").strip().upper()
        if not normalized_symbol:
            return None

        cached = self._get_cached_quote(normalized_symbol)
        if cached:
            return cached

        if normalized_symbol.isdigit():
            quote = await self._get_domestic_quote(normalized_symbol)
        else:
            quote = await self._get_global_quote(normalized_symbol)

        if quote:
            self._save_cached_quote(normalized_symbol, quote)
            return quote

        results = await self.search_stocks(normalized_symbol)
        for item in results:
            if item["symbol"].upper() == normalized_symbol:
                self._save_cached_quote(normalized_symbol, item)
                return item
        fallback = results[0] if results else None
        if fallback:
            self._save_cached_quote(normalized_symbol, fallback)
        return fallback

    async def _get_domestic_quote(self, symbol: str) -> Optional[Dict[str, Any]]:
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

    async def _get_global_quote(self, symbol: str) -> Optional[Dict[str, Any]]:
        yahoo = await self._fetch_yahoo_quote(symbol)
        if yahoo:
            return {
                "symbol": symbol,
                "name": str(yahoo.get("name") or symbol),
                "market": yahoo.get("market"),
                "price": yahoo.get("price"),
                "change": self._coerce_float(yahoo.get("change")),
                "change_percent": yahoo.get("change_percent"),
                "currency": yahoo.get("currency", "USD"),
                "source": yahoo.get("source", f"yahoo_quote:{symbol}"),
            }

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

    async def _enrich_domestic_quotes(self, items: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        async def enrich(item: Dict[str, Any]) -> Dict[str, Any]:
            symbol = str(item.get("symbol") or "")
            if not symbol.isdigit():
                return item
            if item.get("source") != "naver_search_card" and item.get("change_percent") is not None and item.get("price") is not None:
                return item
            detailed = await self.naver._get_korean_stock_by_code(symbol)
            if detailed:
                item["price"] = self._coerce_float(detailed.get("current_price") or detailed.get("price")) or item.get("price")
                item["change_percent"] = self._coerce_float(detailed.get("change_percent"))
                item["source"] = detailed.get("source", item.get("source", "naver"))
            return item

        if not items:
            return items
        return await asyncio.gather(*(enrich(item) for item in items))

    async def _enrich_global_quotes(self, items: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        async def enrich(item: Dict[str, Any]) -> Dict[str, Any]:
            symbol = str(item.get("symbol") or "").upper()
            if not symbol or symbol.isdigit():
                return item
            yahoo = await self._fetch_yahoo_quote(symbol)
            if not yahoo:
                return item
            item["price"] = yahoo.get("price", item.get("price"))
            item["change_percent"] = yahoo.get("change_percent", item.get("change_percent"))
            item["currency"] = yahoo.get("currency", item.get("currency"))
            item["market"] = yahoo.get("market", item.get("market"))
            item["source"] = yahoo.get("source", item.get("source"))
            return item

        if not items:
            return items
        return await asyncio.gather(*(enrich(item) for item in items))

    async def _fetch_yahoo_quote(self, symbol: str) -> Optional[Dict[str, Any]]:
        quote_url = f"https://query1.finance.yahoo.com/v7/finance/quote?symbols={symbol}"
        timeout = aiohttp.ClientTimeout(total=settings.request_timeout)
        payload = None

        try:
            async with aiohttp.ClientSession(timeout=timeout) as session:
                async with session.get(quote_url, headers={"User-Agent": "Mozilla/5.0"}) as response:
                    if response.status != 200:
                        self.logger.warning("Yahoo quote fetch failed: %s %s", symbol, response.status)
                    else:
                        payload = await response.json()
        except Exception as exc:
            self.logger.warning("Yahoo quote fetch error for %s: %s", symbol, exc)

        if payload is None:
            try:
                response = requests.get(quote_url, headers={"User-Agent": "Mozilla/5.0"}, timeout=settings.request_timeout)
                if response.status_code != 200:
                    self.logger.warning("Yahoo quote requests fallback failed: %s %s", symbol, response.status_code)
                else:
                    payload = response.json()
            except Exception as exc:
                self.logger.warning("Yahoo quote requests fallback error for %s: %s", symbol, exc)
                payload = None

        result = (((payload or {}).get("quoteResponse") or {}).get("result") or [None])[0]
        if result:
            price = self._coerce_float(result.get("regularMarketPrice"))
            previous_close = self._coerce_float(result.get("regularMarketPreviousClose"))
            if price is not None and previous_close not in (None, 0):
                change_value = price - previous_close
                change_percent = round((change_value / previous_close) * 100, 2)
                market = self._normalize_yahoo_market(result.get("fullExchangeName") or result.get("exchange"))
                return {
                    "name": result.get("shortName") or result.get("longName") or symbol,
                    "price": price,
                    "change": round(change_value, 4),
                    "change_percent": change_percent,
                    "currency": result.get("currency", "USD"),
                    "market": market,
                    "source": f"yahoo_quote:{symbol}",
                }

        chart_url = (
            "https://query1.finance.yahoo.com/v8/finance/chart/"
            f"{symbol}?range=5d&interval=1d&includePrePost=true"
        )
        try:
            async with aiohttp.ClientSession(timeout=timeout) as session:
                async with session.get(chart_url, headers={"User-Agent": "Mozilla/5.0"}) as response:
                    if response.status != 200:
                        self.logger.warning("Yahoo chart fallback failed: %s %s", symbol, response.status)
                        payload = None
                    else:
                        payload = await response.json()
        except Exception as exc:
            self.logger.warning("Yahoo chart fallback error for %s: %s", symbol, exc)
            payload = None

        if payload is None:
            try:
                response = requests.get(chart_url, headers={"User-Agent": "Mozilla/5.0"}, timeout=settings.request_timeout)
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
        change_percent = round((change_value / previous_close) * 100, 2)
        market = self._normalize_yahoo_market(meta.get("exchangeName"))
        return {
            "name": meta.get("shortName") or meta.get("instrumentType") or symbol,
            "price": price,
            "change": round(change_value, 4),
            "change_percent": change_percent,
            "currency": meta.get("currency", "USD"),
            "market": market,
            "source": f"yahoo_quote:{symbol}",
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

    def _extract_previous_regular_close(self, chart_result: Dict[str, Any]) -> Optional[float]:
        quote = (((chart_result.get("indicators") or {}).get("quote") or [None])[0]) or {}
        closes = quote.get("close") or []
        if not closes:
            return None

        last_non_null: List[float] = []
        for value in closes:
            coerced = self._coerce_float(value)
            if coerced is not None:
                last_non_null.append(coerced)

        if len(last_non_null) >= 2:
            return last_non_null[-2]
        if len(last_non_null) == 1:
            return last_non_null[0]
        return None

    def _get_cached_quote(self, symbol: str) -> Optional[Dict[str, Any]]:
        cache_key = symbol.upper()
        cached = self.quote_cache.get(cache_key)
        if not cached:
            return None
        if time.time() > cached["expires_at"]:
            self.quote_cache.pop(cache_key, None)
            return None
        return dict(cached["data"])

    def _save_cached_quote(self, symbol: str, quote: Dict[str, Any]) -> None:
        self.quote_cache[symbol.upper()] = {
            "data": dict(quote),
            "expires_at": time.time() + self.quote_cache_ttl,
        }

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
