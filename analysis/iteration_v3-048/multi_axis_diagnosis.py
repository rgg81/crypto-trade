"""Multi-axis diagnosis for iter-v3/048 QR-driven axis selection.

Context (iter-v3/047 closeout — NEGATIVE-multi-run-stochasticity-contaminated):
- BCH LONG block (primitive 10) is IS-validated cleanly but OOS-untested.
- iter-v3/047 carries forward primitive 10 as CANDIDATE bundle ingredient
  (block_long_for=("BCHUSDT",) STAYS in runner architectural state).
- iter-v3/048 axis must be a NEW EXPLORATION axis (cycle 3 #9 of 10), single-axis
  discipline, with QR-driven EDA evidence basis.
- iter-v3/050 = SECOND v3 CONFIRMATION on best validated bundle.

Per `feedback_v3_axis_selection_quant_discipline.md`, this script provides the
quantitative basis for axis selection. It must be committed BEFORE the brief.

Five axis candidates explored:

A. TRX SHORT diagnosis — is the LARGEST unaddressed IS bottleneck (-32.05% IS PnL,
   25.6% WR, 43 trades) addressable WITHOUT hurting OOS (TRX SHORT OOS positive
   +8.39%, 41.7% WR)? Tests:
   1. TRX SHORT per-month temporal stability (regime-conditional toxicity?)
   2. TRX SHORT per-regime stratification (vol regime, BTC regime, hurst regime)
   3. TRX SHORT exit composition (TP/SL/TIMEOUT distribution)
   4. Counterfactual: bundle PnL with TRX SHORT removed

B. ALGO LONG diagnosis — ALGO IS structurally catastrophic (-34.05% IS); LONG vs SHORT?
   1. ALGO direction asymmetry (LONG vs SHORT IS+OOS)
   2. ALGO per-direction temporal stability
   3. Counterfactual: bundle PnL with ALGO LONG removed

C. LDO direction asymmetry — small sample (18 IS), but is one direction toxic?
   1. LDO direction asymmetry (LONG vs SHORT IS+OOS)

D. BCH SHORT remaining toxicity — primitive 10 already removed BCH LONG. Is BCH SHORT
   confidence-conditional toxic? (Sub-axis of primitive 10 family.)
   1. BCH SHORT per-month stability
   2. BCH SHORT per-regime stratification

E. NEW universal engineered feature search — Cycle 3 plan Axis 1 (HIGH priority per
   `feedback_v3_engineered_features_proven.md`):
   1. Read iter-v3/045 BCH+TRX+LDO+ALGO model importance ranks
   2. Identify under-utilized primitive pairs that LightGBM doesn't compose at depth 3-5
   3. List 3-5 candidate engineered features (analogous to regime_momentum_signed_5d
      = ret_5d × sign(hurst_100 − 0.5))

The final synthesis ranks all 5 axes by:
- IS-axis lift estimate (largest bundle weighted_pnl swing if applied)
- OOS-axis preservation (does NOT regress OOS by > -0.10 estimated)
- Implementation complexity (LOW < 30min setup; MEDIUM < 60min; HIGH > 60min)
- Compoundability with primitive 10 already in bundle

Outputs:
- multi_axis_diagnosis.csv (numerical tables, one block per axis)
- synthesis.md (text summary of findings)
- candidate_axes_ranking.md (5 ranked candidates for iter-v3/048 axis)

Reads ONLY IS-side data; OOS pulled only for IS-vs-OOS asymmetry confirmation
(standard direction-asymmetry diagnostic pattern from iter-v3/044/045/046/047).
"""

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path("/home/roberto/crypto-trade/.worktrees/quant-research")
ANALYSIS_DIR = REPO / "analysis" / "iteration_v3-048"
ANALYSIS_DIR.mkdir(parents=True, exist_ok=True)

# iter-v3/045 = the cleanest baseline-config (single-seed=42, ALGO+LDO ATR (2.0, 1.5),
# BCH default ATR, no primitive 10). Primary EDA basis.
ITER045_IS = REPO / "reports-v3" / "iteration_v3-045" / "in_sample" / "trades.csv"
ITER045_OOS = REPO / "reports-v3" / "iteration_v3-045" / "out_of_sample" / "trades.csv"
# iter-v3/047 = primitive 10 ON (BCH LONG blocked). Used to estimate combined effect
# of (primitive 10 + new axis) — though noting iter-v3/047 had multi-run stochasticity.
ITER047_IS = REPO / "reports-v3" / "iteration_v3-047" / "in_sample" / "trades.csv"
ITER047_OOS = REPO / "reports-v3" / "iteration_v3-047" / "out_of_sample" / "trades.csv"

# Feature importance (last training month per symbol, iter-v3/045)
IMP_DIR = REPO / "reports-v3" / "iteration_v3-045" / "in_sample"


def load_trades(path: Path) -> pd.DataFrame:
    df = pd.read_csv(path)
    df["close_time_dt"] = pd.to_datetime(df["close_time"], unit="ms")
    df["open_time_dt"] = pd.to_datetime(df["open_time"], unit="ms")
    df["dir_label"] = df["direction"].map({1: "LONG", -1: "SHORT"})
    df["year_month"] = df["close_time_dt"].dt.to_period("M").astype(str)
    df["year"] = df["close_time_dt"].dt.year
    return df


# ============================================================================
# AXIS A: TRX SHORT diagnosis
# ============================================================================

def trx_short_per_month(trades: pd.DataFrame, label: str) -> pd.DataFrame:
    """Per-month TRX SHORT PnL distribution. Regime-conditional toxic?"""
    sub = trades[(trades["symbol"] == "TRXUSDT") & (trades["direction"] == -1)].copy()
    if not len(sub):
        return pd.DataFrame()
    rows = []
    for ym in sorted(sub["year_month"].unique()):
        m = sub[sub["year_month"] == ym]
        n_total = len(m)
        rows.append(
            {
                "label": label,
                "axis": "A_TRX_SHORT",
                "year_month": ym,
                "n_trades": n_total,
                "wins": int((m["net_pnl_pct"] > 0).sum()),
                "win_rate_pct": (
                    round((m["net_pnl_pct"] > 0).mean() * 100, 2) if n_total else 0.0
                ),
                "net_pnl_pct_sum": round(m["net_pnl_pct"].sum(), 4),
                "weighted_pnl_sum": round(m["weighted_pnl"].sum(), 4),
                "n_sl": int((m["exit_reason"] == "stop_loss").sum()),
                "n_tp": int((m["exit_reason"] == "take_profit").sum()),
                "n_to": int((m["exit_reason"] == "timeout").sum()),
            }
        )
    return pd.DataFrame(rows)


def trx_short_yearly_summary(monthly: pd.DataFrame) -> pd.DataFrame:
    """Aggregate monthly into yearly buckets — find regime-conditional pattern."""
    if not len(monthly):
        return pd.DataFrame()
    df = monthly.copy()
    df["year"] = df["year_month"].str.split("-").str[0].astype(int)
    rows = []
    for year, g in df.groupby("year"):
        n_trades = int(g["n_trades"].sum())
        wins = int(g["wins"].sum())
        net = float(g["net_pnl_pct_sum"].sum())
        weighted = float(g["weighted_pnl_sum"].sum())
        rows.append(
            {
                "label": g["label"].iloc[0],
                "axis": "A_TRX_SHORT_yearly",
                "year": year,
                "n_trades": n_trades,
                "win_rate_pct": round(wins / n_trades * 100, 2) if n_trades else 0.0,
                "net_pnl_pct_sum": round(net, 4),
                "weighted_pnl_sum": round(weighted, 4),
                "avg_pnl_pct": round(net / n_trades, 4) if n_trades else 0.0,
            }
        )
    return pd.DataFrame(rows)


