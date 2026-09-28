"""Test the register request in the users router."""

from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING

import pytest
from sqlalchemy.exc import IntegrityError

if TYPE_CHECKING:
    from fastapi.testclient import TestClient
    from pytest_mock import MockFixture

    from imagesecrets.database.user.models import User
    from imagesecrets.database.user.services import UserService

URL = "api/users/register"


@pytest.fixture()
def return_user() -> User:
    """Return a fake database user entry."""
    from imagesecrets.database.user.models import User

    return User(
        username="test_username",
        email="test@email.com",
        password_hash="test_hash",
        created=datetime(year=2000, month=1, day=1),
        updated=datetime(year=3000, month=2, day=2),
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
    user_service: UserService,
    return_user: User,
    username: str,
    email: str,
    password: str,
) -> None:
    """Test successful post request on the register route."""
    from imagesecrets.schemas import UserCreate

    return_user.username = username
    return_user.email = email
    return_user.password_hash = password

    user_service.create.return_value = return_user

    response = api_client.post(
        URL,
        json={"username": username, "email": email, "password": password},
    )

    user_service.create.assert_called_once_with(
        UserCreate(email=email, password=password, username=username),
    )
    assert response.status_code == 201
    json_ = response.json()
    assert json_["username"] == username
    assert json_["email"] == email
    with pytest.raises(KeyError):
        _ = json_["password"]
    assert not json_["decoded_images"]
    assert not json_["encoded_images"]


@pytest.mark.parametrize("username", ["string", "duplicate_username"])
def test_409(
    api_client: TestClient,
    mocker: MockFixture,
    user_service: UserService,
    username: str,
) -> None:
    """Test failing post request with a 409 status code (db conflict)."""
    from imagesecrets.core.util.main import ParsedIntegrity

    exc = Exception()
    err = IntegrityError.instance(
        statement="test_statement",
        params="test_params",
        orig=exc,
        dbapi_base_err=(Exception,),
    )

    user_service.create.side_effect = err

    parse = mocker.patch(
        "imagesecrets.core.util.main.parse_asyncpg_integrity",
        return_value=ParsedIntegrity(field="username", value=username),
    )

    response = api_client.post(
        URL,
        json={
            "username": username,
            "email": "user@example.com",
            "password": "string",
        },
    )

    parse.assert_called_once_with(error=exc)
    assert response.status_code == 409
    json_ = response.json()
    assert json_["detail"] == "account detail already exists"
    assert json_["field"] == "username"
    assert json_["value"] == username


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
