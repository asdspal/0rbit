from fastapi import FastAPI

from app.auth import router as auth_router
from app.agents import router as agents_router
from app.bids import router as bids_router
from app.jobs import router as jobs_router
from app.routes.agents import router as agents_v1_router
from app.routes.auth import router as auth_v1_router
from app.routes.bids import router as bids_v1_router
from app.routes.jobs import router as jobs_v1_router
from app.routes.health import router as health_router
from app.routes.webhooks import router as webhooks_v1_router
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
app.include_router(auth_v1_router)
app.include_router(agents_v1_router)
app.include_router(bids_v1_router)
app.include_router(jobs_v1_router)
app.include_router(health_router)
app.include_router(webhooks_router)
app.include_router(webhooks_v1_router)
