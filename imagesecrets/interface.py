"""Application Programming Interface."""

from __future__ import annotations

from fastapi import FastAPI

from imagesecrets.api.interface import create_api
from imagesecrets.config import settings


def create_application() -> FastAPI:
    """Create the application."""
    return create_api(config=settings)


app = create_application()


__all__ = ["app", "create_application", "create_api"]
