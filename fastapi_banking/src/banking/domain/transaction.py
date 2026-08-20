"""
The Transaction record: an immutable audit entry for a completed operation.

Ported from the parent project's `transaction.py`. In the FastAPI version
these records are also persisted (see `infrastructure/orm.py`), so the
API can serve a transaction history endpoint. The domain object itself
stays storage-agnostic — persistence is the infrastructure layer's job.
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum


class TransactionType(Enum):
    """The kinds of operations we record audit entries for."""
    DEPOSIT = "deposit"
    WITHDRAWAL = "withdrawal"
    BALANCE_INQUIRY = "balance_inquiry"


# A frozen dataclass gives us immutability + value equality + a free
# __repr__ with less boilerplate than the parent project's hand-rolled
# class. `frozen=True` makes every field read-only after construction,
# which is exactly what an audit record needs.
@dataclass(frozen=True)
class Transaction:
    """An immutable record describing one completed banking operation."""

    type: TransactionType
    account_number: str
    amount: float
    balance_after: float
    timestamp: datetime = field(default_factory=datetime.now)

    # We store the account NUMBER, not the Account object itself. This
    # avoids a circular reference and keeps the record valid even if the
    # Account is later removed from the repository.
