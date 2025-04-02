from __future__ import annotations
from typing import TYPE_CHECKING
from collections.abc import Generator
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import delete
from sqlmodel import Session

from app.core.postgres.config import settings
from app.core.postgres.dao import UserDAO
from app.core.postgres.db import init_db
from app.core.postgres.db_engine import engine
from app.main import app
from app.models.core import User
from app.schemas.core_schemas import UserRegister
from app.tests.utils.user import authentication_token_from_email
from app.tests.utils.utils import get_superuser_token_headers


@pytest.fixture(scope="session", autouse=True)
def db() -> Generator[Session, None, None]:
    with Session(engine) as session:
        init_db(session)
        yield session
        session.execute(delete(User))
        session.commit()

@pytest.fixture(scope="module")
def client() -> Generator[TestClient, None, None]:
    with TestClient(app) as c:
        yield c

@pytest.fixture(scope="module")
def superuser_token_headers(client: TestClient, db: Session) -> dict[str, str]:

    return get_superuser_token_headers(client=client)


@pytest.fixture(scope="module")
def normal_user_token_headers(client: TestClient, db: Session) -> dict[str, str]:

    return authentication_token_from_email(
        client=client,
        email=settings.EMAIL_TEST_USER,
        db=db
    )


@pytest.fixture(scope="function")
def test_user(db: Session) -> Generator[User, None, None]:
    """Фикстура для создания тестового пользователя"""
    user_data = {
        "email": "testuser@example.com",
        "username": "testuser",
        "phone": "+1234567890",
        "full_name": "Test User",
        "hashed_password": "ValidPass1!",
        "address": "123 Test St, Test City",
        "postcode": "12345",
        "role": "client",
        "status": "active",
        "balance": 0.0
    }

    user = UserDAO(db).add(UserRegister(**user_data))
    yield user
    db.delete(user)
    db.commit()