import math
from abc import ABC, abstractmethod
from bank.account_status import AccountStatus
from bank.exceptions import InvalidOperationError


class AbstractAccount(ABC):
    def __init__(self, acc_id, name, balance, status=AccountStatus.ACTIVE):
        if not isinstance(acc_id, str) or not acc_id.strip():
            raise InvalidOperationError(f"Недопустимый номер аккаунта {acc_id}")

        if not isinstance(name, str) or not name.strip():
            raise InvalidOperationError(f"Недопустимое имя владельца {name}")

        if isinstance(balance, bool) or not isinstance(balance, (int, float)) or not math.isfinite(balance) or balance < 0:
            raise InvalidOperationError(f"Недопустимый баланс {balance}")

        if not isinstance(status, AccountStatus):
            raise InvalidOperationError(f"Недопустимый статус {status}")

        self.acc_id = acc_id
        self.name = name
        self._balance = balance
        self.status = status

    @abstractmethod
    def deposit(self, amount):
        ...

    @abstractmethod
    def withdraw(self, amount):
        ...

    @abstractmethod
    def get_account_info(self):
        ...