"""iter-v3/122 — CYCLE-7 EXPLORATION #1 — ETH cross-asset feature family EDA.

THE AXIS UNDER TEST (cycle-7 EXPLORATION slot #1 — axis-1 cross-asset/external feeds
per BASELINE_V3.md §"Cycle 7 Axis Priorities" + the /121 closeout candidate menu):

    Does adding ETH-derived cross-asset features (ETH's own returns, ETH-vs-BTC
    relative-strength, ETH-vs-BTC vol differential) — computed from existing
    `data/ETHUSDT/8h.csv` klines via the established `cross_btc_v3.py` external-
    merge pattern — carry incremental directional signal beyond the 14-feature
    /121 BASELINE_V3 stack on the BCH/LDO/TRX 8h cohort?

THE 7-FEED VERDICT — CONFRONTED HEAD-ON (the critical lineage discipline check):

  The BASELINE_V3.md "7-FEED STRUCTURAL VERDICT" — established at iter-v3/086
  closeout, validated at iter-v3/119 — explicitly says: "iter-v3/087+ MUST NOT
  be an 8th crypto-native feature family on the same architecture." The 7
  closed feeds are:

    funding rate (/019, /023, /024, /082 4-family, /085 composed-sign) — 5 data
      points; CLOSED on direct + composed constructions.
    microstructure  (/015 tbr_zscore_30) — 1 data point.
    perp-spot basis (/086 3-family) — 1 data point.

  ALL 7 are NON-OHLCV DERIVATIVES-METADATA feeds — sentiment metadata derived
  from funding settlements, taker-buy quote-volume ratios, or perp-vs-spot mark
  prices. They are crypto-EXCHANGE-INTERNAL feeds.

  ETH klines (`data/ETHUSDT/8h.csv`) are OHLCV — not a derivatives-metadata feed.
  ETH is the #2 crypto-asset by market cap (the index of "everything that isn't
  BTC" in the crypto cross-section); ETH-vs-BTC relative strength encodes
  alt-rotation regime (a market-structure feature, not a sentiment-data feature).
  The information content is structurally different from the 7 closed feeds:
  the closed feeds capture LEVERAGE/POSITIONING (funding) or LIQUIDITY-FLOW
  (microstructure, basis); ETH-vs-BTC captures CROSS-ASSET-PRICE-DIVERGENCE,
  which is a market-structure regime classifier orthogonal to all 7 closed
  derivatives-metadata feeds.

  The verdict's mechanism — "v3 per-symbol depth-3-5 LightGBM trained on
  ~2700-5700 IS rows declines to allocate ranked split capacity to crypto-native
  sentiment information" — addresses sentiment-metadata feeds (where each
  candle has a single scalar funding rate or single scalar basis number that
  the model treats as a numeric feature). ETH OHLCV is structurally different
  in that ETH-derived features participate in the SAME OHLCV family as the
  existing baseline's BTC-derived features (`btc_ret_3d`, `btc_ret_7d`,
  `btc_ret_14d`, `btc_vol_14d`, `sym_vs_btc_ret_7d`). The baseline already
  includes 5 BTC cross-asset features and the importance of `sym_vs_btc_ret_7d`
  at /059 is non-INERT (rank ~7-9/14 on portfolio; gain non-trivial).

  Therefore: the 7-FEED verdict's no-go rule applies to "8th NON-OHLCV crypto-
  native sentiment feed family"; ETH-OHLCV cross-asset features are NOT in that
  scope. This is the same lineage discipline that distinguished /086 (basis;
  IN-SCOPE crypto-native) from /063's `btc_funding_rate_zscore_30` (IN-SCOPE
  derivatives-metadata) vs. the existing baseline BTC OHLCV features (OUT-OF-
  SCOPE because OHLCV-family).

WHY THIS IS NOT A CLOSED / DEAD PATH — dead-path adjacency check:

  iter-v3/063 mass-expansion `sym_vs_btc_ret_3d` / `sym_vs_btc_vol_14d` — REMOVED
               at /064 because the 46-feature MASS expansion catastrophically
               collapsed IS. The features themselves were not falsified — they
               were collateral casualties of the mass-expansion mechanism (per
               `feedback_v3_mass_feature_expansion.md` phased single-feature
               expansion is the path forward). /122 adds at most 4 ETH-cross-
               asset features (phased small-N, not mass) to the 14-feature
               anchor.

  iter-v3/088  cross-sectional re-architecture — used 22-symbol XS_UNIVERSE
               with lambdarank training. ETH was IN the XS_UNIVERSE alongside
               many other alts. /088 was an architecture replacement, not a
               feature addition. /122 keeps the per-symbol architecture entirely
               unchanged; ETH OHLCV merges as a fifth cross-asset feature
               source (alongside the existing BTC merge) into each per-symbol
               LightGBM model's feature matrix. Different mechanism.

  iter-v3/087  WHOLESALE universe expansion 3→6 (GALA+MANA+SAND) — NEGATIVE.
               This was a UNIVERSE axis (TRADED symbols). ETH is in
               V3_EXCLUDED_SYMBOLS (can never be traded by v3); the proposal
               is a CROSS-ASSET FEATURE axis (ETH's klines feed into BCH/LDO/
               TRX features). The /087 closure addresses universe-expansion
               as a breadth lever, not cross-asset features.

  cycle-7 axis menu — BASELINE_V3.md §"Cycle 7 Axis Priorities" lists "HIGH —
               Cross-asset/external feeds" as the FIRST priority and explicitly
               says the constraint is "STRUCTURALLY DIFFERENT primitives than
               the 7 prior INERT-by-importance crypto-native feeds". ETH OHLCV
               is structurally different — see lineage discipline above.

THE FIVE-STEP EDA GATE (mirrors /119 + /118 methodology):
  Step 1 — T1: candidate catalog (4 ETH-derived candidates).
  Step 2 — T2: Linear Redundancy Pre-Falsifier (R² vs 14-feature anchor +
               5 existing BTC-cross-asset baseline; carve-out allowed for
               composed-feature carrier IFF the carrier is /025-class).
  Step 3 — T3 (POOLED) + T4 (per-symbol) univariate walk-forward AUC.
  Step 4 — T5: multivariate (14+1) depth-4 LightGBM importance per symbol.
  Step 5 — T7: multivariate-LIFT screen (14 vs 14+1 OOF AUC, POOLED +
               per-symbol). T9: SSC-RISK gate (the /119-NEW per /118 closeout).
               T6: GO/NO-GO verdict synthesis.

PRE-REGISTERED GO RULE (synthesis script):
  Selection criterion (top candidate emerges):
    - T7 POOLED lift > +0.003 (the /118 + /119 threshold, conservatively set)
    - T9 SSC-RISK FALSE (broad-based, not single-symbol-carrier)
    - T5 importance allocation non-zero (NOT rank 15/15 with near-zero gain)
    - T2 R² < 0.70 OR carve-out applies (composed-feature carve-out NOT used
      here because ETH features are not /025-class composed features —
      they are simple log-return / vol-differential primitives, so the
      strict R² < 0.70 gate applies).

  Per THE PRIME DIRECTIVE the EDA NEVER terminates the iteration — a NO-GO
  sharpens the brief's pre-registered failure mode and the backtest still
  runs. The GO/NO-GO verdict only sets the brief's modal prediction and the
  Section-7/8 pre-registration.

NO CHEATING — strict IS-only invariant
--------------------------------------
Every feature/label row entering any computation in THIS module has
close_time < OOS_CUTOFF_MS = 1742774400000 (2025-03-24). The post-cutoff OOS
is NEVER read by any script in analysis/iteration_v3-122/. ETH klines loaded
from `data/ETHUSDT/8h.csv` are fenced at row level to IS only.

The ETH feature computations use the cross_btc_v3.py pattern verbatim —
log-return windows are past-only (concatenated NaN-prefix + diff-style), the
realized-vol is `rolling(min_periods=W).std()` (the canonical past-only
pandas rolling). The same audit that /059 + /119 passed for BTC features
extends to ETH features by construction (identical math, different symbol).
"""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