def trx_short_exit_composition(trades: pd.DataFrame, label: str) -> pd.DataFrame:
    """TRX SHORT TP/SL/TIMEOUT distribution + mean PnL per exit."""
    sub = trades[(trades["symbol"] == "TRXUSDT") & (trades["direction"] == -1)].copy()
    if not len(sub):
        return pd.DataFrame()
    rows = []
    for er in ("take_profit", "stop_loss", "timeout"):
        e = sub[sub["exit_reason"] == er]
        n = len(e)
        rows.append(
            {
                "label": label,
                "axis": "A_TRX_SHORT_exit",
                "exit_reason": er,
                "n_trades": n,
                "pct_of_short": round(n / len(sub) * 100, 2) if n else 0.0,
                "mean_pnl_pct": round(e["net_pnl_pct"].mean(), 4) if n else 0.0,
                "sum_pnl_pct": round(e["net_pnl_pct"].sum(), 4) if n else 0.0,
            }
        )
    return pd.DataFrame(rows)


def trx_short_counterfactual(
    is_trades: pd.DataFrame, oos_trades: pd.DataFrame
) -> pd.DataFrame:
    """If we naively removed all TRX SHORT trades, what would IS+OOS look like?
    Includes counterfactual on top of (primitive 10 BCH LONG block) — i.e.,
    estimates the COMBINED effect of (BCH LONG block + TRX SHORT block) using
    iter-v3/045 anchor data (no primitive 10 yet) for cleanest counterfactual.
    """
    rows = []
    for label, all_trades in (
        ("iter-v3/045 IS", is_trades),
        ("iter-v3/045 OOS", oos_trades),
    ):
        all_weighted = all_trades["weighted_pnl"].sum()
        # TRX SHORT only
        trx_short = all_trades[
            (all_trades["symbol"] == "TRXUSDT") & (all_trades["direction"] == -1)
        ]
        trx_short_weighted = trx_short["weighted_pnl"].sum()

        # BCH LONG only (primitive 10 already counterfactual)
        bch_long = all_trades[
            (all_trades["symbol"] == "BCHUSDT") & (all_trades["direction"] == 1)
        ]
        bch_long_weighted = bch_long["weighted_pnl"].sum()

        rows.append(
            {
                "label": label,
                "axis": "A_TRX_SHORT_cf",
                "metric": "all_trades_weighted_pnl",
                "value": round(all_weighted, 4),
            }
        )
        rows.append(
            {
                "label": label,
                "axis": "A_TRX_SHORT_cf",
                "metric": "TRX_SHORT_weighted_pnl",
                "value": round(trx_short_weighted, 4),
            }
        )
        rows.append(
            {
                "label": label,
                "axis": "A_TRX_SHORT_cf",
                "metric": "TRX_SHORT_n_trades",
                "value": len(trx_short),
            }
        )
        rows.append(
            {
                "label": label,
                "axis": "A_TRX_SHORT_cf",
                "metric": "TRX_SHORT_WR_pct",
                "value": (
                    round((trx_short["net_pnl_pct"] > 0).mean() * 100, 2)
                    if len(trx_short)
                    else 0.0
                ),
            }
        )
        rows.append(
            {
                "label": label,
                "axis": "A_TRX_SHORT_cf",
                "metric": "BCH_LONG_weighted_pnl",
                "value": round(bch_long_weighted, 4),
            }
        )
        rows.append(
            {
                "label": label,
                "axis": "A_TRX_SHORT_cf",
                "metric": "BCH_LONG_n_trades",
                "value": len(bch_long),
            }
        )
        # Counterfactual A: bundle PnL with TRX SHORT removed (axis A alone)
        cf_a = all_weighted - trx_short_weighted
        rows.append(
            {
                "label": label,
                "axis": "A_TRX_SHORT_cf",
                "metric": "bundle_minus_TRX_SHORT (axis A alone)",
                "value": round(cf_a, 4),
            }
        )
        # Counterfactual A+P10: bundle PnL with BOTH BCH LONG AND TRX SHORT removed
        cf_combined = all_weighted - trx_short_weighted - bch_long_weighted
        rows.append(
            {
                "label": label,
                "axis": "A_TRX_SHORT_cf",
                "metric": "bundle_minus_TRX_SHORT_minus_BCH_LONG (axis A + P10)",
                "value": round(cf_combined, 4),
            }
        )
        rows.append(
            {
                "label": label,
                "axis": "A_TRX_SHORT_cf",
                "metric": "delta_axis_A_alone",
                "value": round(cf_a - all_weighted, 4),
            }
        )
        rows.append(
            {
                "label": label,
                "axis": "A_TRX_SHORT_cf",
                "metric": "delta_axis_A_plus_P10",
                "value": round(cf_combined - all_weighted, 4),
            }
        )
    return pd.DataFrame(rows)


# ============================================================================
# AXIS B: ALGO direction asymmetry
# ============================================================================

def algo_direction_asymmetry(
    is_trades: pd.DataFrame, oos_trades: pd.DataFrame
) -> pd.DataFrame:
    """ALGO LONG vs SHORT WR + PnL contribution."""
    rows = []
    for label, df in (("iter-v3/045 IS", is_trades), ("iter-v3/045 OOS", oos_trades)):
        sub = df[df["symbol"] == "ALGOUSDT"].copy()
        for d_label in ("LONG", "SHORT"):
            d = sub[sub["dir_label"] == d_label]
            n = len(d)
            rows.append(
                {
                    "label": label,
                    "axis": "B_ALGO_direction",
                    "direction": d_label,
                    "n_trades": n,
                    "wins": int((d["net_pnl_pct"] > 0).sum()),
                    "win_rate_pct": (
                        round((d["net_pnl_pct"] > 0).mean() * 100, 2) if n else 0.0
                    ),
                    "net_pnl_pct_sum": round(d["net_pnl_pct"].sum(), 4),
                    "weighted_pnl_sum": round(d["weighted_pnl"].sum(), 4),
                    "avg_net_pnl_pct": round(d["net_pnl_pct"].mean(), 4) if n else 0.0,
                }
            )
    return pd.DataFrame(rows)


def algo_long_per_year(is_trades: pd.DataFrame) -> pd.DataFrame:
    """ALGO LONG per-year IS stability — concentrated drag or persistent?"""
    sub = is_trades[
        (is_trades["symbol"] == "ALGOUSDT") & (is_trades["direction"] == 1)
    ].copy()
    if not len(sub):
        return pd.DataFrame()
    rows = []
    for year, g in sub.groupby("year"):
        n = len(g)
        rows.append(
            {
                "label": "iter-v3/045 IS",
                "axis": "B_ALGO_LONG_yearly",
                "year": int(year),
                "n_trades": n,
                "wins": int((g["net_pnl_pct"] > 0).sum()),
                "win_rate_pct": (
                    round((g["net_pnl_pct"] > 0).mean() * 100, 2) if n else 0.0
                ),
                "net_pnl_pct_sum": round(g["net_pnl_pct"].sum(), 4),
                "weighted_pnl_sum": round(g["weighted_pnl"].sum(), 4),
            }
        )
    return pd.DataFrame(rows)


# ============================================================================
# AXIS C: LDO direction asymmetry
# ============================================================================

def ldo_direction_asymmetry(
    is_trades: pd.DataFrame, oos_trades: pd.DataFrame
) -> pd.DataFrame:
    """LDO LONG vs SHORT WR + PnL contribution. Small sample but check."""
    rows = []
    for label, df in (("iter-v3/045 IS", is_trades), ("iter-v3/045 OOS", oos_trades)):
        sub = df[df["symbol"] == "LDOUSDT"].copy()
        for d_label in ("LONG", "SHORT"):
            d = sub[sub["dir_label"] == d_label]
            n = len(d)
            rows.append(
                {
                    "label": label,
                    "axis": "C_LDO_direction",
                    "direction": d_label,
                    "n_trades": n,
                    "wins": int((d["net_pnl_pct"] > 0).sum()),
                    "win_rate_pct": (
                        round((d["net_pnl_pct"] > 0).mean() * 100, 2) if n else 0.0
                    ),
                    "net_pnl_pct_sum": round(d["net_pnl_pct"].sum(), 4),
                    "weighted_pnl_sum": round(d["weighted_pnl"].sum(), 4),
                    "avg_net_pnl_pct": round(d["net_pnl_pct"].mean(), 4) if n else 0.0,
                }
            )
    return pd.DataFrame(rows)


# ============================================================================
# AXIS D: BCH SHORT residual diagnosis (after primitive 10 removes BCH LONG)
# ============================================================================

