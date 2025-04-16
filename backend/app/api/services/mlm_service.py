
from uuid import UUID

from app.api.services.binary_bonus_service import BinaryBonusService
from app.api.services.generation_bonus_service import GenerationBonusService
from app.api.services.rank_promotion_service import RankPromotionService
from app.api.services.sponsor_bonus_service import SponsorBonusService


class MLMService:
    def __init__(self, session):
        self.session = session
        self.sponsor_bonus_service = SponsorBonusService(session)
        self.generation_bonus_service = GenerationBonusService(session)
        self.binary_bonus_service = BinaryBonusService(session)
        self.rank_service = RankPromotionService(session)

    def on_product_purchase(self, buyer_id: UUID):
        """Main entrypoint for handling bonuses after purchase"""

        # 1. Credit sponsor bonuses (1–4 levels)
        self.sponsor_bonus_service.distribute(buyer_id)

        # 2. Credit genaration bonus
        self.generation_bonus_service.calculate_and_apply(buyer_id)

        # 3. Update binary volume and credit binary bonus
        self.binary_bonus_service.process_binary_impact(buyer_id)

        # 4. Update ranks (if new conditions are reached)
        self.rank_service.check_and_promote(buyer_id)