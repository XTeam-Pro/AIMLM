
from datetime import datetime
from typing import Annotated, Any
from uuid import UUID

import jwt
import redis
from fastapi import Depends, HTTPException, status
from fastapi.encoders import jsonable_encoder
from fastapi.security import OAuth2PasswordBearer
from jwt.exceptions import InvalidTokenError
from pydantic import ValidationError
from redis import Redis
from sqlmodel import Session

from app.core import security
from app.core.postgres.config import settings
from app.core.postgres.dao import UserDAO
from app.core.postgres.session_handler import get_session_with_commit, get_session_without_commit
from app.models.core import User
from app.schemas.core_schemas import TokenPayload

reusable_oauth2 = OAuth2PasswordBearer(
    tokenUrl=f"{settings.API_V1_STR}/login/access-token"
)


def get_redis():
    return redis.from_url(settings.REDIS_URL)




def custom_serializer(obj: Any) -> Any:
    """Custom function to serialize incompatible datatypes with Redis """
    if isinstance(obj, UUID):
        return jsonable_encoder(obj)
    elif isinstance(obj, datetime):
        return obj.isoformat()
    raise TypeError(f"Object of type {obj.__class__.__name__} is not JSON serializable")


CommittedSessionDep = Annotated[Session, Depends(get_session_with_commit)]
UncommittedSessionDep = Annotated[Session, Depends(get_session_without_commit)]
TokenDep = Annotated[str, Depends(reusable_oauth2)]
RedisDep = Annotated[Redis, Depends(get_redis)]

def get_current_user(session: UncommittedSessionDep, token: TokenDep) -> User:
    try:
        payload = jwt.decode(
            token, settings.SECRET_KEY, algorithms=[security.ALGORITHM]
        )
        token_data = TokenPayload(**payload)
    except (InvalidTokenError, ValidationError):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Could not validate credentials",
        )
    user = UserDAO(session).find_one_or_none_by_id(token_data.sub)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    if user.status == "inactive":
        raise HTTPException(status_code=400, detail="Inactive user")
    return user


CurrentUser = Annotated[User, Depends(get_current_user)]


def get_current_active_superuser(current_user: CurrentUser) -> User:
    if current_user.role != "admin":
        raise HTTPException(
            status_code=403, detail="The user doesn't have enough privileges"
        )
    return current_user
