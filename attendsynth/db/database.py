"""Database configuration and session management for AttendSynth AI."""

import os
from typing import Generator
from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker, Session

# Database path in workspace root
DB_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "attendsynth.db"))
DATABASE_URL = f"sqlite:///{DB_PATH}"

# Create SQLite engine with WAL mode for high performance
engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False},
    pool_pre_ping=True,
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


def get_db() -> Generator[Session, None, None]:
    """FastAPI dependency yielding a database session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db():
    """Initializes tables and configures SQLite Pragmas."""
    from attendsynth.db import models  # noqa: F401
    Base.metadata.create_all(bind=engine)
    # Enable WAL mode for concurrent read/write performance
    with engine.connect() as conn:
        conn.exec_driver_sql("PRAGMA journal_mode=WAL;")
        conn.exec_driver_sql("PRAGMA synchronous=NORMAL;")


def get_db_stats_raw() -> dict:
    """Returns database location, existence, and size."""
    exists = os.path.exists(DB_PATH)
    size_bytes = os.path.getsize(DB_PATH) if exists else 0
    return {
        "engine": "SQLite",
        "path": DB_PATH,
        "exists": exists,
        "size_kb": round(size_bytes / 1024, 1),
        "size_mb": round(size_bytes / (1024 * 1024), 2),
    }

