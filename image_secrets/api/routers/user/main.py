"""Main user router."""
from __future__ import annotations

import asyncio
from typing import TYPE_CHECKING, Optional

from fastapi import (
    APIRouter,
    BackgroundTasks,
    Depends,
    Form,
    HTTPException,
    Query,
    status,
)
from fastapi.security import OAuth2PasswordRequestForm
from fastapi_login import LoginManager
from fastapi_mail import FastMail
from pydantic import EmailStr
from tortoise.exceptions import DoesNotExist, IntegrityError

from image_secrets.api import dependencies, responses
from image_secrets.api import schemas as api_schemas
from image_secrets.api.exceptions import DetailExists, NotAuthenticated
from image_secrets.backend import email
from image_secrets.backend.database.token import crud as token_crud
from image_secrets.backend.database.user import crud, schemas
from image_secrets.backend.util.main import parse_unique_integrity

if TYPE_CHECKING:
    from image_secrets.backend.database.user.models import User

config = dependencies.get_config()
router = APIRouter(
    prefix="/users",
    tags=["users"],
    dependencies=[Depends(dependencies.get_config)],
)
manager = LoginManager(
    secret=config.secret_key,
    token_url=f"{router.prefix}/login",
)
manager.not_authenticated_exception = NotAuthenticated


@manager.user_loader
async def user_loader(user_id: int) -> Optional[User]:
    """Load a user based on current jwt token.

    :param user_id: User database id in the sub field of the jwt token

    :raises NotAuthenticated: if no user with the given username was found
        (username changed, account was deleted)

    """
    try:
        return await crud.get(crud.DBIdentifier(column="id", value=user_id))
    except DoesNotExist as e:  # pragma: no cover
        raise NotAuthenticated(status_code=status.HTTP_404_NOT_FOUND) from e


@router.post(
    "/login",
    status_code=status.HTTP_200_OK,
    response_model=api_schemas.Token,
    summary="Login for access token",
    responses=responses.AUTHORIZATION,  # type: ignore
)
async def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
) -> dict[str, str]:
    """Login into an account and obtain access token.

    - **username**: Account username
    - **password**: Account password

    \f
    :param form_data: The OAauth2 form data

    :raises HTTPException: if the user authentication failed

    """
    auth = await crud.authenticate(form_data.username, form_data.password)
    if not auth:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="incorrect username or password",
        )

    identifier = crud.DBIdentifier(column="username", value=form_data.username)
    user_id = await crud.get_id(identifier)
    access_token = manager.create_access_token(data={"sub": user_id})
    return {"access_token": access_token, "token_type": "bearer"}


@router.post(
    "/register",
    status_code=status.HTTP_201_CREATED,
    response_model=schemas.User,
    summary="New user registration",
    responses=responses.CONFLICT,  # type: ignore
)
async def register(
    user: schemas.UserCreate,
    background_tasks: BackgroundTasks,
    email_client: FastMail = Depends(dependencies.get_mail),
) -> Optional[schemas.User]:
    """Register a new user.

    - **username**: New account username
    - **email**: New account email
    - **password**: New account password

    \f
    :param user: Schema with necessary information to create a new user
    :param background_tasks: Starlette ``BackgroundTasks`` instance
    :param email_client: Email SMTP client instance

    :raises DetailExists: if either username or email are already claimed in database

    """
    try:
        db_user = await crud.create(user)
    except IntegrityError as e:
        parsed = parse_unique_integrity(error=e)
        raise DetailExists(
            status_code=status.HTTP_409_CONFLICT,
            message="account detail already exists",
            field=parsed.field,
            value=parsed.value,
        ) from e
    background_tasks.add_task(
        email.send_welcome,
        client=email_client,
        recipient=user.email,
        username=user.username,
    )
    schema: schemas.User = await schemas.User.from_tortoise_orm(db_user)
    return schema


@router.post(
    "/forgot-password",
    status_code=status.HTTP_202_ACCEPTED,
    response_model=api_schemas.Message,
    summary="Request a password reset token",
)
async def forgot_password(
    background_tasks: BackgroundTasks,
    email_client: FastMail = Depends(dependencies.get_mail),
    user_email: EmailStr = Form(
        ...,
        alias="email",
        description="Your account email",
        example="string@example.com",
    ),
) -> dict[str, str]:
    """Send a reset password email with a password reset token.

    - **email**: Account email of the user which needs to have their password reset

    \f
    :param user_email: Email of the account which will have password changed
    :param background_tasks: Starlette ``BackgroundTasks`` instance
    :param email_client: Email SMTP client instance

    """
    try:
        user_id = await crud.get_id(
            crud.DBIdentifier(column="email", value=user_email),
        )
    except DoesNotExist:
        # mimic waiting time of token creation
        await asyncio.sleep(1)
    else:
        token = await token_crud.create_new(owner_id=user_id)
        background_tasks.add_task(
            email.send_reset,
            client=email_client,
            recipient=user_email,
            token=token,
        )
    return {"detail": "email with password reset token has been sent"}


@router.post(
    "/reset-password",
    status_code=status.HTTP_202_ACCEPTED,
    response_model=api_schemas.Message,
    summary="Reset account password",
    responses=responses.AUTHORIZATION,  # type: ignore
)
async def reset_password(
    background_tasks: BackgroundTasks,
    token: str = Query(
        ...,
        description="Forgot password authorization token",
        example="YcEK0RFG0kITiKJ5PsSmPLFLgOkipiBCJqvK9jD7dwk",
    ),
    password: str = Form(
        ...,
        description="New password for your account",
        min_length=6,
        example="SuperSecret123",
    ),
) -> dict[str, str]:
    """Reset account password.

    - **token**: Forgot password token received via email
    - **password**: New password for your account

    \f
    :param background_tasks: Starlette ``BackgroundTasks`` instance
    :param token: Forgot password authorization token
    :param password: New password

    """
    try:
        user_id = await token_crud.get_owner_id(token)
    except DoesNotExist as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="invalid forgot password token",
        ) from e
    # password hashing is handled by the update function
    background_tasks.add_task(crud.update, user_id, password_hash=password)
    return {"detail": "account password updated"}
