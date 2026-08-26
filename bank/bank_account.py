import uuid

from bank.abstract_account import AbstractAccount
from bank.account_status import AccountStatus
from bank.currency import Currency
from bank.exceptions import AccountFrozenError, AccountClosedError, InvalidOperationError, InsufficientFundsError


class BankAccount(AbstractAccount):

    def __init__(self, name, balance, currency, status=AccountStatus.ACTIVE, acc_id=None):
        if acc_id is None:
            acc_id = uuid.uuid4().hex[:8]
        super().__init__(acc_id, name, balance, status)
        if Currency.is_allowed(currency):
            self.currency = currency
        else:
            raise InvalidOperationError(f"Недопустимая валюта {currency}")

    def deposit(self, amount):
        self._validate_operation(amount)
        self._balance += amount

    def withdraw(self, amount):
        self._validate_operation(amount)
        if amount > self._balance:
            raise InsufficientFundsError(f"Недостаточно средств {amount}")

        self._balance -= amount

    def _validate_operation(self, amount):
        if self.status is AccountStatus.FROZEN:
            raise AccountFrozenError(f"Аккаунт {self.name} заморожен")

        if self.status is AccountStatus.CLOSED:
            raise AccountClosedError(f"Аккаунт {self.name} закрыт")

        if isinstance(amount, bool) or not isinstance(amount, (int, float)) or amount <= 0:
            raise InvalidOperationError(f"Невалидная сумма {amount}")

    def get_account_info(self):
        return {
            "Номер аккаунта": self.acc_id,
            "Имя": self.name,
            "Баланс": f"{self._balance} {self.currency}",
            "Статус": self.status.value,
        }

    def __str__(self):
        return f"{type(self).__name__} {self.name} {self.acc_id[-4:]} {self.status.value} {self._balance} {self.currency}"
