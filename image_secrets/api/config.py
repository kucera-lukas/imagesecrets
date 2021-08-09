"""FastAPI configuration."""
from __future__ import annotations

import os
from typing import cast

from fastapi_mail import ConnectionConfig, config
from pydantic import (
    BaseSettings,
    DirectoryPath,
    EmailStr,
    HttpUrl,
    PostgresDsn,
)

from image_secrets.settings import API_IMAGES, MESSAGE_DELIMITER, TEMPLATES

# monkey patch one of fastapi_mail path validation functions
# because it is broken when application is not run from parent folder
config.validate_path = lambda _: True


class Settings(BaseSettings):
    """API Settings."""

    app_name: str = "ImageSecrets"

    message_delimiter: str = MESSAGE_DELIMITER
    image_folder: DirectoryPath = API_IMAGES

    pg_dsn: PostgresDsn = cast(PostgresDsn, os.getenv("DATABASE_URL"))
    secret_key: str = cast(str, os.getenv("SECRET_KEY"))

    icon_url: HttpUrl = cast(HttpUrl, os.getenv("ICON_URL"))
    swagger_url: HttpUrl = cast(HttpUrl, os.getenv("SWAGGER_URL"))
    redoc_url: HttpUrl = cast(HttpUrl, os.getenv("REDOC_URL"))
    repository_url: HttpUrl = cast(HttpUrl, os.getenv("REPOSITORY_URL"))

    @staticmethod
    def email_config() -> ConnectionConfig:
        """Return email connection configuration."""
        return ConnectionConfig(
            MAIL_USERNAME=os.getenv("MAIL_USERNAME"),
            MAIL_PASSWORD=os.getenv("MAIL_PASSWORD"),
            MAIL_PORT=int(cast(int, os.getenv("MAIL_PORT"))),
            MAIL_SERVER=os.getenv("MAIL_SERVER"),
            MAIL_TLS=True,
            MAIL_SSL=False,
            MAIL_FROM=EmailStr(os.getenv("MAIL_FROM")),
            TEMPLATE_FOLDER=str(TEMPLATES),
        )


settings = Settings()


__all__ = [
    "Settings",
]
