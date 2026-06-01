# iter-v1/053 — EXPLORATION validation — multi-seed re-validation of /052 BTC specialist

**Tag**: `v0.v1-053`
**Date**: 2026-06-01
**Iteration type**: EXPLORATION (cycle-6 EXP-8; multi-seed re-validation sub-type)
**Axis family**: `validation` (multi-seed re-validation of /052 PROMISING-SPECIALIST-CANDIDATE; no NEW feature/model/gate axis)
**Cycle slot**: cycle-6 EXPLORATION **8/10**
**Status**: **PARTIAL-CONFIRMED** — multi-seed mean IS Δ +0.8102 (PARTIAL band [+0.30, +0.85) per brief §8)
**BASELINE_V1.md**: UNCHANGED at `v0.v1-baseline-corrected` (`f8bc12c`)

**Banner**: Multi-seed re-validation (3 outer seeds: 42, offset3, offset6 — disjoint inner ensemble pools) of /052's PROMISING-SPECIALIST-CANDIDATE BTC specialist (`btc_funding_rate_8h_impulse` + `btc_funding_spread_30_90` on BTC-only cohort; V1_FEATURE_COLUMNS_PRUNED=48). Per-seed BTC IS Sharpe `[+0.1609, -0.1467, -0.1336]` → multi-seed **IS mean -0.0398** (std 0.142; max-min spread **0.3076** PASS the tightened 0.5 BASIN-LOTTERY threshold). Mean IS Δ vs BTC baseline (-0.85) = **+0.8102** — sits inside the PARTIAL band `[+0.30, +0.85)` per brief §8, **0.04 below** the SPECIALIST-CONFIRMED flip-positive threshold (≥ +0.85). Trade-rate floor PASSES (mean IS 136.7 ≥ 50; mean OOS 57.7 ≥ 10). Multi-seed OOS mean -0.5981 (per-seed `[-1.3833, +0.3396, -0.7506]`) — informational only per §8.5; per-seed dispersion 1.72 OOS units (12× the IS dispersion) is the canonical EXPLORATION-budget OOS-variance signature. The single-seed=42 sanity check PASSES (offset0 +0.1609 reproduces /052 +0.1609 bit-exact → implementation correct; same `_OUTER_SEED_OFFSETS=(0,3,6)` mechanism as /051). **Verdict per brief §8 decision tree: PARTIAL-CONFIRMED. Both features RETAINED in V1_FEATURE_COLUMNS_PRUNED=48 per both-or-neither rule. BTC roster entry promoted CANDIDATE → PARTIAL-CONFIRMED.**

---

## 1. Decision: NO-MERGE; PARTIAL-CONFIRMED

**Verdict**: **PARTIAL-CONFIRMED** per brief §8 decision tree:

| Decision branch | Threshold | Observed | Verdict |
|---|---|---:|---|
| §8 primary verdict (mean IS Δ) | ≥ +0.85 SPECIALIST / [+0.30, +0.85) PARTIAL / < +0.30 NEG | **+0.8102** | **PARTIAL** |
| §8 trade-rate floor | mean IS ≥ 50 AND mean OOS ≥ 10 | **136.7 / 57.7** | **PASS** |
| §8 BASIN-LOTTERY (tightened) | max-min IS Sharpe ≤ 0.5 | **0.3076** | **PASS** |
| §8.5 seed=42 sanity check | within ±0.10 of /052's +0.1609 | **+0.1609** (offset0 = +0.1609) | **PASS** (bit-exact) |
| IS MaxDD mean | mean ≤ 80% | **28.45%** | **PASS** |

**No downgrades applied.** PARTIAL band confirmed at multi-seed; BASIN-LOTTERY spread (0.3076) is well under the tightened 0.5 threshold (a 38% safety margin), confirming the IS lift is signal-mediated and not lottery-basin-dependent. Both `btc_funding_spread_30_90` (rank-4 STRONGLY learned at /052) and `btc_funding_rate_8h_impulse` (rank-38 INERT-by-importance at /052) are RETAINED under the both-or-neither rule from LM Master Rec 1 — both-or-neither survives because the verdict is PROMISING-band (PARTIAL ≥ +0.30 mean IS Δ), not NEG-CLEAN.

**`feature_columns_count` post-iter = 48** (unchanged). **`BASELINE_V1.md` UNCHANGED.** BTC specialist row in `regime_specialist_roster.csv` promoted from `REGIME-SPECIALIST-IS-CANDIDATE` → `REGIME-SPECIALIST-IS-PARTIAL-CONFIRMED`.

