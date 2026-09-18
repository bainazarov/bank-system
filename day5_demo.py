from datetime import datetime, timedelta

from bank.audit_log import AuditLog
from bank.audit_reports import client_profiles, error_statistics, suspicious
from bank.bank import Bank
from bank.bank_account import BankAccount
from bank.client import Client
from bank.enums.audit_severity import AuditSeverity
from bank.enums.transaction_type import TransactionType
from bank.exceptions import HighRiskTransactionError
from bank.risk_analyzer import RiskAnalyzer
from bank.transaction import Transaction

current_time = datetime(2026, 9, 18, 12, 0)


def clock():
    return current_time


def advance(**kwargs):
    global current_time
    current_time += timedelta(**kwargs)


analyzer = RiskAnalyzer(clock=clock)
audit = AuditLog(clock=clock, file_path="audit.json")
bank = Bank("Tbank", clock=clock, risk_analyzer=analyzer, audit_log=audit)

accounts = {
    "C-001": BankAccount("Иван", 2000000, "RUB"),
    "C-002": BankAccount("Ольга", 900000, "RUB"),
    "C-003": BankAccount("Захар", 500000, "RUB"),
    "C-004": BankAccount("Семён", 50000, "RUB"),
}
for client_id, account in accounts.items():
    bank.add_client(Client(account.name, client_id, 30, "123"))
    bank.open_account(client_id, account)


def run(sender, receiver, amount, label):
    txn = Transaction(TransactionType.TRANSFER, amount, "RUB", sender=sender, receiver=receiver)
    try:
        ok = bank.execute_transaction(txn)
        status = "ВЫПОЛНЕНА" if ok else "ОШИБКА"
        print(f"  [{status}] {label}")
    except HighRiskTransactionError:
        print(f"  [БЛОК] {label}")


ivan, olga, zakhar, semyon = accounts.values()

print("Обычные и подозрительные операции (день):")
run(ivan, olga, 5000, "Иван -> Ольга, 5 000")
advance(minutes=5)
run(olga, ivan, 3000, "Ольга -> Иван, 3 000")
advance(minutes=5)
run(zakhar, olga, 2000, "Захар -> Ольга, 2 000")
advance(minutes=5)
run(zakhar, ivan, 500, "Захар -> Иван, 500")
advance(minutes=5)
run(ivan, "ООО Точка", 250_000, "Иван -> внешний кошелёк, 250 000")
advance(minutes=5)
run(ivan, olga, 150000, "Иван -> Ольга, 150 000 (крупная сумма)")
advance(minutes=5)
run(semyon, olga, 100, "Семён -> Ольга, 100")
advance(minutes=1)
run(semyon, olga, 1000000, "Семён -> Ольга, 1 000 000 (нет средств)")

print("Ночные операции:")
advance(hours=11, minutes=20)
run(zakhar, ivan, 1000, "Захар -> Иван, 1 000 (ночь)")
advance(minutes=5)
run(zakhar, ivan, 1100, "Захар -> Иван, 1 100 (ночь)")
advance(minutes=5)
run(zakhar, ivan, 950, "Захар -> Иван, 950 (частые ночные)")
advance(hours=1, minutes=5)
run(ivan, olga, 2000, "Иван -> Ольга, 2 000 (запрещённый час)")

print("\nЖурнал аудита:")
for severity in AuditSeverity:
    count = len(audit.filter(severity=severity))
    if count:
        print(f"  {severity.name}: {count}")
print(f"  файл: {audit.file_path}")

print("\nПодозрительные операции:")
for a in suspicious(analyzer):
    receiver = getattr(a.txn.receiver, "acc_id", a.txn.receiver)
    print(f"  {a.time:%H:%M} {a.subject} -> {receiver} {a.txn.amount} RUB: {a}")

print("\nРиск-профили клиентов:")
for subject, p in client_profiles(analyzer).items():
    print(f"  {subject}: операций={p['transactions']} риск={p['max_level'].label} "
          f"подозрительных={p['suspicious']} баллы={p['score']}")

print("\nСтатистика ошибок:")
for reason, count in error_statistics(audit_log=audit).most_common():
    print(f"  {count}x {reason}")

print("\nЗаблокированные операции:")
for txn, a in bank.blocked_transactions:
    print(f"  Txn {txn.txn_id}: {txn.amount} RUB — {a}")
