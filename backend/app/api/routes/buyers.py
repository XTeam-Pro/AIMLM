import logging

from typing import Optional
from uuid import UUID

from fastapi import APIRouter, HTTPException

from starlette import status

from app.api.dependencies.buyer_deps import PurchaseServiceDep, SaleServiceDep
from app.api.dependencies.deps import CurrentUser, RedisDep, UncommittedSessionDep
from app.api.services.purchase_service import PurchaseResponse
from app.api.services.sale_service import SaleResponse
from app.core.postgres.dao import ProductDAO, UserProductInteractionDAO, TransactionDAO
from app.models.common import Product

from app.schemas.types.common_types import InteractionType, TransactionType

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
router = APIRouter(tags=["buyer"], prefix="/buyers")

@router.get("/products", response_model=list[Product])
def get_sorted_products(
    session: UncommittedSessionDep,
    current_user: CurrentUser,
    order_by: Optional[str] = None,
    skip: int = 0,
    limit: int = 100,
):
    """
    Get a sorted and filtered list of products with pagination.
    Parameters:
    - order_by: Field name to sort by (prefix with '-' for descending)
    - skip: Number of products to skip
    - limit: Maximum products to return
    """
    if not current_user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required"
        )

    try:
        products = ProductDAO(session).find_all(
            order_by=order_by,
            skip=skip,
            limit=limit
        )
        return products
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Failed to fetch products: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )

@router.post("/sell", status_code=status.HTTP_200_OK, response_model=SaleResponse)
def sell_product(
        product_id: UUID,
        buyer_id: UUID,
        current_user: CurrentUser,
        sale_service: SaleServiceDep
):
    """
    Processes the sale of a product
    """
    if not current_user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required"
        )
    try:
        return sale_service.process_sale(
            distributor_id=current_user.id,
            product_id=product_id,
            buyer_id=buyer_id
        )
    except HTTPException as he:
        return {"message": "HTTP Error", "status": he.status_code, "detail": str(he.detail)}
    except Exception as e:
        logger.error(f"Sale failed: {str(e)}", exc_info=True)
        raise HTTPException(
            status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )

@router.post("/purchase", status_code=status.HTTP_200_OK, response_model=PurchaseResponse)
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
            buyer_id=current_user.id,
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


@router.get("/recommendations/viewed", response_model=list[Product] | None)
def get_recommendations(
        session: UncommittedSessionDep,
        current_user: CurrentUser,
        redis: RedisDep,
        limit: int = 100
):
    """
    Get recommendations from same categories as viewed products
    Returns only products not previously viewed by user
    """
    if not current_user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required"
        )

    try:
        # Get user's viewed products and categories
        viewed_products = redis.zrange(f"user:{current_user.id}:views", 0, -1)
        if not viewed_products:
            return []

        # Decode bytes to strings and convert to UUIDs
        viewed_product_ids = [UUID(pid.decode('utf-8')) for pid in viewed_products]

        # Get the actual product objects
        viewed_products_objs = ProductDAO(session).find_all(filters={"id": ("in", viewed_product_ids)})
        viewed_categories = {p.category for p in viewed_products_objs if hasattr(p, 'category')}
        if not viewed_categories:
            return []

        # Get recommended products from same categories (excluding viewed)
        recs = []
        for category in viewed_categories:
            category_products = ProductDAO(session).find_all(
                filters={"category": category, "id": ("not_in", viewed_product_ids)},
                limit=limit * 2
            )
            recs.extend([p.id for p in category_products])

        # Remove duplicates and limit results
        unique_recs_ids = list(set(recs))
        return ProductDAO(session).find_all(filters={"id": ("in", unique_recs_ids)}, limit=limit)
    except HTTPException as he:
        return {"message": "HTTP Error", "status": he.status_code, "detail": str(he.detail)}
    except Exception as e:
        logger.error(f"Recommendation based on views failed: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to generate recommendations by views"
        )