REPO_ROOT = Path(__file__).resolve().parents[2]

OOS_CUTOFF_MS = 1742774400000  # 2025-03-24 -- IMMUTABLE
SYMBOLS: tuple[str, ...] = ("BCHUSDT", "LDOUSDT", "TRXUSDT")  # canonical /059 universe

# The /121 14-feature anchor stack — UNCHANGED vs /059 / /121 BASELINE_V3.md.
# /121 reverted to this 14-feature set when Component B (ret5d_signed_tbi) was
# dropped after /120 attribution analysis.
V3_FEATURE_COLUMNS: list[str] = [
    "max_dd_window_50",
    "ema_spread_atr_20",
    "ret_kurt_50",
    "ret_skew_200",
    "range_realized_vol_50",
    "hurst_diff_100_50",
    "ret_kurt_200",
    "hurst_100",
    "btc_ret_14d",  # existing BTC cross-asset baseline feature
    "ret_skew_50",
    "vwap_dev_20",
    "ret_autocorr_lag1_50",
    "sym_vs_btc_ret_7d",  # existing symbol-vs-BTC baseline feature
    "regime_momentum_signed_5d",
]

# Triple-barrier label config (faithful to /059 / /121).
ATR_TP_MULT = 2.0
ATR_SL_MULT = 1.0
ATR_COL = "natr_21_raw"
TIMEOUT_BARS = 21  # 21 x 8h = 168h horizon — the /059 canonical timeout
FEE_PCT = 0.1

