import hashlib

from bank.client_status import ClientStatus
from bank.exceptions import InvalidOperationError
from bank.validation import is_non_empty_string, is_valid_age


def hash_password(password):
    return hashlib.sha256(password.encode("utf-8")).hexdigest()


class Client:
    def __init__(self, full_name, client_id, age, password, accounts=None, phone=None,
                 status=ClientStatus.ACTIVE):
        if not is_non_empty_string(full_name):
            raise InvalidOperationError(f"Недопустимое ФИО {full_name}")

        if not is_non_empty_string(client_id):
            raise InvalidOperationError(f"Недопустимый ID клиента {client_id}")

        if not is_valid_age(age):
            raise InvalidOperationError(f"Недопустимый возраст {age}")

        if not is_non_empty_string(password):
            raise InvalidOperationError(f"Недопустимый пароль {password}")

        if accounts is None:
            accounts = []

        if not isinstance(accounts, list):
            raise InvalidOperationError(f"Недопустимый список счетов {accounts}")

        if phone is not None and not is_non_empty_string(phone):
            raise InvalidOperationError(f"Недопустимый телефон {phone}")

        self.full_name = full_name
        self.client_id = client_id
        self.age = age
        self.accounts = accounts
        self.phone = phone
        self.status = status
        self.password_hash = hash_password(password)
        self.failed_attempts = 0

    def __str__(self):
        return f"Client {self.full_name} {self.client_id} {self.status.value} age={self.age}"

    def __repr__(self):
        return f"Client({self.full_name!r}, {self.client_id!r}, age={self.age})"