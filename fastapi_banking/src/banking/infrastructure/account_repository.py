"""
SQLAlchemy implementation of the `AccountRepository` port.

This is the bridge between the ORM world (`AccountModel`,
`TransactionModel`) and the domain world (`Account`, `Transaction`).
Translation happens here and only here, so the domain never sees a
SQLAlchemy row.

The class is constructed with a `sessionmaker`; each call opens a
short-lived session, performs the operation, commits, and closes.
Keeping session lifetime scoped to a single repository call is the
simplest correct pattern for a small app like this — no risk of
stale sessions hanging off long-lived objects.
"""

from sqlalchemy import select
from sqlalchemy.orm import Session, sessionmaker

from ..domain.account import Account
from ..domain.transaction import Transaction, TransactionType
from .orm import AccountModel, Base, TransactionModel


class SqlAlchemyAccountRepository:
    """
    Concrete `AccountRepository` adapter backed by SQLAlchemy.

    Satisfies the Protocol in `domain.repositories` structurally — no
    inheritance needed.
    """

    def __init__(self, session_factory: sessionmaker[Session]):
        self._session_factory = session_factory

    # --- Account CRUD -------------------------------------------------

    def get_by_number(self, number: str) -> Account | None:
        with self._session_factory() as session:
            row = session.get(AccountModel, number)
            if row is None:
                return None
            return self._row_to_account(row)

    def add(self, account: Account) -> None:
        with self._session_factory() as session:
            row = AccountModel(
                number=account.number,
                holder=account.name,
                balance=account.balance,
                pin=account._pin,  # noqa: SLF001 — persistence needs the PIN
            )
            session.merge(row)
            session.commit()

    def save(self, account: Account) -> None:
        with self._session_factory() as session:
            row = session.get(AccountModel, account.number)
            if row is None:
                # If the account isn't persisted yet, fall back to add.
                session.merge(
                    AccountModel(
                        number=account.number,
                        holder=account.name,
                        balance=account.balance,
                        pin=account._pin,  # noqa: SLF001
                    )
                )
            else:
                row.balance = account.balance
            session.commit()

    # --- Transactions -------------------------------------------------

    def append_transaction(self, transaction: Transaction) -> None:
        with self._session_factory() as session:
            row = TransactionModel(
                account_number=transaction.account_number,
                type=transaction.type.value,
                amount=transaction.amount,
                balance_after=transaction.balance_after,
                timestamp=transaction.timestamp,
            )
            session.add(row)
            session.commit()

    def list_transactions(self, account_number: str) -> list[Transaction]:
        with self._session_factory() as session:
            stmt = (
                select(TransactionModel)
                .where(TransactionModel.account_number == account_number)
                .order_by(TransactionModel.timestamp, TransactionModel.id)
            )
            rows = session.scalars(stmt).all()
            return [self._row_to_transaction(r) for r in rows]

    # --- Translation helpers -----------------------------------------

    @staticmethod
    def _row_to_account(row: AccountModel) -> Account:
        # We bypass Account.__init__'s validation here because the row
        # already represents a persisted, validated account. Going
        # through __init__ would re-validate (and could fail if a
        # legacy row violates current rules), which is not what we
        # want on the read path.
        account = Account.__new__(Account)
        account._number = row.number  # noqa: SLF001
        account._name = row.holder  # noqa: SLF001
        account._balance = row.balance  # noqa: SLF001
        account._pin = row.pin  # noqa: SLF001
        return account

    @staticmethod
    def _row_to_transaction(row: TransactionModel) -> Transaction:
        return Transaction(
            type=TransactionType(row.type),
            account_number=row.account_number,
            amount=row.amount,
            balance_after=row.balance_after,
            timestamp=row.timestamp,
        )


def create_all_tables(session_factory: sessionmaker[Session]) -> None:
    """Create all tables if they don't exist. Called once at app startup."""
    # Pull the engine out of the sessionmaker.
    engine = session_factory.kw["bind"]
    Base.metadata.create_all(bind=engine)
