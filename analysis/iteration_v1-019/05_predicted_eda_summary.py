"""Pre-registered predictions + wall-clock estimate — iter-v1/019 Phase 1 EDA.

Final EDA artifact for the /019 brief. Consolidates:

1. **ETH anchor numbers** (from script 01)
2. **Chosen gate spec** (from script 04) — direction-aware BTC-trend gate at ±8%
3. **Predicted gate fire rate band** for OOS (per Critic A8 anti-pattern guide:
   pre-register expected fire rate at brief Section 4, with bounds outside which
   the gate is malfunctioning).
4. **Wall-clock estimate decomposition**: ETH-only single-symbol model at
   ENSEMBLE_SIZE=3 + n_trials=18 + V1_FEATURE_COLUMNS_PRUNED 40 cols.

Output (committed):
- eda_summary.csv : single-row summary for brief Section 2.X reference
- gate_fire_rate_band.csv : pre-registered IS + OOS fire-rate bands
"""

from __future__ import annotations

from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "analysis" / "iteration_v1-019"
OUT.mkdir(parents=True, exist_ok=True)


def main() -> None:
    # --- Read prior script outputs ---
    eth_anchor = pd.read_csv(OUT / "eth_per_symbol_baseline.csv")
    gate_choice = pd.read_csv(OUT / "gate_final_choice.csv").iloc[0]
    sweep = pd.read_csv(OUT / "gate_threshold_sweep.csv")

    # --- ETH anchor numbers for F1 / F3 ---
    eth_is_sharpe = float(eth_anchor[eth_anchor["split"] == "IS"]["monthly_sharpe"].iloc[0])
    eth_oos_sharpe = float(eth_anchor[eth_anchor["split"] == "OOS"]["monthly_sharpe"].iloc[0])

    # --- Gate spec ---
    gate_threshold_pct = float(gate_choice["threshold_pct"])
    gate_is_skip = float(gate_choice["is_skip_pct"])
    gate_oos_skip_proj = float(gate_choice["oos_skip_pct_PROJECTED"])
    gate_is_lift = float(gate_choice["is_lift_pct"])

    # --- F-AXIS-MECHANISM gate-fire-rate band ---
    # IS expected fire rate: 17.2% chosen at ±8%. Acceptable band [10%, 30%] —
    # gate must fire materially without over-killing. <10% = thresh effectively
    # off; >30% = thresh too aggressive.
    # OOS projected at 17.4% from baseline OOS roster. Multi-seed /027 will
    # have different roster — band [5%, 35%] OOS.
    bands = pd.DataFrame([
        {
            "scope": "IS",
            "expected_fire_rate_pct": gate_is_skip,
            "acceptable_low_pct": 10.0,
            "acceptable_high_pct": 30.0,
            "rationale": (
                "Lower bound 10% — gate is materially active; below this the "
                "threshold is effectively off and the iteration is a knob "
                "tweak in disguise. Upper bound 30% — gate is not over-"
                "killing; above this we starve the cohort of OOS samples and "
                "F8 OOS-trade-count band may breach."
            ),
        },
        {
            "scope": "OOS_PROJECTED",
            "expected_fire_rate_pct": gate_oos_skip_proj,
            "acceptable_low_pct": 5.0,
            "acceptable_high_pct": 35.0,
            "rationale": (
                "Wider band — OOS Optuna trajectory in /019 will differ from "
                "baseline's, so the roster shifts. Lower 5% admits regimes "
                "with few large BTC moves; upper 35% triggers F8 breach if "
                "OOS gated trade count < 25."
            ),
        },
    ])
    bands.to_csv(OUT / "gate_fire_rate_band.csv", index=False)

    # --- Wall-clock estimate ---
    # Anchored to /018: LINK-only (1 sym) at ENSEMBLE_SIZE=3 + n_trials=18 ran
    # ~25 min total per /018 diary "wall-clock ~25 min". ETH-only is the same
    # scale (1 sym, same feature stack, same n_trials, same ensemble size).
    # Add post-hoc gate filter: <1 min (numpy boolean mask on ~150 IS trades +
    # ~50 OOS trades).
    wallclock = pd.DataFrame([{
        "anchor_iter": "iter-v1/018",
        "anchor_wallclock_min": 25,
        "anchor_axis": "LINK-only (1 sym, n_trials=18, ENSEMBLE_SIZE=3)",
        "iter019_axis": "ETH-only + BTC-trend gate (post-hoc filter)",
        "delta_min": 1,
        "rationale_delta": (
            "ETH-only scale identical to LINK-only (1 sym, same config). Gate "
            "is a post-hoc trade-stream filter; adds <1 min (numpy mask + BTC "
            "klines load)."
        ),
        "predicted_total_min": 26,
        "kill_switch_min": 60,
        "cap_min": 120,
        "margin_pct": (120 - 26) / 120 * 100,
    }])
    wallclock.to_csv(OUT / "wallclock_estimate.csv", index=False)

    # --- Consolidated EDA summary ---
    summary = pd.DataFrame([{
        # Anchor numbers
        "f3_anchor_eth_in_pool_is_sharpe": eth_is_sharpe,
        "f1_anchor_eth_in_pool_oos_sharpe": eth_oos_sharpe,
        # Baseline IS / OOS context
        "eth_is_iters_with_pos_pnl": "1/5",
        "eth_oos_iters_with_pos_pnl": "1/5",
        "eth_baseline_oos_net_pnl_pct": 2.7548,
        "eth_baseline_is_net_pnl_pct": -13.6995,
        # Chosen gate
        "gate_indicator": "btc_ret_14d",
        "gate_threshold_pct": gate_threshold_pct,
        "gate_lookback_bars": 42,
        "gate_lookback_days": 14,
        "gate_rule_long": f"skip ETH long entry when BTC 14d return < -{gate_threshold_pct:.0f}%",
        "gate_rule_short": f"skip ETH short entry when BTC 14d return > +{gate_threshold_pct:.0f}%",
        # IS evidence (gate would have lifted baseline ETH IS from -13.70 → +28.77)
        "is_skip_pct_predicted": gate_is_skip,
        "is_pnl_lift_predicted_pct": gate_is_lift,
        # OOS PROJECTED (informational; sized for F8 band)
        "oos_skip_pct_projected": gate_oos_skip_proj,
        # Cross-year stability
        "is_both_halves_positive_lift": True,
        "is_h1_lift_pct": 6.3266,
        "is_h2_lift_pct": 36.1469,
        # Wall-clock
        "wallclock_predicted_min": 26,
        "wallclock_margin_pct": 78,
    }])
    summary.to_csv(OUT / "eda_summary.csv", index=False)

    print("=== iter-v1/019 EDA SUMMARY ===")
    print()
    print(f"F3 anchor (ETH-in-pool IS monthly Sharpe):  {eth_is_sharpe:+.4f}")
    print(f"F1 anchor (ETH-in-pool OOS monthly Sharpe): {eth_oos_sharpe:+.4f}")
    print()
    print(f"Chosen gate: btc_ret_14d direction-aware at ±{gate_threshold_pct:.0f}%")
    print(f"  rule (long):  skip when BTC 14d return < -{gate_threshold_pct:.0f}%")
    print(f"  rule (short): skip when BTC 14d return > +{gate_threshold_pct:.0f}%")
    print(f"  IS skip rate (predicted): {gate_is_skip:.1f}%")
    print(f"  IS PnL lift (additive, predicted): +{gate_is_lift:.2f}%")
    print(f"  Cross-year stability: H1 +{6.33:.2f}%, H2 +{36.15:.2f}% — both positive PASS")
    print()
    print(f"OOS projection (informational, sizes F8 band):")
    print(f"  Skip rate: {gate_oos_skip_proj:.1f}%")
    print(f"  PnL lift (projected): +{7.84:.2f}%")
    print()
    print(f"Wall-clock estimate: 26 min total (margin 78% under 2h cap)")
    print(f"  Anchor: /018 LINK-only 25 min + 1 min gate filter overhead")
    print()
    print(f"Predicted gate fire rates pre-registered at [10%, 30%] IS / [5%, 35%] OOS")


if __name__ == "__main__":
    main()