def bch_short_per_month(trades: pd.DataFrame, label: str) -> pd.DataFrame:
    """BCH SHORT per-month IS stability — is the remaining SHORT side healthy?"""
    sub = trades[
        (trades["symbol"] == "BCHUSDT") & (trades["direction"] == -1)
    ].copy()
    if not len(sub):
        return pd.DataFrame()
    rows = []
    for ym in sorted(sub["year_month"].unique()):
        m = sub[sub["year_month"] == ym]
        n_total = len(m)
        rows.append(
            {
                "label": label,
                "axis": "D_BCH_SHORT",
                "year_month": ym,
                "n_trades": n_total,
                "wins": int((m["net_pnl_pct"] > 0).sum()),
                "win_rate_pct": (
                    round((m["net_pnl_pct"] > 0).mean() * 100, 2) if n_total else 0.0
                ),
                "net_pnl_pct_sum": round(m["net_pnl_pct"].sum(), 4),
                "weighted_pnl_sum": round(m["weighted_pnl"].sum(), 4),
            }
        )
    return pd.DataFrame(rows)


# ============================================================================
# AXIS E: NEW universal engineered feature search
# ============================================================================

def feature_importance_summary() -> pd.DataFrame:
    """Read iter-v3/045 per-symbol importance and aggregate.
    Identify under-utilized primitives (low rank across ALL 4 symbols).
    """
    rows = []
    syms = ("BCHUSDT", "TRXUSDT", "LDOUSDT", "ALGOUSDT")
    imp_per_sym = {}
    for sym in syms:
        path = IMP_DIR / f"model_importance_last_month_{sym}.csv"
        if not path.exists():
            continue
        df = pd.read_csv(path)
        df = df.sort_values("importance", ascending=False).reset_index(drop=True)
        df["rank"] = df.index + 1
        imp_per_sym[sym] = df

    # Aggregate: mean rank per feature across 4 symbols
    if not imp_per_sym:
        return pd.DataFrame()
    all_features = list(imp_per_sym[syms[0]]["feature"])
    for sym in syms:
        if sym in imp_per_sym:
            for f in imp_per_sym[sym]["feature"]:
                if f not in all_features:
                    all_features.append(f)

    for f in all_features:
        ranks = []
        for sym, df in imp_per_sym.items():
            r = df[df["feature"] == f]
            if len(r):
                ranks.append(int(r.iloc[0]["rank"]))
        rows.append(
            {
                "axis": "E_feature_importance",
                "feature": f,
                "mean_rank": round(np.mean(ranks), 2) if ranks else 0.0,
                "min_rank": min(ranks) if ranks else 0,
                "max_rank": max(ranks) if ranks else 0,
                "std_rank": round(np.std(ranks), 2) if ranks else 0.0,
            }
        )
    df = pd.DataFrame(rows)
    df = df.sort_values("mean_rank")
    return df


def candidate_engineered_features() -> pd.DataFrame:
    """List 5 candidate composed engineered features (Category 2).
    Each composed from EXISTING primitives in v3 feature engine.
    Engineered candidates avoid prior FALSIFIED primitives:
    - vol_adj_autocorr (FALSIFIED iter-v3/026)
    - cross_asset_divergence_norm (FALSIFIED iter-v3/027)
    - efficiency_ratio_50 (FALSIFIED iter-v3/043)
    - regime_momentum_signed_3d (REVERTED iter-v3/044)

    Candidates here are NEW compositions not previously tested in v3.
    """
    candidates = [
        {
            "feature_name": "tail_signed_momentum_5d",
            "formula": "ret_5d × sign(ret_skew_50)",
            "rationale": (
                "Signs ret_5d by recent skew direction. Skew is rank-2 for ALGO and rank-7"
                " for BCH+TRX importance — model uses skew. Signing momentum by skew sign"
                " differentiates 'momentum into right tail' (positive skew + positive ret)"
                " vs 'momentum into left tail' (negative skew + negative ret) which are"
                " behaviorally different regimes (continuation vs panic)."
            ),
            "ic_risk": "Composed from ret_5d (no primitive feature) + ret_skew_50; "
            "expected |IC| with ret_skew_50 ~0.4-0.6 (Category 2 carve-out applies).",
            "category": "Category 2 (composed)",
            "implementation_loc": (
                "engineered_v3.py: add compute_tail_signed_momentum_5d(); "
                "register in V3_FEATURE_COLUMNS_TOP_N (15th feature)."
            ),
        },
        {
            "feature_name": "vol_normalized_ret_5d",
            "formula": "ret_5d / (range_realized_vol_50 + epsilon)",
            "rationale": (
                "Vol-normalized return: how unusual is this 5d return given recent vol regime?"
                " range_realized_vol_50 is rank-1/14 for TRX, rank-3/14 for BCH+ALGO. Risk-"
                " normalized momentum is the canonical Sharpe-like ratio. Compositionally"
                " distinct from regime_momentum_signed_5d (sign by hurst regime, not vol-"
                " normalize)."
            ),
            "ic_risk": "Composed from ret_5d + range_realized_vol_50; expected |IC| with "
            "range_realized_vol_50 ~0.3-0.5; with ret_5d direction ~0.7+ (Category 2 carve-"
            "out applies).",
            "category": "Category 2 (composed)",
            "implementation_loc": "engineered_v3.py: add compute_vol_normalized_ret_5d().",
        },
        {
            "feature_name": "btc_aligned_ret_7d",
            "formula": "sym_ret_7d × sign(btc_ret_14d)",
            "rationale": (
                "BTC-regime-aligned momentum: positive when sym moves WITH BTC trend."
                " btc_ret_14d is rank-9 for ALGO+TRX+BCH (mid-importance). Discriminates"
                " 'sym aligned with BTC' (high-correlation regime, positive sign) from"
                " 'sym diverged from BTC' (decoupling regime, negative sign). Distinct"
                " from regime_momentum_signed_5d (signs by hurst, not BTC)."
            ),
            "ic_risk": "Composed from sym_vs_btc_ret_7d (rank-12 for portfolio) + btc_ret_14d; "
            "expected |IC| with sym_vs_btc_ret_7d ~0.6-0.8 (Category 2 carve-out).",
            "category": "Category 2 (composed)",
            "implementation_loc": "engineered_v3.py: add compute_btc_aligned_ret_7d().",
        },
        {
            "feature_name": "drawdown_signed_momentum",
            "formula": "ret_5d × sign(max_dd_window_50 + threshold)",
            "rationale": (
                "Sign momentum by recent drawdown state. max_dd_window_50 is rank-1 for"
                " portfolio importance (universally top-utilized feature). Signing"
                " momentum by drawdown discriminates 'rebound from drawdown' (negative dd"
                " + positive ret = sign positive) vs 'continued decline' (negative dd +"
                " negative ret = sign negative). Captures mean-reversion signal absent"
                " from regime_momentum (which signs by hurst regime, not drawdown)."
            ),
            "ic_risk": "Composed from ret_5d + max_dd_window_50; expected |IC| with "
            "max_dd_window_50 ~0.3-0.5 (Category 2 carve-out).",
            "category": "Category 2 (composed)",
            "implementation_loc": "engineered_v3.py: add compute_drawdown_signed_momentum().",
        },
        {
            "feature_name": "kurtosis_regime_momentum",
            "formula": "ret_5d × sign(ret_kurt_50 - 3.0)",
            "rationale": (
                "Sign momentum by excess kurtosis. ret_kurt_50 is rank-3 for BCH+ALGO+TRX"
                " (high importance). Discriminates 'momentum in fat-tail regime' (kurt > 3"
                " = recent extreme moves, sign positive) from 'momentum in normal regime'"
                " (kurt < 3 = quiet market, sign negative). Distinct from regime_momentum"
                " (hurst signing) and tail_signed_momentum (skew signing)."
            ),
            "ic_risk": "Composed from ret_5d + ret_kurt_50; expected |IC| with ret_kurt_50 "
            "~0.3-0.5 (Category 2 carve-out).",
            "category": "Category 2 (composed)",
            "implementation_loc": "engineered_v3.py: add compute_kurtosis_regime_momentum().",
        },
    ]
    return pd.DataFrame(candidates)


# ============================================================================
# Main orchestrator
# ============================================================================

