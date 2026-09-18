from collections import deque
from datetime import datetime, timedelta

from bank.enums.risk_level import RiskLevel
from bank.enums.transaction_type import TransactionType


class RiskAssessment:
    def __init__(self, txn, subject, level, score, indicators, time):
        self.txn = txn
        self.subject = subject
        self.level = level
        self.score = score
        self.indicators = list(indicators)
        self.time = time

    def __str__(self):
        marks = ", ".join(self.indicators) if self.indicators else "норма"
        return f"риск={self.level.label} баллы={self.score} [{marks}]"


class RiskAnalyzer:
    POINTS = {"large": 60, "night": 50, "new_account": 30, "frequent": 30}

    def __init__(self, clock=datetime.now, large_limit=100000, freq_limit=3,
                 freq_window_minutes=10):
        self.clock = clock
        self.large_limit = large_limit
        self.freq_limit = freq_limit
        self.freq_window = timedelta(minutes=freq_window_minutes)
        self.assessments = []
        self._history = {}
        self._receivers = {}

    def assess(self, txn):
        now = self.clock()
        score, indicators = 0, []
        subject = self._subject(txn)

        if txn.amount >= self.large_limit:
            score += self.POINTS["large"]
            indicators.append("крупная сумма")
        if self._is_night(now):
            score += self.POINTS["night"]
            indicators.append("операция ночью")

        receiver = self._receiver(txn)
        if receiver and txn.txn_type in (TransactionType.TRANSFER, TransactionType.PAYMENT):
            known = self._receivers.setdefault(subject, set())
            if receiver not in known:
                score += self.POINTS["new_account"]
                indicators.append("перевод на новый счёт")
            known.add(receiver)

        times = self._history.setdefault(subject, deque())
        while times and now - times[0] > self.freq_window:
            times.popleft()
        times.append(now)
        if sum(1 for t in times if now - t <= self.freq_window) >= self.freq_limit:
            score += self.POINTS["frequent"]
            indicators.append("частые операции")

        if score >= 80:
            level = RiskLevel.HIGH
        elif score >= 40:
            level = RiskLevel.MEDIUM
        else:
            level = RiskLevel.LOW

        assessment = RiskAssessment(txn, subject, level, score, indicators, now)
        self.assessments.append(assessment)
        return assessment

    def _is_night(self, now):
        return now.hour >= 23 or now.hour < 5

    def _subject(self, txn):
        return getattr(txn.sender, "acc_id", None) or getattr(txn.receiver, "acc_id", None)

    def _receiver(self, txn):
        return getattr(txn.receiver, "acc_id", None) or txn.receiver