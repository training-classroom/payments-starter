# ADR 0003: Audit every state change

**Status:** Accepted · 2025-02-20

## Context

Internal audit and the regulator expect to reconstruct who changed what, and when, for every payment,
including the ones we refused.

## Decision

Every state change, including a rejection, adds an `AuditEvent` through `audit.record` in the **same
transaction** as the change. The service layer records the event; routers and repositories don't. An
event holds the time (from the injected clock), the actor (`X-Actor`, set by the API gateway), the
action (`<entity>.<past-tense verb>`, for example `payment.rejected`), the entity, and a small
`details` object with no personal data beyond identifiers.

## Consequences

- A rollback removes the change and its event together.
- A replayed request changes nothing, so it records nothing.
- New actions follow the `<entity>.<verb>` naming and are covered by a test.
