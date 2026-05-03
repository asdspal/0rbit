from fastapi import FastAPI

from app.auth import router as auth_router
from app.agents import router as agents_router
from app.bids import router as bids_router
from app.jobs import router as jobs_router
from app.routes.health import router as health_router
from app.webhooks import router as webhooks_router

app = FastAPI(
    title="0rbit Backend API",
    description="Scaffolded FastAPI backend for 0rbit (Section 4)",
    version="0.1.0",
)

app.include_router(auth_router)
app.include_router(agents_router)
app.include_router(bids_router)
app.include_router(jobs_router)
app.include_router(health_router)
app.include_router(webhooks_router)
