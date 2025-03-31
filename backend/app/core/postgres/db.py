

from app.api.deps import CommittedSessionDep
from app.core.postgres.dao import UserDAO

from app.schemas.core_schemas import UserCreate
from app.core.postgres.config import settings
from app.schemas.core_schemas import UserRole, UserStatus

def init_db(session: CommittedSessionDep) -> None:
        user = UserDAO(session).find_one_or_none({"email": settings.FIRST_SUPERUSER})
        if not user:
            superuser_data = {
                "email": settings.FIRST_SUPERUSER,
                "username": "administrator",
                "phone": "+1234567890",
                "full_name": "Super User",
                "hashed_password": settings.FIRST_SUPERUSER_PASSWORD,
                "address": "123 Admin St, Admin City",
                "postcode": "ADMIN01",
                "role": UserRole.ADMIN.value,
                "status": UserStatus.ACTIVE.value,
                "balance": 0.0,
                "timezone_id": 0,
                "mentor_id": None
            }
            user_in = UserCreate(**superuser_data)
            UserDAO(session).add(user_in)
            session.commit()