from _pydecimal import Decimal
from typing import Optional
from uuid import UUID

from app.core.postgres.base import BaseDAO
from app.core.security import verify_password
from app.models.mlm import UserMLM, Bonus
from app.models.user import User, Product, UserProductInteraction, CartItem, Transaction,TimeZone
from app.models.gamification import Achievement, UserAchievement, Challenge, Team, UserChallenge


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

    def find_by_name(self, name: str) -> Optional[TimeZone]:
        """Find a timezone by name"""
        return self.find_one_or_none({"name": name})

    def find_by_offset(self, offset: str) -> Optional[TimeZone]:
        """Find a timezone by offset"""
        return self.find_one_or_none({"offset": offset})

class AchievementDAO(BaseDAO[Achievement]):
    model = Achievement

class UserAchievementDAO(BaseDAO[UserAchievement]):
    model = UserAchievement

class ChallengeDAO(BaseDAO[Challenge]):
    model = Challenge

class TeamDAO(BaseDAO[Team]):
    model = Team

class BonusDAO(BaseDAO[Bonus]):
    model = Bonus

class UserMLMDAO(BaseDAO[UserMLM]):
    model = UserMLM

class UserChallengeDAO(BaseDAO[UserChallenge]):
    model = UserChallenge