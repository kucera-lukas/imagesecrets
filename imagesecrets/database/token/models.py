"""Token database models."""

from sqlalchemy import Column, ForeignKey, Integer, String
from sqlalchemy.orm import backref, relationship

from imagesecrets.database.base import Base


class Token(Base):
    """Token model."""

    token_hash = Column(String(128), nullable=False)

    user_id = Column(Integer, ForeignKey("user.id"), nullable=False)

    user = relationship("User", backref=backref("token", uselist=False))


__all__ = ["Token"]
