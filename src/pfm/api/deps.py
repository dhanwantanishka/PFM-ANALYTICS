"""Shared API dependency: database session and user extraction."""

from __future__ import annotations

from pfm.config import DB_PATH
from pfm.db import get_session
from sqlalchemy.orm import Session


def get_db() -> Session:
    """Yield a database session, closing it after the request."""
    session = get_session(DB_PATH)
    try:
        yield session
    finally:
        session.close()
