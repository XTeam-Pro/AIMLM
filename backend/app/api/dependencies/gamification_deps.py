from datetime import timezone, datetime, timedelta

from sqlmodel import Session

from app.core.postgres.dao import UserDAO, UserAchievementDAO, UserChallengeDAO, TransactionDAO
from app.schemas.types.gamification_types import LeaderboardPeriod
from app.schemas.types.common_types import TransactionType

def get_period_filter(period: LeaderboardPeriod) -> tuple | None:
    """Helper to create time filter based on period"""
    now = datetime.now(timezone.utc)
    if period == LeaderboardPeriod.DAILY:
        return "ge", now - timedelta(days=1)
    elif period == LeaderboardPeriod.WEEKLY:
        return "ge", now - timedelta(weeks=1)
    elif period == LeaderboardPeriod.MONTHLY:
        return "ge", now - timedelta(days=30)
    return None


def get_recruiting_leaderboard(session: Session, limit: int, time_filter: tuple | None = None):
    """Leaderboard by recruiting (Sort by mentees_count)"""
    user_dao = UserDAO(session)

    filters = {}
    if time_filter:
        # if it is necessary to take into account only new mentees within the period
        filters["registration_date"] = time_filter

    # Sorted by descending number of mentees
    users = user_dao.find_all(
        filters=filters,
        order_by="-mentees_count",
        limit=limit
    )

    return [
        {
            "user_id": user.id,
            "username": user.username,
            "score": user.mentees_count,
            "metric": "mentees_count"
        }
        for user in users
    ]


def get_sales_leaderboard(session: Session, limit: int, time_filter: tuple | None = None):
    """Leaderboard by sales (Sort by sales amount)"""
    transaction_dao = TransactionDAO(session)

    filters = {"transaction_type": TransactionType.SALE}
    if time_filter:
        filters["created_at"] = time_filter

    # Group by user_id and sum up by amount
    sales_data = transaction_dao.find_all(
        filters=filters,
        order_by="-total_amount",
        limit=limit
    )

    # Additionally get a user data
    user_ids = [item.user_id for item in sales_data]
    users = UserDAO(session).find_all(filters={"id": ("in", user_ids)})
    user_map = {user.id: user for user in users}

    return [
        {
            "user_id": item["user_id"],
            "username": user_map.get(item["user_id"]).username if item["user_id"] in user_map else None,
            "score": item["total_amount"],
            "metric": "sales_amount"
        }
        for item in sales_data
    ]


def get_activity_leaderboard(session: Session, limit: int, time_filter: tuple | None =None):
    """
    Getting leaderboard by activity (Combination of transactions, achievements and challenges)
    """
    transaction_dao = TransactionDAO(session)
    challenge_dao = UserChallengeDAO(session)
    achievement_dao = UserAchievementDAO(session)
    user_dao = UserDAO(session)

    # 1. Helper function for manual aggregation
    def aggregate_data(items, group_key, sum_field):
        result = {}
        for it in items:
            key = getattr(it, group_key)
            result[key] = result.get(key, 0) + getattr(it, sum_field)
        return [{"user_id": k, "total_amount": v} for k, v in result.items()]

    # 2. Get transaction data
    transaction_filters = {
        "transaction_type": ("not_in", [TransactionType.CASH_OUT, TransactionType.PENALTY])
    }
    if time_filter:
        transaction_filters["created_at"] = time_filter

    transactions = transaction_dao.find_all(filters=transaction_filters, limit=limit)
    transaction_data = aggregate_data(transactions, "user_id", "pv_amount")  # or "cash_amount"

    # 3. Get challenge data
    challenge_filters = {"status": "completed"}
    if time_filter:
        challenge_filters["completed_at"] = time_filter

    challenges = challenge_dao.find_all(filters=challenge_filters)
    challenge_data = aggregate_data(challenges, "user_id", "progress")

    # 4. Get achievement data
    achievement_filters = {"is_unlocked": True}
    if time_filter:
        achievement_filters["unlocked_at"] = time_filter

    achievements = achievement_dao.find_all(filters=achievement_filters)
    # Count achievements per user
    achievement_counts = {}
    for ach in achievements:
        achievement_counts[ach.user_id] = achievement_counts.get(ach.user_id, 0) + 1
    achievement_data = [{"user_id": k, "achievement_count": v} for k, v in achievement_counts.items()]

    # 5. Combine all metrics with weights
    combined_scores = {}

    # Transaction (weight 40%)
    for item in transaction_data:
        user_id = item["user_id"]
        combined_scores[user_id] = combined_scores.get(user_id, 0) + item["total_amount"] * 0.4

    # Challenges (weight 35%)
    for item in challenge_data:
        user_id = item["user_id"]
        combined_scores[user_id] = combined_scores.get(user_id, 0) + item["total_amount"] * 0.35

    # Achievements (weight 25%)
    for item in achievement_data:
        user_id = item["user_id"]
        combined_scores[user_id] = combined_scores.get(user_id, 0) + item["achievement_count"] * 0.25

    # 6. Sort and prepare results
    sorted_users = sorted(combined_scores.items(), key=lambda x: x[1], reverse=True)
    user_ids = [user_id for user_id, _ in sorted_users]
    users = user_dao.find_all(filters={"id": ("in", user_ids)})
    user_map = {user.id: user for user in users}

    return [
        {
            "user_id": user_id,
            "username": user_map[user_id].username if user_id in user_map else "Unknown",
            "score": round(score, 2),
            "details": {
                "transactions": next((t["total_amount"] for t in transaction_data if t["user_id"] == user_id), 0),
                "challenges": next((c["total_amount"] for c in challenge_data if c["user_id"] == user_id), 0),
                "achievements": next((a["achievement_count"] for a in achievement_data if a["user_id"] == user_id), 0)
            }
        }
        for user_id, score in sorted_users
    ]