from sqlalchemy import (
    Column,
    Integer,
    Float,
    BigInteger,
    String,
    ForeignKey,
)

from core.database import Base


class ServerHealthSmartDevice(Base):
    """
    SMART health information for a physical storage device
    belonging to a server-health sample.
    """

    __tablename__ = "server_health_smart_devices"

    id = Column(
        Integer,
        primary_key=True,
        index=True,
    )

    server_health_id = Column(
        Integer,
        ForeignKey("server_health.id"),
        nullable=False,
        index=True,
    )

    device = Column(
        String(512),
        nullable=False,
    )

    model = Column(
        String(512),
        nullable=True,
    )

    temperature_c = Column(
        Float,
        nullable=True,
    )

    reallocated_sectors = Column(
        BigInteger,
        nullable=True,
    )

    pending_sectors = Column(
        BigInteger,
        nullable=True,
    )

    uncorrectable_sectors = Column(
        BigInteger,
        nullable=True,
    )

    power_on_hours = Column(
        BigInteger,
        nullable=True,
    )
