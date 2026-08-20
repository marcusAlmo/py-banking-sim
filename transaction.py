"""
The Transaction class: an immutable record of a completed operation.

WHY TRANSACTION IS NOW A RECORD, NOT AN ACTOR
---------------------------------------------
In the original code, `Transaction` was the class that *performed*
deposits and withdrawals by mutating the global accounts dict. That
conflated two very different responsibilities:

  1. EXECUTING the operation (move money).
  2. RECORDING the operation (audit trail).

Mixing them meant there was no clean record of what happened — the
balance just changed and the reason was lost. By splitting the concerns:

  - Account.deposit / Account.withdraw *execute* the operation and
    enforce the rules.
  - Transaction *records* what happened, so it can be logged, displayed,
    or audited later.

This is the Single Responsibility Principle (the S in SOLID): a class
should have one reason to change. Account changes when banking rules
change; Transaction changes when auditing needs change.

IMMUTABILITY
------------
A Transaction is created AFTER the operation succeeds and is never
modified. Marking fields as read-only (no setters, no mutating methods)
prevents bugs where an audit record is accidentally altered after the
fact. In Python we enforce this by convention (no setters) plus a
__setattr__ guard; for a production system you'd use a frozen dataclass
or a NamedTuple, but the manual version here is clearer for learning.
"""

from datetime import datetime
from enum import Enum


# An Enum is the right way to model a fixed set of categories.
# Compared to string literals ("deposit", "withdraw"), an Enum gives you:
#   - autocomplete in your IDE
#   - typo-proofing (TransactionType.DEPOSIT vs "deopsit")
#   - a single place to see all valid transaction kinds
class TransactionType(Enum):
    DEPOSIT = "deposit"
    WITHDRAWAL = "withdrawal"
    BALANCE_INQUIRY = "balance_inquiry"


class Transaction:
    """
    An immutable record describing one completed banking operation.

    Fields:
        type:        what kind of operation was performed.
        account:     the Account the operation was performed on.
        amount:      the money moved (0 for a balance inquiry).
        balance_after: the account balance immediately after the op.
        timestamp:   when the operation occurred.
    """

    __slots__ = ("_type", "_account_number", "_amount", "_balance_after", "_timestamp")
    # __slots__ fixes the set of attributes an instance can have. This has
    # two benefits: (1) it prevents accidentally setting a misspelled
    # attribute like `t.amout = 5`, and (2) it saves memory because Python
    # doesn't need a per-instance __dict__. For a handful of objects the
    # memory doesn't matter, but the typo-protection does.

    def __init__(
        self,
        type: TransactionType,
        account_number: str,
        amount: float,
        balance_after: float,
        timestamp: datetime | None = None,
    ):
        """
        Create a Transaction record.

        We store the account NUMBER, not the Account object itself. This
        avoids a circular reference and means the record stays valid even
        if the Account is later removed from the Bank.
        """
        self._type = type
        self._account_number = account_number
        self._amount = amount
        self._balance_after = balance_after
        # Default `timestamp` to "now" if the caller didn't supply one.
        # Letting the caller override the timestamp is what makes time-
        # sensitive code testable: a test can pass a fixed timestamp and
        # get deterministic results.
        self._timestamp = timestamp or datetime.now()

    # Read-only properties — no setters, so a Transaction can't be
    # mutated after construction. This is what makes it a trustworthy
    # audit record.
    @property
    def type(self) -> TransactionType:
        return self._type

    @property
    def account_number(self) -> str:
        return self._account_number

    @property
    def amount(self) -> float:
        return self._amount

    @property
    def balance_after(self) -> float:
        return self._balance_after

    @property
    def timestamp(self) -> datetime:
        return self._timestamp

    def __repr__(self) -> str:
        return (
            f"Transaction(type={self._type.value!r}, "
            f"account={self._account_number!r}, "
            f"amount={self._amount:.2f}, "
            f"balance_after={self._balance_after:.2f}, "
            f"at={self._timestamp.isoformat()})"
        )
