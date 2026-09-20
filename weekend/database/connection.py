"""
Database Connection & Session Factory
Autonomous Multi-Agent Placement Readiness Platform
"""

import os
import sys
from typing import Generator
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, Session

from database.models import Base
import config

PRIMARY_DB_URL = config.DATABASE_URL
FALLBACK_DB_URL = "duckdb:///placement_platform.duckdb"

def build_engine(db_url: str):
    """Builds SQLAlchemy engine with connection pooling and timeouts."""
    if db_url.startswith("postgresql"):
        return create_engine(
            db_url,
            pool_size=10,
            max_overflow=20,
            pool_pre_ping=True,
            pool_recycle=1800,
            connect_args={"connect_timeout": 2}
        )
    elif db_url.startswith("duckdb"):
        return create_engine(db_url)
    else:
        return create_engine(db_url)


# Determine active engine
try:
    _test_engine = build_engine(PRIMARY_DB_URL)
    with _test_engine.connect() as conn:
        conn.execute(text("SELECT 1;"))
    engine = _test_engine
    ACTIVE_DB_URL = PRIMARY_DB_URL
    DB_TYPE = "PostgreSQL (Production Active)"
except Exception as err:
    # Gracefully switch to embedded analytical DuckDB when PostgreSQL is offline
    print(f"[DB Notice] PostgreSQL offline or unreachable ({PRIMARY_DB_URL}).")
    print(f"[DB Engine] Activated analytical DuckDB database engine: {FALLBACK_DB_URL}")
    engine = build_engine(FALLBACK_DB_URL)
    ACTIVE_DB_URL = FALLBACK_DB_URL
    DB_TYPE = "DuckDB (Relational & Analytical Active)"

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def init_db() -> None:
    """Creates all database tables according to the ORM schema."""
    Base.metadata.create_all(bind=engine)

def get_db() -> Generator[Session, None, None]:
    """Context-managed database session dependency."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def get_db_status() -> dict:
    """Returns database telemetry and health status."""
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1;"))
            healthy = True
    except Exception:
        healthy = False

    return {
        "engine": DB_TYPE,
        "url": ACTIVE_DB_URL,
        "is_healthy": healthy
    }
