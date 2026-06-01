# iter-v1/057 — EXPLORATION-MULTI-SEED-WEAK-BASIN-LOTTERY — LTC specialist cross-asset ratio (cycle-7 EXP-1/N)

**Tag**: `v0.v1-057`
**Date**: 2026-06-02
**Iteration type**: EXPLORATION-MULTI-SEED-BUILTIN (first cycle-7 EXPLORATION; multi-seed-from-start design per /056 Phase 7.4 Rec A)
**Cycle slot**: cycle-7 EXP **1/N**
**Verdict**: **MULTI-SEED-WEAK-BASIN-LOTTERY**
**Decision**: **REVERT** `ltc_vs_btc_ret_ratio_30` from `V1_FEATURE_COLUMNS_PRUNED` (49 → 48 cols)
**Status**: NO-MERGE (EXPLORATION); BASELINE_V1.md UNCHANGED at `v0.v1-baseline-corrected` (`f8bc12c`)

**Banner**: First cycle-7 EXPLORATION under the reformed multi-seed-from-start budget (per /056 lesson — single-seed=42 EXPLORATION verdicts produced 2/3 BASIN-LOTTERY specialists at /056 CONFIRMATION). Tested `ltc_vs_btc_ret_ratio_30` on LTC-only specialist head; direct algebraic mirror of /055 ETH mechanism. 3 outer seeds × 3 inner = 9 disjoint inner seeds. **Multi-seed mean IS Δ +0.1082 (MULTI-SEED-WEAK band [+0.05, +0.20))** with **max-min spread 0.765 > 0.50 → BASIN-LOTTERY downgrade**. Single-seed=42 alone produced IS Sharpe +0.736 (would have been classified PROMISING-SPECIALIST-CANDIDATE under cycle-6 single-seed budget). Multi-seed exposed the basin-lottery directly. **The reformed budget worked as designed** — caught a false-positive PROMISING specialist BEFORE any CONFIRMATION budget was spent.

---

## 1. Decision: REVERT; verdict MULTI-SEED-WEAK-BASIN-LOTTERY

| Section 8 CONFIRMATION roster condition | Threshold | Observed | Verdict |
|---|---|---:|---|
| A — multi-seed mean IS Δ ≥ +0.20 (PARTIAL) | ≥ +0.20 | **+0.1082** | **FAIL** |
| B — `ltc_vs_btc_ret_ratio_30` importance rank ≤ 10 for ≥2 of 3 seeds | ranks ≤ 10 | **[15, 15, 13]** | **FAIL** |
| C — max-min IS Sharpe spread ≤ 0.50 (stability) | ≤ 0.50 | **0.765** | **FAIL** (BASIN-LOTTERY) |
| D — multi-seed mean OOS ≥ -2.0 (forward-signal) | ≥ -2.0 | **-0.5163** | PASS |

3 of 4 conditions FAIL. Verdict per brief §4: **MULTI-SEED-WEAK** band (IS Δ ∈ [+0.05, +0.20)) downgraded to **BASIN-LOTTERY** per §4.3 stability F-AXIS #3.

Per ACTIONS rule in closeout prompt — **REVERT if BASIN-LOTTERY** — `ltc_vs_btc_ret_ratio_30` REMOVED from `V1_FEATURE_COLUMNS_PRUNED`. Count: 49 → 48. Feature computation function `compute_ltc_vs_btc_ret_ratio_30` (and constants `LTC_FEATURE_COLUMN`, `LTC_TARGET_SYMBOL`) preserved in `src/crypto_trade/features_v1/cross_btc_v1.py` for potential future re-use at a different cohort/window/model-arch.

---

## 2. Observed Results

### 2.1 Multi-seed headline (n=3 outer × 3 inner = 9 disjoint inner seeds)

| Seed | IS Sharpe | OOS Sharpe | IS trades | OOS trades | IS MaxDD% | rank(ltc feature)/49 |
|---|---:|---:|---:|---:|---:|---:|
| seed=42 (offset0) | **+0.7360** | -1.6307 | 132 | 56 | 47.21 | 15 |
| offset3 | +0.1276 | +0.0988 | 127 | 49 | 39.84 | 15 |
| offset6 | -0.0290 | -0.0171 | 128 | 49 | 39.28 | 13 |
| **MEAN (n=3)** | **+0.2782** | **-0.5163** | **129.0** | **51.3** | **42.11** | **14.3** |
| **STD** | **0.4041** | **0.9785** | 2.6 | 4.0 | 4.39 | 1.15 |
| max−min spread | **0.7650** | 1.7295 | — | — | — | — |