@router.get("/recommendations/favorites", response_model=list[Product] | None, status_code=status.HTTP_200_OK)
async def get_recommendations_by_favorites(
        session: UncommittedSessionDep,
        current_user: CurrentUser,
        limit: int = 100
):
    """
    Get product recommendations based on user's favorites.
    Returns products from same categories as favorites, excluding already favorited items.
    """
    if not current_user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required"
        )
    try:
        favorites = UserProductInteractionDAO(session).find_all(filters={
            "user_id": current_user.id,
            "interaction_type": InteractionType.FAVORITE
        })
        if not favorites:
            return []
        favorite_product_ids = [fav.product_id for fav in favorites]
        favorite_products = ProductDAO(session).find_all(filters={"id": ("in", favorite_product_ids)})
        favorite_categories = {product.category for product in favorite_products if product.category}
        if not favorite_categories:
            return []
        recs = []
        for category in favorite_categories:
            category_products = ProductDAO(session).find_all(
                filters={
                    "category": category,
                    "id": ("not_in", favorite_product_ids)  # Exclude already favorited
                },
                limit=limit * 2  # Get extra to account for duplicates
            )
            recs.extend([product.id for product in category_products])
        unique_recs_ids = list(set(recs))
        return ProductDAO(session).find_all(filters={"id": ("in", unique_recs_ids)}, limit=limit)
    except HTTPException as he:
        return {"message": "HTTP Error", "status": he.status_code, "detail": str(he.detail)}
    except Exception as e:
        logger.error(f"Recommendation based on favorites failed: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to generate recommendations by favorites"
        )

@router.get("/recommendations/cart", response_model=list[Product] | None)
def get_recommendations_by_cart(
        session: UncommittedSessionDep,
        current_user: CurrentUser,
        limit: int = 100
):
    """
    Get product recommendations based on the user's cart contents.
    Returns products from the same categories as the products in the cart, excluding the products in the cart themselves.
    """
    if not current_user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required"
        )
    try:
        cart_items = UserProductInteractionDAO(session).find_all(filters={
            "user_id": current_user.id,
            "interaction_type": InteractionType.CART_ADD
        })
        cart_product_ids = [item.product_id for item in cart_items if item.product_id]
        if not cart_product_ids:
            return []
        # Get categories of cart products
        cart_products = ProductDAO(session).find_all(filters={"id": ("in", cart_product_ids)})
        cart_categories = {p.category for p in cart_products if p.category}
        if not cart_categories:
            return []
        recommendations = []
        for category in cart_categories:
            category_products = ProductDAO(session).find_all(
                filters={
                    "category": category,
                    "id": ("not_in", cart_product_ids),
                    "is_active": True
                },
                limit=limit * 2
            )
            recommendations.extend(category_products)
        # Remove duplicates and limit results
        seen_ids = set()
        unique_recommendations = [
            p for p in recommendations
            if not (p.id in seen_ids or seen_ids.add(p.id))
        ]
        return unique_recommendations[:limit]
    except HTTPException as he:
        return {"message": "HTTP Error", "status": he.status_code, "detail": str(he.detail)}
    except Exception as e:
        logger.error(f"Recommendation based on your cart failed: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to generate recommendations by cart content"
        )

@router.get("/recommendations/purchase")
def get_recommendations_by_purchase(
        session: UncommittedSessionDep,
        current_user: CurrentUser,
        limit: int = 100):
    """
    Get product recommendations based on the user's purchases.
    Returns products from the same categories as the products the user purchased,
    excluding the products themselves.
    """
    if not current_user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required"
        )
    try:
        purchased = TransactionDAO(session).find_all(filters={
            "user_id": current_user.id,
            "transaction_type": TransactionType.PRODUCT_PURCHASE
        })
        purchased_ids = [item.product_id for item in purchased if item.product_id]
        if not purchased_ids:
            return []
        products = ProductDAO(session).find_all(filters={"id": ("in", purchased_ids)})
        categories = {p.category for p in products if p.category}
        if not categories:
            return []
        # Get recommendations from same categories
        recommendations = []
        for category in categories:
            category_products = ProductDAO(session).find_all(
                filters={
                    "category": category,
                    "id": ("not_in", purchased_ids),
                    "is_active": True
                },
                limit=limit * 2
            )
            recommendations.extend(category_products)
        seen_ids = set()
        unique_recommendations = [
            p for p in recommendations
            if not (p.id in seen_ids or seen_ids.add(p.id))
        ]
        return unique_recommendations[:limit]
    except HTTPException as he:
        return {"message": "HTTP Error", "status": he.status_code, "detail": str(he.detail)}
    except Exception as e:
        logger.error(f"Recommendation based on your purchases: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to generate recommendations by purchases"
        )
