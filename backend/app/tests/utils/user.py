from fastapi.testclient import TestClient
from sqlmodel import Session

from app.core.postgres.config import settings
from app.core.postgres.dao import UserDAO

from app.schemas.core_schemas import UserRegister
from app.models.core import User
from app.tests.utils.utils import random_email,  random_phone


def create_test_user_data(role="client", status="active"):
    """Generates fake user data"""
    return {
        "email": random_email(),
        "username": "testuser",
        "phone": random_phone(),
        "full_name": "Test User",
        "hashed_password": "ValidPass1",  # Пароль должен соответствовать валидации
        "address": "123 Main St, New York",
        "postcode": "10001",
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


def create_random_user(db: Session) -> User:
    """Creates a random user"""
    user_data = create_test_user_data()
    user_in = UserRegister(**user_data)
    user_dao = UserDAO(db)
    user = user_dao.add(user_in)
    return user


def authentication_token_from_email(
        *, client: TestClient, email: str, db: Session
) -> dict[str, str]:
    """
    Gets auth token for user with the specified email.
    If user doesn't exist it creates him.
    """
    password = "ValidPass1"  # Пароль должен соответствовать валидации

    user_dao = UserDAO(db)
    user = user_dao.find_one_or_none({"email": email})

    if not user:
        user_data = create_test_user_data()
        user_data["email"] = email
        user_data["hashed_password"] = password
        user_in = UserRegister(**user_data)
        user_dao.add(user_in)
    else:
        user_dao.update({"id": user.id}, {"hashed_password": password})

    return user_authentication_headers(client=client, email=email, password=password)


def get_superuser_headers(client: TestClient, db: Session) -> dict[str, str]:
    """Gets superuser's headers"""
    return authentication_token_from_email(
        client=client,
        email=settings.FIRST_SUPERUSER,
        db=db
    )