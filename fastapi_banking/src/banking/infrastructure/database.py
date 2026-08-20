"""
Database engine + session factory.

Centralizing engine construction here means the rest of the app takes a
`Session` factory and never knows the connection string. The FastAPI
app factory (`interfaces/api/app.py`) calls `make_session_factory` once
at startup and injects the resulting factory into the repository.

We use SQLite by default. The URL is overridable so tests can point at
a temporary file (or `:memory:`) without touching production code.
"""

import os
from typing import Callable

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

DEFAULT_URL = os.environ.get("BANKING_DB_URL", "sqlite:///./banking.db")


def make_session_factory(url: str = DEFAULT_URL) -> Callable[[], Session]:
    """
    Build a session factory bound to `url`.

    `check_same_thread=False` is required for SQLite when used behind
    FastAPI's thread-pool — otherwise SQLAlchemy refuses to share the
    connection across request threads.
    """
    connect_args = {"check_same_thread": False} if url.startswith("sqlite") else {}
    engine = create_engine(url, connect_args=connect_args, future=True)
    return sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)
