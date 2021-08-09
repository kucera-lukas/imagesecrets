"""CRUD operation with images via database."""
from __future__ import annotations

from typing import TYPE_CHECKING, Optional

from image_secrets.backend.database.image import models, schemas

if TYPE_CHECKING:
    from image_secrets.backend.database.user.models import User


async def _get(
    relation: str,
    user: User,
    image_name: Optional[str] = None,
) -> list[Optional[models.Image]]:
    """Return User images stored in database.

    :param relation: Either decoded_images or encoded_images
    :param user: User model stored in database
    :param image_name: Constraint for image_name field, defaults to None
        (all images are returned)

    """
    await user.fetch_related(relation)
    field = getattr(user, relation)

    return [
        # not using ``from_tortoise_orm`` because it would try to prefetch the owner FK relation
        # resulting in a very messy result
        # every image would have their ``owner`` field
        # with the full ``User`` model
        schemas.Image.from_orm(img)
        async for img in field
        # short-circuit if no constraint given
        if not image_name
        or image_name
        in {
            img.image_name,
            # user might omit extension
            img.image_name.rstrip(".png"),
        }
    ]


async def get_decoded(
    user: User,
    image_name: str | None = None,
) -> list[Optional[models.Image]]:
    """Return User decoded images stored in database.

    :param user: User model stored in database
    :param image_name: Optional name of the images to return

    """
    return await _get(
        relation="decoded_images",
        user=user,
        image_name=image_name,
    )


async def get_encoded(
    user: User,
    image_name: str | None = None,
) -> list[Optional[models.Image]]:
    """Return User encoded images stored in database.

    :param user: User model stored in database
    :param image_name: Optional name of the images to return

    """
    return await _get(
        relation="encoded_images",
        user=user,
        image_name=image_name,
    )


async def create_decoded(
    owner_id: int,
    data: schemas.ImageCreate,
) -> models.DecodedImage:
    """Insert a new encoded image.

    :param owner_id: User foreign key
    :param data: Image information

    """
    image = await models.DecodedImage.create(owner_id=owner_id, **data.dict())
    return image


async def create_encoded(
    owner_id: int,
    data: schemas.ImageCreate,
) -> models.EncodedImage:
    """Insert a new decoded image.

    :param owner_id: User foreign key
    :param data: Image information

    """
    image = await models.EncodedImage.create(owner_id=owner_id, **data.dict())
    return image
