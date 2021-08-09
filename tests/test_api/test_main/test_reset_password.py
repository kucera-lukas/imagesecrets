"""Test the reset password post request."""
from __future__ import annotations

from typing import TYPE_CHECKING

import pytest
from tortoise.exceptions import DoesNotExist

if TYPE_CHECKING:
    from unittest.mock import AsyncMock

    from fastapi.testclient import TestClient
    from pytest_mock import MockFixture

URL = "/users/reset-password"


@pytest.fixture()
def mock_get_owner_id(mocker: MockFixture):
    """Return mocked get_owner_id function."""
    async_mock = mocker.AsyncMock(return_value=1)
    return mocker.patch(
        "image_secrets.backend.database.token.crud.get_owner_id",
        side_effect=async_mock,
    )


@pytest.fixture()
def mock_update(mocker: MockFixture):
    """Return mocked user crud update function."""
    async_mock = mocker.AsyncMock(return_value=None)
    return mocker.patch(
        "image_secrets.backend.database.user.crud.update",
        side_effect=async_mock,
    )


def test_ok(
    api_client: TestClient,
    mock_get_owner_id: AsyncMock,
    mock_update: AsyncMock,
) -> None:
    """Test a successful request."""
    token = "token"
    password = "password"
    response = api_client.post(
        f"{URL}?token={token}",
        data={"password": password},
    )

    mock_get_owner_id.assert_called_once_with(token)
    mock_update.assert_called_once_with(
        1,  # 1 is the mocked return value of ``mock_get_owner_id``
        password_hash=password,
    )
    assert response.status_code == 202
    assert response.json()["detail"] == "account password updated"


def test_401(
    api_client: TestClient,
    mock_get_owner_id: AsyncMock,
) -> None:
    """Test a request with invalid token."""
    mock_get_owner_id.side_effect = DoesNotExist

    token = "invalid token"
    response = api_client.post(
        f"{URL}?token={token}",
        data={"password": "......"},
    )

    mock_get_owner_id.assert_called_once_with(token)
    assert response.status_code == 401
    assert response.json() == {"detail": "invalid forgot password token"}


def test_422(api_client: TestClient) -> None:
    """Test a request with no token passed in via query param."""
    response = api_client.post(
        URL,
        data={"password": "......"},
    )

    assert response.status_code == 422
    assert response.json() == {"detail": "field required", "field": "token"}
