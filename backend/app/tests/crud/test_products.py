import pytest
from uuid import uuid4
from decimal import Decimal
from datetime import datetime
from app.core.postgres.dao import ProductDAO
from app.models.core import Product
from app.core.postgres.base import BaseDAO
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlmodel import SQLModel


# Test database setup
@pytest.fixture(scope="module")
def test_db():
    # Create a test SQLite database in memory
    engine = create_engine("sqlite:///:memory:")
    SQLModel.metadata.create_all(engine)
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    db = SessionLocal()
    yield db
    db.close()


@pytest.fixture
def product_dao(test_db):
    return ProductDAO(test_db)


# Test CRUD operations

# CREATE test
def test_create_product(product_dao):
    new_product = Product(
        title="Test Product",
        description="This is a test product.",
        category="cosmetics",
        price=Decimal("19.99"),
        pv_value=Decimal("10.00"),
        is_active=True,
    )
    created_product = product_dao.add(new_product)
    assert created_product.id is not None
    assert created_product.title == "Test Product"
    assert created_product.price == Decimal("19.99")


# READ test
def test_read_product(product_dao):
    # Step 1: Generate a UUID manually
    product_id = uuid4()

    # Step 2: Create a product with the UUID you just generated
    new_product = Product(
        id=product_id,  # Pass the UUID directly
        title="Sample Product",
        description="Description of sample product",
        category="test",
        price=Decimal("25.99"),
        pv_value=Decimal("10.00"),
        is_active=True,
    )

    # Step 3: Add the product to the DB
    created_product = product_dao.add(new_product)

    # Step 4: Fetch the product by its UUID
    product_fetched = product_dao.find_one_or_none_by_id(created_product.id)


# UPDATE test
def test_update_product(product_dao):
    # Create a product to update
    product = Product(
        title="Old Title",
        description="Old description.",
        category="cosmetics",
        price=Decimal("15.99"),
        pv_value=Decimal("5.00"),
        is_active=True,
    )
    created_product = product_dao.add(product)
    
    updated_product = product_dao.update({"id": created_product.id}, {"title": "Updated Title"})
    assert updated_product.title == "Updated Title"


# DELETE test
def test_delete_product(product_dao):
    # Create a product to delete
    product = Product(
        title="To Delete",
        description="This product will be deleted.",
        category="cosmetics",
        price=Decimal("10.00"),
        pv_value=Decimal("5.00"),
        is_active=True,
    )
    created_product = product_dao.add(product)
    
    # Delete the product
    deleted_count = product_dao.delete({"id": created_product.id})
    assert deleted_count == 1  # Ensure one product is deleted
    
    # Check the product no longer exists
    deleted_product = product_dao.find_one_or_none_by_id(created_product.id)
    assert deleted_product is None


if __name__ == "__main__":
    pytest.main()
