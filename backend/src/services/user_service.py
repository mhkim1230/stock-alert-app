import os
import uuid
from typing import Optional, Dict, Any
from fastapi import UploadFile

from src.models.database import User, CurrencyAlert, StockAlert, NotificationLog

class UserService:
    """사용자 관련 서비스 클래스"""
    
    async def update_user_profile(
        self, 
        user_id: uuid.UUID, 
        username: Optional[str] = None, 
        email: Optional[str] = None
    ) -> User:
        """
        사용자 프로필 업데이트
        
        :param user_id: 업데이트할 사용자 ID
        :param username: 새 사용자명 (선택)
        :param email: 새 이메일 주소 (선택)
        :return: 업데이트된 사용자 객체
        """
        try:
            user = User.get_by_id(user_id)
            
            # 사용자명 업데이트
            if username:
                # 사용자명 중복 확인
                existing_user = User.select().where(User.username == username).first()
                if existing_user and existing_user.id != user_id:
                    raise ValueError("이미 사용 중인 사용자명입니다.")
                user.username = username
            
            # 이메일 업데이트
            if email:
                # 이메일 중복 확인
                existing_user = User.select().where(User.email == email).first()
                if existing_user and existing_user.id != user_id:
                    raise ValueError("이미 사용 중인 이메일 주소입니다.")
                user.email = email
            
            user.save()
            return user
        
        except User.DoesNotExist:
            raise ValueError("사용자를 찾을 수 없습니다.")
    
    async def upload_profile_image(
        self, 
        user_id: uuid.UUID, 
        file: UploadFile
    ) -> str:
        """
        프로필 이미지 업로드
        
        :param user_id: 사용자 ID
        :param file: 업로드된 이미지 파일
        :return: 프로필 이미지 URL
        """
        try:
            # 사용자 확인
            user = User.get_by_id(user_id)
            
            # 이미지 저장 디렉토리 생성
            upload_dir = os.path.join('uploads', 'profile_images')
            os.makedirs(upload_dir, exist_ok=True)
            
            # 고유한 파일명 생성
            file_extension = file.filename.split('.')[-1]
            filename = f"{user_id}.{file_extension}"
            file_path = os.path.join(upload_dir, filename)
            
            # 파일 저장
            with open(file_path, 'wb') as buffer:
                buffer.write(await file.read())
            
            # 프로필 이미지 URL 생성 (실제 배포 시 CDN 등으로 대체)
            profile_image_url = f"/uploads/profile_images/{filename}"
            
            # 사용자 프로필 이미지 URL 업데이트
            user.profile_image_url = profile_image_url
            user.save()
            
            return profile_image_url
        
        except User.DoesNotExist:
            raise ValueError("사용자를 찾을 수 없습니다.")
        except Exception as e:
            raise ValueError(f"프로필 이미지 업로드 중 오류 발생: {str(e)}")
    
    async def get_user_dashboard_stats(
        self, 
        user_id: uuid.UUID
    ) -> Dict[str, Any]:
        """
        사용자 대시보드 통계 조회
        
        :param user_id: 사용자 ID
        :return: 대시보드 통계 정보
        """
        try:
            # 사용자 확인
            user = User.get_by_id(user_id)
            
            # 통계 계산
            currency_alerts_count = CurrencyAlert.select().where(
                CurrencyAlert.user == user, 
                CurrencyAlert.is_active == True
            ).count()
            
            stock_alerts_count = StockAlert.select().where(
                StockAlert.user == user, 
                StockAlert.is_active == True
            ).count()
            
            unread_notifications_count = NotificationLog.select().where(
                NotificationLog.user == user, 
                NotificationLog.is_read == False
            ).count()
            
            return {
                "total_currency_alerts": currency_alerts_count,
                "total_stock_alerts": stock_alerts_count,
                "unread_notifications": unread_notifications_count
            }
        
        except User.DoesNotExist:
            raise ValueError("사용자를 찾을 수 없습니다.") 