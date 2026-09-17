"""Cache simple en CSV para barras mensuales, compartida entre fuentes de datos."""
from __future__ import annotations

import csv
from pathlib import Path

CACHE_DIR = Path(__file__).resolve().parent.parent / "cache"

FIELDNAMES = ["date", "open", "high", "low", "close", "volume"]


def cache_path(market: str, ticker: str) -> Path:
    safe_ticker = ticker.replace("/", "_")
    d = CACHE_DIR / market
    d.mkdir(parents=True, exist_ok=True)
    return d / f"{safe_ticker}.csv"


def read_cache(path: Path) -> list[dict] | None:
    if not path.exists():
        return None
    with path.open(newline="", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))
    return rows or None


def write_cache(path: Path, bars: list[dict]) -> None:
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=FIELDNAMES)
        writer.writeheader()
        writer.writerows(bars)
