"""v1 funding-rate features — iter-v1/023 (feature-family EXPLORATION #8/10 cycle-3).

Track-isolated: ZERO imports from crypto_trade.features_v2 or crypto_trade.features_v3.
The funding math is COPIED (not imported) from features_v3/funding_v3.py to maintain
v1↔v3 isolation per the v1 track discipline.

Funding rate is the canonical economic primitive of Binance Futures perpetual markets.
Every 8h at 00/08/16 UTC, longs pay shorts (positive funding) or shorts pay longs
(negative funding). Persistent positive funding signals leveraged-long crowding with
mean-reversion / liquidation-cascade pressure (BIS WP 1087, 2025: 10% carry shock →
22% liquidation jump).

Two z-score windows:
  - ``funding_rate_zscore_30``: 30-bar (10-day) window — captures short-term positioning
    regime changes; primary falsifier in F-AXIS-MECHANISM #1.
  - ``funding_rate_zscore_90``: 90-bar (30-day) window — smoother medium-term signal;
    higher IC with momentum features per brief Section 2.3 (max |IC|=0.438 LTC vs MACD).

Data source:
    ``data/funding_rates/<SYMBOL>.csv`` — cached CSV from /fapi/v1/fundingRate.
    Schema: ``funding_time`` (ms epoch int), ``funding_rate`` (float).
    The fetcher (``uv run crypto-trade fetch-funding``) writes this file.

Look-ahead discipline:
    The funding rate AT bar t is the rate that SETTLED at candle open_time T
    (knowable from the previous 8h period close). Past-only is implemented by
    shifting the rolling-window stats by 1 bar:

        bar t z-score  =  (rate[t] - mean(rate[t-window]...rate[t-1]))
                          / std(rate[t-window]...rate[t-1])

    ``rate[t]`` is the rate that settled AT t (broadcast 5 min before settlement,
    so fully knowable at bar t open). The rolling denominator uses ONLY t-window…t-1
    via ``.shift(1)`` — no bar t data enters the denominator.

    Unit-test ``tests/features_v1/test_funding_v1.py`` enforces this invariant.

Outlier clipping:
    When funding is clamped at Binance's floor for >window consecutive bars,
    the rolling std → 0 and z-score → ±∞. We clip to [-10, 10] to prevent
    LightGBM training instability.

Burn-in:
    - funding_rate_zscore_30: first 30 rows NaN (rolling window warm-up)
    - funding_rate_zscore_90: first 90 rows NaN

Track isolation enforcement:
    Phase 6.0 pre-flight Critic verifies:
        grep -r "from crypto_trade.features_v2" src/crypto_trade/features_v1/
        grep -r "from crypto_trade.features_v3" src/crypto_trade/features_v1/
    Both must return empty. This module has ZERO such imports.
"""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

# Rolling window constants (8h cadence: 3 bars/day)
FUNDING_ZSCORE_WINDOW_30: int = 30  # 10-day short-term window
FUNDING_ZSCORE_WINDOW_90: int = 90  # 30-day medium-term window

# Clip z-scored output to prevent LightGBM instability from funding-floor outliers
ZSCORE_CLIP: float = 10.0

# Default data directory for funding-rate cache
_DEFAULT_DATA_DIR: Path = Path("data")


