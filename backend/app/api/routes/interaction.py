import logging
import time
from datetime import datetime,timezone

from uuid import UUID
from fastapi import APIRouter, HTTPException, status
from app.api.dependencies.deps import CommittedSessionDep, CurrentUser, UncommittedSessionDep, RedisDep

from app.core.postgres.dao import (
    ProductDAO,
    UserProductInteractionDAO,
    CartItemDAO, TransactionDAO,
)
from app.schemas.common import UserProductInteractionCreate, CartItemCreate, TransactionPublic
from app.schemas.types.common_types import InteractionType, TransactionType

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
router = APIRouter(tags=["interaction"], prefix="/interaction")

@router.get("/get_purchased", response_model=list[TransactionPublic])
def get_my_products(
    session: UncommittedSessionDep,
    current_user: CurrentUser,
    skip: int = 0,
    limit: int = 100
):
    """
    Returns all product purchase transactions for the current user.
    """
    if not current_user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required"
        )

    transactions = TransactionDAO(session).find_all(
        skip=skip,
        limit=limit,
        filters={
            "buyer_id": current_user.id,
            "type": TransactionType.PRODUCT_PURCHASE
        }
    )

    return [TransactionPublic.model_validate(t) for t in transactions]
@router.post("/track_view", status_code=status.HTTP_201_CREATED)
def track_product_view(
        session: CommittedSessionDep,
        product_id: UUID,
        current_user: CurrentUser,
        redis: RedisDep,
):
    """
    Track product view stores view timestamp and maintains viewed products list
    """
    if not current_user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required"
        )
    user_view_key = f"user:{current_user.id}:views"
    product_viewers_key = f"product:{product_id}:viewers"
    try:
        product = ProductDAO(session).find_one_or_none_by_id(product_id)
        if not product:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Product not found"
            )
        redis.zadd(user_view_key, {str(product_id): time.time()}, nx=True) # only unique keys

        redis.sadd(product_viewers_key, str(current_user.id))
        # TTL = 2 hours
        redis.expire(user_view_key, 7200)
        redis.expire(product_viewers_key, 7200)

        return {
            "message": "View tracked successfully",
            "product_id": str(product_id),
            "timestamp": datetime.now(timezone.utc).isoformat()
        }

    except Exception as e:
        logger.error(f"View tracking failed: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to track view"
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
    existing = UserProductInteractionDAO(session).find_one_or_none({
        "user_id": current_user.id,
        "product_id": product.id,
        "interaction_type": InteractionType.FAVORITE
    })
    if existing:
        return {"message": "Product already in favorites"}
    UserProductInteractionDAO(session).add(UserProductInteractionCreate(
        user_id=current_user.id,
        product_id=product.id,
        interaction_type=InteractionType.FAVORITE,
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
    """Remove product from cart"""
    if not current_user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required"
        )

    deleted_count = CartItemDAO(session).delete(filters={
        "user_id": current_user.id,
        "product_id": product_id
    })
    UserProductInteractionDAO(session).delete(filters={
        "user_id": current_user.id,
        "interaction_type": InteractionType.CART_ADD,
        "product_id": product_id})
    if not deleted_count:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Product not found in cart"
        )

    return {"message": "Product removed from cart"}