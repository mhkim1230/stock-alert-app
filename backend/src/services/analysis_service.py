import logging
from statistics import mean
from typing import Dict, List, Optional

import aiohttp

from src.config.settings import settings


class AnalysisService:
    def __init__(self) -> None:
        self.logger = logging.getLogger(__name__)

    async def get_stock_analysis(self, symbol: str, market: Optional[str] = None) -> Optional[Dict]:
        yahoo_symbol = await self._resolve_stock_symbol(symbol, market)
        history = await self._fetch_history(yahoo_symbol)
        if not history:
            return None
        name = symbol.upper()
        return self._build_analysis(
            history=history,
            asset_type="stock",
            symbol=symbol.upper(),
            name=name,
            price_unit="USD" if not symbol.isdigit() else "KRW",
            source=f"yahoo_chart:{yahoo_symbol}",
            timeframe="최근 6개월 일봉",
        )

    async def get_currency_analysis(self, base: str, target: str) -> Optional[Dict]:
        pair = f"{base.upper()}{target.upper()}=X"
        history = await self._fetch_history(pair)
        if not history:
            return None
        return self._build_analysis(
            history=history,
            asset_type="currency",
            symbol=f"{base.upper()}/{target.upper()}",
            name=f"{base.upper()}/{target.upper()}",
            price_unit=target.upper(),
            source=f"yahoo_chart:{pair}",
            timeframe="최근 6개월 일봉",
        )

    async def _resolve_stock_symbol(self, symbol: str, market: Optional[str]) -> str:
        normalized = symbol.upper()
        if not normalized.isdigit():
            return normalized

        candidates: List[str]
        if market == "KOSDAQ":
            candidates = [f"{normalized}.KQ", f"{normalized}.KS"]
        elif market == "KOSPI":
            candidates = [f"{normalized}.KS", f"{normalized}.KQ"]
        else:
            candidates = [f"{normalized}.KS", f"{normalized}.KQ"]

        for candidate in candidates:
            history = await self._fetch_history(candidate)
            if history:
                return candidate
        return candidates[0]

    async def _fetch_history(self, yahoo_symbol: str) -> List[Dict[str, float]]:
        url = (
            "https://query1.finance.yahoo.com/v8/finance/chart/"
            f"{yahoo_symbol}?range=6mo&interval=1d&includePrePost=false"
        )
        timeout = aiohttp.ClientTimeout(total=settings.request_timeout)

        try:
            async with aiohttp.ClientSession(timeout=timeout) as session:
                async with session.get(url, headers={"User-Agent": "Mozilla/5.0"}) as response:
                    if response.status != 200:
                        self.logger.warning("Analysis history fetch failed: %s %s", yahoo_symbol, response.status)
                        return []
                    payload = await response.json()
        except Exception as exc:
            self.logger.warning("Analysis history fetch error for %s: %s", yahoo_symbol, exc)
            return []

        result = (((payload or {}).get("chart") or {}).get("result") or [None])[0]
        if not result:
            return []

        quote = (((result.get("indicators") or {}).get("quote") or [None])[0]) or {}
        closes = quote.get("close") or []
        highs = quote.get("high") or []
        lows = quote.get("low") or []
        opens = quote.get("open") or []

        candles: List[Dict[str, float]] = []
        for open_, high, low, close in zip(opens, highs, lows, closes):
            if None in (open_, high, low, close):
                continue
            candles.append(
                {
                    "open": float(open_),
                    "high": float(high),
                    "low": float(low),
                    "close": float(close),
                }
            )
        return candles

    def _build_analysis(
        self,
        history: List[Dict[str, float]],
        asset_type: str,
        symbol: str,
        name: str,
        price_unit: str,
        source: str,
        timeframe: str,
    ) -> Dict:
        closes = [item["close"] for item in history]
        highs = [item["high"] for item in history]
        lows = [item["low"] for item in history]

        current = closes[-1]
        sma20 = mean(closes[-20:]) if len(closes) >= 20 else mean(closes)
        sma60 = mean(closes[-60:]) if len(closes) >= 60 else mean(closes)
        low20 = min(lows[-20:]) if len(lows) >= 20 else min(lows)
        low60 = min(lows[-60:]) if len(lows) >= 60 else min(lows)
        high20 = max(highs[-20:]) if len(highs) >= 20 else max(highs)
        high60 = max(highs[-60:]) if len(highs) >= 60 else max(highs)

        if current >= sma20 >= sma60:
            trend = "상승"
            bias = "눌림목 매수 우위"
        elif current <= sma20 <= sma60:
            trend = "하락"
            bias = "보수적 접근"
        else:
            trend = "횡보"
            bias = "박스권 대응"

        supports = sorted(
            {
                round(value, 6)
                for value in (
                    low20,
                    low60,
                    sma20,
                    sma60,
                    current * 0.97,
                    current * 0.92,
                )
                if value < current
            },
            reverse=True,
        )
        resistances = sorted(
            {
                round(value, 6)
                for value in (
                    high20,
                    high60,
                    current * 1.03,
                    current * 1.08,
                )
                if value > current
            }
        )

        first_buy = supports[0] if supports else current * 0.97
        second_buy = supports[1] if len(supports) > 1 else current * 0.92
        first_sell = resistances[0] if resistances else current * 1.03
        second_sell = resistances[1] if len(resistances) > 1 else current * 1.08
        stop_loss = min(second_buy * 0.98, low60 * 0.99)

        notes = [
            f"20일 평균 {self._fmt(sma20, price_unit, asset_type)}, 60일 평균 {self._fmt(sma60, price_unit, asset_type)} 기준입니다.",
            f"최근 20일 고점/저점은 {self._fmt(high20, price_unit, asset_type)} / {self._fmt(low20, price_unit, asset_type)} 입니다.",
            f"1차 매수는 현재가 아래의 가까운 지지선, 2차 매수는 중기 지지선 기준입니다.",
            f"1차 매도는 단기 저항, 2차 매도는 최근 중기 고점 기준입니다.",
        ]

        return {
            "asset_type": asset_type,
            "symbol": symbol,
            "name": name,
            "current_price": round(current, 4),
            "price_unit": price_unit,
            "trend": trend,
            "bias": bias,
            "first_buy": round(first_buy, 4),
            "second_buy": round(second_buy, 4),
            "first_sell": round(first_sell, 4),
            "second_sell": round(second_sell, 4),
            "stop_loss": round(stop_loss, 4),
            "timeframe": timeframe,
            "source": source,
            "notes": notes,
        }

    @staticmethod
    def _fmt(value: float, unit: str, asset_type: str) -> str:
        if asset_type == "currency":
            return f"{value:,.4f} {unit}"
        if unit == "KRW":
            return f"{value:,.0f}원"
        if unit == "USD":
            return f"{value:,.2f} USD"
        return f"{value:,.4f} {unit}"
