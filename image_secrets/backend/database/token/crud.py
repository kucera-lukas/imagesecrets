"""CRUD operations with a Token."""
from __future__ import annotations

from typing import Optional

from tortoise.exceptions import DoesNotExist

from image_secrets.backend import password
from image_secrets.backend.database.token.models import Token
from image_secrets.backend.util.main import token_url


async def create(owner_id: int) -> str:
    """Create a new token and insert it's hash into database.

    :param owner_id: User foreign key

    """
    token = token_url()
    token_hash = password.hash_(token)
    await Token.create(token_hash=token_hash, owner_id=owner_id)
    return token


async def get_owner_id(token: str) -> int:
    """Return owner_id of a token.

    :param token: The token to check

    :raises DoesNotExist: if no token_hash matches the provided token

    """
    tokens = await Token.all().only("token_hash", "owner_id")
    gen = (t.owner_id for t in tokens if password.auth(token, t.token_hash))
    try:
        user_id = next(gen)
    except StopIteration as e:
        raise DoesNotExist(
            f"the token {token!r} does not match any token in database",
        ) from e
    return user_id