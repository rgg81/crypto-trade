"""iter-v3/123 — CYCLE-7 EXPLORATION #2 — ETH-vs-symbol VOL-REGIME-RATIO cross-asset EDA.

THE AXIS UNDER TEST (cycle-7 EXPLORATION slot #2 — axis-1 cross-asset/external feeds
per BASELINE_V3.md §"Cycle 7 Axis Priorities" + the /122 closeout Critic
Recommendation 1 — sister to /122 axis but **non-IC-spanned by the 14-feature
incumbent stack**):

    Does adding `eth_realized_vol_50 / sym_realized_vol_50` (ETH-vs-symbol
    50-bar realized-vol regime ratio) as a sub-axis-B1 cross-asset feature
    — computed from `data/ETHUSDT/8h.csv` klines via the established
    cross_btc_v3 external-merge pattern, normalized by the symbol's own
    50-bar realized vol — carry incremental directional signal beyond the
    14-feature /121 BASELINE_V3 stack on the BCH/LDO/TRX 8h cohort?

THE /122 LESSON LEARNED — IC-SPANNING DIAGNOSTIC (critical context):

  /122 tested A4_eth_ret_3d (cycle-7 slot #1; ETH 3-day log return). FILED
  EXPLORATION-NEGATIVE-INERT (Critic FINAL `9e0eeb6`, 2026-05-20). The
  controlling diagnostic at post-mortem was the IC matrix:
    eth_ret_3d max |IC| = 0.5613 with vwap_dev_20
    eth_ret_3d secondary |IC| = 0.5280 with regime_momentum_signed_5d
    eth_ret_3d tertiary |IC| = 0.4055 with btc_ret_14d
  The T2 R² screen (joint-R² = 0.44) at /122 EDA was INSUFFICIENT diagnostic
  for ETH-derived primitives at the 0.50-0.56 |IC| range. The Critic
  recommendation: "EDA T2 R² against the FULL 15-feature anchor must clear
  the gate **AND** EDA must show pairwise |IC| < 0.40 with `vwap_dev_20` and
  `regime_momentum_signed_5d` specifically. Joint-R² is insufficient
  diagnostic for ETH-derived primitives."

  Sub-axis B1 (eth_realized_vol_50 / sym_realized_vol_50) is the
  STRUCTURALLY NON-IC-SPANNED ETH derivative — it depends on ETH
  REALIZED-VOL (the second moment) not ETH PRICE-RETURN (the first moment).
  vwap_dev_20 and regime_momentum_signed_5d are FIRST-MOMENT primitives;
  the vol-ratio is a SECOND-MOMENT primitive. The pairwise IC against these
  incumbents is predicted ≤ 0.25 (vwap_dev_20) and ≤ 0.30
  (regime_momentum_signed_5d).

THE 7-FEED VERDICT — INHERITED FROM /122 (the critical lineage discipline):

  BASELINE_V3.md "7-FEED STRUCTURAL VERDICT" (established at iter-v3/086,
  validated at iter-v3/119, applied at /122): "iter-v3/087+ MUST NOT be an
  8th crypto-native feature family on the same architecture." The 7 closed
  feeds are: funding (/019/023/024/082/085), microstructure (/015), basis
  (/086) — ALL NON-OHLCV DERIVATIVES-METADATA feeds.

  ETH OHLCV is OHLCV-family, OUT-OF-SCOPE of the 7-FEED verdict (validated
  at /122 — the verdict applied to direct ETH returns and the family
  remains OUT-OF-SCOPE for sub-axis B1 ETH-realized-vol-ratio). The
  vol-ratio is computed entirely from OHLC close prices via 1-bar log
  returns and rolling std — no derivatives-metadata is involved.

WHY THIS IS NOT A CLOSED / DEAD PATH — dead-path adjacency check:

  iter-v3/122  eth_ret_3d closed at EXPLORATION-NEGATIVE-INERT — the
               PRIMITIVE eth_ret_3d is closed, NOT the broader ETH-OHLCV
               cross-asset hypothesis (Critic explicit per-primitive
               interpretation in `review.md` Recommendation 1). Sub-axis
               B1 (vol-regime ratio) is a DIFFERENT primitive: second-
               moment vs eth_ret_3d's first-moment; cross-asset RATIO
               (not direct ETH derivative) vs eth_ret_3d's direct return;
               structurally orthogonal to both vwap_dev_20 (first-moment
               price deviation) and regime_momentum_signed_5d (first-
               moment return-times-regime composed feature).

  iter-v3/119  C6 composed feature (ret5d_signed_tbi = ret_5d × sign(tbi))
               PROMISING-FEATURE-MECHANICAL, DROPPED at /121. C6 is
               composed FIRST-MOMENT. B1 is non-composed SECOND-MOMENT
               cross-asset. Different family.

  iter-v3/088  cross-sectional re-architecture used 22-symbol XS_UNIVERSE
               with lambdarank. /123 keeps per-symbol architecture; only
               adds ONE cross-asset feature to the per-symbol model. Same
               mechanism as /122 setup.

  cycle-7 axis menu — BASELINE_V3.md §"Cycle 7 Axis Priorities" lists
               "HIGH — Cross-asset/external feeds" as the FIRST priority.
               The /122 closure was per-PRIMITIVE not per-FAMILY; the
               broader axis-1 OHLCV cross-asset family stays available
               for /123 with the controlling discipline: must clear
               pairwise IC < 0.40 with the two /122-identified spanning
               incumbents (vwap_dev_20, regime_momentum_signed_5d).

THE FIVE-STEP EDA GATE (mirrors /122 + /119 + /118 methodology with the
/122 closeout pairwise-IC strict gate from Critic Recommendation 1):

  Step 1 — T1: candidate catalog (B1 + 2-3 sister candidates B1a/B1b/B1c).
  Step 2 — T2: Linear Redundancy Pre-Falsifier (joint R² < 0.70 strict +
               PAIRWISE IC < 0.40 with vwap_dev_20 + regime_momentum_signed_5d
               specifically per /122 Critic Rec 1).
  Step 3 — T3 (POOLED) + T4 (per-symbol) univariate walk-forward AUC.
  Step 4 — T5: multivariate (14+1) depth-4 LightGBM importance per symbol.
  Step 5 — T7: multivariate-LIFT screen (14 vs 14+1 OOF AUC, POOLED +
               per-symbol). T9: SSC-RISK gate (the /119-NEW per /118 closeout).
           T6: GO/NO-GO verdict synthesis.

PRE-REGISTERED GO RULE (synthesis script):
  Selection criterion (top candidate emerges):
    - T2 joint R² < 0.70 (the /122 anchor)
    - T2 max-pairwise |IC| with vwap_dev_20 < 0.40 (/122 Critic Rec 1 — STRICT)
    - T2 max-pairwise |IC| with regime_momentum_signed_5d < 0.40 (/122 Critic Rec 1 — STRICT)
    - T7 POOLED lift > +0.003 (the /118 + /119 threshold)
    - T9 SSC-RISK FALSE (broad-based, not single-symbol-carrier)
    - T5 importance allocation non-zero (NOT rank 15/15 with near-zero gain)

  Per THE PRIME DIRECTIVE the EDA NEVER terminates the iteration — a NO-GO
  sharpens the brief's pre-registered failure mode and the backtest still
  runs. The GO/NO-GO verdict only sets the brief's modal prediction and the
  Section-7/8 pre-registration.

NO CHEATING — strict IS-only invariant
--------------------------------------
Every feature/label row entering any computation in THIS module has
close_time < OOS_CUTOFF_MS = 1742774400000 (2025-03-24). The post-cutoff OOS
is NEVER read by any script in analysis/iteration_v3-123/. ETH klines loaded
from `data/ETHUSDT/8h.csv` are fenced at row level to IS only.

The ETH vol-ratio computation uses past-only operators by construction —
`pd.Series.rolling(50, min_periods=50).std()` is canonical past-only
pandas (uses prior 50 bars at each timestamp); the ratio is element-wise
at matched open_time. The same audit that /059 + /122 passed for ETH
log-return features extends to ETH realized-vol features by construction
(identical past-only rolling pattern; only differs in the operator —
.std() vs slicing — at the SAME bar's own returns history).
"""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

