import uuid
from fastapi.testclient import TestClient
from sqlmodel import Session
from app.core.postgres.config import settings
from app.tests.utils.product import create_random_product

from app.tests.utils.item import create_random_item


def test_create_item(
    client: TestClient, superuser_token_headers: dict[str, str], db: Session
) -> None:
    product = create_random_product(db)  # Fixed: use create_random_product instead
    data = {
        "product_id": str(product.id),
        "interaction_type": "PURCHASE",
        "quantity": 2
    }
    response = client.post(
        f"{settings.API_V1_STR}/items/",
        headers=superuser_token_headers,
        json=data,
    )
    assert response.status_code == 200
    content = response.json()
    assert content["interaction_type"] == data["interaction_type"]
    assert content["quantity"] == data["quantity"]
    assert content["product_id"] == data["product_id"]
    assert "id" in content
    assert "user_id" in content

def test_create_item_product_not_found(
        client: TestClient, superuser_token_headers: dict[str, str]
) -> None:
    data = {
        "product_id": str(uuid.uuid4()),
        "interaction_type": "PURCHASE",
        "quantity": 1
    }
    response = client.post(
        f"{settings.API_V1_STR}/items/",
        headers=superuser_token_headers,
        json=data,
    )
    assert response.status_code == 404
    assert response.json()["detail"] == "Product not found"


def test_read_item(
        client: TestClient, superuser_token_headers: dict[str, str], db: Session
) -> None:
    item = create_random_item(db)
    response = client.get(
        f"{settings.API_V1_STR}/items/{item.id}",
        headers=superuser_token_headers,
    )
    assert response.status_code == 200
    content = response.json()
    assert content["interaction_type"] == item.interaction_type
    assert content["quantity"] == item.quantity
    assert content["id"] == str(item.id)
    assert content["user_id"] == str(item.user_id)


def test_read_item_not_found(
        client: TestClient, superuser_token_headers: dict[str, str]
) -> None:
    response = client.get(
        f"{settings.API_V1_STR}/items/{uuid.uuid4()}",
        headers=superuser_token_headers,
    )
    assert response.status_code == 404
    assert response.json()["detail"] == "Item not found"


def test_read_item_not_enough_permissions(
        client: TestClient, normal_user_token_headers: dict[str, str], db: Session
) -> None:
    item = create_random_item(db)
    response = client.get(
        f"{settings.API_V1_STR}/items/{item.id}",
        headers=normal_user_token_headers,
    )
    assert response.status_code == 403
    assert response.json()["detail"] == "Not enough permissions"



def test_update_item(
        client: TestClient, superuser_token_headers: dict[str, str], db: Session
) -> None:
    item = create_random_item(db)
    data = {"interaction_type": "FAVORITE", "quantity": 3}
    response = client.put(
        f"{settings.API_V1_STR}/items/{item.id}",
        headers=superuser_token_headers,
        json=data,
    )
    assert response.status_code == 200
    content = response.json()
    assert content["interaction_type"] == data["interaction_type"]
    assert content["quantity"] == data["quantity"]
    assert content["id"] == str(item.id)


def test_update_item_not_found(
        client: TestClient, superuser_token_headers: dict[str, str]
) -> None:
    data = {"interaction_type": "FAVORITE"}
    response = client.put(
        f"{settings.API_V1_STR}/items/{uuid.uuid4()}",
        headers=superuser_token_headers,
        json=data,
    )
    assert response.status_code == 404
    assert response.json()["detail"] == "Item not found"


def test_update_item_not_enough_permissions(
        client: TestClient, normal_user_token_headers: dict[str, str], db: Session
) -> None:
    item = create_random_item(db)
    data = {"interaction_type": "FAVORITE"}
    response = client.put(
        f"{settings.API_V1_STR}/items/{item.id}",
        headers=normal_user_token_headers,
        json=data,
    )
    assert response.status_code == 403
    assert response.json()["detail"] == "Not enough permissions"


def test_delete_item(
        client: TestClient, superuser_token_headers: dict[str, str], db: Session
) -> None:
    item = create_random_item(db)
    response = client.delete(
        f"{settings.API_V1_STR}/items/{item.id}",
        headers=superuser_token_headers,
    )
    assert response.status_code == 200
    assert response.json()["message"] == "Item deleted successfully"


def test_delete_item_not_found(
        client: TestClient, superuser_token_headers: dict[str, str]
) -> None:
    response = client.delete(
        f"{settings.API_V1_STR}/items/{uuid.uuid4()}",
        headers=superuser_token_headers,
    )
    assert response.status_code == 404
    assert response.json()["detail"] == "Item not found"


def test_delete_item_not_enough_permissions(
        client: TestClient, normal_user_token_headers: dict[str, str], db: Session
) -> None:
    item = create_random_item(db)
    response = client.delete(
        f"{settings.API_V1_STR}/items/{item.id}",
        headers=normal_user_token_headers,
    )
    assert response.status_code == 403
    assert response.json()["detail"] == "Not enough permissions"


def test_get_item_for_product_not_found(
    client: TestClient, superuser_token_headers: dict[str, str], db: Session
) -> None:
    product = create_random_product(db)  # Fixed: use create_random_product
    response = client.get(
        f"{settings.API_V1_STR}/items/product/{product.id}?interaction_type=FAVORITE",
        headers=superuser_token_headers,
    )
    assert response.status_code == 404
    assert "No FAVORITE interaction found" in response.json()["detail"]


