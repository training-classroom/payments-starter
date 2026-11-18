from sqlalchemy import select
from sqlalchemy.orm import Session

from payments.models import Payment


def get(session: Session, payment_id: str) -> Payment | None:
    return session.get(Payment, payment_id)


def find_by_idempotency_key(session: Session, debtor_account_id: str, key: str) -> Payment | None:
    """Find the payment a debtor already submitted with this key. Keys are scoped per debtor."""
    query = select(Payment).where(
        Payment.debtor_account_id == debtor_account_id, Payment.idempotency_key == key
    )
    return session.scalars(query).one_or_none()


def list_for_account(session: Session, account_id: str) -> list[Payment]:
    query = (
        select(Payment)
        .where(
            (Payment.debtor_account_id == account_id) | (Payment.creditor_account_id == account_id)
        )
        .order_by(Payment.created_at, Payment.id)
    )
    return list(session.scalars(query))
