"""Test the array_util module."""

from __future__ import annotations

import functools as fn
from typing import TYPE_CHECKING

import numpy as np
import pytest

from imagesecrets.core.util import array

if TYPE_CHECKING:
    from numpy.typing import ArrayLike

# no need to repeat dtype again
np.array = fn.partial(np.array, dtype=np.uint8)


@pytest.mark.parametrize(
    "message, bits, expected_arr",
    [
        (" ", 1, np.array(([0], [0], [1], [0], [0], [0], [0], [0]))),
        ("A", 1, np.array(([0], [1], [0], [0], [0], [0], [0], [1]))),
        ("1", 1, np.array(([0], [0], [1], [1], [0], [0], [0], [1]))),
        ("22", 2, np.array(([0], [0], [1], [1], [0], [0], [1], [0]) * 2)),
        ("333", 3, np.array(([0], [0], [1], [1], [0], [0], [1], [1]) * 3)),
        ("4444", 4, np.array(([0], [0], [1], [1], [0], [1], [0], [0]) * 4)),
        ("55555", 5, np.array(([0], [0], [1], [1], [0], [1], [0], [1]) * 5)),
        ("666666", 6, np.array(([0], [0], [1], [1], [0], [1], [1], [0]) * 6)),
        ("7777777", 7, np.array(([0], [0], [1], [1], [0], [1], [1], [1]) * 7)),
        (
            "88888888",
            8,
            np.array(([0], [0], [1], [1], [1], [0], [0], [0]) * 8),
        ),
        ("Z" * 50, 1, np.array(([0], [1], [0], [1], [1], [0], [1], [0]) * 50)),
        ("&" * 50, 5, np.array(([0], [0], [1], [0], [0], [1], [1], [0]) * 50)),
    ],
)
def test_message_bit_array(
    message: str,
    bits: int,
    expected_arr: ArrayLike,
    delimiter_array,
) -> None:
    """Test the prepare message function.

    :param message: Message to turn into bit array
    :param bits: Number of bits to use
    :param expected_arr: Expected result
    :param delimiter_array: Delimiter array fixture

    """
    expected_arr = np.concatenate((expected_arr, delimiter_array))
    expected_arr.resize(
        (np.ceil(expected_arr.size / bits).astype(int), bits),
        refcheck=False,
    )

    arr, length = array.message_bit(message, "dlm", bits)

    np.testing.assert_array_equal(arr, expected_arr)
    assert length == expected_arr.size // bits


@pytest.mark.parametrize(
    "col_num, start_from_end",
    [
        (1, True),
        (2, True),
        (3, True),
        (1, False),
        (2, False),
        (3, False),
    ],
)
def test_edit_column(
    test_image_array: ArrayLike,
    col_num: int,
    start_from_end: bool,
) -> None:
    """Test the edit column function."""
    new = np.array([36, 56, 157, 61, 8, 95, 39, 140] * 24)

    bitlike_shape = (-1, 8)

    test_image_array = test_image_array.reshape(bitlike_shape)[
        : new.shape[0] // bitlike_shape[1]
    ].copy()
    new = new.reshape(-1, col_num)[: test_image_array.shape[0], :]

    if start_from_end:
        test_image_array[:, -col_num:] = new
    else:
        test_image_array[:, :col_num] = new

    result = array.edit_column(
        test_image_array.reshape(bitlike_shape),
        new,
        col_num,
        start_from_end,
    )

    np.testing.assert_array_equal(result, test_image_array)


def test_pack_and_concatenate(test_image_array) -> None:
    """Test the pack and concatenate function."""
    unpacked = np.array(
        [
            [0, 0, 0, 0, 1, 1, 1, 0],
            [1, 0, 0, 0, 0, 0, 1, 0],
            [0, 0, 0, 0, 1, 1, 1, 1],
            [1, 1, 1, 1, 0, 1, 1, 0],
            [0, 1, 0, 0, 1, 0, 1, 1],
            [1, 1, 0, 1, 1, 1, 0, 0],
            [0, 0, 1, 1, 0, 1, 1, 1],
            [1, 1, 0, 0, 0, 1, 1, 1],
            [1, 0, 1, 1, 1, 1, 0, 1],
            [0, 0, 1, 0, 0, 1, 0, 0],
            [1, 0, 0, 1, 0, 1, 1, 1],
            [1, 1, 1, 1, 1, 1, 0, 1],
            [0, 0, 1, 1, 0, 0, 1, 1],
            [1, 0, 0, 1, 0, 1, 0, 0],
            [0, 0, 0, 1, 0, 1, 0, 0],
            [0, 1, 1, 0, 0, 0, 0, 1],
            [0, 0, 0, 1, 1, 0, 1, 0],
            [1, 1, 0, 0, 1, 1, 0, 0],
            [1, 1, 0, 0, 1, 0, 0, 1],
            [1, 1, 1, 1, 1, 0, 1, 1],
        ],
    )

    result = array.pack_and_concatenate(
        unpacked.ravel(),
        test_image_array.ravel(),
        (-1,),
    )

    np.testing.assert_array_equal(
        result.ravel()[: -test_image_array.size],
        np.packbits(unpacked),
    )
