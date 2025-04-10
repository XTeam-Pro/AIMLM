
from typing import Any

from fastapi import APIRouter, HTTPException
from starlette import status

from app.api.dependencies.deps import CommittedSessionDep
from app.core.postgres.dao import UserDAO
from app.schemas.users import UserCreate, UserPublic

router = APIRouter(tags=["private"], prefix="/private")





@router.post("/users/", response_model=UserPublic)
def create_user(user_in: UserCreate, session: CommittedSessionDep) -> Any:
    """
    Create a new user.
    """
    if UserDAO(session).find_one_or_none(filters={"email": user_in.email}):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Such user already exists"
        )
    user = UserDAO(session).add(user_in)
    return user
