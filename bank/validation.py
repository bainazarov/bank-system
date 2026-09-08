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