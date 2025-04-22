from decimal import Decimal
from uuid import UUID

from fastapi import HTTPException
from sqlmodel import Session

from app.core.postgres.dao import WalletDAO, TransactionDAO
from app.models.common import Transaction
from app.schemas.common import TransactionCreate
from app.schemas.types.common_types import TransactionStatus, TransactionType
from app.schemas.types.localization_types import CurrencyType
from app.schemas.types.user_types import WalletType
from app.schemas.users import WalletCreate


class WalletService:
    def __init__(self, session: Session):
        self.session = session
        self.wallet_dao = WalletDAO(session)
        self.transaction_dao = TransactionDAO(session)

    def credit_bonus(self, user_id: UUID, amount: Decimal):
        return self.wallet_dao.update_balance(user_id, WalletType.BONUS, amount)

    def create_default_wallets(self, user_id: UUID, currency: CurrencyType):
        for wallet_type in [WalletType.BONUS, WalletType.GIFT]:
            self.wallet_dao.add(WalletCreate(
                user_id=user_id,
                currency=currency,
                type=wallet_type
            ))

    def transfer_to_gift(self, user_id: UUID, amount: Decimal):
        bonus_wallet = self.wallet_dao.get_user_wallet(user_id, WalletType.BONUS)
        gift_wallet = self.wallet_dao.get_user_wallet(user_id, WalletType.GIFT)

        if bonus_wallet.balance < amount:
            raise HTTPException(status_code=400, detail="Not enough funds")

        self.wallet_dao.update_balance(user_id, WalletType.BONUS, -amount)
        self.wallet_dao.update_balance(user_id, WalletType.GIFT, amount)

    def move_funds_and_log_transaction(
            self,
            source_user_id: UUID,
            target_user_id: UUID,
            amount: Decimal,
            transaction_type: TransactionType,
            pv_amount: Decimal = Decimal(0),
            product_id: UUID | None = None,
            note: str = ""
    ) -> Transaction:
        source_wallet = self.wallet_dao.get_user_wallet(source_user_id, WalletType.BONUS)
        target_wallet = self.wallet_dao.get_user_wallet(target_user_id, WalletType.BONUS)

        if source_wallet.balance < amount:
            raise HTTPException(status_code=400, detail="Not enough funds")

        # Update the balance
        self.wallet_dao.update_balance(source_user_id, WalletType.BONUS, -amount)
        self.wallet_dao.update_balance(target_user_id, WalletType.BONUS, amount)

        # Log the transaction
        transaction_data = TransactionCreate(
            buyer_id=source_user_id,
            seller_id=target_user_id,
            source_wallet_id=source_wallet.id,
            target_wallet_id=target_wallet.id,
            cash_amount=amount,
            pv_amount=pv_amount,
            type=transaction_type,
            product_id=product_id,
            status=TransactionStatus.COMPLETED,
            additional_info={"note": note}
        )
        return self.transaction_dao.add(transaction_data)

    def withdraw(self, user_id: UUID, amount: Decimal):
        # withdrawal logic + agreement  check and  jurisdiction
        ...