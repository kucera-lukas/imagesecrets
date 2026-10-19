"""Database services for Token model."""

from __future__ import annotations

from datetime import datetime, timedelta

from sqlalchemy import delete, select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.exc import NoReferenceError

from imagesecrets.core import password
from imagesecrets.core.util import main
from imagesecrets.database.service import DatabaseService
from imagesecrets.database.token.models import Token


class TokenService(DatabaseService):
    """Database service for Token model."""

    @staticmethod
    def create_token() -> tuple[str, str]:
        """Create a new token."""
        token = main.token_url()
        token_hash = password.hash_(token)
        return token, token_hash

    async def delete(self, user_id: int) -> None:
        """Delete a token from database.

        :param user_id: User database id

        """
        stmt = delete(Token).where(Token.user_id == user_id)

        await self._session.execute(statement=stmt)

    async def create(self, user_id: int, token_hash: str) -> None:
        """Insert a new token into the database.

        If a token already exists, update the ``token_hash`` column

        :param user_id: User foreign key
        :param token_hash: The new hashed token

        """
        stmt = insert(Token).values(user_id=user_id, token_hash=token_hash)
        stmt.on_conflict_do_update(
            constraint="user_id",
            set_=dict(token_hash=token_hash),
        )

        await self._session.execute(statement=stmt)

    async def get_user_id(self, token: str) -> int:
        """Return User database id of a token.

        :param token: The token to check

        :raises DoesNotExist: if no token_hash matches the provided token

        """
        stmt = select(Token.user_id, Token.token_hash)

        async_result = await self._session.stream(stmt)

        async for db_token in async_result:
            if password.auth(token, db_token[1]):
                result = db_token[0]
                break
        else:
            raise NoReferenceError(
                f"the token {token!r} does not match any token in database",
            )

        return result

    async def clear(self) -> None:
        """Clear all expired tokens in database."""
        stmt = delete(Token).where(
            Token.created <= (datetime.now() - timedelta(minutes=10)),
        )

        await self._session.execute(statement=stmt)
