"""Test the me router with authenticated user."""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from fastapi.testclient import TestClient

    from imagesecrets.database.user.models import User
    from imagesecrets.database.user.services import UserService

URL = "api/users/me"


def test_get_ok(
    api_client: TestClient,
    user_service: UserService,
    monkeypatch,
    return_user: User,
    access_token,
) -> None:
    """Test the get request."""
    monkeypatch.setattr(
        "fastapi_login.LoginManager.__call__",
        lambda *a, **kw: return_user,
    )

    response = api_client.get(URL, headers=access_token)

    assert response.status_code == 200
    json_ = response.json()
    assert json_["username"] == return_user.username
    assert json_["email"] == return_user.email
    assert not json_["decoded_images"]
    assert not json_["encoded_images"]
