import logging
from statistics import mean
from typing import Dict, List, Optional, Tuple

import aiohttp
from bs4 import BeautifulSoup

from src.config.settings import settings
from src.services.news_service import NewsService
from src.services.stock_service import StockService


class AnalysisService:
    def __init__(self) -> None:
        self.logger = logging.getLogger(__name__)
        self.news_service = NewsService()
        self.stock_service = StockService()

    async def get_stock_analysis(self, symbol: str, market: Optional[str] = None, period: str = "short") -> Optional[Dict]:
        quote = await self.stock_service.get_stock_quote(symbol)
        stock_name = str(quote.get("name") or symbol.upper()) if quote else symbol.upper()
        stock_market = market or (quote.get("market") if quote else None)
        price_unit = str(quote.get("currency") or ("USD" if not symbol.isdigit() else "KRW")) if quote else ("USD" if not symbol.isdigit() else "KRW")
        analysis_window = self._get_analysis_window(period)

        yahoo_symbol = await self._resolve_stock_symbol(symbol, stock_market)
        history = await self._fetch_history(
            yahoo_symbol,
            range_value=analysis_window["range"],
            interval_value=analysis_window["interval"],
        )
        if not history:
            return None
        if symbol.isdigit():
            investor_flow = await self._fetch_investor_flow(symbol)
        else:
            investor_flow = self._build_global_flow(history)
        news_context = await self._build_news_context(symbol=symbol.upper(), name=stock_name, asset_type="stock")
        return self._build_analysis(
            history=history,
            asset_type="stock",
            symbol=symbol.upper(),
            name=stock_name,
            price_unit=price_unit,
            source=f"yahoo_chart:{yahoo_symbol}",
            timeframe=analysis_window["label"],
            investor_flow=investor_flow,
            news_context=news_context,
        )

    async def get_currency_analysis(self, base: str, target: str, period: str = "short") -> Optional[Dict]:
        pair = f"{base.upper()}{target.upper()}=X"
        analysis_window = self._get_analysis_window(period)
        history = await self._fetch_history(
            pair,
            range_value=analysis_window["range"],
            interval_value=analysis_window["interval"],
        )
        if not history:
            return None
        news_context = await self._build_news_context(
            symbol=f"{base.upper()}/{target.upper()}",
            name=f"{base.upper()}/{target.upper()}",
            asset_type="currency",
        )
        return self._build_analysis(
            history=history,
            asset_type="currency",
            symbol=f"{base.upper()}/{target.upper()}",
            name=f"{base.upper()}/{target.upper()}",
            price_unit=target.upper(),
            source=f"yahoo_chart:{pair}",
            timeframe=analysis_window["label"],
            investor_flow=None,
            news_context=news_context,
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
            history = await self._fetch_history(candidate, range_value="1mo", interval_value="1d")
            if history:
                return candidate
        return candidates[0]

    async def _fetch_history(self, yahoo_symbol: str, range_value: str = "6mo", interval_value: str = "1d") -> List[Dict[str, float]]:
        url = (
            "https://query1.finance.yahoo.com/v8/finance/chart/"
            f"{yahoo_symbol}?range={range_value}&interval={interval_value}&includePrePost=false"
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
        volumes = quote.get("volume") or []

        candles: List[Dict[str, float]] = []
        for open_, high, low, close, volume in zip(opens, highs, lows, closes, volumes):
            if None in (open_, high, low, close):
                continue
            candles.append(
                {
                    "open": float(open_),
                    "high": float(high),
                    "low": float(low),
                    "close": float(close),
                    "volume": float(volume) if volume is not None else 0.0,
                }
            )
        return candles

    @staticmethod
    def _get_analysis_window(period: str) -> Dict[str, str]:
        normalized = (period or "short").lower()
        mapping = {
            "short": {"range": "6mo", "interval": "1d", "label": "단기 · 일봉 기준 최근 6개월"},
            "medium": {"range": "2y", "interval": "1wk", "label": "중기 · 주봉 기준 최근 2년"},
            "long": {"range": "5y", "interval": "1mo", "label": "장기 · 월봉 기준 최근 5년"},
        }
        return mapping.get(normalized, mapping["short"])

    async def _fetch_investor_flow(self, symbol: str) -> Optional[Dict]:
        url = f"https://finance.naver.com/item/main.naver?code={symbol}"
        timeout = aiohttp.ClientTimeout(total=settings.request_timeout)
        try:
            async with aiohttp.ClientSession(timeout=timeout) as session:
                async with session.get(url, headers={"User-Agent": "Mozilla/5.0"}) as response:
                    if response.status != 200:
                        return None
                    html = await response.text()
        except Exception as exc:
            self.logger.warning("Investor flow fetch failed for %s: %s", symbol, exc)
            return None

        soup = BeautifulSoup(html, "html.parser")
        table = None
        for candidate in soup.select("table.tb_type1"):
            caption = candidate.find("caption")
            if caption and "외국인 기관" in caption.get_text(" ", strip=True):
                table = candidate
                break
        if table is None:
            return None

        rows = []
        for tr in table.select("tbody tr"):
            cols = tr.find_all(["th", "td"])
            if len(cols) < 5:
                continue
            date = cols[0].get_text(" ", strip=True)
            foreign = self._parse_numeric_value(cols[3].get_text(" ", strip=True))
            institution = self._parse_numeric_value(cols[4].get_text(" ", strip=True))
            if foreign is None or institution is None:
                continue
            rows.append({"date": date, "foreign": int(foreign), "institution": int(institution)})
            if len(rows) >= 5:
                break

        if not rows:
            return None

        latest = rows[0]
        foreign_5d = sum(item["foreign"] for item in rows)
        institution_5d = sum(item["institution"] for item in rows)

        def direction(value: int) -> str:
            if value > 0:
                return "순매수"
            if value < 0:
                return "순매도"
            return "중립"

        return {
            "market_scope": "domestic",
            "latest_date": latest["date"],
            "latest_foreign": latest["foreign"],
            "latest_institution": latest["institution"],
            "foreign_5d": foreign_5d,
            "institution_5d": institution_5d,
            "foreign_direction": direction(foreign_5d),
            "institution_direction": direction(institution_5d),
            "summary": f"최근 5거래일 외국인 {direction(foreign_5d)}, 기관 {direction(institution_5d)}",
        }

    def _build_global_flow(self, history: List[Dict[str, float]]) -> Optional[Dict]:
        if len(history) < 25:
            return None

        recent = history[-20:]
        closes = [item["close"] for item in recent]
        volumes = [item.get("volume", 0.0) for item in recent]

        signed_notional = 0.0
        up_volume = 0.0
        down_volume = 0.0
        obv = 0.0
        obv_20 = []
        adl = 0.0
        adl_20 = []
        previous_close = history[-21]["close"]

        for candle in recent:
            close = candle["close"]
            volume = candle.get("volume", 0.0) or 0.0
            high = candle["high"]
            low = candle["low"]

            if close > previous_close:
                signed_notional += close * volume
                up_volume += volume
                obv += volume
            elif close < previous_close:
                signed_notional -= close * volume
                down_volume += volume
                obv -= volume

            spread = high - low
            money_flow_multiplier = ((close - low) - (high - close)) / spread if spread else 0.0
            adl += money_flow_multiplier * volume

            obv_20.append(obv)
            adl_20.append(adl)
            previous_close = close

        flow_ratio = (up_volume / down_volume) if down_volume > 0 else (9.99 if up_volume > 0 else None)
        obv_change = obv_20[-1] - obv_20[0]
        adl_change = adl_20[-1] - adl_20[0]

        positives = sum(1 for value in (signed_notional, obv_change, adl_change) if value > 0)
        negatives = sum(1 for value in (signed_notional, obv_change, adl_change) if value < 0)
        if positives >= 2 and (flow_ratio or 0) >= 1:
            flow_label = "유입 우위"
        elif negatives >= 2 and (flow_ratio or 0) <= 1:
            flow_label = "유출 우위"
        else:
            flow_label = "혼조"

        def direction(value: float) -> str:
            if value > 0:
                return "유입"
            if value < 0:
                return "유출"
            return "중립"

        return {
            "market_scope": "global",
            "flow_type": "price_volume",
            "flow_label": flow_label,
            "money_flow_20d": round(signed_notional, 2),
            "up_down_volume_ratio": round(flow_ratio, 2) if flow_ratio is not None else None,
            "obv_direction": direction(obv_change),
            "adl_direction": direction(adl_change),
            "summary": "최근 20거래일 가격·거래량 흐름으로 계산한 해외주식 수급 추정입니다.",
        }

    async def _build_news_context(self, symbol: str, name: str, asset_type: str) -> Dict:
        queries = [symbol]
        if name and name.lower() != symbol.lower():
            queries.append(name)

        related_articles = []
        for query in queries[:2]:
            articles = await self.news_service.get_latest_news(query=query, limit=3)
            for article in articles:
                if article["title"] not in {item["title"] for item in related_articles}:
                    related_articles.append(article)

        macro_articles = await self.news_service.get_latest_news(limit=8)
        macro_signals = self._extract_macro_signals(macro_articles, asset_type)

        impact_score = 0
        if related_articles:
            impact_score += self._score_articles(related_articles, asset_type)
        impact_score += sum(signal["score"] for signal in macro_signals)

        if impact_score >= 2:
            bias = "우호적"
        elif impact_score <= -2:
            bias = "부담"
        else:
            bias = "중립"

        return {
            "news_bias": bias,
            "related_headlines": [item["title"] for item in related_articles[:3]],
            "macro_headlines": [item["headline"] for item in macro_signals[:3]],
            "summary": self._compose_news_summary(bias, related_articles, macro_signals, asset_type),
        }

    def _build_analysis(
        self,
        history: List[Dict[str, float]],
        asset_type: str,
        symbol: str,
        name: str,
        price_unit: str,
        source: str,
        timeframe: str,
        investor_flow: Optional[Dict],
        news_context: Dict,
    ) -> Dict:
        closes = [item["close"] for item in history]
        highs = [item["high"] for item in history]
        lows = [item["low"] for item in history]
        volumes = [item.get("volume", 0.0) for item in history]

        current = closes[-1]
        sma20 = mean(closes[-20:]) if len(closes) >= 20 else mean(closes)
        sma60 = mean(closes[-60:]) if len(closes) >= 60 else mean(closes)
        low20 = min(lows[-20:]) if len(lows) >= 20 else min(lows)
        low60 = min(lows[-60:]) if len(lows) >= 60 else min(lows)
        high20 = max(highs[-20:]) if len(highs) >= 20 else max(highs)
        high60 = max(highs[-60:]) if len(highs) >= 60 else max(highs)
        rsi14 = self._calculate_rsi(closes, 14)
        macd_line, macd_signal, macd_hist = self._calculate_macd(closes)
        atr14 = self._calculate_atr(history, 14)
        volume_ratio = self._calculate_volume_ratio(volumes, 20)
        volume_signal = self._label_volume_signal(volume_ratio)

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

        confidence_score = self._calculate_confidence(
            current=current,
            sma20=sma20,
            sma60=sma60,
            low20=low20,
            high20=high20,
            supports=supports,
            resistances=resistances,
            rsi14=rsi14,
            macd_hist=macd_hist,
            volume_ratio=volume_ratio,
            investor_flow=investor_flow,
            news_context=news_context,
        )
        confidence_label = self._label_confidence(confidence_score)

        notes = [
            f"20일 평균 {self._fmt(sma20, price_unit, asset_type)}, 60일 평균 {self._fmt(sma60, price_unit, asset_type)} 기준입니다.",
            f"최근 20일 고점/저점은 {self._fmt(high20, price_unit, asset_type)} / {self._fmt(low20, price_unit, asset_type)} 입니다.",
            f"1차 매수는 현재가 아래의 가까운 지지선, 2차 매수는 중기 지지선 기준입니다.",
            f"1차 매도는 단기 저항, 2차 매도는 최근 중기 고점 기준입니다.",
            f"거래량 신호는 최근 20일 평균 대비 비율({volume_ratio:.2f}배)로 계산합니다." if volume_ratio is not None else "거래량 데이터는 현재 분석에 반영되지 않았습니다.",
            (
                f"RSI(14)는 {rsi14:.2f}, MACD 히스토그램은 {macd_hist:.4f}, ATR(14)는 {atr14:.4f} 입니다."
                if None not in (rsi14, macd_hist, atr14)
                else "보조지표는 사용 가능한 최근 데이터 범위에서 계산했습니다."
            ),
            "이 신뢰도는 가격 구조 일치도를 수치화한 값이며, 실제 수익률 정확도를 보장하지는 않습니다.",
        ]
        if investor_flow:
            notes.append(investor_flow["summary"])
            if investor_flow.get("market_scope") == "global":
                notes.append("해외주식 수급은 무료 가격·거래량 데이터 기반 추정치이며, 기관/외국인 실거래 집계는 아닙니다.")
        if news_context.get("summary"):
            notes.append(news_context["summary"])

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
            "confidence_score": confidence_score,
            "confidence_label": confidence_label,
            "volume_ratio": round(volume_ratio, 2) if volume_ratio is not None else None,
            "volume_signal": volume_signal,
            "rsi14": round(rsi14, 2) if rsi14 is not None else None,
            "macd": round(macd_line, 4) if macd_line is not None else None,
            "macd_signal": round(macd_signal, 4) if macd_signal is not None else None,
            "macd_histogram": round(macd_hist, 4) if macd_hist is not None else None,
            "atr14": round(atr14, 4) if atr14 is not None else None,
            "investor_flow": investor_flow,
            "news_bias": news_context.get("news_bias"),
            "market_context": news_context.get("summary"),
            "related_headlines": news_context.get("related_headlines", []),
            "macro_headlines": news_context.get("macro_headlines", []),
            "timeframe": timeframe,
            "source": source,
            "notes": notes,
        }

    @staticmethod
    def _parse_numeric_value(value: str) -> Optional[float]:
        cleaned = "".join(ch for ch in value if ch.isdigit() or ch in ".-")
        if not cleaned or cleaned in {"-", ".", "-."}:
            return None
        try:
            return float(cleaned)
        except ValueError:
            return None

    @staticmethod
    def _fmt(value: float, unit: str, asset_type: str) -> str:
        if asset_type == "currency":
            return f"{value:,.4f} {unit}"
        if unit == "KRW":
            return f"{value:,.0f}원"
        if unit == "USD":
            return f"{value:,.2f} USD"
        return f"{value:,.4f} {unit}"

    @staticmethod
    def _calculate_confidence(
        current: float,
        sma20: float,
        sma60: float,
        low20: float,
        high20: float,
        supports: List[float],
        resistances: List[float],
        rsi14: Optional[float],
        macd_hist: Optional[float],
        volume_ratio: Optional[float],
        investor_flow: Optional[Dict],
        news_context: Dict,
    ) -> int:
        score = 50

        if current >= sma20 >= sma60 or current <= sma20 <= sma60:
            score += 18
        elif abs(sma20 - sma60) / current <= 0.01:
            score -= 8

        if supports:
            nearest_support_gap = abs(current - supports[0]) / current
            if nearest_support_gap <= 0.03:
                score += 10
            elif nearest_support_gap >= 0.08:
                score -= 6

        if resistances:
            nearest_resistance_gap = abs(resistances[0] - current) / current
            if nearest_resistance_gap <= 0.03:
                score += 10
            elif nearest_resistance_gap >= 0.08:
                score -= 6

        range_ratio = (high20 - low20) / current if current else 0
        if range_ratio <= 0.08:
            score += 8
        elif range_ratio >= 0.2:
            score -= 10

        if rsi14 is not None:
            if 35 <= rsi14 <= 65:
                score += 6
            elif rsi14 <= 25 or rsi14 >= 75:
                score -= 4

        if macd_hist is not None:
            if abs(macd_hist) / current <= 0.015:
                score += 4

        if volume_ratio is not None:
            if 0.9 <= volume_ratio <= 1.8:
                score += 5
            elif volume_ratio >= 2.5:
                score -= 3

        if investor_flow:
            if investor_flow.get("market_scope") == "domestic" and investor_flow["foreign_direction"] == investor_flow["institution_direction"] != "중립":
                score += 5
            elif investor_flow.get("market_scope") == "global":
                if investor_flow.get("flow_label") == "유입 우위":
                    score += 4
                elif investor_flow.get("flow_label") == "유출 우위":
                    score -= 4

        if news_context.get("news_bias") == "우호적":
            score += 3
        elif news_context.get("news_bias") == "부담":
            score -= 3

        return max(35, min(88, int(round(score))))

    @staticmethod
    def _label_confidence(score: int) -> str:
        if score >= 75:
            return "높음"
        if score >= 60:
            return "보통"
        return "낮음"

    @staticmethod
    def _calculate_rsi(closes: List[float], period: int) -> Optional[float]:
        if len(closes) <= period:
            return None
        gains = []
        losses = []
        for previous, current in zip(closes[:-1], closes[1:]):
            delta = current - previous
            gains.append(max(delta, 0))
            losses.append(abs(min(delta, 0)))
        avg_gain = mean(gains[-period:])
        avg_loss = mean(losses[-period:])
        if avg_loss == 0:
            return 100.0
        rs = avg_gain / avg_loss
        return 100 - (100 / (1 + rs))

    @staticmethod
    def _ema(values: List[float], period: int) -> List[float]:
        multiplier = 2 / (period + 1)
        ema_values = [values[0]]
        for value in values[1:]:
            ema_values.append((value - ema_values[-1]) * multiplier + ema_values[-1])
        return ema_values

    def _calculate_macd(self, closes: List[float]) -> Tuple[Optional[float], Optional[float], Optional[float]]:
        if len(closes) < 35:
            return None, None, None
        ema12 = self._ema(closes, 12)
        ema26 = self._ema(closes, 26)
        macd_series = [a - b for a, b in zip(ema12[-len(ema26):], ema26)]
        signal_series = self._ema(macd_series, 9)
        macd_line = macd_series[-1]
        signal_line = signal_series[-1]
        histogram = macd_line - signal_line
        return macd_line, signal_line, histogram

    @staticmethod
    def _calculate_atr(history: List[Dict[str, float]], period: int) -> Optional[float]:
        if len(history) <= period:
            return None
        true_ranges = []
        prev_close = history[0]["close"]
        for candle in history[1:]:
            tr = max(
                candle["high"] - candle["low"],
                abs(candle["high"] - prev_close),
                abs(candle["low"] - prev_close),
            )
            true_ranges.append(tr)
            prev_close = candle["close"]
        return mean(true_ranges[-period:]) if true_ranges else None

    @staticmethod
    def _calculate_volume_ratio(volumes: List[float], period: int) -> Optional[float]:
        if len(volumes) <= period:
            return None
        latest = volumes[-1]
        average = mean(volumes[-period:])
        if average <= 0:
            return None
        return latest / average

    @staticmethod
    def _label_volume_signal(volume_ratio: Optional[float]) -> str:
        if volume_ratio is None:
            return "데이터 없음"
        if volume_ratio >= 1.8:
            return "거래량 급증"
        if volume_ratio >= 1.1:
            return "거래량 증가"
        if volume_ratio <= 0.7:
            return "거래량 위축"
        return "평균 수준"

    @staticmethod
    def _extract_macro_signals(articles: List[Dict[str, str]], asset_type: str) -> List[Dict[str, int]]:
        keyword_scores = {
            "rate": -1,
            "inflation": -1,
            "tariff": -1,
            "war": -2,
            "oil": -1 if asset_type == "stock" else 0,
            "fed": -1,
            "treasury": -1,
            "stimulus": 1,
            "ai": 1,
            "chip": 1,
            "soft landing": 1,
            "cut": 1,
        }

        signals: List[Dict[str, int]] = []
        for article in articles:
            combined = f"{article['title']} {article['summary']}".lower()
            score = 0
            matched = []
            for keyword, keyword_score in keyword_scores.items():
                if keyword in combined:
                    score += keyword_score
                    matched.append(keyword)
            if score == 0:
                continue
            signals.append({"headline": article["title"], "score": score, "keywords": ",".join(matched)})
        return signals

    @staticmethod
    def _score_articles(articles: List[Dict[str, str]], asset_type: str) -> int:
        positive_words = ["beat", "surge", "growth", "partnership", "record", "gain", "rally", "strong"]
        negative_words = ["fall", "drop", "delay", "risk", "probe", "cut", "warn", "miss", "tariff", "war"]
        score = 0
        for article in articles:
            combined = f"{article['title']} {article['summary']}".lower()
            score += sum(1 for word in positive_words if word in combined)
            score -= sum(1 for word in negative_words if word in combined)
        if asset_type == "currency":
            score = int(score / 2)
        return score

    @staticmethod
    def _compose_news_summary(
        bias: str,
        related_articles: List[Dict[str, str]],
        macro_signals: List[Dict[str, int]],
        asset_type: str,
    ) -> str:
        if related_articles:
            lead = "종목 관련 최신 뉴스"
        elif asset_type == "currency":
            lead = "환율 관련 거시 뉴스"
        else:
            lead = "시장 거시 뉴스"

        macro_hint = ""
        if macro_signals:
            macro_hint = f" 거시 변수는 {', '.join(signal['headline'] for signal in macro_signals[:2])} 중심으로 반영했습니다."

        return f"{lead} 기준으로 현재 뉴스 영향은 {bias} 쪽으로 해석됩니다.{macro_hint}"
