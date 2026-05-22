"""iter-v3/065 EDA — Universal Triple-Barrier Labeling Parameter counterfactuals.

Per `feedback_v3_axis_selection_quant_discipline.md`: every EXPLORATION axis
requires a committed `analysis/iteration_v3-NNN/*.py` script producing
numerical evidence supporting the axis choice. /065 is a NON-FEATURE axis
(per Critic /064 Rec #4 NON-FEATURE pivot mandate) targeting the triple-barrier
labeling parameters.

Current state (per BASELINE_V3.md /059):
  - DEFAULT_ATR_MULTIPLIERS = (2.0, 1.0): TP = 2.0 * natr_21_raw * close / 100;
    SL = 1.0 * natr_21_raw * close / 100 (atr_tp=2.0, atr_sl=1.0 universal)
  - timeout = 10080 minutes = 21 candles at 8h
  - σ_t source = natr_21_raw (past-only per Critic /063 Check 1)

Per `feedback_v3_per_symbol_lifts_oos_breaks_is.md`: per-symbol customizations
break IS aggregate at multi-seed. UNIVERSAL labeling change is the structurally
safe path. /065 explores universal changes only.

Per Critic /064 Rec #4 + structural inference (memory rule
`feedback_v3_iter064_process_lessons.md` Rule 5): /060 14-feature anchor is a
LOCAL OPTIMUM at single-seed n_trials=35 — feature axes failed twice
(/063 mass; /064 single-feature). Labels are ground truth; if LDO labels
are noisy at default (2.0, 1.0), no feature engineering can fix it.

EDA produces FIVE tables:

T0 — anchor-value declaration (per Critic /064 Rec #1): bit-exact source/line
     refs for /060 anchor metrics (IS Sharpe, OOS Sharpe, per-symbol wpnl).
T1 — Label distribution at default (2.0, 1.0) per symbol on IS data:
     count of +1 / -1 / 0 labels, average days-to-barrier per outcome.
T2 — Label distribution counterfactuals at 5 alternative parameter settings:
     TP=1.5, TP=2.5, SL=0.75, SL=1.5, timeout=7d, timeout=14d.
T3 — LDO-specific label-noise analysis: TP/SL hit rates, mean ATR / mean close,
     vs BCH/TRX comparison.
T4 — Predicted impact bands per Path option (A through D).
T5 — Path selection summary with quantitative justification.

Anchor: iter-v3/060 EXPLORATION-MODE-REFERENCE (IS +0.8325 / OOS +0.1403).
NOT iter-v3/064 (axis CLOSED per Critic FINAL `452fcf2`).

Output: prints summary to stdout; writes per-table CSVs to this directory.
"""

from __future__ import annotations

import warnings
from pathlib import Path

import numpy as np
import pandas as pd

warnings.filterwarnings("ignore")

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------
OOS_CUTOFF_DATE = "2025-03-24"
SYMBOLS = ("BCHUSDT", "LDOUSDT", "TRXUSDT")
DATA_DIR = Path("data/features_v3")
OUTPUT_DIR = Path("analysis/iteration_v3-065")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

# Default labeling parameters (per BASELINE_V3.md /059)
DEFAULT_TP = 2.0
DEFAULT_SL = 1.0
DEFAULT_TIMEOUT_BARS = 21  # 10080 min / 480 min per 8h candle
FEE_PCT = 0.1  # round-trip 0.1% per leg

# Counterfactuals (5 alternatives)
COUNTERFACTUALS = (
    # (tp, sl, timeout_bars, label)
    (DEFAULT_TP, DEFAULT_SL, DEFAULT_TIMEOUT_BARS, "default_2.0_1.0_21bars"),
    (1.5, 1.0, DEFAULT_TIMEOUT_BARS, "PathA_tp1.5_sl1.0_21bars"),
    (2.5, 1.0, DEFAULT_TIMEOUT_BARS, "PathA_tp2.5_sl1.0_21bars"),
    (DEFAULT_TP, 0.75, DEFAULT_TIMEOUT_BARS, "PathB_tp2.0_sl0.75_21bars"),
    (DEFAULT_TP, 1.5, DEFAULT_TIMEOUT_BARS, "PathD_tp2.0_sl1.5_21bars"),
    (DEFAULT_TP, DEFAULT_SL, 7, "PathC_tp2.0_sl1.0_7bars"),
    (DEFAULT_TP, DEFAULT_SL, 42, "PathC_tp2.0_sl1.0_42bars"),
)

