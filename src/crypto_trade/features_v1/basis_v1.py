"""v1 basis features — iter-v1/034 (feature-family EXPLORATION #1/10 cycle-5).

Track-isolated: ZERO imports from crypto_trade.features_v2 or crypto_trade.features_v3.
The basis math is new (not copied from any existing module); perp-vs-spot is an
orthogonal data source not previously touched in v1 cycles 1-4.

Basis (perp − spot) is the canonical futures-basis primitive of Binance Futures
perpetual markets. Persistent positive basis = leveraged-long crowding → mean-reversion
/ liquidation-cascade pressure; persistent negative basis = leveraged-short stress →
squeeze pressure. The 30-bar z-score normalizes for secular shifts in the perp-spot
premium so the model sees regime-relative positioning stretch, not absolute level.

Single feature exported:
  - ``basis_zscore_30``: 30-bar z-score of basis_bps (window=30 bars = ~10 days at 8h).

Feature definition (canonical):

    basis_bps[t]       = (perp_close[t] - spot_close[t]) / spot_close[t] * 10_000
    basis_zscore_30[t] = (basis_bps[t] - mean(basis_bps[t-30..t-1]))
                         / std(basis_bps[t-30..t-1])

Data source:
    ``data/spot/<SYMBOL>/8h.csv`` — spot kline CSV fetched by the ``bulk`` CLI.
    Perp data is read directly from the kline DataFrame passed to ``add_basis_v1_features``.

Look-ahead discipline:
    ``basis_bps[t]`` uses perp_close[t] and spot_close[t] — BOTH are bar-close prices
    that are fully knowable at bar t close (no future data). The rolling denominator
    uses ONLY bars t-window…t-1 via ``.shift(1)`` — bar t's own basis_bps does NOT
    enter bar t's rolling stats.

    Unit-test ``tests/features_v1/test_basis_v1.py::test_compute_basis_zscore_past_only``
    enforces this invariant.

Outlier clipping:
    ``basis_zscore_30`` is clipped to [-10, +10] (same ``ZSCORE_CLIP`` convention as
    ``funding_v1.py`` and ``open_interest_v1.py``).

Burn-in:
    First 30 rows are NaN per symbol (rolling window warm-up).
    Rows where spot close is missing or zero get NaN basis_bps → NaN z-score.

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

# Rolling window constant (8h cadence: 3 bars/day; 30 bars = 10 days)
BASIS_ZSCORE_WINDOW: int = 30

# Clip z-scored output (matches ZSCORE_CLIP in funding_v1.py)
ZSCORE_CLIP: float = 10.0

# Basis conversion factor: fraction → basis points (bps)
_BPS_FACTOR: float = 10_000.0

# Default data directory for spot kline cache
_DEFAULT_DATA_DIR: Path = Path("data")


def compute_basis_zscore(
    perp_df: pd.DataFrame,
    spot_df: pd.DataFrame,
    window: int = BASIS_ZSCORE_WINDOW,
    clip: float = ZSCORE_CLIP,
    output_col: str = "basis_zscore_30",
) -> pd.DataFrame:
    """Merge perp + spot close prices and compute rolling basis z-score.

    Parameters
    ----------
    perp_df:
        Perpetual kline DataFrame with at least ``open_time`` (ms int) and
        ``close`` (numeric) columns.
    spot_df:
        Spot kline DataFrame with at least ``open_time`` (ms int) and
        ``close`` (numeric) columns.
    window:
        Rolling window in bars for z-score normalization (default 30 = ~10 days at 8h).
    clip:
        Absolute clip threshold for the z-scored output (default 10.0).
    output_col:
        Column name for the z-score output (default ``basis_zscore_30``).

    Returns
    -------
    pd.DataFrame
        Copy of ``perp_df`` with ``output_col`` appended.
        Rows where spot data is missing get NaN basis_bps → NaN z-score.
        First ``window`` rows are NaN by construction (rolling warm-up).

    Notes
    -----
    Look-ahead discipline:
        ``basis_bps[t]`` is computed from bar-close prices (fully knowable at bar close).
        The rolling denominator uses ONLY bars t-window…t-1 (via ``.shift(1)`` on the
        basis_bps series before computing rolling mean/std). Bar t's own basis_bps does
        NOT enter bar t's rolling stats.

    Inner join:
        Merges perp and spot on ``open_time`` via inner join — rows present in perp but
        absent in spot receive NaN basis_bps (left join is used; spot-absent bars produce
        NaN which propagates to NaN z-score). If spot history is shorter than perp, the
        early perp bars will have NaN z-score (no data contamination).
    """
    perp = perp_df.copy()

    # ------------------------------------------------------------------
    # Step 1: align spot closes to perp open_times (left join on open_time)
    # ------------------------------------------------------------------
    spot_close = spot_df[["open_time", "close"]].copy()
    spot_close = spot_close.rename(columns={"close": "_spot_close"})
    spot_close["_merge_key"] = spot_close["open_time"].astype("int64")
    perp["_merge_key"] = perp["open_time"].astype("int64")

    merged = perp.merge(
        spot_close[["_merge_key", "_spot_close"]],
        on="_merge_key",
        how="left",
    ).drop(columns=["_merge_key"])

    # Restore original index
    merged.index = perp_df.index

    # ------------------------------------------------------------------
    # Step 2: compute basis_bps (perp_close - spot_close) / spot_close * 10000
    # ------------------------------------------------------------------
    perp_close = merged["close"].astype(float)
    spot_close_aligned = merged["_spot_close"].astype(float)

    # Guard: spot_close = 0 would produce inf — replace with NaN
    spot_close_safe = spot_close_aligned.replace(0.0, np.nan)
    basis_bps = (perp_close - spot_close_safe) / spot_close_safe * _BPS_FACTOR

    # ------------------------------------------------------------------
    # Step 3: compute past-only rolling z-score
    # Rolling stats are computed on .shift(1) so bar t's own basis_bps does
    # NOT enter bar t's rolling denominator.
    # ------------------------------------------------------------------
    s_shifted = basis_bps.shift(1)
    rmean = s_shifted.rolling(window=window, min_periods=window).mean()
    rstd = s_shifted.rolling(window=window, min_periods=window).std(ddof=1)

    # Numerator: basis_bps[t] (bar-close prices — past-only by construction)
    zscore = (basis_bps - rmean) / rstd.replace(0.0, np.nan)

    # Clip to prevent LightGBM instability
    zscore = zscore.clip(lower=-clip, upper=clip)

    # Write result to a copy of the original perp_df (without _spot_close column)
    result = perp_df.copy()
    result[output_col] = zscore.values

    return result


def add_basis_v1_features(
    df: pd.DataFrame,
    data_dir: Path | str = _DEFAULT_DATA_DIR,
    window: int = BASIS_ZSCORE_WINDOW,
    clip: float = ZSCORE_CLIP,
) -> pd.DataFrame:
    """Load spot klines for ``df``'s symbol and add basis_zscore_30 column.

    Appends ``basis_zscore_30`` to the DataFrame.
    Uses PAST-ONLY rolling z-score computation (shift(1) + rolling stats on basis_bps).

    Parameters
    ----------
    df:
        Perpetual kline DataFrame with ``symbol``, ``open_time`` (ms int), and
        ``close`` (numeric) columns.
    data_dir:
        Root data directory (default ``data/``). Reads spot klines from
        ``data_dir/spot/<SYMBOL>/8h.csv``.
    window:
        Rolling window in bars (default 30 = ~10 days at 8h cadence).
    clip:
        Z-score clip threshold (default 10.0).

    Returns
    -------
    pd.DataFrame
        Input df with ``basis_zscore_30`` column appended.
        Rows where spot data is missing get NaN z-score (graceful degradation).
        First ``window`` rows are NaN by construction (rolling warm-up).

    Raises
    ------
    FileNotFoundError
        If the spot kline CSV for the symbol does not exist under
        ``data_dir/spot/<SYMBOL>/8h.csv``.
        Run ``uv run crypto-trade bulk --symbols <SYMBOL> --intervals 8h`` or
        ``uv run crypto-trade fetch --symbols <SYMBOL> --intervals 8h`` to populate.
    KeyError
        If ``df`` does not contain the ``symbol`` column.

    Notes
    -----
    Spot CSV schema: standard kline CSV format (same as perp ``data/<SYMBOL>/8h.csv``).
    Columns: open_time, open, high, low, close, volume, close_time, ...
    The merge uses ``open_time`` (ms epoch int) — 8h bars are exactly aligned between
    perp and spot (same Binance exchange timestamps).

    Non-null fraction after burn-in should exceed 95% for symbols with full spot history
    (BTC/ETH/LINK/LTC/DOT all available from 2020-01-01 per brief Section 1.0a).
    """
    data_dir = Path(data_dir)

    if "symbol" not in df.columns:
        raise KeyError(
            "df must contain a 'symbol' column for basis_v1 feature group. "
            "Set df['symbol'] = '<SYMBOL>' before calling add_basis_v1_features."
        )

    symbol = df["symbol"].iloc[0]
    spot_path = data_dir / "spot" / symbol / "8h.csv"

    if not spot_path.exists():
        raise FileNotFoundError(
            f"Spot kline CSV not found: {spot_path}. "
            f"Run: uv run crypto-trade bulk --symbols {symbol} --intervals 8h"
        )

    # Read spot klines — only open_time + close needed for basis computation
    spot_df = pd.read_csv(spot_path, usecols=["open_time", "close"])
    spot_df["open_time"] = spot_df["open_time"].astype("int64")
    spot_df["close"] = pd.to_numeric(spot_df["close"], errors="coerce")

    if len(spot_df) == 0:
        # Empty spot CSV — add NaN column and return
        result = df.copy()
        result["basis_zscore_30"] = np.nan
        return result

    return compute_basis_zscore(df, spot_df, window=window, clip=clip)


__all__ = [
    "BASIS_ZSCORE_WINDOW",
    "ZSCORE_CLIP",
    "compute_basis_zscore",
    "add_basis_v1_features",
]
