"""
The Account class: the core domain object of the simulator.

WHY A DEDICATED Account CLASS?
------------------------------
In the original code, an "account" was just an entry in a dict:
    {"1234567890": {"name": "John", "balance": 1000.0, "pin": "1234"}}
Any code anywhere in the project could read or mutate that dict freely —
no rules, no validation, no logging. That's the opposite of encapsulation.

A proper Account class:
  1. ENCAPSULATES state behind methods. The balance can only change via
     `deposit()` and `withdraw()`, which enforce the rules (no negative
     amounts, no overdraft) in ONE place.
  2. GUARDS invariants. The constructor validates that the starting balance
     is non-negative and the PIN is 4 digits, so it's impossible to create
     an Account in an invalid state.
  3. IS TESTABLE in isolation. You can unit-test deposit/withdraw without
     spinning up the whole Bank or the REPL.

This is the difference between "objects as namespaces for functions" and
real object-oriented design: the object protects its own invariants.
"""

from exceptions import InsufficientFundsError, ValidationError


class Account:
    """
    Represents a single bank account.

    Attributes are marked with a single leading underscore (`_balance`,
    `_pin`) to signal that they are internal implementation details.
    Python does not enforce privacy — the underscore is a *convention*
    that tells other developers "don't touch this directly; use the
    methods." External code should call `deposit()`, `withdraw()`, and
    `balance` (the read-only property) instead of poking at `_balance`.

    Convention summary:
      _name      -> "internal" (don't access from outside)
      name       -> "public"   (free to access)
      __name     -> "name-mangled" (harder to access; rarely needed)
    """

    def __init__(self, number: str, name: str, balance: float, pin: str):
        """
        Construct an Account, validating inputs so the object can never
        exist in an invalid state.

        The `: str` / `: float` annotations are TYPE HINTS. They are not
        enforced at runtime, but they document intent and let tools like
        `mypy` or your IDE catch type mistakes before you run the code.
        """
        # Guard the invariants up front. If any of these fail, the object
        # is never created — callers cannot accidentally hold a reference
        # to a half-constructed, invalid Account.
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

    # --- Read-only properties ------------------------------------------
    # A @property turns a method into something that looks like an attribute
    # from the outside (`acct.balance`) but is computed/controlled on the
    # inside. Here we use it to expose state as READ-ONLY: there is no
    # setter, so callers can read `acct.balance` but cannot assign to it.

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

    # --- Auth ----------------------------------------------------------

    def verify_pin(self, pin: str) -> bool:
        """
        Return True if the supplied PIN matches this account's PIN.

        Note we return a bool rather than raising an exception here.
        PIN verification is a yes/no question, so a bool return is the
        most honest API. The Bank layer decides what to do on False
        (raise IncorrectPinError, increment a counter, etc.).
        """
        return self._pin == pin

    # --- Business operations -------------------------------------------
    # These are the ONLY ways to change `_balance`. Centralizing the rules
    # here means we never have to hunt the codebase for places that mutate
    # the balance — there's exactly two of them.

    def deposit(self, amount: float) -> float:
        """
        Add `amount` to the balance and return the new balance.
        Raises ValidationError if amount is not positive.
        """
        if amount <= 0:
            raise ValidationError("Deposit amount must be positive.")
        self._balance += amount
        return self._balance

    def withdraw(self, amount: float) -> float:
        """
        Subtract `amount` from the balance and return the new balance.
        Raises ValidationError if amount is not positive.
        Raises InsufficientFundsError if the balance would go negative.
        """
        if amount <= 0:
            raise ValidationError("Withdrawal amount must be positive.")
        if amount > self._balance:
            # A domain-specific exception lets the UI distinguish
            # "you typed -5" (ValidationError) from "you don't have
            # enough money" (InsufficientFundsError) and respond
            # appropriately to each.
            raise InsufficientFundsError(
                f"Insufficient funds: balance is {self._balance:.2f}, "
                f"requested {amount:.2f}."
            )
        self._balance -= amount
        return self._balance

    # --- Dunder methods ------------------------------------------------
    # __repr__ defines how the object looks when printed or inspected in a
    # debugger. A good __repr__ makes debugging much easier.

    def __repr__(self) -> str:
        # Note we deliberately do NOT include the PIN here — repr output
        # often ends up in logs, and logging a PIN would be a security
        # mistake even in a toy project. Get the habit right early.
        return f"Account(number={self._number!r}, name={self._name!r}, balance={self._balance:.2f})"
