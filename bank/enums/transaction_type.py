from enum import Enum


class TransactionType(Enum):
    TRANSFER = "TRANSFER"  # Перевод между счетами банка
    PAYMENT = "PAYMENT"  # Платёж внешнему получателю
    DEPOSIT = "DEPOSIT"  # Пополнение счёта
    WITHDRAWAL = "WITHDRAWAL"  # Снятие со счёта