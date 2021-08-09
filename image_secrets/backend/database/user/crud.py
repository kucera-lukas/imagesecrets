"""CRUD operations with a user in database."""
from __future__ import annotations

from typing import TYPE_CHECKING, NamedTuple

from tortoise.exceptions import DoesNotExist

from image_secrets.backend import password
from image_secrets.backend.database.user import models, schemas

if TYPE_CHECKING:
    from typing import Any, Optional, Union


class DBIdentifier(NamedTuple):
    """Identifier namedtuple for User in a database.

    :param column: Column of a known user value
    :param value: Value of the column

    """

    column: str
    value: Union[int, str]

    def to_dict(self) -> dict[str, Union[int, str]]:
        """Return column: value dictionary."""
        return {self.column: self.value}


async def get(identifier: DBIdentifier) -> Optional[models.User]:
    """Return User's model stored in a database.

    :param identifier: DBIdentifier to identify which user to return

    """
    return await models.User.get(**identifier.to_dict())


async def get_id(identifier: DBIdentifier) -> int:
    """Return User's database id.

    :param identifier: DBIdentifier to identify which user to return

    """
    result: models.User = await models.User.get(**identifier.to_dict()).only(
        "id",
    )
    return int(result.id)


async def create(user: schemas.UserCreate) -> models.User:
    """Insert a new user.

    :param user: The schema of the new user

    """
    hashed = password.hash_(user.password.get_secret_value())
    db_user = await models.User.create(
        **user.dict(exclude={"password"}),
        password_hash=hashed,
    )
    return db_user


async def delete(user_id: int) -> None:
    """Delete a user from database.

    :param user_id: User's database id

    """
    await models.User.filter(id=user_id).delete()


async def update(user_id: int, **attributes: Any) -> models.User:
    """Update user's credentials in the database.

    :param user_id: User's database id
    :param attributes: Keyword arguments with attributes to update

    """
    if pwd := attributes.get("password_hash"):
        hashed = password.hash_(pwd)
        attributes["password_hash"] = hashed
    await models.User.filter(id=user_id).update(**attributes)
    model = await get(DBIdentifier(column="id", value=user_id))
    assert isinstance(model, models.User)
    return model


async def authenticate(username: str, password_: str) -> bool:
    """Authenticate a user login.

    :param username: User's username
    :param password_: User's password

    """
    try:
        result: models.User = await models.User.get(username=username).only(
            "password_hash",
        )
    except DoesNotExist:
        return False
    return password.auth(password_, result.password_hash)
