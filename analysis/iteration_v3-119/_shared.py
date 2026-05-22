"""iter-v3/119 — NEW engineered-feature axis EDA (cycle-6 EXPLORATION #10 — FINAL).

The axis under test (per `feedback_v3_axis_selection_quant_discipline.md` + the
/118 closeout Recommendation 1 + Critic Recommendation 1):

    Does adding a NEW composed feature on a STRUCTURALLY DIFFERENT regime
    classifier (NOT vol-regime, NOT /025 hurst-regime, NOT funding-rate,
    NOT taker-buy-ratio) carry incremental directional signal beyond the
    14-feature BASELINE_V3 stack on the BCH/LDO/TRX 8h cohort?

Cycle-6 catalog state at /118 closeout:
  /110 NEGATIVE | /111 NEGATIVE | /112 NEGATIVE | /113 NEGATIVE
  /114 NEGATIVE (Check-1 FAIL) | /115 NEGATIVE | /116 PROMISING-MECHANICAL
  /117 NEGATIVE catastrophic (candle-frequency CLOSED) | /118 NEGATIVE
  catastrophic (`value × sign(vol-regime-classifier)` Category-2 CLOSED).

Closure-scope EXCLUSIONS for /119:
  - NO `sign(realized_vol − vol_threshold)` regime sign factor (per /118 broader
    closure on `value × sign(vol-regime-classifier)` Category-2 lineage).
  - NO `/025` hurst-regime retry (occupied by `regime_momentum_signed_5d`).
  - NO `funding_rate_*` / `btc_funding_rate_*` (cycle-3 dead branch:
    /019/023/024/082 ALL INERT).
  - NO `tbr_zscore_30` retry (cycle-2 dead, /015 INERT-by-importance + /085
    closeout ban).
  - NO `ema_spread_atr_20 × sign(ret_kurt_50 − rolling_median_200)` retry —
    REUSES /118 failed-C3 value primitive `ema_spread_atr_20` with the same
    rolling-median technique; a borderline-sister-of-/118 case which we EXCLUDE
    on lineage discipline.

Recommendation framing (the /118 closeout QR's option (a) + the orchestrator's
Category-(i)/(iii) prompt): a composite of the form

    composite_X = primitive_A * sign(primitive_B - threshold)

where:
- primitive_A is a value-encoding feature OUTSIDE the `ema_spread` lineage that
  /118 closed, AND
- primitive_B is a regime-classifying feature OUTSIDE the vol-regime,
  hurst-regime, funding-rate, and taker-buy-ratio lineages.

The /025 precedent (regime_momentum_signed_5d = ret_5d * sign(hurst_100 - 0.5))
is the design template: IS +0.50 / OOS +0.84 vs anchor; importance 51% top
vs 22-25% off-the-shelf. KEPT in V3_FEATURE_COLUMNS since /028 CONFIRMATION-MERGE.
The /118 failure was the vol-regime variant of /025 — same algebraic form,
different regime classifier (vol vs hurst) → catastrophic IS Δ = −0.4543.

Six candidate composites evaluated (T1), split across the prompt's two
categories:

CATEGORY (i) — VOLUME-BASED PRIMITIVES (the highest-priority axis per /118
closeout Section 8.1 + orchestrator's prompt):

  C1 = obv_slope_50 × sign(volume_mom_ratio_20 - 1.0)
       — OBV slope conditioned on volume-momentum regime; encodes "I am in
         a high-volume-momentum regime → OBV trend signal becomes stronger".
         primitive_A = obv_slope_50 (cumulative-volume slope; orthogonal to
         price-momentum primitives). primitive_B = volume_mom_ratio_20
         (10-bar / 50-bar volume ratio; threshold = 1.0 = volume mean-revert
         boundary). NEW lineage — neither primitive appears in V3_FEATURE_COLUMNS.

  C2 = vwap_dev_20 × sign(volume_cv_50 - rolling_median_200)
       — VWAP mean-reversion conditioned on volume-dispersion regime; encodes
         "I am in a high-volume-dispersion (regime change) period → VWAP-rev
         signal STRONGER/WEAKER depending on volume coherence".
         primitive_A = vwap_dev_20 (in TOP_N — value primitive). primitive_B =
         volume_cv_50 (volume coefficient of variation; orthogonal to vol-regime
         realized vol). The rolling-median technique is REUSED from /118 but
         on a DIFFERENT classifier (volume CV vs realized vol). EXPLICIT
         declaration in brief Section 0.5 — this counts as a fresh lineage
         because volume CV is NOT a vol-regime variant (it's a SECOND-MOMENT
         OF VOLUME, not of returns).

CATEGORY (iii) — TAIL / HIGHER-MOMENT REGIME CLASSIFIERS (the orthogonal
candidate per /118 closeout Section 8.1):

  C3 = ret_5d × sign(ret_skew_50)
       — 5-day return conditioned on return-skew sign; encodes "I am in a
         positively-skewed regime (right-tail dominant) → momentum signal
         STRONGER; left-skewed regime → momentum FADES".
         primitive_A = ret_5d (the /025 value primitive — but conditioned by
         a DIFFERENT regime classifier from hurst; not a /025-occupied lineage).
         primitive_B = ret_skew_50 (in TOP_N as a primitive). Algebraic form
         is identical to /025 (ret_5d × sign(...)) but the REGIME CLASSIFIER
         is FUNDAMENTALLY DIFFERENT — skew is a tail/asymmetry property; hurst
         is a long-memory property.

  C4 = sym_vs_btc_ret_7d × sign(ret_kurt_50 - 0)
       — symbol-vs-BTC divergence conditioned on tail-regime sign; encodes
         "I am in a heavy-tail regime → cross-asset signal STRONGER (fat-tail
         events propagate); thin-tail regime → cross-asset signal FADES".
         primitive_A = sym_vs_btc_ret_7d (in TOP_N — cross-asset value
         primitive). primitive_B = ret_kurt_50 (in TOP_N as a primitive).
         The threshold = 0 is the natural cut for excess kurtosis (positive
         = leptokurtic = heavy tail). NOTE: /118 evaluated a similar C6 form
         (vwap_dev_20 × sign(ret_kurt_50 - 0)) which FAILED at T3 (POOLED
         AUC 0.4942, p=0.86). /119 C4 substitutes the value primitive from
         vwap_dev_20 → sym_vs_btc_ret_7d on the grounds that sym_vs_btc is
         a DIFFERENT lineage (cross-asset, not symbol-internal mean-reversion).

  C5 = max_dd_window_50 × sign(ret_skew_200 - 0)
       — drawdown magnitude conditioned on long-horizon skew regime; encodes
         "I am in a long-skew-positive regime → drawdown magnitude predicts
         BOUNCE STRENGTH; long-skew-negative → drawdown predicts FURTHER
         FALL". primitive_A = max_dd_window_50 (in TOP_N). primitive_B =
         ret_skew_200 (in TOP_N). Lineage: NEW — drawdown is a path-property
         primitive, skew is an asymmetry primitive. Threshold = 0 (natural
         skew zero-cross).

CATEGORY (iv) — MICROSTRUCTURE PROXY (single representative for breadth):

  C6 = ret_5d × sign(taker_buy_imbalance_20)
       — 5-day momentum conditioned on order-flow regime; encodes "I am in
         a buy-imbalanced regime → momentum is BUY-CONFIRMED; sell-imbalanced
         → momentum is SUSPECT". primitive_A = ret_5d (the /025 value
         primitive). primitive_B = taker_buy_imbalance_20 (microstructure;
         NOT in TOP_N, NOT in dead-paths list). NOTE: tbr_zscore_30 (the
         /015 NEGATIVE TBR-derived feature) is on the banned-list, but
         taker_buy_imbalance_20 is a DIFFERENT primitive (raw imbalance, not
         z-scored ratio) — eligible as fresh lineage. Threshold = 0 (natural
         imbalance zero-cross).

Linear Redundancy Pre-Falsifier per `feedback_v3_lr_pf_methodology.md`:
- composed-feature carve-out applies (R²>0.50 acceptable when the candidate
  is composed of primitives by construction). PRIMARY falsifier is Sharpe-Δ
  NOT importance rank at the production stage (post-EDA). At EDA stage, AUC
  is the primary discriminator (per /109 / /117 / /118 methodology); per-
  symbol AUC is the /117 g1 hard gate; importance rank is the /025 secondary
  benchmark.

NEW Single-Symbol-Carrier RISK pre-Falsifier (per /118 closeout Critic Rec 1 +
QR Clarification 3, ESTABLISHED at /119):
- For each candidate, compute the per-symbol multivariate-lift signature (T7).
- If single-symbol max-|lift| > 2 × POOLED |lift| magnitude, flag as
  SSC-RISK and tighten Section-4 falsifier band.
- /118 prospectively had SSC ratio ~1.01× (TRX +0.0082 vs POOLED +0.0081) —
  the 2× threshold would have caught it (modulo orientation).
- For /119, the gate fires if ANY symbol's |lift| exceeds 2 × |POOLED lift|.

NO CHEATING — strict IS-only invariant
--------------------------------------
Every feature/label row entering any computation has close_time < OOS_CUTOFF_MS
= 1742774400000 (2025-03-24). The post-cutoff OOS is NEVER read.
"""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

