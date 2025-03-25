from typing import Any

from fastapi import APIRouter, HTTPException
from sqlmodel import select

from app.api.deps import CurrentUser, SessionDep
from app.core.mongo_db import products_collection
from app.models import Item, Message, ProductCreate, ProductPublic, ProductUpdate

router = APIRouter(prefix="/products", tags=["products"])


@router.get("/", response_model=list[ProductPublic])
def read_products(current_user: CurrentUser, skip: int = 0, limit: int = 100) -> Any:
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
def read_product(current_user: CurrentUser, product_id: str) -> Any:
    """
    Fetch product by id.
    """
    product = products_collection.find_one({"_id": product_id})
    if product is None:
        raise HTTPException(status_code=404, detail="Product not found")
    product["id"] = str(product["_id"])
    return ProductPublic(**product)


@router.post("/", response_model=ProductPublic, status_code=201)
def create_product(current_user: CurrentUser, product_in: ProductCreate) -> Any:
    """
    Create new product.
    """
    product_dict = product_in.model_dump()
    result = products_collection.insert_one(product_dict)
    product_dict["id"] = str(result.inserted_id)
    return ProductPublic(**product_dict)


@router.put("/{id}", response_model=ProductPublic)
def update_product(
    current_user: CurrentUser,
    product_id: str,
    product_in: ProductUpdate,
) -> ProductPublic:
    """
    Update a product.
    """
    product = products_collection.find_one({"_id": product_id})
    if product is None:
        raise HTTPException(status_code=404, detail="Product not found")
    update_data = product_in.model_dump(exclude_unset=True)
    products_collection.update_one({"_id": product_id}, {"$set": update_data})
    updated_product = products_collection.find_one({"_id": product_id})
    if updated_product is None:
        raise HTTPException(status_code=404, detail="Product not found")
    updated_product["id"] = str(updated_product["_id"])
    return ProductPublic(**updated_product)


@router.delete("/{id}")
def delete_product(current_user: CurrentUser, product_id: str) -> Message:
    """
    Delete a product.
    """
    product = products_collection.find_one({"_id": product_id})
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    products_collection.delete_one({"_id": product_id})
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
    purchased_items = session.exec(
        select(Item).where(Item.owner_id == current_user.id)
    ).all()

    if not purchased_items:
        raise HTTPException(status_code=404, detail="No recommendations available")

    purchased_categories = {item.category for item in purchased_items}
    recommended_products = list(products_collection.find(
        {"category": {"$in": list(purchased_categories)}},
        limit=limit
    ).sort("rating", -1))

    if not recommended_products:
        raise HTTPException(status_code=404, detail="Out of stock")

    try:
        # Convert MongoDB _id to str and validate
        return [
            ProductPublic(
                id=str(product["_id"]),
                title=product["title"],
                description=product.get("description"),
                category=product["category"],
                price=product["price"],
                rating=product["rating"],
            )
            for product in recommended_products
        ]
    except Exception as e:
        print(f"Validation failed: {e}")
        raise HTTPException(status_code=500, detail="Invalid product data")