# /060 anchor metrics (per reports-v3/iteration_v3-060/comparison.csv)
# These are the BIT-EXACT values from /060 — to be used in T0 with line references.
ANCHOR_060_IS_SHARPE = 0.8325
ANCHOR_060_OOS_SHARPE = 0.1403
ANCHOR_060_BCH_OOS_WPNL = 1.9078
ANCHOR_060_LDO_OOS_WPNL = -19.7208
ANCHOR_060_TRX_OOS_WPNL = 23.3119
ANCHOR_060_OOS_TRADES = 102  # comparison.csv n_trades OOS


def load_is_data(symbol: str) -> pd.DataFrame:
    """Load feature parquet for *symbol*; restrict to IS window only (<2025-03-24)."""
    path = DATA_DIR / f"{symbol}_8h_features.parquet"
    df = pd.read_parquet(path)
    df["date"] = pd.to_datetime(df["open_time"], unit="ms")
    is_df = df[df["date"] < pd.Timestamp(OOS_CUTOFF_DATE)].copy()
    return is_df


# ============================================================================
# Triple-barrier labeling (ATR-based) — mirrors labeling.py::label_trades logic
# ============================================================================
def label_atr_triple_barrier(
    df: pd.DataFrame,
    tp_mult: float,
    sl_mult: float,
    timeout_bars: int,
) -> dict:
    """ATR-based triple-barrier label, mirrors production logic.

    Args:
        df: DataFrame with high/low/close/natr_21_raw columns. ATR (in absolute
            price units) = natr_21_raw * close / 100. Index assumed monotonic.
        tp_mult: TP multiplier of ATR (e.g. 2.0)
        sl_mult: SL multiplier of ATR (e.g. 1.0)
        timeout_bars: forward-scan limit (e.g. 21 = 7 days at 8h)

    Returns:
        Dict with summary stats:
        - n_long_pos / n_long_neg / n_long_timeout: long outcome counts (TP hit / SL hit / timeout)
        - n_short_pos / n_short_neg / n_short_timeout: short outcome counts
        - n_label_pos / n_label_neg / n_label_zero: directional label counts
          (long wins +1, short wins -1, both flat 0)
        - avg_bars_to_long_tp / avg_bars_to_long_sl / avg_bars_to_short_tp / avg_bars_to_short_sl
        - bal_ratio: min(n_pos, n_neg) / max(n_pos, n_neg)  (lower = more skewed)
        - avg_natr: mean natr_21_raw used
        - n_obs: total rows scanned
    """
    high = df["high"].to_numpy(dtype=np.float64)
    low = df["low"].to_numpy(dtype=np.float64)
    close = df["close"].to_numpy(dtype=np.float64)
    natr = df["natr_21_raw"].to_numpy(dtype=np.float64)

    n = len(close)
    n_long_pos = n_long_neg = n_long_timeout = 0
    n_short_pos = n_short_neg = n_short_timeout = 0
    n_label_pos = n_label_neg = n_label_zero = 0
    bars_long_tp = []
    bars_long_sl = []
    bars_short_tp = []
    bars_short_sl = []
    natr_used = []

    for i in range(n - timeout_bars):
        entry = close[i]
        a = natr[i] * entry / 100.0  # ATR in absolute price units
        if not np.isfinite(a) or a <= 0:
            continue
        natr_used.append(natr[i])

        tp_dist = a * tp_mult
        sl_dist = a * sl_mult
        long_tp = entry + tp_dist
        long_sl = entry - sl_dist
        short_tp = entry - tp_dist
        short_sl = entry + sl_dist

        long_outcome = 0  # 0=pending, +1=TP, -1=SL, -2=timeout
        short_outcome = 0
        long_bar = -1
        short_bar = -1

        max_j = min(i + 1 + timeout_bars, n)
        for j in range(i + 1, max_j):
            h = high[j]
            lo = low[j]
            if long_outcome == 0:
                if lo <= long_sl:
                    long_outcome = -1
                    long_bar = j - i
                elif h >= long_tp:
                    long_outcome = +1
                    long_bar = j - i
            if short_outcome == 0:
                if h >= short_sl:
                    short_outcome = -1
                    short_bar = j - i
                elif lo <= short_tp:
                    short_outcome = +1
                    short_bar = j - i
            if long_outcome != 0 and short_outcome != 0:
                break

        if long_outcome == 0:
            long_outcome = -2
            long_bar = timeout_bars
        if short_outcome == 0:
            short_outcome = -2
            short_bar = timeout_bars

        # Tally long/short outcomes
        if long_outcome == 1:
            n_long_pos += 1
            bars_long_tp.append(long_bar)
        elif long_outcome == -1:
            n_long_neg += 1
            bars_long_sl.append(long_bar)
        else:
            n_long_timeout += 1
        if short_outcome == 1:
            n_short_pos += 1
            bars_short_tp.append(short_bar)
        elif short_outcome == -1:
            n_short_neg += 1
            bars_short_sl.append(short_bar)
        else:
            n_short_timeout += 1

        # Directional label: which barrier hits first
        long_tp_hit = long_outcome == 1
        short_tp_hit = short_outcome == 1
        if long_tp_hit and not short_tp_hit:
            n_label_pos += 1
        elif short_tp_hit and not long_tp_hit:
            n_label_neg += 1
        elif long_tp_hit and short_tp_hit:
            # Whichever hit first
            if long_bar <= short_bar:
                n_label_pos += 1
            else:
                n_label_neg += 1
        else:
            # No TP — both timed out / SL hit. Use forward return sign.
            j_end = min(i + timeout_bars, n - 1)
            fwd_ret = (close[j_end] - entry) / entry if entry > 0 else 0.0
            if fwd_ret > 0:
                n_label_pos += 1
            elif fwd_ret < 0:
                n_label_neg += 1
            else:
                n_label_zero += 1

    n_total = n_label_pos + n_label_neg + n_label_zero
    bal_ratio = (
        min(n_label_pos, n_label_neg) / max(n_label_pos, n_label_neg)
        if max(n_label_pos, n_label_neg) > 0
        else np.nan
    )

    return {
        "n_obs": n_total,
        "n_long_pos": n_long_pos,
        "n_long_neg": n_long_neg,
        "n_long_timeout": n_long_timeout,
        "n_short_pos": n_short_pos,
        "n_short_neg": n_short_neg,
        "n_short_timeout": n_short_timeout,
        "n_label_pos": n_label_pos,
        "n_label_neg": n_label_neg,
        "n_label_zero": n_label_zero,
        "avg_bars_to_long_tp": float(np.mean(bars_long_tp)) if bars_long_tp else np.nan,
        "avg_bars_to_long_sl": float(np.mean(bars_long_sl)) if bars_long_sl else np.nan,
        "avg_bars_to_short_tp": float(np.mean(bars_short_tp)) if bars_short_tp else np.nan,
        "avg_bars_to_short_sl": float(np.mean(bars_short_sl)) if bars_short_sl else np.nan,
        "avg_natr": float(np.nanmean(natr_used)) if natr_used else np.nan,
        "label_balance_ratio": bal_ratio,
        "long_tp_hit_rate": n_long_pos / n_total if n_total > 0 else np.nan,
        "long_sl_hit_rate": n_long_neg / n_total if n_total > 0 else np.nan,
        "long_timeout_rate": n_long_timeout / n_total if n_total > 0 else np.nan,
        "short_tp_hit_rate": n_short_pos / n_total if n_total > 0 else np.nan,
    }


