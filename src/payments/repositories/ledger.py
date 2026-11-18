from datetime import datetime

from sqlalchemy import select
from sqlalchemy.orm import Session

from payments.models import LedgerEntry


def post_transfer(
    session: Session,
    *,
    payment_id: str,
    debtor_account_id: str,
    creditor_account_id: str,
    amount_minor: int,
    description: str,
    posted_at: datetime,
) -> None:
    """Post both sides of a transfer. Debits and credits always balance."""
    session.add_all(
        [
            LedgerEntry(
                account_id=debtor_account_id,
                payment_id=payment_id,
                direction="debit",
                amount_minor=amount_minor,
                description=description,
                posted_at=posted_at,
            ),
            LedgerEntry(
                account_id=creditor_account_id,
                payment_id=payment_id,
                direction="credit",
                amount_minor=amount_minor,
                description=description,
                posted_at=posted_at,
            ),
        ]
    )


def entries_for_account(session: Session, account_id: str) -> list[LedgerEntry]:
    query = (
        select(LedgerEntry)
        .where(LedgerEntry.account_id == account_id)
        .order_by(LedgerEntry.posted_at, LedgerEntry.id)
    )
    return list(session.scalars(query))