REPO_ROOT = Path(__file__).resolve().parents[2]

OOS_CUTOFF_MS = 1742774400000  # 2025-03-24 -- IMMUTABLE
SYMBOLS: tuple[str, ...] = ("BCHUSDT", "LDOUSDT", "TRXUSDT")  # canonical /059 universe

# The /059 14-feature anchor stack (CANONICAL post-/059 since /028 CONFIRMATION-MERGE).
V3_FEATURE_COLUMNS: list[str] = [
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

# Triple-barrier label config (faithful to /059).
ATR_TP_MULT = 2.0
ATR_SL_MULT = 1.0
ATR_COL = "natr_21_raw"
TIMEOUT_BARS = 21  # 21 x 8h = 168h horizon — the /059 canonical timeout
FEE_PCT = 0.1

# Walk-forward fold geometry.
N_FOLDS_DEFAULT = 5
EMBARGO_BARS = 22  # /059 walk-forward embargo at the 8h timescale


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
# Candidate composite features (C1..C6)
# -----------------------------------------------------------------------------

EPS = 1e-12


def _rolling_median_past_only(x: np.ndarray, window: int) -> np.ndarray:
    return pd.Series(x).rolling(window, min_periods=window).median().to_numpy()


def _rolling_quantile_past_only(x: np.ndarray, window: int, q: float) -> np.ndarray:
    return pd.Series(x).rolling(window, min_periods=window).quantile(q).to_numpy()


def compute_candidates(df: pd.DataFrame) -> pd.DataFrame:
    """Compute the 6 candidate composites on a symbol's 8h-feature panel.

    All composites are STRICTLY past-only — they read only existing same-row
    feature columns whose values were computed past-only by the features_v3
    pipeline (verified at /059 / /060 audit, and any new rolling stats are
    computed past-only here).
    """
    d = df.copy()
    # Primitive aliases (existing in parquet).
    close = d["close"].to_numpy(dtype="float64")
    log_close = np.log(np.clip(close, 1e-12, None))
    # ret_5d = 15 8h bars = 120h = 5 calendar days
    ret_5d = log_close - pd.Series(log_close).shift(15).to_numpy(dtype="float64")

    obv_slope = d["obv_slope_50"].to_numpy(dtype="float64")
    vol_mom = d["volume_mom_ratio_20"].to_numpy(dtype="float64")
    vwap = d["vwap_dev_20"].to_numpy(dtype="float64")
    vol_cv = d["volume_cv_50"].to_numpy(dtype="float64")
    skew50 = d["ret_skew_50"].to_numpy(dtype="float64")
    skew200 = d["ret_skew_200"].to_numpy(dtype="float64")
    kurt50 = d["ret_kurt_50"].to_numpy(dtype="float64")
    sym_vs_btc = d["sym_vs_btc_ret_7d"].to_numpy(dtype="float64")
    maxdd = d["max_dd_window_50"].to_numpy(dtype="float64")
    tbi = d["taker_buy_imbalance_20"].to_numpy(dtype="float64")

    # Sign helpers (NaN-preserving).
    def _sign(x: np.ndarray, threshold: float) -> np.ndarray:
        out = np.full_like(x, np.nan, dtype="float64")
        mask = ~np.isnan(x)
        out[mask] = np.where(x[mask] > threshold, 1.0, -1.0)
        return out

    # Volume CV rolling-200 median (past-only).
    vol_cv_med200 = _rolling_median_past_only(vol_cv, 200)

    # CATEGORY (i) — VOLUME-BASED PRIMITIVES
    d["C1_obv_signed_volmom"] = obv_slope * _sign(vol_mom, 1.0)
    d["C2_vwap_signed_volcv"] = vwap * _sign(vol_cv - vol_cv_med200, 0.0)

    # CATEGORY (iii) — TAIL / HIGHER-MOMENT REGIME
    d["C3_ret5d_signed_skew50"] = ret_5d * _sign(skew50, 0.0)
    d["C4_symvsbtc_signed_kurt50"] = sym_vs_btc * _sign(kurt50, 0.0)
    d["C5_maxdd_signed_skew200"] = maxdd * _sign(skew200, 0.0)

    # CATEGORY (iv) — MICROSTRUCTURE PROXY
    d["C6_ret5d_signed_tbi"] = ret_5d * _sign(tbi, 0.0)

    return d


CANDIDATE_NAMES: tuple[str, ...] = (
    "C1_obv_signed_volmom",
    "C2_vwap_signed_volcv",
    "C3_ret5d_signed_skew50",
    "C4_symvsbtc_signed_kurt50",
    "C5_maxdd_signed_skew200",
    "C6_ret5d_signed_tbi",
)

# Cycle category mapping for T1 catalog
CANDIDATE_CATEGORY: dict[str, str] = {
    "C1_obv_signed_volmom": "(i) volume",
    "C2_vwap_signed_volcv": "(i) volume",
    "C3_ret5d_signed_skew50": "(iii) tail",
    "C4_symvsbtc_signed_kurt50": "(iii) tail",
    "C5_maxdd_signed_skew200": "(iii) tail",
    "C6_ret5d_signed_tbi": "(iv) microstructure",
}

# T1 motivations (single-line; full text in T1_candidate_catalog.csv)
CANDIDATE_MOTIVATION: dict[str, str] = {
    "C1_obv_signed_volmom": (
        "OBV slope conditioned on volume-momentum regime. primitive_A=obv_slope_50 "
        "(orthogonal to price). primitive_B=volume_mom_ratio_20 threshold=1.0. "
        "NEW lineage — neither primitive in V3_FEATURE_COLUMNS."
    ),
    "C2_vwap_signed_volcv": (
        "VWAP mean-reversion × volume-dispersion regime. primitive_A=vwap_dev_20. "
        "primitive_B=volume_cv_50 (NOT realized vol — second moment OF VOLUME). "
        "Rolling-median technique REUSED from /118 on DIFFERENT classifier."
    ),
    "C3_ret5d_signed_skew50": (
        "5-day return × skew-sign. primitive_A=ret_5d. primitive_B=ret_skew_50. "
        "Algebraic form ~ /025 but regime classifier FUNDAMENTALLY DIFFERENT "
        "(tail/asymmetry, not long-memory)."
    ),
    "C4_symvsbtc_signed_kurt50": (
        "Cross-asset divergence × tail-regime. primitive_A=sym_vs_btc_ret_7d. "
        "primitive_B=ret_kurt_50 threshold=0 (excess-kurtosis natural cut). "
        "NOTE: substitutes value primitive vs /118 C6 fail (vwap × kurt)."
    ),
    "C5_maxdd_signed_skew200": (
        "Drawdown magnitude × long-horizon skew regime. primitive_A=max_dd_window_50. "
        "primitive_B=ret_skew_200. NEW lineage — drawdown is path-property; skew "
        "is asymmetry; both in TOP_N as primitives but never composed."
    ),
    "C6_ret5d_signed_tbi": (
        "5-day momentum × order-flow regime. primitive_A=ret_5d. "
        "primitive_B=taker_buy_imbalance_20 (NOT tbr_zscore_30; raw imbalance — "
        "different primitive from /015 NEGATIVE TBR-derived feature)."
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
    """Load symbol's 8h features, label, add 6 candidates. IS-only fenced."""
    df = load_features_is(symbol)
    df = label_triple_barrier(df)
    df = compute_candidates(df)
    feat_cols = list(V3_FEATURE_COLUMNS) + list(CANDIDATE_NAMES)
    keep_cols = ["open_time", "close_time", "close", "label", "label_valid"] + feat_cols
    keep_cols = [c for c in keep_cols if c in df.columns]
    df = df[keep_cols].copy()
    # Filter to valid-label rows where all 14 baseline + 6 candidates are non-NaN.
    keep = df["label_valid"] & df[feat_cols].notna().all(axis=1)
    df = df[keep].reset_index(drop=True)
    df["symbol"] = symbol
    return df