def compute_funding_rate_zscore(
    df: pd.DataFrame,
    funding_df: pd.DataFrame,
    window: int = FUNDING_ZSCORE_WINDOW_30,
    clip: float = ZSCORE_CLIP,
    output_col: str = "funding_rate_zscore_30",
) -> pd.DataFrame:
    """Merge funding rates into kline frame and compute rolling z-score.

    Parameters
    ----------
    df:
        Kline DataFrame with at least ``open_time`` (ms int) column.
    funding_df:
        DataFrame with columns ``funding_time`` (ms int) and
        ``funding_rate`` (float), as written by the ``fetch-funding`` CLI.
    window:
        Rolling window in bars (default 30 = ~10 days at 8h cadence).
    clip:
        Absolute clip threshold for the z-scored output (default 10.0).
    output_col:
        Column name for the z-score output (default ``funding_rate_zscore_30``).
        Pass ``funding_rate_zscore_90`` when window=90.

    Returns
    -------
    pd.DataFrame
        Input df with ``output_col`` column appended.
        Rows that cannot match a funding record (start of listing) get NaN.
        First ``window`` rows are NaN by construction (rolling warm-up).

    Notes
    -----
    Look-ahead discipline: the z-score at bar t uses ONLY rates t-window…t-1
    for the rolling denominator (via ``.shift(1)``). The numerator uses
    ``rate[t]`` which settled at candle open_time T (past-only by funding
    broadcast convention — the settlement is broadcast 5 min before the 8h
    boundary).

    Alignment: funding settles at exactly 00/08/16 UTC, identical to v1's 8h
    kline open_times. We round both timestamps to the nearest minute
    (//60000*60000) to absorb Binance's ~10-15ms settlement jitter.
    """
    df = df.copy()

    # ------------------------------------------------------------------
    # Step 1: align timestamps (round to nearest minute to handle jitter)
    # ------------------------------------------------------------------
    funding = funding_df.copy()
    funding["open_time_aligned"] = (funding["funding_time"] // 60_000) * 60_000
    df["open_time_aligned"] = (df["open_time"] // 60_000) * 60_000

    # ------------------------------------------------------------------
    # Step 2: left-merge kline → funding on rounded open_time
    # ------------------------------------------------------------------
    merged = df.merge(
        funding[["open_time_aligned", "funding_rate"]],
        on="open_time_aligned",
        how="left",
    ).drop(columns=["open_time_aligned"])

    # Restore original index alignment
    merged.index = df.index

    # ------------------------------------------------------------------
    # Step 3: compute past-only rolling z-score
    # ------------------------------------------------------------------
    s = merged["funding_rate"].astype(float)

    # Rolling stats lagged by 1 bar: at bar t, mean/std use t-window…t-1 only.
    # The .shift(1) ensures bar t's own rate does NOT enter its own denominator.
    s_shifted = s.shift(1)
    rmean = s_shifted.rolling(window=window, min_periods=window).mean()
    rstd = s_shifted.rolling(window=window, min_periods=window).std(ddof=1)

    # Numerator: rate[t] (settled at bar t open — past-only by funding broadcast convention)
    zscore = (s - rmean) / rstd.replace(0, np.nan)

    # Clip to prevent LightGBM instability from funding-floor outliers
    zscore = zscore.clip(lower=-clip, upper=clip)

    df[output_col] = zscore.values

    return df


def add_funding_v1_features(
    df: pd.DataFrame,
    data_dir: Path | str = _DEFAULT_DATA_DIR,
    windows: tuple[int, int] = (FUNDING_ZSCORE_WINDOW_30, FUNDING_ZSCORE_WINDOW_90),
    clip: float = ZSCORE_CLIP,
) -> pd.DataFrame:
    """Load cached funding rates for ``df``'s symbol and add z-score features.

    Appends ``funding_rate_zscore_30`` and ``funding_rate_zscore_90`` columns.
    Both use PAST-ONLY rolling z-score computation (shift(1) + rolling stats).

    Parameters
    ----------
    df:
        Kline DataFrame with ``symbol`` and ``open_time`` columns.
    data_dir:
        Root data directory (default ``data/``). Reads from
        ``data_dir/funding_rates/<SYMBOL>.csv``.
    windows:
        Tuple of (short_window, long_window) in bars. Default (30, 90).
        The output column names are always ``funding_rate_zscore_30`` and
        ``funding_rate_zscore_90`` regardless of custom window values.
    clip:
        Z-score clip threshold (default 10.0).

    Returns
    -------
    pd.DataFrame
        Input df with ``funding_rate_zscore_30`` and ``funding_rate_zscore_90``
        columns appended.

    Raises
    ------
    FileNotFoundError
        If the funding-rate cache for the symbol does not exist.
        Run ``uv run crypto-trade fetch-funding --symbols <SYMBOL>`` first.
    KeyError
        If ``df`` does not contain the ``symbol`` column.

    Notes
    -----
    Non-null rate guard: after the rolling warm-up period, non-null rate should
    exceed 95% for any symbol with full funding history. The runner verifies
    this before training (brief Section 3.3 assertion).
    """
    data_dir = Path(data_dir)

    symbol = df["symbol"].iloc[0] if "symbol" in df.columns else None
    if symbol is None:
        raise KeyError(
            "df must contain a 'symbol' column for funding_v1 feature group. "
            "Set df['symbol'] = '<SYMBOL>' before calling add_funding_v1_features."
        )

    cache_path = data_dir / "funding_rates" / f"{symbol}.csv"
    if not cache_path.exists():
        raise FileNotFoundError(
            f"Funding-rate cache not found: {cache_path}. "
            f"Run: uv run crypto-trade fetch-funding --symbols {symbol}"
        )

    funding_df = pd.read_csv(cache_path)
    if len(funding_df) == 0:
        # Empty cache — add NaN columns and return
        df = df.copy()
        df["funding_rate_zscore_30"] = np.nan
        df["funding_rate_zscore_90"] = np.nan
        return df

    # Apply short window (z30)
    window_30, window_90 = windows
    df = compute_funding_rate_zscore(
        df, funding_df, window=window_30, clip=clip, output_col="funding_rate_zscore_30"
    )

    # Apply long window (z90) — reuses the same funding_df
    df = compute_funding_rate_zscore(
        df, funding_df, window=window_90, clip=clip, output_col="funding_rate_zscore_90"
    )

    return df


__all__ = [
    "FUNDING_ZSCORE_WINDOW_30",
    "FUNDING_ZSCORE_WINDOW_90",
    "ZSCORE_CLIP",
    "compute_funding_rate_zscore",
    "add_funding_v1_features",
]
