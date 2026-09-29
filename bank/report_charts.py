import os

import matplotlib

matplotlib.use("Agg")

import matplotlib.dates as mdates
import matplotlib.pyplot as plt

FIGURE_SIZE = (10, 5.5)
LINE_WIDTH = 2
GRID_ALPHA = 0.3


def currency_pie(share_in_base, path, title="Структура баланса банка"):
    if not share_in_base:
        return None

    fig, ax = plt.subplots(figsize=FIGURE_SIZE)
    ax.pie(
        list(share_in_base.values()),
        labels=[f"{currency}\n{amount:,.0f}" for currency, amount in share_in_base.items()],
        autopct="%1.1f%%",
        startangle=140,
    )
    ax.set_title(title)
    fig.tight_layout()
    return _finish(fig, path)


def clients_bar(top_clients, path, title="Топ клиентов по остаткам"):
    if not top_clients:
        return None

    names = [item["full_name"] for item in top_clients][::-1]
    totals = [item["total_in_base"] for item in top_clients][::-1]

    fig, ax = plt.subplots(figsize=FIGURE_SIZE)
    bars = ax.barh(names, totals, color="steelblue")
    ax.set_title(title)
    ax.set_xlabel("Остаток, RUB")
    ax.grid(axis="x", alpha=GRID_ALPHA)
    ax.bar_label(bars, labels=[f"{total:,.0f}" for total in totals], padding=3)
    fig.tight_layout()
    return _finish(fig, path)


def risk_bar(by_level, path, title="Распределение операций по уровню риска"):
    if not by_level:
        return None

    levels = ["Низкий", "Средний", "Высокий"]
    counts = [by_level.get(level, 0) for level in levels]
    colors = ["#5cb85c", "#f0ad4e", "#d9534f"]

    fig, ax = plt.subplots(figsize=FIGURE_SIZE)
    bars = ax.bar(levels, counts, color=colors)
    ax.set_title(title)
    ax.set_ylabel("Количество операций")
    ax.grid(axis="y", alpha=GRID_ALPHA)
    for bar, count in zip(bars, counts):
        ax.text(bar.get_x() + bar.get_width() / 2, bar.get_height(), str(count),
                ha="center", va="bottom")
    fig.tight_layout()
    return _finish(fig, path)


def balance_line(timeline, path, title="Движение баланса банка"):
    if len(timeline) < 2:
        return None

    times = [point["time"] for point in timeline]
    totals = [point["total"] for point in timeline]

    fig, ax = plt.subplots(figsize=FIGURE_SIZE)
    ax.plot(times, totals, color="darkgreen", marker="o", markersize=4, linewidth=LINE_WIDTH)
    ax.fill_between(times, totals, alpha=0.15, color="darkgreen")
    ax.set_title(title)
    ax.set_ylabel("Суммарный баланс, RUB")
    ax.set_xlabel("Время")
    ax.grid(alpha=GRID_ALPHA)
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%d.%m %H:%M"))
    fig.autofmt_xdate()
    fig.tight_layout()
    return _finish(fig, path)


def _finish(fig, path):
    directory = os.path.dirname(path)
    if directory:
        os.makedirs(directory, exist_ok=True)
    fig.savefig(path, dpi=120)
    plt.close(fig)
    return path
