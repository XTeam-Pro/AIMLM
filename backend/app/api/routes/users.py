import logging
import uuid
from typing import Any
from fastapi import APIRouter, Depends, HTTPException
from starlette import status
from app.api.dependencies.deps import (
    CurrentUser,
    get_current_active_superuser,
    CommittedSessionDep,
    UncommittedSessionDep,
)
from app.api.services.hierarchy_service import HierarchyService

from app.core.postgres.dao import (
    UserProductInteractionDAO,
    UserDAO,
    CartItemDAO, UserMLMDAO, TransactionDAO, UserActivityDAO, UserRankHistoryDAO, PurchaseDAO, BonusDAO,
    UserHierarchyDAO#, WalletDAO
)
from app.core.security import get_password_hash, verify_password
from app.schemas.auth import UpdatePassword
from app.schemas.common import Message
from app.schemas.mlm import UserMLMCreate, UserMLMInput, UserMLMUpdate
from app.schemas.types.common_types import MLMRankType, ContractType
from app.schemas.types.gamification_types import ClubType
from app.schemas.users import UsersPublic, UserPublic, UserUpdateMe, UserUpdate, UserRegister, UserWithMLM
from app.schemas.users import CreateRequest

router = APIRouter(prefix="/users", tags=["Users"])
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

@router.get(
    "/",
    dependencies=[Depends(get_current_active_superuser)],
    response_model=UsersPublic,
)
def read_users(
    session: UncommittedSessionDep,
    skip: int = 0,
    limit: int = 100
) -> UsersPublic:
    user_dao = UserDAO(session)
    mlm_dao = UserMLMDAO(session)

    total = user_dao.count()
    users = user_dao.find_all(skip=skip, limit=limit)

    if not users:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No users found")

    user_ids = [user.id for user in users]
    mlm_records = mlm_dao.find_all(filters={"user_id": ("in", user_ids)})
    mlm_map = {mlm.user_id: mlm for mlm in mlm_records}

    result_data: list[UserWithMLM] = []

    for user in users:
        user_public = UserPublic.model_validate(user)
        mlm_data = mlm_map.get(user.id)
        mlm_public = UserMLMInput.model_validate(mlm_data.model_dump()) if mlm_data else None
        result_data.append(UserWithMLM(user=user_public, mlm=mlm_public))

    return UsersPublic(data=result_data, count=total)
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
                status_code=status.HTTP_409_CONFLICT,
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
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Incorrect password")
    if body.current_password == body.new_password:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="New password cannot be the same as the current one"
        )

    user_dao = UserDAO(session)
    user_dao.update(
        {"id": current_user.id},
        {"hashed_password": get_password_hash(body.new_password)}
    )
    return Message(message="Password updated successfully")


@router.get("/me", response_model=CreateRequest)
def read_user_me(current_user: CurrentUser, session: UncommittedSessionDep) -> Any:
    """
    Get current user.
    """
    user = UserDAO(session).find_one_or_none_by_id(current_user.id)
    user_mlm = UserMLMDAO(session).find_one_or_none(filters={"user_id": current_user.id})
    return CreateRequest(
        user=UserPublic.model_validate(user),
        mlm=UserMLMInput.model_validate(user_mlm.model_dump()) if user_mlm else None
    )

@router.delete("/me", response_model=Message)
def delete_user_me(
        session: CommittedSessionDep,
        current_user: CurrentUser
) -> Any:
    """
    Delete own user. Dangerous! Execute if you know what you are doing.
    """
    if not UserDAO(session).find_one_or_none_by_id(current_user.id):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User with this ID does not exist")
    if current_user.role ==  "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Super users are not allowed to delete themselves"
        )

    UserProductInteractionDAO(session).delete({"user_id": current_user.id})
    UserMLMDAO(session).delete({"user_id": current_user.id})
    CartItemDAO(session).delete({"user_id": current_user.id})
    UserActivityDAO(session).delete({"user_id": current_user.id})
    TransactionDAO(session).delete({"buyer_id": current_user.id})
    PurchaseDAO(session).delete({"user_id": current_user.id})
    UserRankHistoryDAO(session).delete({"user_id": current_user.id})
    BonusDAO(session).delete({"user_id": current_user.id})
    UserHierarchyDAO(session).delete({"ancestor_id": current_user.id})
    UserHierarchyDAO(session).delete({"descendant_id": current_user.id})
    UserDAO(session).delete({"id": current_user.id})
    return Message(message="User deleted successfully")


