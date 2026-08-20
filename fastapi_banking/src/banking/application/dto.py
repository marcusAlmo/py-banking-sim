"""
Data Transfer Objects for the application layer.

DTOs are plain containers describing the inputs and outputs of use
cases. They are deliberately framework-agnostic (no Pydantic, no
SQLAlchemy) so the application layer can be tested without spinning up
any web framework. The interfaces/api layer adapts between these DTOs
and Pydantic request/response models.

Using frozen dataclasses keeps DTOs immutable and gives value equality
for free, which makes assertions in tests read naturally.
"""

from dataclasses import dataclass


@dataclass(frozen=True)
class AuthRequest:
    """Account number + PIN. Used by every authenticated use case."""
    account_number: str
    pin: str


@dataclass(frozen=True)
class AmountRequest:
    """Auth + an amount to move. Used by deposit and withdraw."""
    account_number: str
    pin: str
    amount: float


@dataclass(frozen=True)
class BalanceResult:
    account_number: str
    holder: str
    balance: float


@dataclass(frozen=True)
class OperationResult:
    """Returned by deposit/withdraw: the new balance plus a record id."""
    account_number: str
    new_balance: float
    transaction_id: int | None  # None if the repository doesn't assign ids


@dataclass(frozen=True)
class TransactionView:
    """A single entry in a transaction history listing."""
    type: str
    amount: float
    balance_after: float
    timestamp: str  # ISO-8601; formatting happens here, not at the API edge
