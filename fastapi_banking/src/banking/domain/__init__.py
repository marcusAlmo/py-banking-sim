"""Domain layer: pure business objects and the ports they depend on.

This package must NOT import from FastAPI, SQLAlchemy, Pydantic, or any
other outer-layer module. Everything here is framework-agnostic and could
be reused behind a CLI, a gRPC service, or a job runner unchanged.
"""
