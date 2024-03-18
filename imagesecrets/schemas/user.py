"""User schemas."""

from __future__ import annotations

from datetime import datetime
from typing import Optional

from pydantic import EmailStr, Field, SecretStr, constr

from imagesecrets.schemas.base import ModelSchema
from imagesecrets.schemas.image import Image


class _BaseUser(ModelSchema):
    """Base User schema."""

    username: constr(min_length=6, max_length=128)
    email: EmailStr


class UserCreate(_BaseUser):
    """Schema for User creation."""

    password: SecretStr = Field(..., min_length=6)


class UserUpdate(ModelSchema):
    """Schema for User update."""

    username: Optional[str] = Field(
        None,
        min_length=6,
        max_length=6,
    )
    email: Optional[EmailStr]


class User(_BaseUser):
    """Full User schema."""

    created: datetime
    updated: datetime

    decoded_images: list[Image]
    encoded_images: list[Image]
