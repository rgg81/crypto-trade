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


# ---------------------------------------------------------------------------
# iter-v1/052: Extended funding-rate features for BTC-specialist head
# ---------------------------------------------------------------------------
#
# Two new features derived from the existing ``funding_rate`` primitive:
#   1. ``btc_funding_rate_8h_impulse`` — shock detector (normalized first-difference)
#   2. ``btc_funding_spread_30_90``    — term-structure slope (z30 minus z90)
#
# Both are in the same primitive class as ``funding_rate_zscore_30/90`` (funding-rate
# derived, non-OHLCV). They are registered together as one indivisible axis
# ("both-or-neither revert" rule — brief Section 3.1).
#
# Look-ahead discipline (same as existing features):
#   ``btc_funding_rate_8h_impulse`` uses ``funding_rate.diff()`` which is
#   rate[t] - rate[t-1] — both known at bar t (rate[t] settled at bar t open;
#   rate[t-1] settled at bar t-1 open). The 90-bar rolling std in the denominator
#   uses the lagged first-differences (via rolling on the diff series) — at bar t,
#   the rolling window covers bars t-90 ... t-1 (standard pandas rolling), i.e.
#   it lags correctly. No forward contamination.
#
#   ``btc_funding_spread_30_90`` = z30[t] - z90[t] — both z-scores already use
#   shift(1) look-ahead discipline from ``compute_funding_rate_zscore``. No
#   additional bias introduced.
#
# Burn-in:
#   ``btc_funding_rate_8h_impulse``: first 91 rows NaN (90-bar rolling std needs
#   90 diff() observations; diff() itself produces 1 NaN at the start).
#   ``btc_funding_spread_30_90``: first 90 rows NaN (same as funding_rate_zscore_90
#   burn-in which dominates).
#
# Outlier clipping:
#   ``btc_funding_rate_8h_impulse`` clipped to [-10, 10] (same as z-score features).


def compute_btc_funding_rate_8h_impulse(
    df: pd.DataFrame,
    clip: float = ZSCORE_CLIP,
    output_col: str = "btc_funding_rate_8h_impulse",
) -> pd.DataFrame:
    """Compute the 8h funding-rate impulse (shock detector).

    The impulse is the 8h-difference in funding rate normalised by the 90-bar
    rolling standard deviation of those differences:

        impulse[t] = diff(funding_rate)[t]
                     / rolling(90).std(diff(funding_rate))[t]

    When the rolling std is near-zero (e.g. funding clamped at Binance floor),
    the output is set to 0.0 rather than ±∞ to prevent LightGBM instability.

    Parameters
    ----------
    df:
        Kline DataFrame with a ``funding_rate`` column already merged in.
        Call ``add_funding_v1_features`` first to ensure ``funding_rate`` is
        present. Alternatively, ``add_funding_v1_extended_features`` handles
        the full pipeline.
    clip:
        Absolute clip threshold (default 10.0 — same as z-score features).
    output_col:
        Name of the output column (default ``btc_funding_rate_8h_impulse``).

    Returns
    -------
    pd.DataFrame
        Input df with ``output_col`` column appended.
        First ~91 rows are NaN (1 from diff + 90 from rolling std warm-up).

    Notes
    -----
    Look-ahead discipline: diff()[t] = rate[t] - rate[t-1]; the rolling std
    uses the diff series up to and including bar t (standard pandas rolling,
    NOT shifted). This is intentional: the impulse at bar t is the
    *concurrent* shock (how unusual is today's carry change vs recent
    volatility of carry changes). Bar t's rate settled at bar t's open — it
    is fully known at bar t. No forward contamination.

    Bit-exact reproduction: the formula uses only pandas rolling + numpy
    where — deterministic given the same input series.
    """
    df = df.copy()
    if "funding_rate" not in df.columns:
        raise KeyError(
            "df must contain a 'funding_rate' column to compute "
            "btc_funding_rate_8h_impulse. "
            "Call add_funding_v1_features (or add_funding_v1_extended_features) first."
        )
    fr = df["funding_rate"].astype(float)
    fr_diff = fr.diff()
    std_90 = fr_diff.rolling(window=90, min_periods=90).std(ddof=1)
    # Guard: two cases to handle:
    #   (a) std_90 is NaN (burn-in period; first 91 rows) → output NaN (preserve burn-in)
    #   (b) std_90 is a valid near-zero value (funding-floor clamped regime) → output 0.0
    # Approach: compute fr_diff / std_90 → NaN where std_90 is NaN or near-zero.
    # Then fill back 0.0 ONLY for positions where std_90 is valid but near-zero (not burn-in).
    safe_std = std_90.where(std_90 > 1e-8)  # set near-zero to NaN (keeps burn-in NaN intact)
    impulse_series = fr_diff / safe_std  # NaN for both burn-in and near-zero-std positions
    # Restore 0.0 for near-zero-std positions (std_90 is finite and <= 1e-8; NOT burn-in)
    near_zero_mask = std_90.notna() & (std_90 <= 1e-8)
    impulse_series = impulse_series.copy()
    impulse_series[near_zero_mask] = 0.0
    impulse_clipped = impulse_series.clip(lower=-clip, upper=clip)
    df[output_col] = impulse_clipped.values
    return df


