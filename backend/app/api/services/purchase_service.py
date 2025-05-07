import uuid
from decimal import Decimal
from uuid import UUID

from fastapi import HTTPException
from pydantic import BaseModel

from app.api.services.mlm_service import MLMService
from app.api.services.wallet_service import WalletService
from app.core.postgres.dao import (
    ProductDAO,
    UserDAO,
    TransactionDAO
)
from app.schemas.common import TransactionCreate
from app.schemas.types.common_types import TransactionType, TransactionStatus


class PurchaseResponse(BaseModel):
    message: str
    buyer_cash_balance: Decimal
    seller_pv_earned: Decimal
    seller_pv_balance: Decimal
    transaction_id: uuid.UUID


class PurchaseService:
    def __init__(self, session):
        self.session = session
        self._product_dao = ProductDAO(session)
        self._user_dao = UserDAO(session)
        self._transaction_dao = TransactionDAO(session)
        self._mlm_service = MLMService(session)
        self._company_account_id = UUID("00000000-0000-0000-0000-000000000001")
        self._wallet_service = WalletService(session)

    def process_purchase(self, buyer_id: UUID, product_id: UUID, seller_id: UUID | None = None):  # PurchaseResponse:
        product = self._validate_product(product_id)
        buyer = self._get_user_with_mlm(buyer_id)
        seller = self._determine_seller(buyer, seller_id)

        self._check_user_funds(buyer, product.price)
        updated_buyer = self._update_user_balance(buyer.id, -product.price, Decimal(0))

        transaction_type = TransactionType.PRODUCT_PURCHASE
        if seller:
            is_sponsor = (
                    buyer.mlm_data and seller.id == buyer.mlm_data.sponsor_id
            )
            if is_sponsor:
                seller_cash = product.price * Decimal("0.5")
                seller_pv = product.pv_value
                company_share = product.price * Decimal("0.2")
            else:
                seller_cash = product.price * Decimal("0.3")
                seller_pv = product.pv_value * Decimal("0.8")
                company_share = product.price * Decimal("0.2")

            updated_seller = self._update_user_balance(seller.id, seller_cash, seller_pv)
            self._update_user_balance(self._company_account_id, company_share, Decimal(0))
        else:
            updated_seller = None
            self._update_user_balance(self._company_account_id, product.price, Decimal(0))

        transaction = self._create_transaction(
            buyer_id=buyer.id,
            seller_id=seller.id if seller else None,
            product=product,
            transaction_type=transaction_type
        )

        self._mlm_service.on_product_purchase(buyer.id)

        return PurchaseResponse(
            message="Purchase successful",
            buyer_cash_balance=updated_buyer.mlm_data if buyer else 0,
            seller_pv_earned=product.pv_value if seller else 0,
            seller_pv_balance=updated_seller.pv_balance if seller else 0,
            transaction_id=transaction.id
        )

    def _determine_seller(self, buyer, seller_id=None):
        if seller_id:
            return self._get_user_with_mlm(seller_id)
        elif buyer.mlm_data and buyer.mlm_data.sponsor_id:
            return self._get_user_with_mlm(buyer.mlm_data.sponsor_id)
        return None

    def _validate_product(self, product_id: UUID):
        product = self._product_dao.find_one_or_none_by_id(product_id)
        if not product or not product.is_active:
            raise HTTPException(status_code=409, detail="Product not available for purchase")
        return product

    def _get_user_with_mlm(self, user_id: UUID):
        user = self._user_dao.find_one_or_none_by_id(user_id)
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        return user

    def _check_user_funds(self, user, product_price):
        if user.cash_balance < product_price:
            raise HTTPException(status_code=400, detail="Not enough funds to complete purchase")

    def _update_user_balance(self, user_id: UUID, cash_amount: Decimal, pv_amount: Decimal):
        if cash_amount != 0:
            self._wallet_service.move_funds_and_log_transaction(
                source_user_id=user_id,
                target_user_id=self._company_account_id,
                amount=abs(cash_amount),
                transaction_type=TransactionType.PRODUCT_PURCHASE,
                note="Purchase of the good"
            )
        return self._user_dao.find_one_or_none_by_id(user_id)

    def _create_transaction(self, buyer_id: UUID, seller_id: UUID, product, transaction_type):
        transaction = TransactionCreate(
            buyer_id=buyer_id,
            seller_id=seller_id,
            cash_amount=product.price,
            pv_amount=product.pv_value,
            type=transaction_type,
            product_id=product.id,
            status=TransactionStatus.COMPLETED,
            additional_info={
                "action": "product_purchase",
                "product_price": float(product.price),
                "mlm_level": "direct" if seller_id == buyer_id else "upline"
            }
        )
        return self._transaction_dao.add(transaction)
