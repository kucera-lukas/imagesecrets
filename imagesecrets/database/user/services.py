"""Database services for User model."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, NamedTuple, Union

from sqlalchemy import delete, select, update
from sqlalchemy.orm import selectinload
from sqlalchemy.orm.attributes import InstrumentedAttribute

from imagesecrets.core import password
from imagesecrets.database.service import DatabaseService
from imagesecrets.database.user.models import User
from imagesecrets.schemas.user import UserCreate

if TYPE_CHECKING:
    from sqlalchemy.sql.elements import BinaryExpression


class DBIdentifier(NamedTuple):
    """Identifier namedtuple for User in a database.

    :param column: Column of a known user value
    :param value: Value of the column

    """

    column: Union[str, InstrumentedAttribute]
    value: Union[int, str]

    def to_sqlalchemy(self) -> BinaryExpression:
        """Return sqlalchemy representation of this identifier."""
        column = (
            self.column
            if isinstance(self.column, InstrumentedAttribute)
            else getattr(User, self.column)
        )

        return column == self.value


class UserService(DatabaseService):
    """Database service for User model."""

    async def get(
        self,
        identifier: DBIdentifier,
        relationships: tuple[InstrumentedAttribute] = (
            User.decoded_images,
            User.encoded_images,
        ),
    ) -> User:
        """Return User's model stored in a database.

        :param identifier: DBIdentifier to identify which user to return
        :param relationships: User model relationships to select from database

        """
        stmt = (
            select(User)
            .options(
                *[
                    selectinload(relationship)
                    for relationship in relationships
                ],
            )
            .where(identifier.to_sqlalchemy())
            .limit(1)
        )

        result = await self._session.execute(statement=stmt)

        return result.scalar_one()

    async def get_id(self, identifier: DBIdentifier) -> int:
        """Return User's database id.

        :param identifier: DBIdentifier to identify which user to return

        """
        stmt = select(User.id).where(identifier.to_sqlalchemy()).limit(1)

        result = await self._session.execute(statement=stmt)

        return result.scalar_one()

    async def create(self, user: UserCreate) -> User:
        """Insert a new user.

        :param user: The schema of the new user

        """
        hashed = password.hash_(user.password.get_secret_value())

        db_user = User(
            **user.dict(exclude={"password"}),
            password_hash=hashed,
            decoded_images=[],
            encoded_images=[],
        )

        async with self._session.begin_nested():
            self._session.add(db_user)

        return db_user

    async def delete(self, user_id: int) -> None:
        """Delete a user from database.

        :param user_id: User's database id

        """
        stmt = delete(User).where(User.id == user_id)

        await self._session.execute(statement=stmt)

    async def update(self, user_id: int, **attributes: Any) -> User:
        """Update user's credentials in the database.

        :param user_id: User's database id
        :param attributes: Keyword arguments with attributes to update

        """
        if pwd := attributes.get("password_hash"):
            hashed = password.hash_(pwd)
            attributes["password_hash"] = hashed

        stmt = update(User).where(User.id == user_id).values(**attributes)

        await self._session.execute(statement=stmt)

        return await self.get(DBIdentifier(column=User.id, value=user_id))

    async def authenticate(self, username: str, password_: str) -> bool:
        """Authenticate a user login.

        :param username: User's username
        :param password_: User's password

        """
        stmt = (
            select(User.password_hash)
            .where(User.username == username)
            .limit(1)
        )

        result = await self._session.execute(statement=stmt)

        hashed = result.scalar_one_or_none()
        if not hashed:
            return False

        return password.auth(
            plain=password_,
            hashed=hashed,
        )