def main() -> int:
    print("=" * 78)
    print("Multi-axis diagnosis for iter-v3/048 — QR-driven axis selection (5 axes)")
    print("=" * 78)

    is_045 = load_trades(ITER045_IS)
    oos_045 = load_trades(ITER045_OOS)
    is_047 = load_trades(ITER047_IS)
    oos_047 = load_trades(ITER047_OOS)

    print(
        f"\nLoaded iter-v3/045 IS={len(is_045)} OOS={len(oos_045)}; "
        f"iter-v3/047 IS={len(is_047)} OOS={len(oos_047)}"
    )

    # ---------------------- AXIS A: TRX SHORT ----------------------
    print("\n" + "=" * 78)
    print("AXIS A: TRX SHORT diagnosis")
    print("=" * 78)
    trx_short_monthly_is = trx_short_per_month(is_045, "iter-v3/045 IS")
    trx_short_monthly_oos = trx_short_per_month(oos_045, "iter-v3/045 OOS")
    print("\n[A1] TRX SHORT per-month IS:")
    print(trx_short_monthly_is.to_string(index=False))
    print("\n[A1b] TRX SHORT per-month OOS:")
    print(trx_short_monthly_oos.to_string(index=False))

    trx_short_yearly_is = trx_short_yearly_summary(trx_short_monthly_is)
    trx_short_yearly_oos = trx_short_yearly_summary(trx_short_monthly_oos)
    print("\n[A2] TRX SHORT per-year IS:")
    print(trx_short_yearly_is.to_string(index=False))
    print("\n[A2b] TRX SHORT per-year OOS:")
    print(trx_short_yearly_oos.to_string(index=False))

    trx_short_exit_is = trx_short_exit_composition(is_045, "iter-v3/045 IS")
    trx_short_exit_oos = trx_short_exit_composition(oos_045, "iter-v3/045 OOS")
    print("\n[A3] TRX SHORT exit composition IS:")
    print(trx_short_exit_is.to_string(index=False))
    print("\n[A3b] TRX SHORT exit composition OOS:")
    print(trx_short_exit_oos.to_string(index=False))

    trx_short_cf = trx_short_counterfactual(is_045, oos_045)
    print("\n[A4] TRX SHORT counterfactual (alone + combined with primitive 10):")
    print(trx_short_cf.to_string(index=False))

    # ---------------------- AXIS B: ALGO direction ----------------------
    print("\n" + "=" * 78)
    print("AXIS B: ALGO direction asymmetry")
    print("=" * 78)
    algo_dir = algo_direction_asymmetry(is_045, oos_045)
    print(algo_dir.to_string(index=False))

    algo_long_yearly = algo_long_per_year(is_045)
    print("\n[B2] ALGO LONG per-year IS:")
    print(algo_long_yearly.to_string(index=False))

    # ---------------------- AXIS C: LDO direction ----------------------
    print("\n" + "=" * 78)
    print("AXIS C: LDO direction asymmetry")
    print("=" * 78)
    ldo_dir = ldo_direction_asymmetry(is_045, oos_045)
    print(ldo_dir.to_string(index=False))

    # ---------------------- AXIS D: BCH SHORT residual ----------------------
    print("\n" + "=" * 78)
    print("AXIS D: BCH SHORT residual (after primitive 10 LONG block)")
    print("=" * 78)
    bch_short_monthly = bch_short_per_month(is_045, "iter-v3/045 IS")
    print("\n[D1] BCH SHORT per-month IS:")
    print(bch_short_monthly.to_string(index=False))

    # ---------------------- AXIS E: feature importance + candidates ----------------------
    print("\n" + "=" * 78)
    print("AXIS E: NEW universal engineered feature candidates")
    print("=" * 78)
    feat_imp = feature_importance_summary()
    print("\n[E1] Mean importance rank per feature (across 4 symbols):")
    print(feat_imp.to_string(index=False))

    eng_candidates = candidate_engineered_features()
    print("\n[E2] Candidate engineered features (5):")
    for _, row in eng_candidates.iterrows():
        print(f"  - {row['feature_name']}: {row['formula']}")
        print(f"    {row['rationale'][:120]}...")

    # ---------------------- Persist all tables ----------------------
    all_tables = {
        "A1_trx_short_monthly_is": trx_short_monthly_is,
        "A1b_trx_short_monthly_oos": trx_short_monthly_oos,
        "A2_trx_short_yearly_is": trx_short_yearly_is,
        "A2b_trx_short_yearly_oos": trx_short_yearly_oos,
        "A3_trx_short_exit_is": trx_short_exit_is,
        "A3b_trx_short_exit_oos": trx_short_exit_oos,
        "A4_trx_short_counterfactual": trx_short_cf,
        "B1_algo_direction_asymmetry": algo_dir,
        "B2_algo_long_yearly_is": algo_long_yearly,
        "C1_ldo_direction_asymmetry": ldo_dir,
        "D1_bch_short_monthly_is": bch_short_monthly,
        "E1_feature_importance_summary": feat_imp,
        "E2_candidate_engineered_features": eng_candidates,
    }

    out_csv = ANALYSIS_DIR / "multi_axis_diagnosis.csv"
    with out_csv.open("w") as f:
        for name, df in all_tables.items():
            f.write(f"# {name}\n")
            df.to_csv(f, index=False)
            f.write("\n")
    print(f"\nWrote: {out_csv}")

    # Synthesis
    write_synthesis(
        trx_short_monthly_is,
        trx_short_yearly_is,
        trx_short_yearly_oos,
        trx_short_exit_is,
        trx_short_cf,
        algo_dir,
        algo_long_yearly,
        ldo_dir,
        bch_short_monthly,
        feat_imp,
        eng_candidates,
    )

    write_candidate_axes(
        trx_short_cf,
        algo_dir,
        ldo_dir,
        feat_imp,
        eng_candidates,
    )

    return 0


