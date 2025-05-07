
from typing import Generator
from sqlmodel import Session

from app.core.postgres.db_engine import engine





def get_session_with_commit() -> Generator[Session, None, None]:
    """Session with automatic commit."""
    with Session(engine) as session:
        try:
            yield session
            session.commit()
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()

def get_session_without_commit() -> Generator[Session, None, None]:
    """Session without automatic commit."""
    with Session(engine) as session:
        try:
            yield session
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()