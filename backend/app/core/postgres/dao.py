from typing import Optional
from uuid import UUID

from app.core.postgres.base import BaseDAO
from app.core.security import verify_password
from app.models.core import User, Product, UserProductInteraction, CartItem, Transaction,TimeZone


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

    def update_balance(self, user_id: UUID, amount: float) -> User:
        """Atomic user balance update"""
        user = self.find_one_or_none_by_id(user_id)
        if not user:
            raise ValueError("User not found")

        user.balance += amount
        return self.update({"id": user_id}, {"balance": user.balance})

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