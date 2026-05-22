"""v3 derivatives-microstructure feature panel — iter-v3/093 cycle-4 RE-ARCHITECTURE.

Track-isolated: zero imports from crypto_trade.features (v1) or
crypto_trade.features_v2 (v2).

13-feature derivatives-microstructure panel organised in three active groups
(Section 11 amendment: per-symbol OI leg dropped 18 → 13; BTC OI retained):

  Funding group (7 features):
    f_rate               — funding rate level (the 8h settlement value)
    f_zscore_30          — 30-bar past-only z-score of f_rate
    f_sign_persist_9     — 9-bar sign-persistence of f_rate (mean of sign)
    f_mom_3              — 3-bar (1-day) funding momentum
    f_mom_9              — 9-bar (3-day) funding momentum
    f_accel_3            — 3-bar second-difference (carry-shock, BIS WP 1087)
    f_extreme_persist_9  — rolling |z|>1.5 persistence over 9 bars

  Basis group (4 features):
    b_level              — perp-spot basis level (shifted 1 bar — past-only)
    b_zscore_30          — 30-bar past-only z-score of b_level
    b_momentum_3         — 3-bar change of b_level (lagged basis momentum)
    fb_spread_z          — f_zscore_30 minus b_zscore_30 (corr ~0.22-0.28)

  Open-interest group (5 features — DROPPED per Section 11 amendment):
    oi_log_delta_1, oi_zscore_30, oi_mcap_ratio, oi_price_divergence,
    toptrader_ls_ratio — per-symbol OI excluded; Binance metrics archive
    does not cover the BCH/TRX training burn-in span. Compute code
    (_add_oi_features) is retained but names are NOT in DERIVATIVES_FEATURE_COLUMNS.

  Cross-asset group (2 features — BTC as market-state input):
    btc_f_zscore_30      — BTC funding z-score (broadcast to every symbol)
    btc_oi_zscore_30     — BTC OI log-delta z-score (broadcast; BTC OI
                           archive starts 2020-09, full IS coverage 1.000)

Look-ahead discipline:
    All features are past-only:
    - Funding rate[t] settles at bar t open (broadcast 5 min before the 8h
      boundary) — level and momentum use rate[t]; the z-score denominator
      uses .shift(1) so bar t's own rate never enters its own rolling window.
    - Basis(t) = (perp_close[t] - spot_close[t]) / spot_close[t] is knowable
      only at bar t CLOSE — all basis features are computed on basis.shift(1).
    - OI values are resampled from the PREVIOUS fully-closed 8h period; the
      oi_log_delta_1 at bar t uses oi[t] - oi[t-1] where both are known at
      bar t open; the z-score denominator uses .shift(1).
    - Cross-asset BTC features inherit the same past-only discipline as their
      per-symbol counterparts.

Data sources:
    data/funding_rates/<SYM>.csv  — from ``crypto-trade fetch-funding``
    data/spot/<SYM>/8h.csv        — from ``crypto-trade fetch-spot``
    data/open_interest/<SYM>/8h.csv — from ``crypto-trade fetch-oi`` (NEW)
    data/open_interest/BTCUSDT/8h.csv — BTC OI for cross-asset group
    data/funding_rates/BTCUSDT.csv    — BTC funding for cross-asset group

Outlier clipping:
    All z-scores clipped to [-10, 10] (the funding_v3.ZSCORE_CLIP convention).
    oi_log_delta_1 clipped to [-5, 5] (log-changes > 5 are data artefacts).
"""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

# ── Constants ────────────────────────────────────────────────────────────────

ZSCORE_CLIP: float = 10.0
OI_DELTA_CLIP: float = 5.0
ZSCORE_WINDOW: int = 30
PERSIST_WINDOW: int = 9
MOMENTUM_WINDOW_SHORT: int = 3  # 1-day (3 × 8h)
MOMENTUM_WINDOW_LONG: int = 9  # 3-day (9 × 8h)
EXTREME_Z_THRESHOLD: float = 1.5

_DEFAULT_DATA_DIR: Path = Path("data")

