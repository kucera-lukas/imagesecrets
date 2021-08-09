"""Utility functions for working with numpy arrays."""
from __future__ import annotations

from typing import TYPE_CHECKING

import numpy as np

if TYPE_CHECKING:
    from numpy.typing import ArrayLike


def message_bit(
    message: str,
    delimiter: str,
    bits: int,
) -> tuple[ArrayLike, int]:
    """Return a message turned into bits in an array.

    :param message: Main message to encode
    :param delimiter: Message end identifier
    :param bits: Amount of bits per pixel

    """
    byte_msg: bytes = (message + delimiter).encode("utf-8")

    msg_arr = np.frombuffer(byte_msg, dtype=np.uint8)
    lsbits_arr = np.unpackbits(msg_arr)
    lsbits_arr.resize(  # resize fills with zeros if shape doesn't match fully
        (np.ceil(lsbits_arr.size / bits).astype(int), bits),
        refcheck=False,
    )
    msg_len, _ = lsbits_arr.shape

    return lsbits_arr, msg_len


def edit_column(
    base: ArrayLike,
    new: ArrayLike,
    column_num: int,
    start_from_end: bool = False,
) -> ArrayLike:
    """Replace elements in base array with a new array.

    :param base: Main array to edit
    :param new: New data to put into the main array
    :param column_num: Number of columns of the main base array to edit
    :param start_from_end: If indexing of cols should start from the last column
        rather than from first one, defaults to False

    """
    if start_from_end:
        base[:, -column_num:] = new  # type: ignore
    else:
        base[:, :column_num] = new  # type: ignore
    return base


def pack_and_concatenate(
    unpacked: ArrayLike,
    base: ArrayLike,
    final_shape: tuple,
) -> ArrayLike:
    """Pack bits of the first array and then concatenate it with the base one, lastly reshape it.

    :param unpacked: The packed array with the encoded data
    :param base: Main array with the pixel data
    :param final_shape: Shape of the original image array

    """
    packed_arr = np.packbits(unpacked)
    final: ArrayLike = np.concatenate((packed_arr, base)).reshape(final_shape)
    return final
