from typing import  Any
from uuid import UUID
from fastapi import APIRouter, HTTPException


from app.api.deps import CurrentUser, CommittedSessionDep, UncommittedSessionDep
from app.core.postgres.dao import ProductDAO, UserProductInteractionDAO
from app.schemas.core_schemas import ProductPublic, ProductCreate, ProductUpdate, Message

router = APIRouter(prefix="/product", tags=["products"])


@router.get("/", response_model=list[ProductPublic])
def read_products(
        session: UncommittedSessionDep,
        current_user: CurrentUser,
        skip: int = 0,
        limit: int = 100
) -> Any:
    """Retrieve products with optional filtering by category."""
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="No access to this method")
    return ProductDAO(session).find_all(skip, limit)


@router.get("/{product_id}", response_model=ProductPublic)
def read_product(
        session: UncommittedSessionDep,
        current_user: CurrentUser,
        product_id: UUID
) -> Any:
    """Get product by ID."""
    product = ProductDAO(session).find_one_or_none_by_id(product_id)
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")

    if current_user.role != "admin":
        interactions = UserProductInteractionDAO(session).find_all(filters=
            {
                "user_id": current_user.id,
                "product_id": product_id
        })
        if not interactions:
            raise HTTPException(status_code=403, detail="No access to this product")
    return product


@router.post("/", response_model=ProductPublic, status_code=201)
def create_product(
        session: CommittedSessionDep,
        current_user: CurrentUser,
        product_in: ProductCreate
) -> Any:
    """Create new product (admin only)."""
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")
    if ProductDAO(session).find_one_or_none_by_id(product_in.id):
        raise HTTPException(status_code=409, detail=f"Shaver {product_in.title} already exists ")

    return ProductDAO(session).add(product_in)


@router.put("/{product_id}", response_model=ProductPublic)
def update_product(
        session: CommittedSessionDep,
        current_user: CurrentUser,
        product_id: UUID,
        product_in: ProductUpdate,
) -> Any:
    """Update product details (Admin only)"""
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")

    product_dao = ProductDAO(session)
    product = product_dao.find_one_or_none_by_id(product_id)
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")

    return product_dao.update({"id": product_id}, product_in)


@router.delete("/{product_id}", response_model=Message)
def delete_product(
        session: CommittedSessionDep,
        current_user: CurrentUser,
        product_id: UUID,
) -> Any:
    """
    Delete product (admin only).
    """
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")

    product = ProductDAO(session).find_one_or_none_by_id(product_id)
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    ProductDAO(session).delete({"id": product.id})
    return Message(message="Product deleted successfully")


