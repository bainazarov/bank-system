from bank.account_status import AccountStatus
from bank.bank_account import BankAccount
from bank.exceptions import AccountFrozenError, InvalidOperationError

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
