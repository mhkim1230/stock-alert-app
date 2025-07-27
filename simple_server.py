#!/usr/bin/env python3
"""
간단한 주식/환율 알림 서버 - 데이터베이스 없이 메모리 기반
"""

from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel
from typing import List, Dict, Optional
import asyncio
import yfinance as yf
import requests
from datetime import datetime
import logging
import uvicorn

# 로깅 설정
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="Stock Alert - 간단한 주식/환율 알림")

# 메모리 저장소
alerts_storage: Dict[str, List[Dict]] = {
    "stock": [],
    "currency": []
}

# 데이터 모델
class StockAlert(BaseModel):
    symbol: str
    condition: str  # "above" or "below"
    price: float

class CurrencyAlert(BaseModel):
    base: str
    target: str
    condition: str  # "above" or "below"
    rate: float

class AlertResponse(BaseModel):
    id: int
    type: str
    message: str
    created_at: str

# 정적 파일 서빙
app.mount("/web_simulator", StaticFiles(directory="web_simulator"), name="web_simulator")

@app.get("/")
async def root():
    return {"message": "📈 Stock Alert API - 간단한 주식/환율 알림 서버", "status": "running"}

@app.get("/web_simulator/")
async def web_simulator():
    return FileResponse("web_simulator/index.html")

# 주식 알림 API
@app.post("/api/alerts/stock")
async def create_stock_alert(alert: StockAlert):
    try:
        # 실제 주식 가격 조회
        current_price = 150.0  # 기본값
        try:
            ticker = yf.Ticker(alert.symbol)
            info = ticker.info
            current_price = info.get('currentPrice', 0)
            
            if current_price == 0:
                # 현재가 조회 실패 시 임시 가격 사용
                current_price = 150.0
        except Exception as e:
            logger.warning(f"주식 가격 조회 실패 {alert.symbol}: {e}")
        
        alert_data = {
            "id": len(alerts_storage["stock"]) + 1,
            "symbol": alert.symbol.upper(),
            "condition": alert.condition,
            "target_price": alert.price,
            "current_price": current_price,
            "active": True,
            "created_at": datetime.now().isoformat()
        }
        
        alerts_storage["stock"].append(alert_data)
        
        logger.info(f"주식 알림 생성: {alert.symbol} {alert.condition} ${alert.price}")
        
        return {
            "success": True,
            "message": f"주식 알림이 생성되었습니다: {alert.symbol} {alert.condition} ${alert.price}",
            "alert": alert_data
        }
        
    except Exception as e:
        logger.error(f"주식 알림 생성 실패: {e}")
        raise HTTPException(status_code=500, detail=f"주식 알림 생성 실패: {str(e)}")

@app.post("/api/alerts/currency")
async def create_currency_alert(alert: CurrencyAlert):
    try:
        # 실제 환율 조회 (무료 API 사용)
        current_rate = get_exchange_rate(alert.base, alert.target)
        
        alert_data = {
            "id": len(alerts_storage["currency"]) + 1,
            "base": alert.base,
            "target": alert.target,
            "condition": alert.condition,
            "target_rate": alert.rate,
            "current_rate": current_rate,
            "active": True,
            "created_at": datetime.now().isoformat()
        }
        
        alerts_storage["currency"].append(alert_data)
        
        logger.info(f"환율 알림 생성: {alert.base}/{alert.target} {alert.condition} {alert.rate}")
        
        return {
            "success": True,
            "message": f"환율 알림이 생성되었습니다: {alert.base}/{alert.target} {alert.condition} {alert.rate}",
            "alert": alert_data
        }
        
    except Exception as e:
        logger.error(f"환율 알림 생성 실패: {e}")
        raise HTTPException(status_code=500, detail=f"환율 알림 생성 실패: {str(e)}")

@app.get("/api/alerts/stock")
async def get_stock_alerts():
    return {"alerts": alerts_storage["stock"]}

@app.get("/api/alerts/currency")
async def get_currency_alerts():
    return {"alerts": alerts_storage["currency"]}

@app.delete("/api/alerts/stock/{alert_id}")
async def delete_stock_alert(alert_id: int):
    alerts_storage["stock"] = [a for a in alerts_storage["stock"] if a["id"] != alert_id]
    return {"success": True, "message": "주식 알림이 삭제되었습니다"}

@app.delete("/api/alerts/currency/{alert_id}")
async def delete_currency_alert(alert_id: int):
    alerts_storage["currency"] = [a for a in alerts_storage["currency"] if a["id"] != alert_id]
    return {"success": True, "message": "환율 알림이 삭제되었습니다"}

