from fastapi import APIRouter, HTTPException, Depends
from typing import List
from pydantic import BaseModel
from sqlmodel import Session, select

from app.models import ProductBase, ProductCreate, Product
from app.api.deps import SessionDep

# Создание маршрутизатора
router = APIRouter(prefix="/products", tags=["products"])


@router.get("/", response_model=List[ProductBase])
async def get_products(session: SessionDep):
    """Получить список всех продуктов"""
    statement = select(Product)
    products = session.exec(statement).all()
    return products


@router.get("/{product_id}", response_model=ProductBase)
async def get_product(product_id: int, session: SessionDep):
    """Получить продукт по ID"""
    product = session.get(Product, product_id)
    if product:
        return product
    raise HTTPException(status_code=404, detail="Продукт не найден")


@router.post("/", response_model=ProductBase)
async def create_product(product: ProductCreate, session: SessionDep):
    """Добавить новый продукт"""
    new_product = Product.from_orm(product)
    session.add(new_product)
    session.commit()
    session.refresh(new_product)
    return new_product


@router.put("/{product_id}", response_model=ProductBase)
async def update_product(product_id: int, updated_product: ProductCreate, session: SessionDep):
    """Обновить информацию о продукте по ID"""
    product = session.get(Product, product_id)
    if not product:
        raise HTTPException(status_code=404, detail="Продукт не найден")
    updated_data = updated_product.dict(exclude_unset=True)
    for key, value in updated_data.items():
        setattr(product, key, value)
    session.add(product)
    session.commit()
    session.refresh(product)
    return product


@router.delete("/{product_id}")
async def delete_product(product_id: int, session: SessionDep):
    """Удалить продукт по ID"""
    product = session.get(Product, product_id)
    if product:
        session.delete(product)
        session.commit()
        return {"detail": "Продукт успешно удален"}
    raise HTTPException(status_code=404, detail="Продукт не найден")
