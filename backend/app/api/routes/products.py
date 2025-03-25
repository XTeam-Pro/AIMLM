from typing import Any, List
from uuid import UUID
from fastapi import APIRouter, HTTPException
from sqlmodel import select

from app.base_models import (
    Product,
    ProductCreate,
    ProductPublic,
    Item,
    Message,
    ProductUpdate
)
from app.api.deps import CurrentUser, SessionDep

router = APIRouter(prefix="/products", tags=["products"])


@router.get("/", response_model=List[ProductPublic])
def read_products(
        session: SessionDep,
        current_user: CurrentUser,
        skip: int = 0,
        limit: int = 100,
) -> Any:
    """
    Retrieve products with optional filtering by category.
    """
    query = select(Product)

    if not current_user.is_superuser:
        query = query.join(Item).where(Item.user_id == current_user.id)

    products = session.exec(query.offset(skip).limit(limit)).all()
    return products


@router.get("/{product_id}", response_model=ProductPublic)
def read_product(
        session: SessionDep,
        current_user: CurrentUser,
        product_id: UUID
) -> Any:
    """
    Get product by ID.
    """
    product = session.get(Product, product_id)
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")

    # Check access for non-admin users
    if not current_user.is_superuser:
        item = session.exec(
            select(Item)
            .where(Item.product_id == product_id)
            .where(Item.user_id == current_user.id)
        ).first()
        if not item:
            raise HTTPException(status_code=403, detail="No access to this product")

    return product


@router.post("/", response_model=ProductPublic, status_code=201)
def create_product(
        session: SessionDep,
        current_user: CurrentUser,
        product_in: ProductCreate
) -> Any:
    """
    Create new product (admin only).
    """
    if not current_user.is_superuser:
        raise HTTPException(status_code=403, detail="Not authorized")

    product = Product.model_validate(product_in)
    session.add(product)
    session.commit()
    session.refresh(product)
    return product


@router.put("/{product_id}", response_model=ProductPublic)
def update_product(
        session: SessionDep,
        current_user: CurrentUser,
        product_id: UUID,
        product_in: ProductUpdate,
) -> ProductPublic:
    """Update product details (Admin only)"""
    if not current_user.is_superuser:
        raise HTTPException(status_code=403, detail="Admin access required")

    if not (product := session.get(Product, product_id)):
        raise HTTPException(status_code=404, detail="Product not found")

    product.sqlmodel_update(product_in.model_dump(exclude_unset=True))

    session.add(product)
    session.commit()
    session.refresh(product)
    return product

@router.delete("/{product_id}", response_model=Message)
def delete_product(
        session: SessionDep,
        current_user: CurrentUser,
        product_id: UUID,
) -> Any:
    """
    Delete product (admin only).
    """
    if not current_user.is_superuser:
        raise HTTPException(status_code=403, detail="Not authorized")

    product = session.get(Product, product_id)
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")

    session.delete(product)
    session.commit()
    return Message(message="Product deleted successfully")


@router.get("/recommendations/{limit}", response_model=List[ProductPublic])
def get_recommendations(
        session: SessionDep,
        current_user: CurrentUser,
        limit: int = 5
) -> Any:
    """
    Get personalized product recommendations based on user's purchase history.
    """

    users_items = session.exec(
        select(Item)
        .where(Item.user_id == current_user.id)
    ).all()

    if not users_items:

        products = session.exec(
            select(Product)
            .order_by(Product.popularity.desc())
            .limit(limit)
        ).all()
        return products

    purchased_categories = {item.category for item in users_items if item.category}

    recommended_products = session.exec(
        select(Product)
        .where(Product.category.in_(purchased_categories))
        .order_by(Product.rating.desc())
        .limit(limit)
    ).all()

    return recommended_products