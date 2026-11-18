"""The service's source of the current time.

Every timestamp the service records comes from a `Clock` (see docs/adr/0004-injected-utc-clock.md).
Service and domain code never call `datetime.now()` directly, so tests can pin time and every
timestamp is timezone-aware UTC.
"""

from datetime import UTC, datetime
from typing import Protocol


class Clock(Protocol):
    def now(self) -> datetime:
        """Return the current time as a timezone-aware UTC datetime."""
        ...


class SystemClock:
    """The production clock: the host's current time, in UTC."""

    def now(self) -> datetime:
        return datetime.now(UTC)
