from decimal import Decimal
from uuid import UUID
from sqlalchemy.orm import Session
from app.core.postgres.dao import UserHierarchyDAO, UserMLMDAO, BonusDAO, UserDAO
from app.schemas.mlm import BonusCreate
from app.schemas.types.gamification_types import BonusType
from app.schemas.types.localization_types import CurrencyType


class SponsorBonusService:
    def __init__(self, session: Session):
        self.session = session
        self.hierarchy_dao = UserHierarchyDAO(session)
        self.user_mlm_dao = UserMLMDAO(session)
        self.user_dao = UserDAO(session)
        self.bonus_dao = BonusDAO(session)

    def calculate(self, user_id: UUID) -> dict:
        level_1 = self.hierarchy_dao.find_all(filters={
            "ancestor_id": user_id,
            "level": 1
        })

        total_bonus = 0
        per_user = []

        for record in level_1:
            user_mlm = self.user_mlm_dao.find_one_or_none({"user_id": record.descendant_id})
            if user_mlm:
                pv = float(user_mlm.personal_volume or 0)
                bonus = pv * 0.05  # 5% sponsor bonus  (fixed)
                total_bonus += bonus
                per_user.append({
                    "user_id": str(record.descendant_id),
                    "personal_volume": pv,
                    "bonus": round(bonus, 2)
                })

        return {
            "total": round(total_bonus, 2),
            "details": per_user
        }

    def distribute(self, user_id: UUID):
        result = self.calculate(user_id)
        for item in result["details"]:
            self.user_dao.update_cash_balance(item["user_id"], Decimal(item["bonus"]))
            self.bonus_dao.add(BonusCreate(
                user_id=item["user_id"],
                amount=item["bonus"],
                bonus_type=BonusType.SPONSOR,
                is_paid=True,
                currency=CurrencyType.RUB,
                calculation_period="30 days"
            ))