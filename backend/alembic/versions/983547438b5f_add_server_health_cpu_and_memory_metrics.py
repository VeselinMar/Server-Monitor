"""add server health cpu and memory metrics

Revision ID: <generated>
Revises: 9dd2a7aebe1e
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "<generated>"
down_revision: Union[str, Sequence[str], None] = "9dd2a7aebe1e"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "server_health",
        sa.Column(
            "cpu_per_core_percent",
            sa.JSON(),
            nullable=True,
        ),
    )

    op.add_column(
        "server_health",
        sa.Column(
            "cpu_frequency_mhz",
            sa.Float(),
            nullable=True,
        ),
    )

    op.add_column(
        "server_health",
        sa.Column(
            "memory_used_bytes",
            sa.BigInteger(),
            nullable=True,
        ),
    )

    op.add_column(
        "server_health",
        sa.Column(
            "memory_cached_bytes",
            sa.BigInteger(),
            nullable=True,
        ),
    )

    op.add_column(
        "server_health",
        sa.Column(
            "swap_sin_bytes",
            sa.BigInteger(),
            nullable=True,
        ),
    )

    op.add_column(
        "server_health",
        sa.Column(
            "swap_sout_bytes",
            sa.BigInteger(),
            nullable=True,
        ),
    )


def downgrade() -> None:
    op.drop_column(
        "server_health",
        "swap_sout_bytes",
    )

    op.drop_column(
        "server_health",
        "swap_sin_bytes",
    )

    op.drop_column(
        "server_health",
        "memory_cached_bytes",
    )

    op.drop_column(
        "server_health",
        "memory_used_bytes",
    )

    op.drop_column(
        "server_health",
        "cpu_frequency_mhz",
    )

    op.drop_column(
        "server_health",
        "cpu_per_core_percent",
    )
