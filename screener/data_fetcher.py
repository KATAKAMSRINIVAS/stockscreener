from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Iterable

import pandas as pd
import yfinance as yf

from config import BATCH_SIZE, LOOKBACK_DAYS, MAX_WORKERS, RSI_PERIOD, VOLUME_AVG_WINDOW
from .filters import apply_filters, rank_results
from .indicators import latest_metrics
from .universe import get_market_universe


def _chunks(items: list[str], size: int) -> Iterable[list[str]]:
    for i in range(0, len(items), size):
        yield items[i:i + size]


def _download_ohlcv(symbols: list[str], period_days: int) -> dict[str, pd.DataFrame]:
    out: dict[str, pd.DataFrame] = {}
    if not symbols:
        return out

    for batch in _chunks(symbols, BATCH_SIZE):
        raw = yf.download(
            tickers=batch,
            period=f'{period_days}d',
            interval='1d',
            auto_adjust=False,
            progress=False,
            group_by='ticker',
            threads=True,
            actions=False,
        )
        if raw is None or raw.empty:
            continue

        if isinstance(raw.columns, pd.MultiIndex):
            for symbol in batch:
                if symbol in raw.columns.get_level_values(0):
                    frame = raw[symbol].dropna(how='all')
                    if not frame.empty:
                        out[symbol] = frame
        else:
            symbol = batch[0]
            frame = raw.dropna(how='all')
            if not frame.empty:
                out[symbol] = frame
    return out


def _fetch_pe(symbol: str) -> float | None:
    try:
        info = yf.Ticker(symbol).info or {}
        pe = info.get('trailingPE')
        if pe is None:
            pe = info.get('forwardPE')
        return float(pe) if pe is not None else None
    except Exception:
        return None


def _fetch_pe_parallel(symbols: list[str]) -> dict[str, float | None]:
    out: dict[str, float | None] = {}
    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as pool:
        futures = {pool.submit(_fetch_pe, symbol): symbol for symbol in symbols}
        for future in as_completed(futures):
            symbol = futures[future]
            try:
                out[symbol] = future.result()
            except Exception:
                out[symbol] = None
    return out


def scan_market(market: str, max_pe: float = 20.0, min_volume_ratio: float = 2.0, min_rsi: float = 50.0, limit_universe: int | None = None) -> tuple[pd.DataFrame, dict]:
    """Fetch the market universe, compute metrics, filter, rank, and return results + metadata."""
    symbols = get_market_universe(market)
    if limit_universe:
        symbols = symbols[:limit_universe]

    ohlcv_map = _download_ohlcv(symbols, period_days=LOOKBACK_DAYS)

    metrics_rows = []
    for symbol, hist in ohlcv_map.items():
        metrics = latest_metrics(hist, rsi_period=RSI_PERIOD, volume_window=VOLUME_AVG_WINDOW)
        if metrics:
            metrics_rows.append({'ticker': symbol, **metrics})

    metrics_df = pd.DataFrame(metrics_rows)
    if metrics_df.empty:
        return metrics_df, {
            'market': market,
            'universe_size': len(symbols),
            'history_loaded': 0,
            'filtered_count': 0,
        }

    pe_map = _fetch_pe_parallel(metrics_df['ticker'].tolist())
    metrics_df['pe_ratio'] = metrics_df['ticker'].map(pe_map)
    filtered = apply_filters(metrics_df, max_pe=max_pe, min_volume_ratio=min_volume_ratio, min_rsi=min_rsi)
    ranked = rank_results(filtered)

    metadata = {
        'market': market,
        'universe_size': len(symbols),
        'history_loaded': int(metrics_df['ticker'].nunique()),
        'filtered_count': int(len(ranked)),
    }
    return ranked, metadata
