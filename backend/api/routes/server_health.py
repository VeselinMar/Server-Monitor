import os
from datetime import datetime

from fastapi import APIRouter, Depends, Header, HTTPException
from sqlalchemy.orm import Session

from core.database import SessionLocal
from models.server_health import ServerHealth
from schemas.server_health import (
    ServerHealthCreate,
    ServerHealthResponse,
)
from services import server_health_service


router = APIRouter(
    prefix="/health",
    tags=["server-health"],
)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def verify_health_token(
    authorization: str | None = Header(default=None),
):
    """
    Validate the bearer token used by the server-health collector.
    """
    expected_token = os.getenv("SERVER_HEALTH_API_TOKEN")

    if not expected_token:
        raise HTTPException(
            status_code=503,
            detail="Server health ingestion is not configured",
        )

    if authorization != f"Bearer {expected_token}":
        raise HTTPException(
            status_code=401,
            detail="Invalid or missing server health API token",
        )


@router.post(
    "",
    response_model=ServerHealthResponse,
    status_code=201,
    dependencies=[Depends(verify_health_token)],
)
def create_health(
    health: ServerHealthCreate,
    db: Session = Depends(get_db),
):
    server_health = ServerHealth(**health.model_dump())

    return server_health_service.create(
        db,
        server_health,
    )


@router.get(
    "/latest",
    response_model=ServerHealthResponse,
)
def get_latest(
    db: Session = Depends(get_db),
):
    health = server_health_service.get_latest(db)

    if health is None:
        raise HTTPException(
            status_code=404,
            detail="No server health data available",
        )

    return health


@router.get(
    "/history",
    response_model=list[ServerHealthResponse],
)
def get_history(
    from_dt: datetime,
    to_dt: datetime,
    db: Session = Depends(get_db),
):
    return server_health_service.get_history(
        db,
        from_dt,
        to_dt,
    )
