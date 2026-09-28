"""Database service."""

from __future__ import annotations

from typing import TYPE_CHECKING, AsyncGenerator, Type, TypeVar

from imagesecrets.database import base

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncSession


_T = TypeVar("_T")


class DatabaseService:
    """Base database service class."""

    def __init__(self, session: AsyncSession):
        """Construct the class."""
        self._session = session

    @classmethod
    async def from_session(cls: Type[_T]) -> AsyncGenerator[_T]:
        """Return ``DatabaseService`` instance from new database session."""

        async with base.get_session() as session:
            yield cls(session=session)
