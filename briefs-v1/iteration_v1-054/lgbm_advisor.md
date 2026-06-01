# LightGBM Master Advisor — iter-v1/054 — Phase 4.5 (Pre-Design)

## Context Read

- Track: v1; cycle-6 EXP-9/10 — BTC specialist impulse-drop attribution test
- Cohort: BTCUSDT only (BTC-only specialist; unchanged from /052-/053)
- Axis: `feature-pruning` (validation sub-axis — drop impulse, test spread-alone IS contribution)
- Preceding iteration: /053 PARTIAL-CONFIRMED (mean IS Δ +0.8102 vs BTC baseline -0.85;
  multi-seed mean IS Sharpe -0.0398; multi-seed mean OOS Sharpe -0.5981; basin-lottery PASS
  spread 0.3076 < 0.5; seed=42 sanity PASS; trade-rate PASS)
- Triggering mandate: /053 Rec 1 conditional FIRING — PARTIAL-CONFIRMED verdict triggers the
  impulse-drop revaluation: "if /053 closes PARTIAL-CONFIRMED → consider impulse-drop at /054"
  (brief Section 3.1, /053 LM Master Rec 1 adopted)
- V1_FEATURE_COLUMNS_PRUNED change: DROP `btc_funding_rate_8h_impulse` (48 → 47 cols);
  KEEP `btc_funding_spread_30_90`. Feature computation in funding_v1.py is NOT removed.
- Seeds: --seeds 1 (single-seed=42; EXPLORATION budget); n_trials=18; ENSEMBLE_SIZE=3
- Design mandate: tests whether spread-alone delivers ≥ 95% of the /052 single-seed IS lift
  (+0.16 IS Sharpe), confirming impulse contributes 0-5% genuine signal at this cadence

---

## Phase 4.5 — LM Master Pre-Design Advisory

### Context Assessment

/053 confirmed: `btc_funding_spread_30_90` importance rank 4-10 across ALL 3 outer seeds
(Category-2 algebraic-sister z30-z90 mechanism is multi-seed stable; NOT seed-42-specific).
`btc_funding_rate_8h_impulse` importance rank > 30 in 3/3 seeds (INERT-by-importance multi-seed
confirmed; impulse is not productively learned at 8h cadence in BTC specialist context).

The impulse-drop test has a specific LightGBM prediction: if impulse was genuinely inert
(rank 30-48 in all 3 seeds at n_trials=18), its presence or absence should NOT materially
change the spread feature's learned importance OR the model's IS Sharpe. The spread should
continue to rank 4-10 (or potentially lift to 3-8 now that it's no longer competing with
an INERT feature for colsample_bytree slots). The loss-surface effect of dropping one INERT
feature from 48 → 47 is negligible at n_trials=18/ENSEMBLE_SIZE=3.

However, there is a subtle second-order effect: by removing the impulse feature, the
colsample_bytree sampling (which operates by column index) shifts all columns at indices ≥ 0
by one position (since impulse was at index 0, alphabetically). This does NOT change the
mathematical content of any feature, but at n_trials=18 with colsample_bytree ∈ [0.5, 1.0],
the sampling lottery will produce slightly different realizations. The LM Master predicts this
positional shift has negligible effect on IS Sharpe at n_trials=18.

---

## Top 3 Recommendations

### Rec 1 — Single-seed=42 single-run; compare IS Sharpe vs /052 single-seed IS anchor (+0.1609)

The PRIMARY falsifier is spread-only IS Sharpe vs /052 single-seed=42 IS Sharpe (+0.1609).
Both runs share seed=42 inner pool [42, 123, 456] and n_trials=18. The ONLY change is removing
`btc_funding_rate_8h_impulse` from V1_FEATURE_COLUMNS_PRUNED (48 → 47).

