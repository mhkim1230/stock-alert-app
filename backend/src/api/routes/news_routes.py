from fastapi import APIRouter, Query, HTTPException
from typing import Optional, List
from datetime import datetime

from src.services.news_service import NewsService

router = APIRouter(prefix="/news", tags=["News"])
news_service = NewsService()

@router.get("/")
async def get_news(
    category: Optional[str] = Query("general", description="뉴스 카테고리"),
    limit: int = Query(20, ge=1, le=100, description="뉴스 개수")
):
    """뉴스 목록 조회"""
    try:
        news_data = await news_service.get_news_by_category(category, limit)
        
        return {
            "status": "success",
            "data": news_data,
            "count": len(news_data),
            "category": category
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"뉴스 조회 중 오류 발생: {str(e)}"
        )

@router.get("/search")
async def search_news(
    query: str = Query(..., description="검색 키워드"),
    limit: int = Query(20, ge=1, le=100, description="뉴스 개수")
):
    """뉴스 검색"""
    try:
        news_data = await news_service.search_news(query, limit)
        
        return {
            "status": "success",
            "data": news_data,
            "count": len(news_data),
            "query": query
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"뉴스 검색 중 오류 발생: {str(e)}"
        ) 