**Baseline LTC anchor** (Model D specialist; `BASELINE_V1.md`): IS Sharpe **+0.17**, OOS Sharpe **-4.27**, IS 124 trades, OOS 35 trades, IS MaxDD 56.64%.

### 2.2 Deltas vs baseline LTC

| Metric | Multi-seed mean (n=3) | Baseline LTC | Δ |
|---|---:|---:|---:|
| IS Sharpe | +0.2782 | +0.17 | **+0.1082** |
| OOS Sharpe | -0.5163 | -4.27 | **+3.7537** (informational; OOS drag removal) |
| IS trades | 129.0 | 124 | +5.0 |
| OOS trades | 51.3 | 35 | +16.3 |
| IS MaxDD% | 42.11% | 56.64% | -14.53pp (drag removal) |

### 2.3 Diagnostic — single-seed=42 favorable basin exposed

- seed=42 IS Sharpe alone = **+0.7360** → would have been classified **PROMISING-SPECIALIST-CANDIDATE** under cycle-6 single-seed budget (IS Δ +0.566 > +0.50 SPECIALIST flip-positive band).
- offset3 + offset6 mean IS Sharpe = (0.1276 + -0.029)/2 = **+0.0493** → would have been classified **NEG-INERT** band.
- The 5.7× IS Sharpe gap between seed=42 and offset3+offset6 mean is the canonical basin-lottery signature.
- F-AXIS #3 spread 0.765 > 0.50 fires the BASIN-LOTTERY downgrade rule directly. **Cycle-6 reform worked.**

### 2.4 Feature importance (F-AXIS #2 falsifier)

`ltc_vs_btc_ret_ratio_30` ranks: **[15, 15, 13] of 49** across the 3 outer seeds. None reach top-10 LEARNED gate; all 3 are in 11-30 LEARNED-WEAK band (not INERT >40 either). The feature was learned at modest rank but NOT as a top-10 driver in any seed — consistent with the +0.1082 mean Δ being marginal rather than transformative.

Comparison: /055 ETH ratio ranked 13/48 at single-seed; /056 CONFIRMATION-budget ETH ranked 13/14 (near-INERT). LTC at /057 multi-seed mean rank 14.3/49 is similar to ETH's /055 rank — yet ETH survived /056 at IS Δ +0.20 and LTC at /057 multi-seed produced +0.11. Rank alone does not predict CONFIRMATION outcome; ETH happened to draw a favorable basin at /056 too.

---

## 3. What Worked

1. **Multi-seed-from-start design caught the basin-lottery directly.** /056 Phase 7.4 Rec A mandated minimum 2-seed validation at EXPLORATION budget OR PROMISING-verdict precondition = pre-CONFIRMATION 3-seed proof. /057 implemented the stronger 3-outer × 3-inner = 9-seed design from the start; the seed=42 favorable basin (+0.736) was immediately exposed as inconsistent with offset3 (+0.128) and offset6 (-0.029).
2. **Reformed verdict bands worked.** The brief's §4 verdict bands (MULTI-SEED-SPECIALIST-CANDIDATE / PARTIAL / WEAK / INERT / CLEAN) classified the +0.1082 multi-seed mean cleanly as WEAK. The BASIN-LOTTERY downgrade rule fired on stability F-AXIS #3 without needing post-hoc rationalization.
3. **No saved baseline update prevented.** Had this been a single-seed=42 cycle-6 EXPLORATION (+0.736 single), it would have been classified PROMISING-SPECIALIST-CANDIDATE and pre-registered for cycle-7 CONFIRMATION-PORTFOLIO bundle. The multi-seed budget caught it at EXPLORATION cost (1× wall-clock budget at 9 seeds, vs the 10-seed CONFIRMATION budget that would have been spent only to discover the regression).
4. **Forward-signal floor (mean OOS ≥ -2.0) PASSED.** OOS mean -0.5163 is well above the -2.0 floor; this is a meaningful drag removal vs baseline -4.27 (Δ +3.75 informational). If LTC had to participate in any future portfolio bundle, the feature *might* still reduce LTC's OOS drag — but not enough to justify keeping it in the pruned set given the IS BASIN-LOTTERY signature.
5. **Implementation infrastructure was clean.** No bugs in dispatch, runner, or feature computation. The /055 ETH cross-asset feature pattern transferred cleanly to LTC. Multi-seed runner produced 9 disjoint seeds without overlap; sanity-anchor seed=42 reproduced bit-identically with /055-style pattern.

