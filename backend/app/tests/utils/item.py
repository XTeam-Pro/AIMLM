import uuid
from datetime import datetime, timezone
from random import choice, randint
from sqlmodel import Session
from app.base_models import Item
from app.tests.utils.user import create_random_user
from app.tests.utils.product import create_random_product


def create_random_item(
        db: Session,
        user_id: uuid.UUID | None = None,
        product_id: uuid.UUID | None = None,
        **kwargs
) -> Item:
    """
    Create and return a random Item for testing.

    Args:
        db: SQLModel Session
        user_id: Optional user ID (will create random user if not provided)
        product_id: Optional product ID (will create random product if not provided)
        **kwargs: Override any Item attributes

    Returns:
        Item: The created Item instance
    """
    # Create user if not provided
    if user_id is None:
        user = create_random_user(db)
        user_id = user.id

    # Create product if not provided
    if product_id is None:
        product = create_random_product(db)
        product_id = product.id

    # Generate random item data
    interaction_types = ["PURCHASE", "CART", "FAVORITE", "VIEW"]
    item_data = {
        "interaction_type": kwargs.get("interaction_type", choice(interaction_types)),
        "quantity": kwargs.get("quantity", randint(1, 10)),
        "user_id": user_id,
        "product_id": product_id,
        **kwargs
    }

    # Create and commit the item
    item = Item(**item_data)
    db.add(item)
    db.commit()
    db.refresh(item)
    return item