REPO_ROOT = Path(__file__).resolve().parents[2]

OOS_CUTOFF_MS = 1742774400000  # 2025-03-24 -- IMMUTABLE
SYMBOLS: tuple[str, ...] = ("BCHUSDT", "LDOUSDT", "TRXUSDT")  # canonical /059 universe

# The /121 14-feature anchor stack — UNCHANGED vs /059 / /121 BASELINE_V3.md.
# (Same as /122 _shared.py — /122 was filed NEGATIVE-INERT; the eth_ret_3d
# feature is NOT in the /123 anchor — the anchor reverts to the 14-feature
# canonical baseline per Critic /122 Rec 1 implicit semantics.)
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
    "vwap_dev_20",  # /122 IC-spanning incumbent (pairwise IC threshold target)
    "ret_autocorr_lag1_50",
    "sym_vs_btc_ret_7d",  # existing symbol-vs-BTC baseline feature
    "regime_momentum_signed_5d",  # /122 IC-spanning incumbent (pairwise IC threshold target)
]

# /122 Critic Rec 1 — explicit IC-target incumbents (strict pairwise gate).
IC_TARGET_INCUMBENTS: tuple[str, ...] = (
    "vwap_dev_20",
    "regime_momentum_signed_5d",
)
IC_TARGET_THRESHOLD: float = 0.40  # strict; /122 closeout Critic Rec 1


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
# ETH cross-asset VOL-REGIME-RATIO features (paralleling cross_btc_v3.py — but
# the computed feature is the RATIO of ETH's own realized vol to the symbol's
# realized vol, not a direct ETH price-return). Past-only by construction:
# .rolling(W, min_periods=W).std() uses ONLY the prior W bars at each
# timestamp. The ratio is element-wise after time-aligned left-join on
# open_time, so a non-empty ETH realized-vol value is required for the bar
# to be valid.
# -----------------------------------------------------------------------------


