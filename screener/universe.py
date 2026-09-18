from __future__ import annotations

import io
from functools import lru_cache

import pandas as pd
import requests

REQUEST_TIMEOUT = 20
USER_AGENT = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0 Safari/537.36'

NSE_NIFTY_500_CSV = 'https://archives.nseindia.com/content/indices/ind_nifty500list.csv'
NASDAQ_OTHERLISTED = 'https://www.nasdaqtrader.com/dynamic/SymDir/otherlisted.txt'

FALLBACK_NSE = [
    'RELIANCE.NS', 'HDFCBANK.NS', 'ICICIBANK.NS', 'INFY.NS', 'TCS.NS',
    'LT.NS', 'SBIN.NS', 'ITC.NS', 'BHARTIARTL.NS', 'AXISBANK.NS'
]

FALLBACK_NYSE = [
    'KO', 'PG', 'IBM', 'GE', 'BAC', 'WMT', 'JNJ', 'XOM', 'MCD', 'VZ'
]


def _get(url: str) -> str:
    resp = requests.get(url, headers={'User-Agent': USER_AGENT}, timeout=REQUEST_TIMEOUT)
    resp.raise_for_status()
    return resp.text


@lru_cache(maxsize=4)
def get_nifty_500_symbols() -> list[str]:
    """Load current Nifty 500 constituent symbols and append .NS suffix for Yahoo Finance."""
    try:
        csv_data = _get(NSE_NIFTY_500_CSV)
        df = pd.read_csv(io.StringIO(csv_data))
        possible_cols = [c for c in df.columns if 'symbol' in c.lower()]
        if not possible_cols:
            raise ValueError('No Symbol column found in NSE file')
        col = possible_cols[0]
        symbols = (
            df[col]
            .dropna()
            .astype(str)
            .str.strip()
            .replace('', pd.NA)
            .dropna()
            .map(lambda s: s if s.endswith('.NS') else f'{s}.NS')
            .tolist()
        )
        return sorted(list(dict.fromkeys(symbols)))
    except Exception:
        return FALLBACK_NSE


@lru_cache(maxsize=4)
def get_nyse_symbols() -> list[str]:
    """Load ticker symbols for NYSE-listed equities from Nasdaq Trader's otherlisted file."""
    try:
        txt = _get(NASDAQ_OTHERLISTED)
        df = pd.read_csv(io.StringIO(txt), sep='|')
        df.columns = [c.strip() for c in df.columns]
        filtered = df[df['Exchange'].astype(str).str.strip().eq('N')].copy()
        symbols = (
            filtered['ACT Symbol']
            .dropna()
            .astype(str)
            .str.strip()
            .loc[lambda s: ~s.str.contains(r'\$|\.', regex=True)]
            .tolist()
        )
        return sorted(list(dict.fromkeys(symbols)))
    except Exception:
        return FALLBACK_NYSE


def get_market_universe(market: str) -> list[str]:
    if market.startswith('NSE'):
        return get_nifty_500_symbols()
    return get_nyse_symbols()
