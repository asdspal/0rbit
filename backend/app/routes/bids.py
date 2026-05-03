from fastapi import APIRouter

router = APIRouter(prefix="/v1/bids", tags=["bids"])


@router.get("/", summary="Bids root placeholder")
async def bids_root():
    return {"detail": "Not Implemented"}
