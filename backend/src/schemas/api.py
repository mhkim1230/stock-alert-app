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


class InternalRunResponse(BaseModel):
    status: str
    triggered: int
    checked: int
