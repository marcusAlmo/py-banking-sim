"""
The REPL (Read-Evaluate-Print Loop): the user interface layer.

THE GOAL OF THIS FILE
---------------------
main.py should know NOTHING about banking rules. It should:
  1. Show a menu.
  2. Read input from the user.
  3. Hand that input to the domain layer (Bank / Account).
  4. Print the result or the error message.

That's it. No balance arithmetic, no PIN comparison, no account lookups
happen here. This separation pays off in two ways:

  - You can swap the UI without touching the domain. Want a web front
    end? Replace this file with a Flask app that calls the same Bank
    methods. The Bank doesn't care who's calling it.
  - You can unit-test the domain without simating keystrokes. Tests
    construct a Bank, call .authenticate() and .deposit() directly,
    and never touch this file.

WHY A `main()` FUNCTION INSTEAD OF TOP-LEVEL CODE?
--------------------------------------------------
Wrapping the program in a function and guarding execution with
    if __name__ == "__main__":
means this file can be imported (e.g. by a test or another script)
without the REPL automatically starting. Top-level code runs on import;
function definitions don't. This is the Python idiom for "run only when
executed directly."

WHY `sys.path.insert`?
----------------------
When you run `python main.py`, Python adds main.py's directory to
sys.path automatically, so `import account` works. But if you run from
elsewhere (e.g. `python -m` or an IDE that sets a different working
dir), the sibling modules might not be found. Inserting the script's
own directory makes imports reliable regardless of how it's launched.
In a larger project you'd use a proper package layout + pyproject.toml
instead, but for a single-folder simulator this is fine.
"""

import sys
from pathlib import Path

# Make sibling modules importable no matter where the script is launched from.
sys.path.insert(0, str(Path(__file__).resolve().parent))

from account import Account
from bank import Bank
from exceptions import (
    AccountNotFoundError,
    BankingError,
    IncorrectPinError,
    InsufficientFundsError,
    ValidationError,
)
from transaction import Transaction, TransactionType
from utils import account_number_validator, amount_validator, pin_validator


# --- Seed data ---------------------------------------------------------
# In a real app this would come from a database or a file. Keeping it in
# one factory function here means the UI knows how to build a starting
# Bank, but the Bank class itself stays storage-agnostic.
def build_seed_bank() -> Bank:
    """Create a Bank preloaded with a few demo accounts."""
    accounts = {
        "1234567890": Account("1234567890", "John Doe", 1000.0, "1234"),
        "0987654321": Account("0987654321", "Jane Smith", 1500.0, "5678"),
        "1111222233": Account("1111222233", "Bob Johnson", 2000.0, "9012"),
    }
    return Bank(accounts)


# --- Constants --------------------------------------------------------
# Named constants instead of magic numbers/strings. If you ever want to
# change "3 attempts" to "5 attempts", you change it in one place.
MAX_AUTH_ATTEMPTS = 3

MENU = """
    Please select an action:
     [1] Check Balance
     [2] Deposit
     [3] Withdraw
     [4] Exit
"""


# --- Auth helper ------------------------------------------------------
# Pulling the auth retry loop into its own function keeps the main loop
# readable and gives the auth flow a single, testable entry point.
def authenticate(bank: Bank, action_label: str) -> Account | None:
    """
    Prompt for account number + PIN until auth succeeds or the user
    exhausts MAX_AUTH_ATTEMPTS attempts.

    Returns the authenticated Account on success, or None on lockout.
    Returning None (rather than raising) signals "the user failed to
    log in" — which is a normal control-flow outcome, not an error.
    """
    for attempt in range(1, MAX_AUTH_ATTEMPTS + 1):
        try:
            account_number = account_number_validator(
                input(f"Enter your account number to {action_label}: ")
            )
            pin = pin_validator(input("Enter your PIN: "))
            # authenticate() returns the Account on success, so we can
            # use it immediately without a second lookup.
            return bank.authenticate(account_number, pin)
        except (ValidationError, AccountNotFoundError, IncorrectPinError) as e:
            # We catch exactly the input/auth errors we know how to
            # recover from (by retrying). Anything else (a bug, a
            # missing module) is NOT caught here — it propagates so we
            # notice it instead of silently looping forever.
            remaining = MAX_AUTH_ATTEMPTS - attempt
            print(f"{e} ({remaining} attempt(s) remaining)")
    print("Too many invalid inputs. Please try again later.")
    return None


# --- Main loop --------------------------------------------------------
def main() -> None:
    bank = build_seed_bank()
    # A per-session audit log. In a real system this would be persisted
    # to a database; here we just collect Transaction records in memory
    # so the structure is in place if you want to extend it.
    audit_log: list[Transaction] = []

    print("Welcome to MJ Banking")

    while True:
        action_input = input(MENU)

        # Parse the menu choice. A bad choice is a UI problem, so we
        # handle it here and `continue` — no need to involve the domain.
        try:
            action = int(action_input)
        except ValueError:
            print("Invalid input. Please enter a number between 1 and 4.")
            continue
        if action not in (1, 2, 3, 4):
            print("Invalid input. Please enter a number between 1 and 4.")
            continue

        # Exit doesn't need auth — handle it before the auth prompt.
        if action == 4:
            print("Goodbye!")
            break

        action_label = {1: "Check Balance", 2: "Deposit", 3: "Withdraw"}[action]
        account = authenticate(bank, action_label)
        if account is None:
            continue  # user was locked out; back to the menu

        # Dispatch to the right operation. Each branch is tiny because
        # the real work lives in Account, where it belongs.
        try:
            if action == 1:
                balance = account.balance
                audit_log.append(
                    Transaction(
                        TransactionType.BALANCE_INQUIRY,
                        account.number, 0.0, balance,
                    )
                )
                print(f"Current balance: {balance:.2f}")

            elif action == 2:
                amount = amount_validator(input("Enter the amount to deposit: "))
                new_balance = account.deposit(amount)
                audit_log.append(
                    Transaction(
                        TransactionType.DEPOSIT,
                        account.number, amount, new_balance,
                    )
                )
                print(f"New balance: {new_balance:.2f}")

            elif action == 3:
                amount = amount_validator(input("Enter the amount to withdraw: "))
                new_balance = account.withdraw(amount)
                audit_log.append(
                    Transaction(
                        TransactionType.WITHDRAWAL,
                        account.number, amount, new_balance,
                    )
                )
                print(f"New balance: {new_balance:.2f}")

        except ValidationError as e:
            # The amount the user typed was malformed or non-positive.
            print(e)
        except InsufficientFundsError as e:
            # The amount was valid but the balance is too low.
            # Handling this separately from ValidationError lets us give
            # a clearer message and (in a bigger app) route to different
            # recovery logic.
            print(e)


# The standard Python entry-point guard. `__name__` is "__main__" only
# when this file is run directly (`python main.py`); it's the module
# name (e.g. "main") when imported. So main() runs on direct execution
# but NOT on import — which is exactly what we want.
if __name__ == "__main__":
    main()
