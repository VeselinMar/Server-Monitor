from fastapi import APIRouter
from api.routes import speedtest, connectivity, summary, settings, report, status

api_router = APIRouter(prefix="/network")
"""Top-level API router grouping all network health monitoring endpoints."""

api_router.include_router(speedtest.router)
api_router.include_router(connectivity.router)
api_router.include_router(summary.router)
api_router.include_router(report.router)
api_router.include_router(settings.router)
api_router.include_router(status.router)