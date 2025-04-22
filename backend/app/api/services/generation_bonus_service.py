
from decimal import Decimal

from datetime import datetime, timezone
from uuid import UUID

from sqlalchemy.orm import Session

from app.core.postgres.dao import (
    UserHierarchyDAO,
    UserMLMDAO,
    GenerationBonusMatrixDAO,
    BonusDAO
)
from app.schemas.mlm import BonusCreate
from app.schemas.types.gamification_types import BonusType
from app.schemas.types.localization_types import CurrencyType


class GenerationBonusService:
    def __init__(self, session: Session):
        self.session = session
        self.hierarchy_dao = UserHierarchyDAO(session)
        self.mlm_dao = UserMLMDAO(session)
        self.bonus_matrix_dao = GenerationBonusMatrixDAO(session)
        self.bonus_dao = BonusDAO(session)

    def calculate(self, period_key: str = None) -> list[BonusCreate]:
        """
        Distributes Generation Bonuses to uplines (up to 7 levels)
        based on the binary bonuses received by downline users in a given period.
        """
        # Default to current month if no period is provided
        if not period_key:
            now = datetime.now(timezone.utc)
            period_key = f"{now.year}-{now.month:02}"

        # Fetch all binary bonuses paid during the period
        binary_bonuses = self.bonus_dao.find_all(filters={
            "bonus_type": BonusType.BINARY,
            "calculation_period": period_key,
            "is_paid": True
        })

        bonuses_to_create: list[BonusCreate] = []

        for binary_bonus in binary_bonuses:
            recipient_id = binary_bonus.user_id
            bonus_amount = binary_bonus.amount

            # Find all uplines (ancestors) of the recipient
            uplines = self.hierarchy_dao.find_all(filters={"descendant_id": recipient_id})

            for upline in uplines:
                generation = upline.level
                if generation > 7:
                    continue  # Only 7 generations are eligible

                upline_id = upline.ancestor_id
                upline_mlm = self.mlm_dao.find_one_or_none({"user_id": upline_id})
                if not upline_mlm:
                    continue

                # Get applicable bonus percentage for this rank and generation
                matrix_entry = self.bonus_matrix_dao.find_one_or_none({
                    "rank": upline_mlm.current_rank,
                    "generation": generation
                })
                if not matrix_entry:
                    continue

                percentage = matrix_entry.bonus_percentage
                generation_bonus = (bonus_amount * percentage / Decimal(100)).quantize(Decimal("0.01"))

                if generation_bonus <= 0:
                    continue

                # Create generation bonus record for the upline
                bonuses_to_create.append(BonusCreate(
                    user_id=upline_id,
                    amount=generation_bonus,
                    bonus_type=BonusType.GENERATION,
                    is_paid=True,
                    currency=CurrencyType.RUB,
                    calculation_period=period_key
                ))

        # Save all bonuses in the database
        for bonus in bonuses_to_create:
            self.bonus_dao.add(bonus)

        return bonuses_to_create

    def calculate_for_user(self, user_id: UUID, period_key: str = None) -> dict[int, float]:
        """
        Returns a generation bonus breakdown for a single user.
        Format: {generation_level: bonus_amount}
        """
        if not period_key:
            now = datetime.now(timezone.utc)
            period_key = f"{now.year}-{now.month:02}"

        bonuses = self.bonus_dao.find_all(filters={
            "bonus_type": BonusType.BINARY,
            "calculation_period": period_key,
            "is_paid": True,
            "user_id": user_id
        })

        total_by_generation: dict[int, Decimal] = {}

        for bonus in bonuses:
            uplines = self.hierarchy_dao.find_all(filters={"descendant_id": user_id})
            for upline in uplines:
                generation = upline.level
                if generation > 7:
                    continue
                upline_mlm = self.mlm_dao.find_one_or_none({"user_id": upline.ancestor_id})
                if not upline_mlm:
                    continue
                matrix_entry = self.bonus_matrix_dao.find_one_or_none({
                    "rank": upline_mlm.current_rank,
                    "generation": generation
                })
                if not matrix_entry:
                    continue

                percent = matrix_entry.bonus_percentage
                amount = (bonus.amount * percent / Decimal(100)).quantize(Decimal("0.01"))

                if generation not in total_by_generation:
                    total_by_generation[generation] = Decimal("0")
                total_by_generation[generation] += amount

        return {k: float(v) for k, v in total_by_generation.items()}