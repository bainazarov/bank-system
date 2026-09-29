from datetime import datetime, timedelta

from bank.audit_log import AuditLog
from bank.bank import Bank
from bank.bank_account import BankAccount
from bank.client import Client
from bank.enums.account_status import AccountStatus
from bank.enums.transaction_type import TransactionType
from bank.exceptions import HighRiskTransactionError
from bank.investment_account import InvestmentAccount
from bank.premium_account import PremiumAccount
from bank.report_builder import ReportBuilder
from bank.risk_analyzer import RiskAnalyzer
from bank.savings_account import SavingsAccount
from bank.transaction import Transaction
from bank.transaction_processor import TransactionProcessor
from bank.transaction_queue import TransactionQueue

current_time = datetime(2026, 9, 21, 10, 0)


def clock():
    return current_time


def advance(**kwargs):
    global current_time
    current_time += timedelta(**kwargs)


analyzer = RiskAnalyzer(clock=clock)
audit = AuditLog(clock=clock, file_path="day7_demo.json")
bank = Bank("Тинькофф", clock=clock, risk_analyzer=analyzer, audit_log=audit)

for name, client_id, age in [
    ("Иван", "C-001", 34),
    ("Ольга", "C-002", 29),
    ("Захар", "C-003", 41),
    ("Мария", "C-004", 38),
    ("Пётр", "C-005", 45),
    ("Анна", "C-006", 31),
]:
    bank.add_client(Client(name, client_id, age, "123"))

ivan = BankAccount("Иван", 1_200_000, "RUB")
ivan_sav = SavingsAccount("Иван", 400_000, "RUB", min_balance=50_000, monthly_interest_rate=0.15)
olga = BankAccount("Ольга", 500_000, "RUB")
olga_inv = InvestmentAccount("Ольга", 900_000, "RUB")
zakhar = PremiumAccount("Захар", 600_000, "RUB", overdraft_limit=100_000,
                        withdrawal_limit=250_000, fixed_commission=0)
maria = BankAccount("Мария", 700_000, "RUB", status=AccountStatus.FROZEN)
petr = BankAccount("Пётр", 8_000, "USD")
anna = BankAccount("Анна", 350_000, "RUB")
anna_inv = InvestmentAccount("Анна", 250_000, "RUB")

for client_id, accounts in {
    "C-001": [ivan, ivan_sav],
    "C-002": [olga, olga_inv],
    "C-003": [zakhar],
    "C-004": [maria],
    "C-005": [petr],
    "C-006": [anna, anna_inv],
}.items():
    for account in accounts:
        bank.open_account(client_id, account)

