from typing import List, Optional

from fastapi import APIRouter, Depends

from src.api.dependencies import require_admin_key
from src.schemas.api import NewsArticleResponse
from src.services.news_service import NewsService

router = APIRouter(prefix="/news", tags=["news"])
news_service = NewsService()


@router.get("", response_model=List[NewsArticleResponse], dependencies=[Depends(require_admin_key)])
async def get_news(query: Optional[str] = None, limit: int = 10):
    return await news_service.get_latest_news(query=query, limit=limit)
