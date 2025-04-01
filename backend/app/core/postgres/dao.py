from typing import Optional
from uuid import UUID

from app.core.postgres.base import BaseDAO
from app.core.security import verify_password
from app.models.core import User, Product, UserProductInteraction, CartItem, Transaction,TimeZone

from app.schemas.core_schemas import TransactionType, TransactionCreate, TransactionStatus


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

    def update_cash_balance(self, user_id: UUID, amount: float) -> User:
        """Atomic user cash balance update"""
        user = self.find_one_or_none_by_id(user_id)
        if not user:
            raise ValueError("User not found")

        user.cash_balance += amount
        return self.update({"id": user_id}, {"balance": user.balance})

    def update_pv_balance(self, user_id: UUID, amount: float):
        """Atomic user pv balance update"""
        user = self.find_one_or_none_by_id(user_id)
        if not user:
            raise ValueError("User not found")
        user.pv_balance += amount

class ProductDAO(BaseDAO[Product]):
    model = Product

class UserProductInteractionDAO(BaseDAO[UserProductInteraction]):
    model = UserProductInteraction

class CartItemDAO(BaseDAO[CartItem]):
    model = CartItem

class TransactionDAO(BaseDAO[Transaction]):
    model = Transaction
    def create_transaction(self,
            user_id: UUID,
            amount: float,
            pv_amount: float,
            transaction_type: TransactionType,
            product_id: UUID = None,
            additional_info: dict = None
    ) -> Transaction:
        """Creates transaction record"""
        transaction = TransactionCreate(
            user_id=user_id,
            cash_amount=amount,
            pv_amount=pv_amount,
            type=transaction_type,
            product_id=product_id,
            status=TransactionStatus.COMPLETED,
            additional_info=additional_info
        )
        return self.add(transaction)

class TimeZoneDAO(BaseDAO[TimeZone]):
    model = TimeZone

    def find_by_name(self, name: str) -> Optional[TimeZone]:
        """Find a timezone by name"""
        return self.find_one_or_none({"name": name})

    def find_by_offset(self, offset: str) -> Optional[TimeZone]:
        """Find a timezone by offset"""
        return self.find_one_or_none({"offset": offset})
    
