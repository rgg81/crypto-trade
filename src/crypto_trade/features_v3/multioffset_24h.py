"""Multi-offset 24h derived-series pipeline for iter-v3/117.

Ported directly from analysis/iteration_v3-117/_shared.py (EDA commit c64a5fc,
T4-validated: 900/900 derivation audit PASS). This module is the production
implementation of the 8h→24h aggregation and 14-feature computation for
the 24h-decision-grid multi-offset architecture.

Design:
- Reads data/<SYM>/8h.csv for each symbol (and BTCUSDT for cross-asset features).
- For each offset_h ∈ {0, 8, 16}: aggregates 8h candles into 24h bars. Each
  24h bar's bar_close_time equals the close_time of the last 8h sub-bar in
  its window — the CAUSAL timestamp.
- Per-offset feature computation is ISOLATED: offset-0 rolling windows use
  only offset-0 bars, never cross-pollinating with offset-8 or offset-16.
- Concatenates the 3 offsets per symbol into a pooled panel with an
  offset_id ∈ {0, 8, 16} column (the 15th feature in the 24h feature stack).
- Writes data/features_v3_24h/<SYM>_24h_multioffset_features.parquet.

CAUSAL CORRECTNESS (look-ahead-free assertion — verified at T4 900/900):
    For any 24h decision row in offset O at bar_close_time t_close, the OHLCV
    aggregation uses ONLY 8h candles with close_time <= t_close. No future bar
    peek; no cross-offset peek.

Track isolation: this module imports ONLY from stdlib and third-party packages.
It does NOT import from crypto_trade.features (v1) or crypto_trade.features_v2
(v2). The v3-24h path is fully self-contained.
"""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

MS_PER_HOUR: int = 3_600_000
MS_PER_DAY: int = 86_400_000
MS_PER_8H: int = 8 * MS_PER_HOUR

OFFSETS_H: tuple[int, ...] = (0, 8, 16)

# /059-canonical V3_FEATURE_COLUMNS — 14-feature anchor stack, RECOMPUTED at 24h.
V3_FEATURE_COLUMNS_24H: list[str] = [
    "max_dd_window_50",
    "ema_spread_atr_20",
    "ret_kurt_50",
    "ret_skew_200",
    "range_realized_vol_50",
    "hurst_diff_100_50",
    "ret_kurt_200",
    "hurst_100",
    "btc_ret_14d",
    "ret_skew_50",
    "vwap_dev_20",
    "ret_autocorr_lag1_50",
    "sym_vs_btc_ret_7d",
    "regime_momentum_signed_5d",
]

# The 15th feature: offset_id ∈ {0, 8, 16} (the categorical axis discriminant).
OFFSET_ID_COLUMN: str = "offset_id"


# ---------------------------------------------------------------------------
# 8h CSV loader
# ---------------------------------------------------------------------------


def load_8h_csv(data_dir: Path | str, symbol: str) -> pd.DataFrame:
    """Load one symbol's 8h CSV. No IS fence (runner owns the fence).

    Returns columns: open_time, open, high, low, close, volume, close_time.
    Sorts by open_time ascending.
    """
    data_dir = Path(data_dir)
    csv_path = data_dir / symbol / "8h.csv"
    df = pd.read_csv(csv_path)
    df = df.sort_values("open_time").reset_index(drop=True)
    cols_keep = ["open_time", "open", "high", "low", "close", "volume", "close_time"]
    for col in cols_keep:
        if col not in df.columns:
            raise KeyError(f"Expected column '{col}' not found in {csv_path}")
    return df[cols_keep].astype(
        {
            "open_time": "int64",
            "close_time": "int64",
            "open": "float64",
            "high": "float64",
            "low": "float64",
            "close": "float64",
            "volume": "float64",
        }
    )


# ---------------------------------------------------------------------------
# Multi-offset 24h aggregation
# ---------------------------------------------------------------------------


