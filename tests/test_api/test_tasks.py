"""Test API tasks module."""

from __future__ import annotations

import asyncio
from typing import TYPE_CHECKING

import pytest

if TYPE_CHECKING:
    from unittest.mock import AsyncMock

    from pytest_mock import MockFixture


@pytest.fixture()
def mock_sleep(mocker: MockFixture):
    """Return mocked ``asyncio.sleep``."""
    async_mock = mocker.AsyncMock(return_value=None)
    return mocker.patch(
        "asyncio.sleep",
        side_effect=async_mock,
    )


def test_repeat(mock_sleep: AsyncMock) -> None:
    """Test a successful repeat function call."""
    from imagesecrets.api import tasks

    @tasks.repeat(seconds=1)
    async def test_coro() -> None:
        """Testing coroutine."""
        raise RuntimeError

    asyncio.run(test_coro())

    mock_sleep.assert_called_once_with(1)


@pytest.mark.asyncio
@pytest.mark.disable_autouse
async def test_clear_tokens(mocker: MockFixture):
    from imagesecrets.api import tasks

    clear = mocker.patch(
        "imagesecrets.database.token.services.TokenService.clear",
    )

    await tasks.clear_tokens()

    clear.assert_called_once_with()


@pytest.mark.asyncio
@pytest.mark.disable_autouse
async def test_runner():
    from imagesecrets.api import tasks
    from imagesecrets.interface import app

    tasks.init(app=app)

    for func in app.router.on_startup:
        # need to find correct function
        # for now we just need to find the only task from `api.tasks`
        if func.__module__ != "imagesecrets.api.tasks":
            continue

        await func()
