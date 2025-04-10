from uuid import UUID

from fastapi import APIRouter, HTTPException
from starlette import status

from app.api.dependencies.deps import CommittedSessionDep, CurrentUser
from app.core.postgres.dao import UserDAO
from app.schemas.types.user_types import UserRole

router = APIRouter(prefix="/mentors", tags=["mentors"])


@router.post("/my_clients/{client_id}")
async def add_mentee(
        client_id: UUID,
        session: CommittedSessionDep,
        current_user: CurrentUser,
):

    if current_user.role not in [UserRole.MENTOR, UserRole.DISTRIBUTOR, UserRole.ADMIN]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only mentors, distributors and admins can add mentees"
        )
    mentee = UserDAO(session).find_one_or_none_by_id(client_id)
    if not mentee:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    if mentee.mentor_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User already has a mentor"
        )

    if mentee.id == current_user.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot add yourself as mentee"
        )
    try:
        UserDAO(session).update(
            filters={"id": mentee.id},
            values={"mentor_id": current_user.id}
        )
        # Increment the current user's mentee counter
        updated_count = current_user.mentees_count + 1
        UserDAO(session).update(
            filters={"id": current_user.id},
            values={"mentees_count": updated_count}
        )
        current_user.mentees_count = updated_count

        return {
            "message": f"User {mentee.username} (ID: {mentee.id}) "
                       f"successfully added as mentee",
            "mentees_count": current_user.mentees_count
        }

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"failed to add mentee: {e}"
        )