# Walk-forward fold geometry.
N_FOLDS_DEFAULT = 5
EMBARGO_BARS = 22  # /059 walk-forward embargo at the 8h timescale


# -----------------------------------------------------------------------------
# IS fence and panel loaders
# -----------------------------------------------------------------------------


def _is_only_fence(df: pd.DataFrame) -> pd.DataFrame:
    """Apply IS-only fence at row level. Defensive — raises if any row leaks."""
    out = df[df["close_time"] < OOS_CUTOFF_MS].copy()
    if (out["close_time"] >= OOS_CUTOFF_MS).any():
        raise RuntimeError("IS fence breach detected")
    return out


def load_features_is(symbol: str) -> pd.DataFrame:
    """Load one symbol's pre-computed 8h features parquet, IS-only fenced."""
    parquet = REPO_ROOT / "data" / "features_v3" / f"{symbol}_8h_features.parquet"
    df = pd.read_parquet(parquet)
    df = df.sort_values("open_time").reset_index(drop=True)
    df = _is_only_fence(df)
    return df


# -----------------------------------------------------------------------------
# ETH cross-asset features (paralleling cross_btc_v3.py — IDENTICAL MATH, the
# only delta is the source CSV is ETHUSDT.csv instead of BTCUSDT.csv). The
# features below are computed past-only by construction (rolling.std with
# min_periods=window, log-return windows with NaN-prefix concat). The same
# walk-forward audit that /059 passed for `btc_ret_14d` and `sym_vs_btc_ret_7d`
# extends here by construction.
# -----------------------------------------------------------------------------


def _load_eth_klines() -> pd.DataFrame:
    """Load ETH 8h klines and compute ETH-derived features (cached at module level)."""
    csv_path = REPO_ROOT / "data" / "ETHUSDT" / "8h.csv"
    df = pd.read_csv(csv_path).sort_values("open_time").reset_index(drop=True)
    close = df["close"].to_numpy(dtype=np.float64)
    log_close = np.log(close)
    log_ret_1bar = np.concatenate([[np.nan], np.diff(log_close)])

    # 3-day = 9 8h bars; 14-day = 42 8h bars; 21-day = 63 8h bars.
    df["eth_ret_3d"] = np.concatenate([np.full(9, np.nan), log_close[9:] - log_close[:-9]])
    df["eth_ret_7d"] = np.concatenate([np.full(21, np.nan), log_close[21:] - log_close[:-21]])
    df["eth_ret_14d"] = np.concatenate([np.full(42, np.nan), log_close[42:] - log_close[:-42]])
    df["eth_ret_21d"] = np.concatenate([np.full(63, np.nan), log_close[63:] - log_close[:-63]])

    # 14-day realized vol from 1-bar log returns (annualized over 42-bar window).
    eth_vol = pd.Series(log_ret_1bar).rolling(42, min_periods=42).std().to_numpy() * np.sqrt(42)
    df["eth_vol_14d"] = eth_vol

    return df[["open_time", "eth_ret_3d", "eth_ret_7d", "eth_ret_14d", "eth_ret_21d", "eth_vol_14d"]].copy()


def _load_btc_klines() -> pd.DataFrame:
    """Load BTC 8h klines and compute BTC-derived features (mirrors cross_btc_v3.py)."""
    csv_path = REPO_ROOT / "data" / "BTCUSDT" / "8h.csv"
    df = pd.read_csv(csv_path).sort_values("open_time").reset_index(drop=True)
    close = df["close"].to_numpy(dtype=np.float64)
    log_close = np.log(close)
    log_ret_1bar = np.concatenate([[np.nan], np.diff(log_close)])

    df["btc_ret_21d"] = np.concatenate([np.full(63, np.nan), log_close[63:] - log_close[:-63]])
    btc_vol = pd.Series(log_ret_1bar).rolling(42, min_periods=42).std().to_numpy() * np.sqrt(42)
    df["btc_vol_14d_proxy"] = btc_vol  # local recompute to avoid parquet-version drift

    return df[["open_time", "btc_ret_21d", "btc_vol_14d_proxy"]].copy()


