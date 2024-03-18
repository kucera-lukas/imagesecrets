"""Main user router."""

from __future__ import annotations

import asyncio
import contextlib
import random
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
from sqlalchemy.exc import IntegrityError, NoReferenceError, NoResultFound

from imagesecrets import schemas
from imagesecrets.api import dependencies, responses
from imagesecrets.api.exceptions import DetailExists, NotAuthenticated
from imagesecrets.core import email
from imagesecrets.core.util import main
from imagesecrets.database.token.services import TokenService
from imagesecrets.database.user.services import DBIdentifier, UserService

if TYPE_CHECKING:
    from imagesecrets.database.user.models import User

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
    async with contextlib.asynccontextmanager(
        UserService.from_session,
    )() as user_service:
        try:
            result = await user_service.get(
                DBIdentifier(column="id", value=user_id),
            )
        except NoResultFound as e:
            raise NotAuthenticated(
                status_code=status.HTTP_401_UNAUTHORIZED,
            ) from e

    return result


@router.post(
    "/login",
    status_code=status.HTTP_200_OK,
    response_model=schemas.Token,
    summary="Login for access token",
    responses=responses.AUTHORIZATION,  # type: ignore
)
async def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    user_service: UserService = Depends(UserService.from_session),
) -> dict[str, str]:
    """Login into an account and obtain access token.

    - **username**: Account username
    - **password**: Account password

    \f
    :param form_data: The OAauth2 form data

    :raises HTTPException: if the user authentication failed

    """
    auth = await user_service.authenticate(
        form_data.username,
        form_data.password,
    )
    if not auth:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="incorrect username or password",
        )

    identifier = DBIdentifier(column="username", value=form_data.username)
    user_id = await user_service.get_id(identifier)
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
    user_service: UserService = Depends(UserService.from_session),
) -> User:
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
        db_user = await user_service.create(user)
    except IntegrityError as e:
        parsed = main.parse_asyncpg_integrity(error=e.orig)
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

    return db_user


@router.post(
    "/forgot-password",
    status_code=status.HTTP_202_ACCEPTED,
    response_model=schemas.Message,
    summary="Request a password reset token",
)
async def forgot_password(
    background_tasks: BackgroundTasks,
    email_client: FastMail = Depends(dependencies.get_mail),
    user_service: UserService = Depends(UserService.from_session),
    token_service: TokenService = Depends(TokenService.from_session),
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
        user_id = await user_service.get_id(
            DBIdentifier(column="email", value=user_email),
        )
    except NoResultFound:
        # mimic waiting time of token creation
        await asyncio.sleep(random.random())
    else:
        token, token_hash = token_service.create_token()
        background_tasks.add_task(
            token_service.create,
            user_id=user_id,
            token_hash=token_hash,
        )
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
    response_model=schemas.Message,
    summary="Reset account password",
    responses=responses.AUTHORIZATION,  # type: ignore
)
async def reset_password(
    background_tasks: BackgroundTasks,
    user_service: UserService = Depends(UserService.from_session),
    token_service: TokenService = Depends(TokenService.from_session),
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
        user_id = await token_service.get_user_id(token)
    except NoReferenceError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="invalid forgot password token",
        ) from e
    # password hashing is handled by the update function
    background_tasks.add_task(
        user_service.update,
        user_id,
        password_hash=password,
    )
    return {"detail": "account password updated"}
