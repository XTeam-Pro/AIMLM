from uuid import UUID
from datetime import datetime, timezone
from decimal import Decimal
from typing import Optional

from app.api.services.hierarchy_service import HierarchyService
from app.core.postgres.dao import UserMLMDAO, UserRankHistoryDAO
from app.schemas.types.common_types import MLMRankType


class RankPromotionService:
    def __init__(self, session):
        self.session = session
        self.user_mlm_dao = UserMLMDAO(session)
        self.rank_history_dao = UserRankHistoryDAO(session)
        self.hierarchy_service = HierarchyService(session)

        # Конфигурация рангов (минимальный PV в линии)
        self.rank_requirements = {
            MLMRankType.CARAT_1: Decimal("500"),
            MLMRankType.CARAT_2: Decimal("1000"),
            MLMRankType.CARAT_3: Decimal("2000"),
            MLMRankType.CRYSTAL: Decimal("4000"),
            MLMRankType.RUBIN: Decimal("6000"),
            MLMRankType.SAPPHIRE: Decimal("10000"),
            # ... и т.д.
        }

    def check_and_promote(self, user_id: UUID) -> Optional[MLMRankType]:
        """Check current user and promote if conditions met"""
        user_mlm = self.user_mlm_dao.find_one_or_none({"user_id": user_id})
        if not user_mlm:
            return None

        current_rank = MLMRankType(user_mlm.current_rank)

        for rank, required_pv in self.rank_requirements.items():
            if current_rank.value == rank.value:
                continue  # Already reached the rank

            # Check for 3 active lines
            count = self.hierarchy_service.count_active_lines(
                user_id=user_id,
                threshold=required_pv,
                period=self._current_period()
            )
            if count >= 3:
                # Update the rank
                self.user_mlm_dao.update({"user_id": user_id}, {"current_rank": rank})
                self.rank_history_dao.add({
                    "user_id": user_mlm.id,
                    "rank": rank,
                    "club": user_mlm.current_club,
                    "qualification_period": self._current_period_str(),
                    "group_volume": user_mlm.group_volume,
                    "personal_volume": user_mlm.personal_volume,
                })
                return rank

        return None

    def _current_period(self):
        """Returns start and end of current calendar month"""
        now = datetime.now(timezone.utc)
        start = datetime(now.year, now.month, 1)
        if now.month == 12:
            end = datetime(now.year + 1, 1, 1)
        else:
            end = datetime(now.year, now.month + 1, 1)
        return start, end

    def _current_period_str(self):
        """Returns string like '2025-04' for history"""
        now = datetime.utcnow()
        return f"{now.year}-{now.month:02}"