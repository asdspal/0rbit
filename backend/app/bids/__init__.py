from fastapi import APIRouter

router = APIRouter(tags=["bids"])


@router.get("/bids", summary="Bids root placeholder")
async def bids_root():
    return {"detail": "bids placeholder"}
