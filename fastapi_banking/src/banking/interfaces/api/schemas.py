"""
Pydantic request/response schemas.

These are the wire-level shapes of the API. They are intentionally
separate from the application DTOs in `application/dto.py`:

  - DTOs are framework-agnostic and describe use-case inputs/outputs.
  - Schemas are Pydantic models that handle JSON parsing, validation,
    and OpenAPI documentation.

The routes layer converts between the two. Keeping them separate means
a future gRPC adapter could reuse the DTOs without dragging Pydantic
along.

Pydantic v2 validates the same constraints the domain layer enforces
(account number is 10 digits, PIN is 4 digits, amount is positive).
This duplicate validation is intentional: the API layer rejects
malformed requests before they reach the application services, and the
domain layer remains authoritative for any caller that bypasses the
HTTP edge (tests, a future CLI, etc.).
"""

from pydantic import BaseModel, Field, field_validator


class AuthBody(BaseModel):
    """Body for endpoints that only need authentication."""
    pin: str = Field(..., examples=["1234"])

    @field_validator("pin")
    @classmethod
    def _pin_format(cls, v: str) -> str:
        if len(v) != 4 or not v.isdigit():
            raise ValueError("PIN must be a 4-digit string.")
        return v


class AmountBody(AuthBody):
    """Body for endpoints that need auth + an amount to move."""
    amount: float = Field(..., gt=0, examples=[250.0])


class BalanceResponse(BaseModel):
    account_number: str
    holder: str
    balance: float


class OperationResponse(BaseModel):
    account_number: str
    new_balance: float
    transaction_id: int | None = None


class TransactionItem(BaseModel):
    type: str
    amount: float
    balance_after: float
    timestamp: str


class TransactionHistoryResponse(BaseModel):
    account_number: str
    transactions: list[TransactionItem]


class ErrorResponse(BaseModel):
    """Standard error envelope returned by the error handlers."""
    error: str
    detail: str | None = None
