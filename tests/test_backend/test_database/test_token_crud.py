"""Test the CRUD module for token."""
from __future__ import annotations

import asyncio
from typing import TYPE_CHECKING

import pytest
from tortoise.exceptions import DoesNotExist, IntegrityError

from image_secrets.backend.database.token import crud

if TYPE_CHECKING:
    from unittest.mock import AsyncMock

    from pytest_mock import MockFixture

    from image_secrets.backend.database.token.models import Token
    from image_secrets.backend.database.user.models import User


@pytest.fixture()
def insert_token(insert_user: User) -> Token:
    """Return an existing ``Token`` in database."""
    from image_secrets.backend.database.token.models import Token

    token = Token(
        token_hash="test_token_hash",
        owner_id=insert_user.id,
    )

    loop = asyncio.get_event_loop()
    loop.run_until_complete(token.save())

    return token


@pytest.fixture()
def token() -> Token:
    """Return an encoded image."""
    from image_secrets.backend.database.token import models

    t = models.Token(
        token_hash="test_hash",
        owner_id=2,
    )
    return t


@pytest.fixture()
def mock_create_token(mocker: MockFixture, token: Token):
    """Return mocked Token.create function."""
    async_mock = mocker.AsyncMock(return_value=token)
    return mocker.patch(
        "image_secrets.backend.database.token.models.Token.create",
        side_effect=async_mock,
    )


@pytest.fixture()
def mock_crud_create(mocker: MockFixture, token: Token):
    """Return mocked crud.create function."""
    async_mock = mocker.AsyncMock(return_value=token)
    return mocker.patch(
        "image_secrets.backend.database.token.crud.create",
        side_effect=async_mock,
    )


@pytest.fixture()
def mock_crud_delete(mocker: MockFixture):
    """Return mocked crud.delete function."""
    async_mock = mocker.AsyncMock(return_value=None)
    return mocker.patch(
        "image_secrets.backend.database.token.crud.delete",
        side_effect=async_mock,
    )


@pytest.mark.asyncio
async def test_create(mock_create_token: AsyncMock, token: Token) -> None:
    """Test the create function."""
    result = await crud.create(token.token_hash, token.id)

    mock_create_token.assert_called_once_with(
        token_hash=token.token_hash,
        owner_id=token.id,
    )
    assert result == token


@pytest.mark.asyncio
async def test_create_new(
    mocker: MockFixture,
    mock_crud_create: AsyncMock,
    token: Token,
) -> None:
    token_return = "test_token"
    url_safe = mocker.patch(
        "secrets.token_urlsafe",
        return_value=token_return,
    )
    hash_return = "test_hash"
    hash_ = mocker.patch(
        "image_secrets.backend.password.hash_",
        return_value=hash_return,
    )

    owner_id = 0
    result = await crud.create_new(owner_id)

    url_safe.assert_called_once_with()
    hash_.assert_called_once_with(token_return)
    mock_crud_create.assert_called_once_with(
        token_hash=hash_return,
        owner_id=owner_id,
    )
    assert result == token_return


@pytest.mark.asyncio
async def test_create_new_with_delete(
    mocker: MockFixture,
    insert_token: Token,
    mock_crud_create,
    mock_crud_delete,
    token: Token,
) -> None:
    token_return = "test_token"
    url_safe = mocker.patch(
        "secrets.token_urlsafe",
        return_value=token_return,
    )
    hash_return = "test_hash"
    hash_ = mocker.patch(
        "image_secrets.backend.password.hash_",
        return_value=hash_return,
    )

    mock_crud_create.side_effect = IntegrityError

    owner_id = insert_token.id
    with pytest.raises(IntegrityError):
        await crud.create_new(owner_id)

    url_safe.assert_called_once_with()
    hash_.assert_called_once_with(token_return)
    assert mock_crud_create.call_count == 2
    mock_crud_create.assert_called_with(
        token_hash=hash_return,
        owner_id=owner_id,
    )
    mock_crud_delete.assert_called_once_with(owner_id=owner_id)


@pytest.mark.asyncio
async def test_delete(insert_token: Token) -> None:
    """Test the delete function."""
    result = await crud.delete(owner_id=insert_token.id)

    assert not result


@pytest.mark.asyncio
async def test_get_owner_id_ok(
    mocker: MockFixture,
    insert_token: Token,
) -> None:
    """Test successful get_owner_id function call."""
    auth = mocker.patch(
        "image_secrets.backend.password.auth",
        return_value=True,
    )

    token = "test_token"
    result = await crud.get_owner_id(token)

    auth.assert_called_once_with(token, insert_token.token_hash)
    assert result == insert_token.owner_id


@pytest.mark.asyncio
async def test_get_owner_id_fail(
    mocker: MockFixture,
    insert_token: Token,
) -> None:
    """Test failing get_owner_id function call."""
    auth = mocker.patch(
        "image_secrets.backend.password.auth",
        return_value=False,
    )

    token = "test_token"

    with pytest.raises(DoesNotExist):
        await crud.get_owner_id(token)
    auth.assert_called_once_with(token, insert_token.token_hash)
