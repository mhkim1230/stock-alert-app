from fastapi import APIRouter

router = APIRouter(prefix="/auth", tags=["deprecated"])


@router.get("/status")
async def auth_removed() -> dict:
    return {
        "status": "removed",
        "message": "User signup/login has been removed in single-user admin-key mode.",
    }
