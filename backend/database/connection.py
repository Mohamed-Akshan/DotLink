from typing import Iterator
from sqlalchemy.orm import Session
from sqlalchemy import create_engine, event
from sqlalchemy.orm import declarative_base, sessionmaker
from core.config import settings

Base = declarative_base()

engine = create_engine(settings.database_url, pool_pre_ping=True)

if settings.database_url.startswith("sqlite"):

    @event.listens_for(engine, "connect")
    def configure_sqlite(connection, record) -> None:
        """Enable foreign keys and explicit transaction handling in local tests."""

        connection.isolation_level = None
        connection.execute("PRAGMA foreign_keys=ON")

        return None

    @event.listens_for(engine, "begin")
    def begin_sqlite(connection) -> None:
        """Start a real transaction before nested savepoints."""

        connection.exec_driver_sql("BEGIN")

        return None


SessionLocal = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)


def get_db() -> Iterator[Session]:
    """Provide one database session per API request."""

    with SessionLocal() as db:

        yield db
