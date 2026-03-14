from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.api.dependencies import get_protected_db
from src.config.settings import settings
from src.schemas.api import DeviceTokenCreate, DeviceTokenResponse
from src.services.notification_service import NotificationService

router = APIRouter(prefix="/device-tokens", tags=["device-tokens"])
notification_service = NotificationService(settings)


@router.post("", response_model=DeviceTokenResponse, status_code=status.HTTP_201_CREATED)
async def register_device_token(payload: DeviceTokenCreate, db: AsyncSession = Depends(get_protected_db)):
    item = await notification_service.register_device_token(db, payload.token, payload.platform)
    return item


@router.delete("/{token}", status_code=status.HTTP_204_NO_CONTENT)
async def deactivate_device_token(token: str, db: AsyncSession = Depends(get_protected_db)):
    success = await notification_service.deactivate_device_token(db, token)
    if not success:
        raise HTTPException(status_code=404, detail="Device token not found")
