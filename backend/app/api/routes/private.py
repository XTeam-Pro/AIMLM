from typing import Any

from fastapi import APIRouter


from app.api.deps import CommittedSessionDep
from app.core.security import get_password_hash
from app.models.core import User
from app.schemas.core_schemas import UserPublic,UserCreate

router = APIRouter(tags=["private"], prefix="/private")





@router.post("/users/", response_model=UserPublic)
def create_user(user_in: UserCreate, session: CommittedSessionDep) -> Any:
    """
    Create a new user.
    """
    user = User(
        email=user_in.email,
        username=user_in.username,
        full_name=user_in.full_name,
        phone=user_in.phone,
        hashed_password=get_password_hash(user_in.hashed_password),
        postcode=user_in.postcode,
        address=user_in.address,
        cash_balance=user_in.cash_balance,
        pv_balance=user_in.pv_balance,
        role=user_in.role,
        status=user_in.status
    )

    session.add(user)
    session.commit()

    return user
