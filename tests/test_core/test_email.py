"""Test the email module."""

from __future__ import annotations

import asyncio
from typing import TYPE_CHECKING

import pytest
from pydantic import EmailStr

from imagesecrets.core import email

if TYPE_CHECKING:
    from email.mime.multipart import MIMEMultipart

    from fastapi_login import FastMail


@pytest.fixture(scope="module")
def client() -> FastMail:
    """Return email client in a test mode."""
    from imagesecrets.api.dependencies import get_mail

    return get_mail()


@pytest.mark.parametrize(
    "recipient, username",
    [("email@example.com", "test_username"), ("email@test.abc", "abc")],
)
def test_send_welcome(
    client: FastMail,
    recipient: str,
    username: str,
) -> None:
    """Test the send_welcome function."""
    loop = asyncio.get_event_loop()

    coro = email.send_welcome(
        client=client,
        recipient=EmailStr(recipient),
        username=username,
    )
    with client.record_messages() as outbox:
        loop.run_until_complete(coro)

        assert len(outbox) == 1
        out: MIMEMultipart = outbox[0]

    assert out["From"] == client.config.MAIL_FROM
    assert out["To"] == recipient
    assert out["Subject"] == "Welcome to ImageSecrets"
    assert not out.defects


@pytest.mark.parametrize(
    "recipient, token",
    [
        ("email@example.com", "9876543210"),
        ("email@test.abc", "QWERTYASDF"),
    ],
)
def test_send_reset(
    client: FastMail,
    recipient: str,
    token: str,
) -> None:
    """Test the send_welcome function."""
    loop = asyncio.get_event_loop()

    coro = email.send_reset(
        client=client,
        recipient=EmailStr(recipient),
        token=token,
    )
    with client.record_messages() as outbox:
        loop.run_until_complete(coro)

        assert len(outbox) == 1
        out: MIMEMultipart = outbox[0]

    assert out["From"] == client.config.MAIL_FROM
    assert out["To"] == recipient
    assert out["Subject"] == "Reset Password"
    assert not out.defects
