class AccountFrozenError(Exception):
    """Аккаунт заморожен"""

class AccountClosedError(Exception):
    """Аккаунт закрыт"""

class InvalidOperationError(Exception):
    """Недопустимая операция"""

class InsufficientFundsError(Exception):
    """Недостаточно средств"""