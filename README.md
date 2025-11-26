# Trade Dock (Flask)

Flask toolkit for intraday trading signals, charts, and automation. It pulls market data from Yahoo Finance and TradingView, stores analysis in PostgreSQL, renders candle charts, and can trigger Longbridge day-trade loops or email alerts.

## Features

- Web UI to query tickers by date/interval and visualize price/indicator charts.
- TradingView technical-summary fetcher with per-ticker metrics.
- Backtests for bundled strategies (`/allTradingStrategy`).
- Email alerts for “strong buy/sell” windows (Outlook SMTP stub in `app/emails.py`).
- Experimental Longbridge day-trade loop driven by TradingView + Yahoo Finance signals.

## Requirements

- Python 3.10+
- PostgreSQL (tables `longbridge_trading` and `notification_email`; see `PostG.sql`)
- Network access for Yahoo Finance, TradingView TA, and optionally Longbridge API

## Setup

1. Create a virtual environment and install dependencies:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

2. Configure environment (PostgreSQL + optional Longbridge):

```bash
export DB_USER=liqing           # or your Postgres user
export DB_PASSWORD=liqing       # or your Postgres password
export DB_HOST=localhost
export DB_NAME=postgres
export DB_PORT=5432
# Longbridge credentials: set the variables expected by longbridge.openapi.Config.from_env
# (app key/secret/access token per the Longbridge SDK docs)
# Optional for headless plotting:
export MPLBACKEND=Agg
```

3. Prepare the database:

```bash
psql -d postgres -f "PostG.sql"
# creates longbridge_trading and notification_email tables
```

## Run the app

```bash
python main.py
```

The Flask dev server listens on `http://0.0.0.0:8088/`.

### Core routes

- `/` – landing page wiring the other flows.
- `/queryPrices` – GET shows form; POST renders intraday charts and buy/sell timing for a ticker/date.
- `/queryTradingview` – GET shows form; POST returns TradingView technical summary for selected tickers/interval.
- `/allTradingStrategy` – POST runs bundled backtests via `backtest_all_trading_strategies`.
- `/startEmailNotification` – starts a loop polling TradingView signals and emailing alerts (requires SMTP configured).
- `/longbridge-day-trade` – launches a loop that paper-trades/executes via Longbridge (requires Longbridge creds and DB).

### Email + Longbridge configuration

- Update sender credentials in `app/emails.py` (currently placeholders for Outlook SMTP on port 587).
- Longbridge uses `Config.from_env()`. Provide the app key/secret/access token expected by the Longbridge SDK before hitting `/longbridge-day-trade`.

## Project structure

```
main.py                     # Flask entrypoint
app/
  routes.py                 # HTTP routes
  views.py                  # TradingView fetch + plotting
  models.py                 # indicator calculations, data helpers
  database.py               # Postgres connection via env vars
  longbridgeRealTrading.py  # Longbridge trading loop
  all_trading_strategies.py # backtest orchestration
  emails.py                 # SMTP helpers (edit credentials)
  templates/                # Jinja templates
  static/                   # JS/CSS assets
data_csv/                   # local CSV cache (ignored)
data_svg/                   # generated SVG charts
PostG.sql         # Postgres schema for trading tables
tests/test_strategy.py      # DB-backed strategy replay
```

## Tests

```bash
pytest
```

The test expects a populated `longbridge_trading` table and the DB env vars set; it will fail without that data.

## Notes

- Long-running loops live in `/startEmailNotification` and `/longbridge-day-trade`; run them in a dedicated process/shell.
- Keep secrets out of git; prefer environment variables over hardcoding.
- Headless servers may need `MPLBACKEND=Agg` to render charts.
