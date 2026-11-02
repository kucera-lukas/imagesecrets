"""Message decoding router."""

from __future__ import annotations

from typing import Union

from fastapi import (
    APIRouter,
    Depends,
    File,
    Form,
    HTTPException,
    UploadFile,
    status,
)
from fastapi.responses import JSONResponse

from imagesecrets.api import dependencies, exceptions, responses
from imagesecrets.api.routers.user.main import manager
from imagesecrets.constants import MESSAGE_DELIMITER
from imagesecrets.core import decode
from imagesecrets.core.util import image
from imagesecrets.database.image import models
from imagesecrets.database.image.services import ImageService
from imagesecrets.database.user.models import User
from imagesecrets.schemas import image as schemas

router = APIRouter(
    tags=["decode"],
    dependencies=[Depends(dependencies.get_config)],
    responses=responses.AUTHORIZATION,  # type: ignore
)


@router.get(
    "/decode",
    response_model=list[schemas.Image],
    status_code=status.HTTP_200_OK,
    summary="Decoded images",
)
async def get(
    image_service: ImageService = Depends(ImageService.from_session),
    current_user: User = Depends(manager),
) -> list[models.DecodedImage]:
    """Return all decoded images.

    \f
    :param current_user: Current user dependency

    """
    return await image_service.get_decoded(user_id=current_user.id)


@router.post(
    "/decode",
    response_model=schemas.Image,
    status_code=status.HTTP_201_CREATED,
    summary="Decode a message",
    responses=responses.MESSAGE_NOT_FOUND | responses.MEDIA,  # type: ignore
)
async def post(
    image_service: ImageService = Depends(ImageService.from_session),
    current_user: User = Depends(manager),
    file: UploadFile = File(
        ...,
        description="The image from which to decode the message.",
    ),
    delim: str = Form(
        default=MESSAGE_DELIMITER,
        alias="custom-delimiter",
        description="The previously defined message delimiter.",
        min_length=1,
    ),
    lsb_n: int = Form(
        default=1,
        alias="least-significant-bit-amount",
        description="Number of least significant bits which have been used to encode the message.",
        ge=1,
        le=8,
    ),
) -> Union[models.DecodedImage, JSONResponse]:
    """Decode a message from an image.

    - **custom-delimiter**: String which identifies the end of the encoded message.
    - **least-significant-bit-amount**: Number of least significant bits which was used to encode the message.
    - **file**: The image from which to decode a message.

    \f
    :param current_user: Current user dependency
    :param file: Source image
    :param delim: Message delimiter
    :param lsb_n: Number of lsb

    :raises UnsupportedMediaType: if file is not a png image

    """
    headers = {
        "custom-delimiter": delim,
        "least-significant-bit-amount": repr(lsb_n),
    }
    image_data = await file.read()
    assert isinstance(image_data, bytes)

    if not image.png_filetype(image_data) or not isinstance(image_data, bytes):
        raise exceptions.UnsupportedMediaType(headers=headers)  # type: ignore

    try:
        decoded, fp = decode.api(
            image_data=image_data,
            delimiter=delim,
            lsb_n=lsb_n,
            reverse=False,
        )
    except StopIteration as e:
        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={"detail": e.args[0]},
            headers=headers,
        )
    db_schema = schemas.ImageCreate(
        delimiter=delim,
        lsb_amount=lsb_n,
        message=decoded,
        image_name=file.filename,
        filename=fp.name,
    )
    db_image = await image_service.create_decoded(
        user_id=current_user.id,
        data=db_schema,
    )
    return db_image


@router.get(
    "/decode/{image_name}",
    response_model=list[schemas.Image],
    status_code=status.HTTP_200_OK,
    summary="Decoded image",
    responses=responses.NOT_FOUND,  # type: ignore
)
async def get_images(
    image_name: str,
    current_user: User = Depends(manager),
    image_service: ImageService = Depends(ImageService.from_session),
) -> list[models.DecodedImage]:
    """Return decoded image with the specified name.

    \f
    :param image_name: Name of the image
    :param current_user: Current user dependency

    """
    images = await image_service.get_decoded(
        user_id=current_user.id,
        image_name=image_name,
    )
    if not images:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"no decoded image(s) with name {image_name!r} found",
        )
    return images


__all__ = ["decode", "router"]
