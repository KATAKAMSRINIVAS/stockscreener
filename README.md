# 📊 Stock Screener with Near Real-Time UI

A modular Python + Streamlit project that screens either **Indian NSE-listed stocks from the Nifty 500** or **US NYSE-listed stocks** using **yfinance**.

The app filters stocks with the rules below and displays **ranked results** in a near real-time dashboard.

---

## Features

- Market choice:
  - **NSE (Nifty 500)**
  - **NYSE (all NYSE-listed symbols available through the market file loader)**
- Filters:
  - **P/E ratio < 20**
  - **Volume spike > 2x the 20-day average**
  - **RSI > 50**
- Ranked output with:
  - **Ticker**
  - **Current Price**
  - **P/E**
  - **Volume Ratio**
  - **RSI**
- Near real-time UI refresh with **Streamlit**
- CSV export of current results
- Clean, modular project structure

---

## Project Structure

```text
stock-screener/
├── .streamlit/
│   └── config.toml
├── screener/
│   ├── __init__.py
│   ├── data_fetcher.py
│   ├── filters.py
│   ├── indicators.py
│   └── universe.py
├── app.py
├── config.py
├── requirements.txt
├── README.md
└── Claude.md
```

---

## Setup

### 1) Create and activate a virtual environment

> Recommended: use Python 3.12.x (or 3.11.x). Python 3.14 on Windows can fail here because NumPy 1.26 tries to build from source and needs a C compiler.

**Windows (PowerShell)**

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\Activate.ps1
```

**Linux/macOS**

```bash
python3.12 -m venv .venv
source .venv/bin/activate
```

### 2) Install dependencies

```bash
pip install -r requirements.txt
```

### 3) Run the UI

```bash
streamlit run app.py
```

By default, Streamlit runs on **port 8501**. The included `.streamlit/config.toml` explicitly sets the app to port **8501**.

---

## How the app works

1. Loads the stock universe based on your selected market
2. Downloads recent OHLCV history using `yfinance`
3. Computes:
   - 14-period RSI
   - 20-day average volume
   - volume spike ratio
4. Fetches P/E ratio per ticker
5. Filters results using the configured constraints
6. Ranks the filtered list using a weighted score:
   - **50%** volume spike strength
   - **30%** RSI strength
   - **20%** lower P/E advantage
7. Displays results in the UI and supports CSV export

---

## Notes

- The **NSE universe** is loaded from a public Nifty 500 constituent source with a fallback list if the remote file is unavailable.
- The **NYSE universe** is loaded from a public market-symbol file with a fallback list if the remote file is unavailable.
- Large universes can take time, especially because **P/E** often requires an individual fundamentals lookup per ticker.
- Use the **universe cap** in the sidebar during testing if you want faster results.
- Near real-time behavior is designed around periodic reruns rather than a hard streaming feed.

---

## Known limitations

- `yfinance` depends on Yahoo Finance responses; some tickers may have missing or delayed fundamentals.
- Not every symbol will return a valid trailing P/E or enough historical data.
- This project is intended as a practical screener template and may need tuning for production-scale usage.

---

## Quick usage tips

- Start with **NSE** and a **universe cap** of 100 for a quick validation run.
- If you get zero matches, lower the **volume ratio** threshold or reduce the **RSI** floor.
- Download the CSV after each scan to preserve snapshots.

---

## Disclaimer

`yfinance` is an open-source library that retrieves Yahoo Finance market data and is generally intended for research and educational use. Review the upstream project and Yahoo Finance terms before using it operationally.
