"""Test the login post request on the users router."""

from __future__ import annotations

from collections import Counter
from typing import TYPE_CHECKING

import pytest

if TYPE_CHECKING:
    from fastapi.testclient import TestClient
    from pytest_mock import MockFixture

    from imagesecrets.database.user.services import UserService

URL = "api/users/login"


@pytest.mark.parametrize(
    "username, password",
    [("string", "string"), ("username", "password")],
)
def test_ok(
    api_client: TestClient,
    user_service: UserService,
    mocker: MockFixture,
    monkeypatch,
    username: str,
    password: str,
) -> None:
    """Test successful login post request."""
    user_service.authenticate.return_value = True
    user_service.get_id.return_value = 1

    mocker.Mock(
        "fastapi_login.LoginManager.create_access_token",
        return_value="test_token",
    )

    response = api_client.post(
        URL,
        data={"username": username, "password": password},
    )

    user_service.authenticate.assert_called_once_with(username, password)
    assert response.status_code == 200
    json_ = response.json()
    assert json_["token_type"] == "bearer"
    token: str = json_.get("access_token", None)
    assert token
    assert token.isprintable()
    counter = Counter(token)
    assert counter["."] == 2


def test_401(
    api_client: TestClient,
    user_service: UserService,
) -> None:
    """Test invalid login post with a user which does not exist in a database."""
    user_service.authenticate.return_value = False

    response = api_client.post(
        URL,
        data={"username": "test_username", "password": "test_pwd"},
    )

    assert response.status_code == 401
    assert response.reason == "Unauthorized"
    assert response.json()["detail"] == "incorrect username or password"
