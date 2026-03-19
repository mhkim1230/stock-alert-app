import logging
from typing import Any, Dict, List, Optional

from src.services.domestic_quote_service import DomesticQuoteService
from src.services.global_quote_service import GlobalQuoteService
from src.services.naver_stock_service import NaverStockService


class StockService:
    def __init__(self) -> None:
        self.logger = logging.getLogger(__name__)
        self.naver = NaverStockService()
        self.domestic = DomesticQuoteService(self.naver)
        self.global_quote = GlobalQuoteService(self.naver)

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

        domestics = [item for item in normalized if str(item.get("symbol") or "").isdigit()]
        globals_ = [item for item in normalized if not str(item.get("symbol") or "").isdigit()]

        domestic_map = {
            item["symbol"]: item for item in await self.domestic.enrich_search_results(domestics)
        }
        global_map = {
            item["symbol"]: item for item in await self.global_quote.enrich_search_results(globals_)
        }

        ordered: List[Dict[str, Any]] = []
        for item in normalized:
            symbol = str(item.get("symbol") or "").upper()
            if symbol in domestic_map:
                ordered.append(domestic_map[symbol])
            elif symbol in global_map:
                ordered.append(global_map[symbol])
            else:
                ordered.append(item)
        return ordered

    async def get_stock_quote(self, symbol: str) -> Optional[Dict[str, Any]]:
        normalized_symbol = str(symbol or "").strip().upper()
        if not normalized_symbol:
            return None
        if normalized_symbol.isdigit():
            return await self.domestic.get_quote(normalized_symbol)
        return await self.global_quote.get_quote(normalized_symbol)

    async def get_stock_fundamentals(self, symbol: str) -> Optional[Dict[str, Any]]:
        normalized_symbol = str(symbol or "").strip().upper()
        if not normalized_symbol or normalized_symbol.isdigit():
            return None
        return await self.global_quote.get_fundamentals(normalized_symbol)

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
