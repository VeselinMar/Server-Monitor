from sqlalchemy import Column, Integer, Float, DateTime, BigInteger

from core.database import Base


class ServerHealth(Base):
    """
    ORM model representing a point-in-time snapshot of server health.

    Maps to the 'server_health' table.
    """

    __tablename__ = "server_health"

    id = Column(Integer, primary_key=True, index=True)
    timestamp = Column(DateTime(timezone=True), nullable=False, index=True)

    # CPU
    cpu_percent = Column(Float, nullable=True)
    load_1 = Column(Float, nullable=True)
    load_5 = Column(Float, nullable=True)
    load_15 = Column(Float, nullable=True)

    # Memory
    memory_total_bytes = Column(BigInteger, nullable=True)
    memory_available_bytes = Column(BigInteger, nullable=True)
    swap_total_bytes = Column(BigInteger, nullable=True)
    swap_used_bytes = Column(BigInteger, nullable=True)

    # Temperature
    cpu_package_temp_c = Column(Float, nullable=True)
    cpu_core0_temp_c = Column(Float, nullable=True)
    cpu_core1_temp_c = Column(Float, nullable=True)

    # Disk I/O
    disk_read_bytes = Column(BigInteger, nullable=True)
    disk_write_bytes = Column(BigInteger, nullable=True)
    disk_read_iops = Column(Float, nullable=True)
    disk_write_iops = Column(Float, nullable=True)
    disk_util_percent = Column(Float, nullable=True)

    # Network
    network_rx_bytes = Column(BigInteger, nullable=True)
    network_tx_bytes = Column(BigInteger, nullable=True)
    network_rx_errors = Column(BigInteger, nullable=True)
    network_tx_errors = Column(BigInteger, nullable=True)
    network_rx_drops = Column(BigInteger, nullable=True)
    network_tx_drops = Column(BigInteger, nullable=True)

    # System
    uptime_seconds = Column(Float, nullable=True)
