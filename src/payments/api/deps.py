"""FastAPI dependencies. Everything comes from `app.state`, which `create_app` fills."""

from collections.abc import Iterator
from typing import Annotated

from fastapi import Depends, Header, Request
from sqlalchemy.orm import Session

from payments.clock import Clock
from payments.config import Settings
from payments.services.payment_service import PaymentService


def get_session(request: Request) -> Iterator[Session]:
    session = request.app.state.session_factory()
    try:
        yield session
    finally:
        session.close()


def get_settings(request: Request) -> Settings:
    return request.app.state.settings


def get_clock(request: Request) -> Clock:
    return request.app.state.clock


def get_actor(x_actor: Annotated[str | None, Header(max_length=100)] = None) -> str:
    """Who is calling, for the audit trail. The API gateway sets `X-Actor` in production."""
    return x_actor or "unknown"


SessionDep = Annotated[Session, Depends(get_session)]
SettingsDep = Annotated[Settings, Depends(get_settings)]
ClockDep = Annotated[Clock, Depends(get_clock)]
ActorDep = Annotated[str, Depends(get_actor)]


def get_payment_service(
    session: SessionDep, settings: SettingsDep, clock: ClockDep
) -> PaymentService:
    return PaymentService(session, settings, clock)


PaymentServiceDep = Annotated[PaymentService, Depends(get_payment_service)]
