from app.routes.agents import router as agents_router
from app.routes.auth import router as auth_router
from app.routes.bids import router as bids_router
from app.routes.jobs import router as jobs_router
from app.routes.webhooks import router as webhooks_router

__all__ = [
    "agents_router",
    "auth_router",
    "bids_router",
    "jobs_router",
    "webhooks_router",
]
