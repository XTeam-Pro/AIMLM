import uuid
from typing import Any

from fastapi import APIRouter, Depends, HTTPException


from app.api.deps import (
    CurrentUser,
    get_current_active_superuser,
    CommittedSessionDep,
    UncommittedSessionDep,
)
from app.core.postgres.config import settings
from app.core.postgres.dao import (
    UserProductInteractionDAO,
    UserDAO,
    CartItemDAO
)
from app.core.security import get_password_hash, verify_password
from app.schemas.core_schemas import (
    UsersPublic,
    UserPublic,
    UserCreate,
    UserUpdateMe,
    Message,
    UpdatePassword,
    UserUpdate,
    UserRegister
)
from app.utils import generate_new_account_email, send_email

router = APIRouter(prefix="/users", tags=["users"])


@router.get(
    "/",
    dependencies=[Depends(get_current_active_superuser)],
    response_model=UsersPublic,
)
def read_users(
        session: UncommittedSessionDep,
        skip: int = 0,
        limit: int = 100
) -> Any:
    """
    Retrieve a specific number of users.
    """
    user_dao = UserDAO(session)
    count = user_dao.count()
    users = user_dao.find_all(skip=skip, limit=limit)
    result = []
    for user in users:
        result.append(UserPublic.model_validate(user))

    return UsersPublic(data=result, count=count)


@router.post(
    "/",
    dependencies=[Depends(get_current_active_superuser)],
    response_model=UserPublic
)
def create_user(
        *,
        session: CommittedSessionDep,
        user_in: UserCreate
) -> Any:
    """
    Create new user.
    """
    user_dao = UserDAO(session)
    if user_dao.find_one_or_none({"email": user_in.email}):
        raise HTTPException(
            status_code=400,
            detail="The user with this email already exists in the system.",
        )

    user = user_dao.add(user_in.model_dump())

    if settings.emails_enabled and user_in.email:
        email_data = generate_new_account_email(
            email_to=user_in.email,
            username=user_in.username,
            password=user_in.password
        )
        send_email(
            email_to=user_in.email,
            subject=email_data.subject,
            html_content=email_data.html_content,
        )
    return user


@router.patch("/me", response_model=UserPublic)
def update_user_me(
        *,
        session: CommittedSessionDep,
        user_in: UserUpdateMe,
        current_user: CurrentUser
) -> Any:
    """
    Update own user.
    """
    user_dao = UserDAO(session)

    if user_in.email:
        existing_user = user_dao.find_one_or_none({"email": user_in.email})
        if existing_user and existing_user.id != current_user.id:
            raise HTTPException(
                status_code=409,
                detail="User with this email already exists"
            )

    return user_dao.update(
        {"id": current_user.id},
        user_in.model_dump(exclude_unset=True)
    )


@router.patch("/me/password", response_model=Message)
def update_password_me(
        *,
        session: CommittedSessionDep,
        body: UpdatePassword,
        current_user: CurrentUser
) -> Any:
    """
    Update own password.
    """
    if not verify_password(body.current_password, current_user.hashed_password):
        raise HTTPException(status_code=400, detail="Incorrect password")
    if body.current_password == body.new_password:
        raise HTTPException(
            status_code=400,
            detail="New password cannot be the same as the current one"
        )

    user_dao = UserDAO(session)
    user_dao.update(
        {"id": current_user.id},
        {"hashed_password": get_password_hash(body.new_password)}
    )
    return Message(message="Password updated successfully")


@router.get("/me", response_model=UserPublic)
def read_user_me(current_user: CurrentUser) -> Any:
    """
    Get current user.
    """
    return current_user


@router.delete("/me", response_model=Message)
def delete_user_me(
        session: CommittedSessionDep,
        current_user: CurrentUser
) -> Any:
    """
    Delete own user.
    """
    if current_user.is_superuser:
        raise HTTPException(
            status_code=403,
            detail="Super users are not allowed to delete themselves"
        )

    UserProductInteractionDAO(session).delete({"user_id": current_user.id})
    CartItemDAO(session).delete({"user_id": current_user.id})
    UserDAO(session).delete({"id": current_user.id})

    return Message(message="User deleted successfully")


@router.post("/signup", response_model=UserPublic)
def register_user(
        session: CommittedSessionDep,
        user_in: UserRegister
) -> Any:
    """
    Create new user without the need to be logged in.
    """
    user_dao = UserDAO(session)
    if user_dao.find_one_or_none({"email": user_in.email}):
        raise HTTPException(
            status_code=400,
            detail="The user with this email already exists in the system",
        )
    user_create = UserCreate(**user_in.model_dump())
    return user_dao.add(user_create)

@router.get("/{user_id}", response_model=UserPublic)
def read_user_by_id(
        user_id: uuid.UUID,
        session: CommittedSessionDep,
        current_user: CurrentUser
) -> Any:
    """
    Get a specific user by id.
    """
    user_dao = UserDAO(session)
    user = user_dao.find_one_or_none_by_id(user_id)

    if user == current_user:
        return user
    if current_user.role != "admin":
        raise HTTPException(
            status_code=403,
            detail="The user doesn't have enough privileges",
        )
    return user


@router.patch(
    "/{user_id}",
    dependencies=[Depends(get_current_active_superuser)],
    response_model=UserPublic,
)
def update_user(
        *,
        session: CommittedSessionDep,
        user_id: uuid.UUID,
        user_in: UserUpdate,
) -> Any:
    """
    Update a user.
    """
    user_dao = UserDAO(session)
    db_user = user_dao.find_one_or_none_by_id(user_id)

    if not db_user:
        raise HTTPException(
            status_code=404,
            detail="The user with this id does not exist in the system",
        )

    if user_in.email:
        existing_user = user_dao.find_one_or_none({"email": user_in.email})
        if existing_user and existing_user.id != user_id:
            raise HTTPException(
                status_code=409,
                detail="User with this email already exists"
            )

    return user_dao.update(
        {"id": user_id},
        user_in.model_dump(exclude_unset=True)
    )


@router.delete(
    "/{user_id}",
    dependencies=[Depends(get_current_active_superuser)],
    response_model=Message
)
def delete_user(
        session: CommittedSessionDep,
        current_user: CurrentUser,
        user_id: uuid.UUID
) -> Message:
    """
    Delete a user.
    """
    user_dao = UserDAO(session)
    user = user_dao.find_one_or_none_by_id(user_id)

    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    if user == current_user:
        raise HTTPException(
            status_code=403,
            detail="Super users are not allowed to delete themselves"
        )

    UserProductInteractionDAO(session).delete({"user_id": user_id})
    CartItemDAO(session).delete({"user_id": user_id})
    user_dao.delete({"id": user_id})

    return Message(message="User deleted successfully")