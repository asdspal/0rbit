from fastapi import APIRouter

router = APIRouter(tags=["jobs"])


@router.get("/jobs", summary="Jobs root placeholder")
async def jobs_root():
    return {"detail": "jobs placeholder"}
