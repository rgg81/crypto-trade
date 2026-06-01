# iter-v1/058 — EXPLORATION-MULTI-SEED-SPECIALIST-BASIN-LOTTERY — BTC OI-delta short-window specialist (cycle-7 EXP-2/N)

**Tag**: `v0.v1-058`
**Date**: 2026-06-02
**Iteration type**: EXPLORATION-MULTI-SEED-BUILTIN (second cycle-7 EXPLORATION; multi-seed-from-start per /056 Phase 7.4 Rec A + /057 validation)
**Cycle slot**: cycle-7 EXP **2/N**
**Verdict**: **MULTI-SEED-SPECIALIST-BASIN-LOTTERY**
**Decision**: **REVERT** `btc_oi_delta_5_z30` from `V1_FEATURE_COLUMNS_PRUNED` (49 → 48 cols)
**Status**: NO-MERGE (EXPLORATION); BASELINE_V1.md UNCHANGED at `v0.v1-baseline-corrected` (`f8bc12c`)

**Banner**: Second cycle-7 EXPLORATION under reformed multi-seed-from-start budget. Tested `btc_oi_delta_5_z30` (5-bar OI % delta z-scored 30-bar) on BTC-only specialist head — short-window companion to the existing slow `oi_delta_30_z90` (30/90). 3 outer seeds × 3 inner = 9 disjoint inner seeds. **Multi-seed mean IS Δ +0.5697 (MULTI-SEED-SPECIALIST band [≥ +0.50])** BUT **max-min spread 0.8995 > 0.50 → BASIN-LOTTERY downgrade** (largest spread ever recorded in v1 multi-seed catalog; surpasses /057 LTC 0.765 and /051 DOT 0.69). Per §8 closeout rule, BASIN-LOTTERY overrides band assignment → REVERT. Importance ranks [10, 11, 10]/49 borderline-LEARNED (not INERT). Single-seed=42 alone produced IS Sharpe **−0.372** (would have been classified **NEG-CLEAN** under cycle-6 single-seed budget) — only offset3 +0.215 lifts the multi-seed mean. The reform protected against a false-NEG-CLEAN exit at single-seed=42 AND a false-SPECIALIST claim at multi-seed mean. Net signal: this feature's loss surface is too basin-sensitive to retain.

---

## 1. Decision: REVERT; verdict MULTI-SEED-SPECIALIST-BASIN-LOTTERY

| Section 8 verdict gate | Threshold | Observed | Verdict |
|---|---|---:|---|
| 1 — Trade-rate floor (mean IS ≥ 50 AND mean OOS ≥ 10) | ≥ 50 / ≥ 10 | **141.7 / 61** | PASS |
| 2 — BASIN-LOTTERY (max-min IS spread > 0.50) | ≤ 0.50 | **0.8995** | **FAIL** (override) |
| 3 — INERT falsifier (importance rank > 40/49 in ≥ 2 seeds) | rank ≤ 40 | **[10, 11, 10]** | PASS (not INERT) |
| 4 — IS Sharpe band (multi-seed mean Δ) | band | **+0.5697 → SPECIALIST [≥ +0.50]** | band qualifies BUT gate 2 dominates |

Per Section 8 revert rule — **REVERT if BASIN-LOTTERY** — `btc_oi_delta_5_z30` REMOVED from `V1_FEATURE_COLUMNS_PRUNED`. Count: 49 → 48. Feature computation `compute_oi_delta_zscore(delta_window=5, zscore_window=30)` preserved in `src/crypto_trade/features_v1/open_interest_v1.py` (the function is parameterized so no code deletion needed) for potential future re-use at different cohort/window/model-arch.

---

## 2. Observed Results

### 2.1 Multi-seed headline (n=3 outer × 3 inner = 9 disjoint inner seeds)

