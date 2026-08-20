"""
Unit tests for the application layer.

Each use case is exercised against the in-memory `fake_repo` from
`conftest.py`. These tests verify that the services orchestrate the
domain correctly and persist via the repository port — without any
SQLAlchemy or HTTP machinery in the loop.
"""

import pytest

from banking.application.dto import AmountRequest, AuthRequest
from banking.application.services import (
    CheckBalanceService,
    DepositService,
    TransactionHistoryService,
    WithdrawService,
)
from banking.domain.exceptions import (
    AccountNotFoundError,
    IncorrectPinError,
    InsufficientFundsError,
)


# --- CheckBalanceService ---------------------------------------------


def test_check_balance_returns_current_balance(fake_repo):
    svc = CheckBalanceService(fake_repo)
    result = svc.execute(AuthRequest(account_number="1234567890", pin="1234"))
    assert result.balance == 1000.0
    assert result.holder == "John Doe"


def test_check_balance_records_audit_entry(fake_repo):
    svc = CheckBalanceService(fake_repo)
    svc.execute(AuthRequest(account_number="1234567890", pin="1234"))
    history = TransactionHistoryService(fake_repo).execute(
        AuthRequest(account_number="1234567890", pin="1234")
    )
    assert any(t.type == "balance_inquiry" for t in history)


def test_check_balance_wrong_pin_raises(fake_repo):
    svc = CheckBalanceService(fake_repo)
    with pytest.raises(IncorrectPinError):
        svc.execute(AuthRequest(account_number="1234567890", pin="0000"))


def test_check_balance_unknown_account_raises(fake_repo):
    svc = CheckBalanceService(fake_repo)
    with pytest.raises(AccountNotFoundError):
        svc.execute(AuthRequest(account_number="0000000000", pin="1234"))


# --- DepositService --------------------------------------------------


def test_deposit_increases_balance_and_persists(fake_repo):
    svc = DepositService(fake_repo)
    result = svc.execute(
        AmountRequest(account_number="1234567890", pin="1234", amount=250.0)
    )
    assert result.new_balance == 1250.0
    # Persistence: a fresh lookup should see the new balance.
    again = CheckBalanceService(fake_repo).execute(
        AuthRequest(account_number="1234567890", pin="1234")
    )
    assert again.balance == 1250.0


def test_deposit_records_transaction(fake_repo):
    DepositService(fake_repo).execute(
        AmountRequest(account_number="1234567890", pin="1234", amount=100.0)
    )
    history = TransactionHistoryService(fake_repo).execute(
        AuthRequest(account_number="1234567890", pin="1234")
    )
    deposits = [t for t in history if t.type == "deposit"]
    assert len(deposits) == 1
    assert deposits[0].amount == 100.0
    assert deposits[0].balance_after == 1100.0


# --- WithdrawService -------------------------------------------------


def test_withdraw_decreases_balance(fake_repo):
    result = WithdrawService(fake_repo).execute(
        AmountRequest(account_number="1234567890", pin="1234", amount=300.0)
    )
    assert result.new_balance == 700.0


def test_withdraw_too_much_raises_and_does_not_persist(fake_repo):
    with pytest.raises(InsufficientFundsError):
        WithdrawService(fake_repo).execute(
            AmountRequest(account_number="1234567890", pin="1234", amount=10_000.0)
        )
    # Balance unchanged.
    balance = CheckBalanceService(fake_repo).execute(
        AuthRequest(account_number="1234567890", pin="1234")
    ).balance
    assert balance == 1000.0


# --- TransactionHistoryService ---------------------------------------


def test_history_returns_oldest_first(fake_repo):
    deposit = DepositService(fake_repo)
    withdraw = WithdrawService(fake_repo)
    deposit.execute(AmountRequest("1234567890", "1234", 100.0))
    withdraw.execute(AmountRequest("1234567890", "1234", 50.0))

    history = TransactionHistoryService(fake_repo).execute(
        AuthRequest("1234567890", "1234")
    )
    assert [t.type for t in history] == ["deposit", "withdrawal"]
