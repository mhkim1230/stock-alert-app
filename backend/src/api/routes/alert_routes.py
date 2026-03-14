from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.api.dependencies import get_protected_db
from src.models.database import CurrencyAlert, NewsAlert, StockAlert
from src.schemas.api import (
    CurrencyAlertCreate,
    CurrencyAlertResponse,
    NewsAlertCreate,
    NewsAlertResponse,
    StockAlertCreate,
    StockAlertResponse,
)

router = APIRouter(prefix="/alerts", tags=["alerts"])


@router.get("/stocks", response_model=List[StockAlertResponse])
async def list_stock_alerts(db: AsyncSession = Depends(get_protected_db)):
    return list((await db.execute(select(StockAlert).order_by(StockAlert.created_at.desc()))).scalars())


@router.post("/stocks", response_model=StockAlertResponse, status_code=status.HTTP_201_CREATED)
async def create_stock_alert(payload: StockAlertCreate, db: AsyncSession = Depends(get_protected_db)):
    alert = StockAlert(
        stock_symbol=payload.stock_symbol.upper(),
        target_price=payload.target_price,
        condition=payload.condition,
    )
    db.add(alert)
    await db.commit()
    await db.refresh(alert)
    return alert


@router.delete("/stocks/{alert_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_stock_alert(alert_id: str, db: AsyncSession = Depends(get_protected_db)):
    alert = (await db.execute(select(StockAlert).where(StockAlert.id == alert_id))).scalar_one_or_none()
    if not alert:
        raise HTTPException(status_code=404, detail="Stock alert not found")
    await db.delete(alert)
    await db.commit()


@router.get("/currencies", response_model=List[CurrencyAlertResponse])
async def list_currency_alerts(db: AsyncSession = Depends(get_protected_db)):
    return list((await db.execute(select(CurrencyAlert).order_by(CurrencyAlert.created_at.desc()))).scalars())


@router.post("/currencies", response_model=CurrencyAlertResponse, status_code=status.HTTP_201_CREATED)
async def create_currency_alert(payload: CurrencyAlertCreate, db: AsyncSession = Depends(get_protected_db)):
    alert = CurrencyAlert(
        base_currency=payload.base_currency.upper(),
        target_currency=payload.target_currency.upper(),
        target_rate=payload.target_rate,
        condition=payload.condition,
    )
    db.add(alert)
    await db.commit()
    await db.refresh(alert)
    return alert


@router.delete("/currencies/{alert_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_currency_alert(alert_id: str, db: AsyncSession = Depends(get_protected_db)):
    alert = (await db.execute(select(CurrencyAlert).where(CurrencyAlert.id == alert_id))).scalar_one_or_none()
    if not alert:
        raise HTTPException(status_code=404, detail="Currency alert not found")
    await db.delete(alert)
    await db.commit()


@router.get("/news", response_model=List[NewsAlertResponse])
async def list_news_alerts(db: AsyncSession = Depends(get_protected_db)):
    return list((await db.execute(select(NewsAlert).order_by(NewsAlert.created_at.desc()))).scalars())


@router.post("/news", response_model=NewsAlertResponse, status_code=status.HTTP_201_CREATED)
async def create_news_alert(payload: NewsAlertCreate, db: AsyncSession = Depends(get_protected_db)):
    alert = NewsAlert(keywords=payload.keywords)
    db.add(alert)
    await db.commit()
    await db.refresh(alert)
    return alert


@router.delete("/news/{alert_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_news_alert(alert_id: str, db: AsyncSession = Depends(get_protected_db)):
    alert = (await db.execute(select(NewsAlert).where(NewsAlert.id == alert_id))).scalar_one_or_none()
    if not alert:
        raise HTTPException(status_code=404, detail="News alert not found")
    await db.delete(alert)
    await db.commit()
