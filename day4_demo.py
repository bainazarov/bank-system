from datetime import datetime, timedelta

from bank.bank_account import BankAccount
from bank.enums.account_status import AccountStatus
from bank.enums.transaction_priority import TransactionPriority
from bank.enums.transaction_type import TransactionType
from bank.premium_account import PremiumAccount
from bank.transaction import Transaction
from bank.transaction_processor import TransactionProcessor
from bank.transaction_queue import TransactionQueue

start = datetime(2026, 9, 15, 10, 0)
current_time = start


def clock():
    return current_time


ivan = BankAccount("Иван", 10000, "RUB")
olga = BankAccount("Ольга", 5000, "RUB")
petr = BankAccount("Пётр", 2000, "USD")
anna = PremiumAccount("Анна", 1000, "RUB", overdraft_limit=2000, withdrawal_limit=5000, fixed_commission=0)
frozen = BankAccount("Мария", 7000, "RUB", status=AccountStatus.FROZEN)
dmitry = BankAccount("Дмитрий", 300, "RUB")
tony = BankAccount("Тони", 8000, "EUR")
euro_pocket = BankAccount("Саша", 1000, "EUR")

print("\nСчета:")
for account in [ivan, olga, petr, anna, frozen, dmitry, tony, euro_pocket]:
    print("  ", account)

txs = [
    Transaction(TransactionType.TRANSFER, 1000, "RUB", sender=ivan, receiver=olga),
    Transaction(TransactionType.TRANSFER, 500, "RUB", sender=olga, receiver=ivan,
                priority=TransactionPriority.HIGH),
    Transaction(TransactionType.TRANSFER, 100, "USD", sender=petr, receiver=euro_pocket,
                priority=TransactionPriority.URGENT),
    Transaction(TransactionType.PAYMENT, 2000, "RUB", sender=ivan, receiver="ООО Рога и Копыта"),
    Transaction(TransactionType.TRANSFER, 5000, "RUB", sender=frozen, receiver=olga),
    Transaction(TransactionType.TRANSFER, 900, "RUB", sender=dmitry, receiver=olga),
    Transaction(TransactionType.TRANSFER, 2500, "RUB", sender=anna, receiver=olga,
                priority=TransactionPriority.HIGH),
    Transaction(TransactionType.PAYMENT, 1000, "RUB", sender=ivan, receiver="ЖКХ 228",
                priority=TransactionPriority.HIGH),
    Transaction(TransactionType.TRANSFER, 100, "EUR", sender=tony, receiver=euro_pocket),
    Transaction(TransactionType.TRANSFER, 50, "RUB", sender=ivan, receiver=olga,
                execute_at=start + timedelta(minutes=30)),
]

queue = TransactionQueue()
for txn in txs:
    queue.add(txn)
print(f"\n10 транзакций помещено в очередь: {len(queue)}")

processor = TransactionProcessor(clock=clock)
processor.process_queue(queue)

tx_cancel = Transaction(TransactionType.TRANSFER, 777, "RUB", sender=ivan, receiver=olga,
                        priority=TransactionPriority.HIGH)
queue.add(tx_cancel)
queue.cancel(tx_cancel.txn_id, "Клиент отменил перевод")
print(f"Отмена: {tx_cancel.status.value} -> {tx_cancel.rejection_reason}")

print("\nПорядок успешного выполнения:")
for txn in processor.completed:
    receiver = getattr(txn.receiver, "acc_id", txn.receiver)
    print(f"  [{txn.priority.name:6}] {txn.txn_type.value:8} {txn.sender.acc_id} -> {receiver} "
          f"{txn.amount} {txn.currency}")

print("\nИтог по 10 транзакциям:")
for txn in txs:
    reason = f" | причина: {txn.rejection_reason}" if txn.rejection_reason else ""
    print(f"  {txn.txn_id} [{txn.priority.name:6}] {txn.txn_type.value:8} {txn.amount:5} "
          f"{txn.currency:3} -> {txn.status.value:10}{reason}")

print(f"\nЖурнал ошибок (попыток: {sum(1 for t in txs if t.attempts > 1)}):")
for txn_id, reason, at in processor.error_log:
    print(f"  {at:%H:%M} {txn_id}: {reason}")

current_time = start + timedelta(minutes=31)
processor.process_queue(queue)
delayed = txs[9]
print(f"Отложенная транзакция: {delayed.status.value} в {delayed.executed_at:%H:%M}")

print("\nБалансы после выполнения:")
for account in [ivan, olga, petr, anna, dmitry, tony, euro_pocket]:
    print("  ", account)
