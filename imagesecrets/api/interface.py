"""Application Programming Interface."""

from __future__ import annotations

from fastapi import APIRouter, Depends, FastAPI, status

import imagesecrets
from imagesecrets import schemas
from imagesecrets.api import dependencies, handlers, openapi, responses, tasks
from imagesecrets.api.routers import decode, encode, user
from imagesecrets.config import Settings
from imagesecrets.database import base


def create_router() -> APIRouter:
    router = APIRouter(prefix="/api")

    router.include_router(decode.router)
    router.include_router(encode.router)
    router.include_router(user.main)
    router.include_router(user.me)

    return router


def create_api(config: Settings) -> FastAPI:
    api = FastAPI(
        dependencies=[Depends(dependencies.get_config)],
        title="ImageSecrets",
        description="Encode and decode messages from images!",
        version=imagesecrets.__version__,
        # will be set manually
        docs_url=None,
        redoc_url=None,
        responses=responses.VALIDATION,  # type: ignore
    )

    base.init(api)

    api.include_router(create_router())

    handlers.init(api)
    tasks.init(api)

    @api.get(
        "/",
        response_model=schemas.base.Info,
        status_code=status.HTTP_200_OK,
        summary="Basic information about the API.",
        tags=["home"],
    )
    async def home() -> dict[str, str]:
        """Return basic info about the API."""
        return {
            "AppName": config.app_name,
            "SwaggerUI": config.swagger_url,
            "ReDoc": config.redoc_url,
            "GitHub": config.repository_url,
        }

    api.openapi = openapi.custom(api, swagger=True, redoc=True)  # type: ignore

    return api
