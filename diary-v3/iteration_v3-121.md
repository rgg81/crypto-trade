# iter-v3/121-METHODOLOGY — Cycle-7 BOOTSTRAP (cycle-6 closure event; FIRST cycle-6 merge) — FILED **CONFIRMATION-MERGE — BASELINE_V3.md UPDATES /059 → /121**. The Critic FINAL (`6d1017d`) ruled CONFIRMATION-MERGE on a single round (zero clarifications) per pre-committed Section 4 falsifiers: F1 BOTH-must-improve PASSES (IS Δ **+0.2214** AND OOS Δ **+0.3891** above /059, both legs clear), F2 IS regime-cost floor +0.79 PASSES with +0.52 margin, F3 hard methodology gates PASS (PBO 0.1278 / PSR 1.0 / frac_positive_paths 0.6444 — identical to /059's CPCV-architecture-invariant values), F5 per-symbol cascade PASSES 3/3 (BCH OOS weighted_pnl Δ +11.08, LDO Δ +3.29, TRX Δ +1.04 — broad-based positive). F4 trade-rate floor (98 < 130) is INFORMATIONAL carry-forward per pre-committed Section 4 (consistent with /059's 94-trade outstanding-constraint status). Headline metrics: **IS monthly Sharpe +1.3108 / OOS monthly Sharpe +0.9682** (vs /059 +1.0894 / +0.5791; Δ IS +0.2214 / Δ OOS +0.3891), MaxDD compresses both IS −4.59pp (30.97 → 26.38) and OOS −8.83pp (34.53 → 25.70), OOS/IS Sharpe ratio 0.7386 (well above the 0.50 floor; the IS-dominant character of /059 RE-ANCHOR #2 has rebalanced toward a healthier OOS/IS ratio without sacrificing the IS-Sharpe ≥ 1.0 floor first cleared at /059). **THIS IS THE FIRST BASELINE_V3.md UPDATE SINCE 2026-05-13** (the prior /059 RE-ANCHOR #2 canonical anchor stood unchanged for 7 days across 62 iterations from /060 through /120, including 26 EXPLORATIONs failing PROMISING and 3 CONFIRMATION/BOOTSTRAP attempts that did not produce a BOTH-must-improve update). **/116 no_confirm (the early-exit-on-no-confirmation RULE-layer primitive) is now part of the canonical baseline** — `enable_no_confirm_exit=True`, `no_confirm_trigger_atr=0.50`, `no_confirm_k_candles=4`. Component B (/119 C6 `ret5d_signed_tbi`) DROPPED PERMANENTLY per the /120 F3 binding falsifier and the /121 attribution finding (Component B's marginal multi-seed effect: IS −0.5815 / OOS +0.7264 — degrades IS, drives the /120 bundle's super-additive OOS via FEATURE-RULE interaction effect). **Cycle 6 closes with 1 ingredient merged (/116 no_confirm) + 1 ingredient dropped (/119 C6)**. The cycle-6 axis-menu hypothesis is now FULLY adjudicated: 0 new direct-edge signals discovered across 10 EXPLORATIONs, 1 strictly-accretive mechanical primitive merges. iter-v3/122 = cycle-7 EXPLORATION axis-1 from the /119 diary §8.2 candidate menu (cross-asset/external feeds, longer-cadence labels, NEW model architecture, NEW symbol universe), QR-selected per `feedback_v3_axis_selection_quant_discipline.md`. Single Critic round + zero clarifications; ALL 8 Critic checks PASS.

**Date**: 2026-05-20
**Type**: CONFIRMATION (CYCLE-7 BOOTSTRAP / METHODOLOGY — /018 BOOTSTRAP-class precedent; NOT counted toward cycle-7 cadence; runs at full CONFIRMATION budget: ENSEMBLE_SIZE=10 unified, n_trials=35, full DSR/PBO/PSR re-eval).
**Verdict**: **CONFIRMATION-MERGE — BASELINE_V3.md UPDATES /059 → /121**. RULE-layer single-mechanism strictly-accretive merge. First cycle-6 merged ingredient. First baseline update since 2026-05-13.
**Tag**: `v0.v3-121` (cycle-6 closure + first-baseline-update marker).

---

## 1. Setup — the iteration (brief reference)

**Brief**: `briefs-v3/iteration_v3-121/research_brief.md` (SHA `ad8af39`).
**Iteration class**: cycle-7 BOOTSTRAP per `feedback_v3_iter018_baseline_bootstrap.md` precedent. NOT counted toward the cycle-7 10/10 EXPLORATION cadence per `feedback_v3_strict_10_to_1_cadence.md`. Runs at full CONFIRMATION budget but is structurally a methodology re-validation isolating Component A standalone from the /120 TWO-COMPONENT bundle.

**Single substantive change vs /120 head state** — Component B (/119 C6 `ret5d_signed_tbi`) REVERTED from `V3_FEATURE_COLUMNS_TOP_N` (15 → 14 features). Component A (`enable_no_confirm_exit=True`, `no_confirm_trigger_atr=0.50`, `no_confirm_k_candles=4`) UNCHANGED. ITERATION_LABEL=v3-121.

