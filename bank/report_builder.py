import csv
import json
import os
from collections import Counter
from datetime import datetime

from bank.abstract_account import AbstractAccount
from bank.enums.audit_severity import AuditSeverity
from bank.enums.risk_level import RiskLevel
from bank.exceptions import InvalidOperationError
from bank.exchange_rates import ExchangeRates
from bank.report_charts import balance_line, clients_bar, currency_pie, risk_bar


class ReportBuilder:
    DEFAULT_REPORT_DIR = "reports"
    DEFAULT_CHART_DIR = "charts"
    TOP_LIMIT = 5
    BASE_CURRENCY = "RUB"

    def __init__(self, bank, risk_analyzer=None, audit_log=None, clock=datetime.now,
                 base_currency=BASE_CURRENCY):
        self.bank = bank
        self.risk_analyzer = risk_analyzer
        self.audit_log = audit_log
        self.clock = clock
        self.base_currency = base_currency

    def _client_data(self, client_id):
        client = self.bank.get_client(client_id)
        totals = {}
        for account in client.accounts:
            totals[account.currency] = totals.get(account.currency, 0) + account._balance

        accounts = []
        for account in client.accounts:
            accounts.append({
                "acc_id": account.acc_id,
                "name": account.name,
                "currency": account.currency,
                "balance": account._balance,
                "status": account.status.value,
            })

        return {
            "client_id": client.client_id,
            "full_name": client.full_name,
            "status": client.status.value,
            "age": client.age,
            "accounts_count": len(client.accounts),
            "total_by_currency": totals,
            "total_in_base": self._to_base(totals),
            "accounts": accounts,
        }

    def _bank_data(self):
        accounts = self._all_accounts()

        clients_by_status = Counter()
        for client in self.bank.clients.values():
            clients_by_status[client.status.value] += 1

        accounts_by_status = Counter()
        for account in accounts:
            accounts_by_status[account.status.value] += 1

        totals = self.bank.get_total_balance()
        top_clients = []
        ranking = self.bank.get_clients_ranking(base_currency=self.base_currency)
        for place, client in enumerate(ranking[:self.TOP_LIMIT], 1):
            client_totals = {}
            for account in client.accounts:
                client_totals[account.currency] = client_totals.get(account.currency, 0) + account._balance
            top_clients.append({
                "place": place,
                "client_id": client.client_id,
                "full_name": client.full_name,
                "accounts_count": len(client.accounts),
                "total_by_currency": client_totals,
                "total_in_base": self._to_base(client_totals),
            })

        return {
            "bank_name": self.bank.name,
            "generated_at": self.clock().isoformat(timespec="seconds"),
            "base_currency": self.base_currency,
            "clients_count": len(self.bank.clients),
            "accounts_count": len(accounts),
            "operations_count": len(self.bank.history),
            "total_by_currency": totals,
            "total_in_base": self._to_base(totals),
            "share_in_base": self._share_in_base(totals),
            "clients_by_status": dict(clients_by_status),
            "accounts_by_status": dict(accounts_by_status),
            "top_clients": top_clients,
        }

    def _risk_data(self):
        assessments = self.risk_analyzer.assessments if self.risk_analyzer is not None else []

        by_level = Counter()
        by_indicator = Counter()
        suspicious_operations = []
        for assessment in assessments:
            by_level[assessment.level.label] += 1
            for indicator in assessment.indicators:
                by_indicator[indicator] += 1
            if assessment.level is RiskLevel.LOW:
                continue
            suspicious_operations.append({
                "time": assessment.time.isoformat(timespec="seconds"),
                "txn_id": assessment.txn.txn_id,
                "subject": assessment.subject,
                "amount": assessment.txn.amount,
                "currency": assessment.txn.currency,
                "status": assessment.txn.status.value,
                "level": assessment.level.label,
                "score": assessment.score,
                "indicators": list(assessment.indicators),
            })
        suspicious_operations.sort(key=lambda item: item["score"], reverse=True)

        blocked = []
        for txn, assessment in self.bank.blocked_transactions:
            blocked.append({
                "txn_id": txn.txn_id,
                "subject": assessment.subject,
                "amount": txn.amount,
                "currency": txn.currency,
                "reason": txn.rejection_reason,
            })

        suspicious_clients = []
        for client_id, reason in self.bank.suspicious_events:
            try:
                full_name = self.bank.get_client(client_id).full_name
            except InvalidOperationError:
                full_name = "неизвестный клиент"
            suspicious_clients.append({
                "client_id": client_id,
                "full_name": full_name,
                "reason": reason,
            })

        audit_by_severity = {}
        if self.audit_log is not None:
            for severity in AuditSeverity:
                audit_by_severity[severity.value] = len(self.audit_log.filter(severity=severity))

        return {
            "generated_at": self.clock().isoformat(timespec="seconds"),
            "assessments_count": len(assessments),
            "by_level": dict(by_level),
            "by_indicator": dict(by_indicator),
            "audit_by_severity": audit_by_severity,
            "suspicious_operations": suspicious_operations,
            "blocked_operations": blocked,
            "suspicious_clients": suspicious_clients,
        }

    def _balance_timeline(self):
        balances = {}
        points = []
        for entry in self.bank.history:
            for acc_id, snapshot in entry["balances"].items():
                balances[acc_id] = snapshot
            if not entry["balances"]:
                continue
            totals = {}
            for snapshot in balances.values():
                currency = snapshot["currency"]
                totals[currency] = totals.get(currency, 0) + snapshot["balance"]
            points.append({
                "time": entry["time"],
                "total": self._to_base(totals),
                "accounts": len(balances),
            })
        return points

    def transaction_rows(self):
        rows = []
        for entry in self.bank.history:
            txn = entry["txn"]
            if txn is None:
                continue
            rows.append({
                "time": entry["time"].strftime("%Y-%m-%d %H:%M:%S"),
                "event": entry["event"],
                "txn_id": txn.txn_id,
                "type": txn.txn_type.value,
                "status": entry["status"],
                "sender": self._party(txn.sender),
                "receiver": self._party(txn.receiver),
                "amount": txn.amount,
                "currency": txn.currency,
                "commission": txn.commission,
                "reason": txn.rejection_reason or "",
            })
        return rows

    def risk_rows(self):
        return [
            {
                "time": item["time"],
                "txn_id": item["txn_id"],
                "subject": item["subject"] or "",
                "amount": item["amount"],
                "currency": item["currency"],
                "level": item["level"],
                "score": item["score"],
                "status": item["status"],
                "indicators": ", ".join(item["indicators"]),
            }
            for item in self._risk_data()["suspicious_operations"]
        ]

    def client_report(self, client_id):
        data = self._client_data(client_id)
        acc_ids = {account["acc_id"] for account in data["accounts"]}
        operations = [row for row in self.transaction_rows()
                      if row["sender"] in acc_ids or row["receiver"] in acc_ids]

        lines = [
            f"Отчёт по клиенту {data['full_name']} ({data['client_id']})",
            f"Сформирован: {self.clock():%d.%m.%Y %H:%M}",
            "",
            f"Статус: {data['status']}",
            f"Возраст: {data['age']}",
            f"Счетов: {data['accounts_count']}",
        ]
        for currency, amount in data["total_by_currency"].items():
            lines.append(f"Итого {currency}: {amount:,.2f}")
        lines.append(f"Итого в {self.base_currency}: {data['total_in_base']:,.2f}")

        lines.append("")
        lines.append(f"{'Счёт':<10} {'Владелец':<14} {'Валюта':<8} {'Баланс':>16}  Статус")
        lines.append("-" * 72)
        for account in data["accounts"]:
            lines.append(
                f"{account['acc_id']:<10} {account['name']:<14} {account['currency']:<8} "
                f"{account['balance']:>16,.2f}  {account['status']}"
            )

        lines.append("")
        lines.append(f"Операций по счетам клиента: {len(operations)}")
        lines.append(f"{'Время':<20} {'Тип':<10} {'Сумма':>14} {'Валюта':<8} {'Статус':<10}")
        for row in operations:
            lines.append(
                f"{row['time']:<20} {row['type']:<10} {row['amount']:>14,.2f} "
                f"{row['currency']:<8} {row['status']:<10}"
            )
        return "\n".join(lines)

    def bank_report(self):
        data = self._bank_data()
        lines = [
            f"Отчёт по банку «{data['bank_name']}»",
            f"Сформирован: {data['generated_at']}",
            "",
            f"Клиентов: {data['clients_count']}",
            f"Счетов: {data['accounts_count']}",
            f"Операций в журнале: {data['operations_count']}",
            "",
            f"Баланс по валютам (всего в {self.base_currency}: {data['total_in_base']:,.2f}):",
        ]
        for currency, amount in data["total_by_currency"].items():
            lines.append(f"  {currency}: {amount:,.2f}")

        lines.append("")
        lines.append("Счета по статусам: "
                     + ", ".join(f"{name} — {count}" for name, count in data["accounts_by_status"].items()))
        lines.append("Клиенты по статусам: "
                     + ", ".join(f"{name} — {count}" for name, count in data["clients_by_status"].items()))

        lines.append("")
        lines.append(f"Топ-{len(data['top_clients'])} клиентов по остаткам:")
        lines.append(f"{'#':<3} {'Клиент':<14} {'ID':<8} {'Счетов':>6} {self.base_currency:>18}")
        for item in data["top_clients"]:
            lines.append(
                f"{item['place']:<3} {item['full_name']:<14} {item['client_id']:<8} "
                f"{item['accounts_count']:>6} {item['total_in_base']:>18,.2f}"
            )
        return "\n".join(lines)

    def risk_report(self):
        data = self._risk_data()
        lines = [
            "Отчёт по рискам",
            f"Сформирован: {data['generated_at']}",
            "",
            f"Оценок риска: {data['assessments_count']}",
        ]
        for level, count in data["by_level"].items():
            lines.append(f"  {level}: {count}")

        if data["by_indicator"]:
            lines.append("")
            lines.append("Признаки риска:")
            for indicator, count in sorted(data["by_indicator"].items(), key=lambda pair: -pair[1]):
                lines.append(f"  {indicator}: {count}")

        if data["audit_by_severity"]:
            lines.append("")
            lines.append("Записи аудита по важности:")
            for severity, count in data["audit_by_severity"].items():
                if count:
                    lines.append(f"  {severity}: {count}")

        lines.append("")
        lines.append(f"Подозрительные операции ({len(data['suspicious_operations'])}):")
        lines.append(f"{'Время':<20} {'Счёт':<10} {'Сумма':>14} {'Риск':<10} {'Баллы':>6}")
        for item in data["suspicious_operations"]:
            lines.append(
                f"{item['time']:<20} {item['subject'] or '-':<10} {item['amount']:>14,.2f} "
                f"{item['level']:<10} {item['score']:>6}"
            )

        lines.append("")
        lines.append(f"Заблокированные операции ({len(data['blocked_operations'])}):")
        for item in data["blocked_operations"]:
            lines.append(f"  {item['txn_id']} на {item['amount']:,.2f} {item['currency']}: {item['reason']}")

        lines.append("")
        lines.append(f"Клиенты под подозрением ({len(data['suspicious_clients'])}):")
        for item in data["suspicious_clients"]:
            lines.append(f"  {item['full_name']} ({item['client_id']}): {item['reason']}")
        return "\n".join(lines)

    def all_data(self, client_id=None):
        data = {"bank": self._bank_data(), "risk": self._risk_data()}
        if client_id is not None:
            data["client"] = self._client_data(client_id)
        return data

    def all_reports(self, client_id=None):
        reports = {"bank": self.bank_report(), "risk": self.risk_report()}
        if client_id is not None:
            reports["client"] = self.client_report(client_id)
        return reports

    def export_to_json(self, data, file_path):
        if not isinstance(data, dict):
            raise InvalidOperationError(f"Ожидался словарь, получено {type(data).__name__}")

        self._prepare_file(file_path)
        with open(file_path, "w", encoding="utf-8") as fh:
            json.dump(data, fh, ensure_ascii=False, indent=2)
        return file_path

    def export_to_csv(self, rows, file_path, fieldnames=None):
        if not rows:
            return None

        if fieldnames is None:
            fieldnames = list(rows[0].keys())
        elif not isinstance(fieldnames, (list, tuple)):
            raise InvalidOperationError(f"Ожидался список названий колонок, получено {fieldnames}")

        self._prepare_file(file_path)
        with open(file_path, "w", encoding="utf-8", newline="") as fh:
            writer = csv.DictWriter(fh, fieldnames=fieldnames)
            writer.writeheader()
            for row in rows:
                writer.writerow(row if isinstance(row, dict) else dict(zip(fieldnames, row)))
        return file_path

    def save_charts(self, directory=None):
        directory = directory or self.DEFAULT_CHART_DIR
        self._prepare_dir(directory)

        bank_data = self._bank_data()
        risk_data = self._risk_data()
        saved = [
            currency_pie(bank_data["share_in_base"],
                         os.path.join(directory, "currency_share.png")),
            clients_bar(bank_data["top_clients"],
                        os.path.join(directory, "top_clients.png")),
            risk_bar(risk_data["by_level"],
                     os.path.join(directory, "risk_levels.png")),
            balance_line(self._balance_timeline(),
                         os.path.join(directory, "balance_dynamics.png")),
        ]
        return [path for path in saved if path]

    def export_all(self, client_id=None, directory=None):
        directory = directory or self.DEFAULT_REPORT_DIR
        candidates = {
            "json": self.export_to_json(self.all_data(client_id),
                                        os.path.join(directory, "reports.json")),
            "transactions_csv": self.export_to_csv(self.transaction_rows(),
                                                   os.path.join(directory, "transactions.csv")),
            "risks_csv": self.export_to_csv(self.risk_rows(),
                                            os.path.join(directory, "risks.csv")),
        }
        paths = {name: path for name, path in candidates.items() if path}
        if client_id is not None:
            self.save_reports(self.all_reports(client_id), directory)
            paths["text"] = directory
        return paths

    def save_reports(self, reports, directory=None):
        directory = directory or self.DEFAULT_REPORT_DIR
        self._prepare_dir(directory)
        paths = {}
        for name, text in reports.items():
            path = os.path.join(directory, f"{name}_report.txt")
            with open(path, "w", encoding="utf-8") as fh:
                fh.write(text)
            paths[name] = path
        return paths

    def _share_in_base(self, totals_by_currency):
        return {currency: self._to_base({currency: amount})
                for currency, amount in totals_by_currency.items()}

    def _to_base(self, totals_by_currency):
        total = 0.0
        for currency, amount in totals_by_currency.items():
            total += ExchangeRates.convert(amount, currency, self.base_currency)
        return round(total, 2)

    def _all_accounts(self):
        accounts = []
        for client in self.bank.clients.values():
            accounts.extend(client.accounts)
        return accounts

    def _party(self, account):
        if isinstance(account, AbstractAccount):
            return account.acc_id
        if account is None:
            return ""
        return str(account)

    @staticmethod
    def _prepare_file(path):
        directory = os.path.dirname(path)
        if directory:
            os.makedirs(directory, exist_ok=True)

    @staticmethod
    def _prepare_dir(path):
        os.makedirs(path, exist_ok=True)
