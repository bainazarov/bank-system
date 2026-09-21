from collections import Counter
from datetime import datetime, timedelta

from bank.audit_log import AuditLog
from bank.audit_reports import error_statistics, suspicious
from bank.bank import Bank
from bank.bank_account import BankAccount
from bank.client import Client
from bank.enums.account_status import AccountStatus
from bank.enums.audit_severity import AuditSeverity
from bank.enums.transaction_type import TransactionType
from bank.exceptions import HighRiskTransactionError
from bank.exchange_rates import ExchangeRates
from bank.investment_account import InvestmentAccount
from bank.premium_account import PremiumAccount
from bank.risk_analyzer import RiskAnalyzer
from bank.savings_account import SavingsAccount
from bank.transaction import Transaction
from bank.transaction_processor import TransactionProcessor
from bank.transaction_queue import TransactionQueue

current_time = datetime(2026, 9, 20, 10, 0)


def clock():
    return current_time


def advance(**kwargs):
    global current_time
    current_time += timedelta(**kwargs)


analyzer = RiskAnalyzer(clock=clock)
audit = AuditLog(clock=clock, file_path="day6_demo.json")
bank = Bank("Tinkoff", clock=clock, risk_analyzer=analyzer, audit_log=audit)

for name, client_id, age, password in [
    ("Иван", "C-001", 34, "123"),
    ("Ольга", "C-002", 29, "123"),
    ("Захар", "C-003", 41, "123"),
    ("Семён", "C-004", 22, "123"),
    ("Мария", "C-005", 38, "123"),
    ("Пётр", "C-006", 45, "123"),
    ("Анна", "C-007", 31, "123"),
    ("Тони", "C-008", 27, "123"),
]:
    bank.add_client(Client(name, client_id, age, password))
print(f"Клиентов в банке «{bank.name}»: {len(bank.clients)}")

ivan = BankAccount("Иван", 1_000_000, "RUB")
ivan_sav = SavingsAccount("Иван", 300_000, "RUB", min_balance=50_000, monthly_interest_rate=0.15)
olga = BankAccount("Ольга", 400_000, "RUB")
olga_inv = InvestmentAccount("Ольга", 1_500_000, "RUB")
zakhar = PremiumAccount("Захар", 500_000, "RUB", overdraft_limit=100_000,
                        withdrawal_limit=250_000, fixed_commission=0)
semyon = BankAccount("Семён", 30_000, "RUB")
maria = BankAccount("Мария", 700_000, "RUB", status=AccountStatus.FROZEN)
petr = BankAccount("Пётр", 5_000, "USD")
anna = BankAccount("Анна", 250_000, "RUB")
anna_inv = InvestmentAccount("Анна", 600_000, "RUB")
tony = BankAccount("Тони", 2_000, "EUR")
tony_old = BankAccount("Тони", 100_000, "RUB", status=AccountStatus.CLOSED)

accounts = {
    "C-001": [ivan, ivan_sav],
    "C-002": [olga, olga_inv],
    "C-003": [zakhar],
    "C-004": [semyon],
    "C-005": [maria],
    "C-006": [petr],
    "C-007": [anna, anna_inv],
    "C-008": [tony, tony_old],
}
for client_id, accs in accounts.items():
    for account in accs:
        bank.open_account(client_id, account)

total_accounts = sum(len(accs) for accs in accounts.values())
print(f"Счетов открыто: {total_accounts}")
for client_id in sorted(accounts):
    print(f"  {bank.get_client(client_id).full_name}: "
          + ", ".join(a.acc_id for a in bank.get_client(client_id).accounts))

