from fastapi import APIRouter

router = APIRouter(prefix="/v1/jobs", tags=["jobs"])


@router.get("/", summary="Jobs root placeholder")
async def jobs_root():
    return {"detail": "Not Implemented"}