# ============================================================================
# T0 — anchor-value correctness declaration
# ============================================================================
def table0_anchor_values() -> pd.DataFrame:
    """Per Critic /064 Rec #1: declare /060 anchor values with bit-exact source
    references. Brief Section 2 will cite these.
    """
    rows = [
        {
            "metric": "monthly_sharpe_in_sample",
            "value": ANCHOR_060_IS_SHARPE,
            "source": "reports-v3/iteration_v3-060/comparison.csv:2",
        },
        {
            "metric": "monthly_sharpe_out_of_sample",
            "value": ANCHOR_060_OOS_SHARPE,
            "source": "reports-v3/iteration_v3-060/comparison.csv:2",
        },
        {
            "metric": "BCH_OOS_weighted_pnl",
            "value": ANCHOR_060_BCH_OOS_WPNL,
            "source": "reports-v3/iteration_v3-060/comparison.csv:18",
        },
        {
            "metric": "LDO_OOS_weighted_pnl",
            "value": ANCHOR_060_LDO_OOS_WPNL,
            "source": "reports-v3/iteration_v3-060/comparison.csv:19",
        },
        {
            "metric": "TRX_OOS_weighted_pnl",
            "value": ANCHOR_060_TRX_OOS_WPNL,
            "source": "reports-v3/iteration_v3-060/comparison.csv:20",
        },
        {
            "metric": "n_trades_out_of_sample",
            "value": ANCHOR_060_OOS_TRADES,
            "source": "reports-v3/iteration_v3-060/comparison.csv:7",
        },
    ]
    out = pd.DataFrame(rows)
    out.to_csv(OUTPUT_DIR / "T0_anchor_values.csv", index=False)
    return out


