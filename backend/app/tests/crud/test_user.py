import uuid
from fastapi.encoders import jsonable_encoder
from sqlmodel import Session

from app.core.security import verify_password
from app.models.core import User
from app.schemas.core_schemas import UserCreate, UserUpdate, UserRegister, NewPassword
from app.core.postgres.dao import UserDAO
from app.tests.utils.utils import random_email, random_lower_string, random_phone


def create_test_user_data():
    return {
        "email": random_email(),
        "username": "testuser",
        "phone": random_phone(),
        "full_name": "Test User",
        "hashed_password": "ValidPass1",
        "address": "123 Main St, New York",
        "postcode": "10001",
    }


def test_create_user(db: Session) -> None:
    user_data = create_test_user_data()
    user_in = UserRegister(**user_data)
    user_dao = UserDAO(db)
    user = user_dao.add(user_in)

    assert user.email == user_data["email"]
    assert user.username == user_data["username"]
    assert hasattr(user, "hashed_password")


def test_authenticate_user(db: Session) -> None:
    user_data = create_test_user_data()
    password = user_data["hashed_password"]
    user_in = UserRegister(**user_data)

    user_dao = UserDAO(db)
    user = user_dao.add(user_in)

    # В реальном приложении пароль должен хешироваться перед сохранением
    authenticated_user = user_dao.authenticate(
        email=user_data["email"],
        password=password
    )

    assert authenticated_user
    assert user.email == authenticated_user.email


def test_not_authenticate_user(db: Session) -> None:
    email = random_email()
    password = random_lower_string()
    user_dao = UserDAO(db)
    user = user_dao.authenticate(email=email, password=password)
    assert user is None


def test_check_if_user_is_active(db: Session) -> None:
    user_data = create_test_user_data()
    user_in = UserRegister(**user_data)
    user_dao = UserDAO(db)
    user = user_dao.add(user_in)
    assert user.status == "active"  # Или как у вас определяется активность


def test_check_if_user_is_superuser(db: Session) -> None:
    user_data = create_test_user_data()
    user_in = UserCreate(**user_data, role="admin")
    user_dao = UserDAO(db)
    user = user_dao.add(user_in)
    assert user.role == "admin"


def test_get_user(db: Session) -> None:
    user_data = create_test_user_data()
    user_in = UserRegister(**user_data)
    user_dao = UserDAO(db)
    user = user_dao.add(user_in)

    user_2 = user_dao.find_one_or_none({"id": user.id})
    assert user_2
    assert user.email == user_2.email
    assert jsonable_encoder(user) == jsonable_encoder(user_2)


def test_update_user(db: Session) -> None:
    user_data = create_test_user_data()
    user_in = UserRegister(**user_data)
    user_dao = UserDAO(db)
    user = user_dao.add(user_in)

    new_data = {
        "full_name": "Updated Name",
        "phone": "+12345678901"
    }
    user_in_update = UserUpdate(**new_data)

    updated_user = user_dao.update({"id": user.id}, user_in_update)
    assert updated_user
    assert updated_user.full_name == new_data["full_name"]
    assert updated_user.phone == new_data["phone"]


def test_update_user_password(db: Session) -> None:
    user_data = create_test_user_data()
    user_in = UserRegister(**user_data)
    user_dao = UserDAO(db)
    user = user_dao.add(user_in)

    new_password = "NewValidPass1"


    updated_user = user_dao.update({"id": user.id}, {"hashed_password": new_password})
    assert updated_user
    # Здесь нужно использовать вашу функцию verify_password
    assert verify_password(new_password, updated_user.hashed_password)


def test_get_users_paginated(db: Session) -> None:
    # Создаем несколько тестовых пользователей
    user_dao = UserDAO(db)
    for _ in range(5):
        user_data = create_test_user_data()
        user_in = UserRegister(**user_data)
        user_dao.add(user_in)

    # Тестируем пагинацию
    users_page = user_dao.find_all(skip=0, limit=2)
    assert len(users_page) == 2

    users_page2 = user_dao.find_all(skip=2, limit=2)
    assert len(users_page2) == 2