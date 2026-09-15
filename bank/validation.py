import math


def is_non_negative_number(value):
    return (
            not isinstance(value, bool)
            and isinstance(value, (int, float))
            and math.isfinite(value)
            and value >= 0
    )


def is_positive_number(value):
    return (
            not isinstance(value, bool)
            and isinstance(value, (int, float))
            and math.isfinite(value)
            and value > 0
    )


def is_non_empty_string(value):
    return isinstance(value, str) and bool(value.strip())


def is_valid_age(value):
    return not isinstance(value, bool) and isinstance(value, int) and value >= 18


def is_valid_transaction_type(value):
    from bank.enums.transaction_type import TransactionType
    return isinstance(value, TransactionType)


def is_valid_priority(value):
    from bank.enums.transaction_priority import TransactionPriority
    return isinstance(value, TransactionPriority)


def is_valid_currency(value):
    from bank.enums.currency import Currency
    return is_non_empty_string(value) and Currency.is_allowed(value)


def is_valid_execute_at(value):
    from datetime import datetime
    return value is None or isinstance(value, datetime)


def is_valid_retries(value):
    return isinstance(value, int) and value > 0


def is_valid_commission_rate(value):
    return (
        not isinstance(value, bool)
        and isinstance(value, (int, float))
        and math.isfinite(value)
        and value >= 0
    )