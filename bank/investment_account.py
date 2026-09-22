import math

from bank.enums.account_status import AccountStatus
from bank.bank_account import BankAccount
from bank.exceptions import InvalidOperationError
from bank.validation import is_positive_number

DEFAULT_PORTFOLIO_RATES = {"stocks": 0.5, "bonds": 0.3, "etf": 0.2}


class InvestmentAccount(BankAccount):

    def __init__(self, name, balance, currency, portfolio=None,
                 status=AccountStatus.ACTIVE, acc_id=None):
        super().__init__(name, balance, currency, status, acc_id)
        if portfolio is None:
            portfolio = {
                asset: rate * self._balance
                for asset, rate in DEFAULT_PORTFOLIO_RATES.items()
            }
        self.portfolio = self._validate_portfolio(portfolio)

    def _validate_portfolio(self, portfolio):
        if not isinstance(portfolio, dict) or not portfolio:
            raise InvalidOperationError(f"Недопустимый портфель {portfolio}")

        for asset, amount in portfolio.items():
            if not is_positive_number(amount):
                raise InvalidOperationError(
                    f"Недопустимая сумма {amount} для актива {asset}")

        if sum(portfolio.values()) > self._balance:
            raise InvalidOperationError(
                "Сумма вложений портфеля превышает баланс счёта")

        return portfolio

    def project_yearly_growth(self, growth_rates):
        if not isinstance(growth_rates, dict) or not growth_rates:
            raise InvalidOperationError(f"Недопустимые ставки роста {growth_rates}")

        total_growth = 0
        for asset, amount in self.portfolio.items():
            rate = growth_rates.get(asset)
            if rate is None:
                raise InvalidOperationError(f"Нет ставки роста для актива {asset}")
            if (not isinstance(rate, (int, float)) or isinstance(rate, bool)
                    or not math.isfinite(rate)):
                raise InvalidOperationError(
                    f"Недопустимая ставка роста {rate} для актива {asset}")
            total_growth += amount * rate
        return total_growth

    def withdraw(self, amount):
        super().withdraw(amount)

    def get_account_info(self):
        return {
            "Номер аккаунта": self.acc_id,
            "Имя": self.name,
            "Баланс": f"{self._balance} {self.currency}",
            "Статус": self.status.value,
            "Портфолио": self.portfolio,
        }

    def __str__(self):
        return (
            f"{type(self).__name__} {self.name} {self.acc_id[-4:]} {self.status.value} {self._balance} {self.currency}"
            f" {self.portfolio}")