## 4. What Failed

1. **Mean IS Δ +0.1082 is below PARTIAL threshold (+0.20).** The cross-asset return-ratio mechanism does NOT generalize to LTC at the same strength it did at /055 ETH (+0.40) or /050-/051 DOT (+0.99 multi-seed). LTC's idiosyncratic momentum vs BTC may be too noisy or too liquidity-constrained at the 30-bar window to provide stable specialist edge.
2. **Single-seed=42 basin was 0.69 above the mean of the other two seeds.** This is the largest basin-lottery seed-42 favorability documented in cycle-6/cycle-7 (vs /051 DOT 0.69, /053 BTC 0.31, /055 ETH not multi-seed measured at single-seed). LTC's loss surface at n_trials=18 is highly basin-sensitive — small Optuna search budget exacerbates this.
3. **Feature importance rank 13-15 falls short of LEARNED gate ≤10.** The brief pre-registered ≤10 as the LEARNED threshold; the observed 13-15 falls in the LEARNED-WEAK band (11-30). This corroborates the IS Δ +0.11 being marginal rather than transformative — the feature was used but never as a top-10 driver.
4. **OOS dispersion is 2.4× IS dispersion.** OOS std 0.978 vs IS std 0.404. seed=42's OOS is -1.63 (1.5σ outlier from mean). The same offset=0 seed that produced the favorable IS basin produced the worst OOS — a structural diagnostic of regime mismatch between IS and OOS in the LTC-only window at single-seed=42.

## 5. Lessons (cycle-7 reform validated)

1. **/057 is the first cycle-7 iteration to VALIDATE the multi-seed reform.** Single-seed=42 would have classified this as PROMISING-SPECIALIST-CANDIDATE (Δ +0.566 > +0.50); multi-seed reveals MULTI-SEED-WEAK-BASIN-LOTTERY. The reform saves a 6h CONFIRMATION-budget run that would have produced ~-0.35 regression (per /056 ETH+BTC+DOT pattern).
2. **Cross-asset return-ratio family is LEARNED-WEAK at multi-seed for non-ETH cohorts.** /056 CONFIRMATION proved BTC and DOT regressed to LEARNED-NEGATIVE-AT-CONFIRMATION. /057 adds LTC as the third cohort in this family to fail at multi-seed EXPLORATION. ETH remains the ONLY cross-asset ratio specialist with multi-seed positive Δ in v1 catalog (and /056 ETH IS Δ +0.20 was already marginal). **The cross-asset return-ratio mechanism is ETH-specific at this scale, not a generalizable v1 specialist axis.**
3. **Single-seed=42 favorability is the dominant lottery dimension.** /051 DOT, /053 BTC, /055 ETH, /057 LTC all show this pattern with varying magnitude (DOT 0.69 spread → BTC 0.31 spread → ETH not measured → LTC 0.765 spread). The seed=42 favorable-basin distribution is itself a research question — could be a flaw in `_OUTER_SEED_OFFSETS=(0,3,6)` choice or in the ENSEMBLE_SEEDS=(42, ...) ordering.
4. **Feature computation code preservation for REVERTed features is the correct pattern.** `compute_ltc_vs_btc_ret_ratio_30` is preserved in cross_btc_v1.py. If a future iteration finds a different cohort/window/model-arch that benefits from this signal, the code is ready — no re-implementation cost. This mirrors the /054 impulse-drop preservation pattern (impulse code stays in funding_v1.py even after permanent drop).
5. **Importance rank ≤10 LEARNED gate is the right threshold for cross-asset ratio specialists.** Ranks 13-15 + IS Δ +0.11 are mutually-consistent LEARNED-WEAK; ranks ≤10 + IS Δ ≥ +0.20 would have been LEARNED-PROMISING. The dual-gate (importance + Sharpe Δ) discipline prevents either single signal from producing false positives.