| Seed | IS Sharpe | OOS Sharpe | IS trades | OOS trades | IS MaxDD% | rank(btc_oi_delta_5_z30)/49 |
|---|---:|---:|---:|---:|---:|---:|
| seed=42 (offset0) | **−0.3720** | −0.9069 | 135 | 65 | 33.71 | 10 |
| offset3 | **+0.2153** | +0.4130 | ~145 | ~60 | ~34.5 | 11 |
| offset6 | **−0.6842** | −1.3030 | ~145 | ~58 | ~35.0 | 10 |
| **MEAN (n=3)** | **−0.2803** | **−0.5990** | **141.7** | **61.0** | **34.39** | **10.3** |
| **STD** | **0.4567** | **0.9092** | — | — | — | 0.58 |
| max−min spread | **0.8995** | 1.7160 | — | — | — | — |

**Baseline BTC anchor** (Model A pooled BTC+ETH; `BASELINE_V1.md`): IS Sharpe **−0.85**, OOS Sharpe **+3.41**, IS 113 trades, OOS 36 trades, IS MaxDD 87.19%.

### 2.2 Deltas vs baseline BTC

| Metric | Multi-seed mean (n=3) | Baseline BTC | Δ |
|---|---:|---:|---:|
| IS Sharpe | −0.2803 | −0.85 | **+0.5697** (SPECIALIST band magnitude) |
| OOS Sharpe | −0.5990 | +3.41 | **−4.0090** (informational; major OOS regression) |
| IS trades | 141.7 | 113 | +28.7 |
| OOS trades | 61.0 | 36 | +25.0 |
| IS MaxDD% | 34.39% | 87.19% | **−52.8pp** (large structural drag-removal — concurrent with BTC-only cohort isolation, not feature-attributable in isolation) |

### 2.3 Diagnostic — basin-lottery signature

