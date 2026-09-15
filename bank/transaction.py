import uuid
from datetime import datetime

from bank.exceptions import InvalidOperationError
from bank.enums.transaction_priority import TransactionPriority
from bank.enums.transaction_status import TransactionStatus
from bank.validation import (
    is_non_negative_number,
    is_positive_number,
    is_valid_currency,
    is_valid_execute_at,
    is_valid_priority,
    is_valid_transaction_type,
)


class Transaction:
    def __init__(self, txn_type, amount, currency, sender=None, receiver=None,
                 commission=0.0, priority=TransactionPriority.NORMAL, execute_at=None,
                 txn_id=None):
        if not is_valid_transaction_type(txn_type):
            raise InvalidOperationError(f"Недопустимый тип транзакции {txn_type}")

        if not is_positive_number(amount):
            raise InvalidOperationError(f"Недопустимая сумма {amount}")

        if not is_valid_currency(currency):
            raise InvalidOperationError(f"Недопустимая валюта {currency}")

        if not is_non_negative_number(commission):
            raise InvalidOperationError(f"Недопустимая комиссия {commission}")

        if not is_valid_priority(priority):
            raise InvalidOperationError(f"Недопустимый приоритет {priority}")

        if not is_valid_execute_at(execute_at):
            raise InvalidOperationError(f"Недопустимое время выполнения {execute_at}")

        self.txn_id = txn_id or uuid.uuid4().hex[:8]
        self.txn_type = txn_type
        self.amount = amount
        self.currency = currency
        self.sender = sender
        self.receiver = receiver
        self.commission = commission
        self.priority = priority
        self.execute_at = execute_at
        self.status = TransactionStatus.PENDING
        self.rejection_reason = None
        self.created_at = datetime.now()
        self.updated_at = self.created_at
        self.executed_at = None
        self.cancelled_at = None
        self.attempts = 0

    def mark_processing(self, at=None):
        self.status = TransactionStatus.PROCESSING
        self.updated_at = at or datetime.now()

    def complete(self, at=None):
        self.status = TransactionStatus.COMPLETED
        self.executed_at = at or datetime.now()
        self.updated_at = self.executed_at

    def fail(self, reason, at=None):
        self.status = TransactionStatus.FAILED
        self.rejection_reason = reason
        self.updated_at = at or datetime.now()

    def cancel(self, reason="Отменена оператором", at=None):
        if self.status is not TransactionStatus.PENDING:
            raise InvalidOperationError(
                f"Невозможно отменить транзакцию {self.txn_id}: статус {self.status.value}"
            )
        self.status = TransactionStatus.CANCELLED
        self.rejection_reason = reason
        self.cancelled_at = at or datetime.now()
        self.updated_at = self.cancelled_at

    def register_attempt(self):
        self.attempts += 1

    def is_ready(self, now=None):
        if now is None:
            now = datetime.now()
        if self.execute_at is None:
            return True
        return now >= self.execute_at

    def __str__(self):
        return (
            f"Txn {self.txn_id} {self.txn_type.value} "
            f"{self.amount} {self.currency} {self.priority.name} {self.status.value}"
        )

    def __repr__(self):
        return f"Transaction({self.txn_type.value!r}, {self.amount}, {self.currency!r})"