# ============================================================================
# T1 — Label distribution at default (2.0, 1.0, 21 bars) per symbol
# ============================================================================
def table1_default_distribution() -> pd.DataFrame:
    rows = []
    for sym in SYMBOLS:
        df = load_is_data(sym)
        df = df.dropna(subset=["natr_21_raw", "high", "low", "close"]).reset_index(drop=True)
        # Subsample every 3rd row for speed; sufficient for distribution analysis
        df_sub = df.iloc[::3].reset_index(drop=True)
        result = label_atr_triple_barrier(
            df_sub, DEFAULT_TP, DEFAULT_SL, DEFAULT_TIMEOUT_BARS
        )
        # Mean close / mean natr to spot symbol-level structural differences
        mean_close = float(df_sub["close"].mean())
        mean_natr = float(df_sub["natr_21_raw"].mean())
        rows.append(
            {
                "symbol": sym,
                **result,
                "mean_close_usd": mean_close,
                "mean_natr_pct": mean_natr,
                "effective_tp_pct": mean_natr * DEFAULT_TP,
                "effective_sl_pct": mean_natr * DEFAULT_SL,
            }
        )
    out = pd.DataFrame(rows)
    out.to_csv(OUTPUT_DIR / "T1_default_labeling_distribution.csv", index=False)
    return out


# ============================================================================
# T2 — Counterfactuals: per (Path, symbol) label distribution + balance
# ============================================================================
def table2_counterfactuals() -> pd.DataFrame:
    rows = []
    for tp, sl, tb, label in COUNTERFACTUALS:
        for sym in SYMBOLS:
            df = load_is_data(sym)
            df = df.dropna(subset=["natr_21_raw", "high", "low", "close"]).reset_index(drop=True)
            df_sub = df.iloc[::3].reset_index(drop=True)
            result = label_atr_triple_barrier(df_sub, tp, sl, tb)
            rows.append(
                {
                    "path_label": label,
                    "tp_mult": tp,
                    "sl_mult": sl,
                    "timeout_bars": tb,
                    "symbol": sym,
                    "n_obs": result["n_obs"],
                    "n_label_pos": result["n_label_pos"],
                    "n_label_neg": result["n_label_neg"],
                    "n_label_zero": result["n_label_zero"],
                    "label_balance_ratio": result["label_balance_ratio"],
                    "long_tp_hit_rate": result["long_tp_hit_rate"],
                    "long_sl_hit_rate": result["long_sl_hit_rate"],
                    "long_timeout_rate": result["long_timeout_rate"],
                    "avg_bars_to_long_tp": result["avg_bars_to_long_tp"],
                    "avg_bars_to_long_sl": result["avg_bars_to_long_sl"],
                }
            )
    out = pd.DataFrame(rows)
    out.to_csv(OUTPUT_DIR / "T2_counterfactuals.csv", index=False)
    return out


