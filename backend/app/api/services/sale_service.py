from datetime import datetime, timezone
from decimal import Decimal
from uuid import UUID

from fastapi import HTTPException
from pydantic import BaseModel

from app.api.services.mlm_service import MLMService
from app.core.postgres.dao import (
    ProductDAO,
    UserDAO,
    TransactionDAO,
)
from app.schemas.core_schemas import (
    TransactionCreate,
)
from app.schemas.types.common_types import TransactionType, TransactionStatus


class UpdatedBalances(BaseModel):
    distributor_pv: float
    distributor_cash: float

class SellerBalances(BaseModel):
    cash: Decimal
    pv: Decimal

class SaleResponse(BaseModel):
    message: str
    transaction_id: UUID
    cash_amount: Decimal
    pv_amount: Decimal
    new_cash_balance: Decimal
    new_pv_balance: Decimal
    transaction_type: TransactionType

class SaleService:
    def __init__(self, session):
        self.session = session
        self._product_dao = ProductDAO(session)
        self._user_dao = UserDAO(session)
        self._transaction_dao = TransactionDAO(session)
        self._mlm_service = MLMService(session)
        self._bonus_dao = BonusDAO(session)

    def process_sale(self, seller_id: UUID, product_id: UUID, buyer_id: UUID) -> SaleResponse:
        """Process MLM sale transaction with full bonus distribution"""
        seller = self._validate_seller(seller_id)
        buyer = self._get_user(buyer_id)
        product = self._validate_product(product_id)

        self._check_buyer_funds(buyer, product.price)

        is_sponsor_sale = buyer.sponsor_id == seller_id
        transaction_type = self._determine_transaction_type(is_sponsor_sale)

        # Update balances
        seller_balances = self._update_balances(
            seller_id=seller_id,
            buyer_id=buyer_id,
            product=product,
            is_sponsor_sale=is_sponsor_sale
        )

        # Create transaction
        transaction = self._create_transaction(
            seller_id=seller_id,
            buyer_id=buyer_id,
            product=product,
            transaction_type=transaction_type
        )

        # Distribute MLM bonuses
        if is_sponsor_sale:
            self._distribute_mlm_bonuses(buyer_id, product)

        return SaleResponse(
            message="Sale processed successfully",
            transaction_id=transaction.id,
            cash_amount=product.price,
            pv_amount=product.pv_value,
            new_cash_balance=seller_balances.cash,
            new_pv_balance=seller_balances.pv,
            transaction_type=transaction_type
        )

    def _determine_transaction_type(self, is_sponsor_sale: bool) -> TransactionType:
        return TransactionType.NETWORK_SALE if is_sponsor_sale else TransactionType.RETAIL_SALE

    def _update_balances(self, seller_id: UUID, buyer_id: UUID, product, is_sponsor_sale: bool):
        """Update all relevant balances with MLM logic"""
        # Deduct from buyer
        self._user_dao.update_cash_balance(buyer_id, -product.price)

        # Calculate seller share (50% for sponsor, 30% for direct sale)
        seller_share = product.price * Decimal('0.5' if is_sponsor_sale else '0.3')
        self._user_dao.update_cash_balance(seller_id, seller_share)

        # Add PV to seller
        self._user_dao.update_pv_balance(seller_id, product.pv_value)

        # Company gets remaining amount
        company_share = product.price - seller_share
        self._user_dao.update_company_balance(company_share)

        seller = self._user_dao.find_one_or_none_by_id(seller_id)
        return SellerBalances(cash=seller.cash_balance, pv=seller.pv_balance)

    def _create_transaction(self, seller_id: UUID, buyer_id: UUID, product, transaction_type: TransactionType):
        """Create transaction record according to MLM structure"""
        transaction_data = TransactionCreate(
            cash_amount=product.price,
            pv_amount=product.pv_value,
            type=transaction_type,
            status=TransactionStatus.COMPLETED,
            buyer_id=buyer_id,
            seller_id=seller_id,
            product_id=product.id,
            additional_info={
                "is_mlm_transaction": True,
                "sponsor_sale": transaction_type == TransactionType.NETWORK_SALE,
                "product_price": float(product.price),
                "pv_value": float(product.pv_value),
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
        )
        return self._transaction_dao.add(transaction_data)

    def _distribute_mlm_bonuses(self, buyer_id: UUID, product):
        """Trigger MLM bonus distribution"""
        self._mlm_service.distribute_mlm_bonuses(
            buyer_id=buyer_id,
            product_price=product.price,
            pv_value=product.pv_value
        )

    # Validation methods
    def _validate_seller(self, user_id: UUID):
        user = self._user_dao.find_one_or_none_by_id(user_id)
        if not user or not user.is_distributor:
            raise HTTPException(status_code=403, detail="User is not authorized to perform sales")
        return user

    def _validate_product(self, product_id: UUID):
        product = self._product_dao.find_one_or_none_by_id(product_id)
        if not product or not product.is_active:
            raise HTTPException(status_code=404, detail="Product not available for sale")
        return product

    def _get_user(self, user_id: UUID):
        user = self._user_dao.find_one_or_none_by_id(user_id)
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        return user

    def _check_buyer_funds(self, buyer, product_price: Decimal):
        if buyer.cash_balance < product_price:
            raise HTTPException(status_code=400, detail="Insufficient buyer funds")