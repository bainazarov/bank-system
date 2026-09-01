from bank.bank_account import BankAccount
from bank.exceptions import InsufficientFundsError


class PremiumAccount(BankAccount):
    def __init__(self, name, balance, currency, overdraft_limit, withdrawal_limit, commission_rate):
        super().__init__(name, balance, currency)
        self.overdraft_limit = overdraft_limit
        self.withdrawal_limit = withdrawal_limit
        self.commission_rate = commission_rate


    def withdraw(self, amount):
        super()._validate_operation(amount)

        if amount > self.withdrawal_limit:
            raise InsufficientFundsError(f"Сумма {amount} превышает максимальную сумму за раз")

        total = amount + amount * self.commission_rate
        if total > self._balance + self.overdraft_limit:
            raise InsufficientFundsError(f"Сумма {total} превышает максимальную сумму за раз")

        self._balance -= total


    def get_account_info(self):
        return {
            "Номер аккаунта": self.acc_id,
            "Имя": self.name,
            "Баланс": f"{self._balance} {self.currency}",
            "Статус": self.status.value,
            "Лимит овердрафта": self.overdraft_limit,
            "Максимальная сумма снятия за раз": self.withdrawal_limit,
            "Комиссия": self.commission_rate
        }


    def __str__(self):
        return (
            f"{type(self).__name__} {self.name} {self.acc_id[-4:]} {self.status.value} {self._balance} {self.currency}"
            f" {self.overdraft_limit} {self.withdrawal_limit} {self.commission_rate}")
