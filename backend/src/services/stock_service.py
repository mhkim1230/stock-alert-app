import logging
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
        results = await self.search_stocks(symbol)
        for item in results:
            if item["symbol"].upper() == symbol.upper():
                return item
        return results[0] if results else None

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
        url = (
            "https://query1.finance.yahoo.com/v8/finance/chart/"
            f"{symbol}?range=5d&interval=1d&includePrePost=true"
        )
        timeout = aiohttp.ClientTimeout(total=settings.request_timeout)

        try:
            async with aiohttp.ClientSession(timeout=timeout) as session:
                async with session.get(url, headers={"User-Agent": "Mozilla/5.0"}) as response:
                    if response.status != 200:
                        self.logger.warning("Yahoo quote fetch failed: %s %s", symbol, response.status)
                        payload = None
                    else:
                        payload = await response.json()
        except Exception as exc:
            self.logger.warning("Yahoo quote fetch error for %s: %s", symbol, exc)
            payload = None

        if payload is None:
            try:
                response = requests.get(url, headers={"User-Agent": "Mozilla/5.0"}, timeout=settings.request_timeout)
                if response.status_code != 200:
                    self.logger.warning("Yahoo quote requests fallback failed: %s %s", symbol, response.status_code)
                    return None
                payload = response.json()
            except Exception as exc:
                self.logger.warning("Yahoo quote requests fallback error for %s: %s", symbol, exc)
                return None

        result = (((payload or {}).get("chart") or {}).get("result") or [None])[0]
        if not result:
            return None

        meta = result.get("meta") or {}
        price = self._coerce_float(meta.get("regularMarketPrice"))
        previous_close = self._coerce_float(meta.get("chartPreviousClose") or meta.get("previousClose"))
        if price is None or previous_close in (None, 0):
            return None

        change_percent = round(((price - previous_close) / previous_close) * 100, 2)
        market = self._normalize_yahoo_market(meta.get("exchangeName"))

        return {
            "price": price,
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
        }
        if not exchange_name:
            return None
        return mapping.get(str(exchange_name).upper(), str(exchange_name).upper())

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
