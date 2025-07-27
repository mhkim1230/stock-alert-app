from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import List
from datetime import datetime

from src.services.auth_service import get_current_user
from src.models.database import User, Watchlist, get_db

router = APIRouter(prefix="/watchlist", tags=["Watchlist"])

class WatchlistCreate(BaseModel):
    """관심종목 추가 요청 모델"""
    symbol: str

class WatchlistResponse(BaseModel):
    """관심종목 응답 모델"""
    id: str
    symbol: str
    created_at: datetime

@router.post("", response_model=WatchlistResponse)
async def add_to_watchlist(
    watchlist_data: WatchlistCreate,
    current_user: User = Depends(get_current_user)
):
    """관심종목 추가"""
    try:
        # 이미 존재하는지 확인
        existing = Watchlist.select().where(
            (Watchlist.user == current_user.id) & 
            (Watchlist.symbol == watchlist_data.symbol.upper())
        ).first()
        
        if existing:
            raise HTTPException(
                status_code=400,
                detail="이미 관심종목으로 등록되어 있습니다."
            )
        
        # 새 관심종목 추가
        new_item = Watchlist.create(
            user=current_user.id,
            symbol=watchlist_data.symbol.upper()
        )
        
        return WatchlistResponse(
            id=new_item.id,
            symbol=new_item.symbol,
            created_at=new_item.created_at
        )
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"관심종목 추가 중 오류 발생: {str(e)}"
        )

@router.get("", response_model=List[WatchlistResponse])
async def get_watchlist(
    current_user: User = Depends(get_current_user)
):
    """관심종목 목록 조회"""
    try:
        items = list(Watchlist.select().where(Watchlist.user == current_user.id))
        
        return [
            WatchlistResponse(
                id=item.id,
                symbol=item.symbol,
                created_at=item.created_at
            )
            for item in items
        ]
    
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"관심종목 조회 중 오류 발생: {str(e)}"
        )

@router.delete("/{symbol}")
async def remove_from_watchlist(
    symbol: str,
    current_user: User = Depends(get_current_user)
):
    """관심종목 삭제"""
    try:
        item = Watchlist.select().where(
            (Watchlist.user == current_user.id) & 
            (Watchlist.symbol == symbol.upper())
        ).first()
        
        if not item:
            raise HTTPException(
                status_code=404,
                detail="관심종목을 찾을 수 없습니다."
            )
        
        item.delete_instance()
        
        return {"message": "관심종목이 성공적으로 삭제되었습니다."}
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"관심종목 삭제 중 오류 발생: {str(e)}"
        ) 