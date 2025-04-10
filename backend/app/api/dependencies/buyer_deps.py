from typing import Annotated

from fastapi import Depends

from app.api.dependencies.deps import CommittedSessionDep
from app.api.services.purchase_service import PurchaseService
from app.api.services.sale_service import SaleService


def get_purchase_service(session: CommittedSessionDep) -> PurchaseService:
    """Returns PurchaseService instance with current session"""
    return PurchaseService(session)

PurchaseServiceDep = Annotated[PurchaseService, Depends(get_purchase_service)]


def get_sale_service(session: CommittedSessionDep) -> SaleService:
    """Returns SaleService instance with current session"""
    return SaleService(session)

SaleServiceDep = Annotated[SaleService, Depends(get_sale_service)]