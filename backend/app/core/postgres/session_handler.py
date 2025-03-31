from __future__ import annotations
from typing import Generator, TYPE_CHECKING
from sqlmodel import Session

from app.core.postgres.db_engine import engine


#
# if TYPE_CHECKING:
#     """Prevents circular import"""


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