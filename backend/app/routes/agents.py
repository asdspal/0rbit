from fastapi import APIRouter

router = APIRouter(prefix="/v1/agents", tags=["agents"])


@router.get("/", summary="Agents root placeholder")
async def agents_root():
    return {"detail": "Not Implemented"}
