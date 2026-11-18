"""Synthetic seed data for local runs and tests.

Every name and identifier here is invented. No real customer, account number, or bank identifier
may appear in this repository, in tests, or in prompts.
"""

from datetime import UTC, datetime

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from payments.models import Account, LedgerEntry

# (id, holder name, currency, tier, status, opening balance in minor units)
SEED_ACCOUNTS: tuple[tuple[str, str, str, str, str, int], ...] = (
    ("ACC-1001", "Synthetic Customer 01", "USD", "standard", "active", 1_200_000),
    ("ACC-1002", "Synthetic Customer 02", "USD", "standard", "active", 300_000),
    ("ACC-1003", "Synthetic Customer 03", "USD", "premium", "active", 5_000_000),
    ("ACC-1004", "Synthetic Business 04", "USD", "business", "active", 20_000_000),
    ("ACC-1005", "Synthetic Customer 05", "EUR", "standard", "active", 400_000),
    ("ACC-1006", "Synthetic Customer 06", "USD", "standard", "blocked", 100_000),
)

OPENED_AT = datetime(2025, 1, 6, 9, 0, tzinfo=UTC)


def seed(session: Session) -> None:
    """Insert the seed accounts and their opening balances into an empty database."""
    if session.scalar(select(func.count()).select_from(Account)):
        return
    for account_id, holder, currency, tier, status, opening_minor in SEED_ACCOUNTS:
        session.add(
            Account(
                id=account_id,
                holder_name=holder,
                currency=currency,
                tier=tier,
                status=status,
                opened_at=OPENED_AT,
            )
        )
        session.add(
            LedgerEntry(
                account_id=account_id,
                payment_id=None,
                direction="credit",
                amount_minor=opening_minor,
                description="Opening balance (migrated)",
                posted_at=OPENED_AT,
            )
        )
    session.commit()
