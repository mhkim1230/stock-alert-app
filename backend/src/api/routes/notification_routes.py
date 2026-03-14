from typing import List

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.api.dependencies import get_protected_db
from src.models.database import NotificationLog
from src.schemas.api import NotificationResponse

router = APIRouter(prefix="/notifications", tags=["notifications"])


@router.get("", response_model=List[NotificationResponse])
async def list_notifications(db: AsyncSession = Depends(get_protected_db), limit: int = 20):
    stmt = select(NotificationLog).order_by(NotificationLog.sent_at.desc()).limit(limit)
    return list((await db.execute(stmt)).scalars())


@router.patch("/{notification_id}/read", response_model=NotificationResponse)
async def mark_notification_read(notification_id: str, db: AsyncSession = Depends(get_protected_db)):
    notification = (
        await db.execute(select(NotificationLog).where(NotificationLog.id == notification_id))
    ).scalar_one_or_none()
    if not notification:
        raise HTTPException(status_code=404, detail="Notification not found")
    notification.is_read = True
    await db.commit()
    await db.refresh(notification)
    return notification


@router.get("/unread-count")
async def unread_count(db: AsyncSession = Depends(get_protected_db)):
    stmt = select(func.count(NotificationLog.id)).where(NotificationLog.is_read.is_(False))
    count = (await db.execute(stmt)).scalar_one()
    return {"unread_count": count}
