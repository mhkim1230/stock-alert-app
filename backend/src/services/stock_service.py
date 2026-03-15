import logging
from typing import Any, Dict, List, Optional
import asyncio

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
        return await self._enrich_missing_domestic_change(normalized)

    async def get_stock_quote(self, symbol: str) -> Optional[Dict[str, Any]]:
        results = await self.search_stocks(symbol)
        for item in results:
            if item["symbol"].upper() == symbol.upper():
                return item
        return results[0] if results else None

    async def _enrich_missing_domestic_change(self, items: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        async def enrich(item: Dict[str, Any]) -> Dict[str, Any]:
            symbol = str(item.get("symbol") or "")
            if not symbol.isdigit():
                return item
            if item.get("source") != "naver_search_card" and item.get("change_percent") is not None:
                return item
            detailed = await self.naver._get_korean_stock_by_code(symbol)
            if detailed and detailed.get("change_percent") is not None:
                item["change_percent"] = self._coerce_float(detailed.get("change_percent"))
                item["source"] = detailed.get("source", item.get("source", "naver"))
            return item

        if not items:
            return items
        return await asyncio.gather(*(enrich(item) for item in items))

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
