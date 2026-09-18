from __future__ import annotations

import pandas as pd


def compute_rsi(close: pd.Series, period: int = 14) -> pd.Series:
    """Compute Wilder-style RSI using exponential smoothing."""
    close = close.astype(float)
    delta = close.diff()
    gain = delta.clip(lower=0)
    loss = -delta.clip(upper=0)

    avg_gain = gain.ewm(alpha=1 / period, min_periods=period, adjust=False).mean()
    avg_loss = loss.ewm(alpha=1 / period, min_periods=period, adjust=False).mean()

    rs = avg_gain / avg_loss.replace(0, pd.NA)
    rsi = 100 - (100 / (1 + rs))
    return rsi.fillna(0)


def latest_metrics(df: pd.DataFrame, rsi_period: int = 14, volume_window: int = 20) -> dict | None:
    """Return latest price, volume ratio, and RSI from OHLCV history."""
    if df is None or df.empty or len(df) < max(volume_window + 1, rsi_period + 1):
        return None

    working = df.copy()
    if 'Close' not in working.columns or 'Volume' not in working.columns:
        return None

    working['Close'] = working['Close'].astype(float)
    working['Volume'] = working['Volume'].astype(float)
    working['RSI'] = compute_rsi(working['Close'], period=rsi_period)
    working['AvgVolume20'] = working['Volume'].rolling(window=volume_window).mean()

    latest = working.iloc[-1]
    avg_vol = latest['AvgVolume20']
    if pd.isna(avg_vol) or not avg_vol:
        return None

    volume_ratio = float(latest['Volume']) / float(avg_vol)
    return {
        'current_price': round(float(latest['Close']), 2),
        'volume_ratio': round(volume_ratio, 2),
        'rsi': round(float(latest['RSI']), 2),
        'avg_20d_volume': int(avg_vol),
        'current_volume': int(latest['Volume']),
    }
