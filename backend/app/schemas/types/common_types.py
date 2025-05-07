from enum import Enum

class ContractType(str, Enum):
    BASIC = "Basic"
    STARTUP = "StartUP"
    BUSINESS = "Business"

class ActivityType(str, Enum):
    BONUS = "Bonus"
    ACCUMULATIVE = "Accumulation"

class TransactionStatus(str, Enum):
    PENDING = "pending"
    FAILED = "failed"
    COMPLETED = "completed"

# To distinguish ranks in MLM  (extended list) and gamification (simplified list)
class MLMRankType(str, Enum):
    NEWBIE = "Distributor"
    BRONZE = "BRONZE"
    SILVER = "SILVER"
    GOLD = "GOLD"
    CARAT_1 = "1 CARAT"
    CARAT_2 = "2 CARAT"
    CARAT_3 = "3 CARAT"
    CRYSTAL = "CRYSTAL"
    RUBIN = "RUBIN"
    SAPPHIRE = "SAPPHIRE"
    EMERALD = "EMERALD"
    DIAMOND = "DIAMOND"
    BLACK_DIAMOND = "BLACK DIAMOND STAR"
    RED_DIAMOND = "RED DIAMOND STAR"
    GREEN_DIAMOND = "GREEN DIAMOND STAR"
    BLUE_DIAMOND = "BLUE DIAMOND STAR"
    VIOLET_DIAMOND = "VIOLET DIAMOND STAR"
    PURPLE_DIAMOND = "PURPLE DIAMOND STAR"

# Other ranks for gamification


class ProductCategory(str, Enum):
    COSMETICS = "cosmetics"
    NUTRITION = "nutrition"
    COURSE = "course"
    WEBINAR = "webinar"
    COLLECTION = "collection"

class InteractionType(str, Enum):
    CART_ADD = "cart_add"
    FAVORITE = "favorite"
    WEBINAR_REGISTER = "webinar_register"
    WEBINAR_ATTEND = "webinar_attend"
    ACHIEVEMENT_UNLOCK = "achievement_unlock"


class TransactionType(str, Enum):
    """Actual financial transactions in the MLM system."""

    PRODUCT_PURCHASE = "product_purchase"
    NETWORK_SALE = "network_sale"

    # Finances
    CASH_WITHDRAWAL = "cash_withdrawal"
    CASH_DEPOSIT = "cash_deposit"
    BALANCE_TRANSFER = "balance_transfer"

    # System retention
    SYSTEM_FEE = "system_fee"


