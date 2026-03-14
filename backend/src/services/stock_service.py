import logging
from typing import Any, Dict, List, Optional

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
            normalized.append(
                {
                    "symbol": str(item.get("symbol") or item.get("code") or query).upper(),
                    "name": str(item.get("name") or item.get("stock_name") or query),
                    "price": price,
                    "change": self._coerce_float(item.get("change")),
                    "change_percent": self._coerce_float(
                        item.get("change_percent") or item.get("changeRate")
                    ),
                    "currency": item.get("currency", "KRW"),
                    "source": item.get("source", "naver"),
                }
            )
        return normalized

    async def get_stock_quote(self, symbol: str) -> Optional[Dict[str, Any]]:
        results = await self.search_stocks(symbol)
        for item in results:
            if item["symbol"].upper() == symbol.upper():
                return item
        return results[0] if results else None

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
