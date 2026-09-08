class AccountFrozenError(Exception):
    """Аккаунт заморожен"""

class AccountClosedError(Exception):
    """Аккаунт закрыт"""

class InvalidOperationError(Exception):
    """Недопустимая операция"""

class InsufficientFundsError(Exception):
    """Недостаточно средств"""

class ClientNotFoundError(Exception):
    """Клиент не найден"""

class AccountNotFoundError(Exception):
    """Счёт не найден"""

class ClientBlockedError(Exception):
    """Клиент заблокирован"""

class AuthenticationError(Exception):
    """Ошибка аутентификации"""

class NightOperationsError(Exception):
    """Операции запрещены ночью"""