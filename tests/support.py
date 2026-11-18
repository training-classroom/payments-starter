"""Test helpers shared by the test modules."""

from datetime import datetime, timedelta
from typing import Any


class FrozenClock:
    """A clock that only moves when a test moves it."""

    def __init__(self, at: datetime) -> None:
        if at.tzinfo is None:
            raise ValueError("FrozenClock needs a timezone-aware datetime")
        self._now = at

    def now(self) -> datetime:
        return self._now

    def set(self, at: datetime) -> None:
        self._now = at

    def advance(self, delta: timedelta) -> None:
        self._now += delta


def payment_body(**overrides: Any) -> dict[str, Any]:
    """A valid payment from ACC-1001 (standard tier) to ACC-1002, both USD."""
    body: dict[str, Any] = {
        "debtor_account_id": "ACC-1001",
        "creditor_account_id": "ACC-1002",
        "amount_minor": 10_000,
        "currency": "USD",
        "reference": "Invoice 0001",
    }
    body.update(overrides)
    return body
