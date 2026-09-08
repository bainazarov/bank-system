from bank.account_status import AccountStatus
from bank.bank import Bank
from bank.bank_account import BankAccount
from bank.client import Client
from bank.exceptions import (
    AccountFrozenError,
    AuthenticationError,
    InvalidOperationError,
    InsufficientFundsError,
    NightOperationsError,
)
from bank.investment_account import InvestmentAccount
from bank.premium_account import PremiumAccount
from bank.savings_account import SavingsAccount
from datetime import datetime


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
premAcc = PremiumAccount("Иван", 1000, "RUB", overdraft_limit=2000, withdrawal_limit=3000, fixed_commission=20)
print(premAcc)
try:
    premAcc.withdraw(6000)
except InsufficientFundsError as e:
    print(f"Отказано: {e}")
premAcc.withdraw(2000)
print("После овердрафта:")
print(premAcc.get_account_info())

############################## Bank + Client

bank = Bank("Tinkoff")

ivan = Client("Иван Петров", "C-001", 25, "qwerty", phone="+7-900-000-00-00")
bank.add_client(ivan)
account = BankAccount("Иван Петров", 50000, "RUB")
bank.open_account("C-001", account)
print("Открыт:", account)

bank.unfreeze_account("C-001", account.acc_id)
bank.freeze_account("C-001", account.acc_id)
bank.close_account("C-001", account.acc_id)
print("Статус счёта после freeze/close:", account.status.value)

print("Аутентификация:", bank.authenticate_client("C-001", "qwerty"))
print("Поиск 'петров':", [a.acc_id for a in bank.search_accounts("петров")])
print("Итого по валютам:", bank.get_total_balance())
print("Рейтинг:", [c.full_name for c in bank.get_clients_ranking()])

bank.flag_suspicious("C-001", "3 вывода за минуту")
print("Статус клиента:", ivan.status.value, "| События:", bank.suspicious_events)

for attempt in range(3):
    try:
        bank.authenticate_client("C-001", "wrong")
    except AuthenticationError as e:
        print(f"  Неверный вход {attempt + 1}: {e}")
print("Статус после 3 попыток:", ivan.status.value)

night_bank = Bank("NightBank", clock=lambda: datetime(2026, 9, 8, 3, 0))
night_bank.add_client(ivan)
try:
    night_bank.open_account("C-001", BankAccount("Иван Петров", 1000, "RUB"))
except NightOperationsError as e:
    print("Ночь:", e)
