from datetime import date
from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse
import io
from sqlalchemy.orm import Session

from core.database import SessionLocal
from repositories.summary_repository import get_summaries
from repositories.speedtest_repository import get_incidents
from repositories import settings_repository as settings_repo
from services.report_service import generate_report

router = APIRouter(prefix="/report", tags=["Report"])


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@router.get(
    "/pdf",
    summary="Generate a PDF network health report",
    response_description="PDF file download",
)
def pdf_report(
    from_date: date,
    to_date: date,
    db: Session = Depends(get_db),
):
    """
    Generate and return a PDF report covering the given date range.

    Pulls daily summaries, incident records, and subscriber settings
    from the database, then formats them into a structured PDF suitable
    for ISP complaint submission.
    """
    summaries = get_summaries(db, from_date, to_date)
    incidents = get_incidents(db, from_date, to_date)
    settings  = settings_repo.get_all(db)

    incidents_serialized = [
        {**inc, "start": str(inc["start"]), "end": str(inc["end"])}
        for inc in incidents
    ]

    pdf_bytes = generate_report(
        from_date, to_date, summaries, incidents_serialized, settings
    )

    filename = f"network_report_{from_date}_{to_date}.pdf"
    return StreamingResponse(
        io.BytesIO(pdf_bytes),
        media_type="application/pdf",
        headers={"Content-Disposition": f"attachment; filename={filename}"},
    )