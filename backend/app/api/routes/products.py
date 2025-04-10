from typing import  Any
from uuid import UUID
from fastapi import APIRouter, HTTPException
from pydantic import HttpUrl, BaseModel
from starlette import status

from app.api.dependencies.deps import CurrentUser, CommittedSessionDep, UncommittedSessionDep
from app.core.postgres.dao import ProductDAO, UserProductInteractionDAO
from app.schemas.common import ProductPublic, ProductCreate, ProductUpdate, Message

router = APIRouter(prefix="/product", tags=["products"])


@router.get("/categories")
def get_all_categories(
        session: UncommittedSessionDep,
        current_user: CurrentUser,
        skip: int = 0,
        limit: int = 100
) -> list[str]:
    """
    Returns a list of unique product categories.
    """
    if current_user.role != "admin":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="No access to this method")
    products = ProductDAO(session).find_all(skip, limit)
    return list({product.category for product in products})


@router.get("/", response_model=list[ProductPublic])
def read_products(
        session: UncommittedSessionDep,
        current_user: CurrentUser,
        skip: int = 0,
        limit: int = 100
) -> Any:
    """Retrieve products with optional filtering by category."""
    if current_user.role != "admin":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="No access to this method")
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
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Product not found")

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
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Admin access required")
    if ProductDAO(session).find_one_or_none({"title": product_in.title}):
        raise HTTPException(status_code=409, detail=f"{product_in.title} already exists ")

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
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Admin access required")

    product_dao = ProductDAO(session)
    product = product_dao.find_one_or_none_by_id(product_id)
    if not product:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Product not found")

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
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Admin access required")

    product = ProductDAO(session).find_one_or_none_by_id(product_id)
    if not product:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Product not found")
    ProductDAO(session).delete({"id": product.id})
    return Message(message="Product deleted successfully")

class WebinarCreate(BaseModel):
    webinar_link: HttpUrl

@router.post("/{product_id}/webinar", response_model=ProductPublic, status_code=201)
def create_product_webinar(
        session: CommittedSessionDep,
        current_user: CurrentUser,
        product_id: UUID,
        webinar_in: WebinarCreate,
        is_validated: bool = False
) -> Any:
    """
    Create a webinar for a product.
    Webinar creation is allowed for mentors or validated distributors.
    """
    # Check if the current user is allowed to create webinars.
    if current_user.role == "mentor":
        allowed = True
    elif current_user.role == "distributor" and is_validated:
        allowed = True
    else:
        allowed = False

    if not allowed:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only mentors or validated distributors can create webinars"
        )
    product_dao = ProductDAO(session)
    product = product_dao.find_one_or_none_by_id(product_id)
    if not product:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Product not found")

    update_data = {"webinar_link": webinar_in.webinar_link}
    updated_product = product_dao.update({"id": product_id}, update_data)
    return updated_product


