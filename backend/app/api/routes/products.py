from typing import List, Optional
from uuid import UUID
from fastapi import APIRouter, HTTPException
from sqlalchemy import in_
from sqlmodel import select, desc
from sqlalchemy.sql.expression import Select

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
) -> List[ProductPublic]:
    """
    Retrieve products with optional filtering by category.
    """
    query: Select = select(Product)

    if not current_user.is_superuser:
        query = query.join(Item).where(Item.user_id == current_user.id)

    products = session.exec(query.offset(skip).limit(limit)).all()
    return products


@router.get("/{product_id}", response_model=ProductPublic)
def read_product(
        session: SessionDep,
        current_user: CurrentUser,
        product_id: UUID
) -> ProductPublic:
    """
    Get product by ID.
    """
    product: Optional[ProductPublic] = session.get(Product, product_id)
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")

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
) -> ProductPublic:
    """
    Create new product (admin only).
    """
    if not current_user.is_superuser:
        raise HTTPException(status_code=403, detail="Not authorized")

    product = ProductPublic.model_validate(product_in)
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

    product: Optional[ProductPublic] = session.get(Product, product_id)
    if not product:
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
) -> Message:
    """
    Delete product (admin only).
    """
    if not current_user.is_superuser:
        raise HTTPException(status_code=403, detail="Not authorized")

    product: Optional[Product] = session.get(Product, product_id)
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")

    session.delete(product)
    session.commit()
    return Message(message="Product deleted successfully")


@router.get("/recommendations/{limit}", response_model=list[ProductPublic])
def get_recommendations(
        session: SessionDep,
        current_user: CurrentUser,
        limit: int = 5
) -> list[ProductPublic]:
    """
    Get personalized product recommendations based on user's purchase history.
    """
    users_items: list[Item] = session.exec(
        select(Item)
        .where(Item.user_id == current_user.id)
    ).all()

    if not users_items:
        products: list[ProductPublic] = session.exec(
            select(Product)
            .order_by(desc(Product.popularity))
            .limit(limit)
        ).all()
        return products

    purchased_categories: set[str] = {
        item.category for item in users_items if item.category
    }

    if not purchased_categories:
        return []

    recommended_products: list[ProductPublic] = session.exec(
        select(Product)
        .where(in_(Product.category, purchased_categories))
        .order_by(desc(Product.popularity))
        .limit(limit)
    ).all()

    return recommended_products