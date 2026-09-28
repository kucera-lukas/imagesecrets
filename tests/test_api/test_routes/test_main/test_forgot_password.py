"""Test the forgot password post request."""

from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy.exc import NoResultFound

if TYPE_CHECKING:
    from fastapi.testclient import TestClient
    from pytest_mock import MockFixture

URL = "api/users/forgot-password"


def test_ok(
    api_client: TestClient,
    mocker: MockFixture,
    monkeypatch,
    user_service,
    token_service,
) -> None:
    """Test a successful request."""
    from imagesecrets.database.user.services import DBIdentifier

    user_service.get_id.return_value = 0
    token_service.create_token.return_value = ("test token", "test hash")

    bg_tasks = mocker.patch("fastapi.BackgroundTasks.add_task")

    response = api_client.post(URL, data={"email": "test@example.com"})

    user_service.get_id.assert_called_once_with(
        DBIdentifier(column="email", value="test@example.com"),
    )
    assert bg_tasks.call_count == 2
    assert response.status_code == 202
    assert response.json() == {
        "detail": "email with password reset token has been sent",
    }


def test_ok_no_user(
    api_client: TestClient,
    mocker: MockFixture,
    monkeypatch,
    user_service,
    token_service,
) -> None:
    """Test a successful request without any known user in database."""
    from imagesecrets.database.user.services import DBIdentifier

    user_service.get_id.side_effect = NoResultFound

    random = mocker.patch("random.random", return_value=1)
    sleep = mocker.patch("asyncio.sleep", return_value=None)

    response = api_client.post(URL, data={"email": "unknown@email.com"})

    user_service.get_id.assert_called_once_with(
        DBIdentifier(column="email", value="unknown@email.com"),
    )
    random.assert_called_once_with()
    sleep.assert_called_with(1)
    assert response.status_code == 202
    assert response.json() == {
        "detail": "email with password reset token has been sent",
    }
