"""Module with functions to encode text into images."""
from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

import numpy as np

from image_secrets.backend.util import array, image
from image_secrets.settings import API_IMAGES, MESSAGE_DELIMITER

if TYPE_CHECKING:
    from typing import Union

    from _io import BytesIO
    from numpy.typing import ArrayLike


def api(
    message: str,
    file: bytes,
    delimiter: str,
    lsb_n: int,
    reverse: bool,
    *,
    image_dir: Path = API_IMAGES,
) -> Path:
    """Encode interface for the corresponding API endpoint.

    :param message: Message to encode
    :param file: Data of the image uploaded by user
    :param delimiter: Message end identifier
    :param lsb_n: Number of least significant bits to use
    :param reverse: Reverse encoding bool
    :param image_dir: Directory where to save the final image

    """
    data = image.read_bytes(file)
    arr = main(message, data, delimiter, lsb_n, reverse)
    return image.save_array(arr, image_dir=image_dir)


def main(
    message: str,
    data: Union[BytesIO, Path],
    delimiter: str = MESSAGE_DELIMITER,
    lsb_n: int = 1,
    reverse: bool = False,
) -> ArrayLike:
    """Main encoding interface.

    :param message: Message to encode
    :param data: Pixel image data which can be converted to numpy array by PIL
    :param delimiter: Message end identifier, defaults to 'MESSAGE_DELIMITER'
    :param lsb_n: Number of least significant bits to decode, defaults to 1
    :param reverse: Reverse decoding bool, defaults to False

    :raises ValueError: if the message is too long for the image

    """
    msg_arr, msg_len = array.message_bit(message, delimiter, lsb_n)
    shape, img_arr, unpacked_arr = prepare_image(data, msg_len)

    if (size := img_arr.size * lsb_n) < (msg_len := len(message)):  # type: ignore
        raise ValueError(
            f"The image size ({size:,.0f}) is not enough for the message ({msg_len:,.0f})",
        )

    if reverse:  # pragma: no cover
        msg_arr, img_arr = np.flip(msg_arr), np.flip(
            img_arr,
        )  # all axes get flipped

    enc_arr = array.edit_column(
        unpacked_arr,
        msg_arr,
        column_num=lsb_n,
        start_from_end=True,
    )
    final_arr = array.pack_and_concatenate(enc_arr, img_arr, shape)

    return final_arr if not reverse else np.flip(final_arr)


def prepare_image(
    data: BytesIO,
    message_len: int,
) -> tuple[tuple[int, int, int], ArrayLike, ArrayLike]:
    """Prepare an image for encoding.

    :param data: Pixel image data which can be converted to numpy array by PIL
    :param message_len: Length of the message which will be encoded

    """
    shape, arr = image.data(data)

    arr = arr.ravel()  # type: ignore
    unpacked_arr = np.unpackbits(
        # unpack only needed ones, instead of millions
        arr[:message_len],
    )

    return shape, arr[message_len:], unpacked_arr.reshape(-1, 8)
