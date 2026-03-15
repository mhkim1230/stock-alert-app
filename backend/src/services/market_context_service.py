import asyncio
import logging
from statistics import mean
from typing import Dict, List, Optional, Tuple

import aiohttp

from src.config.settings import settings
from src.services.news_service import NewsService


class MarketContextService:
    MARKET_SYMBOLS = {
        "sp500": {"label": "S&P500", "candidates": ["^GSPC"]},
        "nasdaq": {"label": "나스닥", "candidates": ["^IXIC"]},
        "dow": {"label": "다우", "candidates": ["^DJI"]},
        "vix": {"label": "VIX", "candidates": ["^VIX"]},
        "tnx": {"label": "미국 10년물", "candidates": ["^TNX"]},
        "dxy": {"label": "달러지수", "candidates": ["DX-Y.NYB", "DX=F"]},
        "oil": {"label": "WTI", "candidates": ["CL=F"]},
        "gold": {"label": "금", "candidates": ["GC=F"]},
    }

    TOPIC_GROUPS = {
        "금리": {"keywords": ["rate", "fed", "treasury", "yield", "bond"], "weight": -1},
        "물가": {"keywords": ["inflation", "cpi", "ppi", "price pressure"], "weight": -1},
        "관세": {"keywords": ["tariff", "duty", "trade tension"], "weight": -1},
        "지정학": {"keywords": ["war", "attack", "missile", "drone", "conflict", "ceasefire", "sanction"], "weight": -2},
        "원자재": {"keywords": ["oil", "crude", "gold", "energy"], "weight": -1},
        "정책완화": {"keywords": ["cut", "stimulus", "easing"], "weight": 1},
        "성장산업": {"keywords": ["ai", "chip", "semiconductor", "cloud"], "weight": 1},
    }

    POSITIVE_WORDS = ["beat", "surge", "growth", "partnership", "record", "gain", "rally", "strong", "upgrade"]
    NEGATIVE_WORDS = ["fall", "drop", "delay", "risk", "probe", "cut", "warn", "miss", "downgrade", "weak"]

    def __init__(self, news_service: Optional[NewsService] = None) -> None:
        self.logger = logging.getLogger(__name__)
        self.news_service = news_service or NewsService()

    async def build_context(self, asset_type: str, symbol: str, name: str) -> Dict:
        related_articles, macro_articles, indicators = await self._collect_inputs(symbol, name)
        news_eval = self._evaluate_news(asset_type, related_articles, macro_articles)
        market_eval = self._evaluate_indicators(asset_type, symbol, indicators)

        market_context_score = max(-10, min(10, news_eval["delta"] + market_eval["delta"]))
        if market_context_score >= 3:
            market_bias = "우호적"
        elif market_context_score <= -3:
            market_bias = "부담"
        else:
            market_bias = "중립"

        return {
            "market_context_score": market_context_score,
            "market_context_summary": self._compose_summary(market_eval, news_eval, market_bias),
            "market_bias": market_bias,
            "news_bias": news_eval["bias"],
            "summary": self._compose_summary(market_eval, news_eval, market_bias),
            "macro_reasons": market_eval["reasons"],
            "news_reasons": news_eval["reasons"],
            "themes": news_eval["themes"],
            "indicator_snapshot": indicators,
            "related_articles": related_articles,
            "macro_articles": macro_articles,
        }

    async def _collect_inputs(self, symbol: str, name: str) -> Tuple[List[Dict[str, str]], List[Dict[str, str]], Dict[str, Dict]]:
        queries = [symbol]
        if name and name.lower() != symbol.lower():
            queries.append(name)

        related_results = await asyncio.gather(
            *(self.news_service.get_latest_news(query=query, limit=4) for query in queries[:2]),
            return_exceptions=True,
        )
        related_articles: List[Dict[str, str]] = []
        seen_titles = set()
        for articles in related_results:
            if isinstance(articles, Exception):
                continue
            for article in articles:
                title = article.get("title", "")
                if title in seen_titles:
                    continue
                seen_titles.add(title)
                related_articles.append(article)

        macro_articles, indicators = await asyncio.gather(
            self.news_service.get_latest_news(limit=10),
            self._fetch_market_indicators(),
        )
        return related_articles[:4], macro_articles[:10], indicators

    async def _fetch_market_indicators(self) -> Dict[str, Dict]:
        tasks = {
            key: asyncio.create_task(self._fetch_indicator_with_fallback(config["candidates"], config["label"]))
            for key, config in self.MARKET_SYMBOLS.items()
        }
        results: Dict[str, Dict] = {}
        for key, task in tasks.items():
            payload = await task
            if payload:
                results[key] = payload
        return results

    async def _fetch_indicator_with_fallback(self, candidates: List[str], label: str) -> Optional[Dict]:
        for candidate in candidates:
            payload = await self._fetch_indicator_snapshot(candidate, label)
            if payload:
                return payload
        return None

    async def _fetch_indicator_snapshot(self, symbol: str, label: str) -> Optional[Dict]:
        url = (
            "https://query1.finance.yahoo.com/v8/finance/chart/"
            f"{symbol}?range=2d&interval=60m&includePrePost=false"
        )
        timeout = aiohttp.ClientTimeout(total=settings.request_timeout)
        try:
            async with aiohttp.ClientSession(timeout=timeout) as session:
                async with session.get(url, headers={"User-Agent": "Mozilla/5.0"}) as response:
                    if response.status != 200:
                        return None
                    payload = await response.json()
        except Exception as exc:
            self.logger.warning("Market context fetch failed for %s: %s", symbol, exc)
            return None

        result = (((payload or {}).get("chart") or {}).get("result") or [None])[0]
        if not result:
            return None
        quote = (((result.get("indicators") or {}).get("quote") or [None])[0]) or {}
        closes = [float(value) for value in (quote.get("close") or []) if value is not None]
        if len(closes) < 2:
            return None
        latest = closes[-1]
        previous = closes[-2]
        if previous == 0:
            return None
        change_percent = ((latest - previous) / previous) * 100
        trend_5d = ((latest - closes[0]) / closes[0]) * 100 if closes[0] else 0.0
        return {
            "symbol": symbol,
            "label": label,
            "price": round(latest, 4),
            "change_percent": round(change_percent, 2),
            "trend_5d": round(trend_5d, 2),
        }

    def _evaluate_news(self, asset_type: str, related_articles: List[Dict[str, str]], macro_articles: List[Dict[str, str]]) -> Dict:
        related_positive = 0
        related_negative = 0
        for article in related_articles:
            sentiment = self._classify_article_sentiment(article)
            if sentiment > 0:
                related_positive += 1
            elif sentiment < 0:
                related_negative += 1

        topic_counts: Dict[str, int] = {}
        topic_score = 0
        for article in macro_articles:
            for topic, config in self.TOPIC_GROUPS.items():
                combined = f"{article.get('title', '')} {article.get('summary', '')}".lower()
                if any(keyword in combined for keyword in config["keywords"]):
                    topic_counts[topic] = topic_counts.get(topic, 0) + 1
                    topic_score += config["weight"]

        delta = 0
        reasons: List[str] = []

        if related_articles:
            if related_positive > related_negative:
                delta += 2
                reasons.append(
                    f"종목 관련 기사 {len(related_articles)}건 중 긍정 흐름이 {related_positive}건으로 더 많아 개별 뉴스 톤은 우호적입니다."
                )
            elif related_negative > related_positive:
                delta -= 2
                reasons.append(
                    f"종목 관련 기사 {len(related_articles)}건 중 부정 흐름이 {related_negative}건으로 더 많아 개별 뉴스 톤은 보수적입니다."
                )
            else:
                reasons.append(
                    f"종목 관련 기사 {len(related_articles)}건의 방향이 엇갈려 개별 뉴스 톤은 중립에 가깝습니다."
                )

        sorted_topics = sorted(topic_counts.items(), key=lambda item: item[1], reverse=True)
        if sorted_topics:
            top_topics = ", ".join(f"{label} {count}건" for label, count in sorted_topics[:2])
            if topic_score <= -3:
                delta -= 3
                reasons.append(f"거시 기사에서는 {top_topics}이 반복돼 시장 심리가 다소 방어적으로 기울어 있습니다.")
            elif topic_score >= 2:
                delta += 2
                reasons.append(f"거시 기사에서는 {top_topics} 흐름이 확인돼 위험자산 심리에 우호적입니다.")
            else:
                reasons.append(f"거시 기사에서는 {top_topics} 이슈가 혼재해 방향성은 중립입니다.")

        if delta >= 2:
            bias = "우호적"
        elif delta <= -2:
            bias = "부담"
        else:
            bias = "중립"

        return {
            "delta": max(-5, min(5, delta)),
            "bias": bias,
            "reasons": reasons[:3],
            "themes": [label for label, _ in sorted_topics[:3]],
        }

    def _evaluate_indicators(self, asset_type: str, symbol: str, indicators: Dict[str, Dict]) -> Dict:
        delta = 0
        reasons: List[str] = []

        sp500 = indicators.get("sp500")
        nasdaq = indicators.get("nasdaq")
        vix = indicators.get("vix")
        tnx = indicators.get("tnx")
        dxy = indicators.get("dxy")
        oil = indicators.get("oil")
        gold = indicators.get("gold")

        if sp500 and nasdaq:
            if sp500["change_percent"] > 0 and nasdaq["change_percent"] > 0:
                delta += 2
                reasons.append(
                    f"미국 주요 지수는 S&P500 {sp500['change_percent']:+.2f}%, 나스닥 {nasdaq['change_percent']:+.2f}%로 위험선호 흐름입니다."
                )
            elif sp500["change_percent"] < 0 and nasdaq["change_percent"] < 0:
                delta -= 2
                reasons.append(
                    f"미국 주요 지수는 S&P500 {sp500['change_percent']:+.2f}%, 나스닥 {nasdaq['change_percent']:+.2f}%로 전반적으로 약세입니다."
                )

        if vix:
            if vix["change_percent"] >= 5:
                delta -= 2
                reasons.append(f"VIX가 {vix['change_percent']:+.2f}% 움직여 변동성 경계 심리가 강해졌습니다.")
            elif vix["change_percent"] <= -5:
                delta += 1
                reasons.append(f"VIX가 {vix['change_percent']:+.2f}% 내려 위험회피 심리가 완화되고 있습니다.")

        if asset_type == "stock":
            if tnx:
                if tnx["change_percent"] >= 1:
                    delta -= 1
                    reasons.append(f"미국 10년물 금리가 {tnx['change_percent']:+.2f}% 올라 밸류에이션 부담이 커졌습니다.")
                elif tnx["change_percent"] <= -1:
                    delta += 1
                    reasons.append(f"미국 10년물 금리가 {tnx['change_percent']:+.2f}% 내려 성장주 부담이 완화되고 있습니다.")

            if dxy:
                if dxy["change_percent"] >= 0.5:
                    delta -= 1
                    reasons.append(f"달러지수가 {dxy['change_percent']:+.2f}% 올라 글로벌 유동성 환경은 다소 보수적입니다.")
                elif dxy["change_percent"] <= -0.5:
                    delta += 1
                    reasons.append(f"달러지수가 {dxy['change_percent']:+.2f}% 내려 위험자산 선호에는 우호적입니다.")

            if oil:
                if oil["change_percent"] >= 2:
                    delta -= 1
                    reasons.append(f"유가가 {oil['change_percent']:+.2f}% 올라 비용 부담과 물가 우려가 커질 수 있습니다.")
                elif oil["change_percent"] <= -2:
                    delta += 1
                    reasons.append(f"유가가 {oil['change_percent']:+.2f}% 내려 비용 부담은 다소 완화되고 있습니다.")
        else:
            base, _, target = symbol.partition("/")
            if dxy and ("USD" in {base, target}):
                if base == "USD":
                    delta += 2 if dxy["change_percent"] > 0 else -2 if dxy["change_percent"] < 0 else 0
                    reasons.append(
                        f"달러지수 {dxy['change_percent']:+.2f}% 변화는 {base}/{target} 방향성에 직접 영향을 주고 있습니다."
                    )
                elif target == "USD":
                    delta += -2 if dxy["change_percent"] > 0 else 2 if dxy["change_percent"] < 0 else 0
                    reasons.append(
                        f"달러지수 {dxy['change_percent']:+.2f}% 변화는 {base}/{target} 환율에는 역방향 압력으로 작용합니다."
                    )

            if tnx and ("USD" in {base, target}) and abs(tnx["change_percent"]) >= 1:
                signed = 1 if (base == "USD" and tnx["change_percent"] > 0) or (target == "USD" and tnx["change_percent"] < 0) else -1
                delta += signed
                reasons.append(f"미국 10년물 금리 {tnx['change_percent']:+.2f}% 변화가 달러 강도에 영향을 주고 있습니다.")

            if oil and ("KRW" in {base, target}) and abs(oil["change_percent"]) >= 2:
                signed = 1 if (base == "USD" and target == "KRW" and oil["change_percent"] > 0) else -1 if (base == "USD" and target == "KRW") else 0
                if signed != 0:
                    delta += signed
                    reasons.append(f"유가 {oil['change_percent']:+.2f}% 변화는 원화 민감 구간에 부담을 줄 수 있습니다.")

        if gold and gold["change_percent"] >= 1.5 and vix and vix["change_percent"] > 0:
            delta -= 1
            reasons.append("금과 변동성이 함께 오르고 있어 안전자산 선호가 확인됩니다.")

        return {
            "delta": max(-5, min(5, delta)),
            "reasons": reasons[:4],
            "snapshot": indicators,
        }

    def _compose_summary(self, market_eval: Dict, news_eval: Dict, market_bias: str) -> str:
        market_part = self._compose_market_snapshot(market_eval.get("snapshot") or {})
        news_part = " ".join(news_eval.get("reasons")[:2])
        if market_part and news_part:
            return f"{market_part} {news_part} 현재 시장환경은 {market_bias} 쪽입니다."
        if market_part:
            return f"{market_part} 현재 시장환경은 {market_bias} 쪽입니다."
        if news_part:
            return f"{news_part} 현재 시장환경은 {market_bias} 쪽입니다."
        return f"현재 수집된 시장환경 근거가 제한적이어서 {market_bias} 수준으로만 해석했습니다."

    @staticmethod
    def _compose_market_snapshot(indicators: Dict[str, Dict]) -> str:
        ordered = []
        for key in ("sp500", "nasdaq", "vix", "tnx", "dxy", "oil"):
            payload = indicators.get(key)
            if not payload:
                continue
            ordered.append(f"{payload['label']} {payload['change_percent']:+.2f}%")
        if not ordered:
            return ""
        return f"실시간 시장 지표는 {', '.join(ordered[:5])} 흐름입니다."

    def _classify_article_sentiment(self, article: Dict[str, str]) -> int:
        combined = f"{article.get('title', '')} {article.get('summary', '')}".lower()
        positive = sum(1 for word in self.POSITIVE_WORDS if word in combined)
        negative = sum(1 for word in self.NEGATIVE_WORDS if word in combined)
        if positive > negative:
            return 1
        if negative > positive:
            return -1
        return 0