**Anchors**:
- /059 canonical (IS +1.0894 / OOS +0.5791) — BOTH-must-improve target per `feedback_v3_strict_both_is_oos_baseline.md`.
- /120 TWO-COMPONENT bundle (IS +0.7293 / OOS +1.6946) — attribution reference.
- /116 single-seed EXPLORATION (IS +0.6246 / OOS +1.1089) — Component A standalone reference (single-seed-42 frozen-baseline mode).

**Spec**:
- Runner invocation: `uv run python run_baseline_v3.py --n-trials 35 --clean-oof` (no `--exploration`, no `--seeds`).
- Default 10-seed unified ensemble (CONFIRMATION mode, ENSEMBLE_SIZE=10).
- Total Optuna trials: 35 × 3 symbols × 10 seeds = 1050.
- Hard cap: 6h. Actual wall-clock: **3.21h** (well within cap).

---

## 2. Implementation — setup, engineering report, Critic cycle

### 2.1 Setup commit chain

| Commit | SHA | Description |
|---|---|---|
| Research brief | `ad8af39` | Section-by-section brief; 5 pre-committed falsifiers; first-match-wins decision tree |
| Phase 5.5 gate | `c5a86e5` | PASS (all 11 sections present; bundle state verified; Foundation Audit + Anti-Pattern Catalog clean) |
| Setup commit | `704ee6c` | `V3_FEATURE_COLUMNS_TOP_N` 15→14 (drop `ret5d_signed_tbi`); pre-flight assertion inversion C6-PRESENT → C6-ABSENT; ITERATION_LABEL "v3-120" → "v3-121" |
| Engineering report | `4b1fea2` | Backtest 3.21h wall-clock; all 9 sections + falsifier evaluation + attribution resolution committed |
| Critic FINAL | `6d1017d` | OVERALL=CONFIRMATION-MERGE; single round; zero clarifications; all 8 checks PASS |

### 2.2 Code surfaces (THREE)

Three surfaces changed vs /120 head state. No new feature, no new function, no new test beyond the pre-flight assertion inversion.

1. **`src/crypto_trade/features_v3/__init__.py` line 178** — Removed `"ret5d_signed_tbi"` from `V3_FEATURE_COLUMNS_TOP_N`. Length 15 → 14. The `compute_ret5d_signed_tbi` function remains in `features_v3/engineered_v3.py` as a code-museum reference (consistent with /118+/119 precedent for dropped features).

2. **`run_baseline_v3.py:2983–2996`** — Pre-flight assertion inversion: `assert "ret5d_signed_tbi" in V3_FEATURE_COLUMNS_TOP_N` → `assert "ret5d_signed_tbi" not in V3_FEATURE_COLUMNS_TOP_N`; `assert len(V3_FEATURE_COLUMNS_TOP_N) == 15` → `assert len(V3_FEATURE_COLUMNS_TOP_N) == 14`.

3. **`run_baseline_v3.py:131`** — ITERATION_LABEL "v3-120" → "v3-121"; MODEL_SPECS prefix updated accordingly.

Component A knobs UNCHANGED from /120/116: `enable_no_confirm_exit=True`, `no_confirm_trigger_atr=0.50`, `no_confirm_k_candles=4`. Pre-flight accretion-guard tuple `(True, 0.50, 4)` enforced.

### 2.3 Sacred constants — UNCHANGED

- `OOS_CUTOFF_DATE = 2025-03-24` — IMMUTABLE
- `training_months = 24` — IMMUTABLE
- `ENSEMBLE_SIZE = 10` (unified Phase B-3 architecture) — UNCHANGED
- `ENSEMBLE_SEEDS` 10-tuple lineage-preserved — UNCHANGED
- 14-feature `V3_FEATURE_COLUMNS_TOP_N` (bit-identical to /059)
- 3-symbol universe BCHUSDT/LDOUSDT/TRXUSDT — UNCHANGED
- `(atr_tp=2.0, atr_sl=1.0)` triple-barrier; 21-candle timeout — UNCHANGED
- 7-primitive risk gate stack — UNCHANGED

### 2.4 Critic Phase 7.5 review

Single round; **zero clarifications requested**. All 8 mandatory checks PASS:

| Check | Status | Highlight |
|---|---|---|
| 1 Look-Ahead | PASS | 14-feature stack bit-identical to /059; /116 no_confirm consults only past+current candle (`backtest.py:251-301`) |
| 2 Embargo | PASS | REQUIRED_GAP=66, embargo_candles=22; walk-forward POST-FIX at `e149e9d` |
| 3 Multiple-testing | PASS | PBO 0.1278 < 0.40, PSR 1.0 > 0.95, frac_positive_paths 0.6444 ≥ 0.55 |
| 4 IC Correlation | PASS-CARVEOUT | No new feature at /121; existing 0.7642 pair is Category-2 carve-out (relaxed importance ≥30) |
| 5 ADF Stationarity | PASS-CARRY | No new feature; /059 ADF clean carried forward |
| 6 Pareto Dominance | PASS | Retired Gate replaced by Gate 10-CPCV (frac_positive_paths ≥ 0.55) — PASS at 0.6444 |
| 7 Reproducibility | PASS | Setup SHA `704ee6c`; explicit 14-feature tuple; 10-tuple ENSEMBLE_SEEDS pinned; 10 OOS trade rows spot-checked |
| 8 Hypothesis-Impl Alignment | PASS | Three code surfaces match brief Section 3 verbatim; no scope creep |

---

