"""Module with settings."""
from pathlib import Path

_parent = Path(__file__).parent
ENV = _parent.parent / ".env"
ICON = _parent / "static/favicon.ico"

MESSAGE_DELIMITER = "<{~stop-here~}>"

API_IMAGES = _parent / "static/images"
API_IMAGES.mkdir(parents=True, exist_ok=True)
