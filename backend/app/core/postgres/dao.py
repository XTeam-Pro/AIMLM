from _pydecimal import Decimal
from typing import Optional
from uuid import UUID

from app.core.postgres.base import BaseDAO
from app.core.security import verify_password
from app.models.mlm import UserMLM, Bonus, UserHierarchy, BusinessCenter, GenerationBonusMatrix, UserActivity, \
    UserRankHistory
from app.models.user import User, UserProductInteraction, Transaction
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

# class ExchangeRateDAO(BaseDAO[ExchangeRate]):
#     model = ExchangeRate

# class WalletDAO(BaseDAO[Wallet]):
#     model = Wallet

    # def get_user_wallet(self, user_id: UUID, wallet_type: str) -> Wallet:
    #     return self.find_one_or_none({
    #         "user_id": user_id,
    #         "type": wallet_type
    #     })

    def update_balance(self, user_id: UUID, wallet_type: str, amount: Decimal):
        ...
        # wallet = self.get_user_wallet(user_id, wallet_type)
        # if not wallet:
        #     raise ValueError("Wallet not found")
        # wallet.balance += amount
        # return self.update({"id": wallet.id}, {"balance": wallet.balance})

class ProductDAO(BaseDAO[Product]):
    model = Product

class UserProductInteractionDAO(BaseDAO[UserProductInteraction]):
    model = UserProductInteraction

class CartItemDAO(BaseDAO[CartItem]):
    model = CartItem

class TransactionDAO(BaseDAO[Transaction]):
    model = Transaction

# class TimeZoneDAO(BaseDAO[TimeZone]):
#     model = TimeZone

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

    def update_pv_balance(self, user_id: UUID, amount: Decimal):
        """Atomic user pv balance update"""
        mlm_user = self.find_one_or_none_by_id(user_id)
        if not mlm_user:
            raise ValueError("User not found")
        mlm_user.personal_volume += amount
        return self.update({"user_id": user_id}, {"pv_balance": mlm_user.personal_volume})


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