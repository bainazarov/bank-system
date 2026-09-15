from enum import Enum


class TransactionStatus(Enum):
    PENDING = "PENDING"  # Ожидает обработки
    PROCESSING = "PROCESSING"  # В обработке
    COMPLETED = "COMPLETED"  # Выполнена
    FAILED = "FAILED"  # Отклонена
    CANCELLED = "CANCELLED"  # Отменена