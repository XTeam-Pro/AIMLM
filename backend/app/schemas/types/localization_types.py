from enum import Enum


class TimeZoneNames(str, Enum):
    UTC = "UTC"
    GMT = "GMT"
    EST = "Eastern Standard Time"         # UTC−5
    EDT = "Eastern Daylight Time"         # UTC−4
    CST = "Central Standard Time"         # UTC−6
    CDT = "Central Daylight Time"         # UTC−5
    MSK = "Moscow Standard Time"          # UTC+3
    PST = "Pacific Standard Time"         # UTC−8
    PDT = "Pacific Daylight Time"         # UTC−7
    AEST = "Australian Eastern Standard Time"  # UTC+10
    AEDT = "Australian Eastern Daylight Time"  # UTC+11
    BST = "British Summer Time"           # UTC+1
    CET = "Central European Time"         # UTC+1
    CEST = "Central European Summer Time" # UTC+2
    IST = "Indian Standard Time"          # UTC+5:30
    JST = "Japan Standard Time"           # UTC+9

class CurrencyType(str, Enum):
    RUB = "RUB"
    EUR = "EUR"
    KZT = "KZT"
    TRY = "TRY"
    UZS = "UZS"


class CountryEnum(str, Enum):
    USA = "The United States of America"
    RUSSIA = "Russia"
    CANADA = "Canada"
    UK = "United Kingdom"
    AUSTRALIA = "Australia"
    JAPAN = "Japan"
    CHINA = "China"
    FRANCE = "France"
    SPAIN = "Spain"
    MEXICO = "Mexico"
    BRAZIL = "Brazil"
    GERMANY = "Germany"
    ITALY = "Italy"
    SWITZERLAND = "Switzerland"
    INDIA = "India"
    GLOBAL = "Global"
