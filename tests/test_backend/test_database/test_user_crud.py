"""Test the CRUD module for users."""
from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

from image_secrets.backend.database.user import crud

if TYPE_CHECKING:
    from unittest.mock import AsyncMock

    from pytest_mock import MockFixture

    from image_secrets.backend.database.user.models import User


@pytest.fixture()
def user() -> User:
    """Return an user."""
    from image_secrets.backend.database.user import models

    return models.User(
        username="test_username",
        email="test_email@test.conm",
        password_hash="test_hash",
    )


@pytest.fixture()
def mock_create(mocker: MockFixture, user: User):
    """Return mocked User.create function."""
    async_mock = mocker.AsyncMock(return_value=user)
    return mocker.patch(
        "image_secrets.backend.database.user.models.User.create",
        side_effect=async_mock,
    )


@pytest.fixture()
def mock_get(mocker: MockFixture, user: User):
    """Return mocker User.get function."""
    async_mock = mocker.AsyncMock(return_value=user)
    return mocker.patch(
        "image_secrets.backend.database.user.models.User.get",
        side_effect=async_mock,
    )


@pytest.mark.asyncio
async def test_get(mock_get, user: User) -> None:
    """Test successful get function call."""
    identifier = crud.DBIdentifier(column="username", value=user.username)

    result = await crud.get(identifier)

    mock_get.assert_called_once_with(username=user.username)
    assert result == user


@pytest.mark.asyncio
async def test_get_id(insert_user: User) -> None:
    """Test successful get_id function call."""
    identifier = crud.DBIdentifier(
        column="username",
        value=insert_user.username,
    )

    result = await crud.get_id(identifier)

    assert result == insert_user.id


@pytest.mark.asyncio
async def test_create(
    mocker: MockFixture,
    mock_create: AsyncMock,
    user: User,
) -> None:
    """Test successful create function call."""
    from image_secrets.backend.database.user import schemas

    create = schemas.UserCreate(
        username=user.username,
        email=user.email,
        password=user.password_hash,
    )

    hash_ = mocker.patch(
        "image_secrets.backend.password.hash_",
        return_value=user.password_hash,
    )

    result = await crud.create(create)

    hash_.assert_called_once()
    mock_create.assert_called_once_with(
        username=create.username,
        email=create.email,
        password_hash=user.password_hash,
    )
    assert result.username == create.username
    assert result.email == create.email
    assert result.password_hash == user.password_hash


@pytest.mark.asyncio
async def test_delete(insert_user: User) -> None:
    """Test successful delete function call."""
    result = await crud.delete(0)

    assert result is None


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "column, value",
    [("username", "new_test_username"), ("email", "new_test_email")],
)
async def test_update_no_password_hash(
    mock_get: AsyncMock,
    user: User,
    insert_user: User,
    column: str,
    value: str,
) -> None:
    """Test successful update function call without a password hash."""
    result = await crud.update(
        insert_user.id,
        **{column: value},
    )

    mock_get.assert_called_once_with(id=insert_user.id)
    assert result == user


@pytest.mark.asyncio
async def test_update_with_password_hash(
    mocker: MockFixture,
    mock_get: AsyncMock,
    user: User,
    insert_user: User,
) -> None:
    """Test successful update function call with a password hash."""
    hash_ = mocker.patch(
        "image_secrets.backend.password.hash_",
        return_value="test_hash",
    )

    pwd = "test_password"
    result = await crud.update(
        insert_user.id,
        **{"password_hash": pwd},
    )

    hash_.assert_called_once_with(pwd)
    mock_get.assert_called_once_with(id=insert_user.id)
    assert result == user


@pytest.mark.asyncio
async def test_authenticate_ok(mocker: MockFixture, insert_user: User) -> None:
    """Test successful authenticate function call."""
    auth = mocker.patch(
        "image_secrets.backend.password.auth",
        return_value=True,
    )

    result = await crud.authenticate(
        username=insert_user.username,
        password_=insert_user.password_hash,
    )

    auth.assert_called_once_with(
        insert_user.password_hash,
        insert_user.password_hash,
    )
    assert result


@pytest.mark.asyncio
async def test_authenticate_fail_password_match(
    mocker: MockFixture,
    insert_user: User,
) -> None:
    """Test failing authenticate function call due to not matching password and its hash."""
    auth = mocker.patch(
        "image_secrets.backend.password.auth",
        return_value=False,
    )

    result = await crud.authenticate(
        username=insert_user.username,
        password_=insert_user.password_hash,
    )

    auth.assert_called_once_with(
        insert_user.password_hash,
        insert_user.password_hash,
    )
    assert not result


@pytest.mark.asyncio
async def test_authenticate_fail_no_db_entry(insert_user: User) -> None:
    """Test failing authenticate function call due to inability to find database user entry."""
    result = await crud.authenticate(
        username="...",
        password_="...",
    )

    assert not result


@pytest.mark.parametrize(
    "column, value, result",
    [
        ("username", "test_username", {"username": "test_username"}),
        ("email", "test_email@email.com", {"email": "test_email@email.com"}),
        ("column", "test_value", {"column": "test_value"}),
    ],
)
def test_user_identifier_to_dict(
    column: str,
    value: str,
    result: dict[str, str],
) -> None:
    """Test the user identifier NamedTuple to_dict method."""
    base = crud.DBIdentifier(column=column, value=value)
    returned = base.to_dict()

    assert issubclass(type(base), tuple)
    assert returned == result
