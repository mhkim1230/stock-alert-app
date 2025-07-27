#!/usr/bin/env python3
"""
개선된 네이버 파싱 API 서버
- 하드코딩 제거
- 동적 파싱 서비스 사용
- 정확한 종목명 추출
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
from urllib.parse import quote

# 동적 파싱 서비스 import
from src.services.naver_stock_service import naver_stock_service

app = FastAPI(title="개선된 네이버 금융 파싱 API")

# CORS 설정
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
async def root():
    return {"message": "🚀 개선된 네이버 금융 실시간 파싱 API", "status": "running", "version": "2.0"}

@app.get("/health")
async def health():
    return {"status": "healthy", "service": "naver_parsing_improved", "features": ["dynamic_parsing", "no_hardcoding"]}

@app.get("/naver/stocks/search/{query}")
async def search_stocks(query: str):
    """개선된 동적 파싱 서비스를 사용한 주식 검색"""
    print(f"🔍 주식 검색 (동적 파싱 v2.0): {query}")
    
    try:
        # 새로운 동적 파싱 서비스로 검색
        stocks = await naver_stock_service.search_stock(query)
        
        print(f"✅ 동적 파싱 검색 완료: {len(stocks)}개 종목 발견")
        
        # 결과가 있으면 반환
        if stocks:
            return {
                "results": stocks,
                "query": query,
                "source": "dynamic_parsing",
                "version": "2.0"
            }
        
        # 결과가 없으면 빈 배열 반환
        return {
            "results": [],
            "query": query,
            "message": "검색 결과가 없습니다",
            "source": "dynamic_parsing", 
            "version": "2.0"
        }
        
    except Exception as e:
        print(f"❌ 검색 오류: {e}")
        raise HTTPException(status_code=500, detail=f"검색 중 오류 발생: {str(e)}")

@app.get("/naver/stocks/detail/{symbol}")
async def get_stock_detail(symbol: str):
    """종목코드로 상세 정보 조회"""
    print(f"🔍 종목 상세 조회: {symbol}")
    
    try:
        # 종목코드로 직접 조회
        results = await naver_stock_service.search_stock(symbol)
        
        if results:
            return {
                "result": results[0],
                "symbol": symbol,
                "source": "dynamic_parsing",
                "version": "2.0"
            }
        else:
            raise HTTPException(status_code=404, detail=f"종목을 찾을 수 없습니다: {symbol}")
            
    except Exception as e:
        print(f"❌ 종목 상세 조회 오류: {e}")
        raise HTTPException(status_code=500, detail=f"종목 조회 중 오류 발생: {str(e)}")

@app.get("/naver/currency/rate/{from_currency}/{to_currency}")
async def get_currency_rate(from_currency: str, to_currency: str):
    """환율 정보 조회"""
    print(f"🔍 환율 조회: {from_currency} -> {to_currency}")
    
    try:
        rate = await naver_stock_service.get_exchange_rate(from_currency, to_currency)
        
        return {
            "from_currency": from_currency,
            "to_currency": to_currency,
            "rate": rate,
            "source": "dynamic_parsing",
            "version": "2.0"
        }
        
    except Exception as e:
        print(f"❌ 환율 조회 오류: {e}")
        raise HTTPException(status_code=500, detail=f"환율 조회 중 오류 발생: {str(e)}")

if __name__ == "__main__":
    print("🚀 개선된 네이버 파싱 서버 시작")
    print("  - 하드코딩 제거 ✅")
    print("  - 동적 파싱 ✅") 
    print("  - 정확한 종목명 ✅")
    print("  - 포트: 8001")
    
    uvicorn.run(app, host="0.0.0.0", port=8001) 