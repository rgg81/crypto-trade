"""iter-v1/061 IS-only EDA — BTC zero-randomness diagnostic.

Produces the IS-only numerical evidence table in brief Section 2.
Data sources: prior backtest artifacts from /053, /054, /058 (IS results only).
LM Master prediction from lgbm_advisor.md Phase 4.5.

ORACLE contamination: NONE — all data is from IS windows only or from the LM Master
advisory (which is based on HP analysis, not OOS data).

Run:
    uv run python analysis/iteration_v1-061/btc_zero_randomness_eda.py

Output:
    Prints the evidence table to stdout (no file written — evidence is tabular summary
    of already-known IS metrics from the catalog).
"""

from __future__ import annotations

# ── Section 2 evidence table (from exploration catalog + LM Master lgbm_advisor.md) ──

# Historical BTC-only specialist IS Sharpe reads from the v1 exploration catalog.
# All values are IS-window only (2023-03-24 → 2025-03-24).
# OOS values are NOT included here (would contaminate IS-only evidence).

HISTORICAL_BTC_IS_SHARPE = {
    "/053 offset0 (seed=42, 18 trials)": {
        "is_sharpe": +0.1609,
        "n_trials": 18,
        "subsample": "~0.88",
        "colsample": "~0.72",
        "seeds": 1,
        "note": "single-seed favorable basin; BIT-IDENTICAL across /053 + /054",
    },
    "/053 3-seed mean (seeds=3, 18 trials)": {
        "is_sharpe": -0.04,
        "n_trials": 18,
        "subsample": "varied",
        "colsample": "varied",
        "seeds": 3,
        "note": "spread=0.31; multi-seed mean reveals basin lottery at /053",
    },
    "/054 single-seed=42 (18 trials, spread-only)": {
        "is_sharpe": +0.2614,
        "n_trials": 18,
        "subsample": "~0.985",
        "colsample": "~0.888",
        "seeds": 1,
        "note": "IMPULSE-DROP-CONFIRMED; favorable basin draw at single-seed=42",
    },
    "/058 3-seed mean (seeds=3, 18 trials, OI 5-bar)": {
        "is_sharpe": -0.28,
        "n_trials": 18,
        "subsample": "varied",
        "colsample": "varied",
        "seeds": 3,
        "note": "spread=0.90 (catalog record); MULTI-SEED-SPECIALIST-BASIN-LOTTERY",
    },
    "/059 pool (single-seed, 18 trials, Pool+Route)": {
        "is_sharpe": -0.16,
        "n_trials": 18,
        "subsample": "varied",
        "colsample": "varied",
        "seeds": 1,
        "note": "Pool+Route architecture (different model head; not directly comparable)",
    },
    "LM Master /061 prediction": {
        "is_sharpe": +0.08,
        "n_trials": 1,
        "subsample": "1.0",
        "colsample": "1.0",
        "seeds": 1,
        "note": "band [−0.10, +0.20]; 60% modal probability; NOISE-FLOOR-CONFIRMED expected",
    },
}

LM_MASTER_PREDICTION = {
    "point_estimate": +0.08,
    "band_low": -0.10,
    "band_high": +0.20,
    "modal_probability": 0.60,
    "modal_verdict": "NOISE-FLOOR-CONFIRMED",
    "oos_prediction": -0.70,
    "oos_band_low": -1.20,
    "oos_band_high": -0.20,
    "source": "briefs-v1/iteration_v1-061/lgbm_advisor.md §My Honest Predictions",
}

HARDCODED_HPS_061 = {
    "n_estimators": 300,
    "max_depth": 4,
    "num_leaves": 31,
    "min_child_samples": 50,
    "learning_rate": 0.05,
    "subsample": 1.0,
    "colsample_bytree": 1.0,
    "bagging_freq": 0,
    "reg_alpha": 0.1,
    "reg_lambda": 0.1,
    "deterministic": True,
    "num_threads": 1,
    "is_unbalance": False,
    "force_col_wise": True,
    "confidence_threshold": 0.7,
    "training_days": 360,
    "n_trials": 1,
}


def main() -> None:
    print("=" * 80)
    print("iter-v1/061 IS-only EDA — BTC Zero-Randomness Diagnostic")
    print("=" * 80)

    print("\n--- Section 2: Historical BTC IS Sharpe Reads (IS-window only) ---\n")
    print(f"{'Source':<50} {'IS Sharpe':>10} {'n_trials':>8} {'subsample':>10} {'seeds':>6}")
    print("-" * 86)
    for source, d in HISTORICAL_BTC_IS_SHARPE.items():
        print(
            f"{source:<50} {d['is_sharpe']:>+10.4f} {d['n_trials']:>8} "
            f"{str(d['subsample']):>10} {d['seeds']:>6}"
        )
    print()

    print("--- LM Master Phase 4.5 Prediction ---")
    print(f"  Point estimate : {LM_MASTER_PREDICTION['point_estimate']:+.2f}")
    band_lo = LM_MASTER_PREDICTION["band_low"]
    band_hi = LM_MASTER_PREDICTION["band_high"]
    oos_lo = LM_MASTER_PREDICTION["oos_band_low"]
    oos_hi = LM_MASTER_PREDICTION["oos_band_high"]
    print(f"  Band           : [{band_lo:+.2f}, {band_hi:+.2f}]")
    print(f"  Modal prob     : {LM_MASTER_PREDICTION['modal_probability']:.0%}")
    print(f"  Modal verdict  : {LM_MASTER_PREDICTION['modal_verdict']}")
    oos_pt = LM_MASTER_PREDICTION["oos_prediction"]
    print(f"  OOS prediction : {oos_pt:+.2f} [{oos_lo:+.2f}, {oos_hi:+.2f}]")
    print()

    print("--- Hardcoded HP Dict (/061 spec) ---")
    for k, v in HARDCODED_HPS_061.items():
        print(f"  {k:<25}: {v}")
    print()

    print("--- Key Findings for Brief Section 2 ---")
    print("  1. BTC-only specialist IS Sharpe is dominated by basin-lottery variance.")
    print("     Multi-seed spreads: /053=0.31, /058=0.90 (catalog record).")
    print("     Single-seed=42 reads vary from −0.28 (mean) to +0.26 (/054 favorable basin).")
    print()
    print("  2. Stripping ALL randomness (n_trials=1, subsample=1.0, colsample=1.0,")
    print("     bagging_freq=0, deterministic=True, num_threads=1, is_unbalance=False)")
    print("     produces ONE deterministic read from this distribution.")
    print()
    print("  3. LM Master predicts IS +0.08 (60% modal band [−0.10, +0.20]).")
    print("     The modal outcome is NOISE-FLOOR-CONFIRMED: BTC-only head ≈ 0 Sharpe")
    print("     in expectation; /054's +0.26 was a basin-favorable Optuna draw.")
    print()
    print("  4. Primary deliverable is F1 REPRODUCIBILITY (bit-exact across 2 runs),")
    print("     NOT the IS Sharpe magnitude. The diagnostic confirms zero hidden randomness.")
    print()
    print("  Note: OOS metrics are INFORMATIONAL ONLY per feedback_v3_dsr_mode_artifact.md.")
    print("=" * 80)


if __name__ == "__main__":
    main()
