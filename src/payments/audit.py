"""The audit trail.

Every state change records an audit event in the same transaction as the change itself, so the
trail can't miss a change or record one that rolled back
(see docs/adr/0003-audit-every-state-change.md).
"""

from datetime import datetime
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from payments.models import AuditEvent


def record(
    session: Session,
    *,
    occurred_at: datetime,
    actor: str,
    action: str,
    entity_type: str,
    entity_id: str,
    details: dict[str, Any] | None = None,
) -> AuditEvent:
    """Add an audit event to the session. The caller commits it with the change it describes."""
    event = AuditEvent(
        occurred_at=occurred_at,
        actor=actor,
        action=action,
        entity_type=entity_type,
        entity_id=entity_id,
        details=details or {},
    )
    session.add(event)
    return event


def list_events(
    session: Session, *, entity_id: str | None = None, action: str | None = None
) -> list[AuditEvent]:
    query = select(AuditEvent).order_by(AuditEvent.id)
    if entity_id is not None:
        query = query.where(AuditEvent.entity_id == entity_id)
    if action is not None:
        query = query.where(AuditEvent.action == action)
    return list(session.scalars(query))
