import logging
from datetime import datetime, timezone
from typing import Any, Dict, Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.models.database import DeviceToken, NotificationLog

try:
    from apns2.client import APNsClient
    from apns2.credentials import TokenCredentials
    from apns2.payload import Payload, PayloadAlert
except ImportError:  # pragma: no cover
    APNsClient = None
    TokenCredentials = None
    Payload = None
    PayloadAlert = None


class NotificationService:
    def __init__(self, settings) -> None:
        self.settings = settings
        self.logger = logging.getLogger(__name__)
        self._client = None

    def _get_client(self):
        if self._client is not None:
            return self._client
        if not (
            APNsClient
            and TokenCredentials
            and Payload
            and PayloadAlert
            and self.settings.apns_private_key
            and self.settings.apns_key_id
            and self.settings.apns_team_id
        ):
            return None

        key_path = "/tmp/apns_auth_key.p8"
        with open(key_path, "w", encoding="utf-8") as handle:
            handle.write(self.settings.apns_private_key)

        credentials = TokenCredentials(
            auth_key_path=key_path,
            auth_key_id=self.settings.apns_key_id,
            team_id=self.settings.apns_team_id,
        )
        self._client = APNsClient(credentials=credentials, use_sandbox=self.settings.apns_use_sandbox)
        return self._client

    async def register_device_token(self, db: AsyncSession, token: str, platform: str) -> DeviceToken:
        stmt = select(DeviceToken).where(DeviceToken.token == token)
        existing = (await db.execute(stmt)).scalar_one_or_none()
        if existing:
            existing.platform = platform
            existing.is_active = True
            existing.last_used_at = datetime.now(timezone.utc)
            await db.commit()
            await db.refresh(existing)
            return existing

        item = DeviceToken(token=token, platform=platform, is_active=True)
        db.add(item)
        await db.commit()
        await db.refresh(item)
        return item

    async def deactivate_device_token(self, db: AsyncSession, token: str) -> bool:
        stmt = select(DeviceToken).where(DeviceToken.token == token)
        item = (await db.execute(stmt)).scalar_one_or_none()
        if not item:
            return False
        item.is_active = False
        item.last_used_at = datetime.now(timezone.utc)
        await db.commit()
        return True

    async def create_notification_log(
        self,
        db: AsyncSession,
        alert_type: str,
        message: str,
        status: str,
        alert_id: Optional[str] = None,
        extra_data: Optional[Dict[str, Any]] = None,
    ) -> NotificationLog:
        log = NotificationLog(
            alert_id=alert_id,
            alert_type=alert_type,
            message=message,
            status=status,
            extra_data=extra_data or {},
        )
        db.add(log)
        await db.commit()
        await db.refresh(log)
        return log

    async def send_push_to_all(
        self,
        db: AsyncSession,
        title: str,
        body: str,
        alert_type: str,
        alert_id: Optional[str] = None,
        extra_data: Optional[Dict[str, Any]] = None,
    ) -> int:
        stmt = select(DeviceToken).where(DeviceToken.is_active.is_(True))
        tokens = list((await db.execute(stmt)).scalars().all())
        if not tokens:
            await self.create_notification_log(
                db,
                alert_type=alert_type,
                message=body,
                status="skipped_no_tokens",
                alert_id=alert_id,
                extra_data=extra_data,
            )
            return 0

        sent = 0
        client = self._get_client()
        for token in tokens:
            try:
                if client and Payload and PayloadAlert:
                    payload = Payload(
                        alert=PayloadAlert(title=title, body=body),
                        sound="default",
                        custom=extra_data or {},
                    )
                    client.send_notification(token.token, payload, topic=self.settings.apns_bundle_id)
                token.last_used_at = datetime.now(timezone.utc)
                sent += 1
            except Exception as exc:  # pragma: no cover
                self.logger.warning("APNs send failed for token %s: %s", token.token[:8], exc)
        await db.commit()
        await self.create_notification_log(
            db,
            alert_type=alert_type,
            message=body,
            status="sent" if sent else "failed",
            alert_id=alert_id,
            extra_data=extra_data,
        )
        return sent
