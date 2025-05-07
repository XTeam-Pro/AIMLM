from uuid import UUID
from typing import Optional
from decimal import Decimal
from sqlalchemy.orm import Session
from app.core.postgres.dao import UserMLMDAO, BusinessCenterDAO
from app.schemas.types.common_types import MLMRankType


class BinaryTreeService:
    def __init__(self, session: Session):
        self.session = session
        self.user_mlm_dao = UserMLMDAO(session)
        self.center_dao = BusinessCenterDAO(session)

    def auto_place_user(self, user_id: UUID) -> Optional[UUID]:
        user_mlm = self.user_mlm_dao.find_one_or_none({"user_id": user_id})
        if not user_mlm or not user_mlm.placement_sponsor_id:
            return None

        sponsor_mlm = self.user_mlm_dao.find_one_or_none({"user_id": user_mlm.placement_sponsor_id})
        if not sponsor_mlm:
            return None

        sponsor_centers = self.center_dao.find_all(filters={"owner_id": sponsor_mlm.id})
        sponsor_center = next((c for c in sponsor_centers if c.center_number == 1), None)

        if not sponsor_center:
            return None

        # Find children (left and right)
        left_child = self.center_dao.find_one_or_none({
            "parent_center_id": sponsor_center.id,
            "position_in_parent": "left"
        })
        right_child = self.center_dao.find_one_or_none({
            "parent_center_id": sponsor_center.id,
            "position_in_parent": "right"
        })

        if left_child and right_child:
            # If both branches are occupied, the placement is impossible
            return None

        position = "left" if not left_child else "right"

        # Creating a new business center for user
        new_center = self.center_dao.add({
            "owner_id": user_mlm.id,
            "center_number": 1,
            "parent_center_id": sponsor_center.id,
            "position_in_parent": position,
            "left_volume": Decimal(0),
            "right_volume": Decimal(0)
        })

        return new_center.id

    def run_placement_cron(self) -> list[UUID]:
        """
        Finds all users who reached 1 CARAT rank and are not yet placed in binary tree.
        Automatically places them using auto_place_user().
        Returns list of user_ids who were placed.
        """
        # Find all MLM-users with required rank
        eligible_users = self.user_mlm_dao.find_all(filters={
            "current_rank": MLMRankType.CARAT_1
        })

        placed_users = []

        for user_mlm in eligible_users:
            existing_centers = self.center_dao.find_all(filters={"owner_id": user_mlm.id})
            if existing_centers:
                continue  # User already in the binary structure

            placed_center_id = self.auto_place_user(user_mlm.user_id)
            if placed_center_id:
                placed_users.append(user_mlm.user_id)

        return placed_users
