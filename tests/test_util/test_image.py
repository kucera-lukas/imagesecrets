"""Test the image_util module."""
from __future__ import annotations

from typing import TYPE_CHECKING

import numpy as np
import pytest

from image_secrets.backend.util import image

if TYPE_CHECKING:
    from pathlib import Path


@pytest.mark.parametrize(
    "bytes_",
    [
        b"",
        b"qwerty",
        b"123456789",
        b"~!@#$%^&**()",
    ],
)
def test_read_image_bytes(bytes_: bytes) -> None:
    """Test the read_image_bytes function.

    :param bytes_: Bytes to read

    """
    num = np.random.randint(0, 10)
    assert image.read_bytes(bytes_).read(num) == bytes_[:num]


def test_image_data(test_image_path: Path) -> None:
    """Test the image_data function."""
    shape, arr = image.data(test_image_path)

    assert arr.ndim == 3
    assert arr.dtype == np.uint8
    assert arr.max() <= 255
    assert arr.min() >= 0

    assert shape[-1] == 3
