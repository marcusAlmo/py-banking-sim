"""
Shared pytest fixtures.

Two repositories are exposed:

  - `fake_repo`   : an in-memory dict implementation of the port, for
                    fast unit tests of the application layer.
  - `api_client`  : a FastAPI TestClient bound to a temp SQLite file,
                    for end-to-end API tests.

The temp DB file is created fresh per test via the `tmp_path` fixture,
so tests never see each other's data.
"""

from datetime import datetime
from typing import Iterable

import pytest
from fastapi.testclient import TestClient

from banking.application.dto import AuthRequest
from banking.domain.account import Account
from banking.domain.repositories import AccountRepository
from banking.domain.transaction import Transaction, TransactionType
from banking.interfaces.api.app import create_app


# --- In-memory repository for application-layer tests -----------------


class InMemoryAccountRepository:
    """
    Minimal in-memory implementation of the AccountRepository port.

    Useful for unit-testing application services without spinning up
    SQLAlchemy. Demonstrates that the application layer depends only
    on the *port*, not on any concrete implementation.
    """

    def __init__(self, accounts: Iterable[Account] = ()):
        self._accounts: dict[str, Account] = {a.number: a for a in accounts}
        self._txns: list[Transaction] = []

    def get_by_number(self, number: str) -> Account | None:
        return self._accounts.get(number)

    def add(self, account: Account) -> None:
        self._accounts[account.number] = account

    def save(self, account: Account) -> None:
        # In-memory: the Account object is already mutated in place,
        # so we just need to make sure it's registered.
        self._accounts[account.number] = account

    def append_transaction(self, transaction: Transaction) -> None:
        self._txns.append(transaction)

    def list_transactions(self, account_number: str) -> list[Transaction]:
        return [t for t in self._txns if t.account_number == account_number]


@pytest.fixture
def fake_repo() -> InMemoryAccountRepository:
    """A repository preloaded with the same demo accounts as the seed."""
    return InMemoryAccountRepository(
        [
            Account("1234567890", "John Doe", 1000.0, "1234"),
            Account("0987654321", "Jane Smith", 1500.0, "5678"),
            Account("1111222233", "Bob Johnson", 2000.0, "9012"),
        ]
    )


# --- TestClient for API tests -----------------------------------------


@pytest.fixture
def api_client(tmp_path) -> TestClient:
    """A TestClient against a fresh per-test SQLite file."""
    db_path = tmp_path / "test_banking.db"
    app = create_app(db_url=f"sqlite:///{db_path}")
    # TestClient triggers the lifespan startup/shutdown handlers.
    with TestClient(app) as client:
        yield client
