"""Tasks which should be periodically executed during runtime."""

from __future__ import annotations

import asyncio
import contextlib
import functools as fn
from typing import TYPE_CHECKING, Any, Callable, Coroutine

from imagesecrets.database.token.services import TokenService

if TYPE_CHECKING:
    from fastapi import FastAPI


def init(app: FastAPI) -> None:
    """Add startup event to run all tasks.

    :param app: The application which will have the startup event appended

    """

    @app.on_event("startup")
    async def runner() -> None:
        """Run all tasks."""
        await repeat(seconds=600)(clear_tokens)()


_F = Callable[[], Coroutine[Any, Any, None]]


def repeat(*, seconds: int) -> Callable[[_F], _F]:
    """Decorate a coroutine to be run in an infinite loop.

    :param seconds: How often to repeat coroutine call

    """

    def decorator(func: _F) -> _F:
        """Decorate a coroutine.

        :param func: The coroutine to decorate

        """

        @fn.wraps(func)
        async def wrapper() -> None:
            """Wrap the infinite loop execution."""

            async def loop() -> None:
                """Execute decorated function and sleep for the given amount of seconds."""
                while 1:
                    await asyncio.sleep(seconds)
                    await func()

            asyncio.ensure_future(loop())

        return wrapper

    return decorator


async def clear_tokens() -> None:
    """Clear all expired tokens in database."""
    async with contextlib.asynccontextmanager(
        TokenService.from_session,
    )() as token_service:
        await token_service.clear()
