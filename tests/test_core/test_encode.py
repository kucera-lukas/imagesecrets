"""Test the module used for encoding."""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

import numpy as np
import pytest

from imagesecrets.core import encode

if TYPE_CHECKING:
    from numpy.typing import ArrayLike
    from pytest_mock import MockFixture


@pytest.mark.parametrize("message_len", [0, 10, 11, 100, 192])
def test_prepare_image(
    mocker: MockFixture,
    test_image_array: ArrayLike,
    message_len: int,
) -> None:
    """Test the prepare_image function."""
    mocker.patch(
        "imagesecrets.core.util.image.data",
        return_value=(test_image_array.shape, test_image_array),
    )
    shape, base_arr, unpacked_arr = encode.prepare_image(..., message_len)

    assert shape[-1] == 3
    assert shape == test_image_array.shape

    assert base_arr.ndim == 1
    assert base_arr.dtype == np.uint8
    assert np.logical_and(base_arr >= 0, base_arr <= 255).all()

    assert unpacked_arr.ndim == 2
    assert unpacked_arr.shape == (message_len, 8)
    np.testing.assert_array_equal(unpacked_arr, unpacked_arr.astype(bool))


def test_api(
    tmpdir,
    mocker: MockFixture,
    test_image_array: ArrayLike,
) -> None:
    """Test the api encoding function."""
    tmpdir = Path(tmpdir.mkdir("tmp/"))

    mocker.patch(
        "imagesecrets.core.util.image.read_bytes",
        return_value=...,
    )
    mocker.patch(
        "imagesecrets.core.encode.main",
        return_value=test_image_array,
    )

    result = encode.api(..., ..., ..., ..., ..., image_dir=tmpdir)

    assert isinstance(result, Path)
    assert result.is_file()
    assert result.parent.name == "tmp"
    assert len(result.stem) == 16
    assert result.suffix == ".png"


@pytest.mark.parametrize(
    "message, lsb_n",
    [
        (b"0", 1),
        (b"   ", 2),
        (b"1234", 3),
        (b"xyz+", 4),
    ],
)
def test_main(
    test_image_path: Path,
    test_image_array: ArrayLike,
    message: bytes,
    lsb_n: int,
) -> None:
    """Test the main encoding function."""
    result = encode.main(message.decode(), test_image_path, "", lsb_n)
    with pytest.raises(AssertionError):
        np.testing.assert_array_equal(result, test_image_array)


def test_main_raises_value_error(test_image_path) -> None:
    """Test the the main encode function raises ValueError correctly."""
    with pytest.raises(ValueError):
        encode.main("Hello" * 1000, test_image_path)