Pre-registered decision tree (brief Section 4 F-AXIS #1):

- **Spread-only IS ≥ +0.16** (≈ /052 single-seed IS Sharpe within ±0.05 noise):
  IMPULSE-DROP-CONFIRMED — impulse contributes 0-5% genuine signal; permanently removed;
  BTC specialist roster moves to 47-col stack; seed=42 result anchors /055 CONFIRMATION-bundle
  design.

- **Spread-only IS ∈ [0.0, +0.16)**: IMPULSE-DROP-MARGINAL — both features carry partial IS
  contribution; retain both; document for /055 CONFIRMATION (10-seed budget may resolve).

- **Spread-only IS < 0**: IMPULSE-DROP-DEGRADES — restoring impulse is required; both-or-neither
  rule applies; both features enter /055 CONFIRMATION at 48-col stack.

LM Master prior: IMPULSE-DROP-CONFIRMED at 50% probability (INERT-by-importance = genuinely
not contributing; algebraic sister spread should carry the load solo).
IMPULSE-DROP-MARGINAL at 35% (subtle colsample_bytree position shift produces small regression;
n_trials=18 does not fully resolve attribution at single-seed).
IMPULSE-DROP-DEGRADES at 15% (surprises happen at n_trials=18; the impulse and spread may
be correlated in their loss-surface effects at seed=42 specifically).

**Adopted in brief Section 4 F-AXIS #1.**

### Rec 2 — Trade-rate floor unchanged: IS ≥ 50 trades mandatory

At /052 IS single-seed=42: 133 IS trades. At /053 per-seed IS mean: 136.7 IS trades. Dropping
one INERT feature (impulse) should NOT materially change the trade-count, since impulse never
ranked above 30/48 in any seed and had negligible split-budget allocation. Pre-register:
IS trades ≥ 50 AND OOS trades ≥ 10 as hard floors (unchanged from /052-/053 spec).

If IS trades at /054 drop below 100 (a 25% regression from /052-/053's ~130 mean), note as
anomaly in engineering report for QR interpretation — possible sign that the impulse was
contributing to gating at some threshold even while appearing INERT at importance scoring.

**Adopted in brief Section 4 F-AXIS #2 (trade-rate floor).**

### Rec 3 — Spread importance rank should LIFT (or hold) after impulse removal

At /052 seed=42: `btc_funding_spread_30_90` rank 4/48. At /053 seed=42: rank 4/48 (CONFIRMED
stable). After dropping impulse (48 → 47 cols), the spread's alphabetical position shifts from
index 1 → index 0, and the INERT impulse no longer competes for colsample_bytree slots. The LM
Master predicts spread importance rank lifts to 3-7/47 (tighter top band than /052 4-10 range).

If spread falls BELOW rank 15/47 at /054 while IS Sharpe is positive, note as FLAG in
engineering report (the IS lift may be distributed across the now-rearranged feature set,
which is informational for /055 CONFIRMATION design).

Spread rank is INFORMATIONAL only — it does NOT override the primary F-AXIS #1 verdict.

**Adopted in brief Section 4 F-AXIS #3.**

---

## Flag A — Feature computation code preserved (DO NOT delete impulse function)

`funding_v1.py:compute_btc_funding_rate_8h_impulse` must NOT be removed. Only
`btc_funding_rate_8h_impulse` is removed from `V1_FEATURE_COLUMNS_PRUNED` (48 → 47).
The function code stays in `funding_v1.py` and `add_funding_v1_extended_features` still
computes all four funding features — parquets may still contain the impulse column; the runner
simply does not pass it to LightGBM's `feature_columns` argument.

This preserves the option to restore impulse at /055 CONFIRMATION (IMPULSE-DROP-DEGRADES path).

**Must be documented in brief Section 3 and verified in test suite.**

## Flag B — Parquet regen required (BTCUSDT only)

The 47-col feature set requires a new parquet because the runner validates
`feature_columns=list(V1_FEATURE_COLUMNS_PRUNED)` at training time. Even though impulse may
remain in the parquet (it does — `add_funding_v1_extended_features` still computes it),
the runner must be able to load a parquet and select the 47-col subset correctly. Regen
verifies the parquet pipeline (confirm spread present, check impulse may still be present
as a non-training column — this is fine and expected).

`uv run crypto-trade features --symbols BTCUSDT --interval 8h --track v1 --format parquet --workers 4`

**Must be verified and documented in brief Section 3 and engineering report.**

---

## Prior Distribution (5 bands)

| Verdict | Probability | Rationale |
|---|---|---|
| IMPULSE-DROP-CONFIRMED (spread IS ≥ +0.16) | **50%** | INERT-by-importance confirmed multi-seed 3/3; algebraic sister spread should carry load solo; colsample_bytree shift at 47 cols negligible at n_trials=18 |
| IMPULSE-DROP-MARGINAL (IS ∈ [0, +0.16)) | **35%** | Subtle n_trials=18 colsample_bytree lottery at single-seed; may produce small IS regression vs /052; not fatal for /055 CONFIRMATION |
| IMPULSE-DROP-DEGRADES (IS < 0) | **15%** | LightGBM surprise at seed=42 specifically; lower prior given 3/3 INERT confirmation at multi-seed |
| Anomaly (NaN, crash) | **<1%** | Same codebase as /052-/053; only feature-list change is trivial |

**LM Master modal verdict: IMPULSE-DROP-CONFIRMED at 50%** — most likely outcome given the
3/3 multi-seed INERT confirmation at /053.
