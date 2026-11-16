"""Module with functions to decode text from images."""

from __future__ import annotations

from typing import TYPE_CHECKING

import numpy as np

from imagesecrets.constants import API_IMAGES, MESSAGE_DELIMITER
from imagesecrets.core.util import image

if TYPE_CHECKING:
    from pathlib import Path

    from numpy.typing import ArrayLike


def api(
    image_data: bytes,
    delimiter: str,
    lsb_n: int,
    reverse: bool,
    *,
    image_dir: Path = API_IMAGES,
) -> tuple[str, Path]:
    """Function to be used by the corresponding decode API endpoint.

    :param image_data: Data of the image uploaded by user
    :param delimiter: Message end identifier
    :param lsb_n: Number of least significant bits to decode
    :param reverse: Reverse decoding bool
    :param image_dir: Directory where to save the image

    """
    data = image.read_bytes(image_data)
    _, arr = image.data(data)
    text = main(arr, delimiter, lsb_n, reverse)
    fp = image.save_array(arr, image_dir=image_dir)
    return text, fp


def main(
    array: ArrayLike,
    delimiter: str = MESSAGE_DELIMITER,
    lsb_n: int = 1,
    reverse: bool = False,
) -> str:
    """Decode text from an image.

    :param array: Numpy array with pixel image data
    :param delimiter: Message end identifier, defaults to the one in .settings
    :param lsb_n: Number of least significant bits to decode, defaults to 1
    :param reverse: Reverse decoding bool, defaults to False

    """
    arr = prepare_array(array, lsb_n, reverse)
    return decode_text(arr, delimiter)


def prepare_array(array: ArrayLike, lsb_n: int, reverse: bool) -> ArrayLike:
    """Prepare an array into a form from which it is easy to decode text.

    :param array: The array to work with
    :param lsb_n: How many lsb to use
    :param reverse: Whether the array should be flipped or not

    """
    if not 1 <= lsb_n <= 8:
        raise ValueError(
            f"{lsb_n!r} is not a valid amount of least significant bits, must be within {range(1,9)!r}.",
        )

    shape = (-1, 8)
    if reverse:  # pragma: no cover
        array = np.flip(array)
    arr = np.unpackbits(array).reshape(shape)
    # cut unnecessary bits and pack the rest
    return_arr: ArrayLike = np.packbits(arr[:, -lsb_n:])
    return return_arr


def decode_text(array: ArrayLike, delimiter: str) -> str:
    """Decode text from the given array.

    :param array: The array from which to decode the text
    :param delimiter: Identifier that whole message has been extracted

    :raises StopIteration: if nothing was found in the array

    """
    text = ""
    delim_len = len(delimiter)

    # iterating is faster than vectorizing 'chr' on the whole array,
    # many slow string operation are avoided
    for num in array:  # type: ignore
        text += chr(num)  # type: ignore
        if text.endswith(delimiter):
            return text[:-delim_len]
    raise StopIteration("No message found after scanning the whole image.")
