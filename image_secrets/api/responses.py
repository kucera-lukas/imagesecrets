"""API endpoint response examples."""
from __future__ import annotations

from typing import Any

from image_secrets.api.schemas import Conflict, Field, Message

Response = dict[int, dict[str, Any]]

AUTHORIZATION: Response = {
    401: {"model": Message, "description": "Authorization Error"},
}
FORBIDDEN: Response = {
    403: {"model": Message, "description": "Authorization Error"},
}
NOT_FOUND: Response = {404: {"model": Message, "description": "Not Found"}}
CONFLICT: Response = {
    409: {"model": Conflict, "description": "Conflict Error"},
}
MEDIA: Response = {
    415: {"model": Message, "description": "Unsupported Media Type"},
}
VALIDATION: Response = {
    422: {"model": Field, "description": "Validation Error"},
}

MESSAGE_NOT_FOUND: Response = {
    200: {"model": Message, "description": "Nothing Decoded"},
}
IMAGE_TOO_SMALL: Response = {
    422: {"model": Message, "description": "Invalid Image File"},
}
