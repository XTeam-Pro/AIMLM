import random
import uuid

from fastapi.testclient import TestClient
from sqlmodel import Session, delete

from app.core.postgres.config import settings
from app.core.postgres.dao import UserDAO
from app.core.security import get_password_hash, verify_password

from app.schemas.users import UserRegister
from app.models.user import User
from app.schemas.types import UserRole, UserStatus


def create_test_user_data(role="client", status="active"):
    """Generates valid test user data"""
    return {
        "email": "aleks@google.com",  # Используем допустимый домен
        "username": "Testuser",
        "phone": "+1234567890",  # Фиксированный валидный номер
        "full_name": "Test User",
        "password": "ValidPass1",  # Plain password для регистрации/логина
        "hashed_password": get_password_hash("ValidPass1"),  # Хешированный для БД
        "address": "123 Main St, New York",
        "postcode": "10001",
        "cash_balance": 45.63,
        "pv_balance": 34.21,
        "role": role,
        "status": status,
        "balance": 0.0
    }


def user_authentication_headers(
        *, client: TestClient, email: str, password: str
) -> dict[str, str]:
    """Gets headers with auth token"""
    data = {"username": email, "password": password}

    r = client.post(f"{settings.API_V1_STR}/login/access-token", data=data)
    response = r.json()
    auth_token = response["access_token"]
    headers = {"Authorization": f"Bearer {auth_token}"}
    return headers


def create_test_user(
        role: UserRole = UserRole.CLIENT,
        status: UserStatus = UserStatus.ACTIVE
) -> dict:
    """
    Returns a test user (dict)
    """
    plain_password = "ValidPass1"

    return (
        {
            "email": f"testuser_{uuid.uuid4().hex[:8]}@example.org",
            "username": f"user_{uuid.uuid4().hex[:6]}",
            "phone": f"+{random.randint(100000000000, 999999999999)}",
            "full_name": "Test User",
            "hashed_password": get_password_hash(plain_password),
            "address": "123 Main St, New York",
            "postcode": "10001",
            "role": role,
            "status": status,
            "cash_balance": 0.0,
            "pv_balance": 0.0,
        }
    )

def authentication_token_from_email(
        *, client: TestClient, email: str, db: Session
) -> dict[str, str]:
    """
    Gets auth token for user with the specified email.
    If user doesn't exist it creates him.
    """
    password = "ValidPass1"  # Plain password для аутентификации

    user_dao = UserDAO(db)
    user = user_dao.find_one_or_none({"email": email})

    if not user:
        user_data = create_test_user()
        user_data["email"] = email
        # Сохраняем хешированный пароль в БД
        user_in = UserRegister(**{
            **user_data,
            "hashed_password": get_password_hash(password)
        })
        user_dao.add(user_in)
    else:
        # Обновляем пароль, если пользователь существует
        user_dao.update({"id": user.id}, {
            "hashed_password": get_password_hash(password)
        })

    return user_authentication_headers(
        client=client,
        email=email,
        password=password  # Используем plain password для аутентификации
    )


def get_superuser_headers(client: TestClient, db: Session) -> dict[str, str]:
    """Gets superuser's headers"""
    return authentication_token_from_email(
        client=client,
        email=settings.FIRST_SUPERUSER,
        db=db
    )


# Тестовые функции
def test_user_creation(db: Session):
    """Test user creation in database"""
    user_data = create_test_user()
    user_in = UserRegister(**user_data)
    user_dao = UserDAO(db)
    user = user_dao.add(user_in)

    assert user.email == user_data["email"]
    assert verify_password("ValidPass1", user.hashed_password)


def test_user_authentication(client: TestClient, db: Session):
    """Test user authentication flow"""
    # Создаем тестового пользователя
    user = create_test_user(db)

    # Получаем токен аутентификации
    headers = user_authentication_headers(
        client=client,
        email=user.email,
        password="ValidPass1"  # Plain password
    )

    # Проверяем доступ к защищенному эндпоинту
    r = client.get(f"{settings.API_V1_STR}/users/me", headers=headers)
    assert r.status_code == 200
    current_user = r.json()
    assert current_user["email"] == user.email


def test_superuser_access(client: TestClient, db: Session):
    """Test superuser access"""
    headers = get_superuser_headers(client, db)

    # Проверяем доступ к защищенному эндпоинту
    r = client.get(f"{settings.API_V1_STR}/users/me", headers=headers)
    assert r.status_code == 200
    current_user = r.json()
    assert current_user["email"] == settings.FIRST_SUPERUSER
    assert current_user["role"] == "admin"