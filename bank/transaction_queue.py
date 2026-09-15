from datetime import datetime

from bank.enums.transaction_status import TransactionStatus
from bank.exceptions import InvalidOperationError, TransactionNotFoundError
from bank.transaction import Transaction


class TransactionQueue:
    def __init__(self):
        self.transactions = []

    def add(self, transaction):
        if not isinstance(transaction, Transaction):
            raise InvalidOperationError(f"Не является транзакцией {transaction}")
        self.transactions.append(transaction)

    def ready_transactions(self, now=None):
        if now is None:
            now = datetime.now()
        ready = [
            txn for txn in self.transactions
            if txn.status is TransactionStatus.PENDING and txn.is_ready(now)
        ]
        ready.sort(key=lambda txn: (-txn.priority.value, txn.created_at))
        return ready

    def next(self, now=None):
        ready = self.ready_transactions(now)
        if not ready:
            return None
        txn = ready[0]
        self.transactions.remove(txn)
        if now is None:
            now = datetime.now()
        txn.mark_processing(now)
        return txn

    def peek(self, now=None):
        ready = self.ready_transactions(now)
        return ready[0] if ready else None

    def get(self, txn_id):
        for txn in self.transactions:
            if txn.txn_id == txn_id:
                return txn
        raise TransactionNotFoundError(f"Транзакция {txn_id} не найдена")

    def cancel(self, txn_id, reason="Отменена оператором"):
        txn = self.get(txn_id)
        txn.cancel(reason)
        return txn

    def pending_count(self):
        return sum(1 for txn in self.transactions if txn.status is TransactionStatus.PENDING)

    def __len__(self):
        return len(self.transactions)

    def __iter__(self):
        return iter(self.transactions)