@router.post("/signup", response_model=UserWithMLM)
def register_user(
    session: CommittedSessionDep,
    user_in: UserRegister,
    is_client: bool = False,
) -> UserWithMLM:
    """
    Public signup endpoint. Registers a new user with default MLM settings.
    - is_client: Whether the user wants to be in the MLM structure or not
    """
    user_dao = UserDAO(session)
    user_mlm_dao = UserMLMDAO(session)
    hierarchy_service = HierarchyService(session)

    # Email already exists
    if user_dao.find_one_or_none({"email": user_in.email}):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="The user with this email already exists in the system"
        )

    # Validate referral code
    if not user_in.referral_code:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Referral code is required"
        )

    sponsor = user_dao.find_one_or_none({"referral_code": user_in.referral_code})
    if not sponsor:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Sponsor not found"
        )

    # Create user
    user_dict = user_in.model_dump(exclude={"password", "referral_code"})
    user_dict["hashed_password"] = get_password_hash(user_in.password)
    user_dict["referral_code"] = uuid.uuid4().hex[:8]
    user_dict["sponsor_id"] = sponsor.id
    user = user_dao.add(user_dict)

    # Create MLM profile only for non-clients
    mlm = None
    if not is_client:
        user_mlm_create = UserMLMCreate(
            user_id=user.id,
            contract_type=ContractType.BASIC,
            current_rank=MLMRankType.NEWBIE,
            current_club=ClubType.PREMIER,
            placement_sponsor_id=sponsor.id,
        )
        mlm = user_mlm_dao.add(user_mlm_create)
        hierarchy_service.create_chain_for_new_user(
            sponsor_id=sponsor.id,
            new_user_id=user.id
        )
    return UserWithMLM(
        user=UserPublic.model_validate(user),
        mlm=UserMLMInput.model_validate(mlm) if mlm else None
    )
@router.get("/{user_id}", response_model=CreateRequest)
def read_user_by_id(
        user_id: uuid.UUID,
        session: CommittedSessionDep,
        current_user: CurrentUser
) -> Any:
    """
    Get a specific user by id.
    """
    if current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Only admins can view other users"
        )
    user = UserDAO(session).find_one_or_none_by_id(user_id)
    user_mlm = UserMLMDAO(session).find_one_or_none(filters={"user_id": user_id})
    return CreateRequest(
        user=UserPublic.model_validate(user),
        mlm=UserMLMInput.model_validate(user_mlm.model_dump()) if user_mlm else None
    )


@router.patch(
    "/{user_id}",
    dependencies=[Depends(get_current_active_superuser)],
    response_model=UserWithMLM
)
def update_user(
        *,
        session: CommittedSessionDep,
        user_id: uuid.UUID,
        user_in: UserUpdate,
        user_mlm: UserMLMUpdate,
) -> Any:
    """
    Update a user.
    """
    user_dao = UserDAO(session)
    user_mlm_dao = UserMLMDAO(session)
    db_user = user_dao.find_one_or_none_by_id(user_id)

    if not db_user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="The user with this id does not exist in the system",
        )

    if user_in.email:
        existing_user = user_dao.find_one_or_none({"email": user_in.email})
        if existing_user and existing_user.id != user_id:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="User with this email already exists"
            )
    try:
        user = user_dao.update(
        {"id": user_id},
        user_in
        )
        user_mlm = user_mlm_dao.update(
  {"user_id": user_id},
            user_mlm)
        return UserWithMLM(
            user=UserPublic.model_validate(user),
            mlm=UserMLMInput.model_validate(user_mlm)
        )
    except Exception as e:
        logger.error("Failed to update user:", e)
        session.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update user"
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
    Delete a user (Dangerous! Execute if you know what you are doing).
    """
    user_dao = UserDAO(session)
    user = user_dao.find_one_or_none_by_id(user_id)

    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    if user == current_user:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Super users are not allowed to delete themselves"
        )
    try:
        UserProductInteractionDAO(session).delete({"user_id": user_id})
        #WalletDAO(session).delete({"user_id": user_id})
        CartItemDAO(session).delete({"user_id": user_id})
        UserActivityDAO(session).delete({"user_id": user_id})
        TransactionDAO(session).delete({"buyer_id": user_id})
        PurchaseDAO(session).delete({"user_id": user_id})
        UserRankHistoryDAO(session).delete({"user_id": user_id})
        BonusDAO(session).delete({"user_id": user_id})
        UserMLMDAO(session).delete({"user_id": user_id})
        UserHierarchyDAO(session).delete({"ancestor_id": user_id})
        UserHierarchyDAO(session).delete({"descendant_id": user_id})
        user_dao.delete({"id": user_id})
        return Message(message="User deleted successfully")
    except Exception as e:
        logger.error("Failed to delete this user:", e)
        session.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete this user"
        )