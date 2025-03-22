from typing import Any

from fastapi import APIRouter, HTTPException
from sqlmodel import select

from app.api.deps import CurrentUser, SessionDep
from app.core.mongo_db import products_collection
from app.models import ProductCreate, ProductPublic, ProductUpdate, Message, Item

router = APIRouter(prefix="/products", tags=["products"])


@router.get("/", response_model=ProductPublic)
def read_products(
        skip: int = 0, limit: int = 100
) -> Any:
    """
    Retrieve products.
    """
    products_cursor = products_collection.find().skip(skip).limit(limit)
    products_list = list(products_cursor)

    if not products_list:
        raise HTTPException(status_code=404, detail="No products found")

    for product in products_list:
        product["id"] = str(product["_id"])

    return [ProductPublic(**product) for product in products_list]


@router.get("/{id}", response_model=ProductPublic)
def read_product(
        product_id: str
) -> Any:
    """
    Fetch product by id
    """
    product = products_collection.find_one({"_id": str(product_id)})
    if product is None:
        raise HTTPException(status_code=404, detail="Product not found")
    product["id"] = str(product["_id"])
    return ProductPublic(**product)


@router.post("/", response_model=ProductPublic, status_code=201)
def create_product(
        *, product_in: ProductCreate
) -> Any:
    """
    Create new product.
    """
    product_dict = product_in.model_dump()
    result = products_collection.insert_one(product_dict)
    product_dict["id"] = str(result.inserted_id)
    return ProductPublic(**product_dict)


@router.put("/{id}", response_model=ProductPublic)
def update_product(
        *,
        product_id: str,
        product_in: ProductUpdate,
) -> ProductPublic:
    """
    Update a product
    """
    product = products_collection.find_one({"_id": str(product_id)})
    if product is None:
        raise HTTPException(status_code=404, detail="Product not found")
    update_data = product_in.model_dump(exclude_unset=True)
    products_collection.update_one({"_id": str(product_id)}, {"$set": update_data})
    updated_product = products_collection.find_one({"_id": str(product_id)})
    if updated_product is None:
        raise HTTPException(status_code=404, detail="Product not found")
    updated_product["id"] = str(updated_product["_id"])
    return ProductPublic(**updated_product)


@router.delete("/{id}")
def delete_product(
        product_id: str
) -> Message:
    """
    Delete a product.
    """
    product = products_collection.find_one({"_id": str(product_id)})
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    products_collection.delete_one({"_id": str(product_id)})
    return Message(message="Product deleted successfully")


@router.get("/recommendations/{limit}", response_model=list[ProductPublic])
def get_recommendations(
        limit: int,
        current_user: CurrentUser,
        session: SessionDep,
) -> Any:
    """
    Returns a list of recommended products based on items purchased by the user.
    """
    purchased_items = session.exec(select(Item).where(Item.owner_id == current_user.id)).all()
    if not purchased_items:
        raise HTTPException(
            status_code=404,
            detail="You have no recommendations, start buying to get them!"
        )

    purchased_titles = {item.title for item in purchased_items}

    matching_products = products_collection.find(
        {"title": {"$in": list(purchased_titles)}}
    )
    unique_categories = {product["category"] for product in matching_products if "category" in product}

    if not unique_categories:
        raise HTTPException(
            status_code=404,
            detail="No categories found for matching products!"
        )

    recommended_products = products_collection.find(
        {"category": {"$in": list(unique_categories)}},
        limit=limit
    ).sort("rating", -1)

    formatted_products = []
    for product in recommended_products:
        product["id"] = str(product["_id"])
        del product["_id"]
        formatted_products.append(product)

    return [ProductPublic(**product) for product in formatted_products]
