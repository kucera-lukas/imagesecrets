"""Message decoding router."""
from __future__ import annotations

from typing import TYPE_CHECKING, Optional, Union

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

from image_secrets.api import dependencies, exceptions, responses
from image_secrets.api.routers.user.main import manager
from image_secrets.backend import decode
from image_secrets.backend.database.image import crud, schemas
from image_secrets.backend.database.user import models
from image_secrets.backend.util import image
from image_secrets.settings import MESSAGE_DELIMITER

if TYPE_CHECKING:
    from image_secrets.backend.database.image.models import Image

router = APIRouter(
    tags=["decode"],
    dependencies=[Depends(dependencies.get_config)],
    responses=responses.AUTHORIZATION,  # type: ignore
)


@router.get(
    "/decode",
    response_model=list[Optional[schemas.Image]],
    status_code=status.HTTP_200_OK,
    summary="Decoded images",
)
async def get(
    current_user: models.User = Depends(manager),
) -> list[Optional[Image]]:
    """Return all decoded images.

    \f
    :param current_user: Current user dependency

    """
    images = await crud.get_decoded(user=current_user)
    return images


@router.post(
    "/decode",
    response_model=schemas.Image,
    status_code=status.HTTP_201_CREATED,
    summary="Decode a message",
    responses=responses.MESSAGE_NOT_FOUND | responses.MEDIA,  # type: ignore
)
async def post(
    current_user: models.User = Depends(manager),
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
) -> Union[schemas.Image, JSONResponse]:
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

    if not image.png_filetype(image_data):
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
    db_image = await crud.create_decoded(
        owner_id=current_user.id,
        data=db_schema,
    )
    schema: schemas.Image = await schemas.Image.from_tortoise_orm(db_image)
    return schema


@router.get(
    "/decode/{image_name}",
    response_model=list[schemas.Image],
    status_code=status.HTTP_200_OK,
    summary="Decoded image",
    responses=responses.NOT_FOUND,  # type: ignore
)
async def get_images(
    image_name: str,
    current_user: models.User = Depends(manager),
) -> list[Image]:
    """Return decoded image with the specified name.

    \f
    :param image_name: Name of the image
    :param current_user: Current user dependency

    """
    images = await crud.get_decoded(user=current_user, image_name=image_name)
    if not images:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"no decoded image(s) with name {image_name!r} found",
        )
    return images  # type: ignore


__all__ = ["decode", "router"]
