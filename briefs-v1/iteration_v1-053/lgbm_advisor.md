# LightGBM Master Advisor — iter-v1/053 — Phase 4.5 (Pre-Design)

## Context Read

- Track: v1; cycle-6 EXP-8/10 — BTC specialist multi-seed re-validation
- Cohort: BTCUSDT only (mirror /051's DOT multi-seed pattern from /050)
- Axis: `validation` (multi-seed re-validation sub-type; no new feature or gate axis)
- Preceding iteration: /052 PROMISING-SPECIALIST-CANDIDATE (IS Sharpe +0.16; Δ +1.0109 vs BTC
  baseline -0.85; single-seed=42; both features RETAINED per both-or-neither rule)
- Features UNCHANGED from /052: `btc_funding_rate_8h_impulse` (rank 38/48 INERT-by-importance)
  + `btc_funding_spread_30_90` (rank 4/48 STRONGLY learned); V1_FEATURE_COLUMNS_PRUNED = 48 cols
- Seeds: --seeds 3 with `_OUTER_SEED_OFFSETS=(0, 3, 6)` (offsets 0→pool [42,123,456];
  3→pool [789,1001,2002]; 6→pool [3003,4004,5005]; fully disjoint; mirror /051 pattern exactly)
- Design mandate: LM Master Rec 3 from /052 Phase 4.5 FIRES (PROMISING closeout triggered)
- ENSEMBLE_SIZE=3, n_trials=18 (EXPLORATION cadence preserved; no upgrade to CONFIRMATION budget)

---

## Phase 4.5 — LM Master Pre-Design Advisory

### Context Assessment

/052 produced BTC IS Sharpe +0.1609 (Δ +1.0109 vs BTC baseline -0.85) — the first cycle-6
FLIP-POSITIVE specialist. Attribution diverged: `btc_funding_spread_30_90` rank 4/48 (strongly
learned; 3× gain of parents at ranks 17 and 26) vs `btc_funding_rate_8h_impulse` rank 38/48
(INERT-by-importance). The both-or-neither retain rule from LM Master Rec 1 kept both features
pending /053 multi-seed verdict.

/053's primary question is: **is the /052 IS Sharpe flip genuine (signal-mediated) or a single-
seed=42 favorable basin draw?** The /050→/051 DOT pattern established the correct diagnostic:
run 3 disjoint outer seeds; if mean IS Δ ≥ +0.85 → SPECIALIST-CONFIRMED; < +0.30 → revert.

**Attribution divergence implication for multi-seed.** The /052 impulse feature (rank 38/48)
was INERT at seed=42. Multi-seed may show the impulse learning at different seeds if the
colsample_bytree sampling happens to include it more often at non-42 seeds. However, the
spread feature (rank 4/48) is the primary driver — it is stable enough that it should rank
consistently across seeds. LM Master predicts spread rank will stay top-10 in 2/3 seeds;
impulse rank INERT-to-mid-table in all 3 seeds.

**Stability threshold calibration.** At /051 (DOT multi-seed), the basin-lottery threshold was
max-min spread ≤ 1.0. The IS Δ at /052 (+1.0109) is larger than /050 DOT (+1.1162), so the
expected seed-to-seed variance is similar. However, the /052 Δ is driven primarily by a single
rank-4 feature (btc_funding_spread_30_90) — more concentrated driver → potentially higher seed
variance than the DOT case where the driver feature ranked 7-9 consistently. Recommend tightening
basin-lottery threshold to ≤ 0.5 (i.e., max-min IS Sharpe across 3 outer seeds ≤ 0.5) to
reflect the larger expected variance from a concentrated single-driver. This matches the brief
template design specification.

---

## Top 3 Recommendations

### Rec 1 — Keep both-or-neither revert rule active; tighten basin-lottery threshold to ≤ 0.5

The LM Master Rec 1 both-or-neither rule from /052 remains binding at /053. Even though
`btc_funding_rate_8h_impulse` was INERT at rank 38/48, the multi-seed validation tests the
FULL feature stack, not the individual features. If multi-seed produces SPECIALIST-CONFIRMED
(mean IS Δ ≥ +0.85), both features are confirmed for the roster. If NEGATIVE, both are reverted.

The basin-lottery threshold should be tightened from the /051 precedent (≤ 1.0) to ≤ 0.5 for
/053 because the /052 single-seed Δ is dominated by a single rank-4 feature (concentrated
driver). Higher concentration → higher expected variance → tighter basin-lottery threshold is
appropriate. Brief Section 8 must pre-register the ≤ 0.5 threshold explicitly.

**Verdict bands (pre-registered, derive from /052 context):**
- Mean IS Δ ≥ +0.85 AND max-min ≤ 0.5 → **SPECIALIST-CONFIRMED** (both features into /055 roster)
- Mean IS Δ ∈ [+0.30, +0.85) → **PARTIAL-CONFIRMED** (consider impulse-drop at /054; spread retained)
- Mean IS Δ < +0.30 → **NEG-CLEAN-MULTI-SEED** (revert BOTH features; /052 Δ was lottery)

### Rec 2 — Monitor trade-rate mean floor at IS ≥ 50 AND OOS ≥ 10 (same as /052 brief)

The /052 IS produced 133 IS trades at single-seed=42 (well above 50 floor). Multi-seed at
different inner-ensemble pools may produce slightly different trade counts (R3 fire rates vary
by seed when the covariance matrix is estimated on the same training rows but with different
random regularization). Pre-register: **mean IS trades across 3 seeds ≥ 50** as the hard floor;
mean OOS trades ≥ 10. Individual seed floors are informational only.

If mean IS trades fall below 80 (early-warning threshold from /052), note in engineering report.
If any single seed produces IS trades < 20, log as anomaly but do not block the verdict.

### Rec 3 — Feature attribution monitoring: compare spread rank stability across 3 seeds

At /052, `btc_funding_spread_30_90` ranked 4/48 and `btc_funding_rate_8h_impulse` ranked 38/48.
For multi-seed, record the per-seed importance rank for BOTH features. Expected:
- `btc_funding_spread_30_90`: consistently top-15 across 2-3 seeds (genuine learned signal)
- `btc_funding_rate_8h_impulse`: INERT-to-mid-table (rank 25-48) across all 3 seeds

If `btc_funding_spread_30_90` falls below rank 20 in ≥ 2 seeds while IS Δ is positive, the
IS lift may be noise rather than feature-mediated. Engineering report must record per-seed ranks.

If attribution reverses (impulse rises to top-10 in multiple seeds while spread drops),
note as FLAG in engineering report for QR interpretation — does NOT override verdict bands.

---

## Prior Distribution (5 bands)

| Verdict | Probability | Rationale |
|---|---|---|
| SPECIALIST-CONFIRMED (mean IS Δ ≥ +0.85, spread ≤ 0.5) | **40%** | /052 Δ +1.0109 is genuine flip-positive in the /051 precedent domain; spread rank 4/48 is structurally stable; Category-2 algebraic composition (z30-z90) should survive colsample_bytree variation |
| PARTIAL-CONFIRMED (mean IS Δ ∈ [+0.30, +0.85)) | **20%** | Mean Δ regresses toward mid-band if offset0=42 is slightly favorable basin; /051 DOT mean Δ was 0.12 below single-seed /050 result (from +1.1162 to +0.9945) — similar regression here would bring /053 mean from +1.01 to ~+0.89 (still SPECIALIST boundary) |
| NEG-CLEAN-MULTI-SEED (mean IS Δ < +0.30) | **25%** | Attribution concentration risk: if the +1.01 Δ at seed=42 is basin-specific and the spread feature's rank-4 position was an Optuna accident at seed=42, non-42 seeds may not replicate; /052 OOS −1.38 is a warning signal of potential single-seed volatility |
| BASIN-LOTTERY (max-min > 0.5 even if mean IS Δ ≥ +0.85) | **10%** | Concentrated single-driver (spread rank 4) produces high seed variance — one seed may produce IS Sharpe +0.50 and another −0.10, yielding high mean but failing the spread test |
| Anomaly (crash / NaN / data bug) | **5%** | Multi-seed loops at _OUTER_SEED_OFFSETS=(0,3,6) are battle-tested from /051; small risk of offset arithmetic error at BTC specialist dispatch block |

**LM Master modal verdict: SPECIALIST-CONFIRMED at 40%** — highest probability band.
NEG-CLEAN-MULTI-SEED at 25% is non-trivial given the /052 OOS warning signal.

---

## Risk Flags

**Flag A — /052 OOS Sharpe −1.38 is a warning signal.** At /052, the IS Sharpe was +0.1609
(positive) but OOS was −1.3833 (strongly negative). Under the EXPLORATION-budget OOS-variance
signature (`feedback_v3_single_seed_frozen_baseline.md`), this is expected — single-seed OOS
dispersion is 2-3× IS dispersion. However, the magnitude of OOS collapse (from IS +0.16 to OOS
−1.38) is large. Multi-seed will not resolve the OOS question (OOS dispersion stays high at 3
seeds), but if mean OOS is still strongly negative across 3 seeds, the QR must note this pattern
in the Phase 8 diary. Brief Section 7 must explicitly note the OOS warning.

**Flag B — offset=(0,3,6) arithmetic must use ENSEMBLE_SIZE=3 exactly.** The _OUTER_SEED_OFFSETS
patch `run_baseline_v1._OUTER_SEED_OFFSETS = (0, 3, 6)` must be applied AFTER the import in the
runner, not before. Offsets 0, 3, 6 with ENSEMBLE_SIZE=3 give: pool0=[42,123,456], pool3=
[789,1001,2002], pool6=[3003,4004,5005] — all disjoint, all within the 10-element ENSEMBLE_SEEDS
roster. If ENSEMBLE_SIZE were changed to 4, offset 6+4=10 would exceed len=10 and trigger the
cap guard. Brief Section 3 must pin ENSEMBLE_SIZE=3 explicitly.

**Flag C — V1_ITER053_UNIVERSE must be ("BTCUSDT",) — identical to V1_ITER052_UNIVERSE.**
The runner passes `--symbols BTCUSDT` and the dispatch block in run_baseline_v1.py must check
`set(symbols) == {"BTCUSDT"}`. Do NOT reuse the V1_ITER052_UNIVERSE constant for /053 dispatch —
define `V1_ITER053_UNIVERSE = ("BTCUSDT",)` separately to allow independent revert/keep decisions
in future iterations without coupling /052 and /053 constants.

---

## Closing

/053 is the BTC analog of the /050→/051 DOT multi-seed pattern. The LM Master modal verdict
is SPECIALIST-CONFIRMED at 40%, consistent with the finding that `btc_funding_spread_30_90`
(rank 4/48 at seed=42) is a structurally stable Category-2 composed feature. The critical
distinguishing test is whether the rank-4 position of the spread feature persists across non-42
seeds — if it does, mean IS Δ ≥ +0.85 is highly likely; if it is seed-42-specific, the mean
will regress into NEG-CLEAN territory.

The /052 OOS warning (−1.38) should be treated as an information signal to the QR in Phase 8,
not as a verdict gate at /053 (OOS is informational at EXPLORATION budget per project discipline).
The MERCHANT of multi-seed validation is IS robustness, not OOS prediction.