@app.get("/api/alerts/check")
async def check_alerts():
    """알림 조건 확인 및 트리거"""
    triggered_alerts = []
    
    # 주식 알림 확인
    for alert in alerts_storage["stock"]:
        if not alert["active"]:
            continue
            
        try:
            # 현재 주식 가격 조회
            current_price = alert["current_price"]  # 기본값
            try:
                ticker = yf.Ticker(alert["symbol"])
                current_price = ticker.info.get('currentPrice', alert["current_price"])
            except Exception as e:
                logger.warning(f"주식 가격 조회 실패 {alert['symbol']}: {e}")
            
            alert["current_price"] = current_price
            
            # 조건 확인
            condition_met = False
            if alert["condition"] == "above" and current_price >= alert["target_price"]:
                condition_met = True
            elif alert["condition"] == "below" and current_price <= alert["target_price"]:
                condition_met = True
            
            if condition_met:
                triggered_alerts.append({
                    "type": "stock",
                    "symbol": alert["symbol"],
                    "message": f"📈 {alert['symbol']} 주식이 ${current_price:.2f}에 도달했습니다! (목표: ${alert['target_price']})",
                    "current_price": current_price,
                    "target_price": alert["target_price"]
                })
                
        except Exception as e:
            logger.error(f"주식 가격 조회 실패 {alert['symbol']}: {e}")
    
    # 환율 알림 확인
    for alert in alerts_storage["currency"]:
        if not alert["active"]:
            continue
            
        try:
            # 현재 환율 조회
            current_rate = get_exchange_rate(alert["base"], alert["target"])
            alert["current_rate"] = current_rate
            
            # 조건 확인
            condition_met = False
            if alert["condition"] == "above" and current_rate >= alert["target_rate"]:
                condition_met = True
            elif alert["condition"] == "below" and current_rate <= alert["target_rate"]:
                condition_met = True
            
            if condition_met:
                triggered_alerts.append({
                    "type": "currency",
                    "pair": f"{alert['base']}/{alert['target']}",
                    "message": f"💱 {alert['base']}/{alert['target']} 환율이 {current_rate:.2f}에 도달했습니다! (목표: {alert['target_rate']})",
                    "current_rate": current_rate,
                    "target_rate": alert["target_rate"]
                })
                
        except Exception as e:
            logger.error(f"환율 조회 실패 {alert['base']}/{alert['target']}: {e}")
    
    return {
        "triggered_count": len(triggered_alerts),
        "triggered_alerts": triggered_alerts,
        "total_stock_alerts": len([a for a in alerts_storage["stock"] if a["active"]]),
        "total_currency_alerts": len([a for a in alerts_storage["currency"] if a["active"]])
    }

def get_exchange_rate(base: str, target: str) -> float:
    """무료 환율 API를 사용하여 환율 조회"""
    try:
        # exchangerate-api (무료)
        url = f"https://api.exchangerate-api.com/v4/latest/{base}"
        response = requests.get(url, timeout=5)
        
        if response.status_code == 200:
            data = response.json()
            rate = data["rates"].get(target, 0)
            if rate > 0:
                return rate
        
        # 실패 시 기본값 반환
        if base == "USD" and target == "KRW":
            return 1350.0  # USD/KRW 기본값
        elif base == "EUR" and target == "KRW":
            return 1450.0  # EUR/KRW 기본값
        else:
            return 1.0
            
    except Exception as e:
        logger.error(f"환율 조회 실패: {e}")
        return 1300.0 if target == "KRW" else 1.0

# 백그라운드 알림 체크 (5분마다)
@app.on_event("startup")
async def startup_event():
    logger.info("📈 Stock Alert 서버 시작")
    logger.info("💡 브라우저에서 http://localhost:8000/web_simulator/ 접속하세요")
    
    # 백그라운드 알림 체크 시작
    asyncio.create_task(background_alert_checker())

async def background_alert_checker():
    """백그라운드에서 5분마다 알림 조건 확인"""
    while True:
        try:
            await asyncio.sleep(300)  # 5분 대기
            result = await check_alerts()
            
            if result["triggered_count"] > 0:
                logger.info(f"🔔 {result['triggered_count']}개의 알림이 트리거되었습니다!")
                for alert in result["triggered_alerts"]:
                    logger.info(f"  - {alert['message']}")
                    
        except Exception as e:
            logger.error(f"백그라운드 알림 체크 오류: {e}")

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True) 