def _load_eth_klines_raw() -> pd.DataFrame:
    """Load ETH 8h klines (OHLCV, raw)."""
    csv_path = REPO_ROOT / "data" / "ETHUSDT" / "8h.csv"
    df = pd.read_csv(csv_path).sort_values("open_time").reset_index(drop=True)
    return df


def _compute_realized_vol(close: np.ndarray, window: int) -> np.ndarray:
    """Past-only realized vol: rolling std of 1-bar log returns over W bars.

    Matches `multioffset_24h.py:_build_24h_features` which defines
    `range_realized_vol_50 = log_ret_1bar.rolling(50, min_periods=50).std()`.
    Identical past-only convention; the only difference is W is a parameter.
    """
    log_close = np.log(close)
    log_ret_1bar = np.concatenate([[np.nan], np.diff(log_close)])
    vol = pd.Series(log_ret_1bar).rolling(window, min_periods=window).std().to_numpy()
    return vol


def _load_eth_realized_vol_features() -> pd.DataFrame:
    """Compute ETH-derived realized-vol features at multiple windows (cached).

    Adds 3 windows: eth_rv_25 (12.5d at 8h), eth_rv_50 (~16.7d), eth_rv_100 (~33.3d).
    The first window is included as a lookback-variant; the 100 is per the QR
    prompt's B1c sister candidate.
    """
    df = _load_eth_klines_raw()
    close = df["close"].to_numpy(dtype=np.float64)
    df["eth_rv_25"] = _compute_realized_vol(close, window=25)
    df["eth_rv_50"] = _compute_realized_vol(close, window=50)
    df["eth_rv_100"] = _compute_realized_vol(close, window=100)
    return df[["open_time", "eth_rv_25", "eth_rv_50", "eth_rv_100"]].copy()


