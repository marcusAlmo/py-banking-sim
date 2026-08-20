"""
Repository ports.

A "port" is an abstract interface the domain defines but does not
implement. The domain says "I need something that can fetch and save
Accounts and append Transactions"; the infrastructure layer provides a
concrete adapter (the SQLAlchemy repository) that satisfies it.

Using `typing.Protocol` (structural typing) means the infrastructure
layer doesn't need to import this module to "implement" the port — any
class with the right method signatures qualifies. That keeps the
dependency arrow pointing inward, which is the whole point of DDD
layering.

The repository works in terms of *domain objects* (`Account`,
`Transaction`), not ORM rows. Translation to/from ORM rows happens
inside the infrastructure layer, so the domain never sees SQLAlchemy.
"""

from typing import Protocol

from .account import Account
from .transaction import Transaction


class AccountRepository(Protocol):
    """The port for account/transaction persistence."""

    def get_by_number(self, number: str) -> Account | None:
        """Return the Account with `number`, or None if not found."""
        ...

    def add(self, account: Account) -> None:
        """Persist a new Account. Overwrites if the number already exists."""
        ...

    def save(self, account: Account) -> None:
        """Persist changes to an existing Account (e.g. updated balance)."""
        ...

    def append_transaction(self, transaction: Transaction) -> None:
        """Record a completed operation against an account."""
        ...

    def list_transactions(self, account_number: str) -> list[Transaction]:
        """Return the audit history for `account_number`, oldest first."""
        ...