## 6. Path Forward (recommended /058 axis)

Recommended /058 = **pivot OUT of cross-asset return-ratio family** entirely. Three viable directions:

### Option A (RECOMMENDED) — NEW feature family pivot

Three candidates for /058 axis-family, ordered by priority:

1. **Microstructure or order-flow z-score for LTC** (e.g. taker-buy ratio rolling z-score, or open-interest delta sister to `oi_delta_30_z90` but at different window). Not the same data class as cross-asset ratio. Mirror the /049/050 cycle-6 approach of one-symbol-cohort + one-NEW-feature.
2. **Funding-rate regime variant for LTC** (not the impulse — that was permanently dropped at /054). E.g. funding-rate momentum (5-bar minus 30-bar) on LTC funding cache. Tests a different funding signal class than the BTC-specific term-structure spread /054.
3. **Volatility regime feature on LTC** — Hurst exponent rolling 100-bar, or vol-of-vol z-score. Targets a different alpha hypothesis than the momentum-direction signal class.

### Option B — ETH refinement at multi-seed

Re-validate ETH specialist mechanism with a NEW orthogonal feature (NOT another cross-asset ratio variant — /056 already showed the ratio feature ranked near-INERT at CONFIRMATION). E.g. ETH funding-rate z-score, or ETH-specific microstructure.

### Option C — Different bar-frequency or label-mode (HIGH-RISK axis)

Tests whether the current 8h bar + ATR triple-barrier label is the binding constraint on v1 specialist edge generalization. HIGH-RISK declaration required; multi-seed mandatory.

### Reject

- Re-running LTC cross-asset ratio at higher n_trials. The basin-lottery diagnosis is the FAULT of the LTC + cross-asset-ratio interaction, not the trial budget. /056 already showed higher Optuna budget makes BASIN-LOTTERY worse for non-ETH cohorts (iter-v3/023 precedent: INERT features at higher budget actively HARM OOS).
- Re-testing the cross-asset ratio family on any v1 cohort. BTC + DOT + LTC are now all LEARNED-NEGATIVE-AT-MULTI-SEED; ETH is marginal. The family is exhausted at v1 scale.
- Re-running BTC or DOT cross-asset ratio at /058 without a NEW mechanism. /056 closed both as LEARNED-NEGATIVE-AT-CONFIRMATION.

---

## 7. Cycle-7 Status

| Iter | Type | Axis family | Multi-seed mean IS Δ | Verdict | Baseline update? |
|---|---|---|---:|---|---|
| /057 | EXPLORATION-MULTI-SEED | feature-family (cross-asset ratio, LTC cohort) | **+0.1082** | **MULTI-SEED-WEAK-BASIN-LOTTERY** | NO |

Cycle-7 cadence: 1/10 EXPLORATIONs complete; next CONFIRMATION-PORTFOLIO window opens at /067 if 9 more EXPLORATIONs accumulate.

Per-symbol regime-specialist mandate (per `feedback_v1_cycle6_per_symbol_regime_specialist_mandate.md`) continues into cycle-7 with the multi-seed-from-start reform. The /057 result confirms that the reform catches false positives at EXPLORATION cost — but it does NOT yet provide a positive specialist signal.

---

## 8. Critic Verdict (Phase 7.5, summary)

**Verdict**: EXPLORATION-MULTI-SEED-WEAK-BASIN-LOTTERY (verdict-neutral; no BLOCK).

Key finding: First cycle-7 EXPLORATION under reformed multi-seed budget. Mean IS Δ +0.1082 lands in MULTI-SEED-WEAK band; max-min spread 0.765 fires BASIN-LOTTERY downgrade. Single-seed=42 +0.736 vs offset3+offset6 mean +0.049 = 5.7× gap — canonical basin-lottery signature. Reform CAUGHT a false-positive PROMISING-SPECIALIST-CANDIDATE that single-seed cycle-6 budget would have promoted to CONFIRMATION bundle. Cross-asset return-ratio family is now LEARNED-WEAK at multi-seed for LTC (joining BTC + DOT from /056 CONFIRMATION). Decision: REVERT `ltc_vs_btc_ret_ratio_30` from V1_FEATURE_COLUMNS_PRUNED; preserve compute function for future re-use. /058 pivot recommended OUT of cross-asset return-ratio family.

---

**End of diary.**
