from fastapi import APIRouter

router = APIRouter(tags=["agents"])


@router.get("/agents", summary="Agents root placeholder")
async def agents_root():
    return {"detail": "agents placeholder"}
