"""Test OpenAPI API documentation."""
from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from fastapi.testclient import TestClient
    from pytest_mock import MockFixture

    from image_secrets.api.config import Settings


def test_swagger(
    api_client: TestClient,
    mocker: MockFixture,
    api_settings: Settings,
) -> None:
    """Test the get request on the home route."""
    swagger = mocker.patch(
        "fastapi.openapi.docs.get_swagger_ui_html",
        return_value="test_swagger",
    )

    response = api_client.get("/docs")

    swagger.assert_called_once_with(
        openapi_url="/openapi.json",
        title=api_settings.app_name,
        swagger_favicon_url=api_settings.icon_url,
    )
    response.raise_for_status()
    assert response.status_code == 200
    assert response.json() == "test_swagger"


def test_redoc(
    api_client: TestClient,
    mocker: MockFixture,
    api_settings: Settings,
) -> None:
    """Test the get request on the home route."""
    redoc = mocker.patch(
        "fastapi.openapi.docs.get_redoc_html",
        return_value="test_redoc",
    )

    response = api_client.get("/redoc")

    redoc.assert_called_once_with(
        openapi_url="/openapi.json",
        title=api_settings.app_name,
        redoc_favicon_url=api_settings.icon_url,
    )
    response.raise_for_status()
    assert response.status_code == 200
    assert response.json() == "test_redoc"


def test_openapi_schema(api_settings: Settings) -> None:
    """Test the generated OpenAPI schema."""
    import image_secrets
    from image_secrets.api.interface import app

    schema = app.openapi()
    info = schema["info"]

    assert info["title"] == api_settings.app_name
    assert info["version"] == image_secrets.__version__
    assert info["x-logo"] == {"url": api_settings.icon_url}


def test_openapi_schema_cached(
    mocker: MockFixture,
    api_settings: Settings,
) -> None:
    """Test the that OpenAPI schema is generated only once and then cached."""
    from image_secrets.api.interface import app

    get_openapi = mocker.patch("fastapi.openapi.utils.get_openapi")
    app.openapi_schema = None

    app.openapi()
    get_openapi.assert_called_once()

    get_openapi.reset_mock()

    app.openapi()
    get_openapi.assert_not_called()
