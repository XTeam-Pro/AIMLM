from enum import Enum


class AchievementTier(str, Enum):
    BRONZE = "bronze"
    SILVER = "silver"
    GOLD = "gold"
    PLATINUM = "platinum"

class LeaderboardType(str, Enum):
    SALES = "sales"
    RECRUITING = "recruiting"
    ACTIVITY = "activity"

class LeaderboardPeriod(str, Enum):
    DAILY = "daily"
    WEEKLY = "weekly"
    MONTHLY = "monthly"
    ALL_TIME = "all_time"

class ChallengeStatus(str, Enum):
    UPCOMING = "upcoming"
    ACTIVE = "active"
    COMPLETED = "completed"

class ChallengeType(str, Enum):
    PERSONAL = "personal"
    TEAM = "team"
    COMPANY_WIDE = "company_wide"


class BonusType(str, Enum):
    """Detailed bonus types used when TransactionType=BONUS"""
    MENTOR = "mentor"                # Mentor performance bonus
    RETAIL = "retail"                # Retail profit premium
    ACCUMULATIVE = "accumulative"    # Accumulated volume bonus
    BINARY = "binary"                # Binary structure bonus
    DEVELOPMENT = "development"      # Network development bonus
    SPONSOR = "sponsor"              # Direct sponsorship bonus
    MATCHING = "matching"            # Matching bonus from downline
    LEADERSHIP = "leadership"        # Leadership level achievement

class RankType(str, Enum):
    NEWBIE = "newbie"
    MIDDLE = "middle"
    SENIOR = "senior"
    LEADER = "leader"