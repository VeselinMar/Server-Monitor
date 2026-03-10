from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from api.router import api_router

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

app.include_router(api_router)

@app.get(
    "/",
    response_description="Confirmation that the API is running",
    )
def read_root():
    """Return a simple status message confirming the API is reachable."""
    return {"status": "API running"}

app.include_router(api_router)