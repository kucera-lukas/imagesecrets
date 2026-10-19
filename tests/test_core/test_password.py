"""Test the password utility module."""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

from imagesecrets.core.password import auth, hash_

if TYPE_CHECKING:
    from pytest_mock import MockFixture


@pytest.mark.parametrize("password", ["", "321", "my-password"])
def test_hash_(mocker: MockFixture, password: str) -> None:
    """Test the hash function."""
    gensalt = mocker.patch(
        "bcrypt.gensalt",
        return_value=b"$2b$12$SHamHx8Sd9lxkp/KA2cPhu",
    )

    result = hash_(password)

    gensalt.assert_called_once_with()
    assert isinstance(result, str)
    assert result[:4] == "$2b$"
    assert len(result) == 60
    assert result.isascii()


def test_auth(mocker: MockFixture) -> None:
    """Test the auth function."""
    checkpw = mocker.patch("bcrypt.checkpw", return_value=True)

    result = auth("plain", "hashed")

    checkpw.assert_called_once_with(b"plain", b"hashed")
    assert result