ops = [
    (0, "Иван -> Ольга 10 000 RUB", Transaction(TransactionType.TRANSFER, 10_000, "RUB", sender=ivan, receiver=olga)),
    (5, "Ольга -> Иван 5 000 RUB", Transaction(TransactionType.TRANSFER, 5_000, "RUB", sender=olga, receiver=ivan)),
    (5, "Иван -> Анна 12 000 RUB", Transaction(TransactionType.TRANSFER, 12_000, "RUB", sender=ivan, receiver=anna)),
    (5, "Анна -> Иван 3 000 RUB", Transaction(TransactionType.TRANSFER, 3_000, "RUB", sender=anna, receiver=ivan)),
    (5, "Иван(сбер) -> Ольга 20 000 RUB",
     Transaction(TransactionType.TRANSFER, 20_000, "RUB", sender=ivan_sav, receiver=olga)),
    (5, "Захар -> Ольга 25 000 RUB",
     Transaction(TransactionType.TRANSFER, 25_000, "RUB", sender=zakhar, receiver=olga)),
    (5, "Семён -> Ольга 40 000 RUB — нет средств",
     Transaction(TransactionType.TRANSFER, 40_000, "RUB", sender=semyon, receiver=olga)),
    (5, "Иван -> Ольга(инв) 30 000 RUB",
     Transaction(TransactionType.TRANSFER, 30_000, "RUB", sender=ivan, receiver=olga_inv)),
    (5, "Пётр -> Иван 1 500 USD", Transaction(TransactionType.TRANSFER, 1_500, "USD", sender=petr, receiver=ivan)),
    (5, "Иван -> Пётр 800 USD", Transaction(TransactionType.TRANSFER, 800, "USD", sender=ivan, receiver=petr)),
    (5, "Захар -> ООО «Мечта» 5 000 RUB (платёж)",
     Transaction(TransactionType.PAYMENT, 5_000, "RUB", sender=zakhar, receiver="ООО «Мечта»")),
    (5, "Захар -> ООО «Мечта» 110 000 RUB — крупная",
     Transaction(TransactionType.PAYMENT, 110_000, "RUB", sender=zakhar, receiver="ООО «Мечта»")),
    (5, "Иван -> ООО «Мечта» 3 000 RUB (платёж)",
     Transaction(TransactionType.PAYMENT, 3_000, "RUB", sender=ivan, receiver="ООО «Мечта»")),
    (5, "Иван -> ООО «Мечта» 120 000 RUB — крупная",
     Transaction(TransactionType.PAYMENT, 120_000, "RUB", sender=ivan, receiver="ООО «Мечта»")),
    (5, "Мария -> Ольга 10 000 RUB — счёт заморожен",
     Transaction(TransactionType.TRANSFER, 10_000, "RUB", sender=maria, receiver=olga)),
    (5, "Пополнение Семёна 20 000 RUB", Transaction(TransactionType.DEPOSIT, 20_000, "RUB", receiver=semyon)),
    (5, "Семён снятие 25 000 RUB", Transaction(TransactionType.WITHDRAWAL, 25_000, "RUB", sender=semyon)),
    (5, "Семён снятие 50 000 RUB — нет средств", Transaction(TransactionType.WITHDRAWAL, 50_000, "RUB", sender=semyon)),
    (5, "Тони -> Ольга 500 EUR", Transaction(TransactionType.TRANSFER, 500, "EUR", sender=tony, receiver=olga)),
    (5, "Ольга -> Тони 200 EUR", Transaction(TransactionType.TRANSFER, 200, "EUR", sender=olga, receiver=tony)),
    (5, "Анна -> ООО «ЖКХ» 5 000 RUB (платёж)",
     Transaction(TransactionType.PAYMENT, 5_000, "RUB", sender=anna, receiver="ООО «ЖКХ»")),
    (680, "Захар -> Ольга 1 000 RUB ночью",
     Transaction(TransactionType.TRANSFER, 1_000, "RUB", sender=zakhar, receiver=olga)),
    (5, "Захар -> Ольга 1 100 RUB ночью",
     Transaction(TransactionType.TRANSFER, 1_100, "RUB", sender=zakhar, receiver=olga)),
    (5, "Захар -> Ольга 950 RUB — частые ночные",
     Transaction(TransactionType.TRANSFER, 950, "RUB", sender=zakhar, receiver=olga)),
    (5, "Иван -> ООО «Ночной брокер» 130 000 RUB",
     Transaction(TransactionType.PAYMENT, 130_000, "RUB", sender=ivan, receiver="ООО «Ночной брокер»")),
    (5, "Семён -> Ольга 200 RUB ночью",
     Transaction(TransactionType.TRANSFER, 200, "RUB", sender=semyon, receiver=olga)),
    (5, "Семён -> Ольга 150 RUB ночью",
     Transaction(TransactionType.TRANSFER, 150, "RUB", sender=semyon, receiver=olga)),
    (155, "Иван -> Ольга 5 000 RUB — запрещённый час",
     Transaction(TransactionType.TRANSFER, 5_000, "RUB", sender=ivan, receiver=olga)),
    (240, "Анна -> ООО «ЖКХ» 300 000 RUB — нет средств",
     Transaction(TransactionType.PAYMENT, 300_000, "RUB", sender=anna, receiver="ООО «ЖКХ»")),
    (5, "Иван -> Тони(закрыт) 5 000 RUB",
     Transaction(TransactionType.TRANSFER, 5_000, "RUB", sender=ivan, receiver=tony_old)),
    (5, "Захар -> Анна(инв) 150 000 RUB",
     Transaction(TransactionType.TRANSFER, 150_000, "RUB", sender=zakhar, receiver=anna_inv)),
    (5, "Ольга -> ООО «Магазин» 40 000 RUB (платёж)",
     Transaction(TransactionType.PAYMENT, 40_000, "RUB", sender=olga, receiver="ООО «Магазин»")),
    (5, "Иван -> ООО «Магазин» 60 000 RUB (платёж)",
     Transaction(TransactionType.PAYMENT, 60_000, "RUB", sender=ivan, receiver="ООО «Магазин»")),
    (5, "Пётр -> ООО «Магазин» 1 000 USD (платёж)",
     Transaction(TransactionType.PAYMENT, 1_000, "USD", sender=petr, receiver="ООО «Магазин»")),
    (5, "Тони -> ООО «Магазин» 300 EUR (платёж)",
     Transaction(TransactionType.PAYMENT, 300, "EUR", sender=tony, receiver="ООО «Магазин»")),
    (5, "Пополнение Ивана 100 000 RUB", Transaction(TransactionType.DEPOSIT, 100_000, "RUB", receiver=ivan)),
    (5, "Семён снятие 15 000 RUB", Transaction(TransactionType.WITHDRAWAL, 15_000, "RUB", sender=semyon)),
    (5, "Анна(инв) -> Ольга 20 000 RUB",
     Transaction(TransactionType.TRANSFER, 20_000, "RUB", sender=anna_inv, receiver=olga)),
    (5, "Захар -> ООО «Мечта» 200 000 RUB — крупная",
     Transaction(TransactionType.PAYMENT, 200_000, "RUB", sender=zakhar, receiver="ООО «Мечта»")),
    (5, "Захар -> Иван(сбер) 50 000 RUB",
     Transaction(TransactionType.TRANSFER, 50_000, "RUB", sender=zakhar, receiver=ivan_sav)),
    (5, "Иван(сбер) снятие 290 000 RUB — ниже минимума",
     Transaction(TransactionType.WITHDRAWAL, 290_000, "RUB", sender=ivan_sav)),
    (5, "Пополнение Марии 5 000 RUB — счёт заморожен",
     Transaction(TransactionType.DEPOSIT, 5_000, "RUB", receiver=maria)),
]

