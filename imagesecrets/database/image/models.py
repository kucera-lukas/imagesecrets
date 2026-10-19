"""Image database models."""

from __future__ import annotations

from sqlalchemy import Column, ForeignKey, Integer, SmallInteger, String
from sqlalchemy.orm import relationship

from imagesecrets.constants import MESSAGE_DELIMITER
from imagesecrets.database.base import Base

_foreign_key_kwargs = {
    "column": "user.id",
    "ondelete": "CASCADE",
}
_relationship_kwargs = {
    "nullable": False,
}


class Image:
    """Base image mixin."""

    image_name = Column(String, nullable=False)

    message = Column(String, nullable=False)
    delimiter = Column(String, default=MESSAGE_DELIMITER, nullable=False)
    lsb_amount = Column(SmallInteger, default=1, nullable=False)

    filename = Column(String, nullable=False)


class DecodedImage(Image, Base):
    """Decoded image model."""

    user_id = Column(
        Integer,
        ForeignKey(**_foreign_key_kwargs),
        **_relationship_kwargs,
    )

    user = relationship("User", back_populates="decoded_images")


class EncodedImage(Image, Base):
    """Encoded image model."""

    user_id = Column(
        Integer,
        ForeignKey(**_foreign_key_kwargs),
        **_relationship_kwargs,
    )

    user = relationship("User", back_populates="encoded_images")


__all__ = [
    "Image",
    "DecodedImage",
    "EncodedImage",
]
