"""
End-to-end API tests via FastAPI's TestClient.

These hit the real HTTP surface against a temp SQLite file. They verify
that the whole stack (Pydantic schemas -> routes -> services -> repo ->
ORM -> SQLite) works together and that domain exceptions map to the
right HTTP status codes.
"""

import pytest

from banking.infrastructure.seed import SEED_ACCOUNTS


# --- Health ----------------------------------------------------------


def test_health_endpoint(api_client):
    resp = api_client.get("/health")
    assert resp.status_code == 200
    assert resp.json() == {"status": "ok"}


# --- Seed data is present on startup --------------------------------


def test_seed_accounts_loaded(api_client):
    # A correct PIN against a seeded account should succeed.
    resp = api_client.post(
        "/accounts/1234567890/balance", json={"pin": "1234"}
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["account_number"] == "1234567890"
    assert body["holder"] == "John Doe"
    assert body["balance"] == 1000.0


# --- Balance ---------------------------------------------------------


def test_balance_wrong_pin_returns_401(api_client):
    resp = api_client.post(
        "/accounts/1234567890/balance", json={"pin": "0000"}
    )
    assert resp.status_code == 401
    assert resp.json()["error"] == "incorrect_pin"


def test_balance_unknown_account_returns_404(api_client):
    resp = api_client.post(
        "/accounts/0000000000/balance", json={"pin": "1234"}
    )
    assert resp.status_code == 404
    assert resp.json()["error"] == "account_not_found"


def test_balance_bad_pin_format_returns_422(api_client):
    # Pydantic rejects a non-4-digit PIN before the request reaches the
    # service. FastAPI returns 422 for body validation failures.
    resp = api_client.post(
        "/accounts/1234567890/balance", json={"pin": "12"}
    )
    assert resp.status_code == 422


# --- Deposit ---------------------------------------------------------


def test_deposit_increases_balance(api_client):
    resp = api_client.post(
        "/accounts/1234567890/deposit",
        json={"pin": "1234", "amount": 250.0},
    )
    assert resp.status_code == 200
    assert resp.json()["new_balance"] == 1250.0

    # Verify persistence: a fresh balance request sees the new value.
    balance = api_client.post(
        "/accounts/1234567890/balance", json={"pin": "1234"}
    )
    assert balance.json()["balance"] == 1250.0


def test_deposit_non_positive_amount_returns_422(api_client):
    resp = api_client.post(
        "/accounts/1234567890/deposit",
        json={"pin": "1234", "amount": -10.0},
    )
    assert resp.status_code == 422  # Pydantic Field(gt=0)


# --- Withdraw --------------------------------------------------------


def test_withdraw_decreases_balance(api_client):
    resp = api_client.post(
        "/accounts/1234567890/withdraw",
        json={"pin": "1234", "amount": 300.0},
    )
    assert resp.status_code == 200
    assert resp.json()["new_balance"] == 700.0


def test_withdraw_too_much_returns_409(api_client):
    resp = api_client.post(
        "/accounts/1234567890/withdraw",
        json={"pin": "1234", "amount": 10_000.0},
    )
    assert resp.status_code == 409
    assert resp.json()["error"] == "insufficient_funds"


# --- Transactions ----------------------------------------------------


def test_transaction_history_lists_operations_in_order(api_client):
    api_client.post(
        "/accounts/1234567890/deposit", json={"pin": "1234", "amount": 100.0}
    )
    api_client.post(
        "/accounts/1234567890/withdraw", json={"pin": "1234", "amount": 50.0}
    )
    # Plus the balance inquiry below will be recorded too.
    api_client.post(
        "/accounts/1234567890/balance", json={"pin": "1234"}
    )

    resp = api_client.post(
        "/accounts/1234567890/transactions", json={"pin": "1234"}
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["account_number"] == "1234567890"
    types = [t["type"] for t in body["transactions"]]
    assert types == ["deposit", "withdrawal", "balance_inquiry"]
