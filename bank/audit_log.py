import json
import os
from datetime import datetime

from bank.enums.audit_severity import AuditSeverity


class AuditLog:
    DEFAULT_DIR = "audit"

    def __init__(self, file_path=None, clock=datetime.now):
        self.file_path = self._resolve_path(file_path)
        self.clock = clock
        self.entries = []

    @classmethod
    def _resolve_path(cls, file_path):
        if file_path is None or os.path.dirname(file_path):
            return file_path
        return os.path.join(cls.DEFAULT_DIR, file_path)

    @staticmethod
    def _ensure_dir(path):
        directory = os.path.dirname(path)
        if directory:
            os.makedirs(directory, exist_ok=True)

    def log(self, severity, message):
        entry = {
            "timestamp": self.clock().isoformat(),
            "severity": severity.value,
            "message": message,
        }
        self.entries.append(entry)
        if self.file_path:
            self._ensure_dir(self.file_path)
            with open(self.file_path, "a", encoding="utf-8") as fh:
                fh.write(json.dumps(entry, ensure_ascii=False) + "\n")
        return entry

    def info(self, message):
        return self.log(AuditSeverity.INFO, message)

    def warning(self, message):
        return self.log(AuditSeverity.WARNING, message)

    def error(self, message):
        return self.log(AuditSeverity.ERROR, message)

    def critical(self, message):
        return self.log(AuditSeverity.CRITICAL, message)

    def filter(self, severity=None, min_severity=None, start=None, end=None, query=None):
        result = []
        for entry in self.entries:
            timestamp = datetime.fromisoformat(entry["timestamp"])
            if severity is not None and entry["severity"] != severity.value:
                continue
            if min_severity is not None and entry["severity"] < min_severity.value:
                continue
            if start is not None and timestamp < start:
                continue
            if end is not None and timestamp > end:
                continue
            if query is not None and query.lower() not in entry["message"].lower():
                continue
            result.append(entry)
        return result

    def save(self, file_path=None):
        path = self._resolve_path(file_path or self.file_path)
        if path is None:
            raise ValueError("Не указан путь для сохранения журнала")
        self._ensure_dir(path)
        with open(path, "w", encoding="utf-8") as fh:
            for entry in self.entries:
                fh.write(json.dumps(entry, ensure_ascii=False) + "\n")
        self.file_path = path
        return path

    @classmethod
    def load(cls, file_path):
        path = cls._resolve_path(file_path)
        log = cls(path)
        with open(path, encoding="utf-8") as fh:
            for line in fh:
                if line.strip():
                    log.entries.append(json.loads(line))
        return log

    def __len__(self):
        return len(self.entries)

    def __iter__(self):
        return iter(self.entries)
