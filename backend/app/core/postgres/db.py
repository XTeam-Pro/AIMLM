from datetime import datetime, timezone
from uuid import uuid4

from sqlmodel import Session

from app.api.services.hierarchy_service import HierarchyService
from app.core.postgres.dao import UserDAO, UserMLMDAO

from app.core.postgres.config import settings

from app.core.security import get_password_hash
from app.schemas.types.common_types import MLMRankType, ContractType
from app.schemas.types.gamification_types import  ClubType
from app.schemas.types.localization_types import  CountryEnum
from app.schemas.types.user_types import UserRole, UserStatus

def init_db(session: Session) -> None:
    """
    Initialize the database with a default sponsor and superuser.
    """
    user_dao = UserDAO(session)
    mlm_dao = UserMLMDAO(session)
    # Check if superuser already exists
    existing_superuser = user_dao.find_one_or_none({"email": settings.FIRST_SUPERUSER})
    if existing_superuser:
        return
    # Create fake sponsor user (as upline reference)
    sponsor_data = {
        "email": "sponsor@google.com",
        "username": "sponsor_user",
        "phone": "+11111111111",
        "full_name": "Fake Sponsor",
        "country": CountryEnum.AUSTRALIA,
        "hashed_password": get_password_hash("String123"),
        "rank": MLMRankType.NEWBIE,
        "role": UserRole.DISTRIBUTOR,
        "status": UserStatus.ACTIVE,
        "registration_date": datetime.now(timezone.utc),
        "address": "Some Address",
        "postcode": "123456",
        "referral_code": uuid4().hex[:8]
    }

    sponsor = user_dao.add(sponsor_data)

    # Create actual superuser
    superuser_data = {
        "email": settings.FIRST_SUPERUSER,
        "username": "aleksandr",
        "phone": "+12345678901",
        "full_name": "Super Admin",
        "country": CountryEnum.USA,
        "hashed_password": get_password_hash(settings.FIRST_SUPERUSER_PASSWORD),
        "address": "123 Main St, New York",
        "referral_code": uuid4().hex[:8],
        "postcode": "10001",
        "role": UserRole.ADMIN,
        "status": UserStatus.ACTIVE,
        "rank": MLMRankType.GOLD,
        "registration_date": datetime.now(timezone.utc),
    }

    superuser = user_dao.add(superuser_data)

    # Create MLM data for superuser
    mlm_data = {
        "user_id": superuser.id,
        "contract_type": ContractType.BASIC,
        "current_rank": MLMRankType.NEWBIE,
        "current_club": ClubType.PREMIER,
        "personal_volume": 0,
        "group_volume": 0,
        "accumulated_volume": 0,
        "binary_volume_left": 0,
        "binary_volume_right": 0,
        "sponsor_id": sponsor.id,
        "placement_sponsor_id": None,
        "mentor_id": None
    }
    mlm_dao.add(mlm_data)
    HierarchyService(session).create_chain_for_new_user(
        sponsor_id=sponsor.id,
        new_user_id=superuser.id
    )
    session.commit()