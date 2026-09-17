"""Descarga de barras mensuales historicas desde Yahoo Finance (yfinance).

No requiere ninguna terminal/gateway corriendo, solo internet. Es mas
liviano que IBKR pero puede devolver datos vacios o con delay para algunos
tickers europeos de menor liquidez, y Yahoo puede limitar la tasa de
pedidos si se hacen muchos seguidos (de ahi el pacing y los reintentos).
"""
from __future__ import annotations

import time

from .cache import cache_path, read_cache, write_cache
from .constituents import Constituent

PACING_SECONDS = 0.5
MAX_RETRIES = 2


def _fetch_one(yf_ticker: str, years: int):
    import yfinance as yf

    last_exc = None
    for attempt in range(1, MAX_RETRIES + 1):
        try:
            hist = yf.Ticker(yf_ticker).history(period=f"{years}y", interval="1mo", auto_adjust=False)
            return hist
        except Exception as exc:  # noqa: BLE001
            last_exc = exc
            time.sleep(PACING_SECONDS * attempt)
    raise last_exc


def fetch_monthly_bars(
    market: str,
    constituents: list[Constituent],
    years: int = 3,
    force_refresh: bool = False,
    pacing_seconds: float = PACING_SECONDS,
    **_ignored,
) -> dict[str, list[dict]]:
    """Devuelve {ticker: [{date, open, high, low, close, volume}, ...]}.

    Cada corrida usa cache/<market>/<ticker>.csv; si ya existe y
    force_refresh es False, no vuelve a pedirle datos a Yahoo para ese ticker.
    La clave del resultado es el ticker "propio" (columna ticker del CSV),
    no el yf_ticker usado para consultar Yahoo.
    """
    results: dict[str, list[dict]] = {}

    for c in constituents:
        cache_file = cache_path(market, c.ticker)
        if not force_refresh:
            cached = read_cache(cache_file)
            if cached:
                results[c.ticker] = cached
                continue

        try:
            hist = _fetch_one(c.yf_ticker, years)
            if hist.empty:
                print(f"[{market}] sin datos para {c.ticker} ({c.yf_ticker}), salteo")
                continue

            rows = [
                {
                    "date": idx.strftime("%Y-%m"),
                    "open": row["Open"],
                    "high": row["High"],
                    "low": row["Low"],
                    "close": row["Close"],
                    "volume": row["Volume"],
                }
                for idx, row in hist.iterrows()
            ]
            write_cache(cache_file, rows)
            results[c.ticker] = rows
            print(f"[{market}] {c.ticker}: {len(rows)} barras mensuales")
        except Exception as exc:  # noqa: BLE001 - seguimos con el resto de tickers
            print(f"[{market}] error con {c.ticker} ({c.yf_ticker}): {exc}")
        finally:
            time.sleep(pacing_seconds)

    return results
