from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from pydantic import BaseModel, Field
from typing import Optional
import uuid

from src.services.auth_service import AuthService
from src.models.database import User
from src.services.user_service import UserService

router = APIRouter()
auth_service = AuthService()
user_service = UserService()

class UserProfileUpdate(BaseModel):
    """사용자 프로필 업데이트 요청 모델"""
    username: Optional[str] = Field(None, description="새 사용자명", min_length=3, max_length=50)
    email: Optional[str] = Field(None, description="새 이메일 주소")

class UserProfileResponse(BaseModel):
    """사용자 프로필 응답 모델"""
    id: uuid.UUID
    username: str
    email: str
    is_active: bool
    last_login: Optional[str] = None
    profile_image_url: Optional[str] = None

@router.get("/profile", response_model=UserProfileResponse)
async def get_user_profile(
    current_user: User = Depends(auth_service.get_current_user)
):
    """현재 사용자 프로필 조회"""
    return UserProfileResponse(
        id=current_user.id,
        username=current_user.username,
        email=current_user.email,
        is_active=current_user.is_active,
        last_login=str(current_user.last_login) if current_user.last_login else None
    )

@router.put("/profile", response_model=UserProfileResponse)
async def update_user_profile(
    profile_update: UserProfileUpdate,
    current_user: User = Depends(auth_service.get_current_user)
):
    """사용자 프로필 업데이트"""
    try:
        updated_user = await user_service.update_user_profile(
            user_id=current_user.id,
            username=profile_update.username,
            email=profile_update.email
        )
        return UserProfileResponse(
            id=updated_user.id,
            username=updated_user.username,
            email=updated_user.email,
            is_active=updated_user.is_active,
            last_login=str(updated_user.last_login) if updated_user.last_login else None
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/profile/image")
async def upload_profile_image(
    file: UploadFile = File(...),
    current_user: User = Depends(auth_service.get_current_user)
):
    """프로필 이미지 업로드"""
    try:
        # 이미지 업로드 및 URL 반환
        profile_image_url = await user_service.upload_profile_image(
            user_id=current_user.id, 
            file=file
        )
        return {"profile_image_url": profile_image_url}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/dashboard/stats")
async def get_user_dashboard_stats(
    current_user: User = Depends(auth_service.get_current_user)
):
    """사용자 대시보드 통계 조회"""
    try:
        stats = await user_service.get_user_dashboard_stats(user_id=current_user.id)
        return stats
    except Exception as e:
        raise HTTPException(status_code=500, detail="대시보드 통계를 가져오는 중 오류가 발생했습니다.") 