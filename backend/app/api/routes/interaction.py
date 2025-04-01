import logging
from datetime import datetime,timezone
from decimal import Decimal

from uuid import UUID
from fastapi import APIRouter, HTTPException, status
from app.api.deps import CommittedSessionDep, CurrentUser, UncommittedSessionDep, PurchaseServiceDep

from app.core.postgres.dao import (
    ProductDAO,
    UserProductInteractionDAO,
    CartItemDAO,
    TransactionDAO,
)
from app.schemas.core_schemas import (
    UserProductInteractionCreate,
    InteractionType,
    CartItemCreate,
    TransactionCreate,
    TransactionType,
    TransactionStatus, PurchaseResponse
)
from app.models.core import Transaction

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
router = APIRouter(tags=["Interaction"], prefix="/interaction")


def create_transaction(
        session: CommittedSessionDep,
        user_id: UUID,
        amount: Decimal,
        pv_amount: Decimal,
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
    return TransactionDAO(session).add(transaction)


@router.post("/buy", status_code=status.HTTP_201_CREATED, response_model=PurchaseResponse)
def buy_product(
        product_id: UUID,
        current_user: CurrentUser,
        purchase_service: PurchaseServiceDep
):
    """
    Processes the purchase of a product

    """
    if not current_user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required"
        )

    try:
        return purchase_service.process_purchase(
            user_id=current_user.id,
            product_id=product_id
        )
    except HTTPException as he:
        return {"message": "HTTP Error", "status": he.status_code, "detail": str(he.detail)}
    except Exception as e:
        logger.error(f"Purchase failed: {str(e)}", exc_info=True)
        raise HTTPException(
            status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )


@router.post("/add_to_cart", status_code=status.HTTP_201_CREATED)
async def add_to_cart(
        product_id: UUID,
        session: CommittedSessionDep,
        current_user: CurrentUser,
        quantity: int = 1,
):
    """Add item to cart"""
    if not current_user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required"
        )

    product = ProductDAO(session).find_one_or_none_by_id(product_id)
    if not product or not product.is_active:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Product not available"
        )

    # Check existing cart item
    existing_item = CartItemDAO(session).find_one_or_none({
        "user_id": current_user.id,
        "product_id": product.id
    })

    if existing_item:
        existing_item.quantity += quantity
        session.add(existing_item)
        session.commit()
        return {"message": "Cart item quantity updated"}

    # Register cart interaction
    UserProductInteractionDAO(session).add(UserProductInteractionCreate(
        user_id=current_user.id,
        product_id=product.id,
        interaction_type=InteractionType.CART_ADD,
        pv_awarded=0,
        additional_info={"added_at": datetime.now(timezone.utc).isoformat()}
    ))

    # Create cart item
    item = CartItemDAO(session).add(CartItemCreate(
        user_id=current_user.id,
        product_id=product.id,
        quantity=quantity
    ))

    return {
        "message": "Product added to cart",
        "cart_item_id": str(item.id),
        "quantity": item.quantity
    }


@router.post("/add_to_favorites", status_code=status.HTTP_201_CREATED)
async def add_to_favorites(
        product_id: UUID,
        session: CommittedSessionDep,
        current_user: CurrentUser
):
    """Add product to favorites"""
    if not current_user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required"
        )

    product = ProductDAO(session).find_one_or_none_by_id(product_id)
    if not product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Product not found"
        )

    # Check if already in favorites
    existing = UserProductInteractionDAO(session).find_one_or_none({
        "user_id": current_user.id,
        "product_id": product.id,
        "interaction_type": InteractionType.FAVORITE
    })

    if existing:
        return {"message": "Product already in favorites"}

    # Add to favorites
    UserProductInteractionDAO(session).add(UserProductInteractionCreate(
        user_id=current_user.id,
        product_id=product.id,
        interaction_type=InteractionType.FAVORITE,
        pv_awarded=0,
        additional_info={"added_at": datetime.now(timezone.utc).isoformat()}
    ))

    return {"message": "Product added to favorites"}


@router.delete("/remove_from_favorites/{product_id}", status_code=status.HTTP_200_OK)
async def remove_from_favorites(
        product_id: UUID,
        session: CommittedSessionDep,
        current_user: CurrentUser
):
    """Remove product from favorites"""
    if not current_user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required"
        )

    deleted_count = UserProductInteractionDAO(session).delete({
        "user_id": current_user.id,
        "product_id": product_id,
        "interaction_type": InteractionType.FAVORITE
    })

    if not deleted_count:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Product not found in favorites"
        )

    return {"message": "Product removed from favorites"}


@router.get("/get_favorites", status_code=status.HTTP_200_OK)
async def get_favorites(
        session: UncommittedSessionDep,
        current_user: CurrentUser
):
    """Get user's favorite products"""
    if not current_user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required"
        )

    favorites = UserProductInteractionDAO(session).find_all(filters={
        "user_id": current_user.id,
        "interaction_type": InteractionType.FAVORITE
    })

    return [fav.product for fav in favorites]


@router.get("/get_my_cart", status_code=status.HTTP_200_OK)
async def get_my_cart(
        session: UncommittedSessionDep,
        current_user: CurrentUser
):
    """Get user's cart items"""
    if not current_user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required"
        )

    return CartItemDAO(session).find_all(filters={"user_id": current_user.id})


@router.delete("/remove_from_cart/{product_id}", status_code=status.HTTP_200_OK)
async def remove_from_cart(
        product_id: UUID,
        session: CommittedSessionDep,
        current_user: CurrentUser
):
    """Remove item from cart"""
    if not current_user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required"
        )

    deleted_count = CartItemDAO(session).delete({
        "user_id": current_user.id,
        "product_id": product_id
    })

    if not deleted_count:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Item not found in cart"
        )

    return {"message": "Item removed from cart"}