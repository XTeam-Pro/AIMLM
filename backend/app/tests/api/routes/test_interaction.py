import uuid
from fastapi.testclient import TestClient
from sqlmodel import Session
from app.core.postgres.config import settings
from app.models.core import User, Product, UserProductInteraction, CartItem
from app.core.security import get_password_hash


def create_test_user(db: Session, email: str = "test@example.com") -> User:
    user = User(
        email=email,
        hashed_password=get_password_hash("testpass123"),
        full_name="Test User",
        username="testuser",
        phone="+1234567890",
        address="123 Test St, Test City",
        postcode="12345",
        role="client",
        status="active"
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def create_test_product(db: Session) -> Product:
    product = Product(
        name="Test Product",
        description="Test Description",
        price=10.99,
        stock_quantity=100
    )
    db.add(product)
    db.commit()
    db.refresh(product)
    return product


def test_get_bought_products(
        client: TestClient,
        normal_user_token_headers: dict,
        db: Session
):
    # Создаем тестовые данные
    user = create_test_user(db)
    product = create_test_product(db)

    interaction = UserProductInteraction(
        user_id=user.id,
        product_id=product.id,
        interaction_type="PURCHASE"
    )
    db.add(interaction)
    db.commit()

    response = client.get(
        f"{settings.API_V1_STR}/interaction/get_bought",
        headers=normal_user_token_headers
    )
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["product_id"] == str(product.id)


def test_track_product_view(
        client: TestClient,
        normal_user_token_headers: dict,
        db: Session
):
    product = create_test_product(db)

    response = client.post(
        f"{settings.API_V1_STR}/interaction/track_view",
        headers=normal_user_token_headers,
        json={"product_id": str(product.id)}
    )
    assert response.status_code == 201
    assert response.json()["message"] == "View tracked successfully"


def test_track_product_view_not_found(
        client: TestClient,
        normal_user_token_headers: dict
):
    response = client.post(
        f"{settings.API_V1_STR}/interaction/track_view",
        headers=normal_user_token_headers,
        json={"product_id": str(uuid.uuid4())}
    )
    assert response.status_code == 404
    assert response.json()["detail"] == "Product not found"


def test_add_to_cart(
        client: TestClient,
        normal_user_token_headers: dict,
        db: Session
):
    product = create_test_product(db)

    response = client.post(
        f"{settings.API_V1_STR}/interaction/add_to_cart",
        headers=normal_user_token_headers,
        json={"product_id": str(product.id), "quantity": 2}
    )
    assert response.status_code == 201
    assert response.json()["message"] == "Product added to cart"


def test_add_to_cart_product_not_found(
        client: TestClient,
        normal_user_token_headers: dict
):
    response = client.post(
        f"{settings.API_V1_STR}/interaction/add_to_cart",
        headers=normal_user_token_headers,
        json={"product_id": str(uuid.uuid4())}
    )
    assert response.status_code == 404
    assert response.json()["detail"] == "Product not available"


def test_add_to_favorites(
        client: TestClient,
        normal_user_token_headers: dict,
        db: Session
):
    product = create_test_product(db)

    response = client.post(
        f"{settings.API_V1_STR}/interaction/add_to_favorites",
        headers=normal_user_token_headers,
        json={"product_id": str(product.id)}
    )
    assert response.status_code == 201
    assert response.json()["message"] == "Product added to favorites"


def test_add_to_favorites_already_exists(
        client: TestClient,
        normal_user_token_headers: dict,
        db: Session
):
    user = create_test_user(db)
    product = create_test_product(db)

    interaction = UserProductInteraction(
        user_id=user.id,
        product_id=product.id,
        interaction_type="FAVORITE"
    )
    db.add(interaction)
    db.commit()

    response = client.post(
        f"{settings.API_V1_STR}/interaction/add_to_favorites",
        headers=normal_user_token_headers,
        json={"product_id": str(product.id)}
    )
    assert response.status_code == 200
    assert response.json()["message"] == "Product already in favorites"


def test_remove_from_favorites(
        client: TestClient,
        normal_user_token_headers: dict,
        db: Session
):
    user = create_test_user(db)
    product = create_test_product(db)

    interaction = UserProductInteraction(
        user_id=user.id,
        product_id=product.id,
        interaction_type="FAVORITE"
    )
    db.add(interaction)
    db.commit()

    response = client.delete(
        f"{settings.API_V1_STR}/interaction/remove_from_favorites/{product.id}",
        headers=normal_user_token_headers
    )
    assert response.status_code == 200
    assert response.json()["message"] == "Product removed from favorites"


def test_remove_from_favorites_not_found(
        client: TestClient,
        normal_user_token_headers: dict
):
    response = client.delete(
        f"{settings.API_V1_STR}/interaction/remove_from_favorites/{str(uuid.uuid4())}",
        headers=normal_user_token_headers
    )
    assert response.status_code == 404
    assert response.json()["detail"] == "Product not found in favorites"


def test_get_favorites(
        client: TestClient,
        normal_user_token_headers: dict,
        db: Session
):
    user = create_test_user(db)
    product = create_test_product(db)

    interaction = UserProductInteraction(
        user_id=user.id,
        product_id=product.id,
        interaction_type="FAVORITE"
    )
    db.add(interaction)
    db.commit()

    response = client.get(
        f"{settings.API_V1_STR}/interaction/get_favorites",
        headers=normal_user_token_headers
    )
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["id"] == str(product.id)


def test_get_my_cart(
        client: TestClient,
        normal_user_token_headers: dict,
        db: Session
):
    user = create_test_user(db)
    product = create_test_product(db)

    cart_item = CartItem(
        user_id=user.id,
        product_id=product.id,
        quantity=1
    )
    db.add(cart_item)
    db.commit()

    response = client.get(
        f"{settings.API_V1_STR}/interaction/get_my_cart",
        headers=normal_user_token_headers
    )
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["product_id"] == str(product.id)