DERIVATIVES_FEATURE_COLUMNS: tuple[str, ...] = (
    # Funding group (7)
    "f_rate",
    "f_zscore_30",
    "f_sign_persist_9",
    "f_mom_3",
    "f_mom_9",
    "f_accel_3",
    "f_extreme_persist_9",
    # Basis group (4)
    "b_level",
    "b_zscore_30",
    "b_momentum_3",
    "fb_spread_z",
    # Cross-asset group (2)
    # OI per-symbol group (5) DROPPED per Section 11 amendment — NOT listed here.
    # The compute code (_add_oi_features) is retained for reference.
    "btc_f_zscore_30",
    "btc_oi_zscore_30",
)

assert len(DERIVATIVES_FEATURE_COLUMNS) == 13, (
    f"Expected 13 derivatives features, got {len(DERIVATIVES_FEATURE_COLUMNS)}"
)


# ── Internal helpers ─────────────────────────────────────────────────────────


def _align_merge(df: pd.DataFrame, ext_df: pd.DataFrame, ext_col: str) -> pd.Series:
    """Left-merge ext_df's ext_col into df on open_time, return aligned Series.

    Both DataFrames must have an ``open_time`` column (ms integer).
    Rows in df without a match receive NaN.
    """
    merged = df[["open_time"]].merge(
        ext_df[["open_time", ext_col]],
        on="open_time",
        how="left",
    )
    merged.index = df.index
    return merged[ext_col]


def _zscore_past_only(
    s: pd.Series,
    window: int = ZSCORE_WINDOW,
    clip: float = ZSCORE_CLIP,
) -> pd.Series:
    """Past-only rolling z-score: at bar t uses [t-window, t-1] via .shift(1)."""
    s_shifted = s.shift(1)
    rmean = s_shifted.rolling(window=window, min_periods=window).mean()
    rstd = s_shifted.rolling(window=window, min_periods=window).std(ddof=1)
    z = (s - rmean) / rstd.replace(0, np.nan)
    return z.clip(-clip, clip)


# ── Funding group ────────────────────────────────────────────────────────────


