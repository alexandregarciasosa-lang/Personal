"""Carga y actualizacion de las listas de constituyentes por mercado.

Los CSV en data/ son la fuente que usa el resto del pipeline. Son listas
"semilla" (no necesariamente completas): sp500_constituents.csv puede
regenerarse automaticamente desde Wikipedia con update_sp500_from_wikipedia();
stoxx600_constituents.csv no tiene una fuente publica estructurada y
confiable, asi que se mantiene a mano (ver README para como ampliarlo con
el factsheet oficial de STOXX).
"""
from __future__ import annotations

import csv
from dataclasses import dataclass
from pathlib import Path

DATA_DIR = Path(__file__).resolve().parent.parent / "data"

SP500_CSV = DATA_DIR / "sp500_constituents.csv"
STOXX600_CSV = DATA_DIR / "stoxx600_constituents.csv"

WIKIPEDIA_SP500_URL = "https://en.wikipedia.org/wiki/List_of_S%26P_500_companies"


@dataclass(frozen=True)
class Constituent:
    ticker: str
    name: str
    exchange: str
    currency: str


def _load_csv(path: Path) -> list[Constituent]:
    if not path.exists():
        raise FileNotFoundError(
            f"No se encontro {path}. Corre primero el fetch de constituyentes "
            "correspondiente o crea el CSV manualmente."
        )
    with path.open(newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        return [
            Constituent(
                ticker=row["ticker"].strip(),
                name=row["name"].strip(),
                exchange=row["exchange"].strip(),
                currency=row["currency"].strip(),
            )
            for row in reader
        ]


def load_sp500() -> list[Constituent]:
    return _load_csv(SP500_CSV)


def load_stoxx600() -> list[Constituent]:
    return _load_csv(STOXX600_CSV)


MARKETS = {
    "us": ("S&P 500", load_sp500),
    "eu": ("STOXX Europe 600", load_stoxx600),
}


def update_sp500_from_wikipedia(output_path: Path = SP500_CSV) -> int:
    """Regenera sp500_constituents.csv leyendo la tabla de Wikipedia.

    Requiere acceso a internet y pandas+lxml instalados. Se corre a mano
    (no como parte del pipeline principal) porque IBKR no expone la
    composicion de indices via API.
    """
    import pandas as pd

    tables = pd.read_html(WIKIPEDIA_SP500_URL)
    table = tables[0]

    rows = []
    for _, r in table.iterrows():
        ticker = str(r["Symbol"]).strip().replace(".", " ").replace(" ", ".")
        name = str(r["Security"]).strip()
        rows.append((ticker, name, "SMART", "USD"))

    with output_path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["ticker", "name", "exchange", "currency"])
        writer.writerows(rows)

    return len(rows)


if __name__ == "__main__":
    n = update_sp500_from_wikipedia()
    print(f"Escribi {n} tickers del S&P 500 en {SP500_CSV}")
