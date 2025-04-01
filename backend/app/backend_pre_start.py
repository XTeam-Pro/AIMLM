import logging
from sqlalchemy import Engine
from sqlmodel import Session, select
from tenacity import after_log, before_log, retry, stop_after_attempt, wait_fixed

from app.core.postgres.db_engine import engine

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

max_tries = 60 * 5  # 5 minutes
wait_seconds = 1

@retry(
    stop=stop_after_attempt(max_tries),
    wait=wait_fixed(wait_seconds),
    before=before_log(logger, logging.INFO),
    after=after_log(logger, logging.WARN),
)
def check_db_connection(db_engine: Engine) -> None:
    try:
        with Session(db_engine) as session:
            # Simple connection test
            session.exec(select(1))
    except Exception as e:
        logger.error(e)
        raise e

def main() -> None:
    logger.info("Checking database connection")
    check_db_connection(engine)
    logger.info("Database connection established")

if __name__ == "__main__":
    main()