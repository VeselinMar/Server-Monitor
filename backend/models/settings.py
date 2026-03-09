from sqlalchemy import Column, Integer, String, Float
from core.database import Base


class Setting(Base):
    """
    ORM model for persistent application settings stored as typed key-value pairs.

    Maps to the 'settings' table. Settings are upserted by key — there is
    at most one row per key at any time.
    """

    __tablename__ = "settings"

    id    = Column(
        Integer, 
        primary_key=True, 
        index=True
        )
    key   = Column(
        String, 
        unique=True, 
        index=True, 
        nullable=False
        )
    value = Column(
        String, 
        nullable=True
        )