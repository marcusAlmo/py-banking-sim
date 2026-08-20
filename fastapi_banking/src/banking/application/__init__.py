"""Application layer: use cases that orchestrate the domain.

Each service class corresponds to one user-facing operation (deposit,
withdraw, check balance, ...). Services depend on the `domain` package
and on the `AccountRepository` *port* (a Protocol), never on a concrete
implementation. The composition root (see `interfaces/api/app.py`) wires
a real repository in at startup.
"""
