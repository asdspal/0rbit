from fastapi import APIRouter

router = APIRouter(tags=["webhooks"])


@router.get("/webhooks", summary="Webhooks root placeholder")
async def webhooks_root():
    return {"detail": "webhooks placeholder"}
