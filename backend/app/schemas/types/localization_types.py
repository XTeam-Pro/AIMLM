from enum import Enum


class TimeZoneNames(str, Enum):
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


class CurrencyType(str, Enum):
    RUB = "RUB"
    EUR = "EUR"
    KZT = "KZT"
    TRY = "TRY"
    UZS = "UZS"
