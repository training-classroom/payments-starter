# ADR 0002: Problem details for every error

**Status:** Accepted · 2025-02-03

## Context

Client teams parse our errors to decide whether to retry, ask the customer to fix something, or
escalate. With free-form error bodies they had to match on the message text.

## Decision

Every error response is `application/problem+json` (RFC 9457) with `type`, `title`, `status`,
`detail`, and a machine-readable `code`. `type` is `https://problems.payments.example/` plus the code
with hyphens. `api/errors.py` builds every error response; routers never build error bodies.

| Status | When |
|---|---|
| 400 | The request is malformed: body validation, a missing or invalid header |
| 404 | An account or payment doesn't exist |
| 409 | An idempotency key was reused for a different request |
| 422 | A well-formed payment broke a business rule; the payment is stored as `rejected` and the problem includes `payment_id` |

## Consequences

- A new rejection reason is a new code in `services/payment_rules.py` with a title in
  `REJECTION_TITLES`; the API needs no change.
- Clients can switch on `code` without parsing `detail`.
