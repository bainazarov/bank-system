from abc import ABC, abstractmethod
from bank.account_status import AccountStatus

class AbstractAccount(ABC):
    def __init__(self, acc_id, name, balance, status=AccountStatus.ACTIVE):
        self.acc_id = acc_id
        self.name = name
        self._balance = balance
        self.status = status

    @abstractmethod
    def deposit(self, amount):
        ...

    @abstractmethod
    def withdraw(self, amount):
        ...

    @abstractmethod
    def get_account_info(self):
        ...