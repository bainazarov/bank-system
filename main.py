from bank.account_status import AccountStatus
from bank.bank_account import BankAccount
from bank.exceptions import AccountFrozenError, InvalidOperationError, InsufficientFundsError
from bank.investment_account import InvestmentAccount
from bank.premium_account import PremiumAccount
from bank.savings_account import SavingsAccount

############################## BankAccount
acc = BankAccount("Иван", 1000, "RUB")
acc2 = BankAccount("Андрей", 2000, "RUB", AccountStatus.FROZEN)
print("Активный:", acc)
print("Замороженный:", acc2)

try:
    acc2.deposit(1000)
except AccountFrozenError as e:
    print(f"Отказано {e}")

acc.deposit(1000)
acc.withdraw(500)
print(acc.get_account_info())

try:
    BankAccount("Иван", -100, "RUB")
except InvalidOperationError as e:
    print(f"Отклонено: {e}")

try:
    BankAccount("Иван", True, "RUB")
except InvalidOperationError as e:
    print(f"Отклонено: {e}")

try:
    BankAccount("Иван", 1000, "RUB", "FROZEN")
except InvalidOperationError as e:
    print(f"Отклонено: {e}")

try:
    BankAccount("", 1000, "RUB")
except InvalidOperationError as e:
    print(f"Отклонено: {e}")

try:
    BankAccount("Иван", float("nan"), "RUB")
except InvalidOperationError as e:
    print(f"Отклонено: {e}")

try:
    BankAccount("Иван", float("inf"), "RUB")
except InvalidOperationError as e:
    print(f"Отклонено: {e}")

############################## SavingsAccount
savingAcc = SavingsAccount("Иван", 1000, "RUB", min_balance=1000, monthly_interest_rate=0.5)
savingAcc.apply_monthly_interest()
print(savingAcc.get_account_info())

############################## InvestmentAccount
investAcc = InvestmentAccount("Иван", 1000, "RUB")
investAcc.get_account_info()

############################## PremiumAccount
premAcc = PremiumAccount("Иван", 1000, "RUB", overdraft_limit=2000, withdrawal_limit=3000, commission_rate=0.01)
print(premAcc)
try:
    premAcc.withdraw(6000)
except InsufficientFundsError as e:
    print(f"Отказано: {e}")
premAcc.withdraw(2000)
print("После овердрафта:")
print(premAcc.get_account_info())