operations = [
    (10, "Иван -> Ольга 50 000 RUB",
     Transaction(TransactionType.TRANSFER, 50_000, "RUB", sender=ivan, receiver=olga)),
    (15, "Ольга -> Иван 20 000 RUB",
     Transaction(TransactionType.TRANSFER, 20_000, "RUB", sender=olga, receiver=ivan)),
    (20, "Иван -> ООО «Мечта» 3 000 RUB",
     Transaction(TransactionType.PAYMENT, 3_000, "RUB", sender=ivan, receiver="ООО «Мечта»")),
    (25, "Пополнение счёта Ольги 100 000 RUB",
     Transaction(TransactionType.DEPOSIT, 100_000, "RUB", receiver=olga)),
    (30, "Пётр -> Иван 1 000 USD",
     Transaction(TransactionType.TRANSFER, 1_000, "USD", sender=petr, receiver=ivan)),
    (35, "Иван -> Пётр 900 USD",
     Transaction(TransactionType.TRANSFER, 900, "USD", sender=ivan, receiver=petr)),
    (40, "Захар -> ООО «ЖКХ» 12 000 RUB",
     Transaction(TransactionType.PAYMENT, 12_000, "RUB", sender=zakhar, receiver="ООО «ЖКХ»")),
    (45, "Иван(сбер) -> Анна 60 000 RUB",
     Transaction(TransactionType.TRANSFER, 60_000, "RUB", sender=ivan_sav, receiver=anna)),
    (50, "Анна -> ООО «ЖКХ» 7 000 RUB",
     Transaction(TransactionType.PAYMENT, 7_000, "RUB", sender=anna, receiver="ООО «ЖКХ»")),
    (55, "Анна(инв) -> Ольга 40 000 RUB",
     Transaction(TransactionType.TRANSFER, 40_000, "RUB", sender=anna_inv, receiver=olga)),
    (60, "Ольга(инв) -> Иван 150 000 RUB",
     Transaction(TransactionType.TRANSFER, 150_000, "RUB", sender=olga_inv, receiver=ivan)),
    (65, "Снятие Ольги 80 000 RUB",
     Transaction(TransactionType.WITHDRAWAL, 80_000, "RUB", sender=olga)),
    (70, "Пополнение счёта Анны 250 000 RUB",
     Transaction(TransactionType.DEPOSIT, 250_000, "RUB", receiver=anna)),
    (75, "Иван -> ООО «Мечта» 180 000 RUB — крупный платёж",
     Transaction(TransactionType.PAYMENT, 180_000, "RUB", sender=ivan, receiver="ООО «Мечта»")),
    (80, "Иван -> ООО «Мечта» 175 000 RUB — второй крупный подряд",
     Transaction(TransactionType.PAYMENT, 175_000, "RUB", sender=ivan, receiver="ООО «Мечта»")),
    (85, "Иван -> ООО «Мечта» 190 000 RUB — третий крупный подряд",
     Transaction(TransactionType.PAYMENT, 190_000, "RUB", sender=ivan, receiver="ООО «Мечта»")),
    (90, "Мария -> Ольга 30 000 RUB — счёт заморожен",
     Transaction(TransactionType.TRANSFER, 30_000, "RUB", sender=maria, receiver=olga)),
    (95, "Пётр -> ООО «Магазин» 1 200 USD",
     Transaction(TransactionType.PAYMENT, 1_200, "USD", sender=petr, receiver="ООО «Магазин»")),
    (100, "Захар -> Иван(сбер) 200 000 RUB",
     Transaction(TransactionType.TRANSFER, 200_000, "RUB", sender=zakhar, receiver=ivan_sav)),
    (105, "Иван(сбер) снятие 320 000 RUB — ниже минимума",
     Transaction(TransactionType.WITHDRAWAL, 320_000, "RUB", sender=ivan_sav)),
    (110, "Ольга -> ООО «Магазин» 45 000 RUB",
     Transaction(TransactionType.PAYMENT, 45_000, "RUB", sender=olga, receiver="ООО «Магазин»")),
    (115, "Анна -> Иван 15 000 RUB",
     Transaction(TransactionType.TRANSFER, 15_000, "RUB", sender=anna, receiver=ivan)),
    (120, "Пополнение счёта Захара 300 000 RUB",
     Transaction(TransactionType.DEPOSIT, 300_000, "RUB", receiver=zakhar)),
    (125, "Снятие Пётра 1 000 USD",
     Transaction(TransactionType.WITHDRAWAL, 1_000, "USD", sender=petr)),
    (130, "Ольга -> Иван 25 000 RUB",
     Transaction(TransactionType.TRANSFER, 25_000, "RUB", sender=olga, receiver=ivan)),
    (660, "Захар -> ООО «Ночной брокер» 150 000 RUB — ночь и крупная сумма",
     Transaction(TransactionType.PAYMENT, 150_000, "RUB", sender=zakhar,
                 receiver="ООО «Ночной брокер»")),
    (15, "Захар -> ООО «Ночной брокер» 160 000 RUB",
     Transaction(TransactionType.PAYMENT, 160_000, "RUB", sender=zakhar,
                 receiver="ООО «Ночной брокер»")),
    (20, "Захар -> ООО «Ночной брокер» 170 000 RUB",
     Transaction(TransactionType.PAYMENT, 170_000, "RUB", sender=zakhar,
                 receiver="ООО «Ночной брокер»")),
    (30, "Пополнение счёта Марии 50 000 RUB — счёт заморожен",
     Transaction(TransactionType.DEPOSIT, 50_000, "RUB", receiver=maria)),
    (60, "Анна(инв) -> ООО «Фонд» 500 000 RUB — нет средств",
     Transaction(TransactionType.PAYMENT, 500_000, "RUB", sender=anna_inv, receiver="ООО «Фонд»")),
]

queue = TransactionQueue()
for _, _, txn in operations:
    queue.add(txn)

processor = TransactionProcessor(clock=clock, max_retries=1)
blocked = 0
rejected = 0
completed = 0
while queue.pending_count():
    txn = queue.next(clock())
    advance(minutes=next(minutes for minutes, _, candidate in operations if candidate is txn))
    try:
        if bank.execute_transaction(txn, processor=processor):
            completed += 1
            outcome = "ВЫПОЛНЕНА"
        else:
            rejected += 1
            outcome = "ОТКЛОНЕНА"
    except HighRiskTransactionError:
        blocked += 1
        outcome = "ЗАБЛОКИРОВАНА"
    receiver = getattr(txn.receiver, "acc_id", txn.receiver) or "-"
    print(f"  {clock():%d.%m %H:%M} {txn.txn_id} "
          f"{txn.sender.acc_id if txn.sender else '-':>8} -> {receiver:<16} "
          f"{txn.amount:>9,.0f} {txn.currency}  {outcome}")

print(f"\nИтог: {completed} выполнено, {rejected} отклонено, {blocked} заблокировано")
print(f"Записей в журнале банка: {len(bank.history)}")

builder = ReportBuilder(bank, risk_analyzer=analyzer, audit_log=audit, clock=clock)

print("\n" + "=" * 78)
print(builder.client_report("C-001"))
print("=" * 78)

print(builder.bank_report())
print("=" * 78)

print(builder.risk_report())
print("=" * 78)

paths = builder.export_all(client_id="C-001")
print("Файлы отчётов:")
for name, path in paths.items():
    print(f"  {name}: {path}")

charts = builder.save_charts()
print("Графики:")
for path in charts:
    print(f"  {path}")

timeline = builder._balance_timeline()
print(f"\nТочек в графике движения баланса: {len(timeline)}")
print(f"Итог по графику: {timeline[-1]['total']:,.2f} RUB")
