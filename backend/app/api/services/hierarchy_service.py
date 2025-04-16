from collections import defaultdict
from datetime import datetime
from decimal import Decimal
from uuid import UUID
from sqlalchemy.orm import Session
from app.core.postgres.dao import UserHierarchyDAO, UserActivityDAO



class HierarchyService:
    def __init__(self, session: Session):
        self.session = session
        self.dao = UserHierarchyDAO(session)
        self.activity_dao = UserActivityDAO(session)

    def create_chain_for_new_user(self, sponsor_id: UUID, new_user_id: UUID) -> None:
        """
        Automatically builds a new hierarchy chain when a new user signs up
        """
        ancestors = self.dao.find_all(filters={"descendant_id": sponsor_id})
        for record in ancestors:
            self.dao.add({
                "ancestor_id": record.ancestor_id,
                "descendant_id": new_user_id,
                "level": record.level + 1
            })
        self.dao.add({
            "ancestor_id": sponsor_id,
            "descendant_id": new_user_id,
            "level": 1
        })

    def count_active_lines(self, user_id: UUID, threshold: Decimal, period: tuple[datetime, datetime]) -> int:
        """
        Count the number of active lines (direct lines under the user)
        that have activity over a given threshold in the specified period.
        """
        start_date, end_date = period

        # 1. Getting all user's descendants (hierarchically)
        descendants = self.dao.find_all(filters={"ancestor_id": user_id})
        if not descendants:
            return 0

        # 2. Group descendants by direct line (by direct ancestor)
        # Build mapping: { direct_child_id -> [descendants in this line] }
        lines = defaultdict(set)
        for record in descendants:
            if record.level == 1:
                lines[record.descendant_id].add(record.descendant_id)
            else:
                lines[record.descendant_id].add(record.descendant_id)

        # 3. Check out the activity in each line
        active_lines = 0
        for root_id, members in lines.items():
            for user_id_in_line in members:
                activity = self.activity_dao.find_one_or_none({
                    "user_id": user_id_in_line,
                    "period_start__gte": start_date,
                    "period_end__lte": end_date,
                    "personal_volume__gte": threshold
                })
                if activity:
                    active_lines += 1
                    break  # The line is active - no need to search further
        return active_lines