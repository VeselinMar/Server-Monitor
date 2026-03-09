from sqlalchemy.orm import Session
from models.settings import Setting

# ── Default values ────────────────────────────────────────────────────────────
DEFAULTS = {
    # Subscriber / report details
    "subscriber_name":           "Your Full Name",
    "subscriber_address":        "Your Street Address, Vienna, Austria",
    "subscriber_account_number": "DREI-XXXXXXXXX",
    "subscriber_email":          "your.email@example.com",
    "subscriber_phone":          "+43 XXX XXXXXXX",
    "subscriber_plan":           "MyLife FIX Data 150",
    "subscriber_provider":       "Drei Austria GmbH",

    # Service thresholds
    "contracted_download_mbps":  "150.0",
    "contracted_upload_mbps":    "0.0",
    "download_degraded_mbps":    "75.0",
    "download_critical_mbps":    "30.0",
    "upload_degraded_mbps":      "5.0",
    "upload_critical_mbps":      "2.0",
}


def get_all(db: Session) -> dict:
    """
    Return all settings as a flat dict, falling back to defaults for any
    key not yet stored in the database.
    """
    rows = db.query(Setting).all()
    stored = {r.key: r.value for r in rows}
    return {**DEFAULTS, **stored}


def get(db: Session, key: str) -> str | None:
    """Return a single setting value by key, or its default if not set."""
    row = db.query(Setting).filter(Setting.key == key).first()
    if row:
        return row.value
    return DEFAULTS.get(key)


def upsert_all(db: Session, data: dict) -> dict:
    """
    Upsert a dict of key-value pairs into the settings table.

    Inserts new rows for unknown keys and updates existing ones.
    Returns the full settings dict after saving.
    """
    for key, value in data.items():
        row = db.query(Setting).filter(Setting.key == key).first()
        if row:
            row.value = str(value)
        else:
            db.add(Setting(key=key, value=str(value)))
    db.commit()
    return get_all(db)