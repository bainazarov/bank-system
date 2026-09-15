from bank.enums.currency import Currency
from bank.exceptions import InvalidOperationError
from bank.validation import is_valid_currency


class ExchangeRates:
    RATES_TO_RUB = {
        Currency.USD.value: 92.0,
        Currency.EUR.value: 100.0,
        Currency.RUB.value: 1.0,
        Currency.CNY.value: 12.8,
        Currency.KZT.value: 0.19,
    }

    @classmethod
    def convert(cls, amount, from_currency, to_currency):
        if not is_valid_currency(from_currency) or not is_valid_currency(to_currency):
            raise InvalidOperationError(f"Недопустимая валюта {from_currency} -> {to_currency}")

        if from_currency == to_currency:
            return amount

        if from_currency not in cls.RATES_TO_RUB or to_currency not in cls.RATES_TO_RUB:
            raise InvalidOperationError(f"Нет курса для {from_currency} -> {to_currency}")

        value = amount * cls.RATES_TO_RUB[from_currency] / cls.RATES_TO_RUB[to_currency]
        return round(value, 2)