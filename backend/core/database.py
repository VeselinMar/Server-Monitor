from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

from core.config import DATABASE_URL

engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False},
    # check_same_thread is SQLite-specific — required because FastAPI may access
    # the same connection from multiple threads across the request lifecycle.
)
"""SQLAlchemy engine bound to the configured database URL."""

SessionLocal = sessionmaker(bind=engine)
"""Session factory — call SessionLocal() to obtain a new database session."""

Base = declarative_base()
"""Declarative base class for all ORM models."""