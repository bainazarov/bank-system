from enum import Enum


class AuditSeverity(Enum):
    INFO = 10  # Информационное событие
    WARNING = 20  # Предупреждение
    ERROR = 30  # Ошибка
    CRITICAL = 40  # Критическое событие

    @property
    def label(self):
        return {
            AuditSeverity.INFO: "Инфо",
            AuditSeverity.WARNING: "Предупреждение",
            AuditSeverity.ERROR: "Ошибка",
            AuditSeverity.CRITICAL: "Критично",
        }[self]