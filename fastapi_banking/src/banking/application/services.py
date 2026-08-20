"""
Application services: the use cases of the app.

Each service class is one user-facing operation. A service:

  1. Receives a DTO from the interface layer.
  2. Loads the relevant domain object(s) via the repository port.
  3. Calls a method on the domain object — that's where the rules live.
  4. Persists the result via the repository.
  5. Returns a DTO describing the outcome.

Services do NOT contain business rules themselves. They orchestrate.
The rules ("can't withdraw more than the balance", "PIN must be 4
digits") live in `domain/account.py`. This separation is what lets us
unit-test the rules without any service, and test the services with a
fake in-memory repository (see `tests/test_application.py`).

The repository is injected through the constructor, so the same service
class works against SQLite in production and a fake dict in tests.
"""

from .dto import (
    AmountRequest,
    AuthRequest,
    BalanceResult,
    OperationResult,
    TransactionView,
)
from ..domain.account import Account
from ..domain.exceptions import AccountNotFoundError, IncorrectPinError
from ..domain.repositories import AccountRepository
from ..domain.transaction import Transaction, TransactionType


def _authenticate(repo: AccountRepository, account_number: str, pin: str) -> Account:
    """
    Shared auth helper: load the account and verify the PIN.

    Raises AccountNotFoundError / IncorrectPinError so the API error
    handlers can map them to 404 / 401 respectively. Returns the
    authenticated Account on success.
    """
    account = repo.get_by_number(account_number)
    if account is None:
        raise AccountNotFoundError(f"No account with number {account_number!r}.")
    if not account.verify_pin(pin):
        raise IncorrectPinError("Incorrect PIN.")
    return account


class CheckBalanceService:
    """Use case: return the current balance of an authenticated account."""

    def __init__(self, repo: AccountRepository):
        self._repo = repo

    def execute(self, req: AuthRequest) -> BalanceResult:
        account = _authenticate(self._repo, req.account_number, req.pin)
        # A balance inquiry is itself an auditable event, so we record
        # it just like the REPL does.
        self._repo.append_transaction(
            Transaction(
                type=TransactionType.BALANCE_INQUIRY,
                account_number=account.number,
                amount=0.0,
                balance_after=account.balance,
            )
        )
        return BalanceResult(
            account_number=account.number,
            holder=account.name,
            balance=account.balance,
        )


class DepositService:
    """Use case: deposit a positive amount into an authenticated account."""

    def __init__(self, repo: AccountRepository):
        self._repo = repo

    def execute(self, req: AmountRequest) -> OperationResult:
        account = _authenticate(self._repo, req.account_number, req.pin)
        new_balance = account.deposit(req.amount)  # rules enforced here
        self._repo.save(account)
        txn = Transaction(
            type=TransactionType.DEPOSIT,
            account_number=account.number,
            amount=req.amount,
            balance_after=new_balance,
        )
        self._repo.append_transaction(txn)
        return OperationResult(
            account_number=account.number,
            new_balance=new_balance,
            transaction_id=None,
        )


class WithdrawService:
    """Use case: withdraw a positive amount from an authenticated account."""

    def __init__(self, repo: AccountRepository):
        self._repo = repo

    def execute(self, req: AmountRequest) -> OperationResult:
        account = _authenticate(self._repo, req.account_number, req.pin)
        # Account.withdraw raises InsufficientFundsError if the rules
        # are violated; we let it propagate so the API layer can map it
        # to 409 (conflict) rather than 400.
        new_balance = account.withdraw(req.amount)
        self._repo.save(account)
        txn = Transaction(
            type=TransactionType.WITHDRAWAL,
            account_number=account.number,
            amount=req.amount,
            balance_after=new_balance,
        )
        self._repo.append_transaction(txn)
        return OperationResult(
            account_number=account.number,
            new_balance=new_balance,
            transaction_id=None,
        )


class TransactionHistoryService:
    """Use case: list the audit history for an authenticated account."""

    def __init__(self, repo: AccountRepository):
        self._repo = repo

    def execute(self, req: AuthRequest) -> list[TransactionView]:
        _authenticate(self._repo, req.account_number, req.pin)
        txns = self._repo.list_transactions(req.account_number)
        return [
            TransactionView(
                type=t.type.value,
                amount=t.amount,
                balance_after=t.balance_after,
                timestamp=t.timestamp.isoformat(),
            )
            for t in txns
        ]
