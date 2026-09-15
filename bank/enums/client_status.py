from enum import Enum


class ClientStatus(Enum):
    ACTIVE = "ACTIVE"  # Клиент активен
    BLOCKED = "BLOCKED"  # Клиент заблокирован
    SUSPICIOUS = "SUSPICIOUS"  # Клиент под подозрением