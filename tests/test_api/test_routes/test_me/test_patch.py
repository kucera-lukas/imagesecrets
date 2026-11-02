"""Test the me router with authenticated user."""

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

URL = "api/users/me"


@pytest.mark.parametrize(
    "username, email",
    [("test-name", "test@example.com"), ("123456", "example@result.com")],
)
def test_patch(
    api_client: TestClient,
    return_user: User,
    user_service: UserService,
    access_token,
    username: str,
    email: str,
) -> None:
    """Test successful patch request."""
    from imagesecrets.database.user.models import User

    assert return_user.username != username
    assert return_user.email != email

    new_user = User(
        username=username,
        email=email,
        password_hash="test_hash",
        created=datetime(year=2000, month=1, day=1),
        updated=datetime(year=3000, month=2, day=2),
    )

    user_service.update.return_value = new_user

    response = api_client.patch(
        URL,
        headers=access_token,
        data={"username": username, "email": email},
    )

    user_service.update.assert_called_once_with(
        return_user.id,
        username=username,
        email=email,
    )
    assert response.status_code == 200
    json_ = response.json()
    assert json_["username"] == username
    assert json_["email"] == email


def test_patch_empty(
    api_client: TestClient,
    return_user,
    access_token,
) -> None:
    """Test successful empty patch request"""
    response = api_client.patch(
        URL,
        headers=access_token,
        data={},
    )

    assert response.status_code == 200
    json_ = response.json()
    assert json_["username"] == return_user.username
    assert json_["email"] == return_user.email


@pytest.mark.parametrize("username", ["test-name", "123456"])
def test_patch_409(
    api_client: TestClient,
    mocker: MockFixture,
    user_service: UserService,
    access_token,
    return_user,
    username: str,
) -> None:
    """Test failing patch request with a database conflict error."""
    from imagesecrets.core.util.main import ParsedIntegrity

    exc = Exception()
    err = IntegrityError.instance(
        statement="test_statement",
        params="test_params",
        orig=exc,
        dbapi_base_err=(Exception,),
    )

    user_service.update.side_effect = err

    parse = mocker.patch(
        "imagesecrets.core.util.main.parse_asyncpg_integrity",
        return_value=ParsedIntegrity(field="username", value=username),
    )

    response = api_client.patch(
        URL,
        headers=access_token,
        data={"username": username},
    )

    parse.assert_called_once_with(error=exc)
    assert response.status_code == 409
    json_ = response.json()
    assert json_["detail"] == "account detail already exists"
    assert json_["field"] == "username"
    assert json_["value"].lstrip() == username


@pytest.mark.parametrize("username", ["00000", "1" * 129])
def test_patch_422_username(
    api_client: TestClient,
    access_token,
    username: str,
) -> None:
    """Test a failing patch request with an invalid username in the body."""
    response = api_client.patch(
        URL,
        headers=access_token,
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
    access_token,
    email: str,
) -> None:
    """Test a failing patch request with an invalid email in the body."""

    response = api_client.patch(
        URL,
        headers=access_token,
        data={"email": email},
    )

    assert response.status_code == 422
    assert response.reason == "Unprocessable Entity"
    assert response.json() == {
        "detail": "value is not a valid email address",
        "field": "email",
    }
