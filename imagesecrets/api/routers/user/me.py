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
from sqlalchemy.exc import IntegrityError

from imagesecrets import schemas
from imagesecrets.api import dependencies, exceptions, responses
from imagesecrets.api.routers.user.main import manager
from imagesecrets.core.util import main
from imagesecrets.database.user.models import User
from imagesecrets.database.user.services import UserService

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
    current_user: User = Depends(manager),
) -> User:
    """Show all information connected to a User.

    \f
    :param current_user: Current user dependency

    """
    return current_user


@router.patch(
    "/me",
    response_model=schemas.User,
    status_code=status.HTTP_200_OK,
    summary="Update user credentials",
    responses=responses.CONFLICT,  # type: ignore
)
async def patch(
    user_service: UserService = Depends(UserService.from_session),
    current_user: User = Depends(manager),
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
) -> User:
    """Update account details

    - **username**: New account username
    - **email**: New account email

    \f
    :param current_user: Current user dependency
    :param username: New username for the currently authenticated user
    :param email: New email for the currently authenticated user

    :raises DetailExists: if either of the new values are already claimed in the database

    """
    update_dict = main.ExcludeUnsetDict(
        username=username if current_user.username != username else None,
        email=email if current_user.email != email else None,
    ).exclude_unset()

    if not update_dict:
        # no values to update so we can return right away
        return current_user

    try:
        user = await user_service.update(current_user.id, **update_dict)
    except IntegrityError as e:
        parsed = main.parse_asyncpg_integrity(error=e.orig)
        raise exceptions.DetailExists(
            status_code=status.HTTP_409_CONFLICT,
            message="account detail already exists",
            field=parsed.field,
            value=parsed.value,
        ) from e

    return user


@router.delete(
    "/me",
    status_code=status.HTTP_202_ACCEPTED,
    response_model=schemas.Message,
    summary="Delete an Account",
)
async def delete(
    background_tasks: BackgroundTasks,
    user_service: UserService = Depends(UserService.from_session),
    current_user: User = Depends(manager),
) -> Optional[dict[str, str]]:
    """Delete a user and all extra information connected to it.

    \f
    :param background_tasks: Starlette ``BackgroundTasks`` instance
    :param current_user: Current user dependency

    """
    background_tasks.add_task(user_service.delete, current_user.id)
    return {"detail": "account deleted"}


@router.put(
    "/me/password",
    status_code=status.HTTP_202_ACCEPTED,
    response_model=schemas.Message,
    summary="Change user password",
)
async def password_put(
    background_tasks: BackgroundTasks,
    user_service: UserService = Depends(UserService.from_session),
    current_user: User = Depends(manager),
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
    auth = await user_service.authenticate(
        username=current_user.username,
        password_=old,
    )
    if not auth:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="incorrect password",
        )
    # password hashing is handled by the update function
    background_tasks.add_task(
        user_service.update,
        current_user.id,
        password_hash=new,
    )
    return {"detail": "account password updated"}
