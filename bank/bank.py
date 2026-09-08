from datetime import datetime

from bank.abstract_account import AbstractAccount
from bank.account_status import AccountStatus
from bank.client import Client, hash_password
from bank.client_status import ClientStatus
from bank.exceptions import (
    AccountNotFoundError,
    AuthenticationError,
    ClientBlockedError,
    ClientNotFoundError,
    InvalidOperationError,
    NightOperationsError,
)


class Bank:
    MAX_LOGIN_ATTEMPTS = 3

    def __init__(self, name, clock=datetime.now):
        self.name = name
        self.clients = {}
        self.suspicious_events = []
        self.clock = clock

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
        self._check_night()

        if not isinstance(account, AbstractAccount):
            raise InvalidOperationError(f"Не является счётом {account}")

        if self._find_account(account.acc_id) is not None:
            raise InvalidOperationError(f"Счёт {account.acc_id} уже зарегистрирован")

        client.accounts.append(account)

    def close_account(self, client_id, account_id):
        account = self._get_client_account(client_id, account_id)
        self._check_night()
        account.status = AccountStatus.CLOSED

    def freeze_account(self, client_id, account_id):
        account = self._get_client_account(client_id, account_id)
        self._check_night()
        account.status = AccountStatus.FROZEN

    def unfreeze_account(self, client_id, account_id):
        account = self._get_client_account(client_id, account_id)
        self._check_night()
        account.status = AccountStatus.ACTIVE

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

    def _check_night(self):
        if self.clock().hour < 5:
            raise NightOperationsError("Операции запрещены с 00:00 до 05:00")
