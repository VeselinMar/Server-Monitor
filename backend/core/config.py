import os

DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "sqlite:///./monitoring.db",
)
"""
Database connection URL, configurable via the DATABASE_URL environment variable.
Defaults to a local SQLite file (monitoring.db) if the variable is not set.
"""

SERVER_HEALTH_API_TOKEN = os.getenv(
    "SERVER_HEALTH_API_TOKEN",
)
"""
Bearer token used by the deployed server-health collector.

The token is intentionally optional at configuration level so the application
can still start in development/test environments. The POST endpoint itself
will require it.
"""
