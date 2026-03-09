"""add daily_summaries table

Revision ID: 8a17f25d8db4
Revises: 022c273ceb3d
Create Date: 2026-03-06 14:16:00.073378

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = '8a17f25d8db4'
down_revision: Union[str, Sequence[str], None] = '022c273ceb3d'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'daily_summaries',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('period_date', sa.Date(), nullable=False),
        sa.Column('avg_download_mbps', sa.Float(), nullable=True),
        sa.Column('min_download_mbps', sa.Float(), nullable=True),
        sa.Column('avg_upload_mbps', sa.Float(), nullable=True),
        sa.Column('min_upload_mbps', sa.Float(), nullable=True),
        sa.Column('avg_ping', sa.Float(), nullable=True),
        sa.Column('total_tests', sa.Integer(), nullable=True),
        sa.Column('successful_tests', sa.Integer(), nullable=True),
        sa.Column('failed_tests', sa.Integer(), nullable=True),
        sa.Column('degraded_count', sa.Integer(), nullable=True),
        sa.Column('degraded_total_minutes', sa.Integer(), nullable=True),
        sa.Column('total_checks', sa.Integer(), nullable=True),
        sa.Column('online_checks', sa.Integer(), nullable=True),
        sa.Column('offline_checks', sa.Integer(), nullable=True),
        sa.Column('outage_count', sa.Integer(), nullable=True),
        sa.Column('outage_total_minutes', sa.Integer(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('period_date'),
    )
    op.create_index('ix_daily_summaries_id', 'daily_summaries', ['id'])
    op.create_index('ix_daily_summaries_period_date', 'daily_summaries', ['period_date'])


def downgrade() -> None:
    op.drop_index('ix_daily_summaries_period_date', table_name='daily_summaries')
    op.drop_index('ix_daily_summaries_id', table_name='daily_summaries')
    op.drop_table('daily_summaries')