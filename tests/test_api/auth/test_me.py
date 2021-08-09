"""Test the me router with authenticated user."""
from __future__ import annotations

import asyncio
from typing import TYPE_CHECKING

import pytest

if TYPE_CHECKING:
    from fastapi.testclient import TestClient
    from pytest_mock import MockFixture

    from image_secrets.backend.database.user.models import User


URL = "/users/me"


def test_get(
    api_client: TestClient,
    auth_token: tuple[dict[str, str], User],
) -> None:
    """Test the get request."""
    header = auth_token[0]
    user = auth_token[1]
    response = api_client.get(
        URL,
        headers=header,
    )

    response.raise_for_status()
    assert response.status_code == 200
    assert response.reason == "OK"
    json_ = response.json()
    assert json_["username"] == user.username
    assert json_["email"] == user.email
    assert not json_["decoded_images"]
    assert not json_["encoded_images"]


@pytest.mark.parametrize(
    "username, email",
    [("test-name", "test@email.com"), ("123456", "example@result.com")],
)
def test_patch(
    api_client: TestClient,
    auth_token: tuple[dict[str, str], User],
    username: str,
    email: str,
) -> None:
    """Test successful patch request."""
    header = auth_token[0]
    user = auth_token[1]

    assert user.username != username
    assert user.email != email

    response = api_client.patch(
        URL,
        headers=header,
        data={"username": username, "email": email},
    )

    response.raise_for_status()
    assert response.status_code == 200
    assert response.reason == "OK"
    json_ = response.json()
    assert json_["username"] == username
    assert json_["email"] == email


def test_patch_empty(
    api_client: TestClient,
    auth_token: tuple[dict[str, str], User],
) -> None:
    """Test successful empty patch request"""
    header = auth_token[0]
    user = auth_token[1]

    response = api_client.patch(
        URL,
        headers=header,
        data={},
    )

    response.raise_for_status()
    assert response.status_code == 200
    assert response.reason == "OK"
    json_ = response.json()
    assert json_["username"] == user.username
    assert json_["email"] == user.email


@pytest.mark.parametrize("username", ["test-name", "123456"])
def test_patch_409(
    api_client: TestClient,
    auth_token: tuple[dict[str, str], User],
    username: str,
) -> None:
    """Test failing patch request with a database conflict error."""
    from image_secrets.backend.database.user.models import User

    loop = asyncio.get_event_loop()
    loop.run_until_complete(
        User.create(
            username=username,
            email="email@email.com",
            password_hash="pwd",
        ),
    )

    header = auth_token[0]

    response = api_client.patch(
        URL,
        headers=header,
        data={"username": username},
    )

    assert response.status_code == 409
    assert response.reason == "Conflict"
    json_ = response.json()
    assert json_["detail"] == "account detail already exists"
    assert json_["field"] == "UNIQUE constraint failed"
    assert json_["value"].lstrip() == "user.username"


@pytest.mark.parametrize("username", ["00000", "1" * 129])
def test_patch_422_username(
    api_client: TestClient,
    auth_token: tuple[dict[str, str], User],
    username: str,
) -> None:
    """Test a failing patch request with an invalid username in the body."""
    header = auth_token[0]

    response = api_client.patch(
        URL,
        headers=header,
        data={"username": username},
    )
    assert response.status_code == 422
    assert response.reason == "Unprocessable Entity"
    assert response.json() == {
        "detail": f"ensure this value has at {'least 6 characters' if len(username) < 6 else 'most 128 characters'}",
        "field": "username",
    }


@pytest.mark.parametrize(
    "email",
    ["@", "email@email", "email.com", "email@email.", "@email.com"],
)
def test_patch_422_email(
    api_client: TestClient,
    auth_token: tuple[dict[str, str], User],
    email: str,
) -> None:
    """Test a failing patch request with an invalid email in the body."""
    header = auth_token[0]

    response = api_client.patch(
        URL,
        headers=header,
        data={"email": email},
    )

    assert response.status_code == 422
    assert response.reason == "Unprocessable Entity"
    assert response.json() == {
        "detail": "value is not a valid email address",
        "field": "email",
    }


def test_delete(
    api_client: TestClient,
    auth_token: tuple[dict[str, str], User],
) -> None:
    """Test a successful delete request."""
    header = auth_token[0]
    response = api_client.delete(
        URL,
        headers=header,
    )

    response.raise_for_status()
    assert response.status_code == 202
    assert response.reason == "Accepted"
    assert response.json()["detail"] == "account deleted"


def test_password_put(
    mocker: MockFixture,
    api_client: TestClient,
    auth_token: tuple[dict[str, str], User],
) -> None:
    """Test a successful password put request."""
    authenticate = mocker.patch(
        "image_secrets.backend.database.user.crud.authenticate",
        return_value=True,
    )
    update = mocker.patch(
        "image_secrets.backend.database.user.crud.update",
        return_value=...,
    )

    header = auth_token[0]
    user = auth_token[1]
    old_password = "old_password"
    new_password = "new_password"

    response = api_client.put(
        f"{URL}/password",
        headers=header,
        data={"old": old_password, "new": new_password},
    )

    authenticate.assert_called_once_with(
        username=user.username,
        password_=old_password,
    )
    update.assert_called_once_with(user.id, password_hash=new_password)

    response.raise_for_status()
    assert response.status_code == 202
    assert response.reason == "Accepted"
    assert response.json()["detail"] == "account password updated"


def test_password_put_401(
    mocker: MockFixture,
    api_client: TestClient,
    auth_token: tuple[dict[str, str], User],
) -> None:
    """Test a password put request with invalid password in request body"""
    auth = mocker.patch(
        "image_secrets.backend.database.user.crud.authenticate",
        return_value=False,
    )
    hash_ = mocker.patch(
        "image_secrets.backend.password.hash_",
        return_value="...",
    )

    header = auth_token[0]
    user = auth_token[1]

    response = api_client.put(
        f"{URL}/password",
        headers=header,
        data={"old": "old_password", "new": "new_password"},
    )

    auth.assert_called_once_with(
        username=user.username,
        password_="old_password",
    )
    hash_.assert_not_called()

    assert response.status_code == 401
    assert response.reason == "Unauthorized"
    assert response.json() == {"detail": "incorrect password"}
