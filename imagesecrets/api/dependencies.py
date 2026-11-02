"""API dependencies."""

from __future__ import annotations

import functools
from typing import TYPE_CHECKING, TypeVar

from fastapi_mail import FastMail

from imagesecrets import config
from imagesecrets.database.service import DatabaseService

if TYPE_CHECKING:
    from imagesecrets.config import Settings

_S = TypeVar("_S", bound=DatabaseService)


@functools.cache
def get_config() -> Settings:
    """Return api settings."""
    return config.settings


@functools.cache
def get_mail() -> FastMail:
    """Return SMTP mail client."""
    return FastMail(config.settings.email_config())


__all__ = [
    "get_config",
]
