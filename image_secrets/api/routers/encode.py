"""Message encoding router."""
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
from fastapi.responses import FileResponse, JSONResponse

from image_secrets.api import dependencies, exceptions, responses
from image_secrets.api.routers.user.main import manager
from image_secrets.backend import encode
from image_secrets.backend.database.image import crud, schemas
from image_secrets.backend.database.user import models
from image_secrets.backend.util import image
from image_secrets.settings import MESSAGE_DELIMITER

if TYPE_CHECKING:
    from image_secrets.backend.database.image.models import Image

router = APIRouter(
    tags=["encode"],
    dependencies=[Depends(dependencies.get_config)],
    responses=responses.AUTHORIZATION,  # type: ignore
)


@router.get(
    "/encode",
    response_model=list[Optional[schemas.Image]],
    status_code=status.HTTP_200_OK,
    summary="Encoded images",
)
async def get(
    current_user: models.User = Depends(manager),
) -> list[Optional[Image]]:
    """Return all encoded images.

    \f
    :param current_user: Current user dependency

    """
    images = await crud.get_encoded(user=current_user)
    return images


@router.post(
    "/encode",
    status_code=status.HTTP_201_CREATED,
    response_class=FileResponse,
    summary="Encode a message into an image",
    responses=responses.MEDIA,  # type: ignore
)
async def encode_message(
    current_user: models.User = Depends(manager),
    message: str = Form(
        ...,
        title="Message to encode",
        description="The message to encode into the image.",
        min_length=1,
        example="My secret message!",
    ),
    file: UploadFile = File(
        ...,
        media_type="image/png",
        description="The image in which to encode the message.",
    ),
    delim: str = Form(
        MESSAGE_DELIMITER,
        alias="custom-delimiter",
        description="""String which is going to be appended to the end of your message
        so that the message can be decoded later.""",
        min_length=1,
    ),
    lsb_n: int = Form(
        1,
        alias="least-significant-bit-amount",
        description="Number of least significant bits to alter.",
        ge=1,
        le=8,
    ),
) -> Union[FileResponse, JSONResponse]:
    """Encode a message into an image.

    - **message**: The message to encode into the image
    - **file**: The image
    - **custom-delimiter**: String which is going to be appended to the end of your message
        so that the message can be decoded later.
    - **least-significant-bit-amount**: Number of least significant bits to alter.

    \f
    :param current_user: Current user dependency
    :param message: Message to encode
    :param file: Source image
    :param delim: Message delimiter, defaults to 'MESSAGE_DELIMITER'
    :param lsb_n: Number of lsb to use, defaults to 1

    :raises UnsupportedMediaType: if file is not a png image

    """
    headers = {
        "image-name": file.filename,
        "message": message,
        "delimiter": delim,
        "lsb_amount": repr(lsb_n),
    }
    image_data = await file.read()
    assert isinstance(image_data, bytes)

    if not image.png_filetype(image_data):
        raise exceptions.UnsupportedMediaType(headers=headers)  # type: ignore

    try:
        fp = encode.api(
            message=message,
            file=image_data,
            delimiter=delim,
            lsb_n=lsb_n,
            reverse=False,
        )
    except ValueError as e:
        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            content={"detail": e.args[0], "field": "file"},
            headers=headers,
        )
    image_schema = schemas.ImageCreate(
        delimiter=delim,
        lsb_amount=lsb_n,
        message=message,
        image_name=file.filename,
        filename=fp.name,
    )
    await crud.create_encoded(owner_id=current_user.id, data=image_schema)
    return FileResponse(
        path=fp,
        status_code=status.HTTP_201_CREATED,
        media_type="image/png",
        filename=image_schema.filename,
        headers=headers,
    )


@router.get(
    "/encode/{image_name}",
    response_model=list[schemas.Image],
    status_code=status.HTTP_200_OK,
    summary="Encoded image",
    responses=responses.NOT_FOUND,  # type: ignore
)
async def get_images(
    image_name: str,
    current_user: models.User = Depends(manager),
) -> list[Image]:
    """Return encoded image with the specified name.

    \f
    :param image_name: Name of the image
    :param current_user: Current user dependency

    """
    images = await crud.get_encoded(user=current_user)
    if not images:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"no encoded image(s) with name {image_name!r} found",
        )
    return images  # type: ignore


__all__ = [
    "encode_message",
    "router",
]
