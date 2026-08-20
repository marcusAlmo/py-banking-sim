"""
Seed data: the same three demo accounts the REPL version preloads.

`seed_if_empty` is idempotent — it only inserts when the accounts table
is empty, so restarting the server doesn't duplicate or overwrite data
that's been modified at runtime.
"""

from sqlalchemy import select
from sqlalchemy.orm import Session, sessionmaker

from ..domain.account import Account
from .orm import AccountModel

SEED_ACCOUNTS: list[Account] = [
    Account("1234567890", "John Doe", 1000.0, "1234"),
    Account("0987654321", "Jane Smith", 1500.0, "5678"),
    Account("1111222233", "Bob Johnson", 2000.0, "9012"),
]


def seed_if_empty(session_factory: sessionmaker[Session]) -> None:
    """Insert the demo accounts iff the accounts table is empty."""
    with session_factory() as session:
        any_row = session.scalars(select(AccountModel).limit(1)).first()
        if any_row is not None:
            return
        for acct in SEED_ACCOUNTS:
            session.add(
                AccountModel(
                    number=acct.number,
                    holder=acct.name,
                    balance=acct.balance,
                    pin=acct._pin,  # noqa: SLF001 — persistence needs the PIN
                )
            )
        session.commit()
