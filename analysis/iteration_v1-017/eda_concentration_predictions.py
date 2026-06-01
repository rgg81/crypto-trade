"""iter-v1/017 — Phase 1 EDA: per-symbol PnL concentration & SOL contribution predictions.

Per /016 LM Master Phase 7.4 §6 + Critic Path Forward #1:
- /017 must predict LINK concentration reduction via denominator dilution
- /017 must pre-register a CAUTIOUS expected per-symbol contribution for SOL
  (no strong directional claim per /015 + /016 LM Master FLAT prior rule)

This script:
1. Reads baseline per-symbol concentration (LINK=137.66%, BTC=133.38%, etc).
2. Predicts dilution-based concentration changes for 6-sym and 7-sym universes.
3. Computes a CAUTIOUS SOL/XRP forward expectation using cross-symbol return
   stats only (no labeling, no features) — purely structural.
4. Compares SOL's volatility profile to LINK/DOT (highest baseline contributors)
   to assess whether SOL can absorb LINK-like edge if model-arch handles it.

IS-only data only: uses baseline reports + IS-window log-returns.

Writes:
- concentration_prediction.csv — predicted LINK share under dilution
- sol_xrp_forward_expectation.csv — CAUTIOUS per-symbol prediction
- volatility_profile_comparison.csv — SOL/XRP vs LINK/DOT
"""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

REPO_ROOT = Path("/home/roberto/crypto-trade/.worktrees/quant-research")
OUT_DIR = REPO_ROOT / "analysis" / "iteration_v1-017"
OUT_DIR.mkdir(parents=True, exist_ok=True)
OOS_CUTOFF_DATE = "2025-03-24"


# Baseline per-symbol OOS attribution (from BASELINE_V1.md)
BASELINE_OOS = {
    "LINKUSDT": 34.23,
    "BTCUSDT": 33.17,
    "ETHUSDT": 2.75,
    "DOTUSDT": 1.96,
    "LTCUSDT": -47.25,
}
BASELINE_OOS_TOTAL = 24.87  # sum from BASELINE_V1.md

# Baseline per-symbol IS attribution (from BASELINE_V1.md)
BASELINE_IS = {
    "LINKUSDT": 72.06,
    "DOTUSDT": 26.62,
    "LTCUSDT": 3.27,
    "ETHUSDT": -13.70,
    "BTCUSDT": -37.28,
}
BASELINE_IS_TOTAL = 50.98


def load_klines(symbol: str) -> pd.DataFrame:
    """Load 8h klines."""
    path = REPO_ROOT / "data" / symbol / "8h.csv"
    df = pd.read_csv(path)
    df["open_dt"] = pd.to_datetime(df["open_time"], unit="ms", utc=True)
    return df


def compute_log_returns(df: pd.DataFrame, is_only: bool = True) -> pd.Series:
    df = df.copy().sort_values("open_time").reset_index(drop=True)
    if is_only:
        cutoff_ms = int(pd.Timestamp(OOS_CUTOFF_DATE, tz="UTC").timestamp() * 1000)
        df = df[df["open_time"] < cutoff_ms]
    return np.log(df["close"].astype(float) / df["close"].shift(1).astype(float)).dropna()


