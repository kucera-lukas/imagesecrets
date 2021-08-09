"""Asynchronous email sending."""
from __future__ import annotations

from typing import TYPE_CHECKING

from fastapi_mail import MessageSchema

if TYPE_CHECKING:
    from fastapi_mail import FastMail
    from pydantic import EmailStr


async def send_welcome(
    client: FastMail,
    recipient: EmailStr,
    username: str,
) -> None:
    """Send a welcome email.

    :param client: Email SMTP client
    :param recipient: Recipient of welcome email
    :param username: Name of the recipient

    """
    message = MessageSchema(
        subject="Welcome to ImageSecrets",
        recipients=[recipient],
        body={"username": username},
        subtype="html",
    )
    await client.send_message(message, template_name="welcome_email.html")


async def send_reset(
    client: FastMail,
    recipient: EmailStr,
    token: str,
) -> None:
    """Send a reset password email.

    :param client: Email SMTP client
    :param recipient: Recipient of the email
    :param token: The reset password token

    """
    message = MessageSchema(
        subject="Reset Password",
        recipients=[recipient],
        body={"token": token, "name": recipient},
        subtype="html",
    )
    await client.send_message(message, template_name="reset_email.html")
