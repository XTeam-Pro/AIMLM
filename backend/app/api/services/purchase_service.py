from datetime import datetime, timezone
from uuid import UUID

from fastapi import HTTPException
from fastapi.exceptions import ResponseValidationError

from app.core.postgres.dao import (
    ProductDAO,
    UserDAO,
    CartItemDAO,
    UserProductInteractionDAO,
    TransactionDAO
)
from app.schemas.core_schemas import (
    PurchaseResponse,
    UserProductInteractionCreate,
    InteractionType,
    TransactionType,
    TransactionCreate,
    TransactionStatus
)


class PurchaseService:
    def __init__(self, session):
        self.session = session
        self._product_dao = ProductDAO(session)
        self._user_dao = UserDAO(session)
        self._cart_dao = CartItemDAO(session)
        self._transaction_dao = TransactionDAO(session)
        self._interaction_dao = UserProductInteractionDAO(session)

    def process_purchase(self, user_id: UUID, product_id: UUID) -> PurchaseResponse:
        """Base method for purchase handling"""

        product = self._validate_product(product_id)
        user = self._get_user(user_id)

        self._check_user_funds(user, product.price)
        self._create_interaction(user_id, product)
        updated_user = self._update_balances(user_id, product)
        transaction = self._create_transaction(user_id, product)
        self._remove_from_cart(user_id, product_id)

        return PurchaseResponse(
            message="Purchase successful",
            pv_earned=product.pv_value,
            new_pv_balance=updated_user.pv_balance,
            new_cash_balance=updated_user.cash_balance,
            transaction_id=transaction.id
        )

    def _validate_product(self, product_id: UUID):
        """Checks availability of a product"""
        product = self._product_dao.find_one_or_none_by_id(product_id)
        if not product or not product.is_active:
            raise HTTPException(status_code=409, detail="Product not available for purchase")
        return product

    def _get_user(self, user_id: UUID):
        """Gets user"""
        user = self._user_dao.find_one_or_none_by_id(user_id)
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        return user

    def _check_user_funds(self, user, product_price):
        """Checks whether user have enough money or not"""
        if user.cash_balance < product_price:
            raise HTTPException(status_code=400, detail="Not enough funds to complete purchase")

    def _create_interaction(self, user_id: UUID, product):
        """Creates a record about interaction"""
        interaction_data = UserProductInteractionCreate(
            user_id=user_id,
            product_id=product.id,
            interaction_type=InteractionType.PURCHASE,
            pv_awarded=product.pv_value,
            additional_info={"purchased_at": datetime.now(timezone.utc).isoformat()}
        )
        self._interaction_dao.add(interaction_data)

    def _update_balances(self, user_id: UUID, product):
        """Updates user's balance"""
        self._user_dao.update_pv_balance(user_id, product.pv_value)
        self._user_dao.update_cash_balance(user_id, -product.price)
        return self._user_dao.find_one_or_none_by_id(user_id)

    def _create_transaction(self, user_id: UUID, product):
        """Creates a transaction"""
        transaction = TransactionCreate(
            user_id=user_id,
            cash_amount=product.price,
            pv_amount=product.pv_value,
            type=TransactionType.PURCHASE,
            product_id=product.id,
            status=TransactionStatus.COMPLETED,
            additional_info={
                "action": "product_purchase",
                "product_price": float(product.price)
            }
        )
        return self._transaction_dao.add(transaction)

    def _remove_from_cart(self, user_id: UUID, product_id: UUID):
        """Removes a product from the cart"""
        self._cart_dao.delete({
            "user_id": user_id,
            "product_id": product_id
        })