def _attach_eth_cross_features(df: pd.DataFrame) -> pd.DataFrame:
    """Merge ETH-derived features into a symbol's 8h panel by open_time.

    Adds 4 candidate features to the panel:
      A1 = eth_ret_14d                  — ETH's 14-day log return
      A2 = eth_vs_btc_ret_21d           — ETH 21d ret minus BTC 21d ret
      A3 = eth_vs_btc_vol_diff_14d      — ETH 14d vol minus BTC 14d vol
      A4 = eth_ret_3d                   — ETH's 3-day log return

    All features are past-only by construction (the underlying log-returns and
    realized vols use the canonical past-only rolling/diff convention).
    """
    out = df.copy()
    eth = _load_eth_klines()
    btc = _load_btc_klines()

    # Merge on open_time (left join — preserve symbol's panel rows).
    out = out.merge(eth, on="open_time", how="left")
    out = out.merge(btc, on="open_time", how="left")

    out["A1_eth_ret_14d"] = out["eth_ret_14d"]
    out["A2_eth_vs_btc_ret_21d"] = out["eth_ret_21d"] - out["btc_ret_21d"]
    out["A3_eth_vs_btc_vol_diff_14d"] = out["eth_vol_14d"] - out["btc_vol_14d_proxy"]
    out["A4_eth_ret_3d"] = out["eth_ret_3d"]

    # Drop intermediates to keep panel clean.
    out = out.drop(
        columns=[c for c in ["eth_ret_3d", "eth_ret_7d", "eth_ret_14d", "eth_ret_21d",
                              "eth_vol_14d", "btc_ret_21d", "btc_vol_14d_proxy"]
                  if c in out.columns]
    )
    return out


# -----------------------------------------------------------------------------
# Triple-barrier label on 8h bars (faithful to /059 labelling.label_trades)
# -----------------------------------------------------------------------------


def label_triple_barrier(df: pd.DataFrame) -> pd.DataFrame:
    """Triple-barrier label every 8h bar in one symbol's panel.

    Faithful to v3 labelling.label_trades (triple_barrier): forward-scan to the
    timeout candle, SL checked before TP within a bar (adverse-first), label =
    sign of the better of (long net PnL, short net PnL).
    """
    d = df.sort_values("open_time").reset_index(drop=True).copy()
    close = d["close"].to_numpy(dtype="float64")
    high = d["high"].to_numpy(dtype="float64")
    low = d["low"].to_numpy(dtype="float64")
    atr = d[ATR_COL].to_numpy(dtype="float64")
    n = len(d)
    label = np.zeros(n, dtype="int64")
    valid = np.zeros(n, dtype=bool)
    for i in range(n):
        entry = close[i]
        if entry <= 0:
            continue
        a = atr[i] if not np.isnan(atr[i]) else entry * 0.02
        tp_dist = a * ATR_TP_MULT
        sl_dist = a * ATR_SL_MULT
        long_tp = entry + tp_dist
        long_sl = entry - sl_dist
        short_tp = entry - tp_dist
        short_sl = entry + sl_dist
        long_res = 0
        short_res = 0
        last_close = entry
        deadline_idx = i + TIMEOUT_BARS
        if deadline_idx >= n:
            continue
        for j in range(i + 1, deadline_idx + 1):
            h_bar = high[j]
            l_bar = low[j]
            last_close = close[j]
            if long_res == 0:
                if l_bar <= long_sl:
                    long_res = -1
                elif h_bar >= long_tp:
                    long_res = 1
            if short_res == 0:
                if h_bar >= short_sl:
                    short_res = -1
                elif l_bar <= short_tp:
                    short_res = 1
            if long_res != 0 and short_res != 0:
                break
        if long_res == 0:
            long_res = -2
        if short_res == 0:
            short_res = -2
        fee = entry * (FEE_PCT / 100.0) * 2.0
        if long_res == 1:
            long_pnl = tp_dist - fee
        elif long_res == -1:
            long_pnl = -sl_dist - fee
        else:
            long_pnl = (last_close - entry) - fee
        if short_res == 1:
            short_pnl = tp_dist - fee
        elif short_res == -1:
            short_pnl = -sl_dist - fee
        else:
            short_pnl = (entry - last_close) - fee
        label[i] = 1 if long_pnl >= short_pnl else 0
        valid[i] = True
    d["label"] = label
    d["label_valid"] = valid
    return d


