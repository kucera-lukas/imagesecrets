"""User schemas."""
import functools as fn
from typing import Optional, Type

from pydantic import EmailStr, Field, SecretStr
from tortoise.contrib.pydantic import PydanticModel, pydantic_model_creator

from image_secrets.backend.database.image import schemas
from image_secrets.backend.database.user import models
from image_secrets.backend.regex import USERNAME

USERNAME_STR: str = str(USERNAME.pattern)
pydantic_model_creator = fn.partial(
    pydantic_model_creator,
    cls=models.User,
    exclude=("id", "password_hash"),
)
_UserBase: Type[PydanticModel] = pydantic_model_creator(  # type: ignore
    name="UserBase",
    exclude_readonly=True,
)
_UserFull: Type[PydanticModel] = pydantic_model_creator(  # type: ignore
    name="User",
    exclude_readonly=False,
)


class UserBase(_UserBase):  # type: ignore
    """Base User schema."""

    username: str = Field(
        ...,
        min_length=6,
        max_length=128,
        regex=USERNAME_STR,
    )
    email: EmailStr


class UserCreate(UserBase):
    """Create new User schema."""

    password: SecretStr = Field(..., min_length=6)


class UserUpdate(_UserBase):  # type: ignore
    """Update existing User schema."""

    username: Optional[str] = Field(
        None,
        min_length=6,
        max_length=128,
        regex=USERNAME_STR,
    )
    email: Optional[EmailStr]


class User(_UserFull):  # type: ignore
    """Main User schema."""

    decoded_images: list[schemas.Image]
    encoded_images: list[schemas.Image]