queue = TransactionQueue()
labels = {txn.txn_id: label for _, label, txn in ops}
minutes = {txn.txn_id: m for m, _, txn in ops}
for position, (_, label, txn) in enumerate(ops, 1):
    queue.add(txn)
    print(f"  №{position:2} в очередь: [{txn.priority.name:6}] {txn.txn_type.value:11} {label}")

processor = TransactionProcessor(clock=clock, max_retries=1)
results = []
pending = queue.pending_count()
while queue.pending_count():
    txn = queue.next(clock())
    advance(minutes=minutes[txn.txn_id])
    risk = None
    try:
        ok = bank.execute_transaction(txn, processor=processor)
        outcome = "ВЫПОЛНЕНА" if ok else "ОТКЛОНЕНА"
        risk = analyzer.assessments[-1]
    except HighRiskTransactionError as e:
        outcome = "ЗАБЛОКИРОВАНА"
        risk = analyzer.assessments[-1]
    results.append((clock(), labels[txn.txn_id], txn, outcome, risk))
    mark = {"ВЫПОЛНЕНА": "  [OK]  ", "ОТКЛОНЕНА": "[ОТКЛ.]", "ЗАБЛОКИРОВАНА": "[БЛОК]"}[outcome]
    receiver = getattr(txn.receiver, "acc_id", txn.receiver) or "-"
    level = risk.level.label if risk else "?"
    print(f"  {mark} {clock():%H:%M} {txn.txn_id} "
          f"{txn.sender.acc_id if txn.sender else '-'} -> {receiver} "
          f"{txn.amount:6} {txn.currency:3} риск={level}")

