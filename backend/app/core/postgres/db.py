from sqlmodel import Session

from app.core.postgres.dao import TimeZoneDAO, UserDAO


from app.schemas.types.gamification_types import RankType

from app.core.postgres.config import settings

from app.core.security import get_password_hash
from app.schemas.localization import TimeZoneCreate
from app.schemas.types.localization_types import TimeZoneNames
from app.schemas.types.user_types import UserRole, UserStatus
from app.schemas.users import UserCreate


def init_db(session: Session) -> None:
    """
    Initialize the database with default timezones and superuser
     """
    timezone_dao = TimeZoneDAO(session)
    timezones = [
        {"name": TimeZoneNames.UTC, "offset": "+00:00"},
        {"name": TimeZoneNames.GMT, "offset": "+00:00"},
        {"name": TimeZoneNames.EST, "offset": "-05:00"},
        {"name": TimeZoneNames.EDT, "offset": "-04:00"},
        {"name": TimeZoneNames.CST, "offset": "-06:00"},
        {"name": TimeZoneNames.CDT, "offset": "-05:00"},
        {"name": TimeZoneNames.PST, "offset": "-08:00"},
        {"name": TimeZoneNames.PDT, "offset": "-07:00"},
        {"name": TimeZoneNames.AEST, "offset": "+10:00"},
        {"name": TimeZoneNames.AEDT, "offset": "+11:00"},
        {"name": TimeZoneNames.BST, "offset": "+01:00"},
        {"name": TimeZoneNames.CET, "offset": "+01:00"},
        {"name": TimeZoneNames.CEST, "offset": "+02:00"},
        {"name": TimeZoneNames.IST, "offset": "+05:30"},
        {"name": TimeZoneNames.JST, "offset": "+09:00"},
    ]
    for timezone_data in timezones:
    # Convert dict to Pydantic model instance before passing to DAO
        timezone_model = TimeZoneCreate(**timezone_data)
        if not timezone_dao.find_one_or_none({"name": timezone_model.name}):
            timezone_dao.add(timezone_model)
    session.commit()
    user_dao = UserDAO(session)
    user = user_dao.find_one_or_none({"email": settings.FIRST_SUPERUSER})
    if not user:
        superuser_data = {
            "email": settings.FIRST_SUPERUSER,
            "username": "administrator",
            "phone": "+1234567890",
            "full_name": "Super User",
            "hashed_password": get_password_hash(settings.FIRST_SUPERUSER_PASSWORD),
            "address": "123,Admin St,AdminCity",
            "postcode": "ADMIN01",
        }
        user_dao.add(superuser_data)
    session.commit()