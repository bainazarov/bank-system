from enum import Enum


class RiskLevel(Enum):
    LOW = 10  # Низкий риск
    MEDIUM = 20  # Средний риск
    HIGH = 30  # Высокий риск — операция блокируется

    @property
    def label(self):
        return {
            RiskLevel.LOW: "Низкий",
            RiskLevel.MEDIUM: "Средний",
            RiskLevel.HIGH: "Высокий",
        }[self]