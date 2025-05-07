import random

from unittest.mock import patch


from fastapi.testclient import TestClient
from sqlmodel import Session

from app.core.postgres.config import settings
from app.core.postgres.dao import UserDAO
from app.core.security import verify_password, get_password_hash
from app.schemas.users import UserRegister
from app.schemas.types import UserRole, UserStatus
from app.tests.crud.test_user import create_test_user_data

def create_test_user() -> tuple[dict, str]:
    """
    Creates test data.
    """
    email = f"user_{random.randint(10000, 99999)}@valid-domain.com"
    username = f"user_{random.randint(1000, 9999)}"
    password = "ValidPass1"
    user_data = {
        "email": email,
        "username": username,
        "full_name": "Test User",
        "phone": "+1234567890",
        "hashed_password": get_password_hash(password),
        "address": "123 Main St, New York",
        "postcode": "10001",
        "role": UserRole.CLIENT,
        "status": UserStatus.ACTIVE,
        "cash_balance": 0.0,
        "pv_balance": 0.0,
    }
    return user_data, password

def test_get_users_superuser_me(
        client: TestClient, superuser_token_headers: dict[str, str]
) -> None:
    r = client.get(f"{settings.API_V1_STR}/users/me", headers=superuser_token_headers)
    current_user = r.json()
    assert current_user
    assert current_user["status"] == "active"
    assert current_user["role"] == "admin"
    assert current_user["email"] == settings.FIRST_SUPERUSER

def test_get_users_normal_user_me(
        client: TestClient, normal_user_token_headers: dict[str, str]
) -> None:
    r = client.get(f"{settings.API_V1_STR}/users/me", headers=normal_user_token_headers)
    current_user = r.json()
    assert current_user
    assert current_user["status"] == "active"
    assert current_user["role"] == "client"
    assert current_user["email"] == settings.EMAIL_TEST_USER

def test_create_user_new_email(
        client: TestClient, superuser_token_headers: dict[str, str], db: Session
) -> None:
    with patch("app.utils.send_email", return_value=None):
        user_data, _ = create_test_user()
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
        assert user.username == user_data["username"]

def test_get_existing_user(
        client: TestClient, superuser_token_headers: dict[str, str], db: Session
) -> None:
    user_data, _ = create_test_user()
    user_dao = UserDAO(db)
    user = user_dao.add(UserRegister.model_validate(user_data))

    r = client.get(
        f"{settings.API_V1_STR}/users/{user.id}",
        headers=superuser_token_headers,
    )
    assert 200 <= r.status_code < 300
    api_user = r.json()
    assert api_user["email"] == user_data["email"]
    assert api_user["username"] == user_data["username"]

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
    user_dao = UserDAO(db)
    for _ in range(3):
        user_data, _ = create_test_user()
        user_in = UserRegister.model_validate(user_data)
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
        assert "username" in item
        assert "phone" in item

def test_update_user_me(
        client: TestClient, normal_user_token_headers: dict[str, str], db: Session
) -> None:
    user_data, _ = create_test_user()
    user_in = UserRegister.model_validate(user_data)
    user_dao = UserDAO(db)
    user = user_dao.add(user_in)

    login_data = {
        "username": user_data["email"],
        "password": "ValidPass1",  # Используем plain password
    }
    r = client.post(f"{settings.API_V1_STR}/login/access-token", data=login_data)
    tokens = r.json()
    headers = {"Authorization": f"Bearer {tokens['access_token']}"}

    update_data = {"full_name": "New Name", "phone": "+9876543210"}
    r = client.patch(
        f"{settings.API_V1_STR}/users/me",
        headers=headers,
        json=update_data,
    )
    assert r.status_code == 200
    updated_user = r.json()
    assert updated_user["full_name"] == "New Name"
    assert updated_user["phone"] == "+9876543210"

def test_update_password_me(
        client: TestClient, normal_user_token_headers: dict[str, str], db: Session
) -> None:
    user_data, plain_password = create_test_user()
    user_in = UserRegister.model_validate(user_data)
    user_dao = UserDAO(db)
    user = user_dao.add(user_in)

    login_data = {
        "username": user_data["email"],
        "password": plain_password,
    }
    r = client.post(f"{settings.API_V1_STR}/login/access-token", data=login_data)
    tokens = r.json()
    headers = {"Authorization": f"Bearer {tokens['access_token']}"}

    new_password = "NewValidPass1"
    data = {
        "current_password": plain_password,
        "new_password": new_password,
    }
    r = client.patch(
        f"{settings.API_V1_STR}/users/me/password",
        headers=headers,
        json=data,
    )
    assert r.status_code == 200
    assert r.json()["message"] == "Password updated successfully"

    updated_user = user_dao.find_one_or_none({"id": user.id})
    assert verify_password(new_password, updated_user.hashed_password)

def test_register_user(client: TestClient, db: Session) -> None:
    user_data, _ = create_test_user()
    # Для регистрации используем plain password
    registration_data = user_data.copy()
    registration_data["password"] = "ValidPass1"
    del registration_data["hashed_password"]

    r = client.post(
        f"{settings.API_V1_STR}/users/signup",
        json=registration_data,
    )
    assert r.status_code == 200
    created_user = r.json()

    user_dao = UserDAO(db)
    user = user_dao.find_one_or_none({"email": user_data["email"]})
    assert user
    assert user.email == created_user["email"]
    assert verify_password("ValidPass1", user.hashed_password)

def test_delete_user_me(client: TestClient, db: Session) -> None:
    user_data, plain_password = create_test_user()
    hashed_password = get_password_hash(plain_password)
    user_data["hashed_password"] = hashed_password

    user_dao = UserDAO(db)
    user = user_dao.add(UserRegister.model_validate(user_data))

    db_user = user_dao.find_one_or_none({"email": user_data["email"]})
    assert db_user is not None

    login_data = {
        "username": db_user.email,
        "password": plain_password,
    }
    response = client.post(
        f"{settings.API_V1_STR}/login/access-token",
        data=login_data
    )
    assert response.status_code == 200

    tokens = response.json()
    headers = {"Authorization": f"Bearer {tokens['access_token']}"}
    delete_response = client.delete(
        f"{settings.API_V1_STR}/users/me",
        headers=headers,
    )
    assert delete_response.status_code == 200
    assert delete_response.json()["message"] == "User deleted successfully"

    assert user_dao.find_one_or_none({"id": user.id}) is None