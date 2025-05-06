from decimal import Decimal
from uuid import UUID
from sqlalchemy.orm import Session

from app.core.postgres.dao import BusinessCenterDAO, BonusDAO
from app.api.services.wallet_service import WalletService
from app.schemas.mlm import BonusCreate
from app.schemas.types.gamification_types import BonusType
from app.schemas.types.localization_types import CurrencyType
from app.schemas.types.common_types import TransactionType


class BinaryBonusService:
    def __init__(self, session: Session):
        self.session = session
        self.center_dao = BusinessCenterDAO(session)
        self.bonus_dao = BonusDAO(session)
        self.wallet_service = WalletService(session)
        self._company_account_id = UUID("00000000-0000-0000-0000-000000000001")  # Counting bonuses from the company

    def calculate(self, user_id: UUID) -> dict:
        centers = self.center_dao.find_all(filters={"owner_id": user_id})
        result = {}

        for center in centers:
            left = center.left_volume or Decimal(0)
            right = center.right_volume or Decimal(0)
            payout_volume = min(left, right)
            bonus_percentage = Decimal("0.10")  # 10% from the balance of a smaller side
            bonus = (payout_volume * bonus_percentage).quantize(Decimal("0.01"))

            result[center.center_number] = {
                "left": float(left),
                "right": float(right),
                "payout_volume": float(payout_volume),
                "bonus": float(bonus)
            }

        return result

    def process_binary_impact(self, user_id: UUID) -> dict:
        results = self.calculate(user_id)

        bonuses_issued = []

        for center_number, data in results.items():
            bonus_amount = Decimal(data["bonus"])

            if bonus_amount <= 0:
                continue  # нет смысла начислять 0

            self.wallet_service.move_funds_and_log_transaction(
                source_user_id=self._company_account_id,
                target_user_id=user_id,
                amount=bonus_amount,
                note=f"Бинарный бонус из центра {center_number}"
            )

            # Запись в BonusDAO
            self.bonus_dao.add(BonusCreate(
                user_id=user_id,
                amount=bonus_amount,
                bonus_type=BonusType.BINARY,
                is_paid=True,
                currency=CurrencyType.RUB,
                calculation_period=self._get_current_period()
            ))

            bonuses_issued.append({
                "center": center_number,
                "bonus": float(bonus_amount)
            })

        return {
            "user_id": str(user_id),
            "bonuses_issued": bonuses_issued,
            "total": float(sum(Decimal(b["bonus"]) for b in bonuses_issued))
        }

    def _get_current_period(self) -> str:
        from datetime import datetime, timezone
        now = datetime.now(timezone.utc)
        return f"{now.year}-{now.month:02}"
