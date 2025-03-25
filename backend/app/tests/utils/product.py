import uuid
from sqlmodel import Session
from app.base_models import Product
from random import randint, choice


def create_random_product(db: Session, **kwargs) -> Product:
    """
    Create and return a random Product for testing.
    """
    categories = ["Electronics", "Clothing", "Books", "Home", "Sports"]
    product_data = {
        "title": f"Product-{uuid.uuid4().hex[:6]}",
        "description": f"Description for product",
        "category": choice(categories),
        "price": randint(10, 1000),
        "rating": randint(1, 5),
        "popularity": 0.0,
        **kwargs
    }

    product = Product(**product_data)
    db.add(product)
    db.commit()
    db.refresh(product)
    return product