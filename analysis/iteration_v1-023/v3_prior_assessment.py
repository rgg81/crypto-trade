"""iter-v1/023 — v3 Funding-Axis Prior Assessment.

This script enumerates the v3 funding-axis catalog evidence (4 NEGATIVE/INERT
data points) and contrasts each axis with v1's structurally different setup
to identify which v3 failure modes apply transferable AND which do not.

The output funding_v3_prior_assessment.csv is a key input to the Phase 5 brief
Section 2 IS-only evidence + Section 5 verdict-priors calibration.

Each v3 row is annotated with:
- failure_mode: what specifically went INERT (importance rank, gain share, OOS dissociation)
- v1_structural_difference: what about v1's setup may break the v3 pattern
- transferable_risk_level: HIGH / MEDIUM / LOW for v1 retesting
"""

from __future__ import annotations

from pathlib import Path

import pandas as pd

OUT_DIR = Path(__file__).resolve().parent

rows = [
    {
        "v3_iter": "iter-v3/019",
        "v3_date": "2026-05-07",
        "v3_axis": "per-symbol funding_rate_zscore_30 (rolling 30-cycle z-score), 14th feature",
        "v3_optuna_budget": "n_trials=10, --seeds 1",
        "v3_ensemble_size": "ENSEMBLE_SIZE=3",
        "v3_universe": "BCH+LDO+TRX (3-symbol per-symbol models)",
        "v3_feature_count_pre": 13,
        "v3_feature_count_post": 14,
        "v3_is_sharpe_delta": +0.78,
        "v3_oos_sharpe_delta": "+0.7847 (informational, 91 trades < 130 floor)",
        "v3_verdict": "EXPLORATION-PROMISING-INERT (Falsifier 4)",
        "v3_failure_mode": "importance rank 14/14 LDO+TRX+Portfolio; BCH rank 10/14 (Q3, not top-half); model did NOT learn the feature; IS lift attributed to hyperparam/colsample noise on 14-col surface",
        "v3_root_cause": "n_trials=10 single-seed EXPLORATION budget INSUFFICIENT to learn NEW single-feature signal; established as universal pattern with iter-v3/015 microstructure (also rank 14/14 at n_trials=10)",
        "v1_structural_difference": "v1 uses ENSEMBLE_SIZE=3 + n_trials=18 at EXPLORATION (v1 EXPLORATION budget is HIGHER than v3 by 80%); v1 also uses POOL Model A (joint BTC+ETH 2-symbol training); pool model has 2× rows → better gradient signal per Optuna step than per-symbol",
        "transferable_risk_level": "MEDIUM",
        "v1_mitigation": "n_trials=18 above n_trials=10 INERT-pattern threshold; pool Model A trains on 2× data; per `feedback_v3_inert_features_at_higher_budget.md` BUT v1 budget is higher",
    },
    {
        "v3_iter": "iter-v3/023",
        "v3_date": "2026-05-08",
        "v3_axis": "per-symbol funding_rate_zscore_30 at HIGHER n_trials=35",
        "v3_optuna_budget": "n_trials=35, --seeds 1",
        "v3_ensemble_size": "ENSEMBLE_SIZE=3",
        "v3_universe": "BCH+LDO+TRX (3-symbol per-symbol models)",
        "v3_feature_count_pre": 13,
        "v3_feature_count_post": 14,
        "v3_is_sharpe_delta": "n/a (informational)",
        "v3_oos_sharpe_delta": -1.07,
        "v3_verdict": "EXPLORATION-NEGATIVE (INERT feature actively HARMS at higher Optuna budget)",
        "v3_failure_mode": "INERT feature at rank 14/14 actively destroys OOS Sharpe when Optuna budget increases — larger search space lets Optuna overfit IS to noise INCLUDING the INERT 14th feature, corresponding to OOS-suboptimal regions",
        "v3_root_cause": "Drop INERT features after 1 EXPLORATION verdict; do not retest at higher budget; codified `feedback_v3_inert_features_at_higher_budget.md`",
        "v1_structural_difference": "v1 may inherit this rule directly — if v1/023 z30 produces rank 14/14 (or equivalent bottom-quartile), retesting at higher n_trials in /024 is FORBIDDEN; brief Section 11.7 conditional roadmap must encode this constraint",
        "transferable_risk_level": "HIGH (rule is universal, applies to any track)",
        "v1_mitigation": "Falsifier #1 explicitly checks importance rank; if INERT-by-importance at /023, NO retest at higher budget — pivot to drawdown brake (Path Forward #2) or open-interest (cross-feature-family)",
    },
    {
        "v3_iter": "iter-v3/024",
        "v3_date": "2026-05-08",
        "v3_axis": "btc_funding_rate_zscore_30 cross-asset BROADCAST (drop per-sym, add BTC funding to all 3 sym models)",
        "v3_optuna_budget": "n_trials=35, --seeds 1",
        "v3_ensemble_size": "ENSEMBLE_SIZE=3",
        "v3_universe": "BCH+LDO+TRX (3-symbol per-symbol models)",
        "v3_feature_count_pre": 13,
        "v3_feature_count_post": 14,
        "v3_is_sharpe_delta": "+0.60 vs anchor (lottery on INERT 14th feature)",
        "v3_oos_sharpe_delta": -1.20,
        "v3_verdict": "EXPLORATION-NEGATIVE clean (3rd-worst single-seed; OOS MaxDD 49.97%)",
        "v3_failure_mode": "BTC funding rank 14/14 BCH+LDO+Portfolio + 9/14 TRX — same INERT pattern; INERT-OVERFIT confirmed across funding family",
        "v3_root_cause": "BTC funding broadcast does not break INERT pattern; cross-asset reframing of same z-score feature inherits same model-learning failure",
        "v1_structural_difference": "v1 has BTC + ETH IN-UNIVERSE (already part of pool Model A); BTC funding signal is implicitly available via BTC's own kline features already; broadcasting BTC funding to LINK/LTC/DOT (Model C/D/E) would be a new cross-asset feature — but the same v3/024 INERT pattern likely applies; v1/023 brief should NOT include BTC-funding-broadcast feature (per-symbol only)",
        "transferable_risk_level": "HIGH (reinforces single-feature-z-score family INERT-pattern)",
        "v1_mitigation": "v1/023 brief uses PER-SYMBOL funding-rate z-score only (not cross-asset broadcast); BTC's own funding is its own pool-Model-A feature input — no need for cross-asset broadcast variant",
    },
    {
        "v3_iter": "iter-v3/082",
        "v3_date": "2026-05-16",
        "v3_axis": "4-feature funding FAMILY (funding_sign_persist_9, funding_momentum_3, funding_accel_3, funding_price_divergence_6)",
        "v3_optuna_budget": "n_trials=35, --seeds 3",
        "v3_ensemble_size": "ENSEMBLE_SIZE=3 multi-seed",
        "v3_universe": "BCH+LDO+TRX (3-symbol per-symbol models)",
        "v3_feature_count_pre": 14,
        "v3_feature_count_post": 18,
        "v3_is_sharpe_delta": -0.0118,
        "v3_oos_sharpe_delta": +1.2081,
        "v3_verdict": "EXPLORATION-SUSPICIOUS-OOS-DOMINANT",
        "v3_failure_mode": "4 funding features rank 15/16/17/18 of 18 by importance share (combined 9.90%, below 5.56% uniform-parity baseline averaging 2.475% each); INERT-BY-IMPORTANCE confirmed at family level too; OOS +1.21 lift is Optuna-perturbation lottery on uninformative dimensions",
        "v3_root_cause": "literature-grounded 4-channel family construction did NOT break the single-z-score INERT pattern; the model fundamentally does not learn funding-rate features across 4-channel construction (sign-persist / momentum / accel / divergence); v3 funding axis CLOSED as 4-data-point STRUCTURAL VERDICT",
        "v1_structural_difference": "v3 closing rationale: '3-symbol BCH/LDO/TRX universe gives the family insufficient training data per fit + the model fundamentally does not load funding-rate features'; v1's pool Model A (BTC+ETH) provides 2× rows for joint fit AND LINK/LTC/DOT have ~30-50% more training data than BCH/LDO/TRX (more historical kline depth — funding starts 2020-01 for LINK/LTC vs 2021+ for LDO); v1 ALSO has the methodology-substrate from /021 showing basin-level (not feature-level) cohort effects — funding may act as a basin-shift trigger even at low importance share",
        "transferable_risk_level": "HIGH (4-data-point structural verdict against funding family; multi-channel family construction did not break pattern)",
        "v1_mitigation": "v1/023 brief: (1) PRE-REGISTER importance-rank floor as Falsifier #1 (rank ≥ 15/42 on ≥ 2 of 5 symbols → INERT); (2) ACKNOWLEDGE v3 4-point structural verdict as the binding prior for verdict-class priors (modal INERT 50%); (3) STRUCTURAL HYPOTHESIS for v1 difference: pool Model A's joint loss surface may capture funding-rate signal via cross-cohort interaction (LightGBM trees can split on funding-rate*symbol-dummy effectively when 2 symbols pooled), which 3-symbol per-symbol v3 architecture explicitly cannot",
    },
]

df = pd.DataFrame(rows)
out_path = OUT_DIR / "funding_v3_prior_assessment.csv"
df.to_csv(out_path, index=False)

print(f"v3 funding-axis prior catalog: {len(rows)} data points")
print(f"  ALL 4 NEGATIVE/INERT by importance rank")
print(f"  Output: {out_path}")
print()
print("Summary of transferable risks:")
print(f"  HIGH-risk transferable patterns: {sum(r['transferable_risk_level'] == 'HIGH' for r in rows)}")
print(f"  MEDIUM-risk transferable patterns: {sum(r['transferable_risk_level'] == 'MEDIUM' for r in rows)}")
print()
print("Key v1 mitigations encoded across the 4 rows:")
for r in rows:
    print(f"  {r['v3_iter']}: {r['v1_mitigation'][:120]}...")
