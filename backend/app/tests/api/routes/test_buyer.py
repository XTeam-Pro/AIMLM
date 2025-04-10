import uuid
from unittest.mock import Mock, patch

import pytest
from fastapi.testclient import TestClient
from fastapi import HTTPException, status
from sqlmodel import desc
from app.core.postgres.config import settings
from app.models.user import Product
from app.schemas.core_schemas import PurchaseResponse


def test_get_sorted_products_authenticated(client: TestClient, normal_user_token_headers: dict):
    mock_products = [Product(id=uuid.uuid4(), name="Test Product", category="Electronics")]

    with patch("app.core.postgres.dao.ProductDAO.find_all", return_value=mock_products) as mock_find:
        response = client.get(
            f"{settings.API_V1_STR}/buyers/products",
            headers=normal_user_token_headers
        )
        assert response.status_code == 200
        assert len(response.json()) == 1
        mock_find.assert_called_once()


def test_get_sorted_products_unauthenticated(client: TestClient):
    response = client.get(f"{settings.API_V1_STR}/buyers/products")
    assert response.status_code == status.HTTP_401_UNAUTHORIZED


def test_get_sorted_products_with_filters(client: TestClient, normal_user_token_headers: dict):
    with patch("app.core.postgres.dao.ProductDAO.find_all") as mock_find:
        client.get(
            f"{settings.API_V1_STR}/buyers/products?category=Electronics&order_by=-price",
            headers=normal_user_token_headers
        )
        mock_find.assert_called_once_with(
            filters={"category": "Electronics"},
            order_by=desc("price"),
            skip=0,
            limit=100
        )


# Тесты для /buyers/purchase
def test_buy_product_success(client: TestClient, normal_user_token_headers: dict):
    product_id = uuid.uuid4()
    mock_response = PurchaseResponse(success=True, message="Purchased")

    with patch("app.api.dependencies.PurchaseServiceDep.process_purchase", return_value=mock_response):
        response = client.post(
            f"{settings.API_V1_STR}/buyers/purchase",
            headers=normal_user_token_headers,
            json={"product_id": str(product_id)}
        )
        assert response.status_code == 201
        assert response.json()["success"] is True


def test_buy_product_unauthenticated(client: TestClient):
    response = client.post(
        f"{settings.API_V1_STR}/buyers/purchase",
        json={"product_id": str(uuid.uuid4())}
    )
    assert response.status_code == status.HTTP_401_UNAUTHORIZED


def test_buy_product_service_error(client: TestClient, normal_user_token_headers: dict):
    with patch("app.api.dependencies.PurchaseServiceDep.process_purchase", side_effect=HTTPException(400, "Bad request")):
        response = client.post(
            f"{settings.API_V1_STR}/buyers/purchase",
            headers=normal_user_token_headers,
            json={"product_id": str(uuid.uuid4())}
        )
        assert response.status_code == 400
        assert "HTTP Error" in response.json()["message"]


# Тесты для рекомендаций
def test_get_viewed_recommendations(client: TestClient, normal_user_token_headers: dict, mock_redis):
    # Настройка моков
    product_id = uuid.uuid4()
    mock_redis.zrange.return_value = [str(product_id).encode()]

    mock_product = Product(id=product_id, category="Electronics")
    with patch("app.core.postgres.dao.ProductDAO.find_all") as mock_find:
        mock_find.side_effect = [
            [mock_product],  # Для viewed_products_objs
            [Product(id=uuid.uuid4(), category="Electronics")]  # Для рекомендаций
        ]

        response = client.get(
            f"{settings.API_V1_STR}/buyers/recommendations/viewed",
            headers=normal_user_token_headers
        )
        assert response.status_code == 200
        assert len(response.json()) == 1


def test_get_favorite_recommendations_empty(client: TestClient, normal_user_token_headers: dict):
    with patch("app.core.postgres.dao.UserProductInteractionDAO.find_all", return_value=[]):
        response = client.get(
            f"{settings.API_V1_STR}/buyers/recommendations/favorites",
            headers=normal_user_token_headers
        )
        assert response.status_code == 200
        assert response.json() == []


def test_get_cart_recommendations_error(client: TestClient, normal_user_token_headers: dict):
    with patch("app.core.postgres.dao.UserProductInteractionDAO.find_all", side_effect=Exception("DB error")):
        response = client.get(
            f"{settings.API_V1_STR}/buyers/recommendations/cart",
            headers=normal_user_token_headers
        )
        assert response.status_code == 500
        assert "cart content" in response.json()["detail"]


def test_get_purchase_recommendations_with_limit(client: TestClient, normal_user_token_headers: dict):
    # Настройка тестовых данных
    purchased_product = Product(id=uuid.uuid4(), category="Books")
    recommended_product = Product(id=uuid.uuid4(), category="Books")

    with patch("app.core.postgres.dao.UserProductInteractionDAO.find_all") as mock_interactions, \
            patch("app.core.postgres.dao.ProductDAO.find_all") as mock_products:
        mock_interactions.return_value = [Mock(product_id=purchased_product.id)]
        mock_products.side_effect = [
            [purchased_product],  # Для purchased products
            [recommended_product]  # Для рекомендаций
        ]

        response = client.get(
            f"{settings.API_V1_STR}/buyers/recommendations/purchase?limit=5",
            headers=normal_user_token_headers
        )
        assert response.status_code == 200
        assert len(response.json()) == 1


# Фикстуры для pytest
@pytest.fixture
def mock_redis():
    with patch("app.api.dependencies.RedisDep") as mock:
        yield mock


@pytest.fixture
def normal_user_token_headers(client: TestClient):
    # Здесь должна быть реализация получения токена для обычного пользователя
    return {"Authorization": "Bearer testtoken"}