from fastapi import APIRouter

router = APIRouter(prefix="/v1/auth", tags=["auth"])


@router.get("/nonce", summary="Auth nonce placeholder")
async def auth_nonce():
    return {"detail": "Not Implemented"}