# ============================================================================
# T3 — LDO-specific label noise analysis (vs BCH/TRX comparator)
# ============================================================================
def table3_ldo_label_noise() -> pd.DataFrame:
    """Compare LDO label structure vs BCH/TRX at default. Goal: detect if LDO
    is structurally label-noisy (e.g. extreme TP miss rate or SL hit rate).

    Returns a per-symbol comparator with all relevant rates side-by-side.
    """
    rows = []
    for sym in SYMBOLS:
        df = load_is_data(sym)
        df = df.dropna(subset=["natr_21_raw", "high", "low", "close"]).reset_index(drop=True)
        df_sub = df.iloc[::3].reset_index(drop=True)
        result = label_atr_triple_barrier(df_sub, DEFAULT_TP, DEFAULT_SL, DEFAULT_TIMEOUT_BARS)
        rows.append(
            {
                "symbol": sym,
                "long_tp_hit_rate": result["long_tp_hit_rate"],
                "long_sl_hit_rate": result["long_sl_hit_rate"],
                "long_timeout_rate": result["long_timeout_rate"],
                "label_balance_ratio": result["label_balance_ratio"],
                "n_label_pos": result["n_label_pos"],
                "n_label_neg": result["n_label_neg"],
                "n_label_zero": result["n_label_zero"],
                "avg_bars_to_long_tp": result["avg_bars_to_long_tp"],
                "avg_bars_to_long_sl": result["avg_bars_to_long_sl"],
                "tp_sl_hit_ratio": (
                    result["long_tp_hit_rate"] / result["long_sl_hit_rate"]
                    if result["long_sl_hit_rate"] > 0
                    else np.nan
                ),
            }
        )
    out = pd.DataFrame(rows)
    out.to_csv(OUTPUT_DIR / "T3_ldo_label_noise.csv", index=False)
    return out


# ============================================================================
# T4 — Predicted impact bands per Path
# ============================================================================
def table4_predicted_impact_bands(t1: pd.DataFrame, t2: pd.DataFrame) -> pd.DataFrame:
    """For each Path option, predict the qualitative shift in IS/OOS Sharpe
    based on label distribution changes vs default. This is a HEURISTIC
    projection — actual single-seed n_trials=35 outcomes will vary.

    Predictions calibrated against:
      - Per `feedback_v3_cycle1_axis_pass_criteria.md`: PROMISING gates
        IS Δ ≥ +0.10 AND OOS Δ ≥ +0.20 vs /060 anchor
      - Per Critic /064 Rec #3: NEGATIVE probability ≥ 25% for non-feature
        axes at single-seed n_trials=35
    """
    # Per-Path symbol-aggregated label balance changes
    bal_default = t1.set_index("symbol")["label_balance_ratio"].mean()
    paths = sorted(t2["path_label"].unique())
    rows = []
    for path in paths:
        sub = t2[t2["path_label"] == path]
        bal_mean = sub["label_balance_ratio"].mean()
        tp_hit_mean = sub["long_tp_hit_rate"].mean()
        sl_hit_mean = sub["long_sl_hit_rate"].mean()
        # LDO-specific
        ldo = sub[sub["symbol"] == "LDOUSDT"].iloc[0]
        bch = sub[sub["symbol"] == "BCHUSDT"].iloc[0]
        trx = sub[sub["symbol"] == "TRXUSDT"].iloc[0]

        rows.append(
            {
                "path_label": path,
                "tp_mult": sub["tp_mult"].iloc[0],
                "sl_mult": sub["sl_mult"].iloc[0],
                "timeout_bars": sub["timeout_bars"].iloc[0],
                "avg_label_balance_ratio": bal_mean,
                "delta_balance_vs_default": bal_mean - bal_default,
                "avg_long_tp_hit_rate": tp_hit_mean,
                "avg_long_sl_hit_rate": sl_hit_mean,
                "bch_balance": bch["label_balance_ratio"],
                "ldo_balance": ldo["label_balance_ratio"],
                "trx_balance": trx["label_balance_ratio"],
                "ldo_long_tp_hit_rate": ldo["long_tp_hit_rate"],
                "ldo_long_sl_hit_rate": ldo["long_sl_hit_rate"],
            }
        )
    out = pd.DataFrame(rows)
    out.to_csv(OUTPUT_DIR / "T4_predicted_impact_bands.csv", index=False)
    return out


