# Payments Service

Account-to-account payments for the bank's customer accounts: an idempotent payments API, a
double-entry ledger, per-tier payment rules, and an audit trail of every state change.

## Requirements

- Python 3.14 and [uv](https://docs.astral.sh/uv/) (uv installs the Python version in
  `.python-version` when it's missing)
- Git

## Set up

```powershell
uv sync
```

`uv sync` creates `.venv`, installs the locked dependencies from `uv.lock`, and installs the service
itself in editable mode.

## Run the tests and checks

```powershell
uv run pytest
uv run ruff check
uv run ruff format --check
uv run python scripts/check_dependencies.py
```

The same checks run in CI on every pull request (`.github/workflows/ci.yml`).

## Run the service

```powershell
uv run fastapi dev src/payments/main.py
```

The API docs are at http://127.0.0.1:8000/docs. On first start the service creates `payments.db` and
seeds it with synthetic accounts (`src/payments/seed.py`). Delete the file to start over.

Submit a payment:

```powershell
$body = '{"debtor_account_id":"ACC-1001","creditor_account_id":"ACC-1002","amount_minor":12500,"currency":"USD","reference":"Invoice 0001"}'
Invoke-RestMethod -Method Post -Uri http://127.0.0.1:8000/payments `
  -Headers @{ "Idempotency-Key" = "inv-0001"; "X-Actor" = "teller-17" } `
  -ContentType "application/json" -Body $body
```

## Configuration

Settings come from environment variables prefixed with `PAYMENTS_` (`src/payments/config.py`):

| Variable | Default |
|---|---|
| `PAYMENTS_DATABASE_URL` | `sqlite:///./payments.db` |
| `PAYMENTS_SEED_ON_STARTUP` | `true` |
| `PAYMENTS_TIERS` | JSON object with every tier and its limits in minor units; defaults in `config.py` (`max_payment_minor`: standard 250000, premium 1000000, business 5000000) |

## Project layout

See [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) and the decisions in [docs/adr/](docs/adr/).

## Dependencies

Every direct dependency must be listed in `dependency-policy.toml` with its license and approval
reference. `scripts/check_dependencies.py` fails the build when one isn't.

## Contributing

Open a pull request against `main` using the template. Every change needs a linked change request,
tests, and an approving review.
