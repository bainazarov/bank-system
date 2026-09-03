from bank.account_status import AccountStatus
from bank.bank_account import BankAccount
from bank.exceptions import InvalidOperationError
from bank.validation import is_non_negative_number


class InvestmentAccount(BankAccount):
    EXPECTED_GROWTH = {"stocks": 0.10, "bonds": 0.04, "etf": 0.07}

    def __init__(self, name, balance, currency, portfolio=None,
                 status=AccountStatus.ACTIVE, acc_id=None):
        super().__init__(name, balance, currency, status, acc_id)
        if portfolio is None:
            portfolio = {
                "stocks": 0.5,
                "bonds": 0.3,
                "etf": 0.2
            }
        self.portfolio = self._validate_portfolio(portfolio)

    @classmethod
    def _validate_portfolio(cls, portfolio):
        if not isinstance(portfolio, dict) or not portfolio:
            raise InvalidOperationError(f"Недопустимый портфель {portfolio}")

        for active, share in portfolio.items():
            if active not in cls.EXPECTED_GROWTH:
                raise InvalidOperationError(f"Неизвестный актив {active}")
            if not is_non_negative_number(share):
                raise InvalidOperationError(f"Недопустимая доля {share} для актива {active}")

        if sum(portfolio.values()) != 1.0:
            raise InvalidOperationError("Сумма долей портфеля должна быть равна 1")

        return portfolio

    def project_yearly_growth(self, years=1):
        total_growth = 0
        for active in self.portfolio:
            total_growth += self.portfolio[active] * self.EXPECTED_GROWTH[active]
        return self._balance * (1 + total_growth) ** years

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
