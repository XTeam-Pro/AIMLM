from decimal import Decimal
from uuid import UUID
from sqlalchemy.orm import Session
from app.core.postgres.dao import BusinessCenterDAO, UserDAO, BonusDAO
from app.schemas.mlm import BonusCreate
from app.schemas.types.gamification_types import BonusType
from app.schemas.types.localization_types import CurrencyType


class BinaryBonusService:
    def __init__(self, session: Session):
        self.session = session
        self.center_dao = BusinessCenterDAO(session)
        self.user_dao = UserDAO(session)
        self.bonus_dao = BonusDAO(session)

    def calculate(self, user_id: UUID) -> dict:
        centers = self.center_dao.find_all(filters={"owner_id": user_id})
        result = {}

        for center in centers:
            left = center.left_volume or 0
            right = center.right_volume or 0
            payout_volume = min(left, right)
            bonus_percentage = 0.10  # 10% binary bonus (adjustable)
            bonus = float(payout_volume) * bonus_percentage

            result[center.center_number] = {
                "left": float(left),
                "right": float(right),
                "payout_volume": float(payout_volume),
                "bonus": round(bonus, 2)
            }

        return result

    def process_binary_impact(self, user_id: UUID):
        results = self.calculate(user_id)
        for center_number, data in results.items():
            bonus_amount = Decimal(data["bonus"])
            self.user_dao.update_cash_balance(user_id, bonus_amount)
            self.bonus_dao.add(BonusCreate(
                user_id=user_id,
                amount=bonus_amount,
                bonus_type=BonusType.BINARY,
                is_paid=True,
                currency=CurrencyType.RUB,
                calculation_period="30 days"
            ))