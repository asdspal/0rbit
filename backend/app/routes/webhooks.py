from fastapi import APIRouter

router = APIRouter(prefix="/v1/webhooks", tags=["webhooks"])


@router.get("/", summary="Webhooks root placeholder")
async def webhooks_root():
    return {"detail": "Not Implemented"}
