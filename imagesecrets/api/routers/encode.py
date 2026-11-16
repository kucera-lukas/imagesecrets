"""Message encoding router."""

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
from fastapi.responses import FileResponse, JSONResponse
from starlette.background import BackgroundTasks

from imagesecrets.api import dependencies, exceptions, responses
from imagesecrets.api.routers.user.main import manager
from imagesecrets.constants import MESSAGE_DELIMITER
from imagesecrets.core import encode
from imagesecrets.core.util import image
from imagesecrets.database.image import models
from imagesecrets.database.image.services import ImageService
from imagesecrets.database.user.models import User
from imagesecrets.schemas import image as schemas

router = APIRouter(
    tags=["encode"],
    dependencies=[Depends(dependencies.get_config)],
    responses=responses.AUTHORIZATION,  # type: ignore
)


@router.get(
    "/encode",
    response_model=list[schemas.Image],
    status_code=status.HTTP_200_OK,
    summary="Encoded images",
)
async def get(
    image_service: ImageService = Depends(ImageService.from_session),
    current_user: User = Depends(manager),
) -> list[models.DecodedImage]:
    """Return all encoded images.

    \f
    :param current_user: Current user dependency

    """
    return await image_service.get_encoded(user_id=current_user.id)


@router.post(
    "/encode",
    status_code=status.HTTP_201_CREATED,
    response_class=FileResponse,
    summary="Encode a message into an image",
    responses=responses.MEDIA,  # type: ignore
)
async def encode_message(
    background_tasks: BackgroundTasks,
    image_service: ImageService = Depends(ImageService.from_session),
    current_user: User = Depends(manager),
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
    :param image_service: ``ImageService`` instance
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

    if not image.png_filetype(image_data) or not isinstance(image_data, bytes):
        raise exceptions.UnsupportedMediaType(headers=headers)

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
    background_tasks.add_task(
        image_service.create_encoded,
        user_id=current_user.id,
        data=image_schema,
    )
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
    current_user: User = Depends(manager),
    image_service: ImageService = Depends(ImageService.from_session),
) -> list[models.EncodedImage]:
    """Return encoded image with the specified name.

    \f
    :param image_name: Name of the image
    :param current_user: Current user dependency

    """
    images = await image_service.get_encoded(
        user_id=current_user.id,
        image_name=image_name,
    )
    if not images:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"no encoded image(s) with name {image_name!r} found",
        )
    return images


__all__ = [
    "encode_message",
    "router",
]
