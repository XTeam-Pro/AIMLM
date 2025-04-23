import uuid
from datetime import datetime, timezone


from sqlmodel import Session

from app.api.services.hierarchy_service import HierarchyService
#from app.api.services.wallet_service import WalletService
from app.core.postgres.dao import UserDAO, UserMLMDAO

from app.core.postgres.config import settings

from app.core.security import get_password_hash
from app.schemas.types.common_types import MLMRankType, ContractType
from app.schemas.types.gamification_types import  ClubType
from app.schemas.types.localization_types import CountryEnum, CurrencyType
from app.schemas.types.user_types import UserRole, UserStatus


def init_db(session: Session) -> None:
    """
    Initialize the database with a default sponsor and superuser.
    """
    user_dao = UserDAO(session)
    mlm_dao = UserMLMDAO(session)
    #wallet_service = WalletService(session)
    hierarchy_service = HierarchyService(session)

    # Check if superuser already exists
    existing_superuser = user_dao.find_one_or_none({"email": settings.FIRST_SUPERUSER})
    if existing_superuser:
        return

    # Create fake sponsor user (as upline reference)
    sponsor_data = {
        "email": "sponsor@google.com",
        "name": "Fake",
        "surname": "Sponsor",
        "patronymic": "",
        "country": "Australia",
        "region": "",
        "phone": "+1234567890",
        "city": "",
        "gender": "MALE",
        "hashed_password": get_password_hash("String123"),
        "role": UserRole.DISTRIBUTOR,
        "status": UserStatus.ACTIVE,
        "registration_date": datetime.now(timezone.utc),
        "referral_code": "test-referral",
        "is_active": True
    }
    sponsor = user_dao.add(sponsor_data)

    # Create actual superuser
    superuser_data = {
        "email": settings.FIRST_SUPERUSER,
        "name": "Super",
        "surname": "Admin",
        "patronymic": "",
        "country": "USA",
        "region": "New York",
        "city": "New York",
        "phone": "+1234567890",
        "gender": "MALE",
        "hashed_password": get_password_hash(settings.FIRST_SUPERUSER_PASSWORD),
        "referral_code": uuid.uuid4().hex[:8],
        "role": UserRole.ADMIN,
        "status": UserStatus.ACTIVE,
        "registration_date": datetime.now(timezone.utc),
        "is_active": True,
        "sponsor_id": sponsor.id
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
        "placement_sponsor_id": sponsor.id,
        "mentor_id": None
    }
    mlm_dao.add(mlm_data)

    hierarchy_service.create_chain_for_new_user(
        sponsor_id=sponsor.id,
        new_user_id=superuser.id
    )
    session.commit()