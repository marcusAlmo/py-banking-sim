"""
Custom exception hierarchy for the banking simulator.

WHY A CUSTOM HIERARCHY?
-----------------------
In the original code, every error path raised a bare `ValueError`. That made it
impossible for the UI layer (main.py) to tell apart:
  - a *validation* error (user typed junk) -> retry the prompt
  - an *account* error (account doesn't exist) -> retry the prompt
  - a *business-rule* error (insufficient funds) -> abort the transaction

By giving each kind of failure its own exception type, the caller can catch
exactly the failures it knows how to handle, and let unexpected errors bubble
up as real bugs instead of being silently swallowed.

All exceptions inherit from `BankingError` so a caller can also do a single
    except BankingError as e:
to handle any domain-level failure in one place.
"""


# Base class for every domain-specific error in the app.
# Inheriting from `Exception` (not `ValueError`) keeps our errors separate
# from Python's built-in ValueError, which other libraries might raise.
class BankingError(Exception):
    """Base class for all banking-domain errors."""


# --- Validation errors -------------------------------------------------
# These are raised by utils.py when raw user input fails a format check.
# They signal "the user typed something malformed" -> the UI should re-prompt.

class ValidationError(BankingError):
    """Raised when user input fails a format/range check (e.g. non-digit PIN)."""


# --- Account errors ----------------------------------------------------
# These are raised by the Bank/Account layer when a lookup or auth fails.
# They signal a domain problem, not a formatting problem.

class AccountNotFoundError(BankingError):
    """Raised when an account number is not registered with the bank."""


class IncorrectPinError(BankingError):
    """Raised when a supplied PIN does not match the account's PIN."""


# --- Business-rule errors ----------------------------------------------
# These are raised when an operation violates a banking rule.
# The input was valid and the account exists, but the action is not allowed.

class InsufficientFundsError(BankingError):
    """Raised when a withdrawal exceeds the available balance."""
