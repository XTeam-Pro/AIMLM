from _pydecimal import Decimal
from typing import Optional
from uuid import UUID

from app.core.postgres.base import BaseDAO
from app.core.security import verify_password
from app.models.mlm import UserMLM, Bonus, UserHierarchy, BusinessCenter, GenerationBonusMatrix, UserActivity, \
    UserRankHistory
from app.models.user import User, UserProductInteraction, Transaction,TimeZone
from app.models.gamification import Achievement, UserAchievement, Challenge, UserChallenge
from app.models.common import CartItem, Product, Purchase


class UserDAO(BaseDAO[User]):
    model = User

    def authenticate(self, email: str, password: str) -> Optional[User]:
        """Authenticate a user with email and password"""
        user = self.find_one_or_none({"email": email})
        if not user:
            return None
        if not verify_password(password, user.hashed_password):
            return None
        return user

    def update_cash_balance(self, user_id: UUID, amount: Decimal) -> User:
        """Atomic user cash balance update"""
        user = self.find_one_or_none_by_id(user_id)
        if not user:
            raise ValueError("User not found")

        user.cash_balance += amount
        return self.update({"id": user_id}, {"cash_balance": user.cash_balance})

    def update_pv_balance(self, user_id: UUID, amount: Decimal):
        """Atomic user pv balance update"""
        user = self.find_one_or_none_by_id(user_id)
        if not user:
            raise ValueError("User not found")
        user.pv_balance += amount
        return self.update({"id": user_id}, {"pv_balance": user.pv_balance})

class ProductDAO(BaseDAO[Product]):
    model = Product

class UserProductInteractionDAO(BaseDAO[UserProductInteraction]):
    model = UserProductInteraction

class CartItemDAO(BaseDAO[CartItem]):
    model = CartItem

class TransactionDAO(BaseDAO[Transaction]):
    model = Transaction

class TimeZoneDAO(BaseDAO[TimeZone]):
    model = TimeZone

class AchievementDAO(BaseDAO[Achievement]):
    model = Achievement

class UserAchievementDAO(BaseDAO[UserAchievement]):
    model = UserAchievement

class ChallengeDAO(BaseDAO[Challenge]):
    model = Challenge

class BonusDAO(BaseDAO[Bonus]):
    model = Bonus

class UserMLMDAO(BaseDAO[UserMLM]):
    model = UserMLM

class PurchaseDAO(BaseDAO[Purchase]):
    model = Purchase

class UserChallengeDAO(BaseDAO[UserChallenge]):
    model = UserChallenge

class UserRankHistoryDAO(BaseDAO[UserRankHistory]):
    model = UserRankHistory

class UserHierarchyDAO(BaseDAO[UserHierarchy]):
    model = UserHierarchy

class BusinessCenterDAO(BaseDAO[BusinessCenter]):
    model = BusinessCenter

class UserActivityDAO(BaseDAO[UserActivity]):
    model = UserActivity

class GenerationBonusMatrixDAO(BaseDAO[GenerationBonusMatrix]):
    model = GenerationBonusMatrix