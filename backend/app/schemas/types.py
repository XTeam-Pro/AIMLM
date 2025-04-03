from enum import Enum


class UserRole(str, Enum):
    CLIENT = "client"
    MANAGER = "manager"
    MENTOR = "mentor"
    DISTRIBUTOR = "distributor"
    ADMIN = "admin"


from enum import Enum


class TimeZoneNames(str, Enum):
    """Enumeration of common time zone names with their string values."""
    UTC = "UTC"
    GMT = "GMT"
    EST = "Eastern Standard Time"
    EDT = "Eastern Daylight Time"
    CST = "Central Standard Time"
    CDT = "Central Daylight Time"
    MST = "Mountain Standard Time"
    MDT = "Mountain Daylight Time"
    PST = "Pacific Standard Time"
    PDT = "Pacific Daylight Time"
    AEST = "Australian Eastern Standard Time"
    AEDT = "Australian Eastern Daylight Time"
    BST = "British Summer Time"
    CET = "Central European Time"
    CEST = "Central European Summer Time"
    IST = "Indian Standard Time"
    JST = "Japan Standard Time"


class UserStatus(str, Enum):
    INACTIVE = "inactive"
    ACTIVE = "active"
    PENDING = "pending"
    BLOCKED = "blocked"


class ProductCategory(str, Enum):
    COSMETICS = "cosmetics"
    NUTRITION = "nutrition"
    COURSE = "course"
    WEBINAR = "webinar"
    COLLECTION = "collection"


class InteractionType(str, Enum):
    PURCHASE = "purchase"
    CART_ADD = "cart_add"
    FAVORITE = "favorite"
    WEBINAR_REGISTER = "webinar_register"
    WEBINAR_ATTEND = "webinar_attend"
    ACHIEVEMENT_UNLOCK = "achievement_unlock"


class TransactionType(str, Enum):
    PURCHASE = "purchase"   # Покупка товара (cash_amount < 0, pv_amount > 0)
    BONUS = "bonus"         # Бонус за активность (cash_amount = 0, pv_amount > 0)
    PENALTY = "penalty"     # Штраф (cash_amount = 0, pv_amount < 0)
    ACHIEVEMENT = "achievement"  # Награда за достижение
    REFERRAL = "referral"   # Реферальный бонус (cash_amount > 0)
    CASH_OUT = "cash_out"   # Вывод средств (cash_amount < 0)
    CASH_IN = "cash_in"     # Пополнение баланса (cash_amount > 0)


class TransactionStatus(str, Enum):
    PENDING = "pending"
    FAILED = "failed"
    COMPLETED = "completed"