from enum import Enum


class UserRole(str, Enum):
    CLIENT = "client"
    MANAGER = "manager"
    MENTOR = "mentor"
    DISTRIBUTOR = "distributor"
    ADMIN = "admin"


class UserStatus(str, Enum):
    INACTIVE = "inactive"
    ACTIVE = "active"
    PENDING = "pending"
    BLOCKED = "blocked"