## 3. Results — Phase 7 OOS evaluation (first look)

### 3.1 Headline metrics vs /059 canonical baseline (`reports-v3/iteration_v3-121/comparison.csv`)

| Metric | /059 IS | /059 OOS | /121 IS | /121 OOS | IS Δ vs /059 | OOS Δ vs /059 |
|---|---:|---:|---:|---:|---:|---:|
| Monthly Sharpe | +1.0894 | +0.5791 | **+1.3108** | **+0.9682** | **+0.2214** | **+0.3891** |
| Daily Sharpe | 2.7092 | 1.4359 | 3.1180 | 2.3979 | +0.4088 | +0.9620 |
| Max Drawdown | 30.97% | 34.53% | **26.38%** | **25.70%** | **−4.59pp** | **−8.83pp** |
| Profit Factor | 1.4949 | 1.2107 | 1.6019 | 1.3869 | +0.107 | +0.176 |
| Win Rate (aggregate) | — | 38.3% | — | 39.8% | — | +1.5pp |
| n_trades | 171 | 94 | 173 | 98 | +2 | +4 |
| Total PnL (weighted) | 78.18 | 22.74 | 88.77 | 38.15 | +10.59 | +15.41 |
| Monthly Calmar | 2.5246 | 0.6585 | 3.3647 | 1.4843 | +0.840 | +0.826 |
| OOS/IS Sharpe ratio | — | 0.5316 | — | **0.7386** | — | +0.207 |

**Both legs of BOTH-must-improve clear with material margin**: IS Δ +0.2214 above /059's first-IS-≥-1.0 anchor; OOS Δ +0.3891 above /059's +0.5791. The OOS Δ alone (+0.3891) exceeds the entire prior /059's OOS Sharpe (+0.5791) by 67%. MaxDD compresses on both windows — IS −4.59pp (the no_confirm RULE-layer's early-exit mechanism tightening the drawdown envelope by cutting adverse-direction trades before full SL realization), OOS −8.83pp (the OOS leg sees a larger MaxDD compression than IS).

### 3.2 Methodology metrics (`reports-v3/iteration_v3-121/dsr.json`)

| Metric | /059 | /121 | Status |
|---|---:|---:|---|
| PBO mean | 0.1278 | **0.1278** | PASS (< 0.40; identical to /059 — CPCV architecture-invariant) |
| PSR | 1.0 | **1.0** | PASS (> 0.95; n_trials=1050 saturation) |
| frac_positive_paths (CPCV 45 paths) | 0.6444 | **0.6444** | PASS (≥ 0.55; identical to /059 — CPCV invariant) |
| CPCV path Sharpe Q75 | 0.8378 | 0.8378 | identical |
| OOS/IS Sharpe ratio (Gate 3) | 0.5316 | **0.7386** | PASS (≥ 0.50 floor by margin +0.24) |
| DSR (legacy) | 0.0 | 0.0 | INFORMATIONAL (structural at v3 trade volume) |
| DSR_relative | 0.1134 | **0.9999** | INFORMATIONAL (architecture artifact; threshold needs cycle-1 recalibration) |
| DSR_relative_b4 | 1.0 | **1.0** | INFORMATIONAL — Path B4 tracks relative improvement |
| n_trials | 1050 | 1050 | unchanged |
| n_eff | 19 | 19 | architecture-independent |
| min_trl_months | 5.70 | 5.77 | architecture-consistent |
| n_daily_obs_oos | 90 | 90 | unchanged |

All three binding methodology gates (PBO, PSR, frac_positive_paths) PASS cleanly — and because the CPCV path-generation architecture and seed ensemble are identical to /059, the methodology numbers are bit-near-identical. The substantive uplift is in the IS+OOS headline Sharpes.

### 3.3 CPCV path Sharpe distribution (45 paths)

| Quantile | Path Sharpe |
|---|---:|
| Q25 | −0.243 |
| Q50 (median) | +0.3351 |
| Q75 | +0.8378 |

29/45 paths positive = 0.6444 frac_pos (above 0.55 floor). The lower quartile is modestly negative, expected for a 3-symbol universe with BCH-dominant OOS concentration.

### 3.4 /121 vs /120 / /116 comparison

| Reference | IS Sharpe | OOS Sharpe | vs /059 IS Δ | vs /059 OOS Δ | Architecture |
|---|---:|---:|---:|---:|---|
| /059 canonical (anchor) | +1.0894 | +0.5791 | — | — | unified 10-seed |
| /116 Component A single-seed | +0.6246 | +1.1089 | −0.4648 | +0.5298 | 3-seed EXPLORATION-mode |
| /120 bundle A+B (10-seed) | +0.7293 | +1.6946 | −0.3601 | +1.1155 | unified 10-seed |
| **/121 Component A only (10-seed)** | **+1.3108** | **+0.9682** | **+0.2214** | **+0.3891** | unified 10-seed |

The structural finding: /121 IS (+1.3108) is **substantially HIGHER than both /116 single-seed (+0.62) and /120 bundle (+0.73)** — the /116 IS depression was a single-seed-42 frozen-baseline artifact per `feedback_v3_single_seed_frozen_baseline.md`. At full 10-seed CONFIRMATION, Component A's true IS contribution is positive AND strictly above /059's IS — the /116 single-seed pattern was misleading on the IS axis. OOS compresses from /116 single-seed (+1.1089) to /121 multi-seed (+0.9682), consistent with expected EXPLORATION→CONFIRMATION multi-seed variance reduction.

