"""Router for current user.

Note: manager dependency is in every route because access to the current user information is needed.
    relevant github discussion: https://github.com/tiangolo/fastapi/issues/424#issuecomment-584169213

"""
from __future__ import annotations

from typing import Optional

from fastapi import (
    APIRouter,
    BackgroundTasks,
    Depends,
    Form,
    HTTPException,
    status,
)
from pydantic import EmailStr
from tortoise.exceptions import IntegrityError

from image_secrets.api import dependencies, exceptions, responses
from image_secrets.api import schemas as api_schemas
from image_secrets.api.routers.user.main import manager
from image_secrets.backend.database.user import crud, models, schemas
from image_secrets.backend.util.main import (
    ExcludeUnsetDict,
    parse_unique_integrity,
)

router = APIRouter(
    prefix="/users",
    tags=["me"],
    dependencies=[Depends(dependencies.get_config), Depends(manager)],
    responses=responses.AUTHORIZATION,  # type: ignore
)


@router.get(
    "/me",
    response_model=schemas.User,
    status_code=status.HTTP_200_OK,
    summary="Account information",
)
async def get(
    current_user: models.User = Depends(manager),
) -> Optional[schemas.User]:
    """Show all information connected to a User.

    \f
    :param current_user: Current user dependency

    """
    schema: schemas.User = await schemas.User.from_tortoise_orm(current_user)
    return schema


@router.patch(
    "/me",
    response_model=schemas.User,
    status_code=status.HTTP_200_OK,
    summary="Update user credentials",
    responses=responses.CONFLICT,  # type: ignore
)
async def patch(
    current_user: models.User = Depends(manager),
    username: Optional[str] = Form(
        None,
        description="Your new account username",
        min_length=6,
        max_length=128,
        example="MyUsername",
    ),
    email: Optional[EmailStr] = Form(
        None,
        description="Your new account email",
        example="string@example.com",
    ),
) -> Optional[schemas.User]:
    """Update account details

    - **username**: New account username
    - **email**: New account email

    \f
    :param current_user: Current user dependency
    :param username: New username for the currently authenticated user
    :param email: New email for the currently authenticated user

    :raises DetailExists: if either of the new values are already claimed in the database

    """
    update_dict = ExcludeUnsetDict(
        username=username,
        email=email,
    ).exclude_unset()
    if not update_dict:
        # no values to update so we can return right away
        schema: schemas.User = await schemas.User.from_tortoise_orm(
            current_user,
        )
        return schema

    try:
        user = await crud.update(current_user.id, **update_dict)
    except IntegrityError as e:
        parsed = parse_unique_integrity(error=e)
        raise exceptions.DetailExists(
            status_code=status.HTTP_409_CONFLICT,
            message="account detail already exists",
            field=parsed.field,
            value=parsed.value,
        ) from e
    schema: schemas.User = await schemas.User.from_tortoise_orm(user)  # type: ignore
    return schema


@router.delete(
    "/me",
    status_code=status.HTTP_202_ACCEPTED,
    response_model=api_schemas.Message,
    summary="Delete an Account",
)
async def delete(
    background_tasks: BackgroundTasks,
    current_user: models.User = Depends(manager),
) -> Optional[dict[str, str]]:
    """Delete a user and all extra information connected to it.

    \f
    :param background_tasks: Starlette ``BackgroundTasks`` instance
    :param current_user: Current user dependency

    """
    background_tasks.add_task(crud.delete, current_user.id)
    return {"detail": "account deleted"}


@router.put(
    "/me/password",
    status_code=status.HTTP_202_ACCEPTED,
    response_model=api_schemas.Message,
    summary="Change user password",
)
async def password_put(
    background_tasks: BackgroundTasks,
    current_user: models.User = Depends(manager),
    old: str = Form(
        ...,
        description="Your current account password",
        min_length=6,
        example="MyPassword",
    ),
    new: str = Form(
        ...,
        description="New account password",
        min_length=6,
        example="MyNewPassword",
    ),
) -> Optional[dict[str, str]]:
    """Change account password.

    - **old**: Current account password
    - **new**: New account password

    \f
    :param background_tasks: Starlette ``BackgroundTasks`` instance
    :param current_user: Current user dependency
    :param old: Current password of the currently authenticated user
    :param new: New password of the currently authenticated

    """
    auth = await crud.authenticate(
        username=current_user.username,
        password_=old,
    )
    if not auth:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="incorrect password",
        )
    # password hashing is handled by the update function
    background_tasks.add_task(crud.update, current_user.id, password_hash=new)
    return {"detail": "account password updated"}