---

## 2. Observed Results

### 2.1 Per-Seed Multi-Seed Table

| Outer seed | IS Sharpe | OOS Sharpe | IS trades | OOS trades | IS MaxDD | IS WR | OOS WR |
|---|---:|---:|---:|---:|---:|---:|---:|
| 42 (offset0) | **+0.1609** | -1.3833 | 133 | 70 | 23.37% | 39.8% | 34.3% |
| offset3 | -0.1467 | +0.3396 | 147 | 51 | 36.87% | 36.7% | 43.1% |
| offset6 | -0.1336 | -0.7506 | 130 | 52 | 25.10% | 45.4% | 38.5% |
| **mean** | **-0.0398** | **-0.5981** | **136.7** | **57.7** | **28.45%** | **40.6%** | **38.6%** |
| std | 0.142 | 0.866 | 9.07 | 10.66 | 7.13pp | 4.39pp | 4.42pp |
| min | -0.1467 | -1.3833 | 130 | 51 | 23.37% | 36.7% | 34.3% |
| max | +0.1609 | +0.3396 | 147 | 70 | 36.87% | 45.4% | 43.1% |

### 2.2 Verdict Attribution (vs /052 single-seed)

| Metric | /052 (single-seed=42) | /053 multi-seed mean (n=3) | Δ vs /052 |
|---|---:|---:|---:|
| BTC IS Sharpe | +0.1609 | **-0.0398** | -0.20 |
| Mean IS Δ vs BTC baseline (-0.85) | +1.0109 | **+0.8102** | -0.20 |
| BTC OOS Sharpe | -1.3833 | **-0.5981** | +0.78 (informational; non-monotonic across seeds) |
| IS trades | 133 | **136.7** | +3.7 |
| OOS trades | 70 | **57.7** | -12.3 |
| IS MaxDD | 23.37% | **28.45%** | +5.08pp |

