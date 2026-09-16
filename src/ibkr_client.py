"""Descarga de barras mensuales historicas desde Interactive Brokers (TWS/IB Gateway).

Usa ib_async (fork mantenido de ib_insync). Requiere que TWS o IB Gateway
este corriendo localmente con la API habilitada (Configure > API > Settings
> Enable ActiveX and Socket Clients) y, para las acciones europeas, las
suscripciones de market data de las bolsas correspondientes (LSE, Xetra,
Euronext, SIX, etc.) activas en la cuenta.

IBKR aplica "pacing limits" sobre reqHistoricalData (aprox. 60 requests
cada 10 minutos, y no mas de 1 request identico cada 15s). Este modulo
espacia los pedidos con PACING_SECONDS y cachea cada ticker en un CSV para
que una corrida interrumpida se pueda resumir sin repetir trabajo.
"""
from __future__ import annotations

import csv
import time
from pathlib import Path

from .constituents import Constituent

CACHE_DIR = Path(__file__).resolve().parent.parent / "cache"

PACING_SECONDS = 1.5  # tiempo minimo entre reqHistoricalData sucesivos


def _cache_path(market: str, ticker: str) -> Path:
    safe_ticker = ticker.replace("/", "_")
    d = CACHE_DIR / market
    d.mkdir(parents=True, exist_ok=True)
    return d / f"{safe_ticker}.csv"


def _read_cache(path: Path) -> list[dict] | None:
    if not path.exists():
        return None
    with path.open(newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def _write_cache(path: Path, bars: list[dict]) -> None:
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["date", "open", "high", "low", "close", "volume"])
        writer.writeheader()
        writer.writerows(bars)


def fetch_monthly_bars(
    market: str,
    constituents: list[Constituent],
    years: int = 3,
    host: str = "127.0.0.1",
    port: int = 7497,
    client_id: int = 17,
    force_refresh: bool = False,
    pacing_seconds: float = PACING_SECONDS,
) -> dict[str, list[dict]]:
    """Devuelve {ticker: [{date, open, high, low, close, volume}, ...]}.

    Cada corrida usa cache/<market>/<ticker>.csv; si ya existe y
    force_refresh es False, no vuelve a pedirle datos a IBKR para ese ticker.
    """
    from ib_async import IB, Stock

    results: dict[str, list[dict]] = {}
    pending = []
    for c in constituents:
        cache_file = _cache_path(market, c.ticker)
        if not force_refresh:
            cached = _read_cache(cache_file)
            if cached:
                results[c.ticker] = cached
                continue
        pending.append(c)

    if not pending:
        return results

    ib = IB()
    ib.connect(host, port, clientId=client_id)
    try:
        for c in pending:
            contract = Stock(c.ticker, c.exchange, c.currency)
            try:
                qualified = ib.qualifyContracts(contract)
                if not qualified:
                    print(f"[{market}] no pude resolver el contrato de {c.ticker}, salteo")
                    continue

                bars = ib.reqHistoricalData(
                    qualified[0],
                    endDateTime="",
                    durationStr=f"{years} Y",
                    barSizeSetting="1 month",
                    whatToShow="TRADES",
                    useRTH=True,
                    formatDate=1,
                )
                if not bars:
                    print(f"[{market}] sin barras para {c.ticker}, salteo")
                    continue

                rows = [
                    {
                        "date": b.date.strftime("%Y-%m") if hasattr(b.date, "strftime") else str(b.date)[:7],
                        "open": b.open,
                        "high": b.high,
                        "low": b.low,
                        "close": b.close,
                        "volume": b.volume,
                    }
                    for b in bars
                ]
                _write_cache(_cache_path(market, c.ticker), rows)
                results[c.ticker] = rows
                print(f"[{market}] {c.ticker}: {len(rows)} barras mensuales")
            except Exception as exc:  # noqa: BLE001 - seguimos con el resto de tickers
                print(f"[{market}] error con {c.ticker}: {exc}")
            finally:
                time.sleep(pacing_seconds)
    finally:
        ib.disconnect()

    return results
