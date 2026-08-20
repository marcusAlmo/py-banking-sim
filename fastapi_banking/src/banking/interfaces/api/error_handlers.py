"""
Domain-exception -> HTTP-response mapping.

This is where the typed exception hierarchy pays off. Each domain
error becomes a specific HTTP status code with a meaningful body,
instead of every failure collapsing into a generic 500.

Mapping table:
  ValidationError          -> 400 Bad Request
  AccountNotFoundError    -> 404 Not Found
  IncorrectPinError       -> 401 Unauthorized
  InsufficientFundsError  -> 409 Conflict
  BankingError (fallback) -> 500 Internal Server Error

Anything that isn't a BankingError is *not* handled here — FastAPI's
default 500 response applies, which is what we want for genuine bugs.
"""

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from ...domain.exceptions import (
    AccountNotFoundError,
    BankingError,
    IncorrectPinError,
    InsufficientFundsError,
    ValidationError,
)
from .schemas import ErrorResponse


def register_error_handlers(app: FastAPI) -> None:
    """Attach all domain-exception handlers to `app`."""

    @app.exception_handler(ValidationError)
    async def _validation(req: Request, exc: ValidationError) -> JSONResponse:
        return JSONResponse(
            status_code=400,
            content=ErrorResponse(error="validation_error", detail=str(exc)).model_dump(),
        )

    @app.exception_handler(AccountNotFoundError)
    async def _not_found(req: Request, exc: AccountNotFoundError) -> JSONResponse:
        return JSONResponse(
            status_code=404,
            content=ErrorResponse(error="account_not_found", detail=str(exc)).model_dump(),
        )

    @app.exception_handler(IncorrectPinError)
    async def _bad_pin(req: Request, exc: IncorrectPinError) -> JSONResponse:
        return JSONResponse(
            status_code=401,
            content=ErrorResponse(error="incorrect_pin", detail=str(exc)).model_dump(),
        )

    @app.exception_handler(InsufficientFundsError)
    async def _insufficient(req: Request, exc: InsufficientFundsError) -> JSONResponse:
        return JSONResponse(
            status_code=409,
            content=ErrorResponse(error="insufficient_funds", detail=str(exc)).model_dump(),
        )

    @app.exception_handler(BankingError)
    async def _fallback(req: Request, exc: BankingError) -> JSONResponse:
        # Catch-all for any future BankingError subclass we forget to
        # map explicitly. Better than a bare 500 because it still
        # surfaces the domain message.
        return JSONResponse(
            status_code=500,
            content=ErrorResponse(error="banking_error", detail=str(exc)).model_dump(),
        )
