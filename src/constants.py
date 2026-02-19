from enum import Enum


class MonthFilter(Enum):
    ALL = "Alle maanden"


class Label(Enum):
    GEEN = "Geen label"


class Zakelijkheid(Enum):
    ALL = "Alle"
    BUSINESS = "Zakelijk"
    NON_BUSINESS = "Niet-zakelijk"