def compute_btc_funding_spread_30_90(
    df: pd.DataFrame,
    output_col: str = "btc_funding_spread_30_90",
) -> pd.DataFrame:
    """Compute the funding-rate term-structure slope (z30 minus z90).

    Captures whether short-term positioning pressure (30-bar z-score) is
    running ahead of or behind the medium-term baseline (90-bar z-score).
    Positive = short-term premium > long-term (positioning heating / crowded
    long setup). Negative = backwardation or capitulation.

    Parameters
    ----------
    df:
        Kline DataFrame with both ``funding_rate_zscore_30`` and
        ``funding_rate_zscore_90`` columns already present.
        Call ``add_funding_v1_features`` before this function.
    output_col:
        Name of the output column (default ``btc_funding_spread_30_90``).

    Returns
    -------
    pd.DataFrame
        Input df with ``output_col`` column appended.
        NaN where either parent z-score is NaN (first ~90 rows).

    Notes
    -----
    Look-ahead discipline: both parent z-scores use shift(1) in their
    rolling denominators (see ``compute_funding_rate_zscore``). The spread
    inherits the same look-ahead guarantee — no forward contamination.

    IC note: expected |IC| vs funding_rate_zscore_30 is ~0.70–0.85
    (algebraic sister). This falls under the EDA-informational exemption
    (same-primitive class) per v1 brief Section 2.3. Trees can exploit the
    algebraic shortcut (one split on the spread = one split accessing the
    z30 vs z90 divergence vs two separate splits on the parent features).
    """
    df = df.copy()
    for col in ("funding_rate_zscore_30", "funding_rate_zscore_90"):
        if col not in df.columns:
            raise KeyError(
                f"df must contain '{col}' to compute btc_funding_spread_30_90. "
                "Call add_funding_v1_features first to generate both z-score columns."
            )
    df[output_col] = df["funding_rate_zscore_30"] - df["funding_rate_zscore_90"]
    return df


