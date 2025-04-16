from uuid import UUID
from decimal import Decimal
from sqlalchemy.orm import Session
from app.core.postgres.dao import UserMLMDAO
from app.schemas.types.gamification_types import ClubType


class ClubService:
    def __init__(self, session: Session):
        self.session = session
        self.user_mlm_dao = UserMLMDAO(session)

    def determine_club(self, group_volume: Decimal) -> ClubType:
        """
        Determine the ClubType based on group_volume thresholds.
        """
        if group_volume >= Decimal("25000"):
            return ClubType.PREMIER
        elif group_volume >= Decimal("15000"):
            return ClubType.DIAMOND
        elif group_volume >= Decimal("5000"):
            return ClubType.GOLD
        elif group_volume >= Decimal("2000"):
            return ClubType.CRYSTAL
        else:
            return ClubType.PREMIER  # default fallback (or could be None)

    def check_and_update_user_club(self, user_id: UUID) -> str | None:
        """
        Check if the user should be upgraded to a new club and update if necessary.
        """
        user_mlm = self.user_mlm_dao.find_one_or_none({"user_id": user_id})
        if not user_mlm:
            return None

        current_club = user_mlm.current_club
        new_club = self.determine_club(user_mlm.group_volume)

        if new_club != current_club:
            self.user_mlm_dao.update(
                {"user_id": user_id},
                {"current_club": new_club}
            )
            return new_club

        return current_club