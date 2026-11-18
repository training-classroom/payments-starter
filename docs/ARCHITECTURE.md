# Payments Service Architecture

The Payments service moves money between customer accounts held at the bank. It accepts a payment
request, checks it against the account rules, posts it to a double-entry ledger, and records an audit
event. It runs as one FastAPI process with a relational database (SQLite locally and in tests).

## Layers

```
api/            HTTP: routers, request/response schemas, problem+json errors
  └── services/ business logic: rules, transactions, ledger postings, audit events
        └── repositories/   data access: queries and inserts, no rules
              └── models.py SQLAlchemy tables
```

- **`api/`** turns HTTP into service calls and service results into HTTP. It holds no rules.
- **`services/`** owns the transaction. `PaymentService.submit` is the only code that creates payments
  and ledger entries.
- **`repositories/`** hold queries. A repository never commits.
- **`domain/`** holds small types shared across layers: money formatting and the service errors.
- **`config.py`** reads settings from `PAYMENTS_*` environment variables, including the per-tier
  `TierPolicy`.
- **`clock.py`** is the only source of the current time (ADR 0004).

## Submitting a payment

`POST /payments` with an `Idempotency-Key` header and a JSON body:

1. The router validates the body (`schemas.PaymentCreate`) and calls `PaymentService.submit`.
2. The service looks up the idempotency key. Idempotency keys are unique across the whole service: a
   key that any account has used can't be used again by another account.
3. If the key was used before with the same body, the stored payment is returned as is. If the body
   differs, the request fails with 409.
4. The service loads both accounts, the debtor's balance, and the debtor's `TierPolicy`, and builds a
   `PaymentContext`.
5. `payment_rules.first_violation` runs the rules in `DEFAULT_RULES` order. The first violation wins.
6. A payment that passes is stored as `completed` and posted to the ledger: one debit on the debtor,
   one credit on the creditor. A payment that fails is stored as `rejected` with its rejection code
   and detail, and nothing is posted.
7. An audit event (`payment.completed` or `payment.rejected`) is added, and the transaction commits.

## Rules

Rules live in `services/payment_rules.py`. Each rule is a function that takes a `PaymentContext` and
returns a `RuleViolation` or `None`. Rules don't query the database; anything a rule needs is loaded
into the context first. Each rejection code has a title in `REJECTION_TITLES`.

| Order | Rule | Rejection code |
|---|---|---|
| 1 | Debtor and creditor differ | `same_account` |
| 2 | Both accounts are active | `account_not_active` |
| 3 | Both accounts hold the payment's currency | `currency_mismatch` |
| 4 | Amount is at most the tier's `max_payment_minor` | `amount_over_tier_maximum` |
| 5 | Amount is at most the debtor's balance | `insufficient_funds` |

## Data model

| Table | Holds |
|---|---|
| `accounts` | holder, currency, tier (`standard`, `premium`, `business`), status (`active`, `blocked`, `closed`) |
| `payments` | debtor, creditor, amount, currency, reference, status, rejection code and detail, idempotency key |
| `ledger_entries` | one row per side of a posting; the balance is credits minus debits |
| `audit_events` | who did what to which entity, and when |

Amounts are integers in minor units (ADR 0001). Timestamps are stored as UTC (ADR 0004).

## Errors

Every error response is `application/problem+json` (ADR 0002): 400 for malformed requests, 404 for
unknown accounts or payments, 409 for a reused idempotency key, and 422 for a payment a rule rejected.

## Audit

The service writes an audit event in the same transaction as every state change (ADR 0003).
`GET /audit-events` lists them, filtered by `entity_id` or `action`.

## Testing

Tests use an in-memory database seeded with the synthetic accounts in `seed.py`, and a `FrozenClock`.
`tests/test_conventions.py` checks the ADR rules that can be checked mechanically.

## Decisions

See [`docs/adr/`](adr/).
