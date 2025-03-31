import json

from typing import Any, Optional


from fastapi import APIRouter
from redis import RedisError, Redis
from sqlmodel import select

from app.api.deps import CurrentUser


router = APIRouter(tags=["Buyer"], prefix="/buyers")


def get_cache_key(prefix: str, user_id: str, recommendation_type: str, limit: int) -> str:
    """Generate a consistent cache key for recommendations.

    Args:
        prefix: The base prefix for the cache key (e.g., "recommendations")
        user_id: The user ID to personalize the cache key
        recommendation_type: Type of recommendation (BASIC or PERSONALIZED)
        limit: Number of recommendations requested

    Returns:
        A formatted cache key string
    """
    return f"{prefix}:{user_id}:{recommendation_type}:{limit}"


def cache_response(
        redis_client: Optional[Redis],
        key: str,
        value: Any,
        ex: int = 3600
) -> bool:
    """Cache a response in Redis with expiration.
    Args:
        redis_client: Redis client instance (optional)
        key: Cache key to use
        value: Value to cache (will be JSON serialized)
        ex: Expiration time in seconds

    Returns:
        bool: True if caching was successful, False otherwise
    """
    if not redis_client:
        return False

    try:
        serialized_value = json.dumps(value, default=str)  # default=str handles datetime serialization
        redis_client.set(key, serialized_value, ex=ex)
        return True
    except (RedisError, TypeError) as e:

        raise e

# @router.get("/recommendations/{limit}", response_model=list[ProductPublic])
# def get_recommendations(
#         session: SessionDep,
#         current_user: CurrentUser,
#         limit: int = 5
# ) -> Any:
#     """
#     Get personalized product recommendations based on user's purchase history.
#     """
#
#     users_items = session.exec(
#         select(Item)
#         .where(Item.user_id == current_user.id)
#     ).all()
#
#     if not users_items:
#
#         products = session.exec(
#             select(Product)
#             .order_by(Product.popularity.desc())
#             .limit(limit)
#         ).all()
#         return products
#
#     purchased_categories = {item.category for item in users_items if item.category}
#
#     recommended_products = session.exec(
#         select(Product)
#         .where(Product.category.in_(purchased_categories))
#         .order_by(Product.rating.desc())
#         .limit(limit)
#     ).all()
#
#     return recommended_products