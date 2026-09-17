# Mejor accion por mes: EE.UU. vs Europa

Calcula, para cada mes, que accion tuvo el mejor retorno dentro del S&P 500
(EE.UU.) y dentro del STOXX Europe 600 (Europa), usando datos historicos de
Yahoo Finance (via `yfinance`).

## Como funciona

1. `data/sp500_constituents.csv` y `data/stoxx600_constituents.csv` listan
   los tickers a comparar (`ticker`, `name`, `yf_ticker` -- este ultimo es el
   simbolo tal como lo espera Yahoo Finance, p. ej. `BRK.B` -> `BRK-B`,
   `SAP` -> `SAP.DE`).
2. `src/yfinance_client.py` pide barras **mensuales** (open/close del mes)
   para cada ticker con `yfinance`, con pacing y reintentos. Cachea cada
   ticker en `cache/<market>/<ticker>.csv` para poder resumir una corrida
   interrumpida sin repetir pedidos.
3. `src/analysis.py` calcula el retorno mensual `(close - open) / open` por
   ticker y, para cada mes, elige el de mayor retorno.
4. `main.py` orquesta todo y muestra/exporta el resultado.

## Requisitos

- Python 3.10+
- Conexion a internet (no necesita ninguna terminal/gateway corriendo).

```bash
pip install -r requirements.txt
```

## Uso

```bash
# Ambos mercados, 2 anios de historia
python main.py --market both --years 2

# Solo Europa
python main.py --market eu --years 3

# Prueba rapida con pocos tickers
python main.py --market us --limit 10

# Exportar resultado combinado a CSV
python main.py --market both --csv resultado.csv

# Forzar refetch ignorando la cache
python main.py --market both --force-refresh
```

Salida (por mercado, ordenada por mes):

```
=== S&P 500 (50 tickers) ===
2024-01  NVDA     NVIDIA Corp                         +24.15%
2024-02  META     Meta Platforms Inc                  +18.32%
...
```

## Estado de verificacion

- La logica de calculo (`src/analysis.py`) y la carga de constituyentes
  (`src/constituents.py`) estan testeadas.
- El pipeline completo (`main.py` + `src/yfinance_client.py`, incluyendo
  cache resumible y export a CSV) se probo de punta a punta con respuestas
  de `yfinance` simuladas (mock), porque el entorno donde se desarrollo esto
  no tiene salida de red a Yahoo Finance.
- Lo unico que **no** se verifico todavia es una corrida real contra la API
  de Yahoo Finance. Corre `python main.py --market us --limit 5` como primera
  prueba: si ves barras mensuales y un ganador por mes, esta funcionando.

## Limitaciones y como ampliarlas

- **Listas de constituyentes**: son listas semilla (50 tickers cada una),
  no exhaustivas.
  - S&P 500: se puede regenerar completa desde Wikipedia con
    `python -m src.constituents` (requiere internet y `pandas`/`lxml`).
  - STOXX Europe 600: Wikipedia no tiene una tabla publica confiable con
    los ~600 tickers, asi que `data/stoxx600_constituents.csv` es una
    seleccion manual de large/mid caps. Para la lista completa, descarga el
    factsheet oficial (PDF/Excel) desde stoxx.com o un export de tu
    plataforma de datos, y complete el CSV con las mismas columnas
    (`ticker,name,yf_ticker`), buscando el simbolo de Yahoo Finance de cada
    empresa (sufijo segun la bolsa: `.L` Londres, `.PA` Paris, `.DE` Xetra,
    `.MI` Milan, `.AS` Amsterdam, `.MC` Madrid, `.SW` Suiza, `.CO`
    Copenhague, `.BR` Bruselas).
- **Rate limits de Yahoo Finance**: pedir barras mensuales para 500-600
  tickers puede tardar y, si se hace muy rapido, Yahoo puede empezar a
  devolver errores o datos vacios. La cache en `cache/` permite cortar y
  resumir la corrida; si ves muchos "sin datos" o errores, subi `--pacing`.
- **"Mejor performer"** se define como mayor retorno mensual `(close-open)/open`
  de la barra mensual (`auto_adjust=False`, ajustado por splits pero no por
  dividendos).
