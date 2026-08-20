"""
HTTP routes.

Each route is a thin adapter: parse the Pydantic request schema, build
the corresponding application DTO, call the service, and serialize the
result back into a Pydantic response schema. No business logic lives
here — that's the whole point of the layering.

The repository and services are constructed once in `app.py` and stored
in `app.state`; routes read them back via `request.app.state`. This
keeps route functions signature-simple while still using the same
repository instance across all requests.
"""

from fastapi import APIRouter, Request

from ...application.dto import AmountRequest, AuthRequest
from ...application.services import (
    CheckBalanceService,
    DepositService,
    TransactionHistoryService,
    WithdrawService,
)
from .schemas import (
    AmountBody,
    AuthBody,
    BalanceResponse,
    OperationResponse,
    TransactionHistoryResponse,
    TransactionItem,
)

router = APIRouter(prefix="/accounts/{account_number}", tags=["accounts"])


# Note: balance inquiry and transaction history are POST rather than GET
# because they require a PIN in the request body for authentication.
# GET-with-body is technically valid HTTP but widely discouraged (proxies
# strip it, httpx refuses it), and these are authenticated operations that
# we audit anyway — so POST is the more honest verb.
@router.post("/balance", response_model=BalanceResponse)
def get_balance(account_number: str, body: AuthBody, request: Request) -> BalanceResponse:
    service = CheckBalanceService(request.app.state.repository)
    result = service.execute(
        AuthRequest(account_number=account_number, pin=body.pin)
    )
    return BalanceResponse(
        account_number=result.account_number,
        holder=result.holder,
        balance=result.balance,
    )


@router.post("/deposit", response_model=OperationResponse)
def deposit(account_number: str, body: AmountBody, request: Request) -> OperationResponse:
    service = DepositService(request.app.state.repository)
    result = service.execute(
        AmountRequest(
            account_number=account_number, pin=body.pin, amount=body.amount
        )
    )
    return OperationResponse(
        account_number=result.account_number,
        new_balance=result.new_balance,
        transaction_id=result.transaction_id,
    )


@router.post("/withdraw", response_model=OperationResponse)
def withdraw(account_number: str, body: AmountBody, request: Request) -> OperationResponse:
    service = WithdrawService(request.app.state.repository)
    result = service.execute(
        AmountRequest(
            account_number=account_number, pin=body.pin, amount=body.amount
        )
    )
    return OperationResponse(
        account_number=result.account_number,
        new_balance=result.new_balance,
        transaction_id=result.transaction_id,
    )


@router.post("/transactions", response_model=TransactionHistoryResponse)
def list_transactions(
    account_number: str, body: AuthBody, request: Request
) -> TransactionHistoryResponse:
    service = TransactionHistoryService(request.app.state.repository)
    items = service.execute(
        AuthRequest(account_number=account_number, pin=body.pin)
    )
    return TransactionHistoryResponse(
        account_number=account_number,
        transactions=[
            TransactionItem(
                type=i.type,
                amount=i.amount,
                balance_after=i.balance_after,
                timestamp=i.timestamp,
            )
            for i in items
        ],
    )
