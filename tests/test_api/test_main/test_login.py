"""Test the login post request on the users router."""
from __future__ import annotations

import asyncio
from collections import Counter
from typing import TYPE_CHECKING

import pytest

if TYPE_CHECKING:
    from fastapi.testclient import TestClient
    from pytest_mock import MockFixture

    from image_secrets.backend.database.user.models import User

URL = "/users/login"


@pytest.mark.parametrize(
    "username, password",
    [("string", "string"), ("username", "password")],
)
def test_ok(
    api_client: TestClient,
    mocker: MockFixture,
    username: str,
    password: str,
) -> None:
    """Test successful login post request."""
    from image_secrets.backend.database.user.models import User

    loop = asyncio.get_event_loop()
    loop.run_until_complete(
        User.create(
            username=username,
            email="user@example.com",
            password_hash=password,
        ),
    )

    auth = mocker.patch(
        "image_secrets.backend.password.auth",
        return_value=True,
    )
    response = api_client.post(
        URL,
        data={"username": username, "password": password},
    )

    # plain password should be retrieved from database
    auth.assert_called_once_with(password, password)

    response.raise_for_status()
    assert response.status_code == 200
    assert response.reason == "OK"
    json_ = response.json()
    assert json_["token_type"] == "bearer"
    token: str = json_.get("access_token", None)
    assert token
    assert token.isprintable()
    counter = Counter(token)
    assert counter["."] == 2


def test_401_in_db(
    api_client: TestClient,
    mocker: MockFixture,
    insert_user: User,
) -> None:
    """Test invalid login post request with an existing user in a database."""
    auth = mocker.patch(
        "image_secrets.backend.password.auth",
        return_value=False,
    )
    response = api_client.post(
        URL,
        data={"username": insert_user.username, "password": "test_pwd"},
    )

    auth.assert_called_once_with("test_pwd", insert_user.password_hash)

    assert response.status_code == 401
    assert response.reason == "Unauthorized"
    assert response.json()["detail"] == "incorrect username or password"


def test_401_not_in_db(api_client: TestClient, mocker: MockFixture) -> None:
    """Test invalid login post with a user which does not exist in a database."""
    auth = mocker.patch("image_secrets.backend.password.auth")
    response = api_client.post(
        URL,
        data={"username": "test_username", "password": "test_pwd"},
    )

    # no user in database so auth should not be called
    auth.assert_not_called()

    assert response.status_code == 401
    assert response.reason == "Unauthorized"
    assert response.json()["detail"] == "incorrect username or password"
