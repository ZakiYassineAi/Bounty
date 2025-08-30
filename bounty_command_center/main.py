from fastapi import FastAPI

from .database import create_db_and_tables
from .routers import auth, targets, evidence

# Create the main FastAPI app
app = FastAPI(
    title="Bounty Command Center API",
    description="API for managing bug bounty targets and evidence.",
    version="1.0.0",
)

# --- Event Handlers ---
@app.on_event("startup")
def on_startup():
    """
    This function runs when the application starts.
    It ensures that the database and tables are created.
    """
    create_db_and_tables()

# --- Routers ---
app.include_router(auth.router)
app.include_router(targets.router)
app.include_router(evidence.router)

# A simple root endpoint to confirm the API is running
@app.get("/")
def read_root():
    return {"message": "Welcome to the Bounty Command Center API"}