def main() -> None:
    # ---------- Table 1: concentration prediction under dilution ----------
    print("=== Table 1: Per-Symbol Concentration Predictions ===")

    # LINK current share = 137.66% (large because denominator small)
    rows = []
    for sol_contrib in [-15, -10, -5, 0, 5, 10, 15]:
        # 6-sym universe (5 baseline + SOL)
        new_total = BASELINE_OOS_TOTAL + sol_contrib
        link_share = BASELINE_OOS["LINKUSDT"] / new_total * 100 if new_total != 0 else float("nan")
        btc_share = BASELINE_OOS["BTCUSDT"] / new_total * 100 if new_total != 0 else float("nan")
        eth_share = BASELINE_OOS["ETHUSDT"] / new_total * 100 if new_total != 0 else float("nan")
        ltc_share = BASELINE_OOS["LTCUSDT"] / new_total * 100 if new_total != 0 else float("nan")
        sol_share = sol_contrib / new_total * 100 if new_total != 0 else float("nan")

        rows.append(
            {
                "universe_size": 6,
                "SOL_OOS_contrib_pct": sol_contrib,
                "new_portfolio_OOS_total": round(new_total, 2),
                "LINK_share_pct": round(link_share, 2),
                "BTC_share_pct": round(btc_share, 2),
                "ETH_share_pct": round(eth_share, 2),
                "LTC_share_pct": round(ltc_share, 2),
                "SOL_share_pct": round(sol_share, 2),
                "LINK_share_delta_pp": round(link_share - 137.66, 2),
            }
        )
    concentration_df = pd.DataFrame(rows)
    concentration_df.to_csv(OUT_DIR / "concentration_prediction.csv", index=False)
    print(concentration_df.to_string(index=False))
    print()
    print(f"  Baseline LINK share: 137.66% (denominator-bound because total=24.87)")
    print(f"  At SOL=0 contribution: LINK share UNCHANGED (denominator unchanged)")
    print(f"  At SOL=+10: LINK share drops to {BASELINE_OOS['LINKUSDT'] / (BASELINE_OOS_TOTAL + 10) * 100:.2f}% (Δ -39pp)")
    print()

    # ---------- Table 2: SOL/XRP forward expectation (CAUTIOUS — per FLAT prior) ----------
    print("=== Table 2: SOL/XRP Forward Expectation (CAUTIOUS — FLAT prior) ===")
    # The FLAT prior rule from /015/016 LM Master means: we cannot make strong
    # directional claims at single-seed EXPLORATION budget. The PRIOR is split
    # roughly 33/33/34 across PROMISING/NULL/NEGATIVE for verdict-class.
    #
    # For SOL/XRP per-symbol CONTRIBUTION, we use only structural anchors:
    # - SOL has highest std in universe → expect higher trade-magnitude variance
    # - SOL/XRP have lowest BTC correlation → naive diversification benefit
    # - SOL/XRP have NOT been seen by v1 models — no learned regime
    # - Pure FLAT prior on direction at v1 EXPLORATION budget
    rows = []
    candidate_priors = [
        {"symbol": "SOLUSDT", "abs_p95_pct": 7.52, "ret_std_pct": 3.68, "btc_corr": 0.62},
        {"symbol": "XRPUSDT", "abs_p95_pct": 5.99, "ret_std_pct": 3.04, "btc_corr": 0.59},
    ]
    for cand in candidate_priors:
        # CAUTIOUS bands: contribution within ±20pp of zero, FLAT prior, no strong tilt
        # The lower-vol candidate (XRP) → expect tighter contribution band
        # The higher-vol candidate (SOL) → expect wider contribution band
        symbol = cand["symbol"]
        # CAUTIOUS — span ±2σ of an assumed-zero-mean IS-volatility-scaled distribution
        # NOT a prediction; an outer bound for falsifier
        bound = cand["abs_p95_pct"] * 6.0  # ~6 trade magnitude × p95 abs move
        rows.append(
            {
                "symbol": symbol,
                "is_p95_abs_return_pct": cand["abs_p95_pct"],
                "is_ret_std_pct": cand["ret_std_pct"],
                "is_corr_vs_BTC": cand["btc_corr"],
                "FLAT_prior_expected_OOS_PnL_pct": 0.0,
                "FLAT_prior_falsifier_lower_pct": -bound,
                "FLAT_prior_falsifier_upper_pct": bound,
                "outside_bound_implies": (
                    "anomaly — investigate model fit "
                    "(too negative could be A14-style dead-feed; "
                    "too positive is single-seed lottery)"
                ),
            }
        )
    sol_xrp_df = pd.DataFrame(rows)
    sol_xrp_df.to_csv(OUT_DIR / "sol_xrp_forward_expectation.csv", index=False)
    print(sol_xrp_df.to_string(index=False))
    print()

    # ---------- Table 3: SOL/XRP volatility profile vs LINK/DOT ----------
    print("=== Table 3: Volatility Profile Comparison (SOL/XRP vs LINK/DOT) ===")
    rows = []
    for sym in ["LINKUSDT", "DOTUSDT", "SOLUSDT", "XRPUSDT"]:
        df = load_klines(sym)
        ret = compute_log_returns(df, is_only=True) * 100  # to percent
        rows.append(
            {
                "symbol": sym,
                "role": "baseline" if sym in ("LINKUSDT", "DOTUSDT") else "candidate",
                "is_ret_std_pct": round(ret.std(), 4),
                "is_abs_p95_pct": round(ret.abs().quantile(0.95), 4),
                "is_abs_p99_pct": round(ret.abs().quantile(0.99), 4),
                "is_skew": round(float(ret.skew()), 4),
                "is_kurtosis": round(float(ret.kurtosis()), 4),
            }
        )
    vol_df = pd.DataFrame(rows)
    vol_df.to_csv(OUT_DIR / "volatility_profile_comparison.csv", index=False)
    print(vol_df.to_string(index=False))
    print()
    print("  SOL std (3.68%) > LINK std (3.24%) > DOT std (3.12%) > XRP std (3.04%)")
    print("  SOL p99 abs return (~12-15%) likely highest in expanded universe")
    print("  XRP p99 abs return moderate — XRP is RELATIVELY LOW-VOL candidate")
    print()

    # ---------- Table 4: cross-symbol diversification / new-model-pooling consideration ----------
    print("=== Table 4: Universe Architecture Consideration ===")
    archs = [
        {
            "arch": "Add SOL as ISOLATED Model F (single-symbol)",
            "model_count": 5,  # A (BTC+ETH), C, D, E, F (SOL)
            "scaling_cost_vs_baseline_x": 5.0 / 4.0,  # +25%
            "rationale": "preserves baseline A/C/D/E semantics; SOL gets dedicated model with single-symbol per-symbol Optuna",
        },
        {
            "arch": "Add SOL to POOLED-A (BTC+ETH+SOL)",
            "model_count": 4,  # A_expanded (BTC+ETH+SOL), C, D, E
            "scaling_cost_vs_baseline_x": 1.20,  # pooled model trains on 1.5× rows
            "rationale": "smaller model count; risk of confounding by changing Model A's training distribution",
        },
        {
            "arch": "Single fully-pooled 6-symbol model",
            "model_count": 1,
            "scaling_cost_vs_baseline_x": 1.5,  # pooled trains on 6× rows but 1 Optuna run
            "rationale": "ABANDONS baseline architecture entirely; this is the runner's CURRENT 'else' branch; CONFOUNDS universe axis with model-arch axis",
        },
    ]
    arch_df = pd.DataFrame(archs)
    arch_df.to_csv(OUT_DIR / "architecture_decision.csv", index=False)
    print(arch_df.to_string(index=False))
    print()
    print("  RECOMMENDATION: 'Add SOL as ISOLATED Model F' — preserves /016 baseline")
    print("                  per-model semantics; single-axis universe expansion test.")
    print("                  6-model dispatch precedent: /006 (FILUSDT + MKRUSDT as F,G).")

    print(f"\nOutputs written to {OUT_DIR}/")


if __name__ == "__main__":
    main()
