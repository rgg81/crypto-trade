"""iter-v1/017 — Phase 1 EDA: wall-clock estimate per skill `4cb8972` mandate.

Phase 5.5 BLOCKS if Section 3.6 missing wall-clock estimate OR margin < 20%.

/016 empirical anchor (engineering_report.md §6, diary §LESSON #5):
- 5-sym universe (BTC+ETH+LINK+LTC+DOT) — 4 models A/C/D/E
- ENSEMBLE_SIZE=3 inner seeds, n_trials=18
- V1_FEATURE_COLUMNS_PRUNED (40 features), 8h candles
- Observed wall-clock: ~50 minutes total
- Margin: 75% (against 2h EXPLORATION cap)

/017 expansion options:
- 6-sym (add SOL as Model F): scale ~6/5 = +20% → ~60 min
- 7-sym (add SOL + XRP as F + G): scale ~7/5 = +40% → ~70 min

Both fit comfortably within the 2h cap with adequate margin.

Pre-emptive compression scenarios (if QE pre-flight indicates overshoot):
- n_trials 18 → 15: ~17% saving → from ~70min to ~58min for 7-sym
- Drop XRP, keep only SOL: 6-sym only → ~60min

This script:
1. Computes scaled wall-clock predictions for 6-sym and 7-sym scenarios.
2. Validates ≥20% margin against 2h cap for the selected configuration.
3. Documents the chosen configuration with explicit margin calculation.

Writes:
- wall_clock_scenarios.csv — all scenarios with margins
"""

from __future__ import annotations

from pathlib import Path

import pandas as pd

REPO_ROOT = Path("/home/roberto/crypto-trade/.worktrees/quant-research")
OUT_DIR = REPO_ROOT / "analysis" / "iteration_v1-017"
OUT_DIR.mkdir(parents=True, exist_ok=True)

# /016 empirical anchor
ANCHOR_MIN = 50.0          # observed wall-clock at /016
ANCHOR_SYMBOLS = 5
ANCHOR_N_TRIALS = 18
ANCHOR_ENSEMBLE_SIZE = 3
ANCHOR_FEATURES = 40

EXPLORATION_CAP_MIN = 120  # 2h cap


def predict_wall_clock(
    symbols: int,
    n_trials: int = ANCHOR_N_TRIALS,
    ensemble_size: int = ANCHOR_ENSEMBLE_SIZE,
    features: int = ANCHOR_FEATURES,
) -> float:
    """Linear scaling from /016 50-min anchor.

    Scaling factors:
    - Symbols: linear (each new symbol = additional model)
    - n_trials: ~linear
    - ensemble_size: linear (sub-linear in practice; conservative = linear)
    - features: ~linear up to feature-count saturation (PRUNED-set <50 = OK)
    """
    sym_factor = symbols / ANCHOR_SYMBOLS
    trial_factor = n_trials / ANCHOR_N_TRIALS
    seed_factor = ensemble_size / ANCHOR_ENSEMBLE_SIZE
    feat_factor = features / ANCHOR_FEATURES
    return ANCHOR_MIN * sym_factor * trial_factor * seed_factor * feat_factor


def margin_pct(predicted_min: float) -> float:
    """Margin against EXPLORATION_CAP_MIN."""
    return (EXPLORATION_CAP_MIN - predicted_min) / EXPLORATION_CAP_MIN * 100


def main() -> None:
    print(f"/016 empirical anchor: {ANCHOR_MIN}min @ {ANCHOR_SYMBOLS}sym × {ANCHOR_N_TRIALS}trials × {ANCHOR_ENSEMBLE_SIZE}seeds × {ANCHOR_FEATURES}features")
    print(f"EXPLORATION cap: {EXPLORATION_CAP_MIN}min (2h)")
    print(f"Minimum required margin: 20%")
    print()

    scenarios = [
        # (label, symbols, n_trials, ensemble_size, features)
        ("/016 baseline-anchor", 5, 18, 3, 40),
        ("/017 PRIMARY 6-sym (BTC+ETH+LINK+LTC+DOT+SOL)", 6, 18, 3, 40),
        ("/017 ALT 6-sym (+XRP instead of SOL)", 6, 18, 3, 40),
        ("/017 ALT 7-sym (+SOL +XRP)", 7, 18, 3, 40),
        ("/017 COMPRESSED 7-sym (-3 n_trials)", 7, 15, 3, 40),
        ("/017 COMPRESSED 6-sym (-3 n_trials)", 6, 15, 3, 40),
    ]

    rows = []
    for label, sym, ntr, ens, feat in scenarios:
        predicted = predict_wall_clock(sym, ntr, ens, feat)
        margin = margin_pct(predicted)
        rows.append(
            {
                "scenario": label,
                "symbols": sym,
                "n_trials": ntr,
                "ensemble_size": ens,
                "features": feat,
                "predicted_min": round(predicted, 1),
                "predicted_hr": round(predicted / 60, 2),
                "margin_pct": round(margin, 1),
                "passes_20pct_margin": margin >= 20.0,
                "passes_cap": predicted <= EXPLORATION_CAP_MIN,
            }
        )
    wc_df = pd.DataFrame(rows)
    wc_df.to_csv(OUT_DIR / "wall_clock_scenarios.csv", index=False)
    print("=== Wall-Clock Scenarios ===")
    print(wc_df.to_string(index=False))
    print()

    # CHOSEN configuration
    print("=== CHOSEN: /017 PRIMARY 6-sym (+SOL) ===")
    chosen_min = predict_wall_clock(6, 18, 3, 40)
    chosen_margin = margin_pct(chosen_min)
    print(f"  Predicted wall-clock: {chosen_min:.1f} min ({chosen_min / 60:.2f} hr)")
    print(f"  Margin against 2h cap: {chosen_margin:.1f}%")
    print(f"  Passes ≥20% margin requirement: {chosen_margin >= 20.0}")
    print(f"  Passes 2h cap: {chosen_min <= EXPLORATION_CAP_MIN}")
    print()

    # Sub-linear correction sanity check (per /016 LESSON #5)
    # /016 anchor was OVER-conservative: predicted 1.50-1.75h vs observed 50min.
    # Sub-linear "warmup shared across seeds" correction = 0.7×
    # Apply to 6-sym predictions for robustness check
    print("=== Sub-linear sanity check (per /016 LESSON #5) ===")
    print(f"  /016 prediction band: 90-105 min (over-conservative)")
    print(f"  /016 observed: 50 min (2× faster than prediction)")
    print(f"  → Linear scaling above OVER-estimates by factor ~2×")
    sub_linear = chosen_min * 0.7
    sub_linear_margin = margin_pct(sub_linear)
    print(f"  Sub-linear prediction for 6-sym: {sub_linear:.1f} min ({sub_linear / 60:.2f} hr)")
    print(f"  Sub-linear margin: {sub_linear_margin:.1f}%")
    print()
    print("  Linear scaling provides 50% margin (conservative);")
    print("  Sub-linear realistic estimate provides 65% margin.")
    print("  BOTH well above 20% Phase 5.5 floor.")

    print(f"\nOutputs written to {OUT_DIR}/")


if __name__ == "__main__":
    main()
