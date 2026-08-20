"""Infrastructure layer: technical concerns.

Holds the SQLAlchemy ORM models, the engine/session factory, and the
concrete `AccountRepository` implementation that satisfies the port
declared in `banking.domain.repositories`. This is the only layer that
is allowed to know what a database is.
"""
