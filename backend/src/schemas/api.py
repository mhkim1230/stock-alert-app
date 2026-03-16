from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class HealthResponse(BaseModel):
    status: str
    app: str
    environment: str


class SessionLoginRequest(BaseModel):
    password: str = Field(..., min_length=1)


class SessionStatusResponse(BaseModel):
    authenticated: bool
    mode: str


class DeviceTokenCreate(BaseModel):
    token: str
    platform: str = "iOS"


class DeviceTokenResponse(BaseModel):
    id: str
    token: str
    platform: str
    is_active: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        orm_mode = True


class WatchlistItemCreate(BaseModel):
    symbol: str = Field(..., min_length=1, max_length=20)


class WatchlistItemResponse(BaseModel):
    id: str
    symbol: str
    created_at: datetime
    updated_at: datetime

    class Config:
        orm_mode = True


class FxWatchlistItemCreate(BaseModel):
    base_currency: str = Field(..., min_length=3, max_length=3)
    target_currency: str = Field(..., min_length=3, max_length=3)


class FxWatchlistItemResponse(BaseModel):
    id: str
    base_currency: str
    target_currency: str
    created_at: datetime
    updated_at: datetime

    class Config:
        orm_mode = True


class StockAlertCreate(BaseModel):
    stock_symbol: str = Field(..., min_length=1, max_length=20)
    target_price: float = Field(..., gt=0)
    condition: str = Field(..., regex="^(above|below|equal)$")


class CurrencyAlertCreate(BaseModel):
    base_currency: str = Field(..., min_length=3, max_length=3)
    target_currency: str = Field(..., min_length=3, max_length=3)
    target_rate: float = Field(..., gt=0)
    condition: str = Field(..., regex="^(above|below|equal)$")


class NewsAlertCreate(BaseModel):
    keywords: str = Field(..., min_length=1, max_length=255)


class StockAlertResponse(BaseModel):
    id: str
    stock_symbol: str
    target_price: float
    condition: str
    is_active: bool
    triggered_at: Optional[datetime]
    created_at: datetime
    updated_at: datetime

    class Config:
        orm_mode = True


class CurrencyAlertResponse(BaseModel):
    id: str
    base_currency: str
    target_currency: str
    target_rate: float
    condition: str
    is_active: bool
    triggered_at: Optional[datetime]
    created_at: datetime
    updated_at: datetime

    class Config:
        orm_mode = True


class NewsAlertResponse(BaseModel):
    id: str
    keywords: str
    is_active: bool
    last_checked: Optional[datetime]
    triggered_at: Optional[datetime]
    created_at: datetime
    updated_at: datetime

    class Config:
        orm_mode = True


class NotificationResponse(BaseModel):
    id: str
    alert_id: Optional[str]
    alert_type: str
    message: str
    status: str
    is_read: bool
    extra_data: Dict[str, Any]
    sent_at: datetime

    class Config:
        orm_mode = True


class StockQuoteResponse(BaseModel):
    symbol: str
    name: str
    market: Optional[str] = None
    price: float
    change: Optional[float] = None
    change_percent: Optional[float] = None
    currency: Optional[str] = None
    source: str


class SearchStocksResponse(BaseModel):
    results: List[StockQuoteResponse]


class ExchangeRateResponse(BaseModel):
    base_currency: str
    target_currency: str
    rate: float
    source: str


class NewsArticleResponse(BaseModel):
    title: str
    summary: str
    url: str
    published: str
    source: str


class TechnicalAnalysisResponse(BaseModel):
    asset_type: str
    symbol: str
    name: str
    current_price: float
    price_unit: str
    trend: str
    bias: str
    first_buy: float
    second_buy: float
    first_sell: float
    second_sell: float
    stop_loss: float
    confidence_score: int
    confidence_label: str
    final_score: int
    final_action: str
    trend_score: int
    momentum_score: int
    volume_score: int
    volatility_score: int
    market_context_score: int
    risk_penalty: int
    weighted_risk_penalty: int
    price_basis: str
    market_context_basis: str
    chart_basis: str
    summary_title: str
    summary_body: str
    trend_outlook: str
    action_plan: str
    buy_plan: str
    sell_plan: str
    loss_cut_plan: str
    decision_summary: str
    trend_summary: str
    timing_summary: str
    volume_summary: str
    volatility_summary: str
    market_context_summary: str
    price_reference_summary: str
    decision_reasons: List[str] = Field(default_factory=list)
    trend_reasons: List[str] = Field(default_factory=list)
    momentum_reasons: List[str] = Field(default_factory=list)
    volume_reasons: List[str] = Field(default_factory=list)
    volatility_reasons: List[str] = Field(default_factory=list)
    macro_reasons: List[str] = Field(default_factory=list)
    news_reasons: List[str] = Field(default_factory=list)
    risk_reasons: List[str] = Field(default_factory=list)
    investor_summary: Optional[str] = None
    news_brief: Optional[str] = None
    risk_notes: List[str] = Field(default_factory=list)
    timeframe: str
    source: str
    notes: List[str]


class InternalRunResponse(BaseModel):
    status: str
    triggered: int
    checked: int
