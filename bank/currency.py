from enum import Enum

class Currency(Enum):
    USD = "USD"
    EUR = "EUR"
    RUB = "RUB"
    CNY = "CNY"
    KZT = "KZT"

    @classmethod
    def is_allowed(cls, value):
        return value in [c.value for c in cls]
