from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from pydantic import BaseModel, EmailStr, Field
from typing import Optional
import uuid

from src.services.auth_service import AuthService, get_current_user
from src.services.notification_service import notification_service
from src.models.database import User

router = APIRouter(prefix="/auth", tags=["Authentication"])
auth_service = AuthService()

class UserCreate(BaseModel):
    """사용자 생성 요청 모델"""
    username: str
    email: EmailStr
    password: str

class UserResponse(BaseModel):
    """사용자 응답 모델"""
    id: str
    username: str
    email: str

class TokenResponse(BaseModel):
    """토큰 응답 모델"""
    access_token: str
    token_type: str

class DeviceTokenRequest(BaseModel):
    """디바이스 토큰 등록 요청 모델"""
    device_token: str
    platform: Optional[str] = "iOS"

class TestNotificationRequest(BaseModel):
    """테스트 알림 요청 모델"""
    title: Optional[str] = "테스트 알림"
    body: Optional[str] = "푸시 알림 테스트입니다."

@router.post("/signup", response_model=UserResponse)
async def signup(user: UserCreate):
    """사용자 회원가입"""
    try:
        new_user = await auth_service.create_user(
            username=user.username,
            email=user.email,
            password=user.password
        )
        return UserResponse(
            id=str(new_user.id),
            username=new_user.username,
            email=new_user.email
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/login", response_model=TokenResponse)
async def login(form_data: OAuth2PasswordRequestForm = Depends()):
    """사용자 로그인"""
    try:
        token = await auth_service.authenticate_user(
            form_data.username, 
            form_data.password
        )
        return TokenResponse(
            access_token=token, 
            token_type="bearer"
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e),
            headers={"WWW-Authenticate": "Bearer"}
        )

@router.post("/refresh-token", response_model=TokenResponse)
async def refresh_token(token: str):
    """토큰 갱신"""
    try:
        new_token = await auth_service.refresh_token(token)
        return TokenResponse(
            access_token=new_token, 
            token_type="bearer"
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e),
            headers={"WWW-Authenticate": "Bearer"}
        )

@router.get("/profile", response_model=UserResponse)
async def get_profile(current_user: User = Depends(auth_service.get_current_user)):
    """현재 사용자 프로필 조회"""
    return UserResponse(
        id=str(current_user.id),
        username=current_user.username,
        email=current_user.email
    )

@router.put("/profile")
async def update_profile(
    username: Optional[str] = None,
    email: Optional[EmailStr] = None,
    current_user: User = Depends(auth_service.get_current_user)
):
    """사용자 프로필 업데이트"""
    try:
        updated_user = await auth_service.update_user_profile(
            user_id=current_user.id,
            username=username,
            email=email
        )
        return UserResponse(
            id=str(updated_user.id),
            username=updated_user.username,
            email=updated_user.email
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/register-device-token")
async def register_device_token(
    request: DeviceTokenRequest, 
    current_user: User = Depends(get_current_user)
):
    """
    사용자의 디바이스 토큰 등록
    
    :param request: 디바이스 토큰 및 플랫폼 정보
    :param current_user: 현재 인증된 사용자
    :return: 토큰 등록 결과
    """
    try:
        # 디바이스 토큰 등록 서비스 호출
        result = await notification_service.register_device_token(
            user_id=current_user.id,
            device_token=request.device_token,
            platform=request.platform
        )
        
        if result:
            return {
                "status": "success", 
                "message": "디바이스 토큰이 성공적으로 등록되었습니다.",
                "platform": request.platform
            }
        else:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="디바이스 토큰 등록에 실패했습니다."
            )
    
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"디바이스 토큰 등록 중 오류 발생: {str(e)}"
        )

@router.delete("/unregister-device-token/{device_token}")
async def unregister_device_token(
    device_token: str,
    current_user: User = Depends(get_current_user)
):
    """
    디바이스 토큰 해제
    
    :param device_token: 해제할 디바이스 토큰
    :param current_user: 현재 인증된 사용자
    :return: 토큰 해제 결과
    """
    try:
        result = await notification_service.unregister_device_token(device_token)
        
        if result:
            return {
                "status": "success",
                "message": "디바이스 토큰이 성공적으로 해제되었습니다."
            }
        else:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="해제할 디바이스 토큰을 찾을 수 없습니다."
            )
    
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"디바이스 토큰 해제 중 오류 발생: {str(e)}"
        )

@router.post("/test-notification")
async def test_push_notification(
    request: TestNotificationRequest,
    current_user: User = Depends(get_current_user)
):
    """
    테스트 푸시 알림 전송
    
    :param request: 테스트 알림 내용
    :param current_user: 현재 인증된 사용자
    :return: 알림 전송 결과
    """
    try:
        result = await notification_service.send_push_notification(
            user_id=current_user.id,
            title=request.title,
            body=request.body,
            extra_data={"test": True, "timestamp": str(uuid.uuid4())}
        )
        
        if result:
            return {
                "status": "success",
                "message": "테스트 알림이 성공적으로 전송되었습니다."
            }
        else:
            return {
                "status": "warning",
                "message": "테스트 알림 전송에 실패했습니다. 등록된 디바이스 토큰이 없을 수 있습니다."
            }
    
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"테스트 알림 전송 중 오류 발생: {str(e)}"
        ) 