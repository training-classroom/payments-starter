"""Engine and session setup."""

from sqlalchemy import Engine, create_engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker
from sqlalchemy.pool import StaticPool


class Base(DeclarativeBase):
    pass


def make_engine(database_url: str) -> Engine:
    """Create the engine for a database URL.

    An in-memory SQLite database (`sqlite://`) lives only as long as its connection, so it gets a
    single shared connection; the tests rely on that.
    """
    if database_url.startswith("sqlite"):
        connect_args = {"check_same_thread": False}
        if database_url in ("sqlite://", "sqlite:///:memory:"):
            return create_engine(database_url, connect_args=connect_args, poolclass=StaticPool)
        return create_engine(database_url, connect_args=connect_args)
    return create_engine(database_url)


def make_session_factory(engine: Engine) -> sessionmaker[Session]:
    return sessionmaker(bind=engine, expire_on_commit=False)
