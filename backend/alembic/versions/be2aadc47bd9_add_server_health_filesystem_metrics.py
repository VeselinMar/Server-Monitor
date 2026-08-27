"""add server health filesystem metrics

Revision ID: be2aadc47bd9
Revises: <generated>
Create Date: 2026-08-27 20:20:54.099752

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'be2aadc47bd9'
down_revision: Union[str, Sequence[str], None] = '<generated>'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "server_health_filesystems",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column(
            "server_health_id",
            sa.Integer(),
            nullable=False,
        ),
        sa.Column(
            "mountpoint",
            sa.String(length=512),
            nullable=False,
        ),
        sa.Column(
            "total_bytes",
            sa.BigInteger(),
            nullable=True,
        ),
        sa.Column(
            "used_bytes",
            sa.BigInteger(),
            nullable=True,
        ),
        sa.Column(
            "available_bytes",
            sa.BigInteger(),
            nullable=True,
        ),
        sa.Column(
            "percent",
            sa.Float(),
            nullable=True,
        ),
        sa.Column(
            "inode_total",
            sa.BigInteger(),
            nullable=True,
        ),
        sa.Column(
            "inode_used",
            sa.BigInteger(),
            nullable=True,
        ),
        sa.Column(
            "inode_free",
            sa.BigInteger(),
            nullable=True,
        ),
        sa.Column(
            "inode_percent",
            sa.Float(),
            nullable=True,
        ),
        sa.ForeignKeyConstraint(
            ["server_health_id"],
            ["server_health.id"],
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_server_health_filesystems_id"),
        "server_health_filesystems",
        ["id"],
        unique=False,
    )

    op.create_index(
        op.f("ix_server_health_filesystems_server_health_id"),
        "server_health_filesystems",
        ["server_health_id"],
        unique=False,
    )




def downgrade() -> None:
    """Downgrade schema."""
    pass
