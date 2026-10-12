"""User database models."""

from sqlalchemy import CheckConstraint, Column, String
from sqlalchemy.orm import relationship, validates

from imagesecrets.database.base import Base

_relationship_kwargs = {
    "back_populates": "user",
    "cascade": "all, delete",
    "passive_deletes": True,
}


class User(Base):
    """User model."""

    username = Column(String, unique=True, nullable=False)
    email = Column(String, unique=True, nullable=False)
    password_hash = Column(String(128), nullable=False)

    decoded_images = relationship("DecodedImage", **_relationship_kwargs)
    encoded_images = relationship("EncodedImage", **_relationship_kwargs)

    __table_args__ = (
        CheckConstraint(
            "char_length(username) >= 6",
            name="username_min_length",
        ),
        CheckConstraint(
            "char_length(username) <= 128",
            name="username_max_length",
        ),
    )

    @validates("username")
    def validate_username(self, key, username) -> str:  # pragma: no cover
        """Validate the username column."""
        if not 6 <= len(username) <= 128:
            raise ValueError("Invalid username length.")
        return username
