from enum import Enum

class AccountStatus(Enum):
    ACTIVE = "ACTIVE"  # Счёт активен
    FROZEN = "FROZEN"  # Счёт заморожен
    CLOSED = "CLOSED"  # Счёт закрыт