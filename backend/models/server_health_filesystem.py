from sqlalchemy import (
    Column,
    Integer,
    Float,
    DateTime,
    BigInteger,
    String,
    ForeignKey,
)

from core.database import Base


class ServerHealthFilesystem(Base):
    """
    Filesystem capacity and inode usage for a server-health sample.
    """

    __tablename__ = "server_health_filesystems"

    id = Column(Integer, primary_key=True, index=True)

    server_health_id = Column(
        Integer,
        ForeignKey("server_health.id"),
        nullable=False,
        index=True,
    )

    mountpoint = Column(
        String(512),
        nullable=False,
    )

    total_bytes = Column(
        BigInteger,
        nullable=True,
    )

    used_bytes = Column(
        BigInteger,
        nullable=True,
    )

    available_bytes = Column(
        BigInteger,
        nullable=True,
    )

    percent = Column(
        Float,
        nullable=True,
    )

    inode_total = Column(
        BigInteger,
        nullable=True,
    )

    inode_used = Column(
        BigInteger,
        nullable=True,
    )

    inode_free = Column(
        BigInteger,
        nullable=True,
    )

    inode_percent = Column(
        Float,
        nullable=True,
    )
