"""Test the CRUD module for images."""
from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

from image_secrets.backend.database.image import crud

if TYPE_CHECKING:
    from unittest.mock import AsyncMock, MagicMock

    from pytest_mock import MockFixture

    from image_secrets.backend.database.image.models import (
        DecodedImage,
        EncodedImage,
    )
    from image_secrets.backend.database.image.schemas import ImageCreate
    from image_secrets.backend.database.user.models import User


@pytest.fixture()
def mock_from_orm(mocker: MockFixture):
    """Return mocked schemas.Image.from_orm function."""
    return mocker.patch(
        "image_secrets.backend.database.image.schemas.Image.from_orm",
        return_value="test_image",
    )


@pytest.fixture()
def image_create() -> ImageCreate:
    """Return an ``ImageCreate`` schema."""
    from image_secrets.backend.database.image import schemas

    return schemas.ImageCreate(
        message="test_message",
        image_name="test_name",
        filename="test_filename.png",
    )


@pytest.fixture()
def decoded_image() -> DecodedImage:
    """Return a decoded image."""
    from image_secrets.backend.database.image import models

    return models.DecodedImage(
        filename="test_filename.png",
        image_name="test_image_name",
        message="test_message",
        delimiter="test_delimiter",
        lsb_amount=2,
    )


@pytest.fixture()
def encoded_image() -> EncodedImage:
    """Return an encoded image."""
    from image_secrets.backend.database.image import models

    return models.EncodedImage(
        filename="test_filename.png",
        image_name="test_image_name",
        message="test_message",
        delimiter="test_delimiter",
        lsb_amount=2,
    )


@pytest.fixture()
def mock_create_decoded(mocker: MockFixture, decoded_image: DecodedImage):
    """Return mocked DecodedImage.create function."""
    async_mock = mocker.AsyncMock(return_value=decoded_image)
    return mocker.patch(
        "image_secrets.backend.database.image.models.DecodedImage.create",
        side_effect=async_mock,
    )


@pytest.fixture()
def mock_create_encoded(mocker: MockFixture, encoded_image: EncodedImage):
    """Return mocked EncodedImage.create function."""
    async_mock = mocker.AsyncMock(return_value=encoded_image)
    return mocker.patch(
        "image_secrets.backend.database.image.models.EncodedImage.create",
        side_effect=async_mock,
    )


@pytest.fixture()
def mock_get(mocker: MockFixture):
    """Mock the _get function."""
    async_mock = mocker.AsyncMock(return_value="_get called")
    return mocker.patch(
        "image_secrets.backend.database.image.crud._get",
        side_effect=async_mock,
    )


@pytest.mark.asyncio
async def test_create_decoded(
    mock_create_decoded: MagicMock,
    decoded_image: DecodedImage,
    image_create: ImageCreate,
) -> None:
    """Test the create_decoded function."""
    from image_secrets.backend.database.image import models

    result = await crud.create_decoded(0, image_create)

    assert isinstance(result, models.DecodedImage)
    assert result == decoded_image
    mock_create_decoded.assert_called_once_with(
        owner_id=0,
        **image_create.dict(),
    )


@pytest.mark.asyncio
async def test_create_encoded(
    mock_create_encoded: AsyncMock,
    encoded_image: EncodedImage,
    image_create: ImageCreate,
) -> None:
    """Test the create_encoded function."""
    from image_secrets.backend.database.image import models

    result = await crud.create_encoded(0, image_create)

    assert isinstance(result, models.EncodedImage)
    assert result == encoded_image
    mock_create_encoded.assert_called_once_with(
        owner_id=0,
        **image_create.dict(),
    )


@pytest.mark.asyncio
async def test__get_decoded_no_name(
    mock_from_orm: MagicMock,
    insert_user: User,
    insert_decoded: DecodedImage,
) -> None:
    """Test the _get function with decoded_image and no name."""
    result = await crud._get(
        relation="decoded_images",
        user=insert_user,
    )

    mock_from_orm.assert_called_once_with(insert_decoded)
    assert result == ["test_image"]


