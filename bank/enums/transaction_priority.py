from enum import Enum


class TransactionPriority(Enum):
    LOW = 0  # Низкий
    NORMAL = 1  # Обычный
    HIGH = 2  # Высокий
    URGENT = 3  # Срочный