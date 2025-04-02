from typing import Optional
from uuid import UUID

from app.core.postgres.base import BaseDAO
from app.core.security import verify_password,get_password_hash
from app.models.core import User, Product, UserProductInteraction, CartItem, Transaction,TimeZone

from app.schemas.core_schemas import TransactionType, TransactionCreate, TransactionStatus
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)


class UserDAO(BaseDAO[User]):
    model = User

    def authenticate(self, email: str, password: str) -> Optional[User]:
        """Authenticate a user with email and password"""
        logger.info(f"dao 1  {email} pass {password }")

        user = self.find_one_or_none({"email": email})
        logger.info(f"dao 2  step 2")

        if not user:
            logger.info(f"dao not user")
            return None
        logger.info(f"dao found user")
        logger.info(f"dao user hashed {user.hashed_password}")
        if not verify_password(password, user.hashed_password):
            logger.info(f"dao bad password")
            return None
        logger.info(f"dao okay password")
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
    