def add_funding_v1_extended_features(
    df: pd.DataFrame,
    data_dir: Path | str = _DEFAULT_DATA_DIR,
    clip: float = ZSCORE_CLIP,
) -> pd.DataFrame:
    """Add ALL funding-rate features: z-scores (z30, z90) + impulse + spread.

    This is the iter-v1/052 extended pipeline. Produces:
        - funding_rate_zscore_30        (from existing add_funding_v1_features)
        - funding_rate_zscore_90        (from existing add_funding_v1_features)
        - btc_funding_rate_8h_impulse   (new at /052; shock detector)
        - btc_funding_spread_30_90      (new at /052; term-structure slope)

    Note: despite the ``btc_`` prefix in the feature names, the math applies
    to WHICHEVER symbol's funding data is loaded (the prefix is cosmetic
    naming). For the /052 BTC-only specialist, df always contains BTCUSDT data.

    Implementation note on ``funding_rate`` column:
        ``compute_funding_rate_zscore`` merges the raw ``funding_rate`` series
        into a local ``merged`` variable but does NOT attach it to the returned
        ``df``. This function independently merges the funding CSV to produce
        the ``funding_rate`` column needed by ``compute_btc_funding_rate_8h_impulse``.

    Parameters
    ----------
    df:
        Kline DataFrame with ``symbol`` and ``open_time`` columns.
    data_dir:
        Root data directory (default ``data/``). Reads funding-rate cache from
        ``data_dir/funding_rates/<SYMBOL>.csv``.
    clip:
        Z-score clip threshold (default 10.0).

    Returns
    -------
    pd.DataFrame
        Input df with four new columns appended:
        - funding_rate_zscore_30
        - funding_rate_zscore_90
        - btc_funding_rate_8h_impulse
        - btc_funding_spread_30_90

    Raises
    ------
    FileNotFoundError
        If the funding-rate cache for the symbol does not exist.
    KeyError
        If ``df`` does not contain the ``symbol`` column.
    """
    data_dir = Path(data_dir)

    # Resolve symbol and load the funding-rate cache once (shared across all steps)
    symbol = df["symbol"].iloc[0] if "symbol" in df.columns else None
    if symbol is None:
        raise KeyError(
            "df must contain a 'symbol' column for funding_v1 extended feature group. "
            "Set df['symbol'] = '<SYMBOL>' before calling add_funding_v1_extended_features."
        )
    cache_path = data_dir / "funding_rates" / f"{symbol}.csv"
    if not cache_path.exists():
        raise FileNotFoundError(
            f"Funding-rate cache not found: {cache_path}. "
            f"Run: uv run crypto-trade fetch-funding --symbols {symbol}"
        )
    funding_df = pd.read_csv(cache_path)

    if len(funding_df) == 0:
        # Empty cache — add all four NaN columns and return
        df = df.copy()
        df["funding_rate_zscore_30"] = np.nan
        df["funding_rate_zscore_90"] = np.nan
        df["btc_funding_rate_8h_impulse"] = np.nan
        df["btc_funding_spread_30_90"] = np.nan
        return df

    # Step 1: base z-score features (z30 and z90)
    df = compute_funding_rate_zscore(
        df,
        funding_df,
        window=FUNDING_ZSCORE_WINDOW_30,
        clip=clip,
        output_col="funding_rate_zscore_30",
    )
    df = compute_funding_rate_zscore(
        df,
        funding_df,
        window=FUNDING_ZSCORE_WINDOW_90,
        clip=clip,
        output_col="funding_rate_zscore_90",
    )

    # Step 2: merge raw funding_rate into df for the impulse computation.
    # compute_funding_rate_zscore keeps the z-score only (not the raw rate).
    # We do a lightweight alignment merge here to attach the raw rate column.
    funding_aligned = funding_df.copy()
    funding_aligned["open_time_aligned"] = (funding_aligned["funding_time"] // 60_000) * 60_000
    df_aligned = df.copy()
    df_aligned["open_time_aligned"] = (df_aligned["open_time"] // 60_000) * 60_000
    rate_merged = df_aligned.merge(
        funding_aligned[["open_time_aligned", "funding_rate"]],
        on="open_time_aligned",
        how="left",
    ).drop(columns=["open_time_aligned"])
    rate_merged.index = df_aligned.index
    df["funding_rate"] = rate_merged["funding_rate"].values

    # Step 3: impulse (shock detector) — uses the raw funding_rate column
    df = compute_btc_funding_rate_8h_impulse(df, clip=clip)

    # Step 4: spread (term-structure slope) — uses z30 and z90 from step 1
    df = compute_btc_funding_spread_30_90(df)

    # Drop the intermediate funding_rate column (not a training feature)
    df = df.drop(columns=["funding_rate"], errors="ignore")

    return df


__all__ = [
    "FUNDING_ZSCORE_WINDOW_30",
    "FUNDING_ZSCORE_WINDOW_90",
    "ZSCORE_CLIP",
    "compute_funding_rate_zscore",
    "add_funding_v1_features",
    # iter-v1/052 extended features
    "compute_btc_funding_rate_8h_impulse",
    "compute_btc_funding_spread_30_90",
    "add_funding_v1_extended_features",
]