def _add_funding_features(
    df: pd.DataFrame,
    funding_df: pd.DataFrame,
    prefix: str = "f",
    clip: float = ZSCORE_CLIP,
) -> pd.DataFrame:
    """Compute the 7 funding features and add them to df.

    Parameters
    ----------
    df:
        Kline DataFrame with ``open_time`` column.
    funding_df:
        DataFrame with ``funding_time`` (ms) and ``funding_rate`` (float).
    prefix:
        Column-name prefix.  Use ``"f"`` for per-symbol, ``"btc_f"`` for BTC.
    clip:
        Z-score clip threshold.
    """
    # Round timestamps to nearest minute to absorb Binance settlement jitter
    fund = funding_df.copy()
    fund["open_time"] = (fund["funding_time"] // 60_000) * 60_000

    df_work = df.copy()
    df_work["_ot_aligned"] = (df_work["open_time"] // 60_000) * 60_000

    merged = df_work.merge(
        fund[["open_time", "funding_rate"]].rename(columns={"open_time": "_ot_aligned"}),
        on="_ot_aligned",
        how="left",
    ).drop(columns=["_ot_aligned"])
    merged.index = df_work.index

    r = merged["funding_rate"].astype(float)

    # f_rate — level (past-only by broadcast convention: settles at bar t open)
    df_work[f"{prefix}_rate"] = r.values

    # f_zscore_30 — 30-bar past-only z-score
    df_work[f"{prefix}_zscore_30"] = _zscore_past_only(r, ZSCORE_WINDOW, clip).values

    # f_sign_persist_9 — 9-bar sign persistence of rate (past-only: shift(1) then rolling)
    df_work[f"{prefix}_sign_persist_9"] = (
        np.sign(r).shift(1).rolling(PERSIST_WINDOW, min_periods=PERSIST_WINDOW).mean().values
    )

    # f_mom_3 — 3-bar funding momentum (rate[t] - rate[t-3])
    df_work[f"{prefix}_mom_3"] = (r - r.shift(MOMENTUM_WINDOW_SHORT)).values

    # f_mom_9 — 9-bar funding momentum (rate[t] - rate[t-9])
    df_work[f"{prefix}_mom_9"] = (r - r.shift(MOMENTUM_WINDOW_LONG)).values

    # f_accel_3 — second difference of 3-bar momentum (carry-shock, BIS WP 1087)
    mom3 = r - r.shift(MOMENTUM_WINDOW_SHORT)
    df_work[f"{prefix}_accel_3"] = (mom3 - mom3.shift(MOMENTUM_WINDOW_SHORT)).values

    # f_extreme_persist_9 — rolling fraction of bars where |z| > threshold
    # Uses f_zscore_30 already computed above; past-only via the z-score's own shift(1)
    z30 = _zscore_past_only(r, ZSCORE_WINDOW, clip)
    df_work[f"{prefix}_extreme_persist_9"] = (
        (z30.abs() > EXTREME_Z_THRESHOLD)
        .astype(float)
        .rolling(PERSIST_WINDOW, min_periods=PERSIST_WINDOW)
        .mean()
        .values
    )

    return df_work


# ── Basis group ──────────────────────────────────────────────────────────────


def _add_basis_features(
    df: pd.DataFrame,
    spot_df: pd.DataFrame,
    f_zscore_30_series: pd.Series,
    clip: float = ZSCORE_CLIP,
) -> pd.DataFrame:
    """Compute the 4 basis features and add them to df.

    Parameters
    ----------
    df:
        Perp kline DataFrame with ``open_time`` and ``close`` columns.
    spot_df:
        Spot kline DataFrame with ``open_time`` and ``close`` columns.
    f_zscore_30_series:
        Already-computed f_zscore_30 Series (aligned to df.index) — used for
        fb_spread_z.
    clip:
        Z-score clip threshold.
    """
    df_work = df.copy()
    spot = spot_df[["open_time", "close"]].rename(columns={"close": "_spot_close"})
    merged = df_work.merge(spot, on="open_time", how="left")
    merged.index = df_work.index

    perp_close = merged["close"].astype(float)
    spot_close = merged["_spot_close"].astype(float)
    basis_raw = (perp_close - spot_close) / spot_close.replace(0, np.nan)

    # Strict past-only: basis(t) = (perp[t] - spot[t]) / spot[t] is knowable only at
    # bar t CLOSE; shift one full bar before ALL computations.
    b = basis_raw.shift(1)

    # b_level — lagged basis level
    df_work["b_level"] = b.values

    # b_zscore_30 — 30-bar past-only z-score (b already shifted; use rolling on b directly)
    rmean = b.rolling(window=ZSCORE_WINDOW, min_periods=ZSCORE_WINDOW).mean()
    rstd = b.rolling(window=ZSCORE_WINDOW, min_periods=ZSCORE_WINDOW).std(ddof=1)
    b_z30 = ((b - rmean) / rstd.replace(0, np.nan)).clip(-clip, clip)
    df_work["b_zscore_30"] = b_z30.values

    # b_momentum_3 — 3-bar change of b (already lagged)
    df_work["b_momentum_3"] = (b - b.shift(MOMENTUM_WINDOW_SHORT)).values

    # fb_spread_z — funding z-score minus basis z-score (divergence signal)
    # corr ~0.22-0.28 (IS), so they carry independent information
    fb_spread = f_zscore_30_series - b_z30
    df_work["fb_spread_z"] = fb_spread.clip(-clip, clip).values

    return df_work


# ── OI group ─────────────────────────────────────────────────────────────────


def _add_oi_features(
    df: pd.DataFrame,
    oi_df: pd.DataFrame,
    clip: float = ZSCORE_CLIP,
    oi_delta_clip: float = OI_DELTA_CLIP,
) -> pd.DataFrame:
    """Compute the 5 OI features and add them to df.

    Parameters
    ----------
    df:
        Kline DataFrame with ``open_time``, ``close``, ``volume`` columns.
    oi_df:
        8h OI DataFrame (from ``data/open_interest/<SYM>/8h.csv``) with columns:
        ``open_time``, ``sum_open_interest``, ``sum_open_interest_value``,
        ``count_toptrader_long_short_ratio``, ``sum_toptrader_long_short_ratio``,
        ``count_long_short_ratio``, ``sum_taker_long_short_vol_ratio``.
    """
    df_work = df.copy()

    oi_aligned = oi_df[
        [
            "open_time",
            "sum_open_interest",
            "sum_open_interest_value",
            "count_toptrader_long_short_ratio",
        ]
    ].copy()
    oi_aligned["open_time"] = oi_aligned["open_time"].astype(int)

    merged = df_work.merge(oi_aligned, on="open_time", how="left")
    merged.index = df_work.index

    oi = merged["sum_open_interest"].astype(float)
    oi_val = merged["sum_open_interest_value"].astype(float)
    top_ls = merged["count_toptrader_long_short_ratio"].astype(float)

    # oi_log_delta_1 — 8h log-change of OI (leverage build/unwind rate).
    # log(oi[t] / oi[t-1]) is past-only (both values are snapshots at prior bar ends).
    # Clip to [-5, 5] to suppress data-quality artefacts (e.g. methodology resets).
    log_oi = np.log(oi.replace(0, np.nan))
    oi_delta = (log_oi - log_oi.shift(1)).clip(-oi_delta_clip, oi_delta_clip)
    df_work["oi_log_delta_1"] = oi_delta.values

    # oi_zscore_30 — 30-bar past-only z-score of oi_log_delta_1
    df_work["oi_zscore_30"] = _zscore_past_only(oi_delta, ZSCORE_WINDOW, clip).values

    # oi_mcap_ratio — OI value normalised by trailing 30-bar mean quote-volume.
    # Approximates the leverage-stretch: high OI relative to traded volume signals fragility.
    # All inputs past-only (oi_val at bar t is the previous bar's snapshot; volume is bar t's
    # own volume which settled at close_time — shift 1 bar for strict past-only).
    vol = df_work["volume"].astype(float).shift(1)
    vol_ma30 = vol.rolling(window=ZSCORE_WINDOW, min_periods=ZSCORE_WINDOW).mean()
    oi_ratio = oi_val / vol_ma30.replace(0, np.nan)
    df_work["oi_mcap_ratio"] = oi_ratio.clip(0, 1000).values  # cap extreme values

    # oi_price_divergence — sign(oi_delta) × (1 − |price-return|-rank).
    # High positive: OI building while price is quiet = stealth-leverage build.
    # High negative: OI unwinding into a large price move = confirmed deleveraging.
    # Price return at bar t: log(close[t]/close[t-1]) — past-only via shift(1).
    log_close = np.log(df_work["close"].astype(float))
    price_ret = (log_close - log_close.shift(1)).shift(1)  # past-only
    # Normalise |price-return| to [0, 1] rank within a 30-bar trailing window
    price_ret_abs_rank = (
        price_ret.abs().rolling(ZSCORE_WINDOW, min_periods=ZSCORE_WINDOW).rank(pct=True).fillna(0.5)
    )
    oi_sign = np.sign(oi_delta)
    df_work["oi_price_divergence"] = (oi_sign * (1.0 - price_ret_abs_rank)).values

    # toptrader_ls_ratio — count_toptrader_long_short_ratio.
    # Positive: more top-trader longs than shorts (crowded-long proxy).
    # No additional transformation; already a ratio-scale feature.
    # Clip extreme values (data artefacts in early archive history).
    df_work["toptrader_ls_ratio"] = top_ls.clip(0, 10).values

    return df_work


# ── Cross-asset group ─────────────────────────────────────────────────────────


def _add_btc_cross_asset_features(
    df: pd.DataFrame,
    btc_funding_df: pd.DataFrame,
    btc_oi_df: pd.DataFrame,
    clip: float = ZSCORE_CLIP,
    oi_delta_clip: float = OI_DELTA_CLIP,
) -> pd.DataFrame:
    """Add BTC funding z-score and BTC OI z-score as cross-asset features.

    These are broadcast identically to BCH/LDO/TRX kline frames — the
    market-wide deleveraging-stress regime input (same design as the existing
    cross_btc_v3.py precedent; BTC is a market-state INPUT, not a traded symbol).
    """
    df_work = df.copy()

    # btc_f_zscore_30 — BTC funding z-score (broadcast)
    btc_fund = btc_funding_df.copy()
    btc_fund["open_time"] = (btc_fund["funding_time"] // 60_000) * 60_000
    df_work["_ot_aligned"] = (df_work["open_time"] // 60_000) * 60_000
    merged_fund = df_work.merge(
        btc_fund[["open_time", "funding_rate"]].rename(columns={"open_time": "_ot_aligned"}),
        on="_ot_aligned",
        how="left",
    ).drop(columns=["_ot_aligned"])
    merged_fund.index = df_work.index
    btc_rate = merged_fund["funding_rate"].astype(float)
    df_work["btc_f_zscore_30"] = _zscore_past_only(btc_rate, ZSCORE_WINDOW, clip).values
    df_work = df_work.drop(columns=["_ot_aligned"], errors="ignore")

    # btc_oi_zscore_30 — BTC OI log-delta z-score (broadcast)
    btc_oi = btc_oi_df[["open_time", "sum_open_interest"]].copy()
    btc_oi["open_time"] = btc_oi["open_time"].astype(int)
    merged_oi = df_work.merge(btc_oi, on="open_time", how="left")
    merged_oi.index = df_work.index
    btc_oi_s = merged_oi["sum_open_interest"].astype(float)
    log_btc_oi = np.log(btc_oi_s.replace(0, np.nan))
    btc_oi_delta = (log_btc_oi - log_btc_oi.shift(1)).clip(-oi_delta_clip, oi_delta_clip)
    df_work["btc_oi_zscore_30"] = _zscore_past_only(btc_oi_delta, ZSCORE_WINDOW, clip).values

    return df_work


# ── Public API ────────────────────────────────────────────────────────────────


def compute_derivatives_state_features(
    df: pd.DataFrame,
    funding_df: pd.DataFrame,
    spot_df: pd.DataFrame,
    oi_df: pd.DataFrame,
    btc_funding_df: pd.DataFrame,
    btc_oi_df: pd.DataFrame,
    clip: float = ZSCORE_CLIP,
    oi_delta_clip: float = OI_DELTA_CLIP,
) -> pd.DataFrame:
    """Compute all 18 derivatives-microstructure features for one symbol.

    Parameters
    ----------
    df:
        Perp kline DataFrame with columns: ``open_time`` (ms int),
        ``open``, ``high``, ``low``, ``close``, ``volume``.
    funding_df:
        Per-symbol funding cache (``funding_time`` ms, ``funding_rate`` float).
    spot_df:
        Per-symbol spot 8h kline cache (``open_time`` ms, ``close`` float).
    oi_df:
        Per-symbol 8h OI cache from ``fetch-oi``
        (``open_time`` ms, ``sum_open_interest``, ``sum_open_interest_value``,
        ``count_toptrader_long_short_ratio``).
    btc_funding_df:
        BTCUSDT funding cache (cross-asset broadcast).
    btc_oi_df:
        BTCUSDT 8h OI cache (cross-asset broadcast).
    clip:
        Z-score clip threshold (default 10.0).
    oi_delta_clip:
        Log-OI-delta clip threshold (default 5.0).

    Returns
    -------
    pd.DataFrame
        Input df with the 13 ``DERIVATIVES_FEATURE_COLUMNS`` appended
        (Section 11 amendment: per-symbol OI leg dropped; 18 → 13 features).
        Rows without matching external data receive NaN.
        Note: the per-symbol OI features (oi_log_delta_1, oi_zscore_30,
        oi_mcap_ratio, oi_price_divergence, toptrader_ls_ratio) are
        COMPUTED inside _add_oi_features (code retained for reference) but
        their names are NOT in DERIVATIVES_FEATURE_COLUMNS and are not
        used by the runner.

    Notes
    -----
    Look-ahead invariant enforced by the column-level conventions:
    - Funding: rate[t] past-only (broadcast 5 min before settlement);
      z-score denominator uses .shift(1).
    - Basis: all features on basis.shift(1) (knowable at bar t open only
      from bar t-1 close).
    - BTC OI: log-delta uses oi[t] - oi[t-1] (both known at bar t open
      from the cached 8h snapshots); z-score denominator uses .shift(1).
    """
    df = df.copy()

    # -- Funding group ---------------------------------------------------------
    df = _add_funding_features(df, funding_df, prefix="f", clip=clip)
    f_zscore_30_series = pd.Series(df["f_zscore_30"].values, index=df.index)

    # -- Basis group -----------------------------------------------------------
    df = _add_basis_features(df, spot_df, f_zscore_30_series, clip=clip)

    # -- OI group (per-symbol) — DROPPED from DERIVATIVES_FEATURE_COLUMNS -----
    # The compute call is retained so _add_oi_features remains tested (test #2
    # still calls compute_derivatives_state_features with an oi_df argument).
    # The 5 OI column names are appended to df here but the runner only reads
    # DERIVATIVES_FEATURE_COLUMNS (13 names) — the 5 dead columns are ignored.
    df = _add_oi_features(df, oi_df, clip=clip, oi_delta_clip=oi_delta_clip)

    # -- Cross-asset group (BTC funding + BTC OI) ------------------------------
    df = _add_btc_cross_asset_features(
        df, btc_funding_df, btc_oi_df, clip=clip, oi_delta_clip=oi_delta_clip
    )

    return df


def add_derivatives_state_v3_features(
    df: pd.DataFrame,
    data_dir: Path | str = _DEFAULT_DATA_DIR,
    clip: float = ZSCORE_CLIP,
    oi_delta_clip: float = OI_DELTA_CLIP,
) -> pd.DataFrame:
    """Load all data caches for df's symbol and compute the 18 derivatives features.

    This is the convenience entry-point for use in the runner.  It reads all
    required cache files from the standard locations under ``data_dir``.

    Parameters
    ----------
    df:
        Perp kline DataFrame with ``symbol`` and ``open_time`` columns.
    data_dir:
        Root data directory (default ``data/``).

    Raises
    ------
    KeyError:
        If ``df`` does not contain the ``symbol`` column.
    FileNotFoundError:
        If any required cache file is absent.  Run the corresponding CLI
        fetch command first.
    """
    data_dir = Path(data_dir)

    symbol = df["symbol"].iloc[0] if "symbol" in df.columns else None
    if symbol is None:
        raise KeyError(
            "df must contain a 'symbol' column. Set df['symbol'] = '<SYMBOL>' before calling."
        )

    # Funding (per-symbol)
    funding_path = data_dir / "funding_rates" / f"{symbol}.csv"
    if not funding_path.exists():
        raise FileNotFoundError(
            f"Funding cache not found: {funding_path}. "
            f"Run: uv run crypto-trade fetch-funding --symbols {symbol}"
        )
    funding_df = pd.read_csv(funding_path)

    # Spot klines (per-symbol)
    spot_path = data_dir / "spot" / symbol / "8h.csv"
    if not spot_path.exists():
        raise FileNotFoundError(
            f"Spot kline cache not found: {spot_path}. "
            f"Run: uv run crypto-trade fetch-spot --symbols {symbol}"
        )
    spot_df = pd.read_csv(spot_path)

    # Open interest (per-symbol)
    oi_path = data_dir / "open_interest" / symbol / "8h.csv"
    if not oi_path.exists():
        raise FileNotFoundError(
            f"OI cache not found: {oi_path}. Run: uv run crypto-trade fetch-oi --symbols {symbol}"
        )
    oi_df = pd.read_csv(oi_path)
    oi_df["open_time"] = oi_df["open_time"].astype(int)

    # BTC funding (cross-asset)
    btc_funding_path = data_dir / "funding_rates" / "BTCUSDT.csv"
    if not btc_funding_path.exists():
        raise FileNotFoundError(
            f"BTC funding cache not found: {btc_funding_path}. "
            "Run: uv run crypto-trade fetch-funding --symbols BTCUSDT"
        )
    btc_funding_df = pd.read_csv(btc_funding_path)

    # BTC OI (cross-asset)
    btc_oi_path = data_dir / "open_interest" / "BTCUSDT" / "8h.csv"
    if not btc_oi_path.exists():
        raise FileNotFoundError(
            f"BTC OI cache not found: {btc_oi_path}. "
            "Run: uv run crypto-trade fetch-oi --symbols BTCUSDT"
        )
    btc_oi_df = pd.read_csv(btc_oi_path)
    btc_oi_df["open_time"] = btc_oi_df["open_time"].astype(int)

    return compute_derivatives_state_features(
        df,
        funding_df=funding_df,
        spot_df=spot_df,
        oi_df=oi_df,
        btc_funding_df=btc_funding_df,
        btc_oi_df=btc_oi_df,
        clip=clip,
        oi_delta_clip=oi_delta_clip,
    )
