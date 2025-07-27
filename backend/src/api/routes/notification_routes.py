from fastapi import APIRouter, Depends, HTTPException
from typing import List
from datetime import datetime

from src.services.auth_service import get_current_user
from src.services.notification_service import notification_service
from src.models.database import User, NotificationLog

router = APIRouter(prefix="/notifications", tags=["Notifications"])

@router.get("/")
async def get_notifications(
    current_user: User = Depends(get_current_user),
    limit: int = 20
):
    """사용자의 알림 목록 조회"""
    try:
        notifications = list(
            NotificationLog.select()
            .where(NotificationLog.user == current_user.id)
            .order_by(NotificationLog.created_at.desc())
            .limit(limit)
        )
        
        return {
            "status": "success",
            "data": [
                {
                    "id": notif.id,
                    "type": notif.type,
                    "message": notif.message,
                    "is_read": notif.is_read,
                    "created_at": notif.created_at,
                    "extra_data": notif.extra_data
                }
                for notif in notifications
            ],
            "count": len(notifications)
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"알림 조회 중 오류 발생: {str(e)}"
        )

@router.put("/{notification_id}/read")
async def mark_notification_read(
    notification_id: int,
    current_user: User = Depends(get_current_user)
):
    """알림을 읽음으로 표시"""
    try:
        notification = NotificationLog.select().where(
            (NotificationLog.id == notification_id) & 
            (NotificationLog.user == current_user.id)
        ).first()
        
        if not notification:
            raise HTTPException(
                status_code=404,
                detail="알림을 찾을 수 없습니다."
            )
        
        notification.is_read = True
        notification.save()
        
        return {
            "status": "success",
            "message": "알림이 읽음으로 표시되었습니다."
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"알림 업데이트 중 오류 발생: {str(e)}"
        )

@router.get("/unread-count")
async def get_unread_count(
    current_user: User = Depends(get_current_user)
):
    """읽지 않은 알림 개수 조회"""
    try:
        unread_count = NotificationLog.select().where(
            (NotificationLog.user == current_user.id) & 
            (NotificationLog.is_read == False)
        ).count()
        
        return {
            "status": "success",
            "unread_count": unread_count
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"읽지 않은 알림 개수 조회 중 오류 발생: {str(e)}"
        ) 