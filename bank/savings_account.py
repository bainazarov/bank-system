from bank.bank_account import BankAccount
from bank.exceptions import InsufficientFundsError


class SavingsAccount(BankAccount):
    def __init__(self, name, balance, currency, min_balance, monthly_interest_rate):
        super().__init__(name, balance, currency)
        self.min_balance = min_balance
        self.monthly_interest_rate = monthly_interest_rate


    def withdraw(self, amount):
        if amount > self._balance - self.min_balance:
            raise InsufficientFundsError(f"Недостаточно средств {amount}")

        super().withdraw(amount)


    def apply_monthly_interest(self):
        self._balance += self._balance * self.monthly_interest_rate


    def get_account_info(self):
        return {
            "Номер аккаунта": self.acc_id,
            "Имя": self.name,
            "Баланс": f"{self._balance} {self.currency}",
            "Статус": self.status.value,
            "Минимальный баланс": self.min_balance,
            "Месячная ставка": self.monthly_interest_rate
        }


    def __str__(self):
        return (
            f"{type(self).__name__} {self.name} {self.acc_id[-4:]} {self.status.value} {self._balance} {self.currency}"
            f" {self.min_balance} {self.monthly_interest_rate}")
