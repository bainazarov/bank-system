from datetime import datetime

from bank.abstract_account import AbstractAccount
from bank.enums.account_status import AccountStatus
from bank.enums.transaction_status import TransactionStatus
from bank.enums.transaction_type import TransactionType
from bank.exceptions import (
    AccountClosedError,
    AccountFrozenError,
    InsufficientFundsError,
    InvalidOperationError,
)
from bank.exchange_rates import ExchangeRates
from bank.premium_account import PremiumAccount
from bank.transaction import Transaction
from bank.validation import check_night, is_valid_commission_rate, is_valid_retries


class TransactionProcessor:
    def __init__(self, max_retries=3, external_commission_rate=0.01,
                 exchange_rates=ExchangeRates, clock=datetime.now):
        if not is_valid_retries(max_retries):
            raise InvalidOperationError(f"Недопустимое число попыток {max_retries}")
        if not is_valid_commission_rate(external_commission_rate):
            raise InvalidOperationError(f"Недопустимая ставка комиссии {external_commission_rate}")

        self.max_retries = max_retries
        self.external_commission_rate = external_commission_rate
        self.exchange_rates = exchange_rates
        self.clock = clock
        self.error_log = []
        self.completed = []

    def process_queue(self, queue):
        while queue.pending_count():
            txn = queue.next(self.clock())
            if txn is None:
                break
            success = self.process(txn)
            if not success and txn.attempts < self.max_retries:
                txn.status = TransactionStatus.PENDING
                queue.add(txn)

    def process(self, txn):
        if not isinstance(txn, Transaction):
            raise InvalidOperationError(f"Не является транзакцией {txn}")

        if txn.status not in (TransactionStatus.PENDING, TransactionStatus.PROCESSING):
            reason = f"Транзакция уже обработана (статус {txn.status.value})"
            self._log_error(txn, reason)
            return False

        txn.register_attempt()
        try:
            self._execute(txn)
            txn.complete(self.clock())
            self.completed.append(txn)
            return True
        except Exception as e:
            reason = str(e)
            self._log_error(txn, reason)
            if txn.attempts >= self.max_retries:
                txn.fail(reason, self.clock())
            return False

    def calculate_commission(self, txn):
        commission = txn.commission
        if txn.txn_type is TransactionType.PAYMENT and not isinstance(txn.receiver, AbstractAccount):
            commission += round(txn.amount * self.external_commission_rate, 2)
        return commission

    def _execute(self, txn):
        check_night(self.clock())
        commission = self.calculate_commission(txn)

        if txn.txn_type is TransactionType.DEPOSIT:
            self._check_account(txn.receiver, "Получатель")
            txn.receiver.deposit(self._convert(txn.amount, txn.currency, txn.receiver))
            return

        if txn.txn_type is TransactionType.WITHDRAWAL:
            self._withdraw_checked(txn.sender, self._convert(txn.amount, txn.currency, txn.sender))
            return

        if txn.txn_type is TransactionType.PAYMENT and not isinstance(txn.receiver, AbstractAccount):
            self._withdraw_checked(txn.sender, self._convert(txn.amount + commission, txn.currency, txn.sender))
            return

        self._check_account(txn.sender, "Отправитель")
        self._check_account(txn.receiver, "Получатель")
        debit = self._convert(txn.amount + commission, txn.currency, txn.sender)
        received = self._convert(txn.amount, txn.currency, txn.receiver)
        self._ensure_sufficient(txn.sender, debit)
        self._transfer_atomic(txn.sender, debit, txn.receiver, received)

    def _check_account(self, account, label):
        if account.status is AccountStatus.FROZEN:
            raise AccountFrozenError(f"Счёт {label} {account.acc_id} заморожен")

        if account.status is AccountStatus.CLOSED:
            raise AccountClosedError(f"Счёт {label} {account.acc_id} закрыт")

    def _withdraw_checked(self, sender, total):
        self._check_account(sender, "Отправитель")
        self._ensure_sufficient(sender, total)
        sender.withdraw(total)

    def _ensure_sufficient(self, sender, total):
        self._check_account(sender, "Отправитель")
        if not isinstance(sender, PremiumAccount) and total > sender._balance:
            raise InsufficientFundsError(
                f"Недостаточно средств на счёте {sender.acc_id}: "
                f"{sender._balance} {sender.currency} < {total}"
            )

    def _transfer_atomic(self, sender, debit, receiver, received):
        sender_balance = sender._balance
        receiver_balance = receiver._balance
        try:
            sender.withdraw(debit)
            receiver.deposit(received)
        except Exception:
            sender._balance = sender_balance
            receiver._balance = receiver_balance
            raise

    def _convert(self, amount, from_currency, receiver):
        return self.exchange_rates.convert(amount, from_currency, receiver.currency)

    def _log_error(self, txn, reason):
        self.error_log.append((txn.txn_id, reason, self.clock()))