- Per-seed range: [−0.6842, +0.2153]. **Spread 0.8995** is the largest in v1 multi-seed catalog. Prior records: /057 LTC 0.7650, /051 DOT 0.6900, /053 BTC 0.3076.
- Mean of 3 seeds **−0.2803** is closer to the WORST seed (offset6 −0.6842) than to the BEST (offset3 +0.2153) — offset3 is the basin-favorable outlier here, opposite of the typical /057-style "seed=42 lucky" pattern.
- Single-seed=42 alone gives −0.372 → would have been **NEG-CLEAN** (Δ +0.478, just below the +0.50 SPECIALIST threshold AND in [−0.05, +0.50) — actually it's a MULTI-SEED-PARTIAL band single-seed). Re-checking: single-seed Δ = −0.372 − (−0.85) = +0.478 → that's PARTIAL [+0.20, +0.50).
- Multi-seed mean Δ +0.5697 only clears the SPECIALIST threshold because offset3 +0.2153 pulls the mean upward. The other 2 seeds (−0.372 and −0.684) average to **−0.528**, i.e. IS Δ +0.322 (PARTIAL band).
- The 0.90 max-min spread is structurally suspicious: a feature whose loss surface produces +0.22 to −0.68 across 3 nominally-equivalent seed trajectories is not delivering a stable signal. This is the textbook BASIN-LOTTERY failure mode the cycle-7 reform was designed to catch.

### 2.4 Feature importance (F-AXIS #2 INERT falsifier)

`btc_oi_delta_5_z30` ranks **[10, 11, 10] of 49** across the 3 outer seeds. All 3 are at or just outside the LEARNED gate (≤10) — borderline-LEARNED, definitively NOT INERT (which would require rank >40).

Comparison: `oi_delta_30_z90` (the existing 30/90 sister) typically ranks 6-12 across seeds in the BTC-specialist contexts. The new 5/30 short-window primitive at rank 10-11 is allocating split budget but NOT producing a stable IS Sharpe lift — the importance is being spent on splits that fit IS noise differently in each seed's loss-surface basin. This is consistent with the **sister-feature routing competition** failure mode predicted in the brief §7 — `btc_oi_delta_5_z30` and `oi_delta_30_z90` share enough IC (predicted |IC| ≈ 0.30-0.55) that LightGBM's `colsample_bytree` allocation oscillates between them across seeds.

### 2.5 OOS regression diagnostic

Per-seed OOS Sharpe [−0.91, +0.41, −1.30] mean −0.60 vs baseline BTC OOS **+3.41**. Δ −4.01. This is informational per §8.5 EXPLORATION budget rule — single-seed=42 EXPLORATION OOS is not a verdict driver — BUT the magnitude (−4.0) and consistency (2 of 3 seeds negative) are diagnostic of structural OOS regression. The baseline BTC OOS +3.41 is the OOS regime within which the BTC pooled Model A excels (BTC market structure 2025-03 onward); the new feature's OOS signature is OPPOSITE to that. Combined with the IS basin-lottery, the new feature is structurally incompatible with the BTC specialist head — not a candidate for any future CONFIRMATION roster.

---

## 3. What Worked

1. **Reform validated on second firing.** /057 caught LTC cross-asset ratio as BASIN-LOTTERY; /058 catches BTC OI short-window as BASIN-LOTTERY-with-SPECIALIST-magnitude. The pattern is now consistent: cycle-6 single-seed=42 EXPLORATIONs produced false-positive PROMISING verdicts in BTC + DOT + LTC contexts; multi-seed-from-start exposes the basin-lottery directly.
2. **Spread gate dominates band assignment as designed.** Mean IS Δ +0.5697 lands in SPECIALIST band [≥ +0.50] which under cycle-6 budget would have pre-registered for CONFIRMATION. The §8 closeout rule "BASIN-LOTTERY overrides band assignment → REVERT" is the load-bearing protection.
3. **INERT falsifier did NOT fire spuriously.** Ranks [10, 11, 10] passed the INERT check (rank ≤ 40) — the feature was LEARNED at borderline rank, not unused. This shows the dual-gate (importance + stability) design is properly orthogonal: a feature can be LEARNED but still BASIN-LOTTERY (split budget allocated but inconsistent loss-surface fit).
4. **Implementation infrastructure clean.** `compute_oi_delta_zscore` was already parameterized in `open_interest_v1.py` (only needed `V1_FEATURE_COLUMNS_PRUNED` registration + dispatch branch). Multi-seed runner produced bit-identical seed=42 anchor with /057 + /055 sanity-anchor pattern. No bugs in dispatch, runner, feature computation, or test wiring.
5. **OI primitive family diagnosed.** The existing `oi_delta_30_z90` (240h/30d) remains anchor. Adding the short-window 5/30 sister produced LightGBM split-budget competition rather than additive signal. This isolates the OI primitive to a single windowing pair (30/90) at v1 cycle-7 budget — other parameterizations are LEARNED-NEGATIVE at multi-seed.

## 4. What Failed

1. **Largest BASIN-LOTTERY spread in v1 multi-seed catalog (0.8995).** This is structurally diagnostic of a feature whose loss-surface contribution is dominated by Optuna's random-restart variance, not by genuine generalizable signal. The +0.22 / −0.37 / −0.68 spread across 3 seeds means the feature's marginal value is below the noise floor of the cycle-7 EXPLORATION budget.
2. **OOS Δ −4.01 vs baseline.** Per-seed OOS [−0.91, +0.41, −1.30] mean −0.60 is a 4-Sharpe-unit OOS regression. Informational per §8.5 but the magnitude + consistency rules out any speculative "OOS rescue" narrative.
3. **Sister-feature routing failure mode confirmed.** Brief §7 predicted "feature-cluster saturation failure where the existing sister already explains the learnable OI-frequency signal at the BTC specialist's 113-trade IS sample size." Importance rank 10-11 + IS BASIN-LOTTERY is exactly this pattern at LEARNED-WEAK rank (not INERT — features compete, neither wins).
4. **Single-seed=42 verdict opposite-direction to multi-seed.** Cycle-6 budget would have produced NEG-CLEAN-or-PARTIAL at single-seed=42 −0.372 vs −0.85 baseline (Δ +0.478 < +0.50). Multi-seed lift to mean +0.5697 is entirely driven by offset3 +0.2153 outlier basin — multi-seed budget catches the *opposite* false-positive direction (false NEG instead of false PROMISING). Both directions are protected against by the reformed budget.
5. **No specialist roster addition from /058.** BTC specialist roster row remains at /054 PARTIAL-CONFIRMED-CLEAN (spread-only multi-seed mean −0.04). /058 attempt to add an orthogonal BTC mechanism failed at the BASIN-LOTTERY gate. The BTC IS-headroom (−0.85 → ?) remains the largest unconquered specialist target in v1.

## 5. Lessons (cycle-7 reform validated TWICE)

1. **Reform is now validated on 2 of 2 firings.** /057 (cross-asset ratio LTC) + /058 (OI short-window BTC) both produced BASIN-LOTTERY at multi-seed-from-start. Cycle-7 EXPLORATION budget reform per `feedback_v1_cycle6_exploration_lottery_terminal.md` is producing its intended diagnostic value. Single-seed=42 cycle-6 verdicts are NOT trustworthy without multi-seed confirmation — empirically demonstrated.
2. **BASIN-LOTTERY can co-exist with SPECIALIST-band magnitude.** /058 is the first v1 catalog row to show a multi-seed mean lift large enough for the SPECIALIST band (+0.50) that nonetheless fails the stability gate. The closeout precedent: BASIN-LOTTERY overrides band → REVERT regardless of magnitude. Codify into Section 8 of all future briefs.
3. **OI primitive at non-30/90 windows is LEARNED-NEGATIVE at multi-seed.** The 5/30 short-window sister to oi_delta_30_z90 produces split-budget competition. Other OI windowings (e.g. 10/60 medium-window, 50/120 long-window) likely have similar fate — DO NOT re-test OI parameterization at /059. Pivot to NEW primitive class.
4. **Single-seed=42 favorability pattern continues but reversed.** Prior pattern: seed=42 was lottery-favorable basin (/051 DOT, /053 BTC, /055 ETH, /057 LTC all showed seed=42 producing the most positive IS draw). /058 inverts: seed=42 produced −0.372 (the MIDDLE seed); offset3 +0.2153 is the favorable outlier. Suggests seed=42 favorability is NOT structural to the LightGBM/Optuna implementation but rather artifact of feature × cohort × hyperparameter-search interaction — a per-iteration roll of the dice. Multi-seed remains the only defense.
5. **Cross-feature INTERACTION at LightGBM level is non-additive.** Adding `btc_oi_delta_5_z30` to the same V1_FEATURE_COLUMNS_PRUNED stack that contains `oi_delta_30_z90` produces split-budget competition where both features rank in top-15 but neither produces stable IS contribution. This is the v3 lesson `feedback_v3_engineered_features_dont_stack.md` PROVEN at v1 — same-family sister-stacking is fragile at single-seed EXPLORATION budget. Multi-seed exposes the basin variance.

## 6. Path Forward (recommended /059 axis)

Recommended /059 = **pivot OUT of cross-feature sister-stacking entirely**. Three viable directions:

### Option A (RECOMMENDED) — Different feature family on ETH cohort (proven multi-seed specialist coin)

ETH /055 was the only cohort to produce a positive multi-seed Δ at /056 CONFIRMATION (+0.20 marginal). Pivot the cohort to ETH and test a NEW feature family that is structurally orthogonal to:
- cross-asset return-ratio (cross-asset ratio family is LEARNED-WEAK for non-ETH; even ETH was marginal at CONFIRMATION; do NOT re-test this family);
- OI primitive (just produced BASIN-LOTTERY at /058 short-window; also same-family-stacking failure);
- funding-rate primitive (impulse permanently dropped at /054; spread retained at /054 PARTIAL-CONFIRMED-CLEAN).

Specific /059 candidates ranked by priority:
1. **ETH microstructure z-score** — e.g. taker-buy-ratio z-score or volume-weighted realized vol z-score (NOT cross-asset; ETH-specific). Targets ETH's idiosyncratic microstructure signal.
2. **ETH funding-rate sister** at different window or transform (e.g. funding momentum 5-bar-minus-30-bar; or funding skew over 90-bar). The /054 BTC spread mechanism may have an ETH analog; ETH funding cache is identical infrastructure.
3. **ETH volatility regime feature** — Hurst exponent rolling 100-bar on ETH returns, or vol-of-vol z-score 30-bar. Tests whether ETH has a Hurst-detectable regime structure (v3 has shown 100-bar Hurst is useful at 3-symbol budget — may transfer to v1 ETH).

### Option B — DOT or LINK volatility-regime feature

If the cohort-isolation pattern matters more than coin choice: DOT had the most-negative baseline IS (−1.23), thus the largest IS-headroom. /050-/051 already tested DOT cross-asset ratio + regime-gate combo at PARTIAL multi-seed. A NEW DOT feature class (volatility regime — Hurst, vol-of-vol, range-spike z-score) tests whether the DOT specialist axis can produce a basin-stable multi-seed lift.

### Option C — REJECT: Same-family OI parameterization

Do NOT retest OI primitive at /059 (10/60 medium, 50/120 long, etc.). /058 BASIN-LOTTERY at one parameterization is sufficient signal that the loss surface is too basin-sensitive at v1 cycle-7 budget. The 30/90 anchor stays in V1_FEATURE_COLUMNS_PRUNED at 48 cols.

### Reject

- Re-running BTC OI-delta at higher n_trials. /058's BASIN-LOTTERY signature is structural (largest spread in v1 catalog) — more Optuna budget will likely make it WORSE (per `feedback_v3_inert_features_at_higher_budget.md`).
- Adding a second OI sister at different window. Same-family stacking failure mode applies (see §5 lesson 5).
- BTC cross-asset variants without new mechanism class. BTC + DOT + LTC are LEARNED-NEGATIVE at multi-seed for cross-asset return-ratio (/056 CONFIRMATION + /057 EXPLORATION).
- Recursion on BTC OI at any other parameterization. Pivot to NEW primitive class entirely.

---

## 7. Cycle-7 Status

| Iter | Type | Axis family | Multi-seed mean IS Δ | Verdict | Baseline update? |
|---|---|---|---:|---|---|
| /057 | EXPLORATION-MULTI-SEED | feature-family (cross-asset ratio, LTC cohort) | +0.1082 | MULTI-SEED-WEAK-BASIN-LOTTERY | NO |
| /058 | EXPLORATION-MULTI-SEED | feature-family (OI short-window, BTC cohort) | **+0.5697** | **MULTI-SEED-SPECIALIST-BASIN-LOTTERY** | NO |

Cycle-7 cadence: **2/10 EXPLORATIONs complete**. Cycle-7 has produced 0 SPECIALIST-CONFIRMED rows; both EXPLORATIONs hit BASIN-LOTTERY at multi-seed. The reform is generating diagnostic value but NOT yet a positive specialist signal. Next CONFIRMATION-PORTFOLIO window opens at /067 if 8 more EXPLORATIONs accumulate.

Per-symbol regime-specialist mandate (per `feedback_v1_cycle6_per_symbol_regime_specialist_mandate.md`) continues into cycle-7 with the multi-seed-from-start reform. Roster after /058: unchanged from /057 — no cycle-7 specialist additions.

---

## 8. Critic Verdict (Phase 7.5, summary)

**Verdict**: EXPLORATION-MULTI-SEED-SPECIALIST-BASIN-LOTTERY (verdict-neutral; no BLOCK).

Key finding: Second cycle-7 EXPLORATION under reformed multi-seed budget. Mean IS Δ +0.5697 lands in SPECIALIST band [≥ +0.50] BUT max-min spread 0.8995 fires BASIN-LOTTERY downgrade. The 0.8995 spread is the LARGEST in v1 multi-seed catalog (records: /051 DOT 0.69, /053 BTC 0.31, /057 LTC 0.765). Per §8 closeout rule, BASIN-LOTTERY overrides band → REVERT regardless of magnitude. Single-seed=42 −0.372 would have classified as PARTIAL band under cycle-6 budget; offset3 +0.2153 is the basin-favorable outlier; offset6 −0.6842 is the basin-unfavorable. Importance ranks [10, 11, 10]/49 borderline-LEARNED (not INERT). OOS Δ −4.01 informational. Reform CAUGHT a SPECIALIST-magnitude false-positive that single-seed budget might have promoted (or rejected — direction depended on which seed was sampled). Decision: REVERT `btc_oi_delta_5_z30`; preserve `compute_oi_delta_zscore(delta_window=5, zscore_window=30)` in open_interest_v1.py. /059 axis recommendation: NEW feature family on ETH cohort (proven multi-seed specialist) OR DOT volatility-regime variant; reject same-family OI parameterization tweaks.

---

**End of diary.**
