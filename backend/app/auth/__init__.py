from fastapi import APIRouter

router = APIRouter(tags=["auth"])


@router.get("/auth", summary="Auth root placeholder")
async def auth_root():
    return {"detail": "auth placeholder"}
