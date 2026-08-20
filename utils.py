"""
Input validators for raw user input from the REPL.

THE VALIDATOR'S JOB
-------------------
A validator sits at the BOUNDARY between the untrusted outside world
(the user typing at a keyboard) and the trusted inside of the program.
Its only job is to answer: "is this string well-formed enough to hand
to the domain layer?"

Validators deliberately know nothing about banking rules. They don't
check whether an account exists or whether there are enough funds —
that's the job of Account and Bank. They only check FORMAT:
  - is it the right length?
  - is it all digits?
  - does it parse as a positive number?

Returning the parsed/normalized value (instead of None) lets the caller
chain the validator inline:
    pin = pin_validator(input("PIN: "))
Without the return, the caller would have to keep the original string
around separately, which is error-prone.

WHY ValidationError INSTEAD OF ValueError?
------------------------------------------
Using our own ValidationError (defined in exceptions.py) means the UI
layer can catch *only* input-format problems and re-prompt, while
letting genuinely unexpected errors (a bug in Account, a missing file)
propagate as real exceptions instead of being silently treated as
"the user typed something wrong."
"""

from exceptions import ValidationError


def account_number_validator(account_number: str) -> str:
    """
    Validate that `account_number` is a 10-digit string.
    Returns the validated string. Raises ValidationError otherwise.
    """
    # `len(x) < 10 or len(x) > 10` is just `len(x) != 10`; the original
    # code's verbose form is simplified here. Readable code is better
    # than clever code, but unnecessarily verbose code isn't more
    # readable — it just takes longer to read.
    if len(account_number) != 10 or not account_number.isdigit():
        raise ValidationError("Invalid account number. It must be a 10-digit number.")
    return account_number


def pin_validator(pin: str) -> str:
    """
    Validate that `pin` is a 4-digit string.
    Returns the validated string. Raises ValidationError otherwise.
    """
    if len(pin) != 4 or not pin.isdigit():
        raise ValidationError("Invalid PIN. It must be a 4-digit number.")
    return pin


def amount_validator(amount: str) -> float:
    """
    Validate that `amount` parses as a positive number.
    Returns the parsed float. Raises ValidationError otherwise.

    Note the two-stage structure: we first try to PARSE (could fail with
    a ValueError from float()), then check the BUSINESS constraint
    (must be positive). Keeping these separate means the error message
    can tell the user exactly which problem they hit, instead of a
    generic "invalid amount" that covers both.
    """
    try:
        parsed = float(amount)
    except ValueError:
        raise ValidationError("Invalid amount. Please enter a valid number.")
    if parsed <= 0:
        raise ValidationError("Amount must be a positive number.")
    return parsed
