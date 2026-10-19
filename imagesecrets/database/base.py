"""Base database module."""

from __future__ import annotations

import contextlib
from typing import TYPE_CHECKING

from sqlalchemy import Column, DateTime, Integer, func
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import declarative_base, declared_attr, sessionmaker

from imagesecrets.config import settings

if TYPE_CHECKING:
    from fastapi import FastAPI


class Base:
    """SQLAlchemy base class."""

    @declared_attr
    def __tablename__(cls) -> str:
        """Return database table name."""
        return cls.__name__.lower()

    @declared_attr
    def __mapper_args__(cls) -> dict[str, bool]:
        """Return mapper args dictionary."""
        return {"eager_defaults": True}

    id = Column(Integer, primary_key=True)

    created = Column(DateTime, server_default=func.now())
    updated = Column(
        DateTime,
        server_default=func.now(),
        server_onupdate=func.now(),
    )


Base = declarative_base(cls=Base)

engine = create_async_engine(settings.pg_dsn, future=True, echo=True)
async_sessionmaker = sessionmaker(
    engine,
    expire_on_commit=False,
    class_=AsyncSession,
)


@contextlib.asynccontextmanager
async def get_session() -> AsyncSession:
    """Return database session."""
    async with async_sessionmaker.begin() as session:
        yield session


def init(app: FastAPI) -> None:
    """Initialize SQLAlchemy on startup."""

    @app.on_event("startup")
    async def startup():
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
