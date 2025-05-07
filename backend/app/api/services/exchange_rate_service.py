from decimal import Decimal
from datetime import datetime, timezone
from sqlmodel import Session

from app.schemas.types.localization_types import CurrencyType
from app.core.postgres.dao import ExchangeRateDAO


class ExchangeRateService:
    def __init__(self, session: Session):
        self.session = session
        self.dao = ExchangeRateDAO(session)

    def get_rate(self, from_currency: CurrencyType, to_currency: CurrencyType) -> Decimal:
        if from_currency == to_currency:
            return Decimal("1.0")

        rate_record = self.dao.find_one_or_none({
            "from_currency": from_currency,
            "to_currency": to_currency
        })

        if not rate_record:
            raise ValueError(f"Exchange rate not found for {from_currency} -> {to_currency}")

        return rate_record.rate

    def set_rate(self, from_currency: CurrencyType, to_currency: CurrencyType, rate: Decimal):
        existing = self.dao.find_one_or_none({
            "from_currency": from_currency,
            "to_currency": to_currency
        })

        data = {
            "from_currency": from_currency,
            "to_currency": to_currency,
            "rate": rate,
            "updated_at": datetime.now(timezone.utc)
        }

        if existing:
            return self.dao.update({"id": existing.id}, data)
        return self.dao.add(data)

    def convert(self, amount: Decimal, from_currency: CurrencyType, to_currency: CurrencyType) -> Decimal:
        rate = self.get_rate(from_currency, to_currency)
        return (amount * rate).quantize(Decimal("0.01"))