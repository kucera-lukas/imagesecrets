"""Package with everything connected to database."""
from tortoise import Tortoise

from image_secrets.backend.database.image import models as image_models
from image_secrets.backend.database.token import models as token_models
from image_secrets.backend.database.user import models as user_models
from image_secrets.backend.database.user import schemas  # noqa

# models are initialized early so we can create correct pydantic user schemas
Tortoise.init_models(
    models_paths=(image_models, user_models, token_models),
    app_label="models",
)