@pytest.mark.asyncio
async def test__get_decoded_with_name(
    mock_from_orm: MagicMock,
    insert_user: User,
    insert_decoded: DecodedImage,
) -> None:
    """Test the _get function with decoded_image and a specified name."""
    result = await crud._get(
        relation="decoded_images",
        user=insert_user,
        image_name=insert_decoded.image_name,
    )

    mock_from_orm.assert_called_once_with(insert_decoded)
    assert result == ["test_image"]


@pytest.mark.asyncio
async def test__get_decoded_with_unknown_name(
    mock_from_orm: MagicMock,
    insert_user: User,
    insert_decoded: DecodedImage,
) -> None:
    """Test the _get function with decoded_image and a specified name which does not match anything."""
    result = await crud._get(
        relation="decoded_images",
        user=insert_user,
        image_name="none",
    )

    mock_from_orm.assert_not_called()
    assert result == []


@pytest.mark.asyncio
async def test__get_encoded_no_name(
    mock_from_orm: MagicMock,
    insert_user: User,
    insert_encoded: EncodedImage,
) -> None:
    """Test the _get function with encoded_image and no name."""
    result = await crud._get(
        relation="encoded_images",
        user=insert_user,
    )

    mock_from_orm.assert_called_once_with(insert_encoded)
    assert result == ["test_image"]


@pytest.mark.asyncio
async def test__get_encoded_with_name(
    mock_from_orm: MagicMock,
    insert_user: User,
    insert_encoded: EncodedImage,
) -> None:
    """Test the _get function with encoded_image and a specified name."""
    result = await crud._get(
        relation="encoded_images",
        user=insert_user,
        image_name=insert_encoded.image_name,
    )

    mock_from_orm.assert_called_once_with(insert_encoded)
    assert result == ["test_image"]


@pytest.mark.asyncio
async def test__get_encoded_with_unknown_name(
    mock_from_orm: MagicMock,
    insert_user: User,
    insert_decoded: DecodedImage,
) -> None:
    """Test the _get function with encoded_image and a specified name which does not match anything."""
    result = await crud._get(
        relation="encoded_images",
        user=insert_user,
        image_name="none",
    )

    mock_from_orm.assert_not_called()
    assert result == []


@pytest.mark.asyncio
async def test_get_decoded_no_name(
    mock_get: AsyncMock,
    insert_user: User,
) -> None:
    """Test the get_decoded function without specifying image_name."""
    result = await crud.get_decoded(user=insert_user)

    mock_get.assert_called_once_with(
        relation="decoded_images",
        user=insert_user,
        image_name=None,
    )
    assert result == "_get called"


@pytest.mark.asyncio
@pytest.mark.parametrize("image_name", ("test_name", "..."))
async def test_get_decoded_with_name(
    mock_get: AsyncMock,
    insert_user: User,
    image_name: str,
) -> None:
    """Test the get_decoded function image_name."""
    result = await crud.get_decoded(user=insert_user, image_name=image_name)

    mock_get.assert_called_once_with(
        relation="decoded_images",
        user=insert_user,
        image_name=image_name,
    )
    assert result == "_get called"


@pytest.mark.asyncio
async def test_get_encoded_no_name(
    mock_get: AsyncMock,
    insert_user: User,
) -> None:
    """Test the get_decoded function without specifying image_name."""
    result = await crud.get_encoded(user=insert_user)

    mock_get.assert_called_once_with(
        relation="encoded_images",
        user=insert_user,
        image_name=None,
    )
    assert result == "_get called"


@pytest.mark.asyncio
@pytest.mark.parametrize("image_name", ("test_name", "..."))
async def test_get_encoded_with_name(
    mock_get: AsyncMock,
    insert_user: User,
    image_name: str,
) -> None:
    """Test the get_decoded function with image_name."""
    result = await crud.get_encoded(user=insert_user, image_name=image_name)

    mock_get.assert_called_once_with(
        relation="encoded_images",
        user=insert_user,
        image_name=image_name,
    )
    assert result == "_get called"