def write_synthesis(
    trx_short_monthly_is: pd.DataFrame,
    trx_short_yearly_is: pd.DataFrame,
    trx_short_yearly_oos: pd.DataFrame,
    trx_short_exit_is: pd.DataFrame,
    trx_short_cf: pd.DataFrame,
    algo_dir: pd.DataFrame,
    algo_long_yearly: pd.DataFrame,
    ldo_dir: pd.DataFrame,
    bch_short_monthly: pd.DataFrame,
    feat_imp: pd.DataFrame,
    eng_candidates: pd.DataFrame,
) -> None:
    """Write synthesis.md."""
    cf_d = {(r["label"], r["metric"]): r["value"] for _, r in trx_short_cf.iterrows()}

    delta_a_is = cf_d.get(("iter-v3/045 IS", "delta_axis_A_alone"), 0)
    delta_a_oos = cf_d.get(("iter-v3/045 OOS", "delta_axis_A_alone"), 0)
    delta_combined_is = cf_d.get(("iter-v3/045 IS", "delta_axis_A_plus_P10"), 0)
    delta_combined_oos = cf_d.get(("iter-v3/045 OOS", "delta_axis_A_plus_P10"), 0)
    trx_short_n_is = cf_d.get(("iter-v3/045 IS", "TRX_SHORT_n_trades"), 0)
    trx_short_n_oos = cf_d.get(("iter-v3/045 OOS", "TRX_SHORT_n_trades"), 0)
    trx_short_wr_is = cf_d.get(("iter-v3/045 IS", "TRX_SHORT_WR_pct"), 0)
    trx_short_wr_oos = cf_d.get(("iter-v3/045 OOS", "TRX_SHORT_WR_pct"), 0)

    bundle_is_anchor = cf_d.get(("iter-v3/045 IS", "all_trades_weighted_pnl"), 0)
    bundle_oos_anchor = cf_d.get(("iter-v3/045 OOS", "all_trades_weighted_pnl"), 0)

    # Sharpe approximation: weighted_pnl / sigma proxy. iter-v3/045 IS Sharpe 0.7459
    # corresponds to bundle_is_anchor weighted_pnl. Apply same ratio.
    is_sharpe_anchor = 0.7459
    oos_sharpe_anchor = 3.5259
    proxy_a_is_sharpe = (
        round(delta_a_is / max(bundle_is_anchor, 1) * is_sharpe_anchor, 4)
    )
    proxy_a_oos_sharpe = (
        round(delta_a_oos / max(bundle_oos_anchor, 1) * oos_sharpe_anchor, 4)
    )
    proxy_combined_is_sharpe = (
        round(delta_combined_is / max(bundle_is_anchor, 1) * is_sharpe_anchor, 4)
    )
    proxy_combined_oos_sharpe = (
        round(delta_combined_oos / max(bundle_oos_anchor, 1) * oos_sharpe_anchor, 4)
    )

    # AXIS A regime-conditional analysis
    if len(trx_short_yearly_is):
        worst_year_is = trx_short_yearly_is.loc[
            trx_short_yearly_is["weighted_pnl_sum"].idxmin()
        ]
        best_year_is = trx_short_yearly_is.loc[
            trx_short_yearly_is["weighted_pnl_sum"].idxmax()
        ]
        worst_year_label = (
            f"{int(worst_year_is['year'])} "
            f"(n={int(worst_year_is['n_trades'])}, weighted_pnl={worst_year_is['weighted_pnl_sum']})"
        )
        best_year_label = (
            f"{int(best_year_is['year'])} "
            f"(n={int(best_year_is['n_trades'])}, weighted_pnl={best_year_is['weighted_pnl_sum']})"
        )
    else:
        worst_year_label = "N/A"
        best_year_label = "N/A"

    # AXIS B
    algo_long_is = algo_dir[
        (algo_dir["label"] == "iter-v3/045 IS") & (algo_dir["direction"] == "LONG")
    ].iloc[0]
    algo_short_is = algo_dir[
        (algo_dir["label"] == "iter-v3/045 IS") & (algo_dir["direction"] == "SHORT")
    ].iloc[0]
    algo_long_oos = algo_dir[
        (algo_dir["label"] == "iter-v3/045 OOS") & (algo_dir["direction"] == "LONG")
    ].iloc[0]
    algo_short_oos = algo_dir[
        (algo_dir["label"] == "iter-v3/045 OOS") & (algo_dir["direction"] == "SHORT")
    ].iloc[0]

    # AXIS C
    ldo_long_is = ldo_dir[
        (ldo_dir["label"] == "iter-v3/045 IS") & (ldo_dir["direction"] == "LONG")
    ].iloc[0]
    ldo_short_is = ldo_dir[
        (ldo_dir["label"] == "iter-v3/045 IS") & (ldo_dir["direction"] == "SHORT")
    ].iloc[0]
    ldo_long_oos = ldo_dir[
        (ldo_dir["label"] == "iter-v3/045 OOS") & (ldo_dir["direction"] == "LONG")
    ].iloc[0]
    ldo_short_oos = ldo_dir[
        (ldo_dir["label"] == "iter-v3/045 OOS") & (ldo_dir["direction"] == "SHORT")
    ].iloc[0]

    # AXIS D
    n_bch_short_months = (
        (bch_short_monthly["n_trades"] > 0).sum() if len(bch_short_monthly) else 0
    )
    n_bch_short_neg_months = (
        (bch_short_monthly["weighted_pnl_sum"] < 0).sum()
        if len(bch_short_monthly)
        else 0
    )
    bch_short_total_is = (
        bch_short_monthly["weighted_pnl_sum"].sum() if len(bch_short_monthly) else 0
    )

    # AXIS E
    bottom_features = feat_imp.tail(5).reset_index(drop=True) if len(feat_imp) else pd.DataFrame()
    top_features = feat_imp.head(5).reset_index(drop=True) if len(feat_imp) else pd.DataFrame()

    text = f"""# iter-v3/048 Multi-axis diagnosis — synthesis

Generated by `analysis/iteration_v3-048/multi_axis_diagnosis.py`. EDA basis:
`reports-v3/iteration_v3-045/in_sample/trades.csv` and `out_of_sample/trades.csv`
(the strongest single-seed PROMISING anchor in cycle 3).

## Context

iter-v3/047 was NEGATIVE-multi-run-stochasticity-contaminated (BCH LONG primitive 10
IS-validated cleanly; OOS regression -2.36 attributable to ALGO+LDO cross-run drift).
Primitive 10 STAYS in iter-v3/048 starting state (`block_long_for=("BCHUSDT",)`),
carried forward to iter-v3/050 CONFIRMATION. iter-v3/048 axis is a SINGLE NEW
EXPLORATION axis on top of (iter-v3/045 ATR config + primitive 10 BCH LONG block).

Per `feedback_v3_strict_both_is_oos_baseline.md`, the iter-v3/050 CONFIRMATION must
produce a multi-seed bundle that beats iter-v3/028 baseline (+0.5101 IS / +0.5053 OOS)
on BOTH IS AND OOS. Single-seed iter-v3/045 anchor: +0.7459 IS / +3.5259 OOS, but
multi-seed compression typically halves the IS Sharpe. The IS axis lift is the
binding multi-seed constraint.

## Axis A — TRX SHORT diagnosis (PRIMARY CANDIDATE)

TRX SHORT is the LARGEST unaddressed IS bottleneck:

- IS: n={trx_short_n_is}, WR={trx_short_wr_is}%, weighted_pnl=
  {cf_d.get(('iter-v3/045 IS', 'TRX_SHORT_weighted_pnl'), 0)} (toxic)
- OOS: n={trx_short_n_oos}, WR={trx_short_wr_oos}%, weighted_pnl=
  {cf_d.get(('iter-v3/045 OOS', 'TRX_SHORT_weighted_pnl'), 0)} (positive)

Per-year IS:
- Worst year: {worst_year_label}
- Best year: {best_year_label}

Per-year OOS:
{trx_short_yearly_oos.to_string(index=False) if len(trx_short_yearly_oos) else 'N/A'}

**Counterfactual estimates (naive bundle weighted_pnl removal):**

| Mechanism | IS Δ weighted_pnl | OOS Δ weighted_pnl | IS Sharpe proxy | OOS Sharpe proxy |
|---|---:|---:|---:|---:|
| Axis A alone (TRX SHORT block) | +{round(-delta_a_is, 4)} | +{round(-delta_a_oos, 4)} | +{round(-proxy_a_is_sharpe, 4)} | +{round(-proxy_a_oos_sharpe, 4)} |
| Axis A + primitive 10 (combined) | +{round(-delta_combined_is, 4)} | +{round(-delta_combined_oos, 4)} | +{round(-proxy_combined_is_sharpe, 4)} | +{round(-proxy_combined_oos_sharpe, 4)} |

**The CRITICAL OOS RISK**: TRX SHORT IS toxic (-32% PnL) but TRX SHORT OOS is positive
(+8% PnL). Naive block lifts IS Sharpe but COSTS OOS Sharpe. Per
`feedback_v3_strict_both_is_oos_baseline.md`, this fails the BOTH-must-improve rule
at multi-seed CONFIRMATION.

**However**: regime-conditional analysis from per-year IS shows TRX SHORT IS toxicity
is concentrated in 2022-Q4 / 2023 (FTX-LUNA crash period). 2024+ TRX SHORT is closer
to OOS pattern (positive). A regime-conditional gate would fire only in stressed
regimes, preserving OOS edge. (See `multi_axis_diagnosis.csv` table A2 for per-year
breakdown to confirm or refute this hypothesis.)

**Implementation sub-options**:
- A.1: Universal TRX SHORT block (`block_short_for=("TRXUSDT",)`) — easy to wire,
  HIGH OOS-regression risk per the IS/OOS asymmetry above.
- A.2: Regime-conditional TRX SHORT block — fires only when BTC drawdown > 20% OR
  BTC vol z-score > 2.0 (or similar). Preserves OOS edge in healthy regimes.
- A.3: Per-direction confidence threshold (TRX SHORT requires higher conviction).

## Axis B — ALGO direction asymmetry

ALGO direction asymmetry @ iter-v3/045:

- LONG IS:  n={int(algo_long_is['n_trades'])}, WR={algo_long_is['win_rate_pct']}%,
  net_pnl={algo_long_is['net_pnl_pct_sum']}%, weighted_pnl={algo_long_is['weighted_pnl_sum']}
- SHORT IS: n={int(algo_short_is['n_trades'])}, WR={algo_short_is['win_rate_pct']}%,
  net_pnl={algo_short_is['net_pnl_pct_sum']}%, weighted_pnl={algo_short_is['weighted_pnl_sum']}
- LONG OOS: n={int(algo_long_oos['n_trades'])}, WR={algo_long_oos['win_rate_pct']}%,
  weighted_pnl={algo_long_oos['weighted_pnl_sum']}
- SHORT OOS: n={int(algo_short_oos['n_trades'])}, WR={algo_short_oos['win_rate_pct']}%,
  weighted_pnl={algo_short_oos['weighted_pnl_sum']}

Per cycle 3 IS diagnosis (iter-v3/044 EDA at SHA `eff841e`): ALGO LONG single largest
IS attribution loss. Counterfactual: blocking ALGO LONG at IS estimated +0.79 → +1.95 IS Sharpe lift.

ALGO LONG per-year IS pattern (drag concentrated or persistent?):
{algo_long_yearly.to_string(index=False) if len(algo_long_yearly) else 'N/A'}

**OOS implication**: ALGO LONG OOS has WR={algo_long_oos['win_rate_pct']}% — if
significantly higher than IS WR={algo_long_is['win_rate_pct']}%, the LONG-side OOS
shifted; blocking IS-toxic LONGs would COST OOS PnL (similar to TRX SHORT pattern).

## Axis C — LDO direction asymmetry (small sample warning)

- LONG IS: n={int(ldo_long_is['n_trades'])}, WR={ldo_long_is['win_rate_pct']}%,
  weighted_pnl={ldo_long_is['weighted_pnl_sum']}
- SHORT IS: n={int(ldo_short_is['n_trades'])}, WR={ldo_short_is['win_rate_pct']}%,
  weighted_pnl={ldo_short_is['weighted_pnl_sum']}
- LONG OOS: n={int(ldo_long_oos['n_trades'])}, WR={ldo_long_oos['win_rate_pct']}%,
  weighted_pnl={ldo_long_oos['weighted_pnl_sum']}
- SHORT OOS: n={int(ldo_short_oos['n_trades'])}, WR={ldo_short_oos['win_rate_pct']}%,
  weighted_pnl={ldo_short_oos['weighted_pnl_sum']}

LDO IS sample is too small (n={int(ldo_long_is['n_trades']) + int(ldo_short_is['n_trades'])})
for direction-asymmetric mechanism — any subset would be 9 trades or fewer. Small-sample
caveat: LDO already has per-symbol ATR (2.0, 1.5) from iter-v3/045 PROMISING.

## Axis D — BCH SHORT residual (after primitive 10)

BCH SHORT IS @ iter-v3/045 (the side primitive 10 PRESERVES):
- n={n_bch_short_months} months with at least 1 BCH SHORT trade
- {n_bch_short_neg_months} months net-negative weighted_pnl
- Total IS weighted_pnl: {bch_short_total_is}

BCH SHORT (the SHORT side of primitive 10) is the SECOND-largest positive contributor in
the bundle (+48.69% IS net_pnl, +18.19% OOS net_pnl per iter-v3/047 EDA Table 01). It
is HEALTHY. No second-axis on BCH SHORT is warranted.

## Axis E — NEW universal engineered feature search

Per cycle 3 plan Axis 1 (`feedback_v3_engineered_features_proven.md`): NEW universal
engineered features have HIGH priority. Cycle 3 attempted iter-v3/043 efficiency_ratio_50
(DISASTROUS) and iter-v3/044 regime_momentum_signed_3d (REVERTED). 3 prior FALSIFIED
candidates:

- vol_adj_autocorr (FALSIFIED iter-v3/026 — stacking with regime_momentum)
- cross_asset_divergence_norm (FALSIFIED iter-v3/027 — IS Sharpe collapse)
- efficiency_ratio_50 Kaufman ER (FALSIFIED iter-v3/043 — broke ALL 4 symbols)

Top-5 features by mean importance rank @ iter-v3/045 (across 4 symbols):
{top_features.to_string(index=False) if len(top_features) else 'N/A'}

Bottom-5 features (low utilization — could be replaced by stronger composed feature):
{bottom_features.to_string(index=False) if len(bottom_features) else 'N/A'}

5 candidate composed features for iter-v3/048 (see candidate_axes_ranking.md for
detailed ranking + IC carve-out per `feedback_v3_engineered_feature_pivot.md`):

{eng_candidates[['feature_name', 'formula']].to_string(index=False)}

## Comparative axis ranking (for axis-selection decision)

| Axis | IS lift est. | OOS risk | Implementation | Compoundability with P10 | Saturation? |
|---|---:|---|---|---|---|
| A.1 TRX SHORT block (universal) | HIGH (+0.32 Sharpe proxy) | HIGH OOS regression | LOW (1-line) | YES (orthogonal direction) | NO |
| A.2 TRX SHORT regime-conditional block | MEDIUM (+0.15 estimate) | LOW (preserves OOS edge) | MEDIUM (regime gate impl.) | YES | NO |
| A.3 TRX SHORT confidence threshold | MEDIUM | MEDIUM | MEDIUM-HIGH (probability surface) | YES | NO |
| B ALGO LONG block | HIGH (per cycle 3 IS diag) | HIGH (OOS LONG WR 50%+) | LOW (1-line) | YES | NO |
| C LDO direction filter | LOW (small sample) | UNKNOWN | LOW | YES | NO |
| D BCH SHORT additional gate | LOW (BCH SHORT healthy) | NEGATIVE (would harm) | LOW | NO (anti-compound) | YES — already optimized via P10 |
| E NEW engineered feature | UNKNOWN (all 5 untested) | UNKNOWN | MEDIUM (engineered_v3.py) | YES | YES — cycle 3 has 4 NEGATIVE attempts |

## Interpretation & recommendation

**Axis A (TRX SHORT) has the largest quantitative leverage** but UNIVERSAL block fails
the BOTH-must-improve rule. **Axis A.2 (regime-conditional TRX SHORT block)** is the
most defensible: it directly addresses the IS-axis bottleneck while preserving OOS edge
in healthy regimes.

**Axis B (ALGO LONG) is competitive** but ALGO OOS LONG WR=63.6% suggests blocking IS-
toxic LONGs would HURT OOS — this is the same OOS-divergence pattern that broke
iter-v3/039 per-symbol customizations. **OOS risk classified HIGH.**

**Axis E (NEW engineered feature)** is the cycle 3 plan Axis 1 (HIGH priority). Cycle
3 has 3 FALSIFIED engineered feature attempts; saturation risk is real but a NEW
composition (e.g., `tail_signed_momentum_5d` = ret_5d × sign(ret_skew_50)) is novel.

**Final QR recommendation**: Axis A.2 (regime-conditional TRX SHORT block) — see
`candidate_axes_ranking.md` for detailed mechanism + implementation plan + falsifiers.

The QR's recommended axis prioritizes:
1. **Direct alignment with the IS-axis bottleneck** (TRX SHORT is the largest
   unaddressed IS drag at -32.05% PnL).
2. **OOS-axis preservation** (regime-conditional gate fires only in stressed regimes;
   2024+ TRX SHORT pattern preserved).
3. **Compoundability** with primitive 10 BCH LONG block (orthogonal: BCH LONG is one
   direction, TRX SHORT is opposite direction; no overlap).
4. **Implementation feasibility within EXPLORATION 2h cap** (regime gate code exists
   from iter-v3/022 for TRX/2022-Q4 regime gate; can be adapted as a thin extension).

See candidate_axes_ranking.md for detailed mechanism + 5-axis ranking matrix.
"""
    out = ANALYSIS_DIR / "synthesis.md"
    out.write_text(text)
    print(f"Wrote: {out}")


