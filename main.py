#!/usr/bin/env python3
"""Mejor accion por mes: S&P 500 (US) vs STOXX Europe 600 (EU), via Yahoo Finance.

Ejemplos:
    python main.py --market us --years 2
    python main.py --market eu --years 1
    python main.py --market both --years 3 --csv out.csv
"""
from __future__ import annotations

import argparse
import csv as csv_module
import sys
from pathlib import Path

from src.analysis import best_per_month, monthly_returns
from src.constituents import MARKETS
from src.yfinance_client import fetch_monthly_bars


def run_market(market_key: str, args: argparse.Namespace) -> list[dict]:
    label, loader = MARKETS[market_key]
    constituents = loader()
    if args.limit:
        constituents = constituents[: args.limit]

    print(f"\n=== {label} ({len(constituents)} tickers) ===")
    bars_by_ticker = fetch_monthly_bars(
        market=market_key,
        constituents=constituents,
        years=args.years,
        force_refresh=args.force_refresh,
        pacing_seconds=args.pacing,
    )
    returns = monthly_returns(bars_by_ticker)
    rows = best_per_month(returns, constituents)
    for r in rows:
        print(f"{r['month']}  {r['ticker']:<8} {r['name']:<35} {r['return_pct']:+.2f}%")
    return rows


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--market", choices=["us", "eu", "both"], default="both")
    parser.add_argument("--years", type=int, default=2, help="anios de historia a pedir (default: 2)")
    parser.add_argument("--limit", type=int, default=None, help="limitar cantidad de tickers (para pruebas rapidas)")
    parser.add_argument("--pacing", type=float, default=0.5, help="segundos de espera entre pedidos a Yahoo Finance")
    parser.add_argument("--force-refresh", action="store_true", help="ignorar cache y volver a pedir todo a Yahoo Finance")
    parser.add_argument("--csv", type=Path, default=None, help="ruta para exportar el resultado combinado a CSV")
    args = parser.parse_args()

    markets = ["us", "eu"] if args.market == "both" else [args.market]

    all_rows = []
    for m in markets:
        rows = run_market(m, args)
        for r in rows:
            r["market"] = m
        all_rows.extend(rows)

    if args.csv:
        with args.csv.open("w", newline="", encoding="utf-8") as f:
            writer = csv_module.DictWriter(f, fieldnames=["market", "month", "ticker", "name", "return_pct"])
            writer.writeheader()
            writer.writerows(all_rows)
        print(f"\nExportado a {args.csv}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
