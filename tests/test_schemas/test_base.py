"""Test the base schemas module."""

import pytest

from imagesecrets.schemas import base


@pytest.mark.parametrize(
    "key, result",
    [
        ("", ""),
        ("a", "A"),
        ("A", "A"),
        ("camel", "Camel"),
        ("camel_case", "CamelCase"),
    ],
)
def test_pretty_key(key: str, result: str) -> None:
    """Test the pretty_key function."""
    output = base.pretty_key(key)

    assert output == result


def test_pretty_key_in_alias() -> None:
    """Test the pretty_key function with a key with knows alias."""
    output = base.pretty_key("swagger_url")

    assert output == "SwaggerUI"
