"""Database initialization and session management."""

from pathlib import Path

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from pfm.config import DB_PATH
from pfm.db.models import Base


def get_engine(db_path: Path | None = None):
    """Create a SQLAlchemy engine for the given SQLite path."""
    path = db_path or DB_PATH
    path.parent.mkdir(parents=True, exist_ok=True)
    return create_engine(f"sqlite:///{path}", echo=False)


def init_db(db_path: Path | None = None) -> None:
    """Create all tables if they do not exist."""
    engine = get_engine(db_path)
    Base.metadata.create_all(engine)


def get_session(db_path: Path | None = None) -> Session:
    """Return a new database session."""
    engine = get_engine(db_path)
    Base.metadata.create_all(engine)
    SessionLocal = sessionmaker(bind=engine)
    return SessionLocal()
