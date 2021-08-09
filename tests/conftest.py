"""Session wide fixtures."""
from __future__ import annotations

import asyncio
import os
from pathlib import Path
from typing import TYPE_CHECKING, Generator, Optional

import numpy as np
import pytest
from fastapi.testclient import TestClient
from PIL import Image
from tortoise.contrib.test import finalizer, initializer

from image_secrets.api import config as config_
from image_secrets.backend.database import (
    image_models,
    token_models,
    user_models,
)
from image_secrets.backend.util import main

if TYPE_CHECKING:
    from fastapi_mail import FastMail
    from numpy.typing import ArrayLike
    from py.path import local
    from pytest_mock import MockFixture

    from image_secrets.api.config import Settings
    from image_secrets.backend.database.image.models import (
        DecodedImage,
        EncodedImage,
    )
    from image_secrets.backend.database.user.models import User
    from image_secrets.backend.util.main import ParsedIntegrity


@pytest.fixture(scope="session")
def app_name() -> str:
    """Return the default app name, specified in the Settings BaseModel."""
    return config_.Settings.__dict__["__fields__"]["app_name"].default


@pytest.fixture(scope="function", autouse=True)
def api_settings(request, tmpdir: local, monkeypatch) -> Optional[Settings]:
    """Return settings for testing environment."""
    if "disable_autouse" in set(request.keywords):
        return

    db_url = "sqlite://:memory:"
    # need to construct so there is no field validation
    test_settings = config_.Settings.construct(
        image_folder=str(Path(tmpdir.mkdir("images/")).absolute()),
        pg_dsn=db_url,
        secret_key="test_secret_key" * 10,
        icon_url="https://www.test_icon_url.com",
        swagger_url="https://www.test_swagger_url.com",
        redoc_url="https://www.test_redoc_url.com",
        repository_url="https://www.test_repository_url.com",
    )
    os.environ["MAIL_USERNAME"] = "test_username"
    os.environ["MAIL_PASSWORD"] = "test_password"
    os.environ["MAIL_PORT"] = "0"
    os.environ["MAIL_SERVER"] = "test_server"
    os.environ["MAIL_FROM"] = "test@email.test"
    config_.settings = test_settings

    # need to monkey patch specific functions connected to PostgreSQL
    def sqlite_parsing(error: str) -> ParsedIntegrity:
        """Return parsed sqlite error message."""
        split = str(error).split(":")
        try:
            result = main.ParsedIntegrity(field=split[0], value=split[1])
        except IndexError as e:
            raise ValueError(f"invalid error message: {error!r}") from e
        return result

    monkeypatch.setattr(main, "parse_unique_integrity", sqlite_parsing)

    return config_.settings


@pytest.fixture(scope="function", autouse=True)
def patch_tasks(request, monkeypatch, api_settings: Settings) -> None:
    """Patch tasks with dummy functions."""
    if "disable_autouse" in set(request.keywords):
        return

    from image_secrets.api import tasks

    async def clear_tokens():
        """Test function to clear tokens."""

    monkeypatch.setattr(tasks, "clear_tokens", lambda: clear_tokens())


@pytest.fixture(scope="function", autouse=True)
def email_client(request, api_settings: Settings) -> FastMail | None:
    """Return test email client."""
    if "disable_autouse" in set(request.keywords):
        return

    from image_secrets.api import dependencies

    fm = dependencies.get_mail()
    fm.config.SUPPRESS_SEND = 1
    fm.config.USE_CREDENTIALS = False
    dependencies.get_mail = lambda: fm

    return dependencies.get_mail()


@pytest.fixture(scope="function")
def api_client(
    request,
    api_settings: Settings,
) -> Generator[TestClient, None, None]:
    """Return api test client connected to fake database."""
    # settings already patched by fixture
    from image_secrets.api.interface import app

    initializer(
        [user_models, image_models, token_models],
        db_url=api_settings.pg_dsn,
        app_label="models",
    )

    # testclient __enter__ and __exit__ deals with event loop
    with TestClient(app=app) as client:
        yield client

    request.addfinalizer(finalizer)


@pytest.fixture(scope="function")
def insert_user(api_client: TestClient) -> User:
    """Return user inserted into a clean database."""
    from image_secrets.backend.database.user.models import User

    user = User(
        username="username",
        email="user@example.com",
        password_hash="password",
    )

    loop = asyncio.get_event_loop()
    loop.run_until_complete(user.save())

    return user


@pytest.fixture(scope="function")
def auth_token(
    api_client: TestClient,
    insert_user: User,
    mocker: MockFixture,
) -> tuple[dict[str, str], User]:
    """Return authorized user and a token."""
    mocker.patch("image_secrets.backend.password.auth", return_value=True)
    response = api_client.post(
        "/users/login",
        data={
            "username": insert_user.username,
            "password": insert_user.password_hash,
        },
    ).json()

    token_header = {
        "authorization": f'{response["token_type"].capitalize()} {response["access_token"]}',
    }
    return token_header, insert_user


@pytest.fixture(scope="function")
def insert_decoded(api_client: TestClient, insert_user: User) -> DecodedImage:
    """Return decoded_image inserted into a clean database."""
    from image_secrets.backend.database.image.models import DecodedImage

    img = DecodedImage(
        filename="test_filename",
        image_name="test_image_name",
        message="test_message",
        delimiter="test_delimiter",
        lsb_amount=2,
        owner_id=insert_user.id,
    )
    loop = asyncio.get_event_loop()
    loop.run_until_complete(img.save())

    return img


@pytest.fixture(scope="function")
def insert_encoded(api_client: TestClient, insert_user: User) -> EncodedImage:
    """Return encoded_image inserted into a clean database."""
    from image_secrets.backend.database.image.models import EncodedImage

    img = EncodedImage(
        filename="test_filename",
        image_name="test_image_name",
        message="test_message",
        delimiter="test_delimiter",
        lsb_amount=2,
        owner_id=insert_user.id,
    )
    loop = asyncio.get_event_loop()
    loop.run_until_complete(img.save())

    return img


@pytest.fixture(scope="session")
def test_image_path() -> Path:
    """Return the path to the test.png image."""
    fp: Path = Path(__file__).parent / "test.png"
    assert fp.is_file()
    return fp


@pytest.fixture(scope="session")
def api_image_file(
    test_image_path: Path,
) -> dict[str, tuple[str, bytes, str]]:
    """Return the dict with file needed to use post requests."""
    return {
        "file": (
            test_image_path.name,
            test_image_path.open("rb").read(),
            "image/png",
        ),
    }


@pytest.fixture(scope="session")
def test_image_array(
    test_image_path: Path,
) -> Generator[ArrayLike, None, None]:
    """Return numpy array of the test image."""
    with Image.open(test_image_path).convert("RGB") as img:
        yield np.asarray(img, dtype=np.uint8)


@pytest.fixture(scope="session")
def delimiter_array() -> ArrayLike:
    """Return a delimiter array, string form = 'dlm'."""
    return np.array(
        (
            [0],
            [1],
            [1],
            [0],
            [0],
            [1],
            [0],
            [0],
            [0],
            [1],
            [1],
            [0],
            [1],
            [1],
            [0],
            [0],
            [0],
            [1],
            [1],
            [0],
            [1],
            [1],
            [0],
            [1],
        ),
    )
