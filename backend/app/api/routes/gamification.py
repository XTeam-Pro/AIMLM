import logging
from datetime import datetime, timezone
from fastapi import APIRouter, HTTPException, status
from typing import List
from uuid import UUID

from app.api.dependencies.deps import CurrentUser, CommittedSessionDep, UncommittedSessionDep
from app.api.dependencies.gamification_deps import (
    get_recruiting_leaderboard, get_sales_leaderboard, get_activity_leaderboard, get_period_filter
)
from app.core.postgres.dao import AchievementDAO, UserAchievementDAO, ChallengeDAO
from app.schemas.gamification import ChallengePublic, ChallengeCreate, AchievementPublic, AchievementCreate, \
    UserAchievementPublic
from app.schemas.types.gamification_types import LeaderboardPeriod, LeaderboardType

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

router = APIRouter(tags=["Gamification"], prefix="/gamification")




@router.get("/achievements", response_model=List[AchievementPublic])
def get_all_achievements(current_user: CurrentUser, session: UncommittedSessionDep, include_secret: bool = False):
    """Get all achievements (admin only)."""
    if current_user.role != "admin":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not enough privileges")

    filters = {} if include_secret else {"is_secret": False}
    achievements = AchievementDAO(session).find_all(filters=filters)
    return [AchievementPublic.model_validate(ach) for ach in achievements]


@router.post("/achievements/create", response_model=AchievementPublic)
def create_achievement(achievement_data: AchievementCreate, current_user: CurrentUser, session: CommittedSessionDep):
    """Create a new achievement (admin only)."""
    if current_user.role != "admin":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not enough privileges")

    if AchievementDAO(session).find_one_or_none(filters={"name": achievement_data.name}):
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Achievement already exists")

    new_achievement = AchievementDAO(session).add(achievement_data)
    return AchievementPublic.model_validate(new_achievement)


@router.get("/achievements/{user_id}", response_model=List[UserAchievementPublic])
def get_user_achievements(user_id: UUID, current_user: CurrentUser, session: UncommittedSessionDep):
    """Get all achievements of a user (admin or self)."""
    if user_id != current_user.id and current_user.role != "admin":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Insufficient privileges")

    user_achievements = UserAchievementDAO(session).find_all(filters={"user_id": user_id})
    if not user_achievements:
        return []

    achievement_ids = {ua.achievement_id for ua in user_achievements}
    achievements = AchievementDAO(session).find_all(filters={"id": ("in", achievement_ids)})
    achievement_map = {a.id: a for a in achievements}

    return [
        UserAchievementPublic(
            id=ua.id,
            user_id=ua.user_id,
            progress=ua.progress,
            unlocked_at=ua.unlocked_at,
            is_unlocked=ua.is_unlocked,
            achievement_id=ua.achievement_id,
            achievement=AchievementPublic.model_validate(achievement_map[ua.achievement_id])
        )
        for ua in user_achievements if ua.achievement_id in achievement_map
    ]


@router.patch("/achievements/{user_achievement_id}/unlock")
def toggle_unlock(user_achievement_id: UUID, unlock: bool, current_user: CurrentUser, session: CommittedSessionDep):
    """Toggle unlock status for an achievement (admin only)."""
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Admin only")

    user_achievement = UserAchievementDAO(session).find_one_or_none_by_id(user_achievement_id)
    if not user_achievement:
        raise HTTPException(status_code=404, detail="Not found")

    values = {"is_unlocked": unlock, "unlocked_at": datetime.now(timezone.utc) if unlock else None}
    UserAchievementDAO(session).update(filters={"id": user_achievement_id}, values=values)
    return {"status": "updated"}


@router.patch("/achievements/{user_id}/{achievement_id}/progress", response_model=UserAchievementPublic)
def update_achievement_progress(user_id: UUID, achievement_id: UUID, progress: float, current_user: CurrentUser, session: CommittedSessionDep):
    """
    Update achievement progress for a user (admin only)
    - Automatically unlocks if progress reaches required points
    - Creates new UserAchievement record if it doesn't exist
    """
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Admin only")

    achievement = AchievementDAO(session).find_one_or_none_by_id(achievement_id)
    if not achievement:
        raise HTTPException(status_code=404, detail="Achievement not found")

    user_achievement = UserAchievementDAO(session).find_one_or_none(filters={"user_id": user_id, "achievement_id": achievement_id})

    update_values = {"progress": progress}
    if progress >= float(achievement.points_required):
        update_values.update({"is_unlocked": True, "unlocked_at": datetime.now(timezone.utc)})

    if user_achievement:
        updated = UserAchievementDAO(session).update(filters={"id": user_achievement.id}, values=update_values)
    else:
        update_values.update({"user_id": user_id, "achievement_id": achievement_id})
        updated = UserAchievementDAO(session).add(update_values)

    return UserAchievementPublic.model_validate(updated)


@router.get("/leaderboards/{leaderboard_type}/{period}", response_model=List[dict])
def get_leaderboard(leaderboard_type: LeaderboardType, limit: int, period: LeaderboardPeriod, current_user: CurrentUser, session: UncommittedSessionDep):
    """Get leaderboard by type and time period with custom sorting for each type"""
    if not current_user:
        raise HTTPException(status_code=401, detail="Not authenticated")

    try:
        time_filter = get_period_filter(period) if period != LeaderboardPeriod.ALL_TIME else None

        if leaderboard_type == LeaderboardType.RECRUITING:
            return get_recruiting_leaderboard(session, limit, time_filter)
        elif leaderboard_type == LeaderboardType.SALES:
            return get_sales_leaderboard(session, limit, time_filter)
        elif leaderboard_type == LeaderboardType.ACTIVITY:
            return get_activity_leaderboard(session, limit, time_filter)
        return []

    except Exception as e:
        logger.error(f"Error fetching leaderboard: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to retrieve leaderboard")


@router.post("/challenges", response_model=ChallengePublic)
def create_challenge(challenge_data: ChallengeCreate, current_user: CurrentUser, session: CommittedSessionDep):
    """Create a new challenge (admin only)"""
    if current_user.role != "admin":
        raise HTTPException(status_code=401, detail="Admin only")

    if ChallengeDAO(session).find_one_or_none({"name": challenge_data.name}):
        raise HTTPException(status_code=409, detail="Challenge already exists")
    challenge_dict = challenge_data.model_dump(exclude={"created_by"})
    challenge_dict["created_by"] = current_user.id
    challenge = ChallengeDAO(session).add(challenge_dict)
    return ChallengePublic.model_validate(challenge)


@router.get("/challenges", response_model=List[ChallengePublic])
def get_active_challenges(current_user: CurrentUser, session: UncommittedSessionDep):
    """Get list of active challenges"""
    if not current_user:
        raise HTTPException(status_code=401, detail="Not authenticated")

    challenges = ChallengeDAO(session).find_all(filters={"is_active": True})
    return [ChallengePublic.model_validate(ch) for ch in challenges]