from datetime import datetime, timedelta, timezone
from uuid import UUID
from fastapi import APIRouter, HTTPException, status
from app.api.deps import CommittedSessionDep, CurrentUser, UncommittedSessionDep
from app.core.postgres.dao import (
    ProductDAO,
    UserProductInteractionDAO,
    CartItemDAO,
    TransactionDAO, UserDAO
)
from app.schemas.core_schemas import (
    UserProductInteractionCreate,
    InteractionType,
    CartItemCreate,
    TransactionCreate,
    TransactionType, TransactionStatus
)
from app.models.core import Transaction

router = APIRouter(tags=["Interaction"], prefix="/interaction")


def update_user_balance(
        session: CommittedSessionDep,
        user_id: UUID,
        points: float,
        transaction_type: TransactionType,
        product_id: UUID = None,
        additional_info: dict = None
) -> Transaction:
    """Creates transaction and updates user's balance"""
    user = UserDAO(session).update_balance(user_id, points)

    transaction = TransactionCreate(
        user_id=user_id,
        amount=0.0,  # Need to be configured for money transactions
        points=points,
        type=transaction_type,
        product_id=product_id,
        status=TransactionStatus.COMPLETED,
        additional_info=additional_info
    )
    transaction = TransactionDAO(session).add(transaction)
    # Update user balance
    user.balance += points
    return transaction


@router.post("/buy", status_code=status.HTTP_201_CREATED)
async def buy_product(
        product_id: UUID,
        session: CommittedSessionDep,
        current_user: CurrentUser
):
    """Register product purchase with transaction recording"""
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

    # 1. Register purchase interaction (для аналитики)
    interaction = UserProductInteractionCreate(
        user_id=current_user.id,
        product_id=product.id,
        interaction_type=InteractionType.PURCHASE,
        points_awarded=0,  # Баллы будут в транзакции
        additional_info={"purchase_at": datetime.now(timezone.utc).isoformat()}
    )
    UserProductInteractionDAO(session).add(interaction)

    # 2. Create financial transaction
    transaction = await update_user_balance(
        session=session,
        user_id=current_user.id,
        points=product.points_value,
        transaction_type=TransactionType.PURCHASE,
        product_id=product.id,
        additional_info={
            "action": "product_purchase",
            "product_price": float(product.price)
        }
    )

    # 3. Remove from cart if exists
    CartItemDAO(session).delete({
        "user_id": current_user.id,
        "product_id": product.id
    })

    return {
        "message": "Purchase successful",
        "points_earned": float(product.points_value),
        "new_balance": float(transaction.user.balance),
        "transaction_id": str(transaction.id)
    }


@router.post("/add_to_cart", status_code=status.HTTP_201_CREATED)
async def add_to_cart(
        quantity: int,
        product_id: UUID,
        session: CommittedSessionDep,
        current_user: CurrentUser
):
    """Add item to cart with bonus points"""
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
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Product already in cart"
        )

    # 1. Add cart interaction (Analytics)
    UserProductInteractionDAO(session).add(UserProductInteractionCreate(
        user_id=current_user.id,
        product_id=product.id,
        interaction_type=InteractionType.CART_ADD,
        points_awarded=0,  # scores in transaction
        additional_info={"added_at": datetime.now(timezone.utc).isoformat()}
    ))

    # Award points for adding to cart
    bonus_points = 1.0
    transaction = await update_user_balance(
        session=session,
        user_id=current_user.id,
        points=bonus_points,
        transaction_type=TransactionType.BONUS,
        product_id=product.id,
        additional_info={"action": "cart_add_bonus"}
    )

    # Create cart item
    item = CartItemDAO(session).add(CartItemCreate(
        user_id=current_user.id,
        product_id=product.id,
        quantity=quantity
    ))

    return {
        "message": "Product added to cart",
        "cart_item_id": str(item.id),
        "quantity": item.quantity,
        "bonus_points": float(bonus_points),
        "new_balance": float(transaction.user.balance)
    }


@router.delete("/remove_from_cart/{product_id}", status_code=status.HTTP_200_OK)
async def remove_from_cart(
        product_id: UUID,
        session: CommittedSessionDep,
        current_user: CurrentUser
):
    """Remove item from cart with cleanup"""
    if not current_user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required"
        )

    # 1. Delete cart item
    deleted_count = CartItemDAO(session).delete({
        "user_id": current_user.id,
        "product_id": product_id
    })

    if not deleted_count:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Item not found in cart"
        )

    # 2. Remove cart interaction
    UserProductInteractionDAO(session).delete({
        "user_id": current_user.id,
        "product_id": product_id,
        "interaction_type": InteractionType.CART_ADD
    })

    return {"message": "Item removed from cart"}


@router.post("/view_product", status_code=status.HTTP_201_CREATED)
async def view_product(
        product_id: UUID,
        session: CommittedSessionDep,
        current_user: CurrentUser
):
    """Register product view with points"""
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

    # Check for existing view in last 24 hours
    last_24h = datetime.now(timezone.utc) - timedelta(hours=24)
    existing_view = UserProductInteractionDAO(session).find_one_or_none(
        {
            "user_id": current_user.id,
            "product_id": product.id,
            "interaction_type": InteractionType.VIEW,
            "interaction_date": (">", last_24h)
        }
    )

    if existing_view:
        return {"message": "View already registered today"}

    # 1. Create view interaction (аналитика)
    interaction = UserProductInteractionCreate(
        user_id=current_user.id,
        product_id=product.id,
        interaction_type=InteractionType.VIEW,
        points_awarded=0,  # Баллы в транзакции
        additional_info={"source": "web"}
    )
    UserProductInteractionDAO(session).add(interaction)

    # 2. Award points for viewing
    view_points = 1.0
    transaction = await update_user_balance(
        session=session,
        user_id=current_user.id,
        points=view_points,
        transaction_type=TransactionType.BONUS,
        product_id=product.id,
        additional_info={"action": "product_view"}
    )

    # 3. Cleanup old views (keep last 100)
    view_count = UserProductInteractionDAO(session).count(
        {"user_id": current_user.id, "interaction_type": InteractionType.VIEW}
    )

    if view_count > 100:
        oldest_views = UserProductInteractionDAO(session).find_all(
            filters={"user_id": current_user.id, "interaction_type": InteractionType.VIEW},
            limit=view_count - 100
        )
        for view in oldest_views:
            UserProductInteractionDAO(session).delete({"user_id": view.user_id, "interaction_type": InteractionType.VIEW})

    return {
        "message": "Product view registered",
        "points_awarded": float(view_points),
        "product_title": product.title,
        "product_id": str(product.id),
        "new_balance": float(transaction.user.balance)
    }

@router.get("/get_my_cart", status_code=status.HTTP_200_OK)
def get_my_cart(session: UncommittedSessionDep,
        current_user: CurrentUser):
    if not current_user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required"
        )
    return CartItemDAO(session).find_all(filters={"user_id": current_user.id})


