import os

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./monitoring.db")
"""
Database connection URL, configurable via the DATABASE_URL environment variable.
Defaults to a local SQLite file (monitoring.db) if the variable is not set.
"""