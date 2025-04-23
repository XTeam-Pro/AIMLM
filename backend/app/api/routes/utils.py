import logging

from fastapi import APIRouter, Depends, HTTPException
from starlette import status

from app.api.dependencies.deps import get_current_active_superuser, CommittedSessionDep
from app.core.postgres.dao import GenerationBonusMatrixDAO
from app.schemas.common import Message
from app.schemas.mlm import GenerationBonusMatrixList

from app.utils import generate_test_email, send_email

router = APIRouter(prefix="/utils", tags=["Utils"])
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

@router.post(
    "/test-email/",
    dependencies=[Depends(get_current_active_superuser)],
    status_code=201,
)
def test_email(email_to: str) -> Message:
    """
    Test emails.
    """
    email_data = generate_test_email(email_to=email_to)
    send_email(
        email_to=email_to,
        subject=email_data.subject,
        html_content=email_data.html_content,
    )
    return Message(message="Test email sent")


@router.get("/health-check/")
async def health_check() -> bool:
    return True


@router.post("/matrix/generation_bonus_metrics", dependencies=[Depends(get_current_active_superuser)], status_code=201)
def insert_generation_bonus_matrix(session: CommittedSessionDep, matrix: GenerationBonusMatrixList):
    rows = GenerationBonusMatrixDAO(session).find_all()
    if rows:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Matrix already exists."
        )
    GenerationBonusMatrixDAO(session).add_many(matrix.rows)
    return Message(message="Matrix inserted successfully.")
