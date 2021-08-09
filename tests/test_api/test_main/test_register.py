"""Test the register request in the users router."""
from __future__ import annotations

import asyncio
from typing import TYPE_CHECKING

import pytest

if TYPE_CHECKING:
    from fastapi.testclient import TestClient
    from pytest_mock import MockFixture

    from image_secrets.backend.database.user.models import User


URL = "/users/register"


@pytest.fixture()
def return_user() -> User:
    """Return a fake database user entry."""
    from image_secrets.backend.database.user.models import User

    user = User(
        username="test_usernamne",
        email="test_email@example.com",
        password_hash="test_hash",
    )
    return user


@pytest.fixture()
def mock_user_crud_create(mocker: MockFixture, return_user: User):
    """Return mocked user.crud.create function."""
    async_mock = mocker.AsyncMock(return_value=return_user)
    return mocker.patch(
        "image_secrets.backend.database.user.crud.create",
        side_effect=async_mock,
    )


@pytest.mark.parametrize(
    "username, email, password",
    [
        ("string", "user@example.com", "password"),
        ("123456", "user@string.com", "secret!!"),
    ],
)
def test_ok(
    api_client: TestClient,
    username: str,
    email: str,
    password: str,
) -> None:
    """Test successful post request on the register route."""
    response = api_client.post(
        URL,
        json={"username": username, "email": email, "password": password},
    )
    response.raise_for_status()
    assert response.status_code == 201
    assert response.reason == "Created"
    json_ = response.json()
    assert json_["username"] == username
    assert json_["email"] == email
    with pytest.raises(KeyError):
        _ = json_["password"]
    assert not json_["decoded_images"]
    assert not json_["encoded_images"]


@pytest.mark.parametrize("username", ["string", "duplicate_username"])
def test_409(api_client: TestClient, username: str) -> None:
    """Test failing post request with a 409 status code (db conflict)."""
    from image_secrets.backend.database.user.models import User

    loop = asyncio.get_event_loop()
    loop.run_until_complete(
        User.create(username=username, email="...", password_hash="..."),
    )

    response = api_client.post(
        URL,
        json={
            "username": username,
            "email": "user@example.com",
            "password": "string",
        },
    )

    assert response.status_code == 409
    assert response.reason == "Conflict"
    json_ = response.json()
    assert json_["detail"] == "account detail already exists"
    assert "UNIQUE constraint" in json_["field"]
    assert "username" in json_["value"]


@pytest.mark.parametrize("username", ["", "u" * 5, "u" * 129])
def test_422_username(api_client: TestClient, username: str) -> None:
    """Test unprocessable username entity."""
    response = api_client.post(
        URL,
        json={
            "username": username,
            "email": "email@example.com",
            "password": "string",
        },
    )

    assert response.status_code == 422
    assert response.reason == "Unprocessable Entity"
    assert response.json() == {
        "detail": f"ensure this value has at {'least 6 characters' if len(username) < 6 else 'most 128 characters'}",
        "field": "username",
    }


@pytest.mark.parametrize(
    "email",
    ["", "@", "email@email", "email.com", "email@email.", "@email.com"],
)
def test_422_email(api_client: TestClient, email: str) -> None:
    """Test unprocessable email entity."""
    response = api_client.post(
        URL,
        json={
            "username": "string",
            "email": email,
            "password": "string",
        },
    )

    assert response.status_code == 422
    assert response.reason == "Unprocessable Entity"
    assert response.json() == {
        "detail": "value is not a valid email address",
        "field": "email",
    }