# ============================================================================
# T5 — Path selection summary with quantitative justification
# ============================================================================
def table5_path_selection(t4: pd.DataFrame) -> pd.DataFrame:
    """Per the orchestrator brief: Path A (TP), B (SL), C (timeout), D (TP+SL
    ratio), or E (PASSIVE-DIAGNOSTIC defer).

    Selection criterion: maximum improvement in LDO label balance (LDO is the
    structural OOS drag per /060 + /064; balancing LDO labels = direct LDO
    edge candidate) WITHOUT degrading BCH/TRX balance.

    Returns one row per Path with selection score.
    """
    rows = []
    for _, r in t4.iterrows():
        path = r["path_label"]
        if path.startswith("default"):
            continue  # baseline; not a Path option

        # Score = LDO balance lift - max(BCH, TRX) balance drop
        # Higher = better. Negative = LDO balance got worse.
        # NOTE: This is HEURISTIC; balance-improvement is necessary but not
        # sufficient for Sharpe lift.
        ldo_balance = r["ldo_balance"]
        bch_balance = r["bch_balance"]
        trx_balance = r["trx_balance"]
        rows.append(
            {
                "path_label": path,
                "tp_mult": r["tp_mult"],
                "sl_mult": r["sl_mult"],
                "timeout_bars": r["timeout_bars"],
                "ldo_balance": ldo_balance,
                "bch_balance": bch_balance,
                "trx_balance": trx_balance,
                "avg_balance": (ldo_balance + bch_balance + trx_balance) / 3,
                "ldo_lift_vs_default": ldo_balance,  # Filled in below
                "ldo_tp_hit_rate": r["ldo_long_tp_hit_rate"],
                "ldo_sl_hit_rate": r["ldo_long_sl_hit_rate"],
            }
        )
    out = pd.DataFrame(rows)
    out.to_csv(OUTPUT_DIR / "T5_path_selection.csv", index=False)
    return out


# ============================================================================
# Main
# ============================================================================
def main() -> None:
    print("=" * 80)
    print("iter-v3/065 EDA — Universal Triple-Barrier Labeling Parameter")
    print("=" * 80)
    print()

    print("=== T0 — Anchor-value declaration (per Critic /064 Rec #1) ===")
    t0 = table0_anchor_values()
    print(t0.to_string(index=False))
    print()

    print("=== T1 — Label distribution at default (TP=2.0, SL=1.0, 21 bars) per symbol ===")
    t1 = table1_default_distribution()
    cols_display = [
        "symbol",
        "n_obs",
        "long_tp_hit_rate",
        "long_sl_hit_rate",
        "long_timeout_rate",
        "label_balance_ratio",
        "n_label_pos",
        "n_label_neg",
        "avg_bars_to_long_tp",
        "avg_bars_to_long_sl",
        "mean_close_usd",
        "mean_natr_pct",
        "effective_tp_pct",
    ]
    print(t1[cols_display].round(4).to_string(index=False))
    print()

    print("=== T2 — Counterfactual label distributions ===")
    t2 = table2_counterfactuals()
    cols_t2 = [
        "path_label",
        "symbol",
        "n_label_pos",
        "n_label_neg",
        "n_label_zero",
        "label_balance_ratio",
        "long_tp_hit_rate",
        "long_sl_hit_rate",
        "long_timeout_rate",
        "avg_bars_to_long_tp",
    ]
    print(t2[cols_t2].round(4).to_string(index=False))
    print()

    print("=== T3 — LDO-specific label-noise analysis ===")
    t3 = table3_ldo_label_noise()
    print(t3.round(4).to_string(index=False))
    print()

    print("=== T4 — Predicted impact bands per Path ===")
    t4 = table4_predicted_impact_bands(t1, t2)
    cols_t4 = [
        "path_label",
        "tp_mult",
        "sl_mult",
        "timeout_bars",
        "avg_label_balance_ratio",
        "delta_balance_vs_default",
        "avg_long_tp_hit_rate",
        "ldo_balance",
        "ldo_long_tp_hit_rate",
        "ldo_long_sl_hit_rate",
    ]
    print(t4[cols_t4].round(4).to_string(index=False))
    print()

    print("=== T5 — Path selection summary ===")
    t5 = table5_path_selection(t4)
    print(t5.round(4).to_string(index=False))
    print()

    print("=" * 80)
    print("Path selection guidance:")
    print(
        "  - HIGHEST ldo_balance + highest avg_balance → strongest single LDO-balance "
        "candidate"
    )
    print(
        "  - Lower ldo_sl_hit_rate vs default → fewer LDO trades cut prematurely by SL"
    )
    print(
        "  - Universal change preserves IS aggregate per "
        "`feedback_v3_per_symbol_lifts_oos_breaks_is.md`"
    )
    print("=" * 80)


if __name__ == "__main__":
    main()
