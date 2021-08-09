"""User database models."""
from tortoise import fields, models

from image_secrets.backend.database.image import models as image_models


class User(models.Model):
    """Tortoise user model."""

    id = fields.IntField(pk=True, index=True)
    username = fields.CharField(
        index=True,
        unique=True,
        min_length=6,
        max_length=128,
    )
    email = fields.TextField()
    password_hash = fields.CharField(max_length=128)

    created = fields.DatetimeField(auto_now_add=True)
    modified = fields.DatetimeField(auto_now=True)

    decoded_images: fields.ReverseRelation[image_models.DecodedImage]
    encoded_images: fields.ReverseRelation[image_models.EncodedImage]

    class Meta:
        """Tortoise metaclass."""

        table = "user"


__models__ = [User]
