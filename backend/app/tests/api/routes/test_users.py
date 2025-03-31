
from unittest.mock import patch
from fastapi.testclient import TestClient
from sqlmodel import Session

from app.core.postgres.config import settings
from app.core.postgres.dao import UserDAO
from app.core.security import verify_password
from app.schemas.core_schemas import UserRegister

from app.tests.utils.utils import random_email, random_phone


def create_test_user_data(role="client", status="active"):
    return {
        "email": random_email(),
        "username": "testuser",
        "phone": random_phone(),
        "full_name": "Test User",
        "hashed_password": "ValidPass1",
        "address": "123 Main St, New York",
        "postcode": "10001",
        "role": role,
        "status": status,
        "balance": 0.0
    }


def test_get_users_superuser_me(
        client: TestClient, superuser_token_headers: dict[str, str]
) -> None:
    r = client.get(f"{settings.API_V1_STR}/users/me", headers=superuser_token_headers)
    current_user = r.json()
    assert current_user
    assert current_user["status"] == "active"
    assert current_user["role"] == "admin"  # Предполагая, что admin = суперпользователь
    assert current_user["email"] == settings.FIRST_SUPERUSER


def test_get_users_normal_user_me(
        client: TestClient, normal_user_token_headers: dict[str, str]
) -> None:
    r = client.get(f"{settings.API_V1_STR}/users/me", headers=normal_user_token_headers)
    current_user = r.json()
    assert current_user
    assert current_user["status"] == "active"
    assert current_user["role"] == "client"  # Обычный пользователь
    assert current_user["email"] == settings.EMAIL_TEST_USER


def test_create_user_new_email(
        client: TestClient, superuser_token_headers: dict[str, str], db: Session
) -> None:
    with patch("app.utils.send_email", return_value=None):
        user_data = create_test_user_data()
        r = client.post(
            f"{settings.API_V1_STR}/users/",
            headers=superuser_token_headers,
            json=user_data,
        )
        assert 200 <= r.status_code < 300
        created_user = r.json()

        user_dao = UserDAO(db)
        user = user_dao.find_one_or_none({"email": user_data["email"]})
        assert user
        assert user.email == created_user["email"]


def test_get_existing_user(
        client: TestClient, superuser_token_headers: dict[str, str], db: Session
) -> None:
    user_data = create_test_user_data()
    user_in = UserRegister(**user_data)
    user_dao = UserDAO(db)
    user = user_dao.add(user_in)

    r = client.get(
        f"{settings.API_V1_STR}/users/{user.id}",
        headers=superuser_token_headers,
    )
    assert 200 <= r.status_code < 300
    api_user = r.json()
    assert api_user["email"] == user_data["email"]


def test_create_user_existing_email(
        client: TestClient, superuser_token_headers: dict[str, str], db: Session
) -> None:
    user_data = create_test_user_data()
    user_in = UserRegister(**user_data)
    user_dao = UserDAO(db)
    user_dao.add(user_in)

    r = client.post(
        f"{settings.API_V1_STR}/users/",
        headers=superuser_token_headers,
        json=user_data,
    )
    assert r.status_code == 400
    assert r.json()["detail"] == "The user with this email already exists in the system"


def test_retrieve_users(
        client: TestClient, superuser_token_headers: dict[str, str], db: Session
) -> None:
    # Создаем тестовых пользователей
    user_dao = UserDAO(db)
    for _ in range(3):
        user_data = create_test_user_data()
        user_in = UserRegister(**user_data)
        user_dao.add(user_in)

    r = client.get(
        f"{settings.API_V1_STR}/users/?skip=0&limit=10",
        headers=superuser_token_headers,
    )
    all_users = r.json()

    assert len(all_users["data"]) > 0
    assert "count" in all_users
    for item in all_users["data"]:
        assert "email" in item


def test_update_user_me(
        client: TestClient, normal_user_token_headers: dict[str, str], db: Session
) -> None:
    # Создаем тестового пользователя
    user_data = create_test_user_data()
    user_in = UserRegister(**user_data)
    user_dao = UserDAO(db)
    user = user_dao.add(user_in)

    # Логинимся как этот пользователь
    login_data = {
        "username": user_data["email"],
        "password": user_data["hashed_password"],
    }
    r = client.post(f"{settings.API_V1_STR}/login/access-token", data=login_data)
    tokens = r.json()
    headers = {"Authorization": f"Bearer {tokens['access_token']}"}

    # Обновляем данные
    update_data = {"full_name": "New Name", "phone": "+1234567890"}
    r = client.patch(
        f"{settings.API_V1_STR}/users/me",
        headers=headers,
        json=update_data,
    )
    assert r.status_code == 200
    updated_user = r.json()
    assert updated_user["full_name"] == "New Name"
    assert updated_user["phone"] == "+1234567890"


def test_update_password_me(
        client: TestClient, normal_user_token_headers: dict[str, str], db: Session
) -> None:
    # Создаем тестового пользователя
    user_data = create_test_user_data()
    user_in = UserRegister(**user_data)
    user_dao = UserDAO(db)
    user = user_dao.add(user_in)

    # Логинимся как этот пользователь
    login_data = {
        "username": user_data["email"],
        "password": user_data["hashed_password"],
    }
    r = client.post(f"{settings.API_V1_STR}/login/access-token", data=login_data)
    tokens = r.json()
    headers = {"Authorization": f"Bearer {tokens['access_token']}"}

    # Меняем пароль
    new_password = "NewValidPass1"
    data = {
        "current_password": user_data["hashed_password"],
        "new_password": new_password,
    }
    r = client.patch(
        f"{settings.API_V1_STR}/users/me/password",
        headers=headers,
        json=data,
    )
    assert r.status_code == 200
    assert r.json()["message"] == "Password updated successfully"

    # Проверяем, что пароль действительно изменился
    updated_user = user_dao.find_one_or_none({"id": user.id})
    assert verify_password(new_password, updated_user.hashed_password)


def test_register_user(client: TestClient, db: Session) -> None:
    user_data = create_test_user_data()
    r = client.post(
        f"{settings.API_V1_STR}/users/signup",
        json=user_data,
    )
    assert r.status_code == 200
    created_user = r.json()

    user_dao = UserDAO(db)
    user = user_dao.find_one_or_none({"email": user_data["email"]})
    assert user
    assert user.email == created_user["email"]
    assert verify_password(user_data["hashed_password"], user.hashed_password)


def test_delete_user_me(client: TestClient, db: Session) -> None:
    # Создаем тестового пользователя
    user_data = create_test_user_data()
    user_in = UserRegister(**user_data)
    user_dao = UserDAO(db)
    user = user_dao.add(user_in)

    # Логинимся как этот пользователь
    login_data = {
        "username": user_data["email"],
        "password": user_data["hashed_password"],
    }
    r = client.post(f"{settings.API_V1_STR}/login/access-token", data=login_data)
    tokens = r.json()
    headers = {"Authorization": f"Bearer {tokens['access_token']}"}

    # Удаляем аккаунт
    r = client.delete(
        f"{settings.API_V1_STR}/users/me",
        headers=headers,
    )
    assert r.status_code == 200
    assert r.json()["message"] == "User deleted successfully"

    # Проверяем, что пользователь действительно удален
    assert user_dao.find_one_or_none({"id": user.id}) is None