def _attach_eth_vol_ratio_features(df: pd.DataFrame) -> pd.DataFrame:
    """Merge ETH realized-vol features into a symbol's 8h panel and compute
    ETH-vs-SYMBOL VOL-REGIME-RATIO candidates.

    The 4 candidates:
      B1  = eth_rv_50 / sym_rv_50  — ETH/sym 50-bar vol regime ratio (the PRIMARY)
      B1a = log(eth_rv_50 / sym_rv_50) — same as B1 but log-transformed (sym IC redux)
      B1b = eth_rv_25 / sym_rv_25  — shorter-cadence sister (responsiveness variant)
      B1c = eth_rv_100 / sym_rv_100 — longer-cadence sister (smoothing variant)

    The symbol's realized vol is recomputed locally from the parquet's `close`
    column at the matching windows; the parquet's existing `range_realized_vol_50`
    is the W=50 value (verified parity at this script's _audit_sym_vol_parity).
    """
    out = df.copy()

    # Compute symbol's realized vol at the 3 windows (using close column).
    close_sym = out["close"].to_numpy(dtype=np.float64)
    sym_rv_25 = _compute_realized_vol(close_sym, window=25)
    sym_rv_50 = _compute_realized_vol(close_sym, window=50)
    sym_rv_100 = _compute_realized_vol(close_sym, window=100)
    out["sym_rv_25"] = sym_rv_25
    out["sym_rv_50"] = sym_rv_50
    out["sym_rv_100"] = sym_rv_100

    # Merge ETH realized-vol columns.
    eth = _load_eth_realized_vol_features()
    out = out.merge(eth, on="open_time", how="left")

    # Compute the 4 candidates. Guard divide-by-zero with a tiny epsilon.
    EPS = 1e-12
    out["B1_eth_vs_sym_rv_50"] = out["eth_rv_50"] / (out["sym_rv_50"] + EPS)
    out["B1a_log_eth_vs_sym_rv_50"] = np.log(
        np.maximum(out["eth_rv_50"], EPS) / np.maximum(out["sym_rv_50"], EPS)
    )
    out["B1b_eth_vs_sym_rv_25"] = out["eth_rv_25"] / (out["sym_rv_25"] + EPS)
    out["B1c_eth_vs_sym_rv_100"] = out["eth_rv_100"] / (out["sym_rv_100"] + EPS)

    # Drop intermediates to keep panel clean.
    out = out.drop(
        columns=[c for c in ["eth_rv_25", "eth_rv_50", "eth_rv_100",
                              "sym_rv_25", "sym_rv_50", "sym_rv_100"]
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
    "B1_eth_vs_sym_rv_50",
    "B1a_log_eth_vs_sym_rv_50",
    "B1b_eth_vs_sym_rv_25",
    "B1c_eth_vs_sym_rv_100",
)

# The PRIMARY candidate per the QR prompt — B1 is the lead.
PRIMARY_CANDIDATE: str = "B1_eth_vs_sym_rv_50"

CANDIDATE_CATEGORY: dict[str, str] = {
    "B1_eth_vs_sym_rv_50": "(v) cross-asset ETH/sym vol-regime ratio (PRIMARY)",
    "B1a_log_eth_vs_sym_rv_50": "(v) cross-asset ETH/sym log-vol-ratio (sister: scale-symmetric)",
    "B1b_eth_vs_sym_rv_25": "(v) cross-asset ETH/sym vol-ratio shorter-cadence (sister: W=25)",
    "B1c_eth_vs_sym_rv_100": "(v) cross-asset ETH/sym vol-ratio longer-cadence (sister: W=100)",
}

CANDIDATE_MOTIVATION: dict[str, str] = {
    "B1_eth_vs_sym_rv_50": (
        "ETH 50-bar realized vol divided by symbol's own 50-bar realized vol. "
        "When ETH's vol regime is elevated relative to the symbol's own vol, "
        "this indicates risk-on cross-asset regime where alt idiosyncratic moves "
        "are conditioned by ETH-led volatility (the symmetric mate to the BTC-led "
        "vol regime feature family). Past-only by construction (rolling std with "
        "min_periods=50). PRIMARY candidate per the QR prompt; non-IC-spanned by "
        "vwap_dev_20 (first-moment price deviation) and regime_momentum_signed_5d "
        "(first-moment momentum composed feature) per the /122 closeout Critic "
        "Recommendation 1."
    ),
    "B1a_log_eth_vs_sym_rv_50": (
        "Log of B1 (eth_rv_50 / sym_rv_50). The log transform makes the ratio "
        "symmetric around 0 (when eth_rv = sym_rv, log = 0; positive when ETH "
        "dominates, negative when symbol dominates). The unsmoothed ratio (B1) "
        "is heavily right-skewed; the log transform may produce a more "
        "tree-friendly distribution for LightGBM's split capacity."
    ),
    "B1b_eth_vs_sym_rv_25": (
        "Shorter-cadence (25-bar = 8.3-day) sister to B1. Tradeoff: more "
        "responsive to recent regime shifts but noisier; window aligns with "
        "the /025 5-day cohort cadence."
    ),
    "B1c_eth_vs_sym_rv_100": (
        "Longer-cadence (100-bar = 33.3-day) sister to B1. Tradeoff: smoother "
        "regime classifier but slower to respond to shifts; aligns with the "
        "hurst_100 / hurst_diff_100_50 anchor regime indicator cadence."
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
    """Load symbol's 8h features, label, attach ETH-vs-sym vol-ratio candidates. IS-only fenced."""
    df = load_features_is(symbol)
    df = label_triple_barrier(df)
    df = _attach_eth_vol_ratio_features(df)
    feat_cols = list(V3_FEATURE_COLUMNS) + list(CANDIDATE_NAMES)
    keep_cols = ["open_time", "close_time", "close", "label", "label_valid"] + feat_cols
    keep_cols = [c for c in keep_cols if c in df.columns]
    df = df[keep_cols].copy()
    # Filter to valid-label rows where all 14 baseline + 4 candidates are non-NaN.
    keep = df["label_valid"] & df[feat_cols].notna().all(axis=1)
    df = df[keep].reset_index(drop=True)
    df["symbol"] = symbol
    return df
