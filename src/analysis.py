"""Calculo del mejor performer por mes a partir de barras mensuales."""
from __future__ import annotations

from collections import defaultdict

from .constituents import Constituent


def monthly_returns(bars_by_ticker: dict[str, list[dict]]) -> dict[str, dict[str, float]]:
    """{mes (YYYY-MM): {ticker: retorno_pct}}"""
    out: dict[str, dict[str, float]] = defaultdict(dict)
    for ticker, bars in bars_by_ticker.items():
        for b in bars:
            try:
                open_ = float(b["open"])
                close = float(b["close"])
            except (TypeError, ValueError):
                continue
            if open_ <= 0:
                continue
            ret = (close - open_) / open_ * 100.0
            out[b["date"]][ticker] = ret
    return dict(out)


def best_per_month(
    returns_by_month: dict[str, dict[str, float]],
    constituents: list[Constituent],
) -> list[dict]:
    """Devuelve una fila por mes con el ticker de mejor retorno, ordenado por mes."""
    names = {c.ticker: c.name for c in constituents}
    rows = []
    for month in sorted(returns_by_month):
        month_returns = returns_by_month[month]
        if not month_returns:
            continue
        best_ticker = max(month_returns, key=month_returns.get)
        rows.append(
            {
                "month": month,
                "ticker": best_ticker,
                "name": names.get(best_ticker, best_ticker),
                "return_pct": round(month_returns[best_ticker], 2),
            }
        )
    return rows
