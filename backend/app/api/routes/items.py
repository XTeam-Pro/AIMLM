import uuid
from typing import Any, Optional

from fastapi import APIRouter, HTTPException
from sqlmodel import func, select

from app.api.deps import CurrentUser, SessionDep
from app.base_models import (
    Item,
    ItemCreate,
    ItemPublic,
    ItemsPublic,
    ItemUpdate,
    Message,
    Product,
    User
)

router = APIRouter(prefix="/items", tags=["items"])


@router.get("/", response_model=ItemsPublic)
def read_items(
        session: SessionDep,
        current_user: CurrentUser,
        skip: int = 0,
        limit: int = 100
) -> Any:
    """
    Retrieve user's items with optional filtering.
    """
    query = select(Item).where(Item.user_id == current_user.id)

    count_query = select(func.count()).select_from(query.subquery())
    total = session.exec(count_query).one()

    items = session.exec(query.offset(skip).limit(limit)).all()

    return ItemsPublic(data=items, count=total)


@router.get("/{item_id}", response_model=ItemPublic)
def read_item(
        session: SessionDep,
        current_user: CurrentUser,
        item_id: uuid.UUID
) -> Any:
    """
    Get specific item by ID.
    """
    item = session.get(Item, item_id)
    if not item:
        raise HTTPException(status_code=404, detail="Item not found")

    if not current_user.is_superuser and item.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not enough permissions")

    return item


@router.post("/", response_model=ItemPublic)
def create_item(
    *,
    session: SessionDep,
    current_user: CurrentUser,
    item_in: ItemCreate
) -> Any:
    """
    Create a new item interaction.
    """
    product = session.get(Product, item_in.product_id)
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    item_data = item_in.model_dump(exclude={"category"})
    item = Item(
        **item_data,
        user_id=current_user.id,
        category=product.category,  # Set category from product
    )
    session.add(item)
    session.commit()
    session.refresh(item)

    # Update product popularity
    product.popularity += 1
    session.add(product)
    session.commit()
    return item

@router.put("/{item_id}", response_model=ItemPublic)
def update_item(
        *,
        session: SessionDep,
        current_user: CurrentUser,
        item_id: uuid.UUID,
        item_in: ItemUpdate
) -> Any:
    """
    Update item interaction.
    """
    item = session.get(Item, item_id)
    if not item:
        raise HTTPException(status_code=404, detail="Item not found")

    if not current_user.is_superuser and item.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not enough permissions")

    update_data = item_in.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(item, field, value)

    session.add(item)
    session.commit()
    session.refresh(item)

    return item


@router.delete("/{item_id}", response_model=Message)
def delete_item(
        session: SessionDep,
        current_user: CurrentUser,
        item_id: uuid.UUID
) -> Message:
    """
    Delete item interaction.
    """
    item = session.get(Item, item_id)
    if not item:
        raise HTTPException(status_code=404, detail="Item not found")

    if not current_user.is_superuser and item.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not enough permissions")

    session.delete(item)
    session.commit()

    return Message(message="Item deleted successfully")


@router.get("/product/{product_id}", response_model=ItemPublic)
def get_item_for_product(
        session: SessionDep,
        current_user: CurrentUser,
        product_id: uuid.UUID,
        interaction_type: str
) -> Any:
    """
    Get user's specific interaction with a product.
    """
    item = session.exec(
        select(Item)
        .where(Item.product_id == product_id)
        .where(Item.user_id == current_user.id)
        .where(Item.interaction_type == interaction_type)
    ).first()

    if not item:
        raise HTTPException(
            status_code=404,
            detail=f"No {interaction_type} interaction found for this product"
        )

    return item
