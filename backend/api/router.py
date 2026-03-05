from fastapi import APIRouter
from api.routes import speedtest, connectivity

api_router = APIRouter(prefix="/network")
"""Top-level API router grouping all network health monitoring endpoints."""

api_router.include_router(speedtest.router)
api_router.include_router(connectivity.router)