# -----------------------------------------------------------------------------
# Candidate names + motivations (T1 catalog)
# -----------------------------------------------------------------------------


CANDIDATE_NAMES: tuple[str, ...] = (
    "A1_eth_ret_14d",
    "A2_eth_vs_btc_ret_21d",
    "A3_eth_vs_btc_vol_diff_14d",
    "A4_eth_ret_3d",
)

CANDIDATE_CATEGORY: dict[str, str] = {
    "A1_eth_ret_14d": "(v) cross-asset ETH momentum",
    "A2_eth_vs_btc_ret_21d": "(v) cross-asset ETH/BTC relative-strength",
    "A3_eth_vs_btc_vol_diff_14d": "(v) cross-asset ETH/BTC vol-regime",
    "A4_eth_ret_3d": "(v) cross-asset ETH momentum (short-horizon)",
}

CANDIDATE_MOTIVATION: dict[str, str] = {
    "A1_eth_ret_14d": (
        "ETH's own 14-day log return — symmetric mate to the baseline btc_ret_14d. "
        "ETH is the #2 crypto-asset; ETH's regime is structurally distinct from "
        "BTC's at multi-week horizons (alt-season hypothesis). Past-only by "
        "construction (same math as cross_btc_v3.py's btc_ret_14d)."
    ),
    "A2_eth_vs_btc_ret_21d": (
        "ETH 21-day return minus BTC 21-day return — alt-rotation regime indicator. "
        "When ETH outpaces BTC on multi-week horizon, the broader alt market "
        "tends to follow (Grinold-Kahn cross-asset edge hypothesis). 21-day "
        "horizon avoids overlap with baseline 7d / 14d windows."
    ),
    "A3_eth_vs_btc_vol_diff_14d": (
        "ETH 14-day realized vol minus BTC 14-day realized vol. When ETH "
        "vol-leads BTC, it often signals risk-on regime where alts (incl. "
        "BCH/LDO/TRX) experience higher idiosyncratic moves. Symmetric mate "
        "to the existing baseline cross-asset 14d-vol family."
    ),
    "A4_eth_ret_3d": (
        "ETH's 3-day log return — short-horizon ETH-trend signal. Encodes "
        "leading-asset momentum on a fast horizon; cross-asset analog to "
        "the 3d horizon that /063's btc_ret_3d touched (REMOVED at /064 in "
        "collateral mass-expansion). Reintroduced as the ETH variant via "
        "phased single-feature axis discipline."
    ),
}


# -----------------------------------------------------------------------------
# Walk-forward fold geometry on 8h bars (IS-only)
# -----------------------------------------------------------------------------


def walk_forward_folds(n: int, n_folds: int = N_FOLDS_DEFAULT) -> list[tuple[np.ndarray, np.ndarray]]:
    """Expanding-window folds with a 22-bar embargo purged before test."""
    start = int(n * 0.40)
    test_span = n - start
    chunk = test_span // n_folds
    folds = []
    for k in range(n_folds):
        test_lo = start + k * chunk
        test_hi = start + (k + 1) * chunk if k < n_folds - 1 else n
        train_hi = max(0, test_lo - EMBARGO_BARS)
        train_idx = np.arange(0, train_hi)
        test_idx = np.arange(test_lo, test_hi)
        if len(train_idx) >= 200 and len(test_idx) >= 50:
            folds.append((train_idx, test_idx))
    return folds


# -----------------------------------------------------------------------------
# Per-symbol panel builder (features + label + candidates, IS-only)
# -----------------------------------------------------------------------------


def build_labeled_panel(symbol: str) -> pd.DataFrame:
    """Load symbol's 8h features, label, attach ETH candidates. IS-only fenced."""
    df = load_features_is(symbol)
    df = label_triple_barrier(df)
    df = _attach_eth_cross_features(df)
    feat_cols = list(V3_FEATURE_COLUMNS) + list(CANDIDATE_NAMES)
    keep_cols = ["open_time", "close_time", "close", "label", "label_valid"] + feat_cols
    keep_cols = [c for c in keep_cols if c in df.columns]
    df = df[keep_cols].copy()
    # Filter to valid-label rows where all 14 baseline + 4 candidates are non-NaN.
    keep = df["label_valid"] & df[feat_cols].notna().all(axis=1)
    df = df[keep].reset_index(drop=True)
    df["symbol"] = symbol
    return df
