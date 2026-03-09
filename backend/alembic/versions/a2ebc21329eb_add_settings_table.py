"""add settings table

Revision ID: a2ebc21329eb
Revises: 8a17f25d8db4
Create Date: 2026-03-09 11:59:48.619414

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = 'a2ebc21329eb'
down_revision: Union[str, Sequence[str], None] = '8a17f25d8db4'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'settings',
        sa.Column('id',    sa.Integer(), nullable=False),
        sa.Column('key',   sa.String(),  nullable=False),
        sa.Column('value', sa.String(),  nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('key'),
    )
    op.create_index('ix_settings_id',  'settings', ['id'])
    op.create_index('ix_settings_key', 'settings', ['key'])


def downgrade() -> None:
    op.drop_index('ix_settings_key', table_name='settings')
    op.drop_index('ix_settings_id',  table_name='settings')
    op.drop_table('settings')