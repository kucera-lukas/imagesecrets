"""Database services for Image models."""

from __future__ import annotations

from pathlib import Path
from typing import Optional, Type, TypeVar

from sqlalchemy import select

from imagesecrets.database.base import Base
from imagesecrets.database.image.models import DecodedImage, EncodedImage
from imagesecrets.database.service import DatabaseService
from imagesecrets.schemas import image

_I = TypeVar("_I", bound=Base)


class ImageService(DatabaseService):
    """Database service for Image models."""

    async def _get(
        self,
        model: Type[_I],
        user_id: int,
        image_name: Optional[str] = None,
    ) -> list[_I]:
        """Return User images stored in database.

        :param model: Database model to return
        :param user_id: User model stored in database
        :param image_name: Constraint for image_name field, defaults to None
            (all images are returned)

        """
        stmt = select(model).where(model.user_id == user_id)

        if image_name:
            stmt = stmt.where(
                # ILIKE is not case sensitive
                model.image_name.ilike(
                    # user might or might not omit extension
                    # that's why we add it manually every time
                    f"{str(Path(image_name).with_suffix(''))}.png",
                ),
            )

        result = await self._session.execute(stmt)

        return [row for row in result.scalars()]

    async def get_decoded(
        self,
        user_id: int,
        image_name: Optional[str] = None,
    ) -> list[DecodedImage]:
        """Return User decoded images stored in database.

        :param user_id: User database id
        :param image_name: Optional name of the images to return

        """
        return await self._get(
            model=DecodedImage,
            user_id=user_id,
            image_name=image_name,
        )

    async def get_encoded(
        self,
        user_id: int,
        image_name: Optional[str] = None,
    ) -> list[EncodedImage]:
        """Return User encoded images stored in database.

        :param user_id: User database id
        :param image_name: Optional name of the images to return

        """
        return await self._get(
            model=EncodedImage,
            user_id=user_id,
            image_name=image_name,
        )

    async def create_decoded(
        self,
        user_id: int,
        data: image.ImageCreate,
    ) -> DecodedImage:
        """Insert a new encoded image.

        :param user_id: User foreign key
        :param data: Image information

        """
        image = DecodedImage(user_id=user_id, **data.dict())  # noqa

        async with self._session.begin_nested():
            self._session.add(image)

        return image

    async def create_encoded(
        self,
        user_id: int,
        data: image.ImageCreate,
    ) -> EncodedImage:
        """Insert a new decoded image.

        :param user_id: User foreign key
        :param data: Image information

        """
        image = EncodedImage(user_id=user_id, **data.dict())  # noqa

        async with self._session.begin_nested():
            self._session.add(image)

        return image
