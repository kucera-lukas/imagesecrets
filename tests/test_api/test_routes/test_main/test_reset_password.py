"""Test the reset password post request."""

from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy.exc import NoReferenceError

if TYPE_CHECKING:
    from fastapi.testclient import TestClient

    from imagesecrets.database.token.services import TokenService

URL = "api/users/reset-password"


def test_ok(
    api_client: TestClient,
    token_service: TokenService,
) -> None:
    """Test a successful request."""
    token_service.get_user_id.return_value = 1

    token = "token"
    password = "password"
    response = api_client.post(
        f"{URL}?token={token}",
        data={"password": password},
    )

    token_service.get_user_id.assert_called_once_with(token)
    assert response.status_code == 202
    assert response.json()["detail"] == "account password updated"


def test_401(
    api_client: TestClient,
    token_service: TokenService,
) -> None:
    """Test a request with invalid token."""
    token_service.get_user_id.side_effect = NoReferenceError

    token = "invalid token"
    response = api_client.post(
        f"{URL}?token={token}",
        data={"password": "......"},
    )

    token_service.get_user_id.assert_called_once_with(token)
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
