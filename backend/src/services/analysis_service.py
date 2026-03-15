import logging
from statistics import mean, pstdev
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
            period=period,
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
            period=period,
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
            "intraday": {"range": "10d", "interval": "30m", "label": "30분 · 30분봉 기준 최근 10일"},
            "short": {"range": "6mo", "interval": "1d", "label": "단기 · 일봉 기준 최근 6개월"},
            "medium": {"range": "2y", "interval": "1wk", "label": "중기 · 주봉 기준 최근 2년"},
            "long": {"range": "5y", "interval": "1mo", "label": "장기 · 월봉 기준 최근 5년"},
        }
        return mapping.get(normalized, mapping["short"])

    @staticmethod
    def _get_strategy_profile(period: str) -> Dict[str, float]:
        normalized = (period or "short").lower()
        profiles = {
            "intraday": {
                "primary_span": 16,
                "secondary_span": 48,
                "buy_gap_1": 0.012,
                "buy_gap_2": 0.028,
                "sell_gap_1": 0.012,
                "sell_gap_2": 0.028,
                "stop_factor": 0.992,
                "low_factor": 0.996,
                "primary_label": "16봉",
                "secondary_label": "48봉",
            },
            "short": {
                "primary_span": 20,
                "secondary_span": 60,
                "buy_gap_1": 0.03,
                "buy_gap_2": 0.08,
                "sell_gap_1": 0.03,
                "sell_gap_2": 0.08,
                "stop_factor": 0.98,
                "low_factor": 0.99,
                "primary_label": "20봉",
                "secondary_label": "60봉",
            },
            "medium": {
                "primary_span": 13,
                "secondary_span": 26,
                "buy_gap_1": 0.06,
                "buy_gap_2": 0.14,
                "sell_gap_1": 0.06,
                "sell_gap_2": 0.14,
                "stop_factor": 0.965,
                "low_factor": 0.985,
                "primary_label": "13주",
                "secondary_label": "26주",
            },
            "long": {
                "primary_span": 12,
                "secondary_span": 36,
                "buy_gap_1": 0.1,
                "buy_gap_2": 0.22,
                "sell_gap_1": 0.1,
                "sell_gap_2": 0.22,
                "stop_factor": 0.94,
                "low_factor": 0.975,
                "primary_label": "12개월",
                "secondary_label": "36개월",
            },
        }
        return profiles.get(normalized, profiles["short"])

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
            "summary": self._compose_news_summary(bias, related_articles, macro_signals, asset_type),
            "themes": [item["label"] for item in macro_signals[:3]],
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
        period: str,
        investor_flow: Optional[Dict],
        news_context: Dict,
    ) -> Dict:
        closes = [item["close"] for item in history]
        highs = [item["high"] for item in history]
        lows = [item["low"] for item in history]
        volumes = [item.get("volume", 0.0) for item in history]
        profile = self._get_strategy_profile(period)

        current = closes[-1]
        previous_close = closes[-2] if len(closes) > 1 else closes[-1]
        primary_span = min(profile["primary_span"], len(closes))
        secondary_span = min(profile["secondary_span"], len(closes))
        sma20 = mean(closes[-primary_span:]) if len(closes) >= primary_span else mean(closes)
        sma60 = mean(closes[-secondary_span:]) if len(closes) >= secondary_span else mean(closes)
        prev_sma20 = mean(closes[-primary_span - 1:-1]) if len(closes) > primary_span else sma20
        prev_sma60 = mean(closes[-secondary_span - 1:-1]) if len(closes) > secondary_span else sma60
        low20 = min(lows[-primary_span:]) if len(lows) >= primary_span else min(lows)
        low60 = min(lows[-secondary_span:]) if len(lows) >= secondary_span else min(lows)
        high20 = max(highs[-primary_span:]) if len(highs) >= primary_span else max(highs)
        high60 = max(highs[-secondary_span:]) if len(highs) >= secondary_span else max(highs)
        rsi14 = self._calculate_rsi(closes, 14)
        macd_line, macd_signal, macd_hist = self._calculate_macd(closes)
        macd_metrics = self._calculate_macd_metrics(closes)
        stochastic = self._calculate_stochastic(history)
        atr14 = self._calculate_atr(history, 14)
        bollinger = self._calculate_bollinger(closes, min(20, len(closes)))
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
                    current * (1 - profile["buy_gap_1"]),
                    current * (1 - profile["buy_gap_2"]),
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
                    current * (1 + profile["sell_gap_1"]),
                    current * (1 + profile["sell_gap_2"]),
                )
                if value > current
            }
        )

        first_buy = supports[0] if supports else current * (1 - profile["buy_gap_1"])
        second_buy = supports[1] if len(supports) > 1 else current * (1 - profile["buy_gap_2"])
        first_sell = resistances[0] if resistances else current * (1 + profile["sell_gap_1"])
        second_sell = resistances[1] if len(resistances) > 1 else current * (1 + profile["sell_gap_2"])
        stop_loss = max(second_buy * profile["stop_factor"], low60 * profile["low_factor"])

        trend_score, trend_reasons = self._score_trend(
            current=current,
            previous_close=previous_close,
            sma20=sma20,
            sma60=sma60,
            prev_sma20=prev_sma20,
            macd_metrics=macd_metrics,
        )
        momentum_score, momentum_reasons, timing_summary = self._score_momentum(
            rsi14=rsi14,
            stochastic=stochastic,
        )
        volume_score, volume_reasons, volume_summary = self._score_volume(
            volume_ratio=volume_ratio,
            previous_close=previous_close,
            current=current,
        )
        volatility_score, volatility_reasons, volatility_summary = self._score_volatility(
            current=current,
            atr14=atr14,
            bollinger=bollinger,
        )
        risk_penalty, risk_reasons = self._score_risk(
            current=current,
            sma20=sma20,
            sma60=sma60,
            rsi14=rsi14,
            stochastic=stochastic,
            investor_flow=investor_flow,
            news_context=news_context,
            resistances=resistances,
            bollinger=bollinger,
            macd_metrics=macd_metrics,
        )

        final_score = max(0, min(100, trend_score + momentum_score + volume_score + volatility_score - risk_penalty))
        if final_score >= 60:
            final_action = "매수"
        elif final_score <= 30:
            final_action = "매도"
        else:
            final_action = "홀드"

        confidence_score = max(35, min(95, 35 + volume_score * 4 - max(0, risk_penalty - 6)))
        confidence_label = self._label_confidence(confidence_score)
        investor_summary = self._summarize_investor_flow(investor_flow)
        news_brief = news_context.get("summary")
        price_reference_summary = (
            f"1차 지지선은 {self._fmt(first_buy, price_unit, asset_type)}, 2차 지지선은 {self._fmt(second_buy, price_unit, asset_type)}입니다. "
            f"1차 저항선은 {self._fmt(first_sell, price_unit, asset_type)}, 2차 저항선은 {self._fmt(second_sell, price_unit, asset_type)}입니다."
        )
        decision_reasons = self._build_decision_reasons(
            final_action=final_action,
            trend_reasons=trend_reasons,
            momentum_reasons=momentum_reasons,
            volume_reasons=volume_reasons,
            risk_reasons=risk_reasons,
        )
        decision_summary = (
            f"최종 점수 {final_score}점으로 {final_action} 판단입니다. "
            f"추세 {trend_score}점, 모멘텀 {momentum_score}점, 거래량 {volume_score}점, 변동성 {volatility_score}점에 "
            f"위험 차감 {risk_penalty}점을 반영했습니다."
        )
        trend_summary = self._join_reason_summary(
            trend_reasons,
            fallback=f"{profile['primary_label']}선과 {profile['secondary_label']}선 위치를 기준으로 추세를 확인했습니다.",
        )
        risk_notes = self._build_risk_notes(
            trend=trend,
            rsi14=rsi14,
            macd_hist=macd_hist,
            atr14=atr14,
            volume_ratio=volume_ratio,
            investor_flow=investor_flow,
            news_context=news_context,
        )
        notes = self._build_reason_notes(
            trend=trend,
            sma20=sma20,
            sma60=sma60,
            high20=high20,
            low20=low20,
            price_unit=price_unit,
            asset_type=asset_type,
            volume_signal=volume_signal,
            rsi14=rsi14,
            macd_hist=macd_hist,
            investor_summary=investor_summary,
            news_brief=news_brief,
            profile=profile,
        )

        summary_title = f"최종 {final_score}점 · {final_action}"
        summary_body = decision_summary
        trend_outlook = trend_summary
        action_plan = self._join_reason_summary(
            decision_reasons,
            fallback="현재 구간에서는 가격 기준점을 지키는지 확인하면서 대응 강도를 조절하는 편이 좋습니다.",
        )
        buy_plan = self._join_reason_summary(
            trend_reasons[:2] + momentum_reasons[:1],
            fallback=f"1차 매수는 {self._fmt(first_buy, price_unit, asset_type)}, 2차 매수는 {self._fmt(second_buy, price_unit, asset_type)}입니다.",
        )
        sell_plan = self._join_reason_summary(
            volume_reasons[:1] + risk_reasons[:2],
            fallback=f"1차 매도는 {self._fmt(first_sell, price_unit, asset_type)}, 2차 매도는 {self._fmt(second_sell, price_unit, asset_type)}입니다.",
        )
        loss_cut_plan = f"손절 기준은 {self._fmt(stop_loss, price_unit, asset_type)} 이탈 여부입니다."

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
            "final_score": final_score,
            "final_action": final_action,
            "trend_score": trend_score,
            "momentum_score": momentum_score,
            "volume_score": volume_score,
            "volatility_score": volatility_score,
            "risk_penalty": risk_penalty,
            "summary_title": summary_title,
            "summary_body": summary_body,
            "trend_outlook": trend_outlook,
            "action_plan": action_plan,
            "buy_plan": buy_plan,
            "sell_plan": sell_plan,
            "loss_cut_plan": loss_cut_plan,
            "decision_summary": decision_summary,
            "trend_summary": trend_summary,
            "timing_summary": timing_summary,
            "volume_summary": volume_summary,
            "volatility_summary": volatility_summary,
            "price_reference_summary": price_reference_summary,
            "decision_reasons": decision_reasons,
            "trend_reasons": trend_reasons,
            "momentum_reasons": momentum_reasons,
            "volume_reasons": volume_reasons,
            "volatility_reasons": volatility_reasons,
            "risk_reasons": risk_reasons,
            "investor_summary": investor_summary,
            "news_brief": news_brief,
            "risk_notes": risk_notes,
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
    def _summarize_investor_flow(investor_flow: Optional[Dict]) -> Optional[str]:
        if not investor_flow:
            return None
        if investor_flow.get("market_scope") == "domestic":
            return investor_flow.get("summary")
        if investor_flow.get("market_scope") == "global":
            flow_label = investor_flow.get("flow_label", "혼조")
            ratio = investor_flow.get("up_down_volume_ratio")
            ratio_text = f"상승 거래량 우위 {ratio:.2f}배" if ratio is not None else "거래량 비율 확인 불가"
            return f"해외 수급 추정은 {flow_label}이며, {ratio_text} 흐름입니다."
        return None

    @staticmethod
    def _build_summary_title(trend: str, bias: str, confidence_label: str) -> str:
        if trend == "상승":
            return f"{confidence_label} 신뢰도의 상승 추세 대응 구간입니다."
        if trend == "하락":
            return f"{confidence_label} 신뢰도의 보수적 대응 구간입니다."
        if bias == "박스권 대응":
            return f"{confidence_label} 신뢰도의 방향 확인 구간입니다."
        return f"{confidence_label} 신뢰도의 중립 구간입니다."

    @staticmethod
    def _build_summary_body(
        trend: str,
        bias: str,
        timeframe: str,
        volume_signal: str,
        investor_summary: Optional[str],
        news_brief: Optional[str],
    ) -> str:
        segments = [f"{timeframe} 기준으로 현재 흐름은 {trend} 쪽입니다."]
        if bias:
            segments.append(f"기본 대응은 {bias} 관점으로 보시면 됩니다.")
        if volume_signal and volume_signal != "데이터 없음":
            segments.append(f"거래량은 {volume_signal} 흐름입니다.")
        if investor_summary:
            segments.append(investor_summary)
        if news_brief:
            segments.append(news_brief)
        return " ".join(segments)

    def _build_trend_outlook(
        self,
        trend: str,
        current: float,
        sma20: float,
        sma60: float,
        price_unit: str,
        asset_type: str,
        volume_signal: str,
        investor_summary: Optional[str],
    ) -> str:
        average_desc = (
            f"단기 평균은 {self._fmt(sma20, price_unit, asset_type)}, 중기 평균은 {self._fmt(sma60, price_unit, asset_type)} 수준입니다."
        )
        if trend == "상승":
            base = f"현재가는 주요 평균선 위에서 움직이고 있어 추세 훼손 전까지는 상승 흐름을 우선 봅니다. {average_desc}"
        elif trend == "하락":
            base = f"현재가는 주요 평균선 아래에 머물러 있어 반등이 나오더라도 보수적으로 보시는 편이 좋습니다. {average_desc}"
        else:
            base = f"현재가는 주요 평균선 근처에서 방향성이 엇갈리고 있어 추세 확인이 더 필요합니다. {average_desc}"

        if volume_signal and volume_signal != "데이터 없음":
            base += f" 거래량은 {volume_signal} 흐름입니다."
        if investor_summary:
            base += f" 수급 해석은 {investor_summary}"
        return base

    def _build_action_plan(
        self,
        trend: str,
        bias: str,
        first_buy: float,
        second_buy: float,
        first_sell: float,
        second_sell: float,
        price_unit: str,
        asset_type: str,
    ) -> str:
        if trend == "상승":
            return (
                f"추격 매수보다는 {self._fmt(first_buy, price_unit, asset_type)} 부근 조정 시 1차 대응을 보고, "
                f"흐름이 더 눌리면 {self._fmt(second_buy, price_unit, asset_type)} 부근까지 분할 접근하는 전략이 적절합니다. "
                f"반등 시에는 {self._fmt(first_sell, price_unit, asset_type)}와 {self._fmt(second_sell, price_unit, asset_type)}를 차례로 확인합니다."
            )
        if trend == "하락":
            return (
                f"성급한 진입보다는 추세 안정 여부를 먼저 확인하시고, 들어가더라도 {self._fmt(first_buy, price_unit, asset_type)}와 "
                f"{self._fmt(second_buy, price_unit, asset_type)}를 분할 기준으로만 짧게 대응하는 편이 안전합니다."
            )
        return (
            f"방향성이 아직 뚜렷하지 않아 {self._fmt(first_buy, price_unit, asset_type)}와 {self._fmt(first_sell, price_unit, asset_type)} "
            f"사이의 박스권 대응으로 접근하시고, 이탈 시에는 다음 구간 {self._fmt(second_buy, price_unit, asset_type)} 또는 "
            f"{self._fmt(second_sell, price_unit, asset_type)}를 새 기준으로 보시면 됩니다."
        )

    def _build_buy_plan(self, first_buy: float, second_buy: float, price_unit: str, asset_type: str, trend: str) -> str:
        prefix = "눌림목 관점" if trend == "상승" else "보수적 분할 관점"
        return (
            f"{prefix}에서 1차 매수는 {self._fmt(first_buy, price_unit, asset_type)}, "
            f"2차 매수는 {self._fmt(second_buy, price_unit, asset_type)}를 기준으로 보시면 됩니다."
        )

    def _build_sell_plan(self, first_sell: float, second_sell: float, price_unit: str, asset_type: str, trend: str) -> str:
        prefix = "상승 흐름 이익 실현" if trend == "상승" else "기술적 반등 정리"
        return (
            f"{prefix} 구간은 1차 {self._fmt(first_sell, price_unit, asset_type)}, "
            f"2차 {self._fmt(second_sell, price_unit, asset_type)}입니다."
        )

    def _build_loss_cut_plan(self, stop_loss: float, price_unit: str, asset_type: str) -> str:
        return f"손절 기준은 {self._fmt(stop_loss, price_unit, asset_type)} 이탈 여부입니다. 이 구간 아래에서는 대응 강도를 낮추는 편이 좋습니다."

    @staticmethod
    def _build_risk_notes(
        trend: str,
        rsi14: Optional[float],
        macd_hist: Optional[float],
        atr14: Optional[float],
        volume_ratio: Optional[float],
        investor_flow: Optional[Dict],
        news_context: Dict,
    ) -> List[str]:
        risks: List[str] = []

        if rsi14 is not None and rsi14 >= 70:
            risks.append("단기 과열 신호가 있어 추격 매수는 부담이 될 수 있습니다.")
        elif rsi14 is not None and rsi14 <= 30:
            risks.append("낙폭은 커졌지만 추세 반전 확인 전까지는 저가 매수도 신중해야 합니다.")

        if macd_hist is not None and macd_hist < 0:
            risks.append("모멘텀이 완전히 회복되지 않아 반등 후 다시 흔들릴 수 있습니다.")

        if atr14 is not None and atr14 > 0:
            risks.append("변동성이 살아 있어 가격이 빠르게 흔들릴 수 있습니다.")

        if volume_ratio is not None and volume_ratio <= 0.7:
            risks.append("거래 참여가 약해 반등 탄력이 제한될 수 있습니다.")

        if trend == "하락":
            risks.append("하락 추세 구간에서는 지지선 이탈 시 낙폭이 빠르게 커질 수 있습니다.")

        if investor_flow:
            if investor_flow.get("market_scope") == "domestic":
                foreign_direction = investor_flow.get("foreign_direction")
                institution_direction = investor_flow.get("institution_direction")
                if foreign_direction == institution_direction == "순매도":
                    risks.append("외국인과 기관이 함께 매도 우위라면 단기 반등의 지속성이 약할 수 있습니다.")
            elif investor_flow.get("market_scope") == "global" and investor_flow.get("flow_label") == "유출 우위":
                risks.append("해외 수급 추정상 자금 유출 우위라 단기 추세가 쉽게 꺾일 수 있습니다.")

        news_summary = news_context.get("summary")
        if news_context.get("news_bias") == "부담" and news_summary:
            risks.append(news_summary)
        elif news_context.get("news_bias") == "중립" and news_summary:
            risks.append("뉴스 흐름은 아직 방향을 강하게 밀어주지 않고 있습니다.")

        return list(dict.fromkeys(risks))[:4]

    def _build_reason_notes(
        self,
        trend: str,
        sma20: float,
        sma60: float,
        high20: float,
        low20: float,
        price_unit: str,
        asset_type: str,
        volume_signal: str,
        rsi14: Optional[float],
        macd_hist: Optional[float],
        investor_summary: Optional[str],
        news_brief: Optional[str],
        profile: Dict[str, float],
    ) -> List[str]:
        reasons = [
            f"{profile['primary_label']} 평균과 {profile['secondary_label']} 평균 위치로 추세 방향을 판단했습니다.",
            f"최근 핵심 가격대는 고점 {self._fmt(high20, price_unit, asset_type)}와 저점 {self._fmt(low20, price_unit, asset_type)}입니다.",
        ]

        if volume_signal and volume_signal != "데이터 없음":
            reasons.append(f"거래량은 현재 {volume_signal} 흐름으로 해석했습니다.")

        if rsi14 is not None:
            if rsi14 >= 70:
                reasons.append("보조지표상 단기 과열 구간에 가까워 추격 매수는 불리할 수 있습니다.")
            elif rsi14 <= 30:
                reasons.append("보조지표상 과매도 구간에 가까워 낙폭 둔화 가능성을 함께 봤습니다.")
            else:
                reasons.append("보조지표는 과열도 과매도도 아닌 중립권으로 봤습니다.")

        if macd_hist is not None:
            if macd_hist > 0:
                reasons.append("모멘텀은 완만하게 개선되는 쪽으로 반영했습니다.")
            elif macd_hist < 0:
                reasons.append("모멘텀은 아직 약한 편으로 반영했습니다.")

        if investor_summary:
            reasons.append(investor_summary)
        if news_brief:
            reasons.append(news_brief)
        if trend == "횡보":
            reasons.append("방향성이 약해 지지·저항 이탈 여부를 더 중요하게 봤습니다.")

        return reasons[:5]

    @staticmethod
    def _join_reason_summary(reasons: List[str], fallback: str) -> str:
        cleaned = [reason.strip() for reason in reasons if reason and reason.strip()]
        if not cleaned:
            return fallback
        return " ".join(cleaned[:3])

    def _score_trend(
        self,
        current: float,
        previous_close: float,
        sma20: float,
        sma60: float,
        prev_sma20: float,
        macd_metrics: Dict[str, Optional[float]],
    ) -> Tuple[int, List[str]]:
        score = 0
        reasons: List[str] = []

        if current >= sma20 >= sma60:
            score += 18
            reasons.append("단기선과 중기선이 정배열이라 추세가 상승 쪽으로 기울어 있습니다.")
        elif current >= sma20 and sma20 < sma60:
            score += 12
            reasons.append("현재가가 단기선 위로 올라와 반등 시도가 이어지고 있습니다.")
        elif current <= sma20 <= sma60:
            score += 3
            reasons.append("현재가가 단기선과 중기선 아래에 있어 추세는 아직 약세입니다.")
        else:
            score += 8
            reasons.append("이동평균선이 엇갈려 있어 추세는 아직 확인 구간입니다.")

        if previous_close <= prev_sma20 < current or (previous_close <= prev_sma20 and current > sma20):
            score += 5
            reasons.append("단기 이동평균선을 상향 돌파해 매수세가 다시 들어오고 있습니다.")
        elif previous_close >= prev_sma20 > current or (previous_close >= prev_sma20 and current < sma20):
            reasons.append("단기 이동평균선 아래로 밀려 추세 탄력이 약해졌습니다.")

        if macd_metrics.get("golden_cross"):
            score += 7
            reasons.append("MACD 골든크로스가 발생해 추세 전환 신호가 확인됩니다.")
        elif macd_metrics.get("macd_line") is not None and macd_metrics.get("signal_line") is not None:
            if macd_metrics["macd_line"] > macd_metrics["signal_line"] and (macd_metrics.get("histogram") or 0) >= 0:
                score += 5
                reasons.append("MACD가 시그널선 위에서 유지돼 추세 신호가 우호적입니다.")
            elif macd_metrics.get("dead_cross"):
                reasons.append("MACD 데드크로스가 발생해 추세 반전 신호가 약해졌습니다.")
            elif macd_metrics["macd_line"] < macd_metrics["signal_line"]:
                reasons.append("MACD가 시그널선 아래에 있어 약세 모멘텀이 남아 있습니다.")

        return min(30, score), reasons[:4]

    @staticmethod
    def _score_momentum(
        rsi14: Optional[float],
        stochastic: Dict[str, Optional[float]],
    ) -> Tuple[int, List[str], str]:
        score = 0
        reasons: List[str] = []

        if rsi14 is not None:
            if 45 <= rsi14 <= 65:
                score += 8
                reasons.append("RSI가 중립 상단에 있어 추세를 이어갈 체력이 남아 있습니다.")
            elif 30 <= rsi14 < 45:
                score += 6
                reasons.append("RSI가 과매도 구간에서 벗어나며 반등 여지가 생기고 있습니다.")
            elif 65 < rsi14 <= 75:
                score += 4
                reasons.append("RSI가 강세권에 있지만 과열 직전이라 추격 매수는 조심해야 합니다.")
            elif rsi14 < 30:
                score += 4
                reasons.append("RSI가 과매도권이라 기술적 반등 가능성은 있으나 변동성이 큽니다.")
            else:
                score += 2
                reasons.append("RSI가 과열권에 가까워 단기 진입 타이밍은 보수적으로 보는 편이 좋습니다.")

        k_value = stochastic.get("k")
        d_value = stochastic.get("d")
        if stochastic.get("golden_cross") and k_value is not None and k_value <= 45:
            score += 8
            reasons.append("스토캐스틱 골든크로스가 저점권에서 나와 단기 반등 타이밍 신호가 살아 있습니다.")
        elif k_value is not None and d_value is not None and k_value > d_value and k_value < 80:
            score += 6
            reasons.append("스토캐스틱이 시그널 위에서 움직여 단기 모멘텀이 우호적입니다.")
        elif stochastic.get("dead_cross") and k_value is not None and k_value >= 55:
            score += 1
            reasons.append("스토캐스틱 데드크로스가 나와 단기 탄력이 둔화되고 있습니다.")
        elif k_value is not None and k_value >= 85:
            score += 1
            reasons.append("스토캐스틱이 과열권이라 지금은 타이밍을 좇기보다 눌림을 기다리는 편이 좋습니다.")

        if rsi14 is not None and rsi14 >= 75:
            timing_summary = "RSI와 스토캐스틱 모두 과열권에 가까워 추격 매수보다 눌림 확인이 유리합니다."
        elif rsi14 is not None and rsi14 <= 35:
            timing_summary = "RSI가 눌린 구간에 있고 스토캐스틱 반등 여부를 함께 보면 단기 진입 타이밍을 판단하기 좋습니다."
        else:
            timing_summary = "RSI와 스토캐스틱 기준으로 타이밍은 중립 이상이며, 과열 여부만 조심하면 됩니다."

        return min(20, score), reasons[:4], timing_summary

    @staticmethod
    def _score_volume(
        volume_ratio: Optional[float],
        previous_close: float,
        current: float,
    ) -> Tuple[int, List[str], str]:
        score = 0
        reasons: List[str] = []
        price_up = current >= previous_close

        if volume_ratio is None:
            return 5, ["거래량 데이터가 제한적이라 신뢰도는 보수적으로 반영했습니다."], "거래량 기준 신뢰도는 제한적으로 해석했습니다."

        if volume_ratio >= 1.8 and price_up:
            score += 15
            reasons.append("거래량이 크게 늘어난 상태에서 양봉이 나와 상승 신호 신뢰도가 강해졌습니다.")
        elif volume_ratio >= 1.2 and price_up:
            score += 12
            reasons.append("거래량이 평균보다 늘어난 상태라 상승 시도의 신뢰도가 높아졌습니다.")
        elif 0.9 <= volume_ratio < 1.2:
            score += 9
            reasons.append("거래량이 평균 수준이라 추세 판단의 기본 신뢰도는 유지됩니다.")
        elif volume_ratio >= 1.2 and not price_up:
            score += 5
            reasons.append("거래량은 늘었지만 하락 쪽 거래가 붙어 매수 신호 신뢰도는 낮아졌습니다.")
        else:
            score += 3
            reasons.append("거래량이 줄어 신호의 지속성은 약하게 보는 편이 좋습니다.")

        summary = (
            f"거래량 비율은 {volume_ratio:.2f}배이며, "
            f"{'상승 신호 신뢰도를 높여 주는 구간입니다.' if score >= 10 else '신호를 강하게 밀어주기에는 다소 약한 구간입니다.'}"
        )
        return min(15, score), reasons[:3], summary

    def _score_volatility(
        self,
        current: float,
        atr14: Optional[float],
        bollinger: Dict[str, Optional[float]],
    ) -> Tuple[int, List[str], str]:
        score = 0
        reasons: List[str] = []

        bandwidth = bollinger.get("bandwidth")
        position = bollinger.get("position")
        middle = bollinger.get("middle")
        if bandwidth is not None and position is not None:
            if 0.15 <= position <= 0.75 and bandwidth <= 0.18:
                score += 8
                reasons.append("볼린저밴드 안쪽에서 움직이며 밴드 폭이 과하지 않아 변동성 부담이 크지 않습니다.")
            elif position >= 0.85:
                score += 4
                reasons.append("볼린저밴드 상단 근처라 추세는 강하지만 단기 흔들림 가능성도 커졌습니다.")
            elif position <= 0.15:
                score += 4
                reasons.append("볼린저밴드 하단 부근이라 반등 여지는 있지만 변동성이 아직 큰 구간입니다.")
            else:
                score += 6
                reasons.append("볼린저밴드 기준으로는 중립적인 변동성 구간입니다.")
        else:
            score += 5
            reasons.append("볼린저밴드 데이터가 충분하지 않아 변동성 점수는 보수적으로 반영했습니다.")

        atr_ratio = (atr14 / current) if atr14 and current else None
        if atr_ratio is not None:
            if atr_ratio <= 0.025:
                score += 7
                reasons.append("ATR이 낮아 손절 기준을 잡기 상대적으로 쉬운 구간입니다.")
            elif atr_ratio <= 0.05:
                score += 5
                reasons.append("ATR은 무난한 수준이라 감당 가능한 변동성으로 볼 수 있습니다.")
            elif atr_ratio <= 0.08:
                score += 3
                reasons.append("ATR이 다소 높아 진입 후 흔들림을 감안해야 합니다.")
            else:
                score += 1
                reasons.append("ATR이 높아 단기 변동폭이 크므로 진입 강도를 줄이는 편이 좋습니다.")

        summary = self._join_reason_summary(reasons, "변동성은 중립 수준으로 봤습니다.")
        return min(15, score), reasons[:4], summary

    def _score_risk(
        self,
        current: float,
        sma20: float,
        sma60: float,
        rsi14: Optional[float],
        stochastic: Dict[str, Optional[float]],
        investor_flow: Optional[Dict],
        news_context: Dict,
        resistances: List[float],
        bollinger: Dict[str, Optional[float]],
        macd_metrics: Dict[str, Optional[float]],
    ) -> Tuple[int, List[str]]:
        penalty = 0
        reasons: List[str] = []

        if current < sma20 < sma60:
            penalty += 5
            reasons.append("현재가가 단기선과 중기선 아래에 있어 추세 역행 진입 위험이 있습니다.")

        if resistances:
            gap = abs(resistances[0] - current) / current if current else 0
            if gap <= 0.015:
                penalty += 4
                reasons.append("가까운 저항선이 바로 위에 있어 상승 여력이 제한될 수 있습니다.")

        if rsi14 is not None and rsi14 >= 75:
            penalty += 4
            reasons.append("RSI가 과열권이라 단기 차익 매물이 나올 가능성이 큽니다.")

        k_value = stochastic.get("k")
        if stochastic.get("dead_cross") and k_value is not None and k_value >= 75:
            penalty += 3
            reasons.append("스토캐스틱 데드크로스가 과열권에서 나와 단기 타이밍이 불리합니다.")

        if investor_flow:
            if investor_flow.get("market_scope") == "domestic" and investor_flow.get("foreign_direction") == investor_flow.get("institution_direction") == "순매도":
                penalty += 4
                reasons.append("외국인과 기관이 함께 매도 우위라 수급이 받쳐주지 않고 있습니다.")
            elif investor_flow.get("market_scope") == "global" and investor_flow.get("flow_label") == "유출 우위":
                penalty += 3
                reasons.append("해외 수급 추정상 유출 우위라 단기 추세가 쉽게 꺾일 수 있습니다.")

        if news_context.get("news_bias") == "부담":
            penalty += 4
            reasons.append(news_context.get("summary") or "뉴스·국제정세 부담이 단기 변동성을 키우고 있습니다.")

        if bollinger.get("position") is not None and bollinger["position"] >= 0.95:
            penalty += 2
            reasons.append("볼린저밴드 상단 과열 구간에 가까워 단기 되돌림이 나올 수 있습니다.")

        if macd_metrics.get("dead_cross"):
            penalty += 3
            reasons.append("MACD 데드크로스가 확인돼 추세 탄력이 약해지고 있습니다.")

        return min(20, penalty), reasons[:5]

    def _build_decision_reasons(
        self,
        final_action: str,
        trend_reasons: List[str],
        momentum_reasons: List[str],
        volume_reasons: List[str],
        risk_reasons: List[str],
    ) -> List[str]:
        if final_action == "매수":
            return (trend_reasons[:2] + momentum_reasons[:1] + volume_reasons[:1])[:4]
        if final_action == "매도":
            return (risk_reasons[:3] + trend_reasons[:1])[:4]
        return (trend_reasons[:1] + momentum_reasons[:1] + risk_reasons[:2])[:4]

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

    def _calculate_macd_metrics(self, closes: List[float]) -> Dict[str, Optional[float]]:
        if len(closes) < 35:
            return {
                "macd_line": None,
                "signal_line": None,
                "histogram": None,
                "golden_cross": False,
                "dead_cross": False,
            }
        ema12 = self._ema(closes, 12)
        ema26 = self._ema(closes, 26)
        macd_series = [a - b for a, b in zip(ema12[-len(ema26):], ema26)]
        signal_series = self._ema(macd_series, 9)
        macd_line = macd_series[-1]
        signal_line = signal_series[-1]
        histogram = macd_line - signal_line
        prev_macd = macd_series[-2] if len(macd_series) > 1 else None
        prev_signal = signal_series[-2] if len(signal_series) > 1 else None
        golden_cross = prev_macd is not None and prev_signal is not None and prev_macd <= prev_signal and macd_line > signal_line
        dead_cross = prev_macd is not None and prev_signal is not None and prev_macd >= prev_signal and macd_line < signal_line
        return {
            "macd_line": macd_line,
            "signal_line": signal_line,
            "histogram": histogram,
            "golden_cross": golden_cross,
            "dead_cross": dead_cross,
        }

    @staticmethod
    def _calculate_stochastic(history: List[Dict[str, float]], period: int = 14, smooth: int = 3) -> Dict[str, Optional[float]]:
        if len(history) < period + smooth:
            return {"k": None, "d": None, "golden_cross": False, "dead_cross": False}

        fast_k_values: List[float] = []
        for idx in range(period - 1, len(history)):
            window = history[idx - period + 1: idx + 1]
            highest = max(candle["high"] for candle in window)
            lowest = min(candle["low"] for candle in window)
            close = history[idx]["close"]
            if highest == lowest:
                fast_k_values.append(50.0)
            else:
                fast_k_values.append(((close - lowest) / (highest - lowest)) * 100)

        if len(fast_k_values) < smooth + 1:
            return {"k": None, "d": None, "golden_cross": False, "dead_cross": False}

        slow_k_series = [mean(fast_k_values[max(0, idx - smooth + 1): idx + 1]) for idx in range(len(fast_k_values))]
        slow_d_series = [mean(slow_k_series[max(0, idx - smooth + 1): idx + 1]) for idx in range(len(slow_k_series))]
        k_value = slow_k_series[-1]
        d_value = slow_d_series[-1]
        prev_k = slow_k_series[-2]
        prev_d = slow_d_series[-2]
        return {
            "k": k_value,
            "d": d_value,
            "golden_cross": prev_k <= prev_d and k_value > d_value,
            "dead_cross": prev_k >= prev_d and k_value < d_value,
        }

    @staticmethod
    def _calculate_bollinger(closes: List[float], period: int = 20, multiplier: float = 2.0) -> Dict[str, Optional[float]]:
        if len(closes) < period:
            return {"middle": None, "upper": None, "lower": None, "bandwidth": None, "position": None}
        window = closes[-period:]
        middle = mean(window)
        deviation = pstdev(window) if len(window) > 1 else 0.0
        upper = middle + multiplier * deviation
        lower = middle - multiplier * deviation
        bandwidth = ((upper - lower) / middle) if middle else None
        latest = closes[-1]
        if upper == lower:
            position = 0.5
        else:
            position = (latest - lower) / (upper - lower)
        return {
            "middle": middle,
            "upper": upper,
            "lower": lower,
            "bandwidth": bandwidth,
            "position": position,
        }

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
            "rate": ("금리 경계", -1),
            "inflation": ("물가 부담", -1),
            "tariff": ("관세 이슈", -1),
            "war": ("지정학 불안", -2),
            "attack": ("지정학 불안", -2),
            "missile": ("지정학 불안", -2),
            "drone": ("지정학 불안", -2),
            "conflict": ("지정학 불안", -2),
            "ceasefire": ("중동 긴장", -1),
            "ukraine": ("우크라이나 전쟁", -2),
            "russia": ("우크라이나 전쟁", -2),
            "gaza": ("중동 전쟁", -2),
            "israel": ("중동 전쟁", -2),
            "iran": ("미국-이란 긴장", -2),
            "red sea": ("중동 긴장", -2),
            "sanction": ("제재 리스크", -1),
            "oil": ("유가 변동성", -1 if asset_type == "stock" else 0),
            "fed": ("미국 통화정책 경계", -1),
            "treasury": ("국채금리 변동성", -1),
            "stimulus": ("경기부양 기대", 1),
            "ai": ("인공지능 수요 기대", 1),
            "chip": ("반도체 수요 기대", 1),
            "soft landing": ("연착륙 기대", 1),
            "cut": ("정책 완화 기대", 1),
        }

        signals: List[Dict[str, int]] = []
        for article in articles:
            combined = f"{article['title']} {article['summary']}".lower()
            score = 0
            matched = []
            for keyword, (label, keyword_score) in keyword_scores.items():
                if keyword in combined:
                    score += keyword_score
                    matched.append(label)
            if score == 0:
                continue
            signals.append({"label": ", ".join(list(dict.fromkeys(matched))[:2]), "score": score})
        return signals

    @staticmethod
    def _score_articles(articles: List[Dict[str, str]], asset_type: str) -> int:
        positive_words = ["beat", "surge", "growth", "partnership", "record", "gain", "rally", "strong"]
        negative_words = [
            "fall",
            "drop",
            "delay",
            "risk",
            "probe",
            "cut",
            "warn",
            "miss",
            "tariff",
            "war",
            "attack",
            "missile",
            "drone",
            "conflict",
            "ukraine",
            "russia",
            "gaza",
            "israel",
            "iran",
            "sanction",
        ]
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
            lead = "관련 뉴스 흐름"
        elif asset_type == "currency":
            lead = "환율 거시 환경"
        else:
            lead = "시장 뉴스 흐름"

        if macro_signals:
            macro_labels = ", ".join(signal["label"] for signal in macro_signals[:2] if signal.get("label"))
            if macro_labels:
                if bias == "우호적":
                    return f"{lead}은 대체로 우호적이며, {macro_labels} 요인이 심리를 지지하고 있습니다."
                if bias == "부담":
                    return f"{lead}은 대체로 부담이며, {macro_labels} 요인이 단기 변동성을 키울 수 있습니다."
                return f"{lead}은 뚜렷한 방향성은 없지만, {macro_labels} 이슈는 함께 확인할 필요가 있습니다."

        if bias == "우호적":
            return f"{lead}은 전반적으로 우호적입니다."
        if bias == "부담":
            return f"{lead}은 전반적으로 부담 요인에 가깝습니다."
        return f"{lead}은 아직 중립적인 수준입니다."
