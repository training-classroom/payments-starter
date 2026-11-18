"""Application factory. Run locally with `uv run fastapi dev src/payments/main.py`."""

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI

from payments.api import accounts, audit_events, health, payments
from payments.api.errors import install_error_handlers
from payments.clock import Clock, SystemClock
from payments.config import Settings
from payments.db import Base, make_engine, make_session_factory
from payments.seed import seed


def create_app(settings: Settings | None = None, clock: Clock | None = None) -> FastAPI:
    settings = settings or Settings()
    engine = make_engine(settings.database_url)
    session_factory = make_session_factory(engine)

    @asynccontextmanager
    async def lifespan(app: FastAPI) -> AsyncIterator[None]:
        Base.metadata.create_all(engine)
        if settings.seed_on_startup:
            with session_factory() as session:
                seed(session)
        yield
        engine.dispose()

    app = FastAPI(title="Payments Service", version="1.4.0", lifespan=lifespan)
    app.state.settings = settings
    app.state.session_factory = session_factory
    app.state.clock = clock or SystemClock()

    install_error_handlers(app)
    app.include_router(health.router)
    app.include_router(accounts.router)
    app.include_router(payments.router)
    app.include_router(audit_events.router)
    return app


app = create_app()
