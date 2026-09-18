from collections import Counter

from bank.enums.audit_severity import AuditSeverity
from bank.enums.risk_level import RiskLevel


def suspicious(risk_analyzer, min_level=RiskLevel.MEDIUM):
    return sorted(
        (a for a in risk_analyzer.assessments if a.level.value >= min_level.value),
        key=lambda a: a.score, reverse=True)


def client_profiles(risk_analyzer):
    profiles = {}
    for a in risk_analyzer.assessments:
        p = profiles.setdefault(a.subject, {"transactions": 0, "max_level": RiskLevel.LOW, "suspicious": 0, "score": 0})
        p["transactions"] += 1
        p["max_level"] = a.level if a.level.value > p["max_level"].value else p["max_level"]
        p["suspicious"] += a.level.value >= RiskLevel.MEDIUM.value
        p["score"] += a.score
    return profiles


def error_statistics(processor=None, audit_log=None):
    reasons = Counter()
    if processor is not None:
        reasons.update(reason for _, reason, _ in processor.error_log)
    if audit_log is not None:
        reasons.update(e["message"] for e in audit_log.filter(min_severity=AuditSeverity.ERROR))
    return reasons
