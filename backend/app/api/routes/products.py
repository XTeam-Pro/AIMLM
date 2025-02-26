from fastapi import APIRouter, HTTPException, Depends
from typing import List
from pydantic import BaseModel

from app.models import ProductBase, ProductCreate

# Создание маршрутизатора
router = APIRouter(prefix="/products", tags=["products"])


@router.get("/", response_model=List[ProductBase])
async def get_products():
    """Получить список всех продуктов"""
    return fake_product_db


@router.get("/{product_id}", response_model=ProductBase)
async def get_product(product_id: int):
    """Получить продукт по ID"""
    for product in fake_product_db:
        if product["id"] == product_id:
            return product
    raise HTTPException(status_code=404, detail="Продукт не найден")


@router.post("/", response_model=ProductBase)
async def create_product(product: ProductCreate):
    """Добавить новый продукт"""
    new_id = len(fake_product_db) + 1
    new_product = product.dict()
    new_product["id"] = new_id
    fake_product_db.append(new_product)
    return new_product


@router.put("/{product_id}", response_model=ProductBase)
async def update_product(product_id: int, updated_product: ProductCreate):
    """Обновить информацию о продукте по ID"""
    for product in fake_product_db:
        if product["id"] == product_id:
            product.update(updated_product.dict())
            return product
    raise HTTPException(status_code=404, detail="Продукт не найден")


@router.delete("/{product_id}")
async def delete_product(product_id: int):
    """Удалить продукт по ID"""
    for product in fake_product_db:
        if product["id"] == product_id:
            fake_product_db.remove(product)
            return {"detail": "Продукт успешно удален"}
    raise HTTPException(status_code=404, detail="Продукт не найден")