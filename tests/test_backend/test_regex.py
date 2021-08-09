"""Test the regex module."""
import re

import pytest

from image_secrets.backend.regex import INTEGRITY_FIELD, USERNAME


def test_regex_compiled() -> None:
    """Test that the regex module contains compiled expressions."""
    assert INTEGRITY_FIELD.__class__ is re.Pattern
    assert USERNAME.__class__ is re.Pattern


def test_integrity_properties() -> None:
    """Test the integrity_field regular expression properties."""
    assert INTEGRITY_FIELD.groups == 2
    assert INTEGRITY_FIELD.groupindex
    assert INTEGRITY_FIELD.flags == 32


@pytest.mark.parametrize(
    "full_string, match1, match2",
    [
        ("username)=(name) already exists.", "username", "name"),
        (
            "123456(email)=(email@email.com) already exists.",
            "email",
            "email@email.com",
        ),
        (
            " KEY   (email)=(imagesecrets@email.org) already exists.",
            "email",
            "imagesecrets@email.org",
        ),
        (
            "(username)=(username)) already exists.",
            "username",
            "username)",
        ),
    ],
)
def test_integrity_match(full_string: str, match1: str, match2: str) -> None:
    """Test that the integrity_field matches correct substrings."""
    result = INTEGRITY_FIELD.findall(full_string)[0]
    assert result[0] == match1
    assert result[1] == match2


@pytest.mark.parametrize("string", [" ", " user", "name ", "user name"])
def test_username_whitespace_fail(string: str) -> None:
    """Test that the username regex fails if a whitespace char is in the string."""
    assert not USERNAME.fullmatch(string)


@pytest.mark.parametrize("string", ["1", " 12345", "128" * 43])
def test_username_length_fail(string: str) -> None:
    """Test that the username regex fails due to incorrect length."""
    assert not USERNAME.fullmatch(string)


@pytest.mark.parametrize("string", ["username", "qwerty12", "test" * 10])
def test_username_match(string: str) -> None:
    """Test that the username regex matches correct strings."""
    assert USERNAME.fullmatch(string)