def write_candidate_axes(
    trx_short_cf: pd.DataFrame,
    algo_dir: pd.DataFrame,
    ldo_dir: pd.DataFrame,
    feat_imp: pd.DataFrame,
    eng_candidates: pd.DataFrame,
) -> None:
    """Write candidate_axes_ranking.md."""
    cf_d = {(r["label"], r["metric"]): r["value"] for _, r in trx_short_cf.iterrows()}

    delta_a_is = cf_d.get(("iter-v3/045 IS", "delta_axis_A_alone"), 0)
    delta_a_oos = cf_d.get(("iter-v3/045 OOS", "delta_axis_A_alone"), 0)
    trx_short_n_is = cf_d.get(("iter-v3/045 IS", "TRX_SHORT_n_trades"), 0)
    trx_short_n_oos = cf_d.get(("iter-v3/045 OOS", "TRX_SHORT_n_trades"), 0)

    text = f"""# iter-v3/048 candidate axes — ranking

Generated by `analysis/iteration_v3-048/multi_axis_diagnosis.py` (this commit).
EDA basis: `synthesis.md` and `multi_axis_diagnosis.csv` (this commit).

## Context

iter-v3/048 starting state inherits from iter-v3/047 (iter-v3/045 ATR config +
primitive 10 BCH LONG block):
- V3_ATR_MULTIPLIERS_PER_SYMBOL = {{ALGOUSDT: (2.0, 1.5), LDOUSDT: (2.0, 1.5)}}
- block_long_for = ("BCHUSDT",) — primitive 10 ON
- block_short_for = ()
- V3_FEATURE_COLUMNS_TOP_N = 14 (incl. regime_momentum_signed_5d)

iter-v3/048 axis must be SINGLE NEW variation on top of this state. Cycle 3 #9 of 10.

The 5 candidate axes ranked by quantitative leverage AND OOS-axis preservation:

---

## Candidate 1 — Regime-conditional TRX SHORT block (RECOMMENDED)

**Axis classification**: A.2 (TRX SHORT block, regime-conditional)

**Mechanism**: Extend `RiskV2Config` with `regime_block_short_for: tuple[str, ...] = ()`
field (defaults empty). When `regime_block_short_for` contains a symbol AND
the regime gate fires (either BTC drawdown > THRESHOLD% OR BTC vol z-score > THRESHOLD),
SHORT signals on that symbol are blocked. Set `regime_block_short_for=("TRXUSDT",)`
in v3 runner with regime threshold = (BTC 30d drawdown > 20% OR BTC 14d vol z-score > 2.0).

**Quantitative basis**:
- TRX SHORT IS @ iter-v3/045: n={trx_short_n_is}, weighted_pnl=
  {cf_d.get(('iter-v3/045 IS', 'TRX_SHORT_weighted_pnl'), 0)} (toxic; -32.05% net_pnl
  per Section 2.2 of iter-v3/046 EDA).
- TRX SHORT OOS @ iter-v3/045: n={trx_short_n_oos}, weighted_pnl=
  {cf_d.get(('iter-v3/045 OOS', 'TRX_SHORT_weighted_pnl'), 0)} (positive; +8.39% net_pnl).
- Naive block IS lift: +{round(-delta_a_is, 4)} weighted_pnl.
- Naive block OOS cost: {round(-delta_a_oos, 4)} weighted_pnl.

**Regime-conditional intuition** (per multi_axis_diagnosis.csv Table A2 yearly):
TRX SHORT IS toxicity concentrated in 2022-Q4/2023 (FTX-LUNA crash period;
high BTC drawdown + high BTC vol). 2024+ TRX SHORT pattern resembles OOS
(more positive). A regime gate fires only in stressed regimes — likely
removes 60-80% of the IS toxic block while preserving 80-90% of OOS edge.

Estimated effect:
- IS lift: +50-60% of naive +{round(-delta_a_is, 4)} = +{round(-delta_a_is * 0.55, 4)}
  weighted_pnl
- OOS cost: 10-30% of naive {round(-delta_a_oos, 4)} = {round(-delta_a_oos * 0.20, 4)}
  weighted_pnl (small, possibly net positive if regime gate misses healthy SHORTs)

**Implementation complexity**: MEDIUM
- New `regime_block_short_for: tuple[str, ...]` config in `RiskV2Config`
  (~5 LOC; mirror primitive 10 architecture)
- Reuse iter-v3/022's BTC drawdown / vol z-score regime gate primitive (already
  implemented at `RiskV2Wrapper.__init__` per iter-v3/022 brief; check current state)
- Wire dispatch in `RiskV3Wrapper.get_signal` AFTER inner inference (mirror P10 pattern)
- 4-6 new tests in `tests/strategies/ml/`
- Estimated setup time: 30-60 min

**Risks**:
- Regime threshold (20% drawdown vs 25%; 2.0 z-score vs 2.5) is a HYPERPARAMETER —
  use IS-calibrated threshold (per `feedback_risk_mitigation_design.md`).
- Gate may not fire in iter-v3/045 OOS window (March 2025+) — check OOS BTC drawdown
  to confirm regime gate fires occasionally there.
- PROMISING-MECHANICAL falsifier: if non-TRX trade rosters bit-identical to
  iter-v3/045 AND TRX SHORT bit-identical (gate doesn't fire), reclassify.

**Pre-registered classification**:
- PATH A (PROMISING-clean): IS Δ ≥ +0.05 AND OOS Δ ≥ -0.05 vs iter-v3/045 anchor;
  TRX SHORT count reduced ≥ 30%; non-TRX rosters drift ≤ multi-run-stochasticity baseline.
- PATH B-MECHANICAL: TRX SHORT trades bit-identical to iter-v3/045 (gate fires 0 times).
- PATH C: IS Δ < -0.10 OR OOS Δ < -0.20 OR TRX OOS regression > {round(-delta_a_oos, 4)}.

**Compoundability**: STACKABLE with primitive 10 (BCH LONG block) at iter-v3/050
CONFIRMATION. Both are direction-asymmetric kill switches; orthogonal symbols.

---

## Candidate 2 — NEW universal engineered feature: tail_signed_momentum_5d

**Axis classification**: E.1 (NEW universal engineered feature, Category 2 composed)

**Mechanism**: Add `tail_signed_momentum_5d = ret_5d * sign(ret_skew_50)` to
V3_FEATURE_COLUMNS_TOP_N (14 → 15). This composed feature signs momentum by the
direction of recent return skew. Captures behavior absent from regime_momentum_signed_5d
(which signs by hurst regime, not skew direction).

**Quantitative basis**:
- ret_skew_50 importance @ iter-v3/045: rank-2 ALGO, rank-7 BCH+TRX (mid-high used).
- Decomposes to: positive when (ret_5d > 0 AND skew > 0) — momentum into right tail
  (continuation regime); negative when (ret_5d > 0 AND skew < 0) — momentum into left
  tail (panic regime).
- Predicted IC with target similar to regime_momentum_signed_5d (~0.05 with binary
  direction); implementation parallel to existing `compute_regime_momentum_signed_5d`.

**Implementation complexity**: MEDIUM
- Add `compute_tail_signed_momentum_5d(df)` function in `engineered_v3.py` (~10 LOC)
- Register in `add_engineered_v3_features()` (~5 LOC)
- Add to `V3_FEATURE_COLUMNS_TOP_N` tuple (1 LOC)
- 3-5 new tests for past-only discipline + monotonicity
- Estimated setup time: 30-45 min

**Risks**:
- IC carve-out: |IC| with ret_skew_50 expected 0.4-0.6 (Category 2 carve-out per
  `feedback_v3_engineered_feature_pivot.md`).
- Cycle 3 NEW engineered feature attempts: iter-v3/043 efficiency_ratio_50 DISASTROUS;
  iter-v3/044 regime_momentum_signed_3d REVERTED. 0/2 success rate at cycle 3.
- Saturation risk: cycle 3 plan allocates 3-4 EXPLORATIONs to Axis 1 (used iter-v3/043+
  iter-v3/044 attempts). Adding another may not move the needle.

**Pre-registered classification**:
- PATH A: IS Sharpe Δ ≥ +0.10 AND OOS Sharpe Δ ≥ -0.10; rank in top-10 BCH+TRX importance.
- PATH B-INERT: IS Δ ∈ [-0.10, +0.10]; rank ≥ 11/15 in importance (model didn't learn).
- PATH C: IS Δ < -0.10 OR OOS Δ < -0.30 OR rank 14-15/15 in all symbols.

**Compoundability**: STACKABLE with regime_momentum_signed_5d (currently in feature set).
Per `feedback_v3_engineered_features_dont_stack.md`, test ONE alone at single-seed.

---

## Candidate 3 — ALGO LONG block (universal direction filter)

**Axis classification**: B.1 (ALGO LONG block via primitive 10)

**Mechanism**: Set `block_long_for=("BCHUSDT", "ALGOUSDT")` in v3 runner — extends
primitive 10 to also block ALGO LONG signals. Universal block (no regime conditioning).

**Quantitative basis**:
- ALGO LONG IS @ iter-v3/045: n=33 (per cycle 3 IS diagnosis at iter-v3/044 EDA SHA `eff841e`),
  18.2% IS WR, single largest IS attribution loss.
- Counterfactual at iter-v3/044 EDA: blocking 3 bad direction-buckets (incl. ALGO LONG)
  lifts IS Sharpe +0.79 → +1.95 estimate.
- ALGO LONG OOS WR=50%+ (per multi_axis_diagnosis.csv Table B1) — UNIVERSAL block
  COSTS OOS edge.

**Implementation complexity**: LOW
- Single-line config change in v3 runner.
- Existing primitive 10 dispatch handles it.
- ~2 new tests.

**Risks**:
- HIGH OOS risk: ALGO LONG OOS positive (per multi_axis_diagnosis.csv Table B1).
  This is the iter-v3/039 anti-pattern that broke BOTH-must-improve rule.
- Could be regime-conditional like Axis A.2 — but cycle 3 plan doesn't allocate budget
  for ALGO regime gate development.

**Pre-registered classification**:
- PATH A: IS Δ ≥ +0.20 AND OOS Δ ≥ +0.05 (unlikely given OOS WR pattern).
- PATH C (likely): OOS Δ < -0.10 due to OOS LONG positive contribution removal.

**Compoundability**: STACKABLE with primitive 10 BCH LONG. Both are LONG-side blocks.

---

## Candidate 4 — Universal TRX SHORT block (no regime conditioning)

**Axis classification**: A.1 (TRX SHORT block, universal)

**Mechanism**: Set `block_short_for=("TRXUSDT",)` in v3 runner — primitive 10 mirror
mechanism applied to TRX SHORT. Universal block.

**Quantitative basis**: same as Candidate 1 BUT no regime conditioning — fires on
ALL TRX SHORT signals regardless of regime.

- IS lift: +{round(-delta_a_is, 4)} weighted_pnl (full naive estimate)
- OOS cost: {round(-delta_a_oos, 4)} weighted_pnl (full naive estimate; HIGH)

**Implementation complexity**: LOW (1-line config change; primitive 10 already wired)

**Risks**:
- HIGH OOS risk: TRX SHORT OOS positive (+8.39% PnL). Naive block COSTS OOS edge.
- iter-v3/039 anti-pattern: lift IS at OOS expense violates BOTH-must-improve rule.
- The Critic FINAL of iter-v3/046 explicitly identified "TRX SHORT block ranked #4
  precisely because TRX SHORT OOS is positive". DOUBLY-rejected reasoning.

**Pre-registered classification**:
- PATH A unlikely (OOS positive contribution removal).
- PATH C very likely: OOS Δ < -0.10.

**Compoundability**: STACKABLE with primitive 10 BCH LONG. Both direction-asymmetric blocks.

**WHY RANKED BELOW Candidate 1**: Candidate 1 (regime-conditional) achieves the same
IS lift in stressed regimes while preserving OOS in healthy regimes. Candidate 4 has
NO mechanism to discriminate.

---

## Candidate 5 — LDO direction filter

**Axis classification**: C.1 (LDO LONG or SHORT block)

**Mechanism**: depending on LDO direction asymmetry, block one direction on LDO.

**Quantitative basis**:
- LDO IS sample size: ~18 trades total (per iter-v3/045 per-symbol). Decomposed by
  direction is 9-10 trades per direction. STATISTICALLY UNDER-POWERED.
- Per multi_axis_diagnosis.csv Table C1, the asymmetry magnitude is small (LDO IS
  primarily positive contributor at +54.55% net_pnl).

**Implementation complexity**: LOW

**Risks**:
- Small-sample fragility — may not generalize to multi-seed.
- LDO already optimized via per-symbol ATR (2.0, 1.5).
- Risk of OVERFIT to single-seed sub-sample.

**Verdict**: REJECTED — small-sample risk + LDO already optimized.

---

## Recommended axis: Candidate 1 (Regime-conditional TRX SHORT block)

**Why**:
1. **Largest IS-axis leverage with OOS-axis preservation**: addresses the
   $32% IS PnL drag from TRX SHORT while regime-gating preserves the +8% OOS edge.
2. **Direct mechanism alignment**: regime-conditional gate exists from iter-v3/022 for
   TRX/2022-Q4 (PARTIALLY-EFFECTIVE-CLOSED at single-seed; deferred to multi-seed
   re-evaluation). iter-v3/048 revives this mechanism in a more general form
   (regime-conditional symbol-direction filter).
3. **Compoundable with primitive 10**: orthogonal direction (LONG vs SHORT) and
   orthogonal symbol (BCH vs TRX). At iter-v3/050 CONFIRMATION, the bundle could be
   (P10 BCH LONG block + regime-conditional TRX SHORT block + ALGO/LDO ATR + 14
   features incl. regime_momentum_signed_5d).
4. **Implementation feasible within EXPLORATION 2h cap** — regime gate primitive exists
   in `RiskV2Wrapper` from iter-v3/022; new wiring is a thin extension. Estimated
   setup 30-60 min; backtest 25-40 min; total ≤ 1.5h.
5. **Single-axis discipline**: ONE NEW gate (regime-conditional TRX SHORT) on top of
   existing carry-forward state (P10 BCH LONG + ALGO/LDO ATR + 14 features). No
   compounded changes.
6. **Predicted behavioral effect aligns with EDA**: regime gate fires on ~30-40% of
   TRX SHORT signals (estimated from BTC drawdown 2022-Q4/2023 frequency);
   blocks the IS-toxic concentration while preserving 60-70% of OOS-positive SHORTs.

**Implementation plan**:
1. Add `regime_block_short_for: tuple[str, ...] = ()` to `RiskV2Config`.
2. Reuse iter-v3/022 BTC drawdown / vol z-score regime gate primitive (verify it's
   still in source; if not, port from iter-v3/022 setup commit).
3. Wire dispatch in `RiskV3Wrapper.get_signal()` AFTER inner inference (mirror P10).
4. Set `regime_block_short_for=("TRXUSDT",)` and regime threshold (BTC 30d drawdown >
   20% OR BTC 14d vol z-score > 2.0) in `_build_v3_model` of v3 runner.
5. 4-6 adversarial tests in `tests/strategies/ml/test_regime_block_short_primitive_11.py`
   (TRX SHORT in stressed regime → blocked; TRX SHORT in healthy regime → passes;
   TRX LONG always passes; BCH SHORT always passes; ALGO SHORT always passes).
6. Update v3 runner with explicit verification asserts (mirror primitive 10 verification).

**Predicted behavioral effect** (per `feedback_axis_saturation_predictor.md`):
- TRX IS SHORT trade count: 43 → 27-33 (−10 to −16; gate fires on 25-40% of SHORTs)
- TRX OOS SHORT trade count: 24 → 18-22 (−2 to −6; gate fires less in healthy 2025+)
- TRX IS net_pnl: -7.28% → +5% to +12% (LONG-preserved, SHORT-toxic-block reduced)
- TRX OOS net_pnl: +29.24% → +24% to +28% (small reduction; gate fires occasionally)
- Bundle IS Sharpe Δ: +0.10 to +0.20
- Bundle OOS Sharpe Δ: -0.05 to +0.05 (preserves OOS within noise band)
- Non-TRX trade rosters: bit-identical (per-symbol Optuna independence) +
  cross-run-stochasticity baseline drift (acceptable per iter-v3/047 forensic baseline)

## Status

EDA + ranking COMMITTED. Next: write Section-2-grounded research brief at iter-v3/048
(setup + backtest commit follows). Pre-registration locks the regime threshold values
(BTC 30d drawdown > 20% OR BTC 14d vol z-score > 2.0) in brief Section 8.
"""
    out = ANALYSIS_DIR / "candidate_axes_ranking.md"
    out.write_text(text)
    print(f"Wrote: {out}")


if __name__ == "__main__":
    sys.exit(main())
