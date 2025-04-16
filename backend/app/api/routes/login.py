from datetime import timedelta
from typing import Annotated, Any

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import HTMLResponse
from fastapi.security import OAuth2PasswordRequestForm

from app.api.dependencies.deps import CurrentUser, get_current_active_superuser,CommittedSessionDep
from app.core import security
from app.core.postgres.config import settings
from app.core.postgres.dao import UserDAO
from app.core.security import get_password_hash
from app.schemas.auth import Token, NewPassword
from app.schemas.common import Message
from app.schemas.types.user_types import UserStatus
from app.schemas.users import UserPublic

from app.utils import (
    generate_password_reset_token,
    generate_reset_password_email,
    send_email,
    verify_password_reset_token,
)



import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)


router = APIRouter(tags=["login"])


@router.post("/login/access-token")
def login_access_token(
        session: CommittedSessionDep,
        form_data: Annotated[OAuth2PasswordRequestForm, Depends()]
) -> Token:
    """
    OAuth2 compatible token login, get an access token for future requests
    """
    # Authenticate user through DAO
    logger.info(f"Step 1: login_access_token  email {form_data.username } pass {form_data.password }")
    user_dao = UserDAO(session)
    user = user_dao.authenticate(
        email=form_data.username,
        password=form_data.password
    )

    if not user:
        logger.warning(f"Failed login attempt: {form_data.username}")
        raise HTTPException(status_code=400, detail="Incorrect email or password")

    if user.status == UserStatus.INACTIVE:
        logger.info(f"Inactive user attempted login: {form_data.username}")
        raise HTTPException(status_code=400, detail="Inactive user")

    # Generate token
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    return Token(
        access_token=security.create_access_token(
            user.id,
            expires_delta=access_token_expires
        ),
        token_type="bearer"
    )

@router.post("/login/test-token", response_model=UserPublic)
def test_token(current_user: CurrentUser) -> Any:
    """
    Test access token
    """
    return current_user


@router.post("/password-recovery/{email}")
def recover_password(email: str, session: CommittedSessionDep) -> Message:
    """
    Password Recovery
    """
    user = UserDAO(session).find_one_or_none({"email": email})

    if not user:
        raise HTTPException(
            status_code=404,
            detail="The user with this email does not exist in the system.",
        )
    password_reset_token = generate_password_reset_token(email=email)
    email_data = generate_reset_password_email(
        email_to=user.email, email=email, token=password_reset_token
    )
    send_email(
        email_to=user.email,
        subject=email_data.subject,
        html_content=email_data.html_content,
    )
    return Message(message="Password recovery email sent")


@router.post("/reset-password/")
def reset_password(session: CommittedSessionDep, body: NewPassword) -> Message:
    """
    Reset password
    """
    email = verify_password_reset_token(token=body.token)
    if not email:
        raise HTTPException(status_code=400, detail="Invalid token")
    user = UserDAO(session).find_one_or_none({"email": email})
    if not user:
        raise HTTPException(
            status_code=404,
            detail="The user with this email does not exist in the system.",
        )
    elif not user.is_active:
        raise HTTPException(status_code=400, detail="Inactive user")
    hashed_password = get_password_hash(password=body.new_password)
    user.hashed_password = hashed_password
    session.add(user)
    session.commit()
    return Message(message="Password updated successfully")


@router.post(
    "/password-recovery-html-content/{email}",
    dependencies=[Depends(get_current_active_superuser)],
    response_class=HTMLResponse,
)
def recover_password_html_content(email: str, session: CommittedSessionDep) -> Any:
    """
    HTML Content for Password Recovery
    """
    user = UserDAO(session).find_one_or_none({"email": email})

    if not user:
        raise HTTPException(
            status_code=404,
            detail="The user with this username does not exist in the system.",
        )
    password_reset_token = generate_password_reset_token(email=email)
    email_data = generate_reset_password_email(
        email_to=user.email, email=email, token=password_reset_token
    )

    return HTMLResponse(
        content=email_data.html_content, headers={"subject:": email_data.subject}
    )
