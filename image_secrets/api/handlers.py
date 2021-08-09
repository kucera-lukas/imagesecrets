"""Exception handlers for api."""
from __future__ import annotations

from typing import TYPE_CHECKING

from fastapi import Request, status
from fastapi.encoders import jsonable_encoder
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from image_secrets.api.exceptions import DetailExists, NotAuthenticated

if TYPE_CHECKING:
    from typing import Any, Optional

    from fastapi import FastAPI


def init(app: FastAPI) -> None:
    """Connect exception handlers to app.

    :param app: The current app instance

    """
    # same as decorator syntax
    app.exception_handler(RequestValidationError)(validation_error)
    app.exception_handler(DetailExists)(detail_exists)
    app.exception_handler(NotAuthenticated)(not_authenticated)


async def handler(
    status_code: int,
    message: str,
    field: str,
    value: str | None = None,
    headers: Optional[dict[Any, Any]] = None,
) -> JSONResponse:
    """Create a json response.

    :param status_code: Status code of the response
    :param message: Response detail
    :param field: Field which caused this response
    :param value: The field value
    :param headers: Optional headers to include in the response

    """
    content = {"detail": message, "field": field}
    if value:
        content |= {"value": value}
    return JSONResponse(
        status_code=status_code,
        content=jsonable_encoder(content),
        headers=headers,  # type: ignore
    )


async def validation_error(
    req: Request,
    exc: RequestValidationError,
) -> JSONResponse:
    """Parse the validation error and return response with well readable details.

    :param req: The original starlette request
    :param exc: The exception that was raised

    """
    errors = exc.errors()[0]
    msg = errors["msg"]
    field = errors["loc"][-1]
    return await handler(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        message=msg,
        field=field,
    )


async def detail_exists(req: Request, exc: DetailExists) -> JSONResponse:
    """Return field already exists response via response handler.

    :param req: The original starlette request
    :param exc: The exception that was raised

    """
    return await handler(
        status_code=exc.status_code,
        message=exc.message,
        field=exc.field,
        value=exc.value,
    )


async def not_authenticated(
    req: Request,
    exc: NotAuthenticated,
) -> JSONResponse:
    """Return invalid access token response.

    :param req: The original starlette request
    :param exc: The exception that was raised

    """
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": "invalid access token"},
        headers={"WWW-Authenticate": "Bearer"},
    )
