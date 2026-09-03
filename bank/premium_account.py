from bank.account_status import AccountStatus
from bank.bank_account import BankAccount
from bank.exceptions import InsufficientFundsError, InvalidOperationError
from bank.validation import is_non_negative_number


class PremiumAccount(BankAccount):
    def __init__(self, name, balance, currency, overdraft_limit, withdrawal_limit, fixed_commission,
                 status=AccountStatus.ACTIVE, acc_id=None):
        super().__init__(name, balance, currency, status, acc_id)
        if not is_non_negative_number(overdraft_limit):
            raise InvalidOperationError(f"Недопустимый лимит овердрафта {overdraft_limit}")
        if not is_non_negative_number(withdrawal_limit):
            raise InvalidOperationError(f"Недопустимый лимит снятия {withdrawal_limit}")
        if not is_non_negative_number(fixed_commission):
            raise InvalidOperationError(f"Недопустимая фиксированная комиссия {fixed_commission}")
        self.overdraft_limit = overdraft_limit
        self.withdrawal_limit = withdrawal_limit
        self.fixed_commission = fixed_commission


    def withdraw(self, amount):
        super()._validate_operation(amount)

        if amount > self.withdrawal_limit:
            raise InsufficientFundsError(f"Сумма {amount} превышает максимальную сумму за раз")

        total = amount + self.fixed_commission
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
            "Фиксированная комиссия": self.fixed_commission
        }


    def __str__(self):
        return (
            f"{type(self).__name__} {self.name} {self.acc_id[-4:]} {self.status.value} {self._balance} {self.currency}"
            f" {self.overdraft_limit} {self.withdrawal_limit} {self.fixed_commission}")
