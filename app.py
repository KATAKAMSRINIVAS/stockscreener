from __future__ import annotations

from datetime import datetime

import pandas as pd
import streamlit as st
from streamlit_autorefresh import st_autorefresh

from config import APP_TITLE, DEFAULT_MARKET, DEFAULT_REFRESH_SECONDS, DEFAULT_TOP_N
from screener import scan_market
from screener.universe import get_market_universe

st.set_page_config(page_title=APP_TITLE, layout='wide', page_icon='📈')


def _sidebar() -> dict:
    st.sidebar.title('Controls')
    market = st.sidebar.selectbox(
        'Choose market',
        options=['NSE (Nifty 500)', 'NYSE (All NYSE-listed)'],
        index=0 if DEFAULT_MARKET.startswith('NSE') else 1,
    )
    refresh_seconds = st.sidebar.slider('Auto-refresh interval (seconds)', 15, 300, DEFAULT_REFRESH_SECONDS, 15)
    top_n = st.sidebar.number_input('Top results to display', min_value=5, max_value=100, value=DEFAULT_TOP_N, step=5)
    max_pe = st.sidebar.number_input('Max P/E ratio', min_value=1.0, max_value=200.0, value=20.0, step=1.0)
    min_volume_ratio = st.sidebar.number_input('Min volume spike ratio', min_value=1.0, max_value=20.0, value=2.0, step=0.1)
    min_rsi = st.sidebar.number_input('Min RSI', min_value=1.0, max_value=100.0, value=50.0, step=1.0)
    scan_limit = st.sidebar.number_input(
        'Optional universe cap (0 = scan full universe)',
        min_value=0,
        max_value=5000,
        value=0,
        step=50,
        help='Use a lower cap during testing if you want faster scans.',
    )
    manual_refresh = st.sidebar.button('Run scan now', type='primary')
    return {
        'market': market,
        'refresh_seconds': refresh_seconds,
        'top_n': int(top_n),
        'max_pe': float(max_pe),
        'min_volume_ratio': float(min_volume_ratio),
        'min_rsi': float(min_rsi),
        'scan_limit': None if int(scan_limit) == 0 else int(scan_limit),
        'manual_refresh': manual_refresh,
    }


@st.cache_data(ttl=60, show_spinner=False)
def _run_scan_cached(market: str, max_pe: float, min_volume_ratio: float, min_rsi: float, scan_limit: int | None):
    return scan_market(
        market=market,
        max_pe=max_pe,
        min_volume_ratio=min_volume_ratio,
        min_rsi=min_rsi,
        limit_universe=scan_limit,
    )


def _style_result_frame(df: pd.DataFrame) -> pd.DataFrame:
    display = df.copy()
    display = display.rename(columns={
        'ticker': 'Ticker',
        'current_price': 'Current Price',
        'pe_ratio': 'P/E',
        'volume_ratio': 'Volume Ratio',
        'rsi': 'RSI',
        'avg_20d_volume': '20D Avg Volume',
        'current_volume': 'Current Volume',
        'rank_score': 'Rank Score',
    })
    ordered_cols = [
        'Ticker', 'Current Price', 'P/E', 'Volume Ratio', 'RSI',
        'Current Volume', '20D Avg Volume', 'Rank Score'
    ]
    keep = [c for c in ordered_cols if c in display.columns]
    return display[keep]


def main() -> None:
    controls = _sidebar()
    st_autorefresh(interval=controls['refresh_seconds'] * 1000, key='screen-refresh')

    st.title(APP_TITLE)
    st.caption('Filter stocks by value, volume spike, and momentum using yfinance-backed data.')

    universe_size = len(get_market_universe(controls['market']))
    st.info(
        f"Selected universe: **{controls['market']}** | "
        f"Universe size available: **{universe_size:,}** | "
        f"Refresh interval: **{controls['refresh_seconds']} sec** | "
        f"Recommended local port: **8501**"
    )

    if controls['manual_refresh']:
        _run_scan_cached.clear()

    with st.spinner('Scanning market... this can take a while for large universes.'):
        ranked, metadata = _run_scan_cached(
            controls['market'],
            controls['max_pe'],
            controls['min_volume_ratio'],
            controls['min_rsi'],
            controls['scan_limit'],
        )

    left, mid, right, far = st.columns(4)
    left.metric('Universe scanned', f"{metadata.get('universe_size', 0):,}")
    mid.metric('History loaded', f"{metadata.get('history_loaded', 0):,}")
    right.metric('Matches', f"{metadata.get('filtered_count', 0):,}")
    far.metric('Last refresh', datetime.now().strftime('%Y-%m-%d %H:%M:%S'))

    if ranked.empty:
        st.warning('No stocks matched the current filters. Try relaxing the P/E, volume ratio, or RSI thresholds.')
        st.stop()

    top_df = ranked.head(controls['top_n'])
    display_df = _style_result_frame(top_df)

    st.subheader('Ranked Results')
    st.dataframe(display_df, use_container_width=True)

    csv_bytes = display_df.to_csv(index=True).encode('utf-8')
    st.download_button(
        label='Download results as CSV',
        data=csv_bytes,
        file_name='screened_stocks.csv',
        mime='text/csv',
    )

    st.subheader('Signal Snapshot')
    chart_df = top_df[['ticker', 'volume_ratio', 'rsi']].set_index('ticker')
    st.bar_chart(chart_df)

    with st.expander('Ranking logic used'):
        st.markdown("""
- **50% weight**: higher volume spike ratio
- **30% weight**: stronger RSI
- **20% weight**: lower P/E ratio (value tilt)

Score formula combines normalized values and sorts descending.
""")

    with st.expander('Operational notes'):
        st.markdown("""
- Large universes can be slow because fundamentals such as P/E often require per-symbol lookups.
- Use the **universe cap** during testing to limit the number of symbols scanned.
- Near real-time refresh is implemented with a browser-side timer to trigger reruns.
- Data quality depends on the Yahoo Finance fields returned for each ticker.
""")


if __name__ == '__main__':
    main()
