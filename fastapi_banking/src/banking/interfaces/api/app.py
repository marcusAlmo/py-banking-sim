"""
FastAPI application factory + lifespan.

This is the *composition root*: the one place where concrete
implementations are wired together. Everything else in the codebase
depends on abstractions (Protocols, base classes); only `app.py`
knows that the repository is SQLAlchemy-backed and that the DB is
SQLite.

Lifespan:
  1. Build the session factory from the configured DB URL.
  2. Create tables if missing.
  3. Seed demo accounts if the table is empty.
  4. Construct the repository and stash it on `app.state` so routes
     can read it back without each route having to know how to build
     one.
"""

from contextlib import asynccontextmanager

from fastapi import FastAPI

from ...infrastructure.account_repository import (
    SqlAlchemyAccountRepository,
    create_all_tables,
)
from ...infrastructure.database import DEFAULT_URL, make_session_factory
from ...infrastructure.seed import seed_if_empty
from .error_handlers import register_error_handlers
from .routes import router as accounts_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup: build repo, create tables, seed. Shutdown: nothing to do."""
    url = app.state.db_url
    session_factory = make_session_factory(url)
    create_all_tables(session_factory)
    seed_if_empty(session_factory)
    app.state.session_factory = session_factory
    app.state.repository = SqlAlchemyAccountRepository(session_factory)
    yield
    # No explicit close needed: SQLite file handles are released when
    # the engine is garbage-collected.


def create_app(db_url: str = DEFAULT_URL) -> FastAPI:
    """Build a configured FastAPI app. Override `db_url` for tests."""
    app = FastAPI(
        title="fastapi-banking",
        description="DDD-layered FastAPI rewrite of py-banking-sim.",
        version="0.1.0",
        lifespan=lifespan,
    )
    app.state.db_url = db_url
    register_error_handlers(app)
    app.include_router(accounts_router)

    @app.get("/health", tags=["meta"])
    def health() -> dict[str, str]:
        """Liveness probe."""
        return {"status": "ok"}

    return app


# Module-level instance so `uvicorn banking.interfaces.api.app:app` works.
app = create_app()
