from fastapi import APIRouter
from api.routes import (
    speedtest,
    connectivity,
    summary,
    settings,
    report,
    status,
    server_health,
)


api_router = APIRouter()

network_router = APIRouter(prefix="/network")
"""API endpoints for network health monitoring."""

network_router.include_router(speedtest.router)
network_router.include_router(connectivity.router)
network_router.include_router(summary.router)
network_router.include_router(settings.router)
network_router.include_router(report.router)
network_router.include_router(status.router)


server_router = APIRouter(prefix="/server")
"""API endpoints for server/system monitoring."""

server_router.include_router(server_health.router)


api_router.include_router(network_router)
api_router.include_router(server_router)
