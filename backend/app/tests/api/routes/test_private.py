from fastapi.testclient import TestClient
from sqlmodel import Session

from app.core.postgres.config import settings
from app.core.postgres.dao import UserDAO


def test_create_user(client: TestClient, db: Session) -> None:
    r = client.post(
        f"{settings.API_V1_STR}/private/users/",
        json={
            "email": "pollo@listo.com",
            "password": "password123",
            "full_name": "Pollo Listo",
        },
    )

    assert r.status_code == 200

    data = r.json()

    user = UserDAO(db).find_one_or_none_by_id(data["id"])

    assert user
    assert user.email == "pollo@listo.com"
    assert user.full_name == "Pollo Listo"
