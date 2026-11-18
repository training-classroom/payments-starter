# ADR 0001: Money in integer minor units

**Status:** Accepted · 2025-01-14

## Context

Binary floats can't represent most decimal amounts exactly, and decimal types invite rounding at
inconsistent points. Reconciliation with the core ledger requires amounts that match to the cent.

## Decision

Every amount is an `int` in the currency's minor units (cents for USD and EUR): in the API
(`amount_minor`), in the database, in configuration (`TierPolicy`), and in calculations. Amounts are
formatted for people only at the edge, with `domain.money.format_minor`.

## Consequences

- No float or decimal type holds an amount. `tests/test_conventions.py` checks this.
- Field and setting names that hold amounts end in `_minor`.
- Supporting a currency with a different number of decimal places would need a change to
  `format_minor`.
