from typing import Optional

from fastapi import Cookie, Depends, Header, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.config.settings import settings
from src.core.security import decode_session_token
from src.models.database import get_db


async def require_admin_key(
    authorization: Optional[str] = Header(default=None),
    x_admin_key: Optional[str] = Header(default=None),
) -> None:
    bearer_token = None
    if authorization and authorization.lower().startswith("bearer "):
        bearer_token = authorization.split(" ", 1)[1].strip()

    supplied_key = x_admin_key or bearer_token
    if supplied_key != settings.admin_api_key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid admin credentials",
        )


async def require_session(
    session_cookie: Optional[str] = Cookie(default=None, alias=settings.session_cookie_name),
) -> None:
    if not session_cookie or not decode_session_token(session_cookie):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required",
        )


async def require_session_or_admin(
    authorization: Optional[str] = Header(default=None),
    x_admin_key: Optional[str] = Header(default=None),
    session_cookie: Optional[str] = Cookie(default=None, alias=settings.session_cookie_name),
) -> None:
    bearer_token = None
    if authorization and authorization.lower().startswith("bearer "):
        bearer_token = authorization.split(" ", 1)[1].strip()

    supplied_key = x_admin_key or bearer_token
    if supplied_key and supplied_key == settings.admin_api_key:
        return

    if session_cookie and decode_session_token(session_cookie):
        return

    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Authentication required",
    )


async def get_protected_db(
    _: None = Depends(require_session_or_admin),
    db: AsyncSession = Depends(get_db),
) -> AsyncSession:
    return db
