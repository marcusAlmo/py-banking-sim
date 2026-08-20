"""
The Account entity: the core domain object of the simulator.

This is a faithful port of the parent project's `account.py`. The class
is a *pure domain entity*: it knows banking rules and nothing else. It
does not import SQLAlchemy, Pydantic, or any other infrastructure
concern. The infrastructure layer is responsible for persisting and
rehydrating Account instances; the domain layer just enforces the rules.

Keeping the entity pure is what lets us unit-test it without a database
(see `tests/test_domain.py`) and reuse it unchanged behind other
interfaces later.
"""

from .exceptions import InsufficientFundsError, ValidationError


class Account:
    """
    Represents a single bank account.

    Attributes are marked with a single leading underscore to signal
    that they are internal. External code should use `deposit()`,
    `withdraw()`, and the read-only properties instead of poking at
    the underscored fields directly.
    """

    def __init__(self, number: str, name: str, balance: float, pin: str):
        # Guard the invariants up front. If any of these fail, the
        # object is never created — callers cannot accidentally hold a
        # reference to a half-constructed, invalid Account.
        if not (len(number) == 10 and number.isdigit()):
            raise ValidationError("Account number must be a 10-digit string.")
        if not name:
            raise ValidationError("Account holder name cannot be empty.")
        if balance < 0:
            raise ValidationError("Starting balance cannot be negative.")
        if not (len(pin) == 4 and pin.isdigit()):
            raise ValidationError("PIN must be a 4-digit string.")

        self._number = number
        self._name = name
        self._balance = balance
        self._pin = pin

    # --- Read-only properties -----------------------------------------

    @property
    def number(self) -> str:
        return self._number

    @property
    def name(self) -> str:
        return self._name

    @property
    def balance(self) -> float:
        """Read-only access to the balance. Use deposit()/withdraw() to change it."""
        return self._balance

    # --- Auth ---------------------------------------------------------

    def verify_pin(self, pin: str) -> bool:
        """
        Return True if the supplied PIN matches this account's PIN.

        Returns a bool rather than raising: PIN verification is a
        yes/no question, so a bool is the most honest API. The caller
        (an application service) decides what to do on False.
        """
        return self._pin == pin

    # --- Business operations ------------------------------------------
    # These are the ONLY ways to change `_balance`. Centralizing the
    # rules here means we never have to hunt the codebase for places
    # that mutate the balance — there's exactly two of them.

    def deposit(self, amount: float) -> float:
        """Add `amount` to the balance and return the new balance."""
        if amount <= 0:
            raise ValidationError("Deposit amount must be positive.")
        self._balance += amount
        return self._balance

    def withdraw(self, amount: float) -> float:
        """Subtract `amount` from the balance and return the new balance."""
        if amount <= 0:
            raise ValidationError("Withdrawal amount must be positive.")
        if amount > self._balance:
            raise InsufficientFundsError(
                f"Insufficient funds: balance is {self._balance:.2f}, "
                f"requested {amount:.2f}."
            )
        self._balance -= amount
        return self._balance

    def __repr__(self) -> str:
        # Deliberately do NOT include the PIN — repr output often ends
        # up in logs, and logging a PIN would be a security mistake
        # even in a toy project.
        return (
            f"Account(number={self._number!r}, name={self._name!r}, "
            f"balance={self._balance:.2f})"
        )

    def __eq__(self, other: object) -> bool:
        # Two Accounts are "the same" if their (unique) account number
        # matches. This is identity-by-key, which is what DDD calls an
        # "entity" — it has a stable identity independent of its
        # attribute values.
        return isinstance(other, Account) and other._number == self._number

    def __hash__(self) -> int:
        return hash(self._number)
