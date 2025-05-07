from sqlmodel import create_engine
from app.core.postgres.config import settings

engine = create_engine(
    str(settings.SQLALCHEMY_DATABASE_URI),
    pool_size=20,
    max_overflow=10,
    pool_pre_ping=True
)