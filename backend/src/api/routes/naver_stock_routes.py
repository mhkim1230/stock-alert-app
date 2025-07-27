#!/usr/bin/env python3
"""
네이버 파싱 기반 실제 주식 검색 API
- 실시간 네이버 파이낸스 데이터
- 삼성전자, 애플 등 주요 주식 지원
"""

from fastapi import APIRouter, HTTPException
from typing import List, Dict, Any
import logging

from src.services.naver_stock_service import naver_stock_service

router = APIRouter()
logger = logging.getLogger(__name__)

@router.get("/stocks/search/{query}")
async def search_stocks_naver(query: str) -> Dict[str, Any]:
    """
    네이버 파싱 기반 실시간 주식 검색
    - 삼성전자, 애플, 테슬라 등 주요 주식 지원
    - 실제 네이버 파이낸스에서 파싱
    """
    try:
        logger.info(f"🔍 네이버 주식 검색 요청: {query}")
        
        # 네이버에서 실시간 주식 정보 파싱
        results = await naver_stock_service.search_stock(query)
        
        if not results:
            return {
                "query": query,
                "results": [],
                "count": 0,
                "source": "naver_real",
                "message": "검색 결과가 없습니다"
            }
        
        return {
            "query": query,
            "results": results,
            "count": len(results),
            "source": "naver_real",
            "message": "실시간 네이버 파싱 성공"
        }
        
    except Exception as e:
        logger.error(f"❌ 네이버 주식 검색 실패: {e}")
        raise HTTPException(
            status_code=500, 
            detail=f"주식 검색 중 오류 발생: {str(e)}"
        )

@router.get("/currency/rate/{from_currency}/{to_currency}")
async def get_exchange_rate_naver(from_currency: str, to_currency: str) -> Dict[str, Any]:
    """
    네이버 파싱 기반 실시간 환율 조회
    - USD/KRW, EUR/KRW 등 주요 환율 지원
    - 실제 네이버에서 파싱
    """
    try:
        logger.info(f"💱 네이버 환율 조회 요청: {from_currency}→{to_currency}")
        
        # 네이버에서 실시간 환율 정보 파싱
        rate = await naver_stock_service.get_exchange_rate(from_currency, to_currency)
        
        if rate <= 0:
            raise HTTPException(
                status_code=404,
                detail=f"환율 정보를 찾을 수 없습니다: {from_currency}→{to_currency}"
            )
        
        return {
            "base_currency": from_currency.upper(),
            "target_currency": to_currency.upper(),
            "rate": round(rate, 4),
            "source": "naver_real",
            "last_updated": "실시간"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ 네이버 환율 조회 실패: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"환율 조회 중 오류 발생: {str(e)}"
        )

@router.get("/test/naver/{query}")
async def test_naver_parsing(query: str) -> Dict[str, Any]:
    """
    네이버 파싱 테스트 엔드포인트
    - 디버깅용
    """
    try:
        logger.info(f"🧪 네이버 파싱 테스트: {query}")
        
        if query in ['삼성전자', '삼성', 'samsung']:
            # 삼성전자 테스트
            results = await naver_stock_service.search_stock('삼성전자')
        elif query.lower() in ['aapl', '애플', 'apple']:
            # 애플 테스트
            results = await naver_stock_service.search_stock('애플')
        else:
            # 일반 검색
            results = await naver_stock_service.search_stock(query)
        
        return {
            "test_query": query,
            "results": results,
            "count": len(results),
            "status": "success" if results else "no_results",
            "message": f"네이버 파싱 테스트 완료: {len(results)}개 결과"
        }
        
    except Exception as e:
        logger.error(f"❌ 네이버 파싱 테스트 실패: {e}")
        return {
            "test_query": query,
            "results": [],
            "count": 0,
            "status": "error",
            "error": str(e),
            "message": "네이버 파싱 테스트 실패"
        } 