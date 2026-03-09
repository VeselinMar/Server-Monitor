from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from core.database import SessionLocal
from repositories import settings_repository as repo

router = APIRouter(prefix="/settings", tags=["Settings"])


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@router.get(
    "",
    summary="Get all application settings",
    response_description="Flat dict of all settings with defaults filled in",
)
def get_settings(db: Session = Depends(get_db)):
    """
    Return all settings as a flat key-value dict.

    Missing keys are filled in from defaults so the response always
    contains the full set of expected keys.
    """
    return repo.get_all(db)


@router.put(
    "",
    summary="Save application settings",
    response_description="Full settings dict after saving",
)
def save_settings(data: dict, db: Session = Depends(get_db)):
    """
    Upsert the provided settings into the database.

    Accepts a partial or full dict — only provided keys are updated.
    Returns the complete settings dict after saving.
    """
    return repo.upsert_all(db, data)