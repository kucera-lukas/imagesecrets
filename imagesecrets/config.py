"""FastAPI configuration."""

from __future__ import annotations

import os
from typing import cast

import dotenv
from fastapi_mail import ConnectionConfig, config
from pydantic import BaseSettings, EmailStr, HttpUrl, PostgresDsn, validator

from imagesecrets.constants import MESSAGE_DELIMITER, TEMPLATES

dotenv.load_dotenv()

# monkey patch one of fastapi_mail path validation functions
# because it is broken when application is not run from parent folder
config.validate_path = lambda _: True


def asyncpg_engine_dsn(db_url: str) -> str:
    """Return Database URL with asyncpg engine.

    :param db_url: Base database URL

    """
    split = db_url.split(":")
    split[0] = f"{split[0]}ql+asyncpg"
    return ":".join(split)


class Settings(BaseSettings):
    """API Settings."""

    app_name: str = "ImageSecrets"

    message_delimiter: str = MESSAGE_DELIMITER

    pg_dsn: PostgresDsn = cast(PostgresDsn, os.environ["DATABASE_URL"])
    secret_key: str = cast(str, os.environ["SECRET_KEY"])

    icon_url: HttpUrl = cast(HttpUrl, os.environ["ICON_URL"])
    swagger_url: HttpUrl = cast(HttpUrl, os.environ["SWAGGER_URL"])
    redoc_url: HttpUrl = cast(HttpUrl, os.environ["REDOC_URL"])
    repository_url: HttpUrl = cast(HttpUrl, os.environ["REPOSITORY_URL"])

    @validator("pg_dsn", allow_reuse=True)
    def postgres_engine(cls, v: str) -> str:
        return asyncpg_engine_dsn(db_url=v)

    @staticmethod
    def email_config() -> ConnectionConfig:
        """Return email connection configuration."""
        return ConnectionConfig(
            MAIL_USERNAME=os.environ["MAIL_USERNAME"],
            MAIL_PASSWORD=os.environ["MAIL_PASSWORD"],
            MAIL_PORT=int(os.environ["MAIL_PORT"]),
            MAIL_SERVER=os.environ["MAIL_SERVER"],
            MAIL_TLS=True,
            MAIL_SSL=False,
            MAIL_FROM=EmailStr(os.environ["MAIL_FROM"]),
            TEMPLATE_FOLDER=str(TEMPLATES),
        )


settings = Settings()


__all__ = [
    "Settings",
]
