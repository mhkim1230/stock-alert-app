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
        self.fundamentals_cache: Dict[str, Dict[str, Any]] = {}
        self.quote_cache_ttl = min(settings.CACHE_TIMEOUT, 20)
        self.fundamentals_cache_ttl = min(settings.CACHE_TIMEOUT, 300)

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

    async def get_fundamentals(self, symbol: str) -> Optional[Dict[str, Any]]:
        normalized_symbol = str(symbol or "").strip().upper()
        if not normalized_symbol or normalized_symbol.isdigit():
            return None

        cached = self._get_cached_fundamentals(normalized_symbol)
        if cached:
            return cached

        fundamentals = await self._fetch_yahoo_fundamentals(normalized_symbol)
        if fundamentals:
            self._save_cached_fundamentals(normalized_symbol, fundamentals)
        return fundamentals

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
            f"{symbol}?range=2d&interval=1m&includePrePost=true"
        )
        payload = await self._fetch_json(chart_url)
        chart_result = (((payload or {}).get("chart") or {}).get("result") or [None])[0]
        if not chart_result:
            return None

        meta = chart_result.get("meta") or {}
        price = self._extract_latest_trade_price(chart_result)
        if price is None:
            price = self._coerce_float(meta.get("regularMarketPrice"))
        previous_close = self._coerce_float(
            meta.get("previousClose") or meta.get("chartPreviousClose") or meta.get("regularMarketPreviousClose")
        )
        if price is None or previous_close in (None, 0):
            return None

        change_value = price - previous_close
        return {
            "symbol": symbol,
            "name": meta.get("shortName") or meta.get("longName") or symbol,
            "price": price,
            "change": round(change_value, 4),
            "change_percent": self._truncate_percent((change_value / previous_close) * 100),
            "currency": meta.get("currency", "USD"),
            "market": self._normalize_yahoo_market(meta.get("exchangeName") or meta.get("fullExchangeName")),
            "source": f"global:yahoo_extended_quote:{symbol}",
        }

    async def _fetch_yahoo_fundamentals(self, symbol: str) -> Optional[Dict[str, Any]]:
        url = (
            "https://query1.finance.yahoo.com/ws/fundamentals-timeseries/v1/finance/timeseries/"
            f"{symbol}?type=annualTotalRevenue,annualOperatingIncome,annualNetIncome,annualDilutedEPS,"
            "annualCurrentAssets,annualCurrentLiabilities,annualTotalAssets,"
            "annualTotalLiabilitiesNetMinorityInterest,annualStockholdersEquity,annualFreeCashFlow"
            "&period1=1609459200&period2=1893456000"
        )
        payload = await self._fetch_json(url)
        result = (((payload or {}).get("timeseries") or {}).get("result") or [])
        if not result:
            return None

        rows = {((item.get("meta") or {}).get("type") or [None])[0]: item for item in result}
        latest_revenue = self._latest_reported_value(rows.get("annualTotalRevenue"), "annualTotalRevenue")
        prev_revenue = self._previous_reported_value(rows.get("annualTotalRevenue"), "annualTotalRevenue")
        latest_operating_income = self._latest_reported_value(rows.get("annualOperatingIncome"), "annualOperatingIncome")
        latest_net_income = self._latest_reported_value(rows.get("annualNetIncome"), "annualNetIncome")
        latest_eps = self._latest_reported_value(rows.get("annualDilutedEPS"), "annualDilutedEPS")
        prev_eps = self._previous_reported_value(rows.get("annualDilutedEPS"), "annualDilutedEPS")
        latest_current_assets = self._latest_reported_value(rows.get("annualCurrentAssets"), "annualCurrentAssets")
        latest_current_liabilities = self._latest_reported_value(rows.get("annualCurrentLiabilities"), "annualCurrentLiabilities")
        latest_total_assets = self._latest_reported_value(rows.get("annualTotalAssets"), "annualTotalAssets")
        latest_total_liabilities = self._latest_reported_value(
            rows.get("annualTotalLiabilitiesNetMinorityInterest"),
            "annualTotalLiabilitiesNetMinorityInterest",
        )
        latest_equity = self._latest_reported_value(rows.get("annualStockholdersEquity"), "annualStockholdersEquity")
        latest_free_cash_flow = self._latest_reported_value(rows.get("annualFreeCashFlow"), "annualFreeCashFlow")
        prev_free_cash_flow = self._previous_reported_value(rows.get("annualFreeCashFlow"), "annualFreeCashFlow")

        revenue_growth = self._growth_ratio(latest_revenue, prev_revenue)
        earnings_growth = self._growth_ratio(latest_eps, prev_eps)
        free_cash_flow_growth = self._growth_ratio(latest_free_cash_flow, prev_free_cash_flow)
        operating_margin = self._safe_divide(latest_operating_income, latest_revenue)
        profit_margin = self._safe_divide(latest_net_income, latest_revenue)
        current_ratio = self._safe_divide(latest_current_assets, latest_current_liabilities)
        debt_to_equity = self._safe_divide(latest_total_liabilities, latest_equity, scale=100)
        return_on_equity = self._safe_divide(latest_net_income, latest_equity)
        asset_turnover = self._safe_divide(latest_revenue, latest_total_assets)

        parsed = {
            "symbol": symbol,
            "revenue_growth": revenue_growth,
            "earnings_growth": earnings_growth,
            "free_cash_flow_growth": free_cash_flow_growth,
            "operating_margins": operating_margin,
            "profit_margins": profit_margin,
            "return_on_equity": return_on_equity,
            "debt_to_equity": debt_to_equity,
            "current_ratio": current_ratio,
            "asset_turnover": asset_turnover,
            "latest_revenue": latest_revenue,
            "latest_net_income": latest_net_income,
            "latest_eps": latest_eps,
        }

        if not any(
            parsed.get(key) is not None
            for key in (
                "revenue_growth",
                "earnings_growth",
                "profit_margins",
                "debt_to_equity",
                "current_ratio",
            )
        ):
            return None
        return parsed

    async def _fetch_json(self, url: str) -> Optional[Dict[str, Any]]:
        timeout = aiohttp.ClientTimeout(total=settings.request_timeout)
        headers = {"User-Agent": "Mozilla/5.0"}
        try:
            async with aiohttp.ClientSession(timeout=timeout) as session:
                async with session.get(url, headers=headers) as response:
                    if response.status == 200:
                        return await response.json()
                    self.logger.warning("Yahoo fetch failed: %s %s", url, response.status)
        except Exception as exc:
            self.logger.warning("Yahoo fetch error for %s: %s", url, exc)

        try:
            response = requests.get(url, headers=headers, timeout=settings.request_timeout)
            if response.status_code == 200:
                return response.json()
            self.logger.warning("Yahoo requests fallback failed: %s %s", url, response.status_code)
        except Exception as exc:
            self.logger.warning("Yahoo requests fallback error for %s: %s", url, exc)
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

    def _get_cached_fundamentals(self, symbol: str) -> Optional[Dict[str, Any]]:
        cached = self.fundamentals_cache.get(symbol)
        if not cached:
            return None
        if time.time() > cached["expires_at"]:
            self.fundamentals_cache.pop(symbol, None)
            return None
        return dict(cached["data"])

    def _save_cached_fundamentals(self, symbol: str, fundamentals: Dict[str, Any]) -> None:
        self.fundamentals_cache[symbol] = {
            "data": dict(fundamentals),
            "expires_at": time.time() + self.fundamentals_cache_ttl,
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
    def _extract_raw(value: Any) -> Optional[float]:
        if isinstance(value, dict):
            value = value.get("raw")
        return GlobalQuoteService._coerce_float(value)

    def _extract_latest_trade_price(self, chart_result: Dict[str, Any]) -> Optional[float]:
        quote = (((chart_result.get("indicators") or {}).get("quote") or [None])[0]) or {}
        closes = quote.get("close") or []
        for value in reversed(closes):
            coerced = self._coerce_float(value)
            if coerced is not None and coerced > 0:
                return coerced
        return None

    @staticmethod
    def _latest_reported_value(item: Optional[Dict[str, Any]], key: str) -> Optional[float]:
        if not item:
            return None
        values = item.get(key) or []
        if not values:
            return None
        latest = values[-1]
        return GlobalQuoteService._extract_raw(latest.get("reportedValue"))

    @staticmethod
    def _previous_reported_value(item: Optional[Dict[str, Any]], key: str) -> Optional[float]:
        if not item:
            return None
        values = item.get(key) or []
        if len(values) < 2:
            return None
        previous = values[-2]
        return GlobalQuoteService._extract_raw(previous.get("reportedValue"))

    @staticmethod
    def _growth_ratio(current: Optional[float], previous: Optional[float]) -> Optional[float]:
        if current is None or previous in (None, 0):
            return None
        return (current - previous) / abs(previous)

    @staticmethod
    def _safe_divide(numerator: Optional[float], denominator: Optional[float], scale: float = 1.0) -> Optional[float]:
        if numerator is None or denominator in (None, 0):
            return None
        return (numerator / denominator) * scale

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