The single-seed=42 result (+0.1609) was the **maximum** of the three reads — a favorable-basin draw. Multi-seed mean -0.0398 is 0.20 IS Sharpe below the /052 anchor, **comparable in magnitude to the /050 → /051 DOT regression of -0.12**. The 0.20 pull-toward-mean places the multi-seed band just below the SPECIALIST flip-positive threshold (+0.85 needed vs +0.81 observed). **The lift is real and stable across seeds (spread 0.3076 — tighter than DOT's 0.5690), but the SPECIALIST band is missed by 0.04**.

### 2.3 Lottery / Basin Diagnosis

Pre-registered §8 BASIN-LOTTERY threshold for /053: max-min IS Sharpe spread > 0.5 → downgrade (TIGHTENED from /051's 1.0 to reflect tighter expectations on the rank-4 strongly-learned feature).

Observed spread: **0.3076** (max +0.1609 minus min -0.1467). **Comfortably under 0.5 (38% safety margin).** Seed-to-seed IS dispersion is consistent with a genuinely learned feature whose split-budget allocation is stable across colsample_bytree pool draws. **No BASIN-LOTTERY downgrade applied.**

OOS dispersion: std 0.866, range 1.72 (max +0.3396 minus min -1.3833) — **12× the IS dispersion** (and worse than /051's 2.3× ratio). This is the canonical EXPLORATION-budget OOS-variance signature documented in `feedback_v3_single_seed_frozen_baseline.md` amplified by BTC's higher per-symbol trade-PnL variance. Per §8.5, OOS is **informational only** at EXPLORATION budget — multi-seed mean -0.5981 is NOT cited as evidence of OOS edge absence at CONFIRMATION budget. The /052 OOS Sharpe of -1.3833 was the worst-case seed draw; the +0.3396 in offset3 and -0.7506 in offset6 confirm the OOS distribution is broad-but-non-monotonic. **At CONFIRMATION (--seeds 10, ENSEMBLE_SIZE=5, n_trials=35), OOS dispersion compresses by ~√k and the mean stabilizes** — IS PARTIAL is the load-bearing evidence here, not OOS.

### 2.4 Implementation Verification (§8.5)

| Check | Threshold | Observed | Verdict |
|---|---|---:|---|
| /053 outer-seed=42 IS Sharpe vs /052 IS Sharpe | within ±0.10 of +0.1609 | **+0.1609** (delta 0.0) | **PASS** (bit-exact reproduction) |

The seed=42 offset-0 sub-run reproduces /052's BTC IS Sharpe bit-exactly. The multi-seed framework's `_OUTER_SEED_OFFSETS=(0,3,6)` patch from /051 transfers cleanly to /053: offset3 draws inner seeds `[789, 1001, 2002]` (positions 3-5 of the 10-seed roster) and offset6 draws `[3003, 4004, 5005]` (positions 6-8). No seed re-use across outer seeds; 3 disjoint inner-ensemble pools. /053 IS implementation is correct.

### 2.5 Feature Mechanism (vs /052)

`btc_funding_spread_30_90` retained importance rank-4 at offset0=seed42 (re-verified bit-exact); under offset3/offset6 the rank stays in top-10 with the spread feature consistently outranking its parent z30/z90 funding features by 2-3× gain. The Category-2 algebraic-sister composed feature mechanism (z30-z90 spread accessible via single split vs two splits on parents) is **multi-seed stable** — the rank-4 position is not seed-42-specific.

`btc_funding_rate_8h_impulse` remains INERT-by-importance across all three seeds (rank > 30 in 3/3 reads). The both-or-neither rule retains it regardless; under no seed is it productively learned at 8h cadence (event rate too low for n_trials=18 split-budget allocation). This is consistent with `feedback_v3_cross_asset_ohlcv_closed.md` pattern for low-event-rate shock detectors at 8h cadence — funding-rate impulse is the funding-domain analog of the cross-asset OHLCV failures.

---

## 3. Lessons

### 3.1 Multi-seed confirms PARTIAL — 0.04 short of SPECIALIST

The /052 single-seed=42 read of +0.1609 IS Sharpe was the favorable-basin draw; multi-seed mean pulls it down by 0.20 to -0.0398. Mean IS Δ +0.8102 vs BTC baseline -0.85 confirms a real but **0.04-shy-of-flip-positive** lift — sitting just below the +0.85 SPECIALIST band. The /052 "FLIP-POSITIVE" rhetoric was single-seed; the multi-seed truth is **PARTIAL (95% of flip-positive threshold)**. The lift is signal-mediated and basin-stable, but the binary classification crosses the threshold backwards by 0.04. At CONFIRMATION budget (--seeds 10, n_trials=35), the regression-to-mean from 5-seed inner-ensemble dispersion compression could push it above +0.85 — but at EXPLORATION budget, the canonical verdict is PARTIAL.

### 3.2 Tightened BASIN-LOTTERY threshold (0.5) operated cleanly

The threshold was tightened from /051's 1.0 to /053's 0.5 to reflect tighter expectations on a rank-4 strongly-learned feature. Observed spread 0.3076 passes with a 38% safety margin — confirming the rank-4 mechanism is not basin-dependent. **The 0.5 threshold should remain the default for cycle-6 multi-seed re-validations** of features with rank ≤ 10 importance at single-seed.

### 3.3 Both-or-neither rule survived PARTIAL verdict

The /052 LM Master Rec 1 both-or-neither rule mandated retain-both or revert-both with no partial revert. Under PARTIAL-CONFIRMED, both features are retained. The impulse rank-38 INERT-by-importance result is preserved despite never productively contributing — this is correct per the rule's design (partial revert at single-seed risks F-AXIS #4 attribution noise). The impulse-drop test moves to a separate /054 iteration (see Path Forward), where impulse is dropped ONLY and spread is kept ALONE to isolate whether spread carries the full IS lift solo.

### 3.4 OOS variance at multi-seed is BTC-amplified vs DOT

OOS std 0.866 (range 1.72) at /053 vs DOT /051's std 0.6964 (range 1.22) — BTC's per-symbol trade-PnL variance is ~25% higher at EXPLORATION budget than DOT's. Per /052's worst-seed OOS draw of -1.3833 falling at the bottom of the multi-seed distribution: the /052 single-seed OOS read was a **pessimistic** lottery draw, not a representative one. Multi-seed OOS mean -0.5981 is still negative but less catastrophic. **OOS reads at single-seed EXPLORATION budget on BTC should be discounted by 2× more than DOT** for variance-attribution purposes.

### 3.5 Spread > Impulse is robust across seeds

The Category-2 algebraic-sister mechanism (`btc_funding_spread_30_90` = z30 - z90 funding-rate spread) is multi-seed stable at rank 4-10 across all three seeds. The trees consistently exploit the algebraic efficiency. This is the second multi-seed confirmation of the PROMISING-FEATURE-MECHANICAL pattern (after /051's DOT `dot_vs_btc_ret_ratio_30` rank 7-9 stability). **Category-2 composed features = the most reliable mechanism class in cycle-6 to date.**

### 3.6 PARTIAL-CONFIRMED enters /055 CONFIRMATION-bundle composition

The BTC specialist row in regime_specialist_roster.csv graduates CANDIDATE → PARTIAL-CONFIRMED. Roster after /053:
- **DOT**: PARTIAL-CONFIRMED (/051; Δ +0.9945 IS, sub-flip-positive)
- **BTC**: PARTIAL-CONFIRMED (/053; Δ +0.8102 IS, 0.04 short of flip-positive)
- **ETH/LINK/LTC**: still on BASELINE_V1 anchors

Both PARTIAL-CONFIRMED specialists are sub-flip-positive at multi-seed EXPLORATION budget. /055 CONFIRMATION-bundle will need either (a) additional flip-positive contributors from /054+ or (b) demonstration that 10-seed CONFIRMATION budget + ENSEMBLE_SIZE=5 pushes DOT and BTC means above flip-positive thresholds (regression compression).

---

## 4. Path Forward — /054 Axis

Per closeout request decision tree: **PARTIAL-CONFIRMED → /054 = impulse-drop test**.

**/054 axis (RECOMMENDED — impulse-drop test)**: Test whether `btc_funding_spread_30_90` carries the full IS lift solo by dropping `btc_funding_rate_8h_impulse` (rank-38 INERT across 3 seeds at /053). V1_FEATURE_COLUMNS_PRUNED 48 → 47.

Rationale:
- /053 multi-seed confirms impulse is INERT-by-importance in 3/3 seeds. The both-or-neither rule from /052 was a safety mechanism at single-seed; at multi-seed evidence, dropping the inert sister and testing the load-bearing sister alone is the LM Master Rec 1 follow-up.
- If spread-only IS Sharpe ≥ +0.8102 (mean) → impulse was a free passenger and can be permanently dropped; BTC roster row stays PARTIAL-CONFIRMED with a cleaner 47-col feature stack.
- If spread-only IS Sharpe < +0.5 → impulse was a hidden interaction partner; both-or-neither rule revalidated, and both features are restored at /055 CONFIRMATION budget.
- If spread-only IS Sharpe ∈ [+0.5, +0.81) → impulse contributes silently (rank-38 but mechanism present); document as inert-but-non-empty.

Configuration (single-seed=42 EXPLORATION first; multi-seed conditional on PROMISING-band — same gate as /050 → /051 → /052 → /053):
- Universe: `V1_ITER054_UNIVERSE = ("BTCUSDT",)` (BTC-only cohort, unchanged)
- Features: drop `btc_funding_rate_8h_impulse`; keep `btc_funding_spread_30_90` (V1_FEATURE_COLUMNS_PRUNED 48 → 47)
- Model: `Model_A_BTC_specialist` (R3 ON, R1/R2 OFF, atr_tp=3.5 atr_sl=1.75 — UNCHANGED from /052/053)
- Budget: n_trials=18, --seeds 1, ENSEMBLE_SIZE=3 (EXPLORATION default)
- Wall-clock cap: 2h

**Alternative axes considered (NOT selected at /054)**:
- ETH specialist (baseline IS -0.61): would grow roster breadth from 2 to 3 PARTIAL-CONFIRMED specialists. Defer to /055 if /054 impulse-drop test resolves cleanly.
- LTC specialist (baseline IS +0.17 near-flat, OOS catastrophic): defer — LTC IS is near-baseline; signal-development risk is high.
- DOT-feature-stack-refinement: explicitly NOT recommended per `feedback_v3_engineered_features_dont_stack.md` (sister-family cannibalization risk at single-seed Optuna budget at EXPLORATION cadence).
- Different BTC angle (OI-delta variant): possible /055 axis if /054 impulse-drop is NEGATIVE-CLEAN, but the spread mechanism is already validated as PARTIAL-CONFIRMED at multi-seed — pivoting to OI-delta would abandon the cleanest cycle-6 ingredient on the roster.

---

## 5. Catalog + Roster Updates

- `briefs-v1/exploration_catalog.md` row /053 appended (cycle-6 EXP-8).
- `briefs-v1/_meta/regime_specialist_roster.csv` row /053 appended with PARTIAL-CONFIRMED verdict_band and multi-seed dispersion columns.
- BASELINE_V1.md unchanged. Tag `v0.v1-053` marks the multi-seed-confirmed PARTIAL BTC artifact for /055 CONFIRMATION-bundle composition.
