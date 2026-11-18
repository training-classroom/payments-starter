from sqlalchemy import case, func, select
from sqlalchemy.orm import Session

from payments.models import Account, LedgerEntry


def get(session: Session, account_id: str) -> Account | None:
    return session.get(Account, account_id)


def list_all(session: Session) -> list[Account]:
    return list(session.scalars(select(Account).order_by(Account.id)))


def balance_minor(session: Session, account_id: str) -> int:
    """The account's balance: the sum of its credits minus the sum of its debits."""
    signed = case(
        (LedgerEntry.direction == "credit", LedgerEntry.amount_minor),
        else_=-LedgerEntry.amount_minor,
    )
    total = session.scalar(
        select(func.coalesce(func.sum(signed), 0)).where(LedgerEntry.account_id == account_id)
    )
    return int(total or 0)
