"""App Configuration."""
from pathlib import Path

URL_KEY_ALIAS = {
    "swagger_url": "SwaggerUI",
    "redoc_url": "ReDoc",
    "github_url": "GitHub",
}

_parent = Path(__file__).parent
ENV = _parent.parent / ".env"
ICON = _parent / "static/favicon.ico"
TEMPLATES = _parent / "templates"

MESSAGE_DELIMITER = "<{~stop-here~}>"

API_IMAGES = _parent / "static/images"
API_IMAGES.mkdir(parents=True, exist_ok=True)
