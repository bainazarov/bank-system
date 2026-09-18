from datetime import datetime

from bank.abstract_account import AbstractAccount
from bank.client import Client, hash_password
from bank.enums.account_status import AccountStatus
from bank.enums.audit_severity import AuditSeverity
from bank.enums.client_status import ClientStatus
from bank.enums.risk_level import RiskLevel
from bank.exceptions import (
    AccountNotFoundError,
    AuthenticationError,
    ClientBlockedError,
    ClientNotFoundError,
    HighRiskTransactionError,
    InvalidOperationError,
)
from bank.transaction import Transaction
from bank.transaction_processor import TransactionProcessor
from bank.validation import check_night


class Bank:
    MAX_LOGIN_ATTEMPTS = 3

    def __init__(self, name, clock=datetime.now, risk_analyzer=None, audit_log=None):
        self.name = name
        self.clients = {}
        self.suspicious_events = []
        self.clock = clock
        self.risk_analyzer = risk_analyzer
        self.audit_log = audit_log
        self.blocked_transactions = []

    def add_client(self, client):
        if not isinstance(client, Client):
            raise InvalidOperationError(f"Не является клиентом {client}")

        if client.client_id in self.clients:
            raise InvalidOperationError(f"Клиент с ID {client.client_id} уже существует")

        self.clients[client.client_id] = client

    def get_client(self, client_id):
        if client_id not in self.clients:
            raise ClientNotFoundError(f"Клиент {client_id} не найден")
        return self.clients[client_id]

    def authenticate_client(self, client_id, password):
        client = self.get_client(client_id)

        if client.status is ClientStatus.BLOCKED:
            raise ClientBlockedError(f"Клиент {client.full_name} заблокирован")

        stored_hash = client.password_hash
        if stored_hash != hash_password(password):
            client.failed_attempts += 1
            remaining = Bank.MAX_LOGIN_ATTEMPTS - client.failed_attempts
            if remaining <= 0:
                client.status = ClientStatus.BLOCKED
                raise AuthenticationError(f"Клиент {client.full_name} заблокирован после 3 попыток")
            raise AuthenticationError(f"Неверный пароль, осталось попыток: {remaining}")
        else:
            client.failed_attempts = 0
            return True

    def open_account(self, client_id, account):
        client = self.get_client(client_id)
        check_night(self.clock())

        if not isinstance(account, AbstractAccount):
            raise InvalidOperationError(f"Не является счётом {account}")

        if self._find_account(account.acc_id) is not None:
            raise InvalidOperationError(f"Счёт {account.acc_id} уже зарегистрирован")

        client.accounts.append(account)

    def close_account(self, client_id, account_id):
        account = self._get_client_account(client_id, account_id)
        check_night(self.clock())
        account.status = AccountStatus.CLOSED

    def freeze_account(self, client_id, account_id):
        account = self._get_client_account(client_id, account_id)
        check_night(self.clock())
        if account.status is not AccountStatus.ACTIVE:
            raise InvalidOperationError(
                f"Невозможно заморозить счёт {account_id}: текущий статус {account.status.value}"
            )
        account.status = AccountStatus.FROZEN

    def unfreeze_account(self, client_id, account_id):
        account = self._get_client_account(client_id, account_id)
        check_night(self.clock())
        if account.status is not AccountStatus.FROZEN:
            raise InvalidOperationError(
                f"Невозможно разморозить счёт {account_id}: текущий статус {account.status.value}"
            )
        account.status = AccountStatus.ACTIVE

    def deposit(self, client_id, account_id, amount):
        account = self._get_client_account(client_id, account_id)
        check_night(self.clock())
        account.deposit(amount)

    def withdraw(self, client_id, account_id, amount):
        account = self._get_client_account(client_id, account_id)
        check_night(self.clock())
        account.withdraw(amount)

    def search_accounts(self, query):
        pattern = str(query).strip().lower()
        if not pattern:
            return []

        matches = []
        for account in self._all_accounts():
            if pattern in account.acc_id.lower() or pattern in account.name.lower():
                matches.append(account)
        return matches

    def flag_suspicious(self, client_id, reason):
        client = self.get_client(client_id)
        client.status = ClientStatus.SUSPICIOUS
        self.suspicious_events.append((client_id, reason))

    def execute_transaction(self, txn, processor=None):
        if not isinstance(txn, Transaction):
            raise InvalidOperationError(f"Не является транзакцией {txn}")

        if processor is None:
            processor = TransactionProcessor(clock=self.clock)

        if self.risk_analyzer is not None:
            assessment = self.risk_analyzer.assess(txn)
            if self.audit_log is not None:
                severity = (AuditSeverity.CRITICAL if assessment.level is RiskLevel.HIGH
                            else AuditSeverity.WARNING if assessment.level is RiskLevel.MEDIUM
                else AuditSeverity.INFO)
                self.audit_log.log(severity, f"Риск операции {txn.txn_id}: {assessment}")
            if assessment.level is RiskLevel.HIGH:
                return self._block(txn, assessment)

        ok = processor.process(txn)
        if self.audit_log is not None:
            if ok:
                message, severity = f"Операция {txn.txn_id} выполнена", AuditSeverity.INFO
            else:
                reason = processor.error_log[-1][1] if processor.error_log else "ошибка"
                message, severity = f"Операция {txn.txn_id} не выполнена: {reason}", AuditSeverity.ERROR
            self.audit_log.log(severity, message)
        return ok

    def _block(self, txn, assessment):
        self.blocked_transactions.append((txn, assessment))
        if self.audit_log is not None:
            self.audit_log.critical(f"Операция {txn.txn_id} заблокирована: {assessment}")

        if isinstance(txn.sender, AbstractAccount):
            for client in self.clients.values():
                if any(account is txn.sender for account in client.accounts):
                    self.flag_suspicious(client.client_id, f"попытка опасной операции {txn.txn_id}")
                    break

        raise HighRiskTransactionError(f"Операция {txn.txn_id} заблокирована (высокий риск)")

    def get_total_balance(self):
        totals = {}
        for account in self._all_accounts():
            totals[account.currency] = totals.get(account.currency, 0) + account._balance
        return totals

    def get_clients_ranking(self):
        def total_balance(client):
            return sum(account._balance for account in client.accounts)

        return sorted(self.clients.values(), key=total_balance, reverse=True)

    def _get_client_account(self, client_id, account_id):
        client = self.get_client(client_id)

        for account in client.accounts:
            if account.acc_id == account_id:
                return account

        raise AccountNotFoundError(f"Счёт {account_id} не найден у клиента {client_id}")

    def _find_account(self, account_id):
        for account in self._all_accounts():
            if account.acc_id == account_id:
                return account
        return None

    def _all_accounts(self):
        accounts = []
        for client in self.clients.values():
            accounts.extend(client.accounts)
        return accounts
