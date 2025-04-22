import uuid
from typing import Any
from fastapi import APIRouter, HTTPException
from starlette import status

from app.api.dependencies.deps import CommittedSessionDep
from app.api.services.hierarchy_service import HierarchyService
from app.api.services.wallet_service import WalletService
from app.core.postgres.dao import UserDAO, UserMLMDAO
from app.core.security import get_password_hash
from app.schemas.mlm import UserMLMCreate, UserMLMInput
from app.schemas.types.localization_types import CurrencyType

from app.schemas.users import UserPublic, CreateRequest, TestSponsorCreate, UserWithMLM

router = APIRouter(tags=["private"], prefix="/private")

@router.post("/create-sponsor", response_model=UserPublic)
def create_test_sponsor(
    sponsor_in: TestSponsorCreate,
    session: CommittedSessionDep
):
    user_dao = UserDAO(session)
    wallet_service = WalletService(session)
    if user_dao.find_one_or_none({"email": sponsor_in.email}):
        raise HTTPException(status_code=400, detail="Sponsor with this email already exists")
    sponsor_dict = sponsor_in.model_dump()
    password = sponsor_dict.pop("password")
    sponsor_dict["hashed_password"] = get_password_hash(password)
    new_sponsor = user_dao.add(sponsor_dict)
    wallet_service.create_default_wallets(new_sponsor.id, CurrencyType.RUB)
    return UserPublic.model_validate(new_sponsor)



@router.post("/users/", response_model=UserWithMLM)
def create_user(signup_data: CreateRequest, session: CommittedSessionDep) -> Any:
    """
    Create a new user with MLM data and attach to the hierarchy.
    """
    user_in = signup_data.user
    user_mlm_data = signup_data.mlm
    user_dao = UserDAO(session)
    wallet_service = WalletService(session)
    hierarchy_service = HierarchyService(session)

    if user_dao.find_one_or_none({"email": user_in.email}):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="The user with this email already exists in the system"
        )

    # Validate sponsor by referral_code
    if not user_in.referral_code:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Referral code is required")
    sponsor = user_dao.find_one_or_none({"referral_code": user_in.referral_code})
    if not sponsor:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Sponsor not found"
        )

    # Hash password and create user
    user_dict = user_in.model_dump(exclude={"password", "referral_code"})
    user_dict["hashed_password"] = get_password_hash(user_in.password)
    user_dict["referral_code"] = uuid.uuid4().hex[:8]
    user = user_dao.add(user_dict)
    # Add to hierarchy
    hierarchy_service.create_chain_for_new_user(
        sponsor_id=sponsor.id,
        new_user_id=user.id,
    )
    wallet_service.create_default_wallets(user.id, CurrencyType.RUB)
    # Add MLM data
    user_mlm_dao = UserMLMDAO(session)
    user_mlm_create = UserMLMCreate(
        user_id=user.id,
        contract_type=user_mlm_data.contract_type,
        current_rank=user_mlm_data.current_rank,
        current_club=user_mlm_data.current_club,
        personal_volume=user_mlm_data.personal_volume,
        group_volume=user_mlm_data.group_volume,
        accumulated_volume=user_mlm_data.accumulated_volume,
        binary_volume_left=user_mlm_data.binary_volume_left,
        binary_volume_right=user_mlm_data.binary_volume_right,
        sponsor_id=sponsor.id,
        placement_sponsor_id=user_mlm_data.placement_sponsor_id if user_mlm_data.placement_sponsor_id else sponsor.id,
        mentor_id=user_mlm_data.mentor_id,
    )
    mlm = user_mlm_dao.add(user_mlm_create)

    return UserWithMLM(
        user=UserPublic.model_validate(user),
        mlm=UserMLMInput.model_validate(mlm)
    )