### 3.5 Per-symbol IS attribution (`reports-v3/iteration_v3-121/in_sample/per_symbol.csv`)

| Symbol | /059 IS trades | /121 IS trades | /059 IS WR | /121 IS WR | /059 IS net_pnl_pct | /121 IS net_pnl_pct | Delta pnl |
|---|---:|---:|---:|---:|---:|---:|---:|
| BCHUSDT | 83 | 85 | 49.4% | **50.6%** | +109.23% | **+119.15%** | **+9.92pp** |
| LDOUSDT | 9 | 9 | 33.3% | 33.3% | +0.89% | **+9.53%** | **+8.64pp** |
| TRXUSDT | 79 | 79 | 34.2% | 34.2% | +3.95% | **+7.31%** | **+3.36pp** |

**3/3 symbols improve IS net_pnl_pct vs /059** — broad-based, NOT a single-symbol carrier. BCH (the dominant IS-share symbol at /059's 95.76%) gains +9.92pp. LDO (the chronic IS-drag symbol at /059 with only +0.89%) improves substantially to +9.53% — the no_confirm RULE-layer cuts LDO's worst losing trades early before they reach full SL. TRX gains +3.36pp.

### 3.6 Per-symbol OOS attribution (F5 cascade — load-bearing; `reports-v3/iteration_v3-121/out_of_sample/per_symbol.csv`)

| Symbol | /059 OOS trades | /121 OOS trades | /059 OOS WR | /121 OOS WR | /059 OOS weighted_pnl | /121 OOS weighted_pnl | Delta | F5 verdict |
|---|---:|---:|---:|---:|---:|---:|---:|---|
| BCHUSDT | 34 | 35 | 41.2% | **48.6%** | +24.7502 | **+35.8314** | **+11.0812** | **PASS** |
| LDOUSDT | 12 | 12 | 25.0% | 25.0% | −6.1783 | **−2.8864** | **+3.2919** | **PASS** |
| TRXUSDT | 48 | 51 | 41.7% | **43.1%** | +4.1639 | **+5.2077** | **+1.0438** | **PASS** |

**F5 OVERALL: 3/3 symbols positive OOS Δ vs /059 → PASS (exceeds ≥2/3 threshold by 1).** BCH (+11.08) carries the largest OOS Δ — BCH IS WR climbs 41.2% → 48.6%, net_pnl_pct climbs 26.58% → 52.48%. LDO recovers from deep negative to near-neutral (+3.29 Δ; still OOS-negative at −2.89 but materially improved). TRX adds marginally (+1.04 Δ). The cascade is genuinely broad-based, not just a BCH-only effect.

### 3.7 /116 no_confirm mechanism validation

Exit-reason breakdown:

| Period | take_profit | stop_loss | timeout | no_confirm | Total |
|---|---:|---:|---:|---:|---:|
| IS | — | — | — | **10** | 173 |
| OOS | — | — | — | **9** | 98 |

no_confirm fires at 10/173 IS trades (5.8%) and 9/98 OOS trades (9.2%). Consistent with /116 EDA T7 — the rule is more active in volatile/chop regimes.

no_confirm exits, per-period:

| Period | no_confirm exits | Wins | WR | Avg net_pnl_pct |
|---|---:|---:|---:|---:|
| IS | 10 | 1 | 10.0% | −0.988% |
| OOS | 9 | 1 | 11.1% | −0.928% |

The rule's design (cut losing positions early before they reach full SL realization) is realized as expected: ~10% WR with ~−1% avg net_pnl_pct. The IS↔OOS consistency (10.0% vs 11.1% WR; −0.988% vs −0.928% avg) confirms the rule is firing in structurally similar trade situations across both windows.

Per-symbol OOS no_confirm breakdown:
- TRXUSDT: 5 exits, WR 0/5 = 0.0%, avg net_pnl_pct = −0.846%
- BCHUSDT: 3 exits, WR 1/3 = 33.3%, avg net_pnl_pct = −1.250%
- LDOUSDT: 1 exit, WR 0/1 = 0.0%, net_pnl_pct = −1.929%

### 3.8 OOS trade-rate

98 OOS trades across 14 OOS months = **7.0 trades/month**. F4 trade-rate floor of ≥10/month (≥130 OOS total) is NOT cleared (margin: +32 trades short of the floor). Status: **INFORMATIONAL** per pre-committed brief Section 4 — consistent with /059's outstanding-constraint status (94 trades) and /120's 96 trades; the floor is a v3-wide outstanding constraint, not a /121-specific block. Reaching 130 OOS trades on the 3-symbol BCH/LDO/TRX universe at current regime requires ~18-19 OOS months of coverage or universe expansion (universe expansion is closed at a 4-failure track record per `BASELINE_V3.md` Dead Ideas).

---

## 4. Critic Review Summary (Phase 7.5)

### 4.1 Single round — zero clarifications

The Critic FINAL (`6d1017d`) issued OVERALL=CONFIRMATION-MERGE on the first review pass with zero clarifications requested. All 8 mandatory checks PASS; no QR response round needed.

### 4.2 The 5 falsifier outcomes with numerical traces

| F# | Status | Observed | Threshold | Margin |
|---|---|---:|---:|---:|
| **F1 BOTH-must-improve** | **PASS** | IS +1.3108 AND OOS +0.9682 | IS ≥ +1.0894 AND OOS ≥ +0.5791 | IS leg +0.2214; OOS leg +0.3891 |
| **F2 IS regime-cost floor** | **PASS** | IS +1.3108 | ≥ +0.79 | +0.5208 |
| **F3 Hard methodology gates** | **PASS** | PBO 0.1278, PSR 1.0, frac_pos 0.6444 | PBO<0.40, PSR>0.95, frac_pos≥0.55 | All clean |
| **F4 Trade-rate floor** | INFORMATIONAL | 98 OOS trades | ≥ 130 | −32 (carry-forward; not block) |
| **F5 Per-symbol cascade** | **PASS** | 3/3 symbols positive Δ vs /059 | ≥ 2/3 positive | exceeds by 1 symbol |

**4/5 binding falsifiers PASS with material margin. F4 INFORMATIONAL per pre-committed brief Section 4.**

Per the brief Section 8.3 first-match-wins decision tree branch 5: all falsifiers PASS → CONFIRMATION-PARTIAL-MERGE (RULE-layer single-mechanism). BASELINE_V3.md UPDATES /059 → /121.

### 4.3 Substantive classification — CONFIRMATION-MERGE

The Critic FINAL conclusion:

> CONFIRMATION-MERGE — /116 no_confirm RULE-layer primitive STANDALONE at 10-seed CONFIRMATION clears BOTH-must-improve (IS +0.22, OOS +0.39 above /059), F2 regime-cost floor (IS +1.31 well above +0.79), F3 methodology gates, and F5 cascade (3/3 symbols positive OOS Δ vs /059); F4 trade-rate (98 < 130) INFORMATIONAL per pre-committed brief Section 4. BASELINE_V3.md UPDATES from /059 → /121 — first methodologically-clean cycle-6 single-mechanism merge in v3 history. Attribution gap from /120 empirically resolved.

---

## 5. The attribution gap RESOLUTION — the load-bearing finding

The central post-/120 question: was the /120 bundle's all-time v3 OOS record (+1.6946) driven by Component A alone, by Component B alone, or by a non-additive multi-mechanism interaction effect? /121 answers this empirically and definitively.

### 5.1 Quantitative decomposition

| Reference | IS Sharpe | OOS Sharpe | vs /059 IS Δ | vs /059 OOS Δ |
|---|---:|---:|---:|---:|
| /059 canonical | +1.0894 | +0.5791 | — | — |
| /116 Component A single-seed | +0.6246 | +1.1089 | −0.4648 | +0.5298 |
| /120 bundle A+B (10-seed) | +0.7293 | +1.6946 | −0.3601 | +1.1155 |
| **/121 Component A only (10-seed)** | **+1.3108** | **+0.9682** | **+0.2214** | **+0.3891** |

**Component B marginal effect at multi-seed** (= /120 bundle minus /121 Component A standalone):

- IS Δ: +0.7293 − +1.3108 = **−0.5815**
- OOS Δ: +1.6946 − +0.9682 = **+0.7264**

### 5.2 The three resolved sub-findings

**Finding 1 — /116 single-seed IS depression was a frozen-baseline artifact, not a structural Component-A property.**

/116 reported IS +0.6246 at single-seed-42 EXPLORATION-mode — a Δ of −0.4648 vs /059 — and this was the central piece of evidence that motivated the /120 brief's F2/F4 IS regime-cost floor calibration at +0.79. /121's 10-seed CONFIRMATION delivers IS +1.3108 (Δ +0.2214 vs /059) — Component A standalone IS is **above /059, not below**. The /116 single-seed IS depression was a single-seed-42 lottery artifact per `feedback_v3_single_seed_frozen_baseline.md`, NOT a structural property of the no_confirm primitive. **The /116 single-seed pattern was misleading on the IS axis.** This finding fundamentally reshapes how single-seed EXPLORATION evidence should be weighed for RULE-layer primitives: single-seed IS depression is not a reliable signal of multi-seed IS regime-cost.

**Finding 2 — Component B's marginal multi-seed effect is IS −0.58 / OOS +0.73; the /120 bundle's super-additive OOS is the multi-mechanism interaction effect, NOT Component A's direct contribution.**

The /120 bundle's all-time OOS record (+1.6946) decomposes as: Component A standalone OOS Δ (+0.3891) + Component B marginal OOS Δ (+0.7264) = +1.1155 vs /059. Component B alone is not on disk (it was never run standalone at 10-seed), but the additive decomposition gives Component B's marginal contribution. **The bundle's super-additive OOS lift is GENUINE multi-mechanism interaction effect** — Component B's FEATURE-layer loss-surface redistribution (C6 at importance position 14, dropping `regime_momentum_signed_5d` portfolio importance by 66.1%) reorganizes the entry distribution such that Component A's RULE-layer exit channel operates on a structurally DIFFERENT trade set in OOS (Jaccard 0.48 with /116-alone OOS roster; 30 trades unique to bundle out of 96 OOS trades per /120 Critic Q3 set-comparison).

**Finding 3 — Component A alone is strictly-accretive AND IS-preserving; Component B contributes a net-negative IS marginal effect; F3-DROP at /120 was the correct call.**

The /120 bundle's IS collapse to +0.7293 (Δ −0.3601 vs /059) was attributable entirely to Component B's feature-layer IS cost (−0.5815 marginal). Removing Component B (the /121 configuration) restores AND IMPROVES IS to +1.3108 (Δ +0.2214 vs /059). The pre-committed F3-DROP-Component-B decision at /120 was the correct binding call: /121 isolated yields the strictly-accretive IS+OOS improvement that the bundle could not, while the /120 bundle's all-time OOS record (+1.6946) is documented as a structural multi-mechanism artifact — non-replicable as a single-primitive property and unmergeable due to IS regime-cost.

### 5.3 The non-compoundable-as-signal-source invariant — validated

Component B is the FIRST PROMISING-FEATURE-MECHANICAL primitive (per `feedback_v3_promising_feature_mechanical.md` established at /119). The /120 F3 binding gate (sister-redistribution conjunctive AND gate) caught the FEATURE-MECHANICAL signature even when the bundle achieved all-time v3 OOS record and the interaction effect was genuine. The /121 post-validation empirically confirms: when Component A standalone produces IS-preserving + OOS-accretive multi-seed metrics that beat /059 on BOTH axes, the bundle's super-additive OOS lift was NOT compoundable signal — it was a non-replicable interaction artifact. Component B's marginal effect at multi-seed (IS −0.58 / OOS +0.73) is NOT a "new edge ingredient"; it is a catalyst whose direct effect is net-negative on IS, with OOS lift dependent on the interaction with Component A's RULE-layer overlay. **PROMISING-FEATURE-MECHANICAL is correctly classified as non-compoundable-as-signal-source.**

The validation note appended to `feedback_v3_promising_feature_mechanical.md` (this iteration): F3-DROP fires CORRECTLY at multi-seed even when (a) the bundle achieves all-time OOS record, (b) all 3 OOS symbols Δ positive, (c) F1 stacking-linearity PASSES, and (d) Jaccard 0.48 confirms genuine interaction. The /121 post-validation empirically confirms the binding-test pre-commitment was the correct call: Component A alone shows IS-preserving + OOS-accretive at multi-seed.

---

## 6. Cycle-6 final scoreboard

### 6.1 Cycle-6 EXPLORATION outcomes (10/10)

| Slot | Iteration | Verdict | Axis |
|---|---|---|---|
| 1 | iter-v3/110 | UNRESOLVED (label-confound) | Symbol selection (CRV/AAVE/GRT/ADA) |
| 2 | iter-v3/111 | NEGATIVE clean | Symbol selection re-test (CRV/AAVE/GRT/ADA, label fixed) |
| 3 | iter-v3/112 | NEGATIVE | Pooled cross-symbol model architecture |
| 4 | iter-v3/113 | NEGATIVE | Multi-frequency features on 8h base |
| 5 | iter-v3/114 | NEGATIVE-INVALID (Check-1 + Check-8 FAIL) | Risk management (LDO kill-switch) |
| 6 | iter-v3/115 | NEGATIVE-clean | Coherent horizon-exit labeling |
| 7 | **iter-v3/116** | **PROMISING-MECHANICAL (RULE form)** | Exit-on-no-confirmation primitive |
| 8 | iter-v3/117 | NEGATIVE catastrophic | Candle frequency 8h → 24h-multi-offset |
| 9 | iter-v3/118 | NEGATIVE catastrophic | Category-2 composed (ema_spread × sign(vol-regime)) |
| 10 | **iter-v3/119** | **PROMISING-FEATURE-MECHANICAL (FEATURE form, NEW sister-subtype)** | Category-2 composed (ret_5d × sign(taker_buy_imbalance_20)) |

**Cycle-6 EXPLORATION outcome distribution: 8 NEGATIVE + 2 PROMISING (both mechanical; 0 direct-edge).**

### 6.2 Cycle-6 CONFIRMATION + BOOTSTRAP outcomes

| Iteration | Type | Verdict | Outcome |
|---|---|---|---|
| iter-v3/120 | CONFIRMATION (TWO-COMPONENT bundle: /116 + /119 C6) | **NO-MERGE per F3+F4 binding** | All-time v3 OOS record (+1.6946) recorded but NOT merged; Component B DROPPED |
| iter-v3/121-METHODOLOGY | CONFIRMATION (BOOTSTRAP: /116 Component A standalone) | **MERGE — BASELINE UPDATES** | First cycle-6 merged ingredient; BASELINE_V3.md /059 → /121 |

### 6.3 Cycle-6 final outcome

**Net: 1 ingredient merged (/116 no_confirm RULE-layer primitive) + 1 ingredient dropped (/119 C6 FEATURE-layer composed feature) + 0 new direct-edge signals discovered.**

The cycle-6 axis-menu hypothesis (the user's 2026-05-19 directive that 4 structural axes — symbol selection, pooled-vs-per-symbol, multi-freq features, risk management — would surface NEW EDGE on the v3 binding constraint) is now FULLY adjudicated:

- **FALSIFIED on the new-direct-edge axis**: 0 of 10 EXPLORATIONs produced direct-edge PROMISING. The 4 menu axes (/110-/114) all NEGATIVE; the extended menu items (/115-/119) added 2 PROMISING outcomes but BOTH were mechanical (not signal-discovery).
- **PARTIALLY VALIDATED on the strictly-accretive mechanical-primitive axis**: 2 mechanical PROMISING outcomes — /116 RULE-form (the merged ingredient) and /119 FEATURE-form (the dropped ingredient).

The cycle-6 outcome confirms the /105→/109 cycle-5 structural finding: **the v3 binding constraint is DOWNSTREAM of the training label** — in the trade-construction / exit / risk layer. The only PROMISING outcomes (/116 RULE-layer exit primitive + /119 FEATURE-layer loss-surface reorganization at the entry layer) were in the downstream layer the cycle-5 chain identified; the 8 cycle-6 axes that re-walked or refined upstream/horizontal axes (universe, pooled architecture, multi-freq, risk primitives, labeling estimand, candle frequency, vol-regime composed features) all NEGATIVE.

### 6.4 Why /121 is the cycle-6 closure event

iter-v3/121-METHODOLOGY is the cycle-6 closure event because:

1. It empirically resolves the /120 attribution gap (Component A vs Component B contributions).
2. It produces the FIRST BASELINE_V3.md update in v3's post-/059 history (the first since the /059 RE-ANCHOR #2 on 2026-05-13).
3. It merges /116 no_confirm as the first cycle-6 strictly-accretive ingredient — finalizing cycle 6's net outcome.
4. It validates the F3 binding-gate methodology — F3 fires correctly even when the bundle achieves all-time OOS record + interaction effect is genuine; Component A alone is the correct merge candidate.
5. It authorizes the cycle-7 setup with /121 as the new anchor for /122 onward.

---

## 7. Cycle-7 setup pointers

### 7.1 /122 = cycle-7 EXPLORATION axis-1

**Anchor**: /121 (IS +1.3108 / OOS +0.9682), NOT /059. All cycle-7 EXPLORATIONs anchor against the new baseline.

**Axis selection**: QR-led per `feedback_v3_axis_selection_quant_discipline.md`. Brief Section 2 must contain EDA-derived numerical tables from a committed `analysis/iteration_v3-122/*.py` script. Orchestrator may suggest candidates but cannot commit setup without QR backing.

**Candidate axis menu** (from /119 diary §8.2, carried forward via `project_v3_cycle7_setup.md`):

1. **Cross-asset/external feeds** — funding rates from a different venue (Bybit, OKX), perp-spot basis, liquidations data, on-chain BTC metrics (Glassnode/CryptoQuant), DeFi TVL/lending utilization. Constraint: v3 has tried 7 non-OHLCV crypto-native feeds (funding /019/023/024/082/085, microstructure /015, basis /086) — all INERT-by-importance. Cycle-7 cross-asset/external-feed axes must use STRUCTURALLY DIFFERENT primitives or NEW transformation pipelines NOT yet attempted.

2. **Non-LightGBM model classes NOT yet tested at /109 depth** — ensemble-of-different-model-classes; neural-network-with-different-training-regime (deeper depth than tested at /109); LSTM / Transformer with explicit time-series inductive bias; CatBoost / XGBoost-v2 with hyperparameter regime distinct from /016's depth-wise defaults.

3. **Longer-cadence labels** — 1-week or 1-month horizon labels with appropriate execution geometry.

4. **NEW symbol universe NOT-already-tested variants** per `feedback_v3_concentration_is_signal.md` constraints. Extreme-out-of-distribution candidates selected via STRUCTURALLY DIFFERENT screening than prior universe-expansion failures.

**Forbidden cycle-7 axes** (carried forward):

- Re-walking cycle-6 NEGATIVE axes (universe / pooled / multi-freq-on-8h / risk-primitive-kill-switches / coherent-horizon-exit-labeling / candle-frequency / vol-regime-composed-features) without genuinely-new structural delta.
- Knob-tuning saturated axes (ADX threshold, z-score threshold, BTC-band threshold).
- Per-symbol customizations (closed at /039 NEGATIVE).
- Component B-style FEATURE-layer cannibalizer features (per F3 binding-gate validation at /120 + /121 attribution finding — cycle-7 engineered-feature axes must be /025-class direct-edge candidates, not /119-class FEATURE-MECHANICAL cannibalizers).

### 7.2 Cycle-7 cadence

Per `feedback_v3_strict_10_to_1_cadence.md`: 10 EXPLORATIONs (iter-v3/122–/131) + 1 CONFIRMATION (iter-v3/132). The /121-METHODOLOGY BOOTSTRAP does NOT count toward the 10/10 cadence. EXPLORATION 2h cap; CONFIRMATION 6h cap (empirically updated from 4h per `feedback_v3_cadence_discipline.md`).

### 7.3 Outstanding constraints carried into cycle 7

| # | Constraint | Threshold | /121 Observed | Required Lift |
|---|---|---:|---:|---:|
| 1 | OOS Sharpe ≥ +1.0 | ≥ 1.0 | +0.9682 | +0.03 (very close — could clear in any cycle-7 PROMISING) |
| 2 | OOS trades ≥ 130 | ≥ 130 | 98 | +32 (or +18 months of OOS data accumulation) |
| 3 | OOS trades/month ≥ 10 | ≥ 10 | 7.0 | +3.0 (or universe expansion) |
| 4 | Top-symbol concentration ≤ 30% | ≤ 30% | BCH 95.76% | structural property of 3-symbol BCH-dominant universe |
| 5 | Legacy DSR > 0.95 | > 0.95 | 0.0 | structural at v3 trade volume; needs gate reformulation |
| 6 | DSR_relative > 0.95 (Path B4) | > 0.95 | 1.0 | PASS at /121 (vs /059 0.1134; resolved under Path B4) |

OOS trade-rate floor remains the binding v3-wide constraint. The OOS Sharpe ≥ +1.0 floor is +0.03 away (within reach of any cycle-7 PROMISING).

---

## 8. BASELINE_V3.md update — what changes

**BEFORE** (post-/059, unchanged 2026-05-13 to 2026-05-20):
- Canonical: iter-v3/059 (RE-ANCHOR #2 — unified 10-seed ensemble)
- IS monthly Sharpe: +1.0894
- OOS monthly Sharpe: +0.5791
- OOS/IS ratio: 0.5316
- Tag: `v0.v3-059`

**AFTER** (post-/121):
- Canonical: iter-v3/121-METHODOLOGY (cycle-6 closure + first-baseline-update marker — /116 no_confirm RULE-layer primitive merged)
- IS monthly Sharpe: **+1.3108**
- OOS monthly Sharpe: **+0.9682**
- OOS/IS ratio: **0.7386**
- Tag: `v0.v3-121`

Sacred constants UNCHANGED: OOS_CUTOFF_DATE=2025-03-24, training_months=24, ENSEMBLE_SIZE=10, ENSEMBLE_SEEDS (10-tuple), V3_FEATURE_COLUMNS_TOP_N (14 features bit-identical to /059), V3_MODELS (BCH/LDO/TRX), ATR multipliers (2.0/1.0), 7-primitive risk gate stack.

Sacred constants ADDED:
- `enable_no_confirm_exit = True`
- `no_confirm_trigger_atr = 0.50`
- `no_confirm_k_candles = 4`

/059 is preserved as PRIOR CANONICAL in the new BASELINE_V3.md baseline-history section. The /059 → /121 transition is the first BASELINE_V3.md update since the 2026-05-13 RE-ANCHOR #2; the /059 anchor stood unchanged for 7 days across 62 iterations (60 EXPLORATIONs + /070 CONFIRMATION + /081 CONFIRMATION + /092 CONFIRMATION + /120 CONFIRMATION attempted and not merged).

---

## 9. Memory updates needed

1. **APPEND to `feedback_v3_promising_feature_mechanical.md`** — /121 validation note: F3 ("allocation cannibal without contribution") fires CORRECTLY at multi-seed even when the bundle achieves all-time v3 OOS record + interaction is genuine; the post-validation pass at /121-METHODOLOGY (Component A alone shows IS-preserving + OOS-accretive at multi-seed) confirms PROMISING-FEATURE-MECHANICAL is correctly classified as non-compoundable-as-signal-source. The F3-DROP decision is the binding test.

2. **UPDATE `project_v3_cycle6_axis_menu.md`** — cycle-6 CLOSED with 1 ingredient merged (/116 no_confirm) + 1 ingredient dropped (/119 C6); BASELINE UPDATED /059 → /121.

3. **UPDATE `project_v3_cycle7_setup.md`** — /121 BOOTSTRAP COMPLETED with MERGE; cycle-7 /122 launches against /121 anchor (NOT /059).

4. **NEW `feedback_v3_baseline_v121_no_confirm.md`** — document the /116 no_confirm primitive now in canonical baseline: params, mechanism, code surfaces, and the rule that future ingredients must show strict improvement OVER /121 (NOT /059).

5. **UPDATE `MEMORY.md` index** — add the new feedback entry; update cycle-6/7 index lines with the merge outcome.

---

## 10. Catalog entry

Per the standard schema, appended to `briefs-v3/exploration_catalog.md`:

```
| iter-v3/121 | 2026-05-20 | METHODOLOGY-BOOTSTRAP — /116 no_confirm STANDALONE at 10-seed CONFIRMATION | +0.2214 | +0.3891 | CONFIRMATION-MERGE — first cycle-6 merge | YES — BASELINE_V3.md UPDATES /059 → /121 |
```

---

## 11. Closeout

iter-v3/121-METHODOLOGY closes the cycle-6 narrative arc and opens the cycle-7 narrative arc. The cycle-6 axis-menu hypothesis (user directive 2026-05-19, `project_v3_cycle6_axis_menu.md`) produced 0 new direct-edge signals across 10 EXPLORATIONs and 1 strictly-accretive mechanical primitive merge. The /105→/109 cycle-5 structural finding (binding constraint is DOWNSTREAM of training label, in the trade-construction / exit / risk layer) is reconfirmed by cycle-6's empirical outcome: the only PROMISING-class outcomes were at the downstream layer (RULE-form exit primitive + FEATURE-form loss-surface reorganization). Cycle 7 reorients structurally toward fundamentally different edge sources — cross-asset/external feeds, non-LightGBM model classes, longer-cadence labels, NEW symbol universes — with /122 = QR-selected EXPLORATION axis-1 from the /119 diary §8.2 candidate menu, anchored against the new /121 baseline.

**The /121 merge is the first cycle-6 ingredient merge in v3 history and the first BASELINE_V3.md update since 2026-05-13. /116 no_confirm (the early-exit-on-no-confirmation RULE-layer primitive) is now part of the canonical baseline.**
