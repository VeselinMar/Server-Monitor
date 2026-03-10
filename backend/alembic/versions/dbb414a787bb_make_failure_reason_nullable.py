"""make failure_reason nullable

Revision ID: dbb414a787bb
Revises: a2ebc21329eb
Create Date: 2026-03-10 12:22:03.391015

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'dbb414a787bb'
down_revision: Union[str, Sequence[str], None] = 'a2ebc21329eb'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # SQLite does not support ALTER COLUMN, so we recreate the table.
    op.execute("""
        CREATE TABLE speedtest_failures_new (
            id INTEGER PRIMARY KEY,
            timestamp DATETIME NOT NULL,
            status VARCHAR NOT NULL,
            server_name VARCHAR,
            server_id INTEGER,
            distance FLOAT,
            failure_reason VARCHAR
        )
    """)
    op.execute("""
        INSERT INTO speedtest_failures_new
        SELECT id, timestamp, status, server_name, server_id, distance, failure_reason
        FROM speedtest_failures
    """)
    op.execute("DROP TABLE speedtest_failures")
    op.execute("ALTER TABLE speedtest_failures_new RENAME TO speedtest_failures")

    # Fix settings index uniqueness
    op.drop_index(op.f('ix_settings_key'), table_name='settings')
    op.create_index(op.f('ix_settings_key'), 'settings', ['key'], unique=True)


def downgrade() -> None:
    op.execute("""
        CREATE TABLE speedtest_failures_new (
            id INTEGER PRIMARY KEY,
            timestamp DATETIME NOT NULL,
            status VARCHAR NOT NULL,
            server_name VARCHAR,
            server_id INTEGER,
            distance FLOAT,
            failure_reason VARCHAR NOT NULL
        )
    """)
    op.execute("""
        INSERT INTO speedtest_failures_new
        SELECT id, timestamp, status, server_name, server_id, distance, failure_reason
        FROM speedtest_failures
    """)
    op.execute("DROP TABLE speedtest_failures")
    op.execute("ALTER TABLE speedtest_failures_new RENAME TO speedtest_failures")

    op.drop_index(op.f('ix_settings_key'), table_name='settings')
    op.create_index(op.f('ix_settings_key'), 'settings', ['key'], unique=False)