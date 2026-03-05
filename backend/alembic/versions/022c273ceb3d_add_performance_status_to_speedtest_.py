"""add performance_status to speedtest_results

Revision ID: 022c273ceb3d
Revises: 
Create Date: 2026-03-05 15:11:11.601284
"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = '022c273ceb3d'
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """
    performance_status column was added manually via ALTER TABLE before
    Alembic was set up. Column already exists with correct type and all
    rows are backfilled — nothing to do here.
    """
    pass


def downgrade() -> None:
    """SQLite does not support DROP COLUMN in older versions — no-op."""
    pass