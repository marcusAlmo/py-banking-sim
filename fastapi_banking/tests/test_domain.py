"""
Unit tests for the domain layer.

No DB, no HTTP, no Pydantic — just the Account entity's rules. These
should run in milliseconds and give fast feedback when refactoring the
domain.
"""

import pytest

from banking.domain.account import Account
from banking.domain.exceptions import InsufficientFundsError, ValidationError


def test_valid_account_constructs():
    acct = Account("1234567890", "Alice", 500.0, "1234")
    assert acct.number == "1234567890"
    assert acct.name == "Alice"
    assert acct.balance == 500.0


@pytest.mark.parametrize(
    "number,name,balance,pin",
    [
        ("123", "Alice", 100.0, "1234"),         # bad account number
        ("1234567890", "", 100.0, "1234"),       # empty name
        ("1234567890", "Alice", -1.0, "1234"),   # negative balance
        ("1234567890", "Alice", 100.0, "12"),    # bad PIN
        ("1234567890", "Alice", 100.0, "abcd"),  # non-digit PIN
    ],
)
def test_invalid_construction_raises(number, name, balance, pin):
    with pytest.raises(ValidationError):
        Account(number, name, balance, pin)


def test_deposit_increases_balance():
    acct = Account("1234567890", "Alice", 100.0, "1234")
    assert acct.deposit(50.0) == 150.0
    assert acct.balance == 150.0


def test_deposit_non_positive_raises():
    acct = Account("1234567890", "Alice", 100.0, "1234")
    with pytest.raises(ValidationError):
        acct.deposit(0.0)
    with pytest.raises(ValidationError):
        acct.deposit(-10.0)


def test_withdraw_decreases_balance():
    acct = Account("1234567890", "Alice", 100.0, "1234")
    assert acct.withdraw(40.0) == 60.0


def test_withdraw_more_than_balance_raises():
    acct = Account("1234567890", "Alice", 100.0, "1234")
    with pytest.raises(InsufficientFundsError):
        acct.withdraw(101.0)


def test_verify_pin_returns_bool():
    acct = Account("1234567890", "Alice", 100.0, "1234")
    assert acct.verify_pin("1234") is True
    assert acct.verify_pin("0000") is False


def test_accounts_equal_by_number():
    a = Account("1234567890", "Alice", 100.0, "1234")
    b = Account("1234567890", "Bob", 999.0, "5678")
    assert a == b  # same number -> same identity
    assert hash(a) == hash(b)
