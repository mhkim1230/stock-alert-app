import os
import pytest

os.environ.setdefault("DATABASE_URL", "postgresql://placeholder:placeholder@placeholder.invalid:5432/postgres")
os.environ.setdefault("ADMIN_API_KEY", "placeholder-admin-key")

from src.services.analysis_service import AnalysisService
from src.services.global_quote_service import GlobalQuoteService


@pytest.mark.asyncio
async def test_get_quote_uses_latest_trade_price_and_previous_close(monkeypatch):
    async def fake_fetch_json(self, url: str):
        assert "finance/chart/NVDA" in url
        return {
            "chart": {
                "result": [
                    {
                        "meta": {
                            "regularMarketPrice": 183.22,
                            "previousClose": 180.25,
                            "currency": "USD",
                            "shortName": "NVIDIA Corporation",
                            "exchangeName": "NMS",
                        },
                        "indicators": {
                            "quote": [
                                {
                                    "close": [181.1, None, 183.22, 184.55],
                                }
                            ]
                        },
                    }
                ]
            }
        }

    monkeypatch.setattr(GlobalQuoteService, "_fetch_json", fake_fetch_json)

    service = GlobalQuoteService()
    quote = await service.get_quote("NVDA")

    assert quote is not None
    assert quote["price"] == 184.55
    assert quote["change"] == 4.3
    assert quote["change_percent"] == 2.38
    assert quote["market"] == "NASDAQ"
    assert quote["source"] == "global:yahoo_extended_quote:NVDA"


@pytest.mark.asyncio
async def test_get_fundamentals_parses_timeseries_payload(monkeypatch):
    async def fake_fetch_json(self, url: str):
        assert "fundamentals-timeseries" in url
        return {
            "timeseries": {
                "result": [
                    {
                        "meta": {"type": ["annualTotalRevenue"]},
                        "annualTotalRevenue": [
                            {"reportedValue": {"raw": 100.0}},
                            {"reportedValue": {"raw": 140.0}},
                        ],
                    },
                    {
                        "meta": {"type": ["annualDilutedEPS"]},
                        "annualDilutedEPS": [
                            {"reportedValue": {"raw": 2.0}},
                            {"reportedValue": {"raw": 3.0}},
                        ],
                    },
                    {
                        "meta": {"type": ["annualOperatingIncome"]},
                        "annualOperatingIncome": [
                            {"reportedValue": {"raw": 20.0}},
                            {"reportedValue": {"raw": 42.0}},
                        ],
                    },
                    {
                        "meta": {"type": ["annualNetIncome"]},
                        "annualNetIncome": [
                            {"reportedValue": {"raw": 16.0}},
                            {"reportedValue": {"raw": 33.0}},
                        ],
                    },
                    {
                        "meta": {"type": ["annualCurrentAssets"]},
                        "annualCurrentAssets": [
                            {"reportedValue": {"raw": 50.0}},
                            {"reportedValue": {"raw": 65.0}},
                        ],
                    },
                    {
                        "meta": {"type": ["annualCurrentLiabilities"]},
                        "annualCurrentLiabilities": [
                            {"reportedValue": {"raw": 35.0}},
                            {"reportedValue": {"raw": 40.0}},
                        ],
                    },
                    {
                        "meta": {"type": ["annualTotalAssets"]},
                        "annualTotalAssets": [
                            {"reportedValue": {"raw": 120.0}},
                            {"reportedValue": {"raw": 150.0}},
                        ],
                    },
                    {
                        "meta": {"type": ["annualTotalLiabilitiesNetMinorityInterest"]},
                        "annualTotalLiabilitiesNetMinorityInterest": [
                            {"reportedValue": {"raw": 70.0}},
                            {"reportedValue": {"raw": 72.0}},
                        ],
                    },
                    {
                        "meta": {"type": ["annualStockholdersEquity"]},
                        "annualStockholdersEquity": [
                            {"reportedValue": {"raw": 50.0}},
                            {"reportedValue": {"raw": 78.0}},
                        ],
                    },
                    {
                        "meta": {"type": ["annualFreeCashFlow"]},
                        "annualFreeCashFlow": [
                            {"reportedValue": {"raw": 11.0}},
                            {"reportedValue": {"raw": 18.0}},
                        ],
                    },
                ]
            }
        }

    monkeypatch.setattr(GlobalQuoteService, "_fetch_json", fake_fetch_json)

    service = GlobalQuoteService()
    fundamentals = await service.get_fundamentals("NVDA")

    assert fundamentals is not None
    assert fundamentals["revenue_growth"] == 0.4
    assert fundamentals["earnings_growth"] == 0.5
    assert round(fundamentals["operating_margins"], 2) == 0.30
    assert round(fundamentals["profit_margins"], 4) == round(33.0 / 140.0, 4)
    assert round(fundamentals["current_ratio"], 3) == 1.625
    assert round(fundamentals["debt_to_equity"], 3) == round((72.0 / 78.0) * 100, 3)
    assert round(fundamentals["return_on_equity"], 4) == round(33.0 / 78.0, 4)


def test_global_fundamental_scores_produce_reasons():
    service = AnalysisService()
    fundamentals = {
        "revenue_growth": 0.18,
        "earnings_growth": 0.24,
        "operating_margins": 0.32,
        "profit_margins": 0.28,
        "forward_pe": 28.4,
        "peg_ratio": 1.35,
        "price_to_sales": 11.2,
        "debt_to_equity": 52.0,
        "current_ratio": 1.42,
        "return_on_equity": 0.41,
        "beta": 1.76,
    }

    fundamental_score, fundamental_reasons, fundamental_summary = service._score_fundamentals(fundamentals)
    valuation_score, valuation_reasons, valuation_summary = service._score_valuation(fundamentals)
    quality_score, quality_reasons, quality_summary = service._score_quality(fundamentals)

    assert fundamental_score > 0
    assert valuation_score > 0
    assert quality_score > 0
    assert fundamental_reasons
    assert valuation_reasons
    assert quality_reasons
    assert fundamental_summary
    assert valuation_summary
    assert quality_summary
