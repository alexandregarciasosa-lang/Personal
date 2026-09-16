# Mejor accion por mes: EE.UU. vs Europa

Calcula, para cada mes, que accion tuvo el mejor retorno dentro del S&P 500
(EE.UU.) y dentro del STOXX Europe 600 (Europa), usando datos historicos de
Interactive Brokers.

## Como funciona

1. `data/sp500_constituents.csv` y `data/stoxx600_constituents.csv` listan
   los tickers a comparar (ticker, nombre, exchange y moneda en formato IBKR).
2. `src/ibkr_client.py` se conecta a TWS/IB Gateway y pide barras **mensuales**
   (open/close del mes) para cada ticker, con pacing para respetar los limites
   de IBKR. Cachea cada ticker en `cache/<market>/<ticker>.csv` para poder
   resumir una corrida interrumpida sin repetir pedidos.
3. `src/analysis.py` calcula el retorno mensual `(close - open) / open` por
   ticker y, para cada mes, elige el de mayor retorno.
4. `main.py` orquesta todo y muestra/exporta el resultado.

## Requisitos

- Python 3.10+
- TWS o IB Gateway corriendo localmente (paper o real), con la API habilitada:
  `Configure > API > Settings > Enable ActiveX and Socket Clients`.
- Suscripciones de market data activas para las bolsas que quieras consultar
  (EE.UU. para el S&P 500; LSE, Xetra/IBIS, Euronext, SIX, Borsa Italiana,
  BME, etc. para el STOXX 600). Sin la suscripcion correspondiente, IBKR
  puede devolver datos vacios o demorados para esos tickers.

```bash
pip install -r requirements.txt
```

## Uso

```bash
# Ambos mercados, 2 anios de historia, contra TWS paper (puerto 7497 por defecto)
python main.py --market both --years 2

# Solo Europa, contra IB Gateway paper (puerto 4002)
python main.py --market eu --port 4002

# Prueba rapida con pocos tickers
python main.py --market us --limit 10

# Exportar resultado combinado a CSV
python main.py --market both --csv resultado.csv
```

Puertos tipicos: `7497` TWS paper, `7496` TWS real, `4002` Gateway paper,
`4001` Gateway real.

Salida (por mercado, ordenada por mes):

```
=== S&P 500 (50 tickers) ===
2024-01  NVDA     NVIDIA Corp                         +24.15%
2024-02  META     Meta Platforms Inc                  +18.32%
...
```

## Limitaciones y como ampliarlas

- **Listas de constituyentes**: son listas semilla, no exhaustivas.
  - S&P 500: se puede regenerar completa desde Wikipedia con
    `python -m src.constituents` (requiere internet y `pandas`/`lxml`).
  - STOXX Europe 600: Wikipedia no tiene una tabla publica confiable con
    los ~600 tickers, asi que `data/stoxx600_constituents.csv` es una
    seleccion manual de large/mid caps. Para la lista completa, descarga el
    factsheet oficial (PDF/Excel) desde stoxx.com o un export de tu
    plataforma de datos, y complete el CSV con las mismas columnas
    (`ticker,name,exchange,currency`) usando el ticker y exchange que IBKR
    reconozca (podes verificarlo con `search_contracts` en IBKR o en TWS).
- **Rate limits de IBKR**: pedir barras mensuales para 500-600 tickers puede
  tardar bastante por el pacing (~1.5s entre pedidos por defecto). La cache
  en `cache/` permite cortar y resumir la corrida.
- **"Mejor performer"** se define como mayor retorno mensual `(close-open)/open`
  de la barra mensual de IBKR (precios ajustados por splits, no por dividendos).
