"""Database tables.

Timestamps use `UTCDateTime`: SQLite has no timezone-aware datetime type, so values are stored as
naive UTC and come back as aware UTC. Comparing a naive value with an aware one raises `TypeError`,
so nothing outside this module ever sees a naive datetime.
"""

from datetime import UTC, datetime
from typing import Any

from sqlalchemy import JSON, DateTime, ForeignKey, Integer, String, UniqueConstraint
from sqlalchemy.engine import Dialect
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.types import TypeDecorator

from payments.db import Base


class UTCDateTime(TypeDecorator[datetime]):
    impl = DateTime
    cache_ok = True

    def process_bind_param(self, value: datetime | None, dialect: Dialect) -> datetime | None:
        if value is None:
            return None
        if value.tzinfo is None:
            raise ValueError("Timestamps must be timezone-aware; use the injected Clock")
        return value.astimezone(UTC).replace(tzinfo=None)

    def process_result_value(self, value: datetime | None, dialect: Dialect) -> datetime | None:
        if value is None:
            return None
        return value.replace(tzinfo=UTC)


class Account(Base):
    __tablename__ = "accounts"

    id: Mapped[str] = mapped_column(String(20), primary_key=True)
    holder_name: Mapped[str] = mapped_column(String(100))
    currency: Mapped[str] = mapped_column(String(3))
    tier: Mapped[str] = mapped_column(String(20))
    # active | blocked | closed
    status: Mapped[str] = mapped_column(String(20))
    opened_at: Mapped[datetime] = mapped_column(UTCDateTime)


class Payment(Base):
    __tablename__ = "payments"
    __table_args__ = (
        UniqueConstraint("debtor_account_id", "idempotency_key", name="uq_payment_idempotency"),
    )

    id: Mapped[str] = mapped_column(String(40), primary_key=True)
    debtor_account_id: Mapped[str] = mapped_column(ForeignKey("accounts.id"))
    creditor_account_id: Mapped[str] = mapped_column(ForeignKey("accounts.id"))
    amount_minor: Mapped[int] = mapped_column(Integer)
    currency: Mapped[str] = mapped_column(String(3))
    reference: Mapped[str] = mapped_column(String(140))
    # completed | rejected
    status: Mapped[str] = mapped_column(String(20))
    rejection_code: Mapped[str | None] = mapped_column(String(40), default=None)
    rejection_detail: Mapped[str | None] = mapped_column(String(300), default=None)
    idempotency_key: Mapped[str] = mapped_column(String(100))
    created_at: Mapped[datetime] = mapped_column(UTCDateTime)


class LedgerEntry(Base):
    """One side of a double-entry posting. A completed payment posts a debit and a credit."""

    __tablename__ = "ledger_entries"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    account_id: Mapped[str] = mapped_column(ForeignKey("accounts.id"))
    payment_id: Mapped[str | None] = mapped_column(ForeignKey("payments.id"), default=None)
    # debit | credit
    direction: Mapped[str] = mapped_column(String(6))
    amount_minor: Mapped[int] = mapped_column(Integer)
    description: Mapped[str] = mapped_column(String(140))
    posted_at: Mapped[datetime] = mapped_column(UTCDateTime)


class AuditEvent(Base):
    __tablename__ = "audit_events"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    occurred_at: Mapped[datetime] = mapped_column(UTCDateTime)
    actor: Mapped[str] = mapped_column(String(100))
    action: Mapped[str] = mapped_column(String(60))
    entity_type: Mapped[str] = mapped_column(String(40))
    entity_id: Mapped[str] = mapped_column(String(40))
    details: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict)
