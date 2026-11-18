# ADR 0004: An injected UTC clock

**Status:** Accepted · 2025-03-11

## Context

Timestamps were hard to test when code called `datetime.now()` directly, and naive datetimes mixed
with aware ones raised `TypeError` at run time.

## Decision

- `clock.Clock` is the only source of the current time. `create_app` takes a clock; services receive
  it. Production uses `SystemClock`; tests use `FrozenClock` from `tests/support.py`.
- Every datetime in the service is timezone-aware **UTC**. `models.UTCDateTime` stores UTC and
  returns aware values.

## Consequences

- No code outside `clock.py` calls `datetime.now()`, `datetime.utcnow()`, `date.today()`, or
  `time.time()`. `tests/test_conventions.py` checks this.
- Tests set the time explicitly and can move it with `FrozenClock.advance`.
