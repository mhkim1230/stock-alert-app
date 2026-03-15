from fastapi import APIRouter, Depends, HTTPException, Response, status

from src.api.dependencies import require_session
from src.config.settings import settings
from src.core.security import create_session_token, verify_admin_password
from src.schemas.api import SessionLoginRequest, SessionStatusResponse

router = APIRouter(prefix="/session", tags=["session"])


@router.post("/login", response_model=SessionStatusResponse)
async def login(payload: SessionLoginRequest, response: Response):
    if not verify_admin_password(payload.password):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid password")

    response.set_cookie(
        key=settings.session_cookie_name,
        value=create_session_token(),
        max_age=settings.session_max_age_days * 24 * 60 * 60,
        httponly=True,
        secure=not settings.debug,
        samesite="lax",
        path="/",
    )
    return {"authenticated": True, "mode": "session"}


@router.post("/logout", response_model=SessionStatusResponse)
async def logout(response: Response):
    response.delete_cookie(key=settings.session_cookie_name, path="/")
    return {"authenticated": False, "mode": "session"}


@router.get("/me", response_model=SessionStatusResponse)
async def me(_: None = Depends(require_session)):
    return {"authenticated": True, "mode": "session"}
