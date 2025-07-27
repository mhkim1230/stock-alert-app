#!/usr/bin/env python3
"""
깔끔한 주식 API - 하드코딩 없음
사용자가 한국/해외 구분
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
import asyncio
import requests
import re
from bs4 import BeautifulSoup
from urllib.parse import quote
from typing import Dict, List, Optional
import logging

app = FastAPI(title="🎯 깔끔한 주식 API - Zero Hardcoding")

# CORS 설정
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 로깅 설정
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# HTTP 헤더
HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
    'Accept-Language': 'ko-KR,ko;q=0.9,en;q=0.8',
}

@app.get("/")
async def root():
    return {
        "service": "🎯 깔끔한 주식 API", 
        "version": "1.0",
        "features": ["zero_hardcoding", "user_driven_separation"],
        "endpoints": {
            "korean": "/stocks/korea/{query}",
            "world": "/stocks/world/{symbol}",
            "auto": "/stocks/auto/{query}"
        }
    }

@app.get("/stocks/korea/{query}")
async def get_korean_stock(query: str):
    """
    한국 주식 조회 (네이버 동적 파싱)
    
    Args:
        query: 종목명 또는 종목코드 (예: "삼성전자", "005930")
    """
    try:
        logger.info(f"🇰🇷 한국 주식 조회: {query}")
        
        # 종목코드 찾기 (네이버 검색 사용)
        code = await find_korean_stock_code(query)
        if not code:
            raise HTTPException(status_code=404, detail=f"한국 주식을 찾을 수 없습니다: {query}")
        
        # 네이버 금융에서 실시간 데이터 파싱
        stock_data = await parse_korean_stock(code)
        if not stock_data:
            raise HTTPException(status_code=500, detail=f"주식 데이터 파싱 실패: {code}")
        
        return {
            "success": True,
            "market": "korea",
            "data": stock_data,
            "source": "naver_dynamic_parsing"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ 한국 주식 조회 오류: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/stocks/world/{symbol}")
async def get_world_stock(symbol: str):
    """
    해외 주식 조회 (외부 API 사용)
    
    Args:
        symbol: 해외 주식 심볼 (예: "NVDA", "AAPL")
    """
    try:
        logger.info(f"🌍 해외 주식 조회: {symbol}")
        
        # Yahoo Finance API 사용 (무료, 인증 없음)
        stock_data = await get_yahoo_finance_data(symbol)
        if not stock_data:
            raise HTTPException(status_code=404, detail=f"해외 주식을 찾을 수 없습니다: {symbol}")
        
        return {
            "success": True,
            "market": "world",
            "data": stock_data,
            "source": "yahoo_finance"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ 해외 주식 조회 오류: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/stocks/auto/{query}")
async def get_stock_auto(query: str):
    """
    자동 구분 조회 (네이버 검색 활용)
    
    Args:
        query: 종목명 (예: "삼성전자", "엔비디아")
    """
    try:
        logger.info(f"🔍 자동 구분 조회: {query}")
        
        # 네이버 검색으로 한국/해외 구분
        classification = await classify_stock_via_naver(query)
        
        if classification["type"] == "korean":
            return await get_korean_stock(classification["code"])
        elif classification["type"] == "world":
            return await get_world_stock(classification["symbol"])
        else:
            raise HTTPException(status_code=404, detail=f"종목을 찾을 수 없습니다: {query}")
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ 자동 구분 조회 오류: {e}")
        raise HTTPException(status_code=500, detail=str(e))

async def find_korean_stock_code(query: str) -> Optional[str]:
    """네이버 검색으로 한국 종목코드 찾기"""
    try:
        # 6자리 숫자면 종목코드로 간주
        if query.isdigit() and len(query) == 6:
            return query
        
        # 네이버 검색
        search_query = quote(f"{query} 주가")
        url = f"https://search.naver.com/search.naver?query={search_query}"
        
        response = requests.get(url, headers=HEADERS, timeout=10)
        response.raise_for_status()
        
        # 한국 주식 패턴 찾기
        codes = re.findall(r'finance\.naver\.com/item/main\.naver\?code=(\d{6})', response.text)
        return codes[0] if codes else None
        
    except Exception as e:
        logger.error(f"❌ 종목코드 찾기 실패: {e}")
        return None

async def parse_korean_stock(code: str) -> Optional[Dict]:
    """네이버 금융에서 한국 주식 데이터 파싱"""
    try:
        url = f"https://finance.naver.com/item/main.naver?code={code}"
        response = requests.get(url, headers=HEADERS, timeout=10)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # 종목명 추출 (title 태그에서)
        title = soup.find('title')
        stock_name = title.get_text().split(':')[0].strip() if title else code
        
        # 현재가 추출 (.today .blind에서)
        current_price = None
        today_blinds = soup.select('.today .blind')
        for blind in today_blinds:
            price_text = blind.get_text().replace(',', '')
            if price_text.isdigit():
                current_price = float(price_text)
                break
        
        # 변동률 추출 (% 포함된 텍스트에서)
        change_percent = None
        all_text = soup.get_text()
        percent_matches = re.findall(r'([+-]?\d+\.?\d*)%', all_text)
        if percent_matches:
            for match in percent_matches:
                try:
                    pct = float(match)
                    if -30 <= pct <= 30:  # 합리적 범위
                        change_percent = pct
                        break
                except:
                    continue
        
        if not current_price:
            return None
            
        return {
            "symbol": code,
            "name": stock_name,
            "current_price": current_price,
            "change_percent": change_percent or 0.0,
            "currency": "KRW"
        }
        
    except Exception as e:
        logger.error(f"❌ 한국 주식 파싱 실패: {e}")
        return None

async def get_yahoo_finance_data(symbol: str) -> Optional[Dict]:
    """Yahoo Finance에서 해외 주식 데이터 조회"""
    try:
        # Yahoo Finance 무료 API (실제로는 웹 스크래핑)
        url = f"https://finance.yahoo.com/quote/{symbol}"
        response = requests.get(url, headers=HEADERS, timeout=10)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # 종목명 추출
        name_elem = soup.find('h1', {'data-field': 'name'}) or soup.find('h1')
        stock_name = name_elem.get_text().strip() if name_elem else symbol
        
        # 현재가 추출 (여러 선택자 시도)
        price_selectors = [
            '[data-field="regularMarketPrice"]',
            '.Fw\\(b\\).Fz\\(36px\\)',
            '.Trsdu\\(0\\.3s\\).Fw\\(b\\).Fz\\(36px\\)',
            '.livePrice span'
        ]
        
        current_price = None
        for selector in price_selectors:
            price_elem = soup.select_one(selector)
            if price_elem:
                price_text = price_elem.get_text().replace(',', '').replace('$', '')
                try:
                    current_price = float(price_text)
                    break
                except:
                    continue
        
        # 변동률 추출
        change_selectors = [
            '[data-field="regularMarketChangePercent"]',
            '.Fw\\(500\\).Pstart\\(8px\\)',
            '.Trsdu\\(0\\.3s\\).Fw\\(500\\)'
        ]
        
        change_percent = None
        for selector in change_selectors:
            change_elem = soup.select_one(selector)
            if change_elem:
                change_text = change_elem.get_text()
                match = re.search(r'([+-]?\d+\.?\d*)%', change_text)
                if match:
                    try:
                        change_percent = float(match.group(1))
                        break
                    except:
                        continue
        
        if not current_price:
            return None
            
        return {
            "symbol": symbol,
            "name": stock_name,
            "current_price": current_price,
            "change_percent": change_percent or 0.0,
            "currency": "USD"
        }
        
    except Exception as e:
        logger.error(f"❌ Yahoo Finance 조회 실패: {e}")
        return None

async def classify_stock_via_naver(query: str) -> Dict:
    """네이버 검색으로 주식 분류"""
    try:
        search_query = quote(f"{query} 주가")
        url = f"https://search.naver.com/search.naver?query={search_query}"
        
        response = requests.get(url, headers=HEADERS, timeout=10)
        response.raise_for_status()
        
        html = response.text
        
        # 한국 주식 패턴
        korean_codes = re.findall(r'finance\.naver\.com/item/main\.naver\?code=(\d{6})', html)
        if korean_codes:
            return {"type": "korean", "code": korean_codes[0]}
        
        # 해외 주식 패턴
        world_symbols = re.findall(r'worldstock/stock/([A-Z\.]+)', html)
        if world_symbols:
            clean_symbol = world_symbols[0].split('.')[0]  # .O 제거
            return {"type": "world", "symbol": clean_symbol}
        
        return {"type": "unknown"}
        
    except Exception as e:
        logger.error(f"❌ 주식 분류 실패: {e}")
        return {"type": "unknown"}

if __name__ == "__main__":
    logger.info("🚀 깔끔한 주식 API 시작 (포트 8002)")
    uvicorn.run(app, host="0.0.0.0", port=8002) 