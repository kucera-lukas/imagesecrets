"""Test the module used for decoding."""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

import numpy as np
import pytest

from imagesecrets.constants import API_IMAGES
from imagesecrets.core import decode

if TYPE_CHECKING:
    from numpy.typing import ArrayLike
    from py.path import local
    from pytest_mock import MockFixture


@pytest.mark.parametrize("lsb_n", [1, 2, 3, 4, 5, 6, 7, 8])
def test_prepare_array(test_image_array: ArrayLike, lsb_n: int) -> None:
    """Test the prepare array function."""
    result = decode.prepare_array(test_image_array, lsb_n, False)

    assert np.ceil(test_image_array.size / result.size) == np.ceil(8 / lsb_n)
    assert result.ndim == 1

    np.testing.assert_array_equal(
        np.unpackbits(test_image_array).reshape(-1, 8)[:, -lsb_n:],
        np.unpackbits(result).reshape(-1, lsb_n),
    )


@pytest.mark.parametrize("lsb_n", [-1, 0, 9, 1000])
def test_prepare_array_raises(lsb_n: int):
    """Test that the prepare array function raises value error if invalid lsb_n arg is passed in."""
    with pytest.raises(ValueError):
        decode.prepare_array(..., lsb_n, ...)


@pytest.mark.parametrize(
    "text",
    ["", " ", "hello", "987654321", "~!@#$%^&*()_"],
)
def test_decode_text(text: str) -> None:
    """Test the decode text function."""
    ascii_msg = map(ord, f"{text}dlm___decode noise")

    result = decode.decode_text(np.fromiter(ascii_msg, dtype=np.uint8), "dlm")

    assert not result.endswith("dlm")
    np.testing.assert_string_equal(result, text)


def test_decode_text_raises(
    test_image_array: ArrayLike,
) -> None:
    """Test that the decode_text function raises StopIteration with wrong input."""
    with pytest.raises(StopIteration):
        decode.decode_text(test_image_array.ravel(), "fake delimiter")


@pytest.mark.parametrize(
    "delimiter, lsb_n",
    [
        ("delimiter1", 1),
        ("delimiter2", 2),
        ("delimiter3", 3),
        ("delimiter4", 4),
        ("delimiter5", 5),
        ("delimiter6", 6),
        ("delimiter7", 7),
        ("delimiter8", 8),
    ],
)
def test_main(mocker: MockFixture, delimiter: str, lsb_n: int) -> None:
    """Test the main function."""
    arr = np.fromiter(map(ord, f"Hello{lsb_n}{delimiter}"), dtype=np.uint8)
    mocker.patch(
        "imagesecrets.core.decode.prepare_array",
        return_value=arr,
    )
    result = decode.main(
        ...,
        delimiter,
        lsb_n,
    )
    assert result == f"Hello{lsb_n}"


@pytest.mark.parametrize(
    "image_data, delimiter, lsb_n",
    [(b"image_data", "delimiter", 1)],
)
def test_api(
    mocker: MockFixture,
    tmpdir: local,
    image_data: bytes,
    delimiter: str,
    lsb_n: int,
) -> None:
    """Test the api decode function."""
    tmpdir = Path(tmpdir.mkdir("tmp/"))

    read_bytes = mocker.patch(
        "imagesecrets.core.util.image.read_bytes",
        return_value="bytes read",
    )
    data = mocker.patch(
        "imagesecrets.core.util.image.data",
        return_value=(..., "array"),
    )
    main = mocker.patch(
        "imagesecrets.core.decode.main",
        retuen_value="Message",
    )
    save_array = mocker.patch(
        "imagesecrets.core.util.image.save_array",
        return_value=tmpdir / "image.png",
    )

    decode.api(image_data, delimiter, lsb_n, False)
    read_bytes.assert_called_once_with(image_data)
    data.assert_called_once_with("bytes read")
    main.assert_called_once_with("array", delimiter, lsb_n, False)
    save_array.assert_called_once_with("array", image_dir=API_IMAGES)
