# Claude.md

## Project Name
Stock Screener with Near Real-Time UI

## Goal
Create a Python application with a Streamlit UI that screens:
- Indian NSE-listed stocks from the **Nifty 500**, or
- US **NYSE-listed stocks**

based on user selection.

## Functional Rules
The screener must only return stocks that satisfy all of the following:
- **P/E ratio < 20**
- **Current volume > 2x 20-day average volume**
- **RSI > 50**

## Required Output Fields
The UI must show ranked results with:
- Ticker
- Current Price
- P/E Ratio
- Volume Ratio
- RSI

## UI Expectations
- Build with **Streamlit**
- Support auto-refresh in near real-time intervals
- Allow user-controlled filters and universe cap
- Provide CSV export

## Architecture
- `app.py`: Streamlit UI and orchestration
- `screener/universe.py`: Load market universes
- `screener/indicators.py`: RSI and volume calculations
- `screener/filters.py`: Apply filters and ranking logic
- `screener/data_fetcher.py`: yfinance download + fundamentals retrieval
- `config.py`: constants and defaults

## Ranking Strategy
Use a weighted score:
- 50% volume spike strength
- 30% RSI strength
- 20% lower P/E advantage

## Runtime
- Run locally with:
  - `streamlit run app.py`
- Port:
  - `8502`

## Engineering Notes
- Prefer modular, readable code
- Use safe fallbacks if universe sources are unavailable
- Avoid hard-coding market data into the UI layer
- Keep calculations testable and separated from presentation
- Use cache where possible to reduce repeat network calls

## Caveats
- Data completeness depends on Yahoo Finance responses
- P/E may be missing for some symbols
- Large universes can be slower because of fundamentals lookups
