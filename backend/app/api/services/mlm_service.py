from decimal import Decimal
from uuid import UUID
from typing import Optional, List


from pydantic import BaseModel

from app.core.postgres.dao import UserDAO, BonusDAO
from app.schemas.mlm import BonusCreate
from app.schemas.types.gamification_types import BonusType
from app.schemas.types.localization_types import CurrencyType


class SellerShare(BaseModel):
    cash_amount: Decimal
    pv_amount: Decimal


class MLMLevel(BaseModel):
    level: int
    percentage: float
    pv_percentage: float


class MLMBonus(BaseModel):
    receiver_id: UUID
    amount: Decimal | float
    pv_amount: Decimal | float
    level: Decimal | int
    bonus_type: BonusType


class MLMService:
    def __init__(self, session):
        self.session = session
        self._user_dao = UserDAO(session)
        self._bonus_dao = BonusDAO(session)

        # MLM-levels configuration (level: percentage, PV percentage)
        self.mlm_levels = [
            MLMLevel(level=1, percentage=0.30, pv_percentage=0.50),  # 30% cash, 50% PV for level 1
            MLMLevel(level=2, percentage=0.15,pv_percentage=0.30),  # 15% cash, 30% PV for level 2
            MLMLevel(level=3, percentage=0.10, pv_percentage=0.20),  # 10% cash, 20% PV for level 3
            MLMLevel(level=4, percentage=0.05,pv_percentage=0.10),  # 5% cash, 10% PV for level 4
        ]

    def distribute_mlm_bonuses(self, buyer_id: UUID, product_price: Decimal,
                               pv_value: Decimal, seller_id: Optional[UUID] = None):
        """Distribute bonuses across MLM upline structure"""
        buyer = self._user_dao.find_one_or_none_by_id(buyer_id)
        if not buyer or not buyer.sponsor_id:
            return

        current_sponsor_id = buyer.sponsor_id
        bonuses = []

        # Allocate bonuses by levels
        for level in self.mlm_levels:
            if not current_sponsor_id:
                break

            # Exclude the seller himself (he's already gained his share)
            if level.level == 1 and seller_id and current_sponsor_id == seller_id:
                current_sponsor = self._user_dao.find_one_or_none_by_id(current_sponsor_id)
                current_sponsor_id = current_sponsor.sponsor_id if current_sponsor else None
                continue

            cash_bonus = product_price * level.percentage
            pv_bonus = pv_value * level.pv_percentage

            bonuses.append(MLMBonus(
                receiver_id=current_sponsor_id,
                amount=cash_bonus,
                pv_amount=pv_bonus,
                level=level.level,
                bonus_type=BonusType.SPONSOR
            ))

            # Going to the next sponsor  in the upline
            current_sponsor = self._user_dao.find_one_or_none_by_id(current_sponsor_id)
            current_sponsor_id = current_sponsor.sponsor_id if current_sponsor else None

        # Apply all bonuses
        self._apply_bonuses(bonuses)

    def _apply_bonuses(self, bonuses: List[MLMBonus]):
        """Apply all calculated bonuses to users"""
        for bonus in bonuses:
            # Update users' balances
            self._user_dao.update_cash_balance(bonus.receiver_id, bonus.amount)
            self._user_dao.update_pv_balance(bonus.receiver_id, bonus.pv_amount)

            # Commit bonus transaction
            self._bonus_dao.add(BonusCreate(
                user_id=bonus.receiver_id,
                amount=bonus.amount,
                bonus_type=bonus.bonus_type,
                is_paid=True,
                currency=CurrencyType.RUB,
                calculation_period="30 days"
            ))
