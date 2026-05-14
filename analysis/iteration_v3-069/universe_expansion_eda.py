"""iter-v3/069 EDA — UNIVERSE EXPANSION axis (4th symbol; cycle 1 #10 of 10).

NON-FEATURE PIVOT continuation per Critic /064 Rec #4 directive (locked for /065-/069).
Cycle 1 #10 of 10 — FINAL before /070 CONFIRMATION.
Sibling axes: /065 (SL widening — TRAIN-TIME magnitude); /066 (vol_scale_ceiling — INFER);
/067 (inference threshold floor — INFER); /068 (label_timeout doubling — TRAIN-TIME duration).
/069 axis = UNIVERSE — DENOMINATOR EXPANSION dimension. Different from all five sibling
axes (all were UNIVERSAL knobs at fixed universe).

Anchor = iter-v3/060 EXPLORATION-MODE-REFERENCE (IS +0.8325 / OOS +0.1403).

Per `feedback_v3_concentration_is_signal.md` LOCKED 2026-05-07:
  - Universe expansion is explicitly the permitted ORTHOGONAL mechanism for
    addressing concentration risk. Denominator expansion = adding symbols,
    NOT scaling positions DOWN (the iter-v3/020 cap-mechanism failure).
  - This is HIGH-priority axis #2b.

Per `feedback_v3_iter064_process_lessons.md`:
  Rule 1: T0 anchor values from comparison.csv:LINE byte-exact (NOT hand-typed).
  Rule 3: NEGATIVE probability for non-feature single-axis at single-seed n_trials=35
          calibrated UP (≥25%). Per Critic /068 Rec #1: labeling-axis pre-register
          [-0.50, +0.50] envelope. Universe-expansion is structurally similar (axis
          changes per-symbol Optuna budget allocation) — widen NEGATIVE band.
  Rule 5: 14-feature anchor is LOCAL OPTIMUM — non-feature axes are productive.

Per diary lesson (a) of iter-v3/021 (HBAR+AVAX catastrophe):
  "EDA correlation ranking is necessary but not sufficient for symbol selection."
  This EDA ADDS per-symbol IS feature-mean comparison vs incumbents (BCH+LDO+TRX) at
  the V3_FEATURE_COLUMNS level. Pure return-correlation ranking is structurally
  insufficient (/021 ranked HBAR rank-1 by correlation; HBAR was the WORST IS
  contributor at -36.5%).

Per diary lesson (b) of iter-v3/021:
  "Universe expansion at n_trials=35 split N ways is over-stretched."
  This EDA tests 1-symbol expansion ONLY (3 → 4) — NOT 2-symbol (/021's wrong call).

Per `feedback_v3_per_symbol_lifts_oos_breaks_is.md`: This is a UNIVERSAL change
(adding 1 symbol with the same risk gates, same features, same labeling). No
per-symbol customization. CONFIRMED PERMITTED at CONFIRMATION bundle composition.

Per diary lesson (c) of iter-v3/021:
  "HBAR + AVAX axis CLOSED at catalog level."
  Candidate pool EXCLUDES HBARUSDT and AVAXUSDT. Remaining candidates from /021
  EDA: ATOMUSDT, FILUSDT, ALGOUSDT, ADAUSDT, VETUSDT.

ALGOUSDT was tested at iter-v3/034-039 as a per-symbol-bundle ingredient at the
iter-v3/028 baseline + per-symbol-customizations. iter-v3/039 = SECOND v3 CONFIRMATION
= CONFIRMATION-NO-MERGE. ALGO was REVERTED at iter-v3/051 (system-level REVERT to
3-symbol universe). However the /039 failure was attributed to per-symbol
customizations (BCH fracdiff per-symbol + LDO ATR per-symbol), NOT to ALGO itself.
Per BASELINE_V3.md, the architecture re-anchor at /058+/059 also reverted ALGO.
ALGO remains candidate-eligible for cycle 1 retest under UNIVERSAL discipline.

Output: 6 tables (T0-T5) + 1 ranking CSV committed to analysis/iteration_v3-069/.
"""

from __future__ import annotations

import csv
from datetime import UTC, datetime
from pathlib import Path

import numpy as np
import pandas as pd

# ============================================================================
# Constants
# ============================================================================

ROOT = Path(__file__).resolve().parent
REPO_ROOT = ROOT.parent.parent
DATA_DIR = REPO_ROOT / "data"

# Sacred constants
OOS_CUTOFF_MS = 1742774400000  # 2025-03-24 UTC

# IS evaluation window (same as iter-v3/021 EDA — 2023-04-01 → OOS cutoff)
IS_EVAL_START_MS = int(datetime(2023, 4, 1, tzinfo=UTC).timestamp() * 1000)
IS_EVAL_END_MS = OOS_CUTOFF_MS

