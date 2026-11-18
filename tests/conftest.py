"""Shared fixtures.

Tests run against an in-memory SQLite database seeded with the synthetic accounts in
`payments.seed`, and a `FrozenClock` so every timestamp is predictable.
"""

from collections.abc import Iterator
from datetime import UTC, datetime

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from payments.config import Settings
from payments.main import create_app
from payments.services.payment_service import PaymentService
from tests.support import FrozenClock


@pytest.fixture
def clock() -> FrozenClock:
    return FrozenClock(datetime(2026, 3, 16, 14, 30, tzinfo=UTC))


@pytest.fixture
def settings() -> Settings:
    return Settings(database_url="sqlite://", seed_on_startup=True)


@pytest.fixture
def app(settings: Settings, clock: FrozenClock) -> FastAPI:
    return create_app(settings, clock)


@pytest.fixture
def client(app: FastAPI) -> Iterator[TestClient]:
    # Entering the client runs the lifespan, which creates the tables and seeds them.
    with TestClient(app) as test_client:
        yield test_client


@pytest.fixture
def session(client: TestClient, app: FastAPI) -> Iterator[Session]:
    with app.state.session_factory() as db_session:
        yield db_session


@pytest.fixture
def service(session: Session, settings: Settings, clock: FrozenClock) -> PaymentService:
    return PaymentService(session, settings, clock)
