# fastapi-banking

A FastAPI rewrite of the parent project's REPL banking simulator, structured
according to **Domain-Driven Design** layering.

## Why this exists

The original `py-banking-sim` is a CLI/REPL app. Its `main.py` already
separates the UI from the domain (`Bank`, `Account`), but everything is
in-memory and the only interface is `input()`/`print()`. This rewrite shows
what the same domain looks like behind an HTTP API, with real persistence,
and with the seams DDD recommends made explicit.

## Layering

```
src/banking/
├── domain/            # Pure business objects. No FastAPI, no SQLAlchemy.
│   ├── account.py         Account entity (rules live here)
│   ├── transaction.py     Transaction record + TransactionType enum
│   ├── exceptions.py      BankingError hierarchy (mirrors ../exceptions.py)
│   └── repositories.py    AccountRepository Protocol (the PORT)
├── application/       # Use cases. Orchestrates domain + repositories.
│   ├── services.py        DepositService, WithdrawService, ...
│   └── dto.py             Plain dataclasses for service inputs/outputs
├── infrastructure/    # Technical concerns: DB, ORM, repo implementations.
│   ├── orm.py             SQLAlchemy models (AccountModel, TransactionModel)
│   ├── database.py        engine + session factory
│   ├── account_repository.py   SQLAlchemy impl of domain.AccountRepository
│   └── seed.py            Demo data
└── interfaces/api/    # Inbound adapters: the HTTP surface.
    ├── app.py             FastAPI app factory + lifespan (creates tables)
    ├── routes.py          endpoints
    ├── schemas.py         Pydantic request/response models
    └── error_handlers.py  map domain exceptions -> HTTP responses
```

### Dependency rule

Dependencies point **inward**. `domain` imports nothing from the outer
layers. `application` imports `domain` only. `infrastructure` implements
the ports `domain` defines. `interfaces/api` calls `application` services
and never touches `domain` invariants directly.

## Running

```bash
cd fastapi_banking
python -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"
uvicorn banking.interfaces.api.app:app --reload
```

The API is then served at http://127.0.0.1:8000 with interactive docs at
`/docs`.

### Seed accounts

On startup the app creates three demo accounts (same numbers/PINs as the
REPL version):

| Account number | Holder       | PIN  | Balance |
|----------------|--------------|------|---------|
| 1234567890     | John Doe     | 1234 | 1000.00 |
| 0987654321     | Jane Smith   | 5678 | 1500.00 |
| 1111222233     | Bob Johnson  | 9012 | 2000.00 |

## Endpoints

Auth is per-request: send `account_number` and `pin` in the JSON body.

```bash
# Check balance (POST because it requires a PIN in the body)
curl -s -X POST localhost:8000/accounts/1234567890/balance \
  -H 'Content-Type: application/json' \
  -d '{"pin":"1234"}'

# Deposit
curl -s -X POST localhost:8000/accounts/1234567890/deposit \
  -H 'Content-Type: application/json' \
  -d '{"pin":"1234","amount":250.00}'

# Withdraw
curl -s -X POST localhost:8000/accounts/1234567890/withdraw \
  -H 'Content-Type: application/json' \
  -d '{"pin":"1234","amount":100.00}'

# Transaction history
curl -s -X POST localhost:8000/accounts/1234567890/transactions \
  -H 'Content-Type: application/json' \
  -d '{"pin":"1234"}'
```

## Tests

```bash
pytest
```

`tests/` exercises each layer in isolation:

- `test_domain.py` — Account rules with no DB, no HTTP.
- `test_application.py` — use cases against a fake in-memory repository.
- `test_api.py` — end-to-end via FastAPI's `TestClient` against a temp SQLite file.