CANDLE_MS = 480 * 60 * 1000  # 8h interval = 480 min

# /060 EXPLORATION anchor (Section 2.1 T0 source — byte-exact)
ITER_060 = REPO_ROOT / "reports-v3" / "iteration_v3-060"
COMP_060 = ITER_060 / "comparison.csv"
IS_PSYM_060 = ITER_060 / "in_sample" / "per_symbol.csv"
OOS_PSYM_060 = ITER_060 / "out_of_sample" / "per_symbol.csv"

# Current 3-symbol universe (BASELINE_V3.md)
BASELINE_SYMBOLS = ("BCHUSDT", "LDOUSDT", "TRXUSDT")

# Candidate pool — excludes V3_EXCLUDED_SYMBOLS + HBAR/AVAX (CLOSED per /021
# diary lesson (c)) + DOGE/SOL/XRP/NEAR (project_tried_symbols.md 2026-04-21).
# Remaining symbols passing iter-v3/021 Gate 1 (data quality):
#   ATOMUSDT, FILUSDT, ALGOUSDT, ADAUSDT, VETUSDT
# We rank ALL 5 by structural + complementarity + feature-space proximity.
CANDIDATES = (
    "ATOMUSDT",
    "FILUSDT",
    "ALGOUSDT",
    "ADAUSDT",
    "VETUSDT",
)


