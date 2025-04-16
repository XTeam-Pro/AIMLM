from uuid import UUID
from decimal import Decimal
from collections import defaultdict
from sqlalchemy.orm import Session

from app.core.postgres.dao import (
    UserHierarchyDAO,
    UserMLMDAO,
    GenerationBonusMatrixDAO
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

    def calculate(self, user_id: UUID) -> dict[int, Decimal]:
        """
        Returns dict: {generation (int): bonus sum (Decimal)}
        """
        # Getting all descendants in the hierarchy
        descendants = self.hierarchy_dao.find_all(filters={"ancestor_id": user_id})

        # Getting MLM user's profile
        user_mlm = self.mlm_dao.find_one_or_none({"user_id": user_id})
        if not user_mlm:
            return {}

        user_rank = user_mlm.current_rank

        # Getting all lines from the bonus matrix for the current rank
        rank_bonus_rules = self.bonus_matrix_dao.find_all(filters={"rank": user_rank})
        bonus_map = {r.generation: r.bonus_percentage for r in rank_bonus_rules}

        bonuses_by_generation = defaultdict(Decimal)

        for record in descendants:
            gen = record.level
            bonus_percent = bonus_map.get(gen)
            if not bonus_percent:
                continue

            descendant_mlm = self.mlm_dao.find_one_or_none({"user_id": record.descendant_id})
            if not descendant_mlm:
                continue

            pv = descendant_mlm.personal_volume or Decimal(0)
            bonus = (pv * bonus_percent / Decimal(100)).quantize(Decimal("0.01"))
            bonuses_by_generation[gen] += bonus

        return dict(bonuses_by_generation)

    def calculate_and_apply(self, user_id: UUID):
        bonuses = self.calculate(user_id)
        for generation, amount in bonuses.items():
            self.bonus_matrix_dao.add(BonusCreate(
                user_id=user_id,
                amount=amount,
                bonus_type=BonusType.MATCHING,
                is_paid=True,
                currency=CurrencyType.RUB,
                calculation_period="30 days"
            ))
