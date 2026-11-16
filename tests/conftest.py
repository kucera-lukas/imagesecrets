"""Session wide fixtures."""

from __future__ import annotations

import asyncio
from pathlib import Path
from typing import TYPE_CHECKING, Generator, Optional

import numpy as np
import pytest
from fastapi.testclient import TestClient
from PIL import Image

if TYPE_CHECKING:
    from _pytest.monkeypatch import MonkeyPatch
    from fastapi_mail import FastMail
    from numpy.typing import ArrayLike
    from py.path import local
    from pytest_mock import MockFixture

    from imagesecrets.config import Settings
    from imagesecrets.database.image.services import ImageService
    from imagesecrets.database.token.services import TokenService
    from imagesecrets.database.user.services import UserService


@pytest.fixture(autouse=True)
def api_settings(
    request,
    tmpdir: local,
    monkeypatch: MonkeyPatch,
) -> Optional[Settings]:
    """Return settings for testing environment."""
    if "disable_autouse" in set(request.keywords):
        return

    monkeypatch.setenv(
        "DATABASE_URL",
        "postgres://username:password@test_database:5432/imagesecrets",
    )
    monkeypatch.setenv("SECRET_KEY", "test_secret_key" * 10)
    monkeypatch.setenv("ICON_URL", "https://www.test_icon_url.com")
    monkeypatch.setenv("SWAGGER_URL", "https://www.test_swagger_url.com")
    monkeypatch.setenv("REDOC_URL", "https://www.test_redoc_url.com")
    monkeypatch.setenv("REPOSITORY_URL", "https://www.test_repository_url.com")

    monkeypatch.setenv("MAIL_USERNAME", "test_username")
    monkeypatch.setenv("MAIL_PASSWORD", "test_password")
    monkeypatch.setenv("MAIL_PORT", "0")
    monkeypatch.setenv("MAIL_SERVER", "test_server")
    monkeypatch.setenv("MAIL_FROM", "test_mail_from@email.com")

    from imagesecrets.config import settings

    return settings


@pytest.fixture(scope="session")
def app_name(api_settings) -> str:
    """Return the default app name, specified in the Settings BaseModel."""
    return api_settings.app_name


@pytest.fixture(scope="function", autouse=True)
def patch_tasks(request, monkeypatch, api_settings: Settings) -> None:
    """Patch tasks with dummy functions."""
    if "disable_autouse" in set(request.keywords):
        return

    from imagesecrets.api import tasks

    async def clear_tokens():
        """Test function to clear tokens."""

    monkeypatch.setattr(tasks, "clear_tokens", lambda: clear_tokens())


@pytest.fixture(scope="function", autouse=True)
def email_client(
    request,
    monkeypatch: MonkeyPatch,
    api_settings: Settings,
) -> FastMail | None:
    """Return test email client."""
    if "disable_autouse" in set(request.keywords):
        return

    from imagesecrets.api import dependencies

    fm = dependencies.get_mail()

    fm.config.SUPPRESS_SEND = 1
    fm.config.USE_CREDENTIALS = False

    monkeypatch.setattr(dependencies, "get_mail", lambda: fm)

    return dependencies.get_mail()


@pytest.fixture()
def async_context_manager():
    """Return asynchronous context manager."""

    # not using func wrapped in `contextlib.asynccontextmanager`
    # so we can dynamically specify what should be returned by
    # __aenter__ (eg. some `Mock` objects).
    class AsyncContextManager:
        def __init__(self, obj):
            self.obj = obj

        async def __aenter__(self):
            return self.obj

        async def __aexit__(self, exc_type, exc_val, exc_tb): ...

    return AsyncContextManager(obj=None)


@pytest.fixture()
def async_iterator():
    class AsyncIterator:
        def __init__(self, objs):
            self.objs = objs

        async def __aiter__(self):
            for obj in self.objs:
                yield obj

    return AsyncIterator(objs=range(5))


@pytest.fixture()
def database_session(mocker: MockFixture, async_context_manager):
    session = mocker.Mock()

    session.execute = mocker.AsyncMock()
    session.stream = mocker.AsyncMock()

    session.begin_nested = mocker.Mock(return_value=async_context_manager)
    session.add = mocker.Mock()

    return session


@pytest.fixture()
def user_service(database_session) -> UserService:
    from imagesecrets.database.user.services import UserService

    return UserService(session=database_session)


@pytest.fixture()
def image_service(database_session) -> ImageService:
    from imagesecrets.database.image.services import ImageService

    return ImageService(session=database_session)


@pytest.fixture()
def token_service(database_session) -> TokenService:
    from imagesecrets.database.token.services import TokenService

    return TokenService(session=database_session)


@pytest.fixture()
def api_client(
    monkeypatch,
    mocker: MockFixture,
    api_settings: Settings,
    user_service,
    token_service,
    image_service,
) -> Generator[TestClient, None, None]:
    """Return api test client connected to fake database."""
    from imagesecrets.database.image.services import ImageService
    from imagesecrets.database.token.services import TokenService
    from imagesecrets.database.user.services import UserService
    from imagesecrets.interface import app

    for index, func in enumerate(app.router.on_startup.copy()):
        if func.__module__ == "imagesecrets.database.base":
            app.router.on_startup.pop(index)

    for service, fixture in zip(
        (UserService, ImageService, TokenService),
        (user_service, image_service, token_service),
    ):

        async def func(obj=fixture):
            yield obj

        monkeypatch.setattr(
            service,
            "from_session",
            func,
        )

        methods = [
            method
            for method in dir(service)
            if not method.startswith("__") and method != "from_session"
        ]

        for method in methods:
            func = getattr(service, method)

            if asyncio.iscoroutinefunction(func=func):
                mock = mocker.AsyncMock()
            else:
                mock = mocker.Mock()

            monkeypatch.setattr(service, method, mock)

    # testclient __enter__ and __exit__ deals with event loop
    with TestClient(app=app) as client:
        yield client


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
) -> ArrayLike:
    """Return numpy array of the test image."""
    with Image.open(test_image_path).convert("RGB") as img:
        array = np.array(img, dtype=np.uint8)
    return array


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
