from __future__ import annotations

import pandas as pd


def apply_filters(df: pd.DataFrame, max_pe: float = 20.0, min_volume_ratio: float = 2.0, min_rsi: float = 50.0) -> pd.DataFrame:
    if df.empty:
        return df
    working = df.copy()
    return working[
        working['pe_ratio'].notna()
        & (working['pe_ratio'] < max_pe)
        & (working['volume_ratio'] > min_volume_ratio)
        & (working['rsi'] > min_rsi)
    ]


def rank_results(df: pd.DataFrame) -> pd.DataFrame:
    if df.empty:
        return df

    working = df.copy()
    working['value_score'] = (20 - working['pe_ratio']).clip(lower=0) / 20
    working['momentum_score'] = (working['rsi'] / 100).clip(lower=0)
    working['volume_spike_score'] = (working['volume_ratio'] / working['volume_ratio'].max()).clip(lower=0)
    working['rank_score'] = (
        working['volume_spike_score'] * 0.50
        + working['momentum_score'] * 0.30
        + working['value_score'] * 0.20
    ).round(4)

    ordered = working.sort_values(
        by=['rank_score', 'volume_ratio', 'rsi', 'pe_ratio'],
        ascending=[False, False, False, True],
    ).reset_index(drop=True)
    ordered.index = ordered.index + 1
    ordered.index.name = 'rank'
    return ordered
