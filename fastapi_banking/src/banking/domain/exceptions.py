"""
Domain exception hierarchy.

This is a near-verbatim copy of the parent project's `exceptions.py`,
relocated into the `domain` package so the domain layer can raise and
catch its own errors without depending on anything outside.

The same rationale applies: a typed hierarchy lets outer layers (the
FastAPI error handlers in `interfaces/api/error_handlers.py`) translate
each kind of failure into the right HTTP status code instead of lumping
everything into a generic 500.
"""


class BankingError(Exception):
    """Base class for all banking-domain errors."""


class ValidationError(BankingError):
    """Raised when input fails a format/range check (e.g. non-digit PIN)."""


class AccountNotFoundError(BankingError):
    """Raised when an account number is not registered with the bank."""


class IncorrectPinError(BankingError):
    """Raised when a supplied PIN does not match the account's PIN."""


class InsufficientFundsError(BankingError):
    """Raised when a withdrawal exceeds the available balance."""
