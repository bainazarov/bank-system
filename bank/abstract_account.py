from abc import ABC, abstractmethod
from bank.account_status import AccountStatus
from bank.exceptions import InvalidOperationError
from bank.validation import is_non_empty_string, is_non_negative_number


class AbstractAccount(ABC):
    def __init__(self, acc_id, name, balance, status=AccountStatus.ACTIVE):
        if not is_non_empty_string(acc_id):
            raise InvalidOperationError(f"Недопустимый номер аккаунта {acc_id}")

        if not is_non_empty_string(name):
            raise InvalidOperationError(f"Недопустимое имя владельца {name}")

        if not is_non_negative_number(balance):
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