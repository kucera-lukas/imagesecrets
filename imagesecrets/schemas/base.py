"""Base schemas."""

from __future__ import annotations

from pydantic import BaseModel, HttpUrl

from imagesecrets.constants import URL_KEY_ALIAS


class ModelSchema(BaseModel):
    """Base schema for database models."""

    class Config:
        """Pydantic configuration."""

        orm_mode = True


def pretty_key(key: str) -> str:
    """Return a pretty key if specified alias for it exists, otherwise camelcase."""
    return URL_KEY_ALIAS.get(key) or "".join(
        w.capitalize() for w in key.split("_")
    )


class Info(BaseModel):
    """Response model for home route."""

    app_name: str
    swagger_url: HttpUrl
    redoc_url: HttpUrl
    github_url: HttpUrl

    class Config:
        """Model configuration."""

        alias_generator = pretty_key


class Message(BaseModel):
    """Response model for a single detail field."""

    detail: str


class Field(Message):
    """Response model for invalid field value."""

    field: str


class Conflict(Field):
    """Response model for conflicting field value."""

    value: str


class Token(BaseModel):
    """Response model for access token."""

    access_token: str
    token_type: str