def aggregate_to_24h(df8h: pd.DataFrame, offset_h: int) -> pd.DataFrame:
    """Aggregate one symbol's 8h frame to a 24h series at offset `offset_h`.

    Each 24h bar groups the (up to) three consecutive 8h candles whose
    open_time falls in [D + offset_h, D + offset_h + 24h) where D is a UTC
    day boundary (epoch ms). Returns a DataFrame with columns:
        bar_open_time   -- start of the 24h window (epoch ms)
        bar_close_time  -- close_time of the LAST 8h sub-bar in the window
                           (CAUSAL timestamp — features and label are only
                           valid once bar_close_time is in the past)
        open / high / low / close / volume
        offset_h        -- offset in hours (0, 8, or 16)
        n_8h            -- number of 8h sub-bars in this 24h bar (1, 2, or 3)

    LOOK-AHEAD-FREE: bar_close_time = close_time of the most-recent 8h sub-bar.
    By construction every sub-bar has close_time <= bar_close_time. No future bar
    enters any 24h bar's aggregation. The 3 offset series are computed independently.

    Bars with fewer than 3 sub-bars (boundary/gap days) are retained; downstream
    feature computation drops NaN-rows via min_periods enforcement.
    """
    if offset_h not in OFFSETS_H:
        raise ValueError(f"offset_h must be one of {OFFSETS_H}, got {offset_h}")
    df = df8h.sort_values("open_time").reset_index(drop=True).copy()
    offset_ms = offset_h * MS_PER_HOUR
    # Bucket each 8h candle into the 24h window whose start = D + offset_ms.
    shifted = df["open_time"].to_numpy(dtype="int64") - offset_ms
    bucket = (shifted // MS_PER_DAY) * MS_PER_DAY + offset_ms
    df["bar_open_time"] = bucket
    grp = df.groupby("bar_open_time", sort=True)
    bars = pd.DataFrame(
        {
            "bar_open_time": grp["bar_open_time"].first().to_numpy(),
            "open": grp["open"].first().to_numpy(),
            "high": grp["high"].max().to_numpy(),
            "low": grp["low"].min().to_numpy(),
            "close": grp["close"].last().to_numpy(),
            "volume": grp["volume"].sum().to_numpy(),
            "bar_close_time": grp["close_time"].last().to_numpy(),
            "n_8h": grp.size().to_numpy(),
        }
    ).reset_index(drop=True)
    bars["offset_h"] = offset_h
    # Defensive: bar_close_time MUST be > bar_open_time and within 24h.
    delta = bars["bar_close_time"] - bars["bar_open_time"]
    if (delta <= 0).any():
        raise RuntimeError(
            f"aggregate_to_24h: bar_close_time <= bar_open_time for offset_h={offset_h}. "
            "Aggregation bug — check input 8h CSV sort order."
        )
    if (delta > MS_PER_DAY).any():
        raise RuntimeError(
            f"aggregate_to_24h: bar_close_time > bar_open_time + 24h for offset_h={offset_h}. "
            "Aggregation bug — cross-day contamination."
        )
    return bars


# ---------------------------------------------------------------------------
# 14-feature computation on 24h bars (per-offset ISOLATED)
# ---------------------------------------------------------------------------


def _compute_natr_21(df: pd.DataFrame) -> np.ndarray:
    """natr_21_raw on 24h bars: 21-bar ATR / close. Used as the ATR column for labels."""
    high = df["high"].to_numpy(dtype="float64")
    low = df["low"].to_numpy(dtype="float64")
    close = df["close"].to_numpy(dtype="float64")
    prev_close = np.concatenate([[np.nan], close[:-1]])
    tr = np.maximum(
        high - low,
        np.maximum(np.abs(high - prev_close), np.abs(low - prev_close)),
    )
    atr = pd.Series(tr).rolling(21, min_periods=21).mean().to_numpy()
    with np.errstate(divide="ignore", invalid="ignore"):
        natr = np.where(close > 0, atr / close, np.nan)
    return natr


def _ema(x: np.ndarray, span: int) -> np.ndarray:
    return pd.Series(x).ewm(span=span, adjust=False, min_periods=span).mean().to_numpy()


def _atr_ewm(high: np.ndarray, low: np.ndarray, close: np.ndarray, period: int) -> pd.Series:
    """Wilder EWM ATR matching regime_v3._atr — alpha=1/period.

    Matches the exact computation used by ``add_regime_v3_features`` so that
    ``atr_pct_rank_200`` in the 24h parquet is consistent with the 8h parquet.
    """
    prev_close = np.concatenate([[np.nan], close[:-1]])
    tr = np.maximum(
        high - low,
        np.maximum(np.abs(high - prev_close), np.abs(low - prev_close)),
    )
    return pd.Series(tr).ewm(alpha=1.0 / period, adjust=False).mean()


def _pct_rank_200(series: pd.Series) -> np.ndarray:
    """Rolling 200-bar percentile rank — current value vs last 200 observations.

    Matches ``regime_v3._pct_rank(series, 200)``:
      * min_periods = max(20, 200 // 5) = 40
      * result ∈ [0, 1]: fraction of prior values strictly less than the current one.
    """
    return (
        series.rolling(200, min_periods=40)
        .apply(lambda x: (x[:-1] < x[-1]).sum() / (len(x) - 1) if len(x) > 1 else 0.5, raw=True)
        .to_numpy()
    )


def _hurst_window(x: np.ndarray, w: int) -> np.ndarray:
    """Rescaled-range Hurst exponent on a rolling window of log-returns.

    out[t] uses x[t-w+1 .. t]. NaN where insufficient history or degenerate R/S.
    Pure-past-only computation: no future bar leaks into any index.
    """
    n = len(x)
    out = np.full(n, np.nan)
    if n < w + 1:
        return out
    log_x = np.log(np.where(x > 0, x, np.nan))
    log_ret = np.concatenate([[np.nan], np.diff(log_x)])
    for t in range(w, n):
        seg = log_ret[t - w + 1 : t + 1]
        if np.any(np.isnan(seg)):
            continue
        mean_seg = seg.mean()
        dev = seg - mean_seg
        cum = np.cumsum(dev)
        r_stat = cum.max() - cum.min()
        s_stat = seg.std(ddof=0)
        if s_stat > 0 and r_stat > 0:
            out[t] = np.log(r_stat / s_stat) / np.log(w)
    return out


def compute_features_24h(panel_one_offset: pd.DataFrame) -> pd.DataFrame:
    """Compute the /059 14-feature stack on ONE offset's 24h series.

    CRITICAL: features are computed independently per offset (rolling windows
    use only that offset's own bars). The caller must pass a DataFrame filtered
    to a single offset_h value. Cross-offset pollution is prevented by construction.

    Two cross-asset features (btc_ret_14d, sym_vs_btc_ret_7d) require the
    matching BTC offset panel — see compute_features_for_symbol() which handles
    the BTC join.

    Returns the input DataFrame with the 14 feature columns (+ natr_21_raw)
    appended in-place. All features are NaN-safe via min_periods.
    """
    d = panel_one_offset.sort_values("bar_close_time").reset_index(drop=True).copy()
    close = d["close"].to_numpy(dtype="float64")
    high = d["high"].to_numpy(dtype="float64")
    low = d["low"].to_numpy(dtype="float64")
    n = len(d)
    log_close = np.log(np.where(close > 0, close, np.nan))
    log_ret = np.concatenate([[np.nan], np.diff(log_close)])

    # natr_21_raw — ATR column for triple-barrier labeling.
    d["natr_21_raw"] = _compute_natr_21(d)

    # atr_pct_rank_200 — risk-gate primitive (vol-scaling + low-vol gate).
    # NOT a model feature (absent from V3_FEATURE_COLUMNS_24H); required by
    # RiskV3Wrapper._build_lookups regardless of feature set (see risk_v3.py:264).
    # Uses EWM ATR with alpha=1/14, matching regime_v3.add_regime_v3_features.
    atr14_ewm = _atr_ewm(high, low, close, period=14)
    d["atr_pct_rank_200"] = _pct_rank_200(atr14_ewm)

    # max_dd_window_50: drawdown from rolling 50-bar peak.
    roll_max = pd.Series(close).rolling(50, min_periods=50).max().to_numpy()
    with np.errstate(divide="ignore", invalid="ignore"):
        dd = np.where(roll_max > 0, (close - roll_max) / roll_max, np.nan)
    d["max_dd_window_50"] = dd

    # ema_spread_atr_20: (close - ema20) / atr14.
    ema20 = _ema(close, 20)
    prev_c = np.concatenate([[np.nan], close[:-1]])
    tr14 = np.maximum(high - low, np.maximum(np.abs(high - prev_c), np.abs(low - prev_c)))
    atr14 = pd.Series(tr14).rolling(14, min_periods=14).mean().to_numpy()
    with np.errstate(divide="ignore", invalid="ignore"):
        d["ema_spread_atr_20"] = np.where(atr14 > 0, (close - ema20) / atr14, np.nan)

    # ret_kurt_50, ret_kurt_200, ret_skew_50, ret_skew_200.
    s_ret = pd.Series(log_ret)
    d["ret_kurt_50"] = s_ret.rolling(50, min_periods=50).kurt().to_numpy()
    d["ret_kurt_200"] = s_ret.rolling(200, min_periods=200).kurt().to_numpy()
    d["ret_skew_50"] = s_ret.rolling(50, min_periods=50).skew().to_numpy()
    d["ret_skew_200"] = s_ret.rolling(200, min_periods=200).skew().to_numpy()

    # range_realized_vol_50: rolling std of log_ret.
    d["range_realized_vol_50"] = s_ret.rolling(50, min_periods=50).std().to_numpy()

    # hurst_100, hurst_diff_100_50.
    h100 = _hurst_window(close, 100)
    h50 = _hurst_window(close, 50)
    d["hurst_100"] = h100
    d["hurst_diff_100_50"] = h100 - h50

    # vwap_dev_20: (close - vwap20) / close.
    vol = d["volume"].to_numpy(dtype="float64")
    pv20 = pd.Series(close * vol).rolling(20, min_periods=20).sum().to_numpy()
    v20 = pd.Series(vol).rolling(20, min_periods=20).sum().to_numpy()
    with np.errstate(divide="ignore", invalid="ignore"):
        vwap20 = np.where(v20 > 0, pv20 / v20, np.nan)
        d["vwap_dev_20"] = np.where(close > 0, (close - vwap20) / close, np.nan)

    # ret_autocorr_lag1_50: rolling 50-bar lag-1 autocorrelation.
    def _ac_lag1(s: pd.Series) -> float:
        if s.isna().any() or len(s) < 3:
            return np.nan
        a = s.iloc[:-1].to_numpy()
        b = s.iloc[1:].to_numpy()
        sa = float(a.std())
        sb = float(b.std())
        if sa == 0 or sb == 0:
            return np.nan
        return float(((a - a.mean()) * (b - b.mean())).mean() / (sa * sb))

    d["ret_autocorr_lag1_50"] = (
        s_ret.rolling(50, min_periods=50).apply(_ac_lag1, raw=False).to_numpy()
    )

    # regime_momentum_signed_5d: ret_5d * sign(hurst_100 - 0.5).
    out_5 = np.full(n, np.nan)
    if n > 5:
        out_5[5:] = log_close[5:] - log_close[:-5]
    sign_h = np.sign(h100 - 0.5)
    d["regime_momentum_signed_5d"] = out_5 * sign_h

    # btc_ret_14d and sym_vs_btc_ret_7d are populated by add_btc_cross_features().
    # Set to NaN here so the column exists for downstream concatenation.
    d["btc_ret_14d"] = np.nan
    d["sym_vs_btc_ret_7d"] = np.nan

    return d


def add_btc_cross_features(
    symbol_panel: pd.DataFrame,
    btc_panel_by_offset: dict[int, pd.DataFrame],
) -> pd.DataFrame:
    """Attach btc_ret_14d and sym_vs_btc_ret_7d to a symbol's per-offset panel.

    btc_ret_14d: 14-bar log return of BTCUSDT at the SAME offset.
    sym_vs_btc_ret_7d: (sym 7-bar log return) - (btc 7-bar log return).

    Joined by bar_close_time at the same offset (exact equality). Past-only
    by construction — BTC features computed from same-offset BTC bars.
    """
    d = symbol_panel.sort_values("bar_close_time").reset_index(drop=True).copy()
    offset_h = int(d["offset_h"].iloc[0])
    btc = btc_panel_by_offset[offset_h].sort_values("bar_close_time").reset_index(drop=True)
    btc_close = btc["close"].to_numpy(dtype="float64")
    btc_log = np.log(np.where(btc_close > 0, btc_close, np.nan))
    n_b = len(btc)
    btc_ret_14d = np.full(n_b, np.nan)
    btc_ret_7d = np.full(n_b, np.nan)
    if n_b > 14:
        btc_ret_14d[14:] = btc_log[14:] - btc_log[:-14]
    if n_b > 7:
        btc_ret_7d[7:] = btc_log[7:] - btc_log[:-7]
    btc_join = pd.DataFrame(
        {
            "bar_close_time": btc["bar_close_time"].to_numpy(),
            "btc_ret_14d": btc_ret_14d,
            "btc_ret_7d": btc_ret_7d,
        }
    )
    d = d.merge(btc_join, on="bar_close_time", how="left", suffixes=("_sym", ""))
    # Drop the NaN placeholder columns populated by compute_features_24h.
    for _col in ["btc_ret_14d_sym", "sym_vs_btc_ret_7d"]:
        if _col in d.columns:
            d = d.drop(columns=[_col])
    # Keep the btc_ret_14d from the join (replaces NaN placeholder).
    sym_close = d["close"].to_numpy(dtype="float64")
    sym_log = np.log(np.where(sym_close > 0, sym_close, np.nan))
    n = len(d)
    sym_ret_7d = np.full(n, np.nan)
    if n > 7:
        sym_ret_7d[7:] = sym_log[7:] - sym_log[:-7]
    d["sym_vs_btc_ret_7d"] = sym_ret_7d - d["btc_ret_7d"].to_numpy()
    d = d.drop(columns=["btc_ret_7d"])
    return d


# ---------------------------------------------------------------------------
# BTC offset panels helper
# ---------------------------------------------------------------------------


def build_btc_offset_panels(data_dir: Path | str) -> dict[int, pd.DataFrame]:
    """Build per-offset BTCUSDT 24h panels (close + bar_close_time only).

    Computed once and shared across all symbol feature computations.
    Reads data/BTCUSDT/8h.csv (no IS fence — caller is responsible).
    """
    data_dir = Path(data_dir)
    out: dict[int, pd.DataFrame] = {}
    df8h = load_8h_csv(data_dir, "BTCUSDT")
    for off in OFFSETS_H:
        out[off] = aggregate_to_24h(df8h, off)
    return out


# ---------------------------------------------------------------------------
# Top-level per-symbol feature generation
# ---------------------------------------------------------------------------


def generate_multioffset_24h_features(
    symbol: str,
    data_dir: Path | str,
    features_24h_dir: Path | str,
    btc_panels: dict[int, pd.DataFrame] | None = None,
) -> Path:
    """Generate the 24h multi-offset feature parquet for one symbol.

    Steps (look-ahead-free):
      1. Load 8h CSV for the symbol.
      2. For each offset_h ∈ {0, 8, 16}:
         a. Aggregate 8h → 24h at that offset.
         b. Compute 14 features on that offset's bars ONLY.
         c. Join BTC cross-asset features from the same-offset BTC panel.
      3. Concatenate the 3 per-offset frames; add offset_id column.
      4. Sort by bar_close_time.
      5. Add `open_time = bar_open_time` (for lgbm.py join compatibility).
      6. Write to features_24h_dir/<symbol>_24h_features.parquet.
         Filename uses the naming convention `{sym}_{interval}_features.parquet`
         that LightGbmStrategy.lookup_features() and _load_atr_for_master() expect
         when interval='24h'. The '_multioffset' suffix is omitted from the filename
         so lgbm.py's standard lookup (f"{sym}_{self._interval}_features.parquet")
         resolves correctly.

    Returns the Path of the written parquet.

    The parquet schema:
        open_time (= bar_open_time — lgbm.py join key),
        bar_open_time, bar_close_time, open, high, low, close, volume,
        offset_h, n_8h, natr_21_raw,
        <14 V3_FEATURE_COLUMNS_24H columns>,
        offset_id (int64 — the 15th feature; alias of offset_h)

    Note: warm-up rows (NaN feature values) are PRESERVED so LightGbmStrategy
    can apply its own min_periods NaN filtering at training time.
    """
    data_dir = Path(data_dir)
    features_24h_dir = Path(features_24h_dir)
    if btc_panels is None:
        btc_panels = build_btc_offset_panels(data_dir)

    features_24h_dir.mkdir(parents=True, exist_ok=True)

    df8h = load_8h_csv(data_dir, symbol)
    parts: list[pd.DataFrame] = []
    for off in OFFSETS_H:
        bars = aggregate_to_24h(df8h, off)
        feat = compute_features_24h(bars)
        feat = add_btc_cross_features(feat, btc_panels)
        parts.append(feat)

    panel = pd.concat(parts, axis=0, ignore_index=True)
    panel = panel.sort_values("bar_close_time").reset_index(drop=True)
    panel["offset_id"] = panel["offset_h"].astype("int64")

    # Add open_time alias = bar_open_time for lgbm.py lookup compatibility.
    # LightGbmStrategy._load_atr_for_master reads features by joining on open_time.
    panel["open_time"] = panel["bar_open_time"].to_numpy(dtype="int64")

    # Write with the interval-canonical filename that lgbm.py expects:
    # features_dir/{sym}_24h_features.parquet → resolves at interval='24h'.
    out_path = features_24h_dir / f"{symbol}_24h_features.parquet"
    panel.to_parquet(out_path, index=False)
    return out_path


def write_24h_kline_csv(symbol: str, data_dir: Path | str) -> Path:
    """Write the 24h multi-offset OHLCV as a kline-compatible CSV at data/<SYM>/24h.csv.

    The backtest engine's build_master reads from csv_path(data_dir, symbol, interval),
    which is data/<SYM>/<interval>.csv. At --bar-interval 24h, BacktestConfig.interval='24h'
    so the engine expects data/<SYM>/24h.csv. This function writes a kline-compatible
    CSV (with zero-filled ancillary columns: quote_volume, trades, taker_buy_volume,
    taker_buy_quote_volume) so the standard load_kline_array() path works unchanged.

    The CSV contains the full 3-offset concatenated panel sorted by bar_close_time.
    The standard kline columns are:
        open_time      = bar_open_time (the 24h window start)
        open, high, low, close, volume
        close_time     = bar_close_time (the CAUSAL timestamp — close_time of the
                         last 8h sub-bar in the window)
        quote_volume   = 0 (not available from aggregation; unused by backtest)
        trades         = 0 (not available; unused by backtest)
        taker_buy_volume          = 0 (unused)
        taker_buy_quote_volume    = 0 (unused)

    CAUSAL CORRECTNESS: open_time = bar_open_time (when the decision is made);
    close_time = bar_close_time (when OHLCV is fully known). The backtest uses
    open_time for trade entry and close_time for labelling/exit scanning — both
    are correct at 24h.

    Returns the path of the written CSV.
    """
    data_dir = Path(data_dir)
    df8h = load_8h_csv(data_dir, symbol)
    parts: list[pd.DataFrame] = []
    for off in OFFSETS_H:
        bars = aggregate_to_24h(df8h, off)
        parts.append(bars)
    panel = pd.concat(parts, axis=0, ignore_index=True)
    panel = panel.sort_values("bar_close_time").reset_index(drop=True)

    # Build the kline-compatible CSV frame.
    csv_frame = pd.DataFrame(
        {
            "open_time": panel["bar_open_time"].to_numpy(dtype="int64"),
            "open": panel["open"].to_numpy(dtype="float64"),
            "high": panel["high"].to_numpy(dtype="float64"),
            "low": panel["low"].to_numpy(dtype="float64"),
            "close": panel["close"].to_numpy(dtype="float64"),
            "volume": panel["volume"].to_numpy(dtype="float64"),
            "close_time": panel["bar_close_time"].to_numpy(dtype="int64"),
            "quote_volume": 0.0,
            "trades": 0,
            "taker_buy_volume": 0.0,
            "taker_buy_quote_volume": 0.0,
        }
    )
    out_path = data_dir / symbol / "24h.csv"
    csv_frame.to_csv(out_path, index=False)
    return out_path


def generate_all_multioffset_24h_features(
    symbols: list[str],
    data_dir: Path | str,
    features_24h_dir: Path | str,
) -> dict[str, Path]:
    """Generate 24h multi-offset feature parquets AND kline CSVs for all symbols.

    For each symbol (excluding BTCUSDT which is cross-asset only):
      1. Writes data/<SYM>/24h.csv (kline-compatible OHLCV for the backtest engine).
      2. Writes data/features_v3_24h/<SYM>_24h_multioffset_features.parquet.

    BTCUSDT gets a 24h.csv (for cross-asset feature construction) but NOT a feature
    parquet (it is not a traded symbol in the v3 BCH/LDO/TRX universe).

    Builds BTC panels once and reuses across symbols.
    Returns a dict mapping symbol → parquet path (only for non-BTC symbols).
    """
    data_dir = Path(data_dir)
    features_24h_dir = Path(features_24h_dir)
    btc_panels = build_btc_offset_panels(data_dir)
    result: dict[str, Path] = {}
    for sym in symbols:
        # Write kline CSV (needed for backtest engine's build_master).
        csv_path = write_24h_kline_csv(sym, data_dir)
        print(f"  [24h kline] {sym}: wrote {csv_path.name}")
        if sym == "BTCUSDT":
            # BTC is cross-asset only — no feature parquet needed.
            continue
        path = generate_multioffset_24h_features(sym, data_dir, features_24h_dir, btc_panels)
        result[sym] = path
        print(f"  [24h features] {sym}: wrote {path.name}")
    return result