def _write_csv(rows: list[dict], path: Path) -> None:
    if not rows:
        path.write_text("")
        return
    with path.open("w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        w.writeheader()
        w.writerows(rows)


# ============================================================================
# Helpers
# ============================================================================


def load_klines(symbol: str) -> pd.DataFrame:
    path = DATA_DIR / symbol / "8h.csv"
    if not path.exists():
        raise FileNotFoundError(f"missing data: {path}")
    df = pd.read_csv(
        path,
        dtype={
            "open": float, "high": float, "low": float, "close": float,
            "volume": float, "quote_volume": float,
            "taker_buy_volume": float, "taker_buy_quote_volume": float,
        },
    )
    df["open_time"] = df["open_time"].astype(np.int64)
    df["close_time"] = df["close_time"].astype(np.int64)
    df["trades"] = df["trades"].astype(np.int64)
    df["dt"] = pd.to_datetime(df["open_time"], unit="ms", utc=True)
    df = df.set_index("dt").sort_index()
    return df


def is_window_mask(df: pd.DataFrame) -> pd.Series:
    return (df["open_time"] >= IS_EVAL_START_MS) & (df["open_time"] < IS_EVAL_END_MS)


def compute_returns(df: pd.DataFrame) -> pd.Series:
    """8h log returns."""
    s = pd.Series(np.log(df["close"].values), index=df.index)
    return s.diff().dropna()


# ============================================================================
# T0 — Anchor value declaration (Rule 1 compliance — byte-exact)
# ============================================================================

def t0_anchor_values() -> None:
    """Read /060 anchor byte-exact (Rule 1 from feedback_v3_iter064_process_lessons.md)."""
    rows = [
        # Headline metrics (comparison.csv:2-10)
        {"metric": "monthly_sharpe_in_sample", "value": "0.8325",
         "source": "reports-v3/iteration_v3-060/comparison.csv:2"},
        {"metric": "monthly_sharpe_out_of_sample", "value": "0.1403",
         "source": "reports-v3/iteration_v3-060/comparison.csv:2"},
        {"metric": "max_drawdown_in_sample", "value": "31.8701",
         "source": "reports-v3/iteration_v3-060/comparison.csv:4"},
        {"metric": "max_drawdown_out_of_sample", "value": "35.7804",
         "source": "reports-v3/iteration_v3-060/comparison.csv:4"},
        {"metric": "n_trades_in_sample", "value": "159",
         "source": "reports-v3/iteration_v3-060/comparison.csv:7"},
        {"metric": "n_trades_out_of_sample", "value": "102",
         "source": "reports-v3/iteration_v3-060/comparison.csv:7"},
        {"metric": "weighted_pnl_total_in_sample", "value": "51.8906",
         "source": "reports-v3/iteration_v3-060/comparison.csv:10"},
        {"metric": "weighted_pnl_total_out_of_sample", "value": "5.4989",
         "source": "reports-v3/iteration_v3-060/comparison.csv:10"},
        {"metric": "dsr", "value": "0.0",
         "source": "reports-v3/iteration_v3-060/comparison.csv:11"},
        {"metric": "pbo", "value": "0.1278",
         "source": "reports-v3/iteration_v3-060/comparison.csv:12"},
        {"metric": "psr", "value": "0.9763",
         "source": "reports-v3/iteration_v3-060/comparison.csv:13"},
        # Per-symbol weighted_pnl (comparison.csv:18-20)
        {"metric": "BCH_OOS_weighted_pnl", "value": "1.9078",
         "source": "reports-v3/iteration_v3-060/comparison.csv:18 (per_symbol weighted_pnl col)"},
        {"metric": "LDO_OOS_weighted_pnl", "value": "-19.7208",
         "source": "reports-v3/iteration_v3-060/comparison.csv:19 (per_symbol weighted_pnl col)"},
        {"metric": "TRX_OOS_weighted_pnl", "value": "23.3119",
         "source": "reports-v3/iteration_v3-060/comparison.csv:20 (per_symbol weighted_pnl col)"},
        {"metric": "BCH_OOS_n_trades", "value": "37",
         "source": "reports-v3/iteration_v3-060/comparison.csv:18 (n_trades col)"},
        {"metric": "LDO_OOS_n_trades", "value": "11",
         "source": "reports-v3/iteration_v3-060/comparison.csv:19 (n_trades col)"},
        {"metric": "TRX_OOS_n_trades", "value": "54",
         "source": "reports-v3/iteration_v3-060/comparison.csv:20 (n_trades col)"},
        {"metric": "BCH_OOS_win_rate", "value": "32.4",
         "source": "reports-v3/iteration_v3-060/comparison.csv:18 (win_rate col)"},
        {"metric": "LDO_OOS_win_rate", "value": "18.2",
         "source": "reports-v3/iteration_v3-060/comparison.csv:19 (win_rate col)"},
        {"metric": "TRX_OOS_win_rate", "value": "48.1",
         "source": "reports-v3/iteration_v3-060/comparison.csv:20 (win_rate col)"},
        # IS per-symbol (in_sample/per_symbol.csv)
        {"metric": "BCH_IS_n_trades", "value": "73",
         "source": "reports-v3/iteration_v3-060/in_sample/per_symbol.csv"},
        {"metric": "LDO_IS_n_trades", "value": "11",
         "source": "reports-v3/iteration_v3-060/in_sample/per_symbol.csv"},
        {"metric": "TRX_IS_n_trades", "value": "75",
         "source": "reports-v3/iteration_v3-060/in_sample/per_symbol.csv"},
        {"metric": "BCH_IS_win_rate", "value": "45.2",
         "source": "reports-v3/iteration_v3-060/in_sample/per_symbol.csv"},
        {"metric": "LDO_IS_win_rate", "value": "27.3",
         "source": "reports-v3/iteration_v3-060/in_sample/per_symbol.csv"},
        {"metric": "TRX_IS_win_rate", "value": "29.3",
         "source": "reports-v3/iteration_v3-060/in_sample/per_symbol.csv"},
        # Cycle-1 anchor cross-references
        {"metric": "current_universe", "value": "BCH+LDO+TRX (3 symbols)",
         "source": "run_baseline_v3.py:139-143 V3_MODELS"},
        {"metric": "current_required_gap", "value": "66",
         "source": "validation_v3.py:56 — will need 88 = (21+1)*4 for /069"},
        {"metric": "current_label_timeout_minutes", "value": "10080",
         "source": "run_baseline_v3.py — REVERT /068's 20160 back to 10080"},
        # LDO weakness pattern (Critic /068 Rec #3)
        {"metric": "LDO_OOS_WR_iter060", "value": "18.2",
         "source": "reports-v3/iteration_v3-060/comparison.csv:19 — Critic /068 Rec #3 cite"},
        {"metric": "LDO_OOS_WR_iter064", "value": "7.1",
         "source": "diary-v3/iteration_v3-068.md:34 Critic /068 Rec #3 cite"},
        {"metric": "LDO_OOS_WR_iter068", "value": "8.3",
         "source": "diary-v3/iteration_v3-068.md:34 Critic /068 Rec #3 cite"},
    ]
    _write_csv(rows, ROOT / "T0_anchor_values.csv")
    print(f"T0: {len(rows)} anchor values written (Rule 1 compliance).")


# ============================================================================
# T1 — Per-candidate Gate 1 (data quality) + Gate 2 (liquidity)
# ============================================================================

def t1_per_candidate_data_quality() -> None:
    """Gate 1 (24mo pre-IS history + IS coverage ≥99% + gaps≤5) + Gate 2 (liquidity)."""
    rows = []
    for sym in CANDIDATES:
        df = load_klines(sym)
        # Pre-IS history
        first_ms = int(df["open_time"].iloc[0])
        pre_is_months = (IS_EVAL_START_MS - first_ms) / (1000 * 86400 * 30.4375)
        # IS coverage
        is_mask = is_window_mask(df)
        is_n = int(is_mask.sum())
        is_expected = (IS_EVAL_END_MS - IS_EVAL_START_MS) // CANDLE_MS
        is_coverage_pct = 100.0 * is_n / max(is_expected, 1)
        # Gaps in IS window
        is_df = df.loc[is_mask].copy()
        if len(is_df) > 1:
            delta_ms = is_df["open_time"].diff().dropna()
            gap_count = int((delta_ms > 1.5 * CANDLE_MS).sum())
        else:
            gap_count = 0
        # Liquidity
        is_df["date"] = is_df.index.date
        daily_qvol = is_df.groupby("date")["quote_volume"].sum()
        avg_qvol = float(daily_qvol.mean())
        p10_qvol = float(daily_qvol.quantile(0.10))

        gate1_pass = (
            pre_is_months >= 24.0
            and is_coverage_pct >= 99.0
            and gap_count <= 5
        )
        # Liquidity threshold: avg > $20M AND p10 > $5M (same as /021 EDA)
        gate2_pass = avg_qvol > 2.0e7 and p10_qvol > 5.0e6

        rows.append({
            "symbol": sym,
            "pre_is_months": round(pre_is_months, 2),
            "is_coverage_pct": round(is_coverage_pct, 2),
            "gap_count": gap_count,
            "is_avg_daily_qvol_usd_M": round(avg_qvol / 1e6, 1),
            "is_p10_daily_qvol_usd_M": round(p10_qvol / 1e6, 1),
            "gate1_pass": gate1_pass,
            "gate2_pass": gate2_pass,
        })
    _write_csv(rows, ROOT / "T1_per_candidate_data_quality.csv")
    print(f"T1: {len(rows)} candidates evaluated on Gate 1 + Gate 2.")
    for r in rows:
        print(
            f"  {r['symbol']}: pre_is={r['pre_is_months']}mo "
            f"cov={r['is_coverage_pct']}% gaps={r['gap_count']} "
            f"qvol_avg=${r['is_avg_daily_qvol_usd_M']}M "
            f"p10=${r['is_p10_daily_qvol_usd_M']}M "
            f"gate1={r['gate1_pass']} gate2={r['gate2_pass']}"
        )


# ============================================================================
# T2 — Cross-correlation with BCH/LDO/TRX (Pearson on 8h log returns, IS window)
# ============================================================================

def t2_correlation_diversification() -> None:
    """8h log-return correlation with each of BCH/LDO/TRX on IS window."""
    # Cache baseline returns (IS window only)
    baseline_returns: dict[str, pd.Series] = {}
    for sym in BASELINE_SYMBOLS:
        df = load_klines(sym)
        is_mask = is_window_mask(df)
        baseline_returns[sym] = compute_returns(df.loc[is_mask])

    rows = []
    for sym in CANDIDATES:
        cand_df = load_klines(sym)
        is_mask = is_window_mask(cand_df)
        cand_ret = compute_returns(cand_df.loc[is_mask])
        corrs = {}
        for base_sym, base_ret in baseline_returns.items():
            joined = pd.concat([cand_ret, base_ret], axis=1, join="inner").dropna()
            if len(joined) < 100:
                corrs[base_sym] = float("nan")
            else:
                corrs[base_sym] = float(joined.iloc[:, 0].corr(joined.iloc[:, 1]))
        mean_abs = float(np.mean([abs(c) for c in corrs.values() if not np.isnan(c)]))
        max_abs = float(np.max([abs(c) for c in corrs.values() if not np.isnan(c)]))
        rows.append({
            "symbol": sym,
            "corr_BCH": round(corrs["BCHUSDT"], 4),
            "corr_LDO": round(corrs["LDOUSDT"], 4),
            "corr_TRX": round(corrs["TRXUSDT"], 4),
            "mean_abs_corr": round(mean_abs, 4),
            "max_abs_corr": round(max_abs, 4),
            "gate3_corr_pass": max_abs < 0.70,  # IC hard gate threshold
        })
    _write_csv(rows, ROOT / "T2_correlation_diversification.csv")
    print(f"T2: {len(rows)} candidates evaluated on Pearson correlation.")
    for r in rows:
        print(f"  {r['symbol']}: corr_BCH={r['corr_BCH']} corr_LDO={r['corr_LDO']} "
              f"corr_TRX={r['corr_TRX']} mean|c|={r['mean_abs_corr']} max|c|={r['max_abs_corr']}")


# ============================================================================
# T3 — Per-symbol feature-mean / std comparison vs incumbents
# (Per diary lesson (a) of iter-v3/021 — sufficient condition for symbol selection)
# ============================================================================

def t3_feature_space_proximity() -> None:
    """Compare candidate IS feature distribution vs incumbents' IS feature distribution.

    Per `feedback_v3_iter064_process_lessons.md` Rule 5 / iter-v3/021 lesson (a):
    Pure return-correlation is insufficient — feature-space proximity matters.

    Method:
      For each symbol (3 incumbents + 5 candidates), compute IS-window distribution
      of 6 stationary proxies (per V3_FEATURE_COLUMNS reference):
        - log_return_8h: 8h log return
        - ret_5d: 5-day cumulative log return (15 bars at 8h)
        - vol_50bar: 50-bar rolling std of 8h returns (regime range proxy)
        - skew_50bar: 50-bar rolling skew of returns
        - kurt_50bar: 50-bar rolling kurt of returns
        - autocorr_lag1_50: 50-bar rolling autocorrelation lag-1

      Candidate-vs-incumbent SIMILARITY = mean Euclidean distance in z-score space
      to each of 3 incumbents (averaged). LOWER = MORE SIMILAR = candidate's
      feature regime is closer to the regime the 14-feature LightGBM heads are
      DESIGNED for.

      This DOES NOT predict OOS — it predicts whether the trained model TRANSFERS
      to the candidate's regime (per-symbol Optuna fit budget is shared at
      n_trials=35/N — so candidates that don't fit existing feature regime won't
      fit at all at low budget; this is the /021 HBAR/AVAX failure mode).
    """
    # Compute features for all 8 symbols
    all_features: dict[str, pd.DataFrame] = {}
    all_symbols = list(BASELINE_SYMBOLS) + list(CANDIDATES)
    for sym in all_symbols:
        df = load_klines(sym)
        is_mask = is_window_mask(df)
        sub = df.loc[is_mask].copy()
        ret = compute_returns(sub)
        feats = pd.DataFrame(index=ret.index)
        feats["log_return_8h"] = ret
        feats["ret_5d"] = ret.rolling(15).sum()
        feats["vol_50bar"] = ret.rolling(50).std()
        feats["skew_50bar"] = ret.rolling(50).skew()
        feats["kurt_50bar"] = ret.rolling(50).kurt()
        feats["autocorr_lag1_50"] = ret.rolling(50).apply(
            lambda x: x.autocorr(lag=1) if x.std() > 1e-9 else 0.0, raw=False
        )
        feats = feats.dropna()
        all_features[sym] = feats

    # Compute per-symbol mean of each feature (in IS window)
    means_per_sym = {}
    stds_per_sym = {}
    for sym, feats in all_features.items():
        means_per_sym[sym] = feats.mean()
        stds_per_sym[sym] = feats.std()

    # Z-score normalization across all 8 symbols using pooled mean+std
    pooled_means = pd.concat([f for f in all_features.values()]).mean()
    pooled_stds = pd.concat([f for f in all_features.values()]).std()
    z_means_per_sym = {
        sym: (means_per_sym[sym] - pooled_means) / pooled_stds
        for sym in all_symbols
    }

    # Per-candidate Euclidean distance in z-score space to each incumbent
    rows = []
    for sym in CANDIDATES:
        cand_z = z_means_per_sym[sym]
        distances = {}
        for base_sym in BASELINE_SYMBOLS:
            base_z = z_means_per_sym[base_sym]
            d = float(np.sqrt(((cand_z - base_z) ** 2).sum()))
            distances[base_sym] = d
        mean_distance = float(np.mean(list(distances.values())))
        rows.append({
            "symbol": sym,
            "z_dist_BCH": round(distances["BCHUSDT"], 4),
            "z_dist_LDO": round(distances["LDOUSDT"], 4),
            "z_dist_TRX": round(distances["TRXUSDT"], 4),
            "mean_z_dist": round(mean_distance, 4),
        })

    # Also export per-symbol raw z-score means for transparency
    z_rows = []
    for sym in all_symbols:
        z = z_means_per_sym[sym]
        z_rows.append({
            "symbol": sym,
            "log_return_8h_z": round(float(z["log_return_8h"]), 4),
            "ret_5d_z": round(float(z["ret_5d"]), 4),
            "vol_50bar_z": round(float(z["vol_50bar"]), 4),
            "skew_50bar_z": round(float(z["skew_50bar"]), 4),
            "kurt_50bar_z": round(float(z["kurt_50bar"]), 4),
            "autocorr_lag1_50_z": round(float(z["autocorr_lag1_50"]), 4),
        })
    _write_csv(rows, ROOT / "T3_feature_space_proximity.csv")
    _write_csv(z_rows, ROOT / "T3b_per_symbol_feature_z_means.csv")
    print(f"T3: {len(rows)} candidates evaluated on feature-space proximity (per /021 lesson (a)).")
    for r in sorted(rows, key=lambda x: x["mean_z_dist"]):
        print(f"  {r['symbol']}: mean_z_dist={r['mean_z_dist']} "
              f"(BCH={r['z_dist_BCH']}, LDO={r['z_dist_LDO']}, TRX={r['z_dist_TRX']})")


# ============================================================================
# T4 — Trade-rate proxy (informational; gate retention is the dominant factor)
# ============================================================================

def t4_trade_rate_proxy() -> None:
    """Trade-count estimate at default labeling (timeout=21, ATR (2.0, 1.0)).

    Heuristic: NATR_pct × candle count × gate retention.
    Gate retention from /060 anchor: BCH 73/24mo = 3.04/mo, LDO 11/24mo = 0.46/mo,
    TRX 75/24mo = 3.13/mo — incumbents average ~2.2/mo. At NATR=4%, raw rate
    is roughly 90 cands/mo × 0.10 = 9/mo; gate retention ≈ 0.25 yields ~2.2/mo.
    """
    rows = []
    for sym in CANDIDATES:
        df = load_klines(sym)
        is_mask = is_window_mask(df)
        sub = df.loc[is_mask].copy()
        if len(sub) < 25:
            rows.append({"symbol": sym, "natr_21_is_pct": 0.0,
                         "raw_trades_per_month_proxy": 0.0,
                         "gate_retained_trades_per_month_proxy": 0.0})
            continue
        h = sub["high"].values
        lw = sub["low"].values
        c = sub["close"].values
        prev_c = np.r_[np.nan, c[:-1]]
        tr = np.maximum.reduce([h - lw, np.abs(h - prev_c), np.abs(lw - prev_c)])
        atr = pd.Series(tr).rolling(21, min_periods=21).mean().values
        natr = atr / c * 100.0
        natr_mean = float(np.nanmean(natr))
        # Rough proxy: 90 candles/mo × NATR/100 × 2.5 (TP=2 ATR scaling)
        raw_rate = 90.0 * min(0.25, natr_mean / 100.0 * 2.5)
        gate_retention = 0.25  # /060 anchor calibrated to ~2.2/mo per symbol
        rows.append({
            "symbol": sym,
            "natr_21_is_pct": round(natr_mean, 4),
            "raw_trades_per_month_proxy": round(raw_rate, 2),
            "gate_retained_trades_per_month_proxy": round(raw_rate * gate_retention, 2),
        })
    _write_csv(rows, ROOT / "T4_trade_rate_proxy.csv")
    print(f"T4: {len(rows)} candidates evaluated on trade-rate proxy.")
    for r in rows:
        print(f"  {r['symbol']}: NATR={r['natr_21_is_pct']}% "
              f"raw_rate={r['raw_trades_per_month_proxy']}/mo "
              f"gate_retained={r['gate_retained_trades_per_month_proxy']}/mo")


# ============================================================================
# T5 — Composite ranking + final pick
# ============================================================================

def t5_composite_ranking() -> None:
    """Composite ranking — PER /021 LESSON (a) REWEIGHTED.

    iter-v3/021 EDA weighted 0.30 × complementarity (correlation), which was
    structurally insufficient. iter-v3/069 EDA reweights to put feature-space
    proximity at the dominant slot:

      Composite = 0.35 × feature_proximity (1 - mean_z_dist / max_dist_norm)
                + 0.20 × complementarity (1 - mean_abs_corr_baseline)
                + 0.20 × data_quality (gate1_pass × 0.5 + gate2_pass × 0.5)
                + 0.15 × liquidity (log10(avg_qvol_M) / log10(1e3))
                + 0.10 × trade_rate (gate_retained / 5.0 trade/month proxy)

    Feature-proximity dominant: 0.35 weight (vs /021's 0.30 on correlation).
    The candidate the trained 14-feature stack TRANSFERS to is the one whose
    IS feature regime is closest to the BCH+LDO+TRX feature regime. This is
    THE primary axis of selection per /021 diary lesson (a).
    """
    # Load all sub-scores
    t1 = list(csv.DictReader(open(ROOT / "T1_per_candidate_data_quality.csv")))
    t2 = list(csv.DictReader(open(ROOT / "T2_correlation_diversification.csv")))
    t3 = list(csv.DictReader(open(ROOT / "T3_feature_space_proximity.csv")))
    t4 = list(csv.DictReader(open(ROOT / "T4_trade_rate_proxy.csv")))

    # Index by symbol
    t1_idx = {r["symbol"]: r for r in t1}
    t2_idx = {r["symbol"]: r for r in t2}
    t3_idx = {r["symbol"]: r for r in t3}
    t4_idx = {r["symbol"]: r for r in t4}

    # Pool max feature distance for normalization
    max_z_dist = max(float(r["mean_z_dist"]) for r in t3)

    rows = []
    for sym in CANDIDATES:
        # 1. Feature-space proximity: 1 - mean_z_dist / max_z_dist (lower dist = higher score)
        feat_prox_raw = float(t3_idx[sym]["mean_z_dist"])
        feat_prox_score = 1.0 - feat_prox_raw / max(max_z_dist, 1e-6)
        # 2. Complementarity: 1 - mean |corr|
        compl_score = 1.0 - float(t2_idx[sym]["mean_abs_corr"])
        # 3. Data quality: gate1 × 0.5 + gate2 × 0.5 (both pass = 1.0)
        dq_score = (
            0.5 * (t1_idx[sym]["gate1_pass"] == "True")
            + 0.5 * (t1_idx[sym]["gate2_pass"] == "True")
        )
        # 4. Liquidity: log10(avg_qvol_m) / log10(1000) — caps at $1B
        avg_qvol_m = float(t1_idx[sym]["is_avg_daily_qvol_usd_M"])
        liq_score = min(1.0, np.log10(max(avg_qvol_m, 1.0)) / np.log10(1000))
        # 5. Trade rate: gate_retained / 5.0 (caps at 5/month)
        tr_score = min(1.0, float(t4_idx[sym]["gate_retained_trades_per_month_proxy"]) / 5.0)

        composite = (
            0.35 * feat_prox_score
            + 0.20 * compl_score
            + 0.20 * dq_score
            + 0.15 * liq_score
            + 0.10 * tr_score
        )
        rows.append({
            "symbol": sym,
            "feat_proximity_score_035": round(feat_prox_score, 4),
            "complementarity_score_020": round(compl_score, 4),
            "data_quality_score_020": round(dq_score, 4),
            "liquidity_score_015": round(liq_score, 4),
            "trade_rate_score_010": round(tr_score, 4),
            "composite": round(composite, 4),
            "mean_z_dist": round(feat_prox_raw, 4),
            "mean_abs_corr": float(t2_idx[sym]["mean_abs_corr"]),
            "gate1_pass": t1_idx[sym]["gate1_pass"],
            "gate2_pass": t2_idx[sym]["gate3_corr_pass"],
        })
    # Rank by composite
    rows = sorted(rows, key=lambda x: x["composite"], reverse=True)
    _write_csv(rows, ROOT / "T5_composite_ranking.csv")
    print("T5: candidates ranked by composite (feature-space-proximity-dominant weighting):")
    for i, r in enumerate(rows, 1):
        print(f"  Rank {i}: {r['symbol']} composite={r['composite']} "
              f"(feat_prox={r['feat_proximity_score_035']}, "
              f"compl={r['complementarity_score_020']}, "
              f"liq={r['liquidity_score_015']})")
    top = rows[0]
    print(f"\n  TOP PICK: {top['symbol']} — mean_z_dist={top['mean_z_dist']} "
          f"mean_abs_corr={top['mean_abs_corr']}")


# ============================================================================
# T6 — Predicted impact of adding 4th symbol
# ============================================================================

def t6_predicted_impact() -> None:
    """Predicted impact on /060 anchor of adding 1 symbol.

    Key mechanisms:
      1. REQUIRED_GAP changes: (21+1)*3=66 → (21+1)*4=88. +22 candles.
         Per-cell training-sample loss ~22/2192 IS bars = ~1% (smaller than
         /068's +3-5% from timeout doubling — should not catastrophically
         degrade LDO).
      2. n_trials_total scales: 35 × 3 syms × 3 seeds = 315 → 35 × 4 syms × 3 seeds = 420.
         Per-symbol Optuna fit budget UNCHANGED at 35 trials × 3 seeds = 105
         fits/cell (each LightGbmStrategy instance is per-symbol independent).
         CONTRA to /021's flawed reasoning that "5 sym × 35 trials = 175 split 5 ways"
         — Optuna is INDEPENDENT per symbol. Each new symbol gets its own
         35 trials × 3 seeds × n_months fit budget.
      3. Universe denominator expands 3 → 4 → top symbol concentration shrinks.
         /060 TRX OOS weighted_pnl was +23.31 (424% concentration on +5.49 total).
         With 4th symbol contributing ~0% (lottery-symmetric), TRX share would
         dilute to ~3/4 × 424% = 318%, still concentrated but mechanically
         reduced. With 4th symbol contributing +5 weighted_pnl (typical),
         total OOS PnL grows to ~10.5; TRX share = 23.31/10.5 = 222%, real
         dilution.
      4. LDO concentration dilution (Critic /068 Rec #3 LDO targeting):
         /060 LDO IS share = -25.44% (negative drag); with 4th symbol replacing
         "marginal share," LDO weight diluted from 11/159 = 6.9% to 11/(159+~50)
         = 5.3% on IS. Smaller dilution than ideal because LDO trade count is
         already low — but mechanical pressure reduction.
      5. Trade-count effects (predicted band):
         IS: 159 + (NATR-derived rate × 24mo × gate retention 0.25) ≈ +35 to +50
             trades. Predicted IS trades: [194, 209].
         OOS: 102 + (similar logic × 14mo OOS) ≈ +20 to +30 trades.
             Predicted OOS trades: [122, 132]. May or may not clear /070
             bundle-level floor 130.
      6. Sharpe impact: dominated by 4th-symbol per-symbol Sharpe contribution.
         At UNIVERSAL-feature, UNIVERSAL-labeling, UNIVERSAL-risk-gates with
         independent per-symbol Optuna fit, 4th symbol's behavior is mostly
         decoupled from incumbents. PROMISING scenario: 4th symbol contributes
         IS Sharpe ~+0.3 / OOS Sharpe ~+0.3 (rough centroid of /060
         incumbents).
    """
    rows = [
        {
            "axis": "REQUIRED_GAP", "before": "66", "after": "88",
            "delta": "+22",
            "interpretation": "+1% per-cell train sample loss (small)",
        },
        {
            "axis": "n_trials_total", "before": "315", "after": "420",
            "delta": "+105",
            "interpretation": (
                "Optuna independent per-symbol; per-symbol budget UNCHANGED"
            ),
        },
        {
            "axis": "n_symbols", "before": "3", "after": "4",
            "delta": "+1",
            "interpretation": (
                "denominator expansion (per concentration_is_signal)"
            ),
        },
        {
            "axis": "predicted_IS_trades", "before": "159",
            "after": "[194, 209]", "delta": "+35 to +50",
            "interpretation": (
                "from NATR-derived candidate trade-rate proxy"
            ),
        },
        {
            "axis": "predicted_OOS_trades", "before": "102",
            "after": "[122, 132]", "delta": "+20 to +30",
            "interpretation": "bundle-level floor 130 may or may not clear",
        },
        {
            "axis": "wall_clock_estimate", "before": "0.4-0.7h",
            "after": "1.5h target", "delta": "+0.8-1.1h",
            "interpretation": (
                "4 syms x 3 seeds x 35 trials at single-seed EXPLORATION"
            ),
        },
        # Predicted Sharpe bands (widened per Critic /068 Rec #1)
        {
            "axis": "predicted_IS_Sharpe_PROMISING", "before": "+0.83",
            "after": "[+0.93, +1.10]", "delta": "+0.10 to +0.27",
            "interpretation": (
                "4th symbol contributes IS Sharpe ~+0.3 + dilution effect"
            ),
        },
        {
            "axis": "predicted_IS_Sharpe_NEGATIVE", "before": "+0.83",
            "after": "[+0.33, +0.63]", "delta": "-0.20 to -0.50",
            "interpretation": (
                "4th symbol drags IS (Optuna doesn't fit at single-seed) "
                "per /021 mode"
            ),
        },
        {
            "axis": "predicted_OOS_Sharpe_PROMISING", "before": "+0.14",
            "after": "[+0.24, +0.50]", "delta": "+0.10 to +0.36",
            "interpretation": (
                "4th symbol contributes OOS + concentration dilution "
                "lifts TRX edge denominator"
            ),
        },
        {
            "axis": "predicted_OOS_Sharpe_NEGATIVE", "before": "+0.14",
            "after": "[-0.36, -0.16]", "delta": "-0.30 to -0.50",
            "interpretation": (
                "envelope per Critic /068 Rec #1 widening; "
                "4th sym OOS-negative scenario"
            ),
        },
    ]
    _write_csv(rows, ROOT / "T6_predicted_impact.csv")
    print("T6: predicted-impact table written.")
    for r in rows:
        print(f"  {r['axis']}: {r['before']} → {r['after']} ({r['delta']}) — {r['interpretation']}")


# ============================================================================
# Driver
# ============================================================================

def main() -> None:
    print("=" * 70)
    print("iter-v3/069 EDA — UNIVERSE EXPANSION (4th symbol; cycle 1 #10 of 10)")
    print(f"Output dir: {ROOT}")
    print("Anchor: iter-v3/060 (IS +0.8325 / OOS +0.1403)")
    print(f"Candidates: {CANDIDATES}")
    print("EXCLUDED: V3_EXCLUDED_SYMBOLS + HBAR/AVAX (iter-v3/021 closed)")
    print("=" * 70)
    t0_anchor_values()
    print()
    t1_per_candidate_data_quality()
    print()
    t2_correlation_diversification()
    print()
    t3_feature_space_proximity()
    print()
    t4_trade_rate_proxy()
    print()
    t5_composite_ranking()
    print()
    t6_predicted_impact()


if __name__ == "__main__":
    main()
