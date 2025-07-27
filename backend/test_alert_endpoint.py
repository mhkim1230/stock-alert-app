#!/usr/bin/env python3
"""
알람 API 테스트 스크립트
"""

import sys
import os
sys.path.append('.')

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import uvicorn

app = FastAPI(title="Alert Test Server")

class StockAlertCreate(BaseModel):
    stock_symbol: str
    target_price: float
    condition: str

class CurrencyAlertCreate(BaseModel):
    base_currency: str
    target_currency: str
    target_rate: float
    condition: str

@app.get("/")
async def root():
    return {"message": "✅ 알람 테스트 서버 작동 중"}

@app.get("/health")
async def health():
    return {"status": "healthy"}

@app.post("/alerts/stock")
async def create_stock_alert(alert_data: StockAlertCreate):
    """주식 알림 생성 테스트"""
    try:
        print(f"📥 주식 알람 생성 요청: {alert_data}")
        
        # 간단한 검증
        if not alert_data.stock_symbol:
            raise HTTPException(status_code=400, detail="주식 심볼이 필요합니다")
        
        if alert_data.target_price <= 0:
            raise HTTPException(status_code=400, detail="목표 가격은 0보다 커야 합니다")
        
        if alert_data.condition not in ['above', 'below', 'equal']:
            raise HTTPException(status_code=400, detail="조건은 above, below, equal 중 하나여야 합니다")
        
        # 성공 응답
        return {
            "id": 123,
            "stock_symbol": alert_data.stock_symbol,
            "target_price": alert_data.target_price,
            "condition": alert_data.condition,
            "message": "✅ 주식 알람 생성 성공 (테스트)"
        }
        
    except Exception as e:
        print(f"❌ 주식 알람 생성 오류: {e}")
        raise HTTPException(status_code=500, detail=f"주식 알람 생성 중 오류: {str(e)}")

@app.post("/alerts/currency")
async def create_currency_alert(alert_data: CurrencyAlertCreate):
    """환율 알림 생성 테스트"""
    try:
        print(f"📥 환율 알람 생성 요청: {alert_data}")
        
        # 간단한 검증
        if not alert_data.base_currency or not alert_data.target_currency:
            raise HTTPException(status_code=400, detail="기준 통화와 대상 통화가 필요합니다")
        
        if alert_data.target_rate <= 0:
            raise HTTPException(status_code=400, detail="목표 환율은 0보다 커야 합니다")
        
        if alert_data.condition not in ['above', 'below', 'equal']:
            raise HTTPException(status_code=400, detail="조건은 above, below, equal 중 하나여야 합니다")
        
        # 성공 응답
        return {
            "id": 124,
            "base_currency": alert_data.base_currency,
            "target_currency": alert_data.target_currency,
            "target_rate": alert_data.target_rate,
            "condition": alert_data.condition,
            "message": "✅ 환율 알람 생성 성공 (테스트)"
        }
        
    except Exception as e:
        print(f"❌ 환율 알람 생성 오류: {e}")
        raise HTTPException(status_code=500, detail=f"환율 알람 생성 중 오류: {str(e)}")

@app.get("/alerts/stock")
async def get_stock_alerts():
    """주식 알림 목록 조회 테스트"""
    return [
        {
            "id": 123,
            "stock_symbol": "005930",
            "target_price": 65000,
            "condition": "above",
            "message": "테스트 주식 알람"
        }
    ]

@app.get("/alerts/currency")
async def get_currency_alerts():
    """환율 알림 목록 조회 테스트"""
    return [
        {
            "id": 124,
            "base_currency": "USD",
            "target_currency": "KRW",
            "target_rate": 1300,
            "condition": "above",
            "message": "테스트 환율 알람"
        }
    ]

if __name__ == "__main__":
    print("🧪 알람 테스트 서버 시작...")
    print("📡 URL: http://localhost:8002")
    print("📈 주식 알람: POST /alerts/stock")
    print("💱 환율 알람: POST /alerts/currency") 
    uvicorn.run(app, host="0.0.0.0", port=8002, log_level="info") 