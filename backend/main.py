from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from core.database import engine, Base

from api.router import api_router

# Create all tables defined on Base metadata if they don't already exist.
# This runs on startup, so the database schema is always in sync with the models.
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Server Monitor",
    description="API for tracking network health over time via automated speed tests."
    )

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get(
    "/",
    response_description="Confirmation that the API is running",
    )
def read_root():
    """Return a simple status message confirming the API is reachable."""
    return {"status": "API running"}

app.include_router(api_router)