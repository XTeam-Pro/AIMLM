from uuid import UUID
from decimal import Decimal
from datetime import datetime, timezone

from sqlalchemy.orm import Session

from app.core.postgres.dao import (
    UserDAO,
    PurchaseDAO,
    BonusDAO, UserMLMDAO
)
from app.schemas.mlm import BonusCreate
from app.schemas.types.gamification_types import BonusType
from app.schemas.types.localization_types import CurrencyType


class SponsorBonusService:
    def __init__(self, session: Session):
        self.session = session
        self.user_dao = UserDAO(session)
        self.user_mlm_dao = UserMLMDAO(session)
        self.purchase_dao = PurchaseDAO(session)
        self.bonus_dao = BonusDAO(session)

    def _get_current_period(self) -> str:
        now = datetime.now(timezone.utc)
        return f"{now.year}-{now.month:02}"

    def calculate(self, user_id: UUID) -> dict[str, float]:
        """
        Calculate  bonus for direct referrals(level 1) .
        """
        sponsored_users = self.user_dao.find_all(filters={"sponsor_id": user_id})
        total_bonus = Decimal("0.00")

        for user in sponsored_users:
            # Find first purchase of this referral
            purchases = self.purchase_dao.find_all(filters={"user_id": user.id})
            if not purchases:
                continue

            first_purchase = min(purchases, key=lambda p: p.created_at)

            # Check if sponsor bonus already paid for this referral
            already_paid = self.bonus_dao.find_one_or_none(filters={
                "user_id": user_id,
                "bonus_type": BonusType.SPONSOR
            })
            if already_paid:
                continue

            # Calculate 5% of PV from first purchase
            pv = first_purchase.pv_value or Decimal(0)
            bonus_amount = (pv * Decimal("0.05")).quantize(Decimal("0.01"))

            if bonus_amount <= 0:
                continue

            # Create sponsor bonus
            self.bonus_dao.add(BonusCreate(
                user_id=user_id,
                amount=bonus_amount,
                bonus_type=BonusType.SPONSOR,
                is_paid=True,
                currency=CurrencyType.RUB,
                calculation_period=self._get_current_period(),
            ))

            total_bonus += bonus_amount

        return {
            "total": float(total_bonus),
            "sponsored_count": len(sponsored_users),
            "bonus_created": bool(total_bonus > 0)
        }

    def distribute(self, buyer_id: UUID) -> dict[str, float | str]:
        """
        Calculate and applies  bonus for direct referrals (level 1).
        Only applies to first purchase, and only if not already paid.
        """
        buyer = self.user_dao.find_one_or_none_by_id(buyer_id)
        if not buyer:
            return {"error": "buyer_not_found"}

        # 1. Check a sponsor
        mlm_info = self.user_mlm_dao.find_one_or_none(filters={"user_id": buyer_id})
        if not mlm_info or not mlm_info.sponsor_id:
            return {"error": "no_sponsor"}

        sponsor_id = mlm_info.sponsor_id

        # 2. Get all buyer's purchases
        purchases = self.purchase_dao.find_all(filters={"user_id": buyer_id})
        if not purchases:
            return {"error": "no_purchases"}

        # 3. Take the very first purchase
        first_purchase = min(purchases, key=lambda p: p.created_at)

        already_paid = self.bonus_dao.find_one_or_none(filters={
            "user_id": sponsor_id,
            "source_user_id": buyer_id,
            "bonus_type": BonusType.SPONSOR
        })
        if already_paid:
            return {"status": "already_paid"}

        pv = first_purchase.pv_value or Decimal(0)
        bonus_amount = (pv * Decimal("0.05")).quantize(Decimal("0.01"))

        if bonus_amount <= 0:
            return {"status": "zero_bonus"}

        self.bonus_dao.add(BonusCreate(
            user_id=sponsor_id,
            source_user_id=buyer_id,
            amount=bonus_amount,
            bonus_type=BonusType.SPONSOR,
            is_paid=True,
            currency=CurrencyType.RUB,
            calculation_period=self._get_current_period(),
        ))

        return {
            "status": "bonus_created",
            "sponsor_id": str(sponsor_id),
            "buyer_id": str(buyer_id),
            "bonus_amount": float(bonus_amount)
        }