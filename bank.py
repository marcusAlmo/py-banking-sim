"""
The Bank class: manages the collection of accounts and authentication.

WHY A Bank CLASS?
-----------------
In the original code, `accounts` was a module-level dict in core.py, and
`verify_account` / `verify_pin` were free functions that read that global.
That design has two problems:

  1. GLOBAL MUTABLE STATE. Any module that imports `core` can mutate
     `accounts` at any time. There's no single owner of the data, so
     it's impossible to reason about who changed what and when.

  2. NO SINGLE SOURCE OF TRUTH. If you wanted to add a second bank, or
     persist accounts to a file, or add an audit log, you'd have to
     scatter changes across free functions and the global dict.

Wrapping the collection in a Bank class gives you:
  - ONE OWNER of the account data (the Bank instance).
  - A CLEAR API surface: `get_account`, `authenticate`, `add_account`.
  - A NATURAL PLACE to add cross-cutting concerns later (persistence,
    logging, rate limiting) without touching Account or the UI.

DEPENDENCY INJECTION
--------------------
Notice the constructor takes a `accounts` dict but does NOT hardcode one.
This is called *dependency injection*: the caller decides which accounts
the Bank manages. That makes the class trivially testable — a test can
construct a Bank with a single fake account and exercise it in isolation,
with no side effects on any global state.
"""

from account import Account
from exceptions import AccountNotFoundError, IncorrectPinError


class Bank:
    """
    Holds and manages a collection of Account objects.

    Internally we store accounts in a dict keyed by account number for
    O(1) lookup. The dict is created in __init__ and never replaced, so
    references to the Bank always see a consistent collection.
    """

    def __init__(self, accounts: dict[str, Account] | None = None):
        """
        Create a Bank.

        Args:
            accounts: Optional initial mapping of {number: Account}.
                If None, the Bank starts empty. We copy the supplied
                dict so the caller can't later mutate our internal
                state by holding onto their reference.
        """
        # `dict(...)` makes a shallow copy. The Account objects themselves
        # are shared, but the mapping structure is private to this Bank.
        # `None` is falsy, so `accounts or {}` yields a fresh empty dict
        # when the caller passes nothing.
        self._accounts: dict[str, Account] = dict(accounts or {})

    # --- Collection management ----------------------------------------

    def add_account(self, account: Account) -> None:
        """Register an Account with the bank. Overwrites if the number exists."""
        self._accounts[account.number] = account

    def get_account(self, number: str) -> Account:
        """
        Look up an account by number.

        Raises AccountNotFoundError if no account has that number.
        Returning the Account object (rather than a dict) means callers
        get a real object with methods, not raw data they have to know
        how to interpret.
        """
        account = self._accounts.get(number)
        if account is None:
            raise AccountNotFoundError(f"No account with number {number!r}.")
        return account

    # --- Authentication -----------------------------------------------
    # Auth is a Bank responsibility, not an Account responsibility,
    # because "does this account exist?" is a question about the
    # *collection*, not about a single account. The PIN check itself
    # delegates to Account.verify_pin, since only the Account knows its
    # own PIN.

    def authenticate(self, number: str, pin: str) -> Account:
        """
        Verify the account exists AND the PIN matches.

        Returns the authenticated Account on success so the caller can
        proceed to operate on it without a second lookup.

        Raises:
            AccountNotFoundError: no such account.
            IncorrectPinError: account exists but PIN is wrong.
        """
        account = self.get_account(number)
        if not account.verify_pin(pin):
            raise IncorrectPinError("Incorrect PIN.")
        return account
