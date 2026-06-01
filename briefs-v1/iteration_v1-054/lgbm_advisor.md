# LightGBM Master Advisor — iter-v1/054 — Phase 4.5 (Pre-Design)

## Context Read

- Track: v1; cycle-6 EXP-9/10 — BTC specialist impulse-drop attribution test
- Cohort: BTCUSDT only (BTC-only specialist; unchanged from /052-/053)
- Axis: `feature-pruning` (validation sub-axis — drop impulse, test spread-alone IS contribution)
- Preceding iteration: /053 PARTIAL-CONFIRMED (mean IS Δ +0.8102 vs BTC baseline -0.85;
  multi-seed mean IS Sharpe -0.0398; multi-seed mean OOS Sharpe -0.5981; spread rank stable
  4-10 across all 3 outer seeds; impulse rank > 30 in 3/3 seeds = INERT multi-seed confirmed)
- Triggering mandate: /053 Rec 1 conditional FIRING — PARTIAL-CONFIRMED verdict triggers the
  impulse-drop revaluation per brief Section 3.1 and /053 LM Master Rec 1 (adopted)
- V1_FEATURE_COLUMNS_PRUNED change: DROP `btc_funding_rate_8h_impulse` (48 → 47 cols);
  KEEP `btc_funding_spread_30_90`. Feature computation in funding_v1.py is NOT removed.
- Seeds: --seeds 1 (single-seed=42; EXPLORATION budget); n_trials=18; ENSEMBLE_SIZE=3

---

## Phase 4.5 — LM Master Pre-Design Advisory

### ML Perspective

Removing an INERT feature (importance rank > 30/48 in all 3 outer seeds at /053) from a
LightGBM ensemble has three canonical outcomes:

**(a) No change** — impulse was genuinely dead weight; spread-alone delivers ≥ 95% of /052
single-seed IS lift. Pareto-improvement by simplification only. Most likely given 3/3 INERT
multi-seed confirmation.

**(b) Minor lift** — impulse was crowding split budget away from spread via colsample_bytree
lottery; removing it frees budget for the spread and related top-ranked features. IS Sharpe
exceeds /052 +0.16 anchor. A regression-tax diagnosis: impulse subtracted from spread.

**(c) Regression** — impulse was acting as a noise-correlator that incidentally helped the
spread feature avoid colsample_bytree starvation at seed=42; removing it destabilizes the
basin. IS Sharpe drops below 0. Structural value masked by low importance rank.

---

## Top 3 Recommendations

### Rec 1 — Spread-alone IS Sharpe should match /052's +0.16 ± 0.05 IF impulse was truly dead

The PRIMARY falsifier is spread-only IS Sharpe vs /052 single-seed=42 IS Sharpe (+0.1609).
Both runs share seed=42 inner pool [42, 123, 456] and n_trials=18. The ONLY change is removing
`btc_funding_rate_8h_impulse` from V1_FEATURE_COLUMNS_PRUNED (48 → 47).

If spread-alone IS Sharpe substantially BEATS +0.16 (outcome b above), impulse was crowding
(regression-tax); the drop is permanently confirmed as a Pareto-improvement.

If spread-alone IS Sharpe is substantially BELOW +0.16 (outcome c above), impulse had
structural value masked by importance scoring; restore both features, both-or-neither
retain rule applies, and /055 CONFIRMATION enters with the full 48-col stack.

Pre-register: ± 0.05 IS Sharpe is the single-seed=42 noise floor at n_trials=18. Results
within [+0.11, +0.21] are CONFIRMED; results in [0.0, +0.11) are MARGINAL; results < 0 are
DEGRADES.

### Rec 2 — Importance rank of spread should LIFT to top-5 if it carries the full load now

At /052 seed=42: `btc_funding_spread_30_90` rank 4/48. At /053 seed=42: rank 4/48 (confirmed
stable across 3 outer seeds). After dropping impulse (48 → 47 cols), the INERT impulse no
longer competes for colsample_bytree slots. The LM Master predicts spread importance rank
lifts to 3-7/47 (tighter top band).

If spread falls BELOW rank 15/47 at /054 while IS Sharpe is positive, flag in engineering
report — the IS lift may be redistributed across the rearranged feature set, informing
/055 CONFIRMATION design. Rank is INFORMATIONAL only; does not override F-AXIS #1 verdict.

Watch for rank degradation (spread drops to rank 15+/47 compared to rank 4/48 at /053):
that would indicate Optuna found a different basin via the colsample_bytree position shift,
not that the feature's signal decayed.

### Rec 3 — Trade count comparison: spread-alone vs /053 both-feature

At /052 IS single-seed=42: 133 IS trades. At /053 per-seed IS mean: 136.7 IS trades.
Pre-register: IS trades ≥ 50 AND OOS trades ≥ 10 as hard floors (unchanged from /052-/053
spec). A drop from ~130 IS trades is informational; a drop below 100 (>25% regression) flags
impulse as a potential regime gate (selectivity contributor despite low importance rank).

If IS trade count drops significantly vs /053 (~136), impulse was acting as a regime gate
even while appearing INERT at importance scoring — report and let QR interpret. If IS trade
count is unchanged (~130-140), impulse was pure noise; split-budget dead weight only.

---

## Prior Distribution

| Verdict | Probability | Rationale |
|---|---|---|
| IMPULSE-DROP-CONFIRMED (spread IS ≥ +0.16) | **50%** | INERT-by-importance confirmed multi-seed 3/3; algebraic sister spread carries load solo |
| IMPULSE-DROP-MARGINAL (IS ∈ [0, +0.16)) | **25%** | Subtle colsample_bytree position lottery at single-seed=42; n_trials=18 does not fully resolve |
| IMPULSE-DROP-DEGRADES (IS < 0) | **20%** | LightGBM surprise at seed=42; impulse and spread may share loss-surface correlation at this seed |
| LOTTERY (anomaly, NaN, crash) | **5%** | Same codebase as /052-/053; trivial feature-list change; low but non-zero at n_trials=18 |

**LM Master modal verdict: IMPULSE-DROP-CONFIRMED at 50%** — most likely given the
3/3 multi-seed INERT confirmation at /053.

---

## Risk Flags

- **Single-seed=42 diagnostic power**: the ± 0.05 IS Sharpe noise floor at n_trials=18
  limits resolution for "no change" decisions. A result in [+0.11, +0.21] is CONFIRMED;
  anything tighter requires the multi-seed CONFIRMATION budget to resolve attribution.
- **Multi-seed validation conditional**: run 10-seed validation only on PROMISING-CONFIRMED
  outcome (mirror /050→/051 precedent). Do NOT burn multi-seed budget on MARGINAL or
  DEGRADES paths — route to /055 CONFIRMATION design revision instead.

---

## Closing

This is a Pareto-cleanup test. PASS (CONFIRMED) = drop impulse permanently for /055
CONFIRMATION bundle; 47-col BTC specialist stack enters the multi-seed validation phase.
FAIL (DEGRADES) = restore impulse, both-or-neither retain rule wins, /055 CONFIRMATION
enters at 48-col stack. The outcome decides the exact column set — not the direction of
the BTC specialist thesis.
