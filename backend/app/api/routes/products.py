from fastapi import APIRouter, HTTPException
from typing import List
from sqlmodel import select
from starlette.responses import JSONResponse

from app.core.mongo_db import products_collection
from app.models import Item, ProductCreate, ProductPublic, ProductUpdate
from app.api.deps import SessionDep, CurrentUser

router = APIRouter(prefix="/products", tags=["products"])


@router.post("/", response_model=ProductPublic, status_code=201)
def create_product(product: ProductCreate) -> ProductPublic:
    """
    Create a new product in the database.
    """
    product_dict = product.model_dump()
    result = products_collection.insert_one(product_dict)
    product_dict["id"] = str(result.inserted_id)
    return ProductPublic(**product_dict)


@router.get("/read_all", response_model=List[ProductPublic])
def get_all_products() -> List[ProductPublic] | HTTPException:
    """
    Retrieve all products from the database.
    """
    products_cursor = products_collection.find()
    products_list = list(products_cursor)

    if not products_list:
        raise HTTPException(status_code=404, detail="There are no products")

    for product in products_list:
        product["id"] = str(product["_id"])

    return [ProductPublic(**product) for product in products_list]


@router.get("/read/{product_id}", response_model=ProductPublic)
def get_product(product_id: str) -> ProductPublic | HTTPException:
    """
    Retrieve a single product by its ID.
    """
    product = products_collection.find_one({"_id": product_id})
    if product:
        product["id"] = str(product["_id"])
        return ProductPublic(**product)
    raise HTTPException(status_code=404, detail="Product not found")


@router.put("/update/{product_id}", response_model=ProductPublic)
def update_product(product_id: str, product: ProductUpdate) -> ProductPublic | HTTPException:
    """
    Update a product by its ID.
    """
    update_data = {k: v for k, v in product.model_dump().items() if v is not None}
    if update_data:
        products_collection.update_one({"_id": product_id}, {"$set": update_data})
    updated_product = products_collection.find_one({"_id": product_id})
    if updated_product:
        updated_product["id"] = str(updated_product["_id"])
        return ProductPublic(**updated_product)
    raise HTTPException(status_code=404, detail="Product not found")


@router.delete("/delete/{product_id}", status_code=204)
def delete_product(product_id: str) -> HTTPException | JSONResponse:
    """
    Delete a product by its ID.
    """
    result = products_collection.delete_one({"_id": product_id})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Product not found")
    return JSONResponse(status_code=200, content=f"Product with id {product_id} successfully deleted")


@router.get("/recommendations/{limit}", response_model=List[ProductPublic])
def get_recommendations(
        limit: int,
        user: CurrentUser,
        session: SessionDep,
) -> List[ProductPublic] | HTTPException:
    """
    Returns a list of recommended products depending on items picked up by a user.
    """
    purchased_items = session.exec(select(Item).where(Item.owner_id == user.id)).all()
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