print(f"\nВсего отправлено в очередь: {pending}, обработано: {len(results)}")

print(f"  файл: {audit.file_path}")
for severity in AuditSeverity:
    count = len(audit.filter(severity=severity))
    if count:
        print(f"  {severity.label}: {count}")

client_id = "C-001"
client = bank.get_client(client_id)
print(f"\nСчета клиента «{client.full_name}»:")
for account in client.accounts:
    print(f"  {account}")

print(f"\nИстория операций клиента «{client.full_name}»:")
ivan_accounts = {account.acc_id for account in client.accounts}
for at, label, txn, outcome, risk in results:
    involved = (getattr(txn.sender, "acc_id", None), getattr(txn.receiver, "acc_id", None))
    if any(acc in ivan_accounts for acc in involved):
        receiver = getattr(txn.receiver, "acc_id", txn.receiver) or "—"
        sender = txn.sender.acc_id if txn.sender else "-"
        print(f"  {at:%m-%d %H:%M} {txn.txn_type.value:11} {sender} -> {receiver} "
              f"{txn.amount:6} {txn.currency:3} {txn.status.value}")

medium_plus = suspicious(analyzer)
print(f"\nПодозрительные операции (уровень >= среднего, {len(medium_plus)}):")
for a in medium_plus:
    receiver = getattr(a.txn.receiver, "acc_id", a.txn.receiver)
    print(f"  {a.time:%H:%M} {a.subject} -> {receiver} {a.txn.amount} {a.txn.currency} "
          f"{a.txn.status.value}: {a}")

if bank.blocked_transactions:
    print(f"\nЗаблокированные операции ({len(bank.blocked_transactions)}):")
    for txn, a in bank.blocked_transactions:
        receiver = getattr(txn.receiver, "acc_id", txn.receiver)
        print(f"  {a.time:%H:%M} {txn.sender.acc_id} -> {receiver} {txn.amount} "
              f"{txn.currency} — {a}")
    print(f"События «подозрительных» клиентов: {bank.suspicious_events}")

print("\nТоп-3 клиента по сумме остатков (без конвертации валют):")
for place, c in enumerate(bank.get_clients_ranking()[:3], 1):
    total = sum(account._balance for account in c.accounts)
    print(f"  {place}. {c.full_name}: {total:,.0f} (счетов: {len(c.accounts)})")

status_stats = Counter(txn.status.value for _, _, txn, _, _ in results)
print("\nСтатистика транзакций по статусам:")
for status, count in status_stats.most_common():
    print(f"  {status}: {count}")

type_stats = Counter(txn.txn_type.value for _, _, txn, _, _ in results)
print("По типам:")
for t, count in type_stats.most_common():
    print(f"  {t}: {count}")

outcomes = Counter(outcome for _, _, _, outcome, _ in results)
print(f"Итог: {outcomes['ВЫПОЛНЕНА']} выполнено, {outcomes['ОТКЛОНЕНА']} отклонено, "
      f"{outcomes['ЗАБЛОКИРОВАНА']} заблокировано")

print("\nТиповые причины отклонений:")
for reason, count in error_statistics(audit_log=audit).most_common(5):
    print(f"  {count}x {reason}")

balances = bank.get_total_balance()
print("\nОбщий баланс банка:")
total_rub = 0.0
for currency, amount in balances.items():
    total_rub += ExchangeRates.convert(amount, currency, "RUB")
    print(f"  {currency}: {amount:,.0f}")
print(f"  ИТОГО в рублях: {total_rub:,.0f} RUB")

print("\nИтоговые балансы клиентов:")
for client_id in sorted(bank.clients):
    for account in bank.get_client(client_id).accounts:
        print(f"  {account}")
