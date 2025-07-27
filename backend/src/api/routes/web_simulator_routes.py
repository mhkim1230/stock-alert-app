"""
웹 시뮬레이터 라우트
iOS 시뮬레이터에서 테스트할 수 있는 웹 앱 서빙
"""

from fastapi import APIRouter, Request, HTTPException
from fastapi.responses import HTMLResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from typing import List, Optional
import os
from pathlib import Path
from datetime import datetime

router = APIRouter()

# 테스트용 메모리 저장소
test_stock_alerts = []
test_currency_alerts = []

class TestStockAlert(BaseModel):
    symbol: str
    target_price: float
    condition: str

class TestCurrencyAlert(BaseModel):
    base_currency: str
    target_currency: str
    target_rate: float
    condition: str

# 웹 시뮬레이터 HTML 파일 경로
WEB_SIMULATOR_PATH = Path(__file__).parent.parent.parent.parent / "web_simulator"

@router.get("/web_simulator/", response_class=HTMLResponse)
async def serve_web_simulator():
    """웹 시뮬레이터 메인 페이지 서빙"""
    html_file = WEB_SIMULATOR_PATH / "index.html"
    
    if html_file.exists():
        with open(html_file, 'r', encoding='utf-8') as f:
            content = f.read()
        return HTMLResponse(content=content)
    else:
        return HTMLResponse(
            content="""
            <html>
                <head>
                    <title>웹 시뮬레이터 오류</title>
                    <meta charset="UTF-8">
                    <meta name="viewport" content="width=device-width, initial-scale=1.0">
                </head>
                <body style="font-family: -apple-system, BlinkMacSystemFont, sans-serif; padding: 20px; text-align: center;">
                    <h1>❌ 웹 시뮬레이터를 찾을 수 없습니다</h1>
                    <p>web_simulator/index.html 파일이 존재하지 않습니다.</p>
                    <p>경로: {}</p>
                </body>
            </html>
            """.format(html_file),
            status_code=404
        )

@router.get("/web_simulator/test")
async def web_simulator_test():
    """웹 시뮬레이터 테스트 엔드포인트"""
    return {
        "status": "success",
        "message": "웹 시뮬레이터 테스트 성공",
        "cost": "₩0 (완전 무료!)",
        "features": [
            "이메일 알림 (Gmail SMTP)",
            "FCM 푸시 알림 (Firebase)",
            "텔레그램 봇 알림",
            "웹 푸시 알림"
        ]
    }

@router.get("/web_simulator/status")
async def web_simulator_status():
    """웹 시뮬레이터 시스템 상태"""
    return {
        "system": "완전 무료 알림 시스템",
        "status": "정상 작동",
        "cost": "₩0",
        "annual_savings": "$99+",
        "notification_channels": 4,
        "platform_support": ["iOS", "Android", "Web", "Desktop"]
    } 

# 테스트용 주식 알림 엔드포인트 (인증 없이 사용 가능)
@router.post("/api/alerts/stock")
async def create_test_stock_alert(alert: TestStockAlert):
    """테스트용 주식 알림 생성 (웹 시뮬레이터용)"""
    new_alert = {
        "id": len(test_stock_alerts) + 1,
        "symbol": alert.symbol,
        "target_price": alert.target_price,
        "condition": alert.condition,
        "is_active": True,
        "created_at": datetime.now().isoformat(),
        "triggered_at": None
    }
    test_stock_alerts.append(new_alert)
    return new_alert

@router.get("/api/alerts/stock")
async def get_test_stock_alerts():
    """테스트용 주식 알림 목록 조회 (웹 시뮬레이터용)"""
    return test_stock_alerts

@router.delete("/api/alerts/stock/{alert_id}")
async def delete_test_stock_alert(alert_id: int):
    """테스트용 주식 알림 삭제 (웹 시뮬레이터용)"""
    global test_stock_alerts
    test_stock_alerts = [alert for alert in test_stock_alerts if alert["id"] != alert_id]
    return {"message": "알림이 삭제되었습니다."}

# 테스트용 환율 알림 엔드포인트 (인증 없이 사용 가능)
@router.post("/api/alerts/currency")
async def create_test_currency_alert(alert: TestCurrencyAlert):
    """테스트용 환율 알림 생성 (웹 시뮬레이터용)"""
    new_alert = {
        "id": len(test_currency_alerts) + 1,
        "base_currency": alert.base_currency,
        "target_currency": alert.target_currency,
        "target_rate": alert.target_rate,
        "condition": alert.condition,
        "is_active": True,
        "created_at": datetime.now().isoformat(),
        "triggered_at": None
    }
    test_currency_alerts.append(new_alert)
    return new_alert

@router.get("/api/alerts/currency")
async def get_test_currency_alerts():
    """테스트용 환율 알림 목록 조회 (웹 시뮬레이터용)"""
    return test_currency_alerts

@router.delete("/api/alerts/currency/{alert_id}")
async def delete_test_currency_alert(alert_id: int):
    """테스트용 환율 알림 삭제 (웹 시뮬레이터용)"""
    global test_currency_alerts
    test_currency_alerts = [alert for alert in test_currency_alerts if alert["id"] != alert_id]
    return {"message": "알림이 삭제되었습니다."} 