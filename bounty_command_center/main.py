from fastapi import FastAPI

from .database import create_db_and_tables
from .logging_setup import setup_logging
from .routers import auth, targets, evidence, reports, programs


# --- Lifespan Management ---
from contextlib import asynccontextmanager

@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Manages application startup and shutdown events.
    """
    setup_logging(log_to_file=True)
    create_db_and_tables()
    yield

# Create the main FastAPI app
app = FastAPI(
    title="Bounty Command Center API",
    description="API for managing bug bounty targets and evidence.",
    version="1.0.0",
    lifespan=lifespan,
)

# --- Routers ---
app.include_router(auth.router)
app.include_router(targets.router)
app.include_router(evidence.router)
app.include_router(reports.router)
app.include_router(programs.router)


import redis
from sqlmodel import Session, select
from fastapi import Depends, HTTPException

from .config import settings
from .database import get_session
from . import models

@app.get("/healthz", tags=["Health"])
def health_check():
    """Liveness probe: Checks if the application is running."""
    return {"status": "ok"}

@app.get("/readyz", tags=["Health"])
def readiness_check(db: Session = Depends(get_session)):
    """Readiness probe: Checks if the application can connect to dependencies."""
    try:
        # Check DB connection
        db.exec(select(1))

        # Check Redis connection
        redis_client = redis.from_url(settings.celery.broker_url)
        redis_client.ping()

        return {"status": "ok", "dependencies": {"database": "ok", "redis": "ok"}}

    except Exception as e:
        raise HTTPException(
            status_code=503,
            detail={
                "status": "unavailable",
                "error": str(e),
            },
        )

# A simple root endpoint to confirm the API is running
@app.get("/")
def read_root():
    return {"message": "Welcome to the Bounty Command Center API"}
