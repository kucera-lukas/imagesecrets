"""Utility functions."""
from __future__ import annotations

import functools as fn
import math
import re
import secrets
from typing import TYPE_CHECKING, Any, NamedTuple, Optional, Type, TypeVar

from image_secrets.backend.regex import INTEGRITY_FIELD

if TYPE_CHECKING:
    from tortoise.exceptions import IntegrityError


_T = TypeVar("_T")


def partial_init(
    cls: Type[_T],
    *args: Optional[Any],
    **kwargs: Optional[Any],
) -> _T:
    """Partially instantiate a class initializer.

    :param cls: The class to instantiate
    :param args: Optional positional arguments
    :param kwargs: Optional keyword arguments

    """

    class Partial(cls):  # type: ignore
        """Partial class with partially initialized initializer."""

        __init__ = fn.partialmethod(cls.__init__, *args, **kwargs)  # type: ignore

        # repr with ``Partial`` would be confusing
        __repr__ = cls.__repr__

    return Partial  # type: ignore


class ExcludeUnsetDict(dict):
    """Dict subclass with added ``exclude_unset`` method."""

    def exclude_unset(self) -> dict:
        """Return dictionary with all items which are truthy."""
        return {key: value for key, value in self.items() if value}


def token_hex(length: int, /) -> str:
    """Return a random token hex.

    :param length: How many chars should the final token have

    """
    nbytes = math.ceil(abs(length) / 2)
    return secrets.token_hex(nbytes)


def token_url() -> str:
    """Return random and URL safe token."""
    return secrets.token_urlsafe()


class ParsedIntegrity(NamedTuple):
    """Representation of field and value collected from Tortoise IntegrityError."""

    field: str
    value: str


def parse_unique_integrity(
    *,
    error: IntegrityError,
) -> ParsedIntegrity:
    """Parse a database uniqueness IntegrityError and return the conflicting field and value."""
    err = str(error)
    try:
        result = re.findall(INTEGRITY_FIELD, err)[0]
    except IndexError as e:
        raise ValueError(f"invalid error message: {err!r}") from e
    return ParsedIntegrity(field=result[0], value=result[1])


__all__ = [
    "token_hex",
]
