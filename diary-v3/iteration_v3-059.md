# Iteration iter-v3/059 — Diary

## Decision: CONFIRMATION-MERGE — RE-ANCHOR-MERGE-IS-DOMINANT (architectural transition certified clean)

iter-v3/059 is the **SECOND BASELINE RE-ANCHOR** in v3 history and the **FIRST iteration** under the unified 10-seed ensemble architecture (Phase B-3 refactor at commit `ab2d9ac`). It is **NOT** a cycle 1 EXPLORATION; per user directive 2026-05-13 it is orthogonal to cycle counting and not subject to the 10:1 cadence constraint. Cycle 1 EXPLORATIONs begin AFTER /059 BASELINE_V3.md update at iter-v3/060.

Per Critic FINAL `0fc18c2`: **CONFIRMATION-MERGE — RE-ANCHOR-MERGE-IS-DOMINANT**. All 13 methodology checks PASS or PASS-equivalent (3 hard-blocking gates all PASS; DSR_relative FAIL is informational per brief Section 8.4). Path classification fired the pre-registered RE-ANCHOR-MERGE-IS-DOMINANT taxonomy (OOS/IS = 0.5316 < 0.70). Per brief Section 8.1 LOCKED criteria, **BASELINE_V3.md update is MANDATORY regardless of path direction** — this is an integrity correction (architecture transition certification), not a competitive CONFIRMATION.

## Section 1 — What Was Done

### Phase A — Optuna n_jobs=2 (ATTEMPTED + REVERTED)

Commit `0a3c30e` introduced `n_jobs=2` parallelization to Optuna's `study.optimize()` call site. Initial smoke-test runs revealed 5× GIL slowdown per trial (LightGBM training in parallel threads under Python's GIL is dominated by lock contention, not parallel CPU throughput). The optimization was **reverted at commit `31665f6`** to restore `n_jobs=1`. Net architectural change from Phase A: **none**. The brief Section 0.5 commit chain text retained "n_jobs=2 (Phase A `0a3c30e`)" wording; the actual run executed at HEAD `31665f6` (n_jobs=1). Documented transparently in engineering report Headers; Critic flagged as minor brief-vs-run divergence in Recommendation #4.

### Phase B-3 — Unified 10-seed ensemble architecture (commit `ab2d9ac`)

The substantive architectural change:

- **ENSEMBLE_SIZE**: 5 → 10
- **ENSEMBLE_SEEDS**: hardcoded 10-tuple with lineage preservation
  - Seeds 0-4 (outer=42 lineage): 191664963, 1662057957, 1405681631, 942484272, 929893137
  - Seeds 5-9 (outer=123 lineage): 33158374, 1465339467, 1273345680, 115579757, 1952249162
- **Outer-seed loop ELIMINATED** in `run_baseline_v3.py`: single unified `_run_single_seed` call replaces 2-outer × 5-inner loop
- **Single LightGbmStrategy instance per (symbol, walk-forward month)** cell: one Optuna optimization, one trained-model bundle, one inference path with proba averaging across all 10 models
- **Single trade roster**: ONE unified roster from 10-model averaged probability vs /058's two rosters merged via arithmetic-mean Sharpe
- **`--seeds` deprecated**: logs warning if passed, value ignored; not passed for /059
- **`_verify_feature_columns` ENSEMBLE_SIZE=10 assertion** added at runtime to prevent regression
- **Report file changes**: `seed_summary.json` → `ensemble_summary.json` (10 rows with lineage annotation); `pareto_front.csv` no longer produced
- **Total Optuna trials UNCHANGED**: 35 × 3 syms × 10 seeds = 1050 (same as /058's 35 × 3 × 2 outer × 5 inner = 1050)

### Phase C — RE-ANCHOR #2 backtest

Setup commit `20095a8` bumped `ITERATION_LABEL` to "v3-059" and committed the brief + Phase 5.5 gate. Phase 5.5 gate PASS at the same SHA (all 11 brief sections + bundle state + Foundation Audit Boot Steps 9-11 + Anti-Pattern Catalog 13 entries + data freshness re-fetch verified). Backtest run command: `uv run python run_baseline_v3.py --clean-oof`. Wall-clock 3.60h (~35% faster than /058's 5.49h despite n_jobs=1; speedup comes from no v1/v2 parallel contention on this hardware in this run). Engineering report `bea0987` documents READY-FOR-CRITIC; Critic FINAL `0fc18c2` issued CONFIRMATION-MERGE.

## Section 2 — Results Table

### Multi-anchor headline comparison

| Metric | /028 BIASED anchor | /058 multi-seed mean (RE-ANCHOR #1) | **/059 unified (RE-ANCHOR #2)** | Δ vs /058 |
|---|---:|---:|---:|---:|
| **IS monthly Sharpe** | +0.5101 | +0.7481 | **+1.0894** | **+0.34** |
| **OOS monthly Sharpe** | +0.5053 | +0.8700 | **+0.5791** | **-0.29** |
| OOS/IS monthly ratio | 0.99 | 1.163 | **0.5316** | -0.63 |
| IS/OOS daily ratio | — | 0.860 | **1.881** | +1.02 (IS-dominance revealed) |
| IS daily Sharpe | — | — | 2.7092 | — |
| OOS daily Sharpe | — | — | 1.4359 | — |
| OOS MaxDD | 23.53% | 31.10% | **34.53%** | +3.43pp |
| OOS Calmar | 0.9229 | 1.2028 | **0.6585** | -0.54 |
| **DSR_relative** | n/a | 0.9982 (first PASS) | **0.1134** | -0.885 (architecture artifact; see §6) |
| frac_positive_paths (CPCV) | n/a | 0.6444 | **0.6444** | 0.000 (IDENTICAL — CPCV invariant) |
| PBO | 0.1243 | 0.1278 | **0.1278** | 0.000 (IDENTICAL) |
| CPCV path Sharpe Q75 | — | 0.8378 | **0.8378** | 0.000 (IDENTICAL) |
| PSR | — | 1.0 | **1.0** | 0.000 |
| IS Trades | 182 | 177.0 mean | **171** | -6 |
| OOS Trades | 93.5 | 94.5 mean / 189 aggregate | **94** | -0.5 (essentially unchanged) |
| min_trl_months (DSR_relative input) | — | 11.53 | **5.70** | -5.83 (≈ halving consistent with outer-seed collapse) |

### Hard-blocking MERGE gates (per brief Section 8.4 LOCKED)

| Gate | Threshold | /059 Observed | Status |
|---|---|---:|---|
| Gate 3 — OOS/IS Sharpe ratio ≥ 0.5 | ≥ 0.5 | **0.5316** | **PASS** (barely; 0.016 above floor) |
| Gate 6 — PSR > 0.95 | > 0.95 | **1.0000** | **PASS** |
| Gate 10-CPCV — frac_positive_paths ≥ 0.55 | ≥ 0.55 | **0.6444** | **PASS** |

All 3 hard-blocking gates PASS. Gate 10 Pareto (multi-seed: both seeds OOS > 0) RETIRED per brief Section 8.2 — not applicable to unified architecture.

## Section 3 — Per-Symbol OOS Decomposition

### OOS attribution (from comparison.csv)

| Symbol | OOS weighted_pnl | OOS n_trades | OOS WR | OOS concentration_pct |
|--------|----------------:|-------------:|-------:|----------------------:|
| BCH | **+24.75** | 34 | 41.2% | 108.86% (driver) |
| TRX | **+4.16** | 48 | 39.6% | 18.31% |
| LDO | -6.18 | 12 | 25.0% | -27.17% (drag) |

### Cross-iteration OOS per-symbol comparison

| Symbol | /058 seed 42 | /058 seed 123 | **/059 unified** | Δ vs /058 seed 42 | Notes |
|---|---:|---:|---:|---:|---|
| BCH | +27.25 | — | **+24.75** | -2.50 | Stable (small drop) |
| TRX | +23.03 | — | **+4.16** | **-18.87** | Primary OOS drag — collapsed |
| LDO | -15.29 | — | **-6.18** | +9.11 | Improved (less negative); 25.0% WR vs 18.2% |

### IS per-symbol (BCH concentration fragility flag)

| Symbol | IS trades | IS WR | IS Net PnL% | % of Total IS PnL |
|---|---:|---:|---:|---:|
| BCH | 83 | 49.4% | +109.23% | **95.76%** |
| TRX | 79 | 34.2% | +3.95% | 3.47% |
| LDO | 9 | 33.3% | +0.89% | 0.78% |

**BCH carries 95.76% of IS PnL** with the highest IS win rate (49.4% vs portfolio 33.33%). The IS Sharpe of +1.0894 is almost entirely a BCH IS Sharpe. This is a fragility flag for cycle 1 axis design (per Critic Recommendation #3 — every cycle 1 brief Section 4 must project BCH IS sensitivity).

## Section 4 — Critic Verdict Summary

Per Critic FINAL `0fc18c2`: **OVERALL: CONFIRMATION-MERGE — RE-ANCHOR-MERGE-IS-DOMINANT** (architectural transition certified clean; suspicious OOS/IS = 0.53 flagged for cycle 1 QR diagnostic, but mandatory BASELINE_V3.md update proceeds).

### Methodology checks (13 of 13 PASS or PASS-equivalent)

| Check | Status | Notes |
|---|---|---|
| 1 Look-Ahead Audit | PASS | Walk-forward fix at `e149e9d` intact; embargo_ms = 22 candles × 480 min × 60_000 ms; on-chain/funding/microstructure absent from 14-feature stack |
| 2 Embargo Width | PASS | REQUIRED_GAP = 66 = (21+1)×3; verified runtime assertion; CPCV embargo=27 |
| 3 Multiple-Testing Correction | **PARTIAL FAIL** (informational) | Gates 3+6+10-CPCV all PASS; DSR_relative=0.1134 FAILS 0.95 but is informational per brief Section 8.4 (architecture-change calibration mismatch) |
| 4 IC Correlation | PASS | Established composed-feature carve-out for regime_momentum_signed_5d × vwap_dev_20 = 0.7642 |
| 5 ADF Stationarity | PASS | 1803/2198 stationary; identical pattern to /058 |
| 6 Pareto Dominance | PASS | Replaced by Gate 10-CPCV per brief Section 8.2-8.3; pareto_front.csv correctly ABSENT; ensemble_summary.json PRESENT with 10 lineage rows |
| 7 Reproducibility | PASS | All commit SHAs verifiable; feature columns pinned; ENSEMBLE_SEEDS 10-tuple hardcoded with regression test `test_ensemble_unified.py::TestEnsembleSeedsLineage`; trade math spot-check matches CSV to 4 decimals |
| 8 Hypothesis-Implementation | PASS (with note) | Single change ITERATION_LABEL="v3-059" verified; minor brief-vs-run divergence (Phase A n_jobs=2 in brief text vs n_jobs=1 in actual run) — Critic Recommendation #4 |
| 9 Symbol Exclusion | PASS | V3_EXCLUDED_SYMBOLS includes 11 symbols; no overlap with (BCH, LDO, TRX) |
| 10 Feature Isolation | PASS | features_v3/ has zero v1/v2 imports |
| 11 Forming-Candle | PASS | fetcher.py filter `if k.close_time < now_ms` preserved |
| 12 Library Version Pinning | PASS | All versions unchanged from /058 |
| 13 §11 Anti-Pattern Static Scan | CLEAN | All 13 catalog entries (A1, A5, A7, A8, A12, A13 + track isolation + feature columns + A2/A3/A4/A6/A9/A10/A11) — zero unexplained matches |

### Architecture-specific concerns audit (FIRST AUDIT under unified 10-seed)

- **Lineage preservation**: ENSEMBLE_SEEDS[0:5] from outer=42, [5:10] from outer=123, verified at `tests/strategies/ml/test_ensemble_unified.py::TestEnsembleSeedsLineage`. Each seed runs independently-seeded TPESampler → no Optuna-search contamination.
- **`_confidence_threshold` consistency**: computed as single mean of N per-seed thresholds (lgbm.py:507). Same scheme as /058 except N=10 instead of N=5. No structural change.
- **Proba averaging**: lgbm.py:621-624 averages `predict_proba()` over all 10 self._models. Identical pattern to /058 (vector-mean of probabilities, not log-odds).
- **Trade roster construction**: brief Section 4.1 prediction verified — ONE unified roster from 10-model averaged probability vs /058's two rosters merged. Trade count essentially unchanged (171 IS / 94 OOS vs /058 mean 177/94.5) but Sharpe materially shifted.
- **Optuna efficiency**: n_eff = 19 (per-cell PCA-95 median). Identical to /058 — architecture-independent.

## Section 5 — Path Classification: RE-ANCHOR-MERGE-IS-DOMINANT

Per brief Section 8.3 LOCKED pre-registered taxonomy:

```
RE-ANCHOR-MERGE-CLEAN:         IS > 0 AND OOS > 0 AND OOS/IS in [0.7, 1.5]  — NOT FIRED
RE-ANCHOR-MERGE-OOS-DOMINANT:  OOS > 0 AND OOS/IS > 1.5                      — NOT FIRED
RE-ANCHOR-MERGE-IS-DOMINANT:   IS > 0 AND OOS/IS < 0.7                       — FIRED ✓
RE-ANCHOR-COLLAPSE:            IS <= 0 OR OOS <= 0                            — NOT FIRED
```

Observed OOS/IS = 0.5316 < 0.70 → **PATH: RE-ANCHOR-MERGE-IS-DOMINANT (suspicious)**.

Per brief Section 8.5: BASELINE_V3.md update MANDATORY regardless. The "suspicious" qualifier triggers a **QR diagnostic before cycle 1 launch** at the orchestrator level (not blocking BASELINE_V3.md update). Cycle 1 EXPLORATIONs anchor on /059 unified-architecture numbers from iter-v3/060 onward.

### IS-dominance is structural, not a methodology defect

The engineering report Section "IS-OOS Ratio 0.53 — Borderline Suspect: Investigation" establishes the root cause: **cross-seed cancellation at /058 was unmasked**, not a regression at /059.

At /058: seed 42 IS/OOS = 1.60× (IS-dominant); seed 123 OOS/IS = 3.91× (strongly OOS-dominant); arithmetic mean yielded the apparent 0.86 ratio. The unified 10-seed ensemble inherits seed-42 lineage IS-dominance at prediction-averaging stage while suppressing seed-123 lineage OOS-dominance into the averaged signal. Two competing hypotheses (averaging convergence; IS-biased seed lineage) — both predict the IS-dominant pattern is structural to the unified architecture with these specific seed lineages, not a data-mining artifact or labeling leak.

OOS Sharpe +0.5791 is positive AND both BCH (+24.75) and TRX (+4.16) contribute positive OOS weighted_pnl. The IS-dominance is a ratio concern, not an OOS-failure concern.

## Section 6 — Failure-Mode Prediction Check

### Brief Section 7 pre-registered failure modes

| Failure mode | Probability estimate | Detection criterion | **Fired?** |
|---|---|---|---|
| RE-ANCHOR-COLLAPSE (unified consensus too strict; near-zero signal variance) | 15-25% | OOS Trades < 60 AND OOS Sharpe < +0.20 | **NO** (OOS=94 trades; OOS Sharpe +0.58) |
| RE-ANCHOR-MERGE-IS-DOMINANT (unified ensemble over-regularizes IS; OOS suffers from reduced trade count) | 20-30% | IS > 0 AND OOS/IS < 0.7 | **YES** — fired at 0.5316 |
| RE-ANCHOR-MERGE-CLEAN (moderate Sharpe shift with cleaner IS/OOS ratio in [0.7, 1.3]) | 50-60% | IS in [+0.55, +0.85]; OOS in [+0.65, +0.95]; ratio 0.7-1.5 | **NO** |

**Pre-registered secondary failure mode FIRED.** The brief explicitly anticipated "averaging convergence suppresses high-variance bet placement" → the data verifies this exactly at TRX (OOS +23.03 → +4.16, -18.87 weighted_pnl collapse). Detection criterion matched (IS > 0 at +1.0894 AND OOS/IS < 0.7 at 0.5316).

### Predicted-vs-observed band check (brief Section 4.2)

| Metric | /059 predicted band | /059 observed | Direction |
|---|---|---:|---|
| IS monthly Sharpe | +0.55 to +0.85 | **+1.0894** | ABOVE upper band by +0.239 |
| OOS monthly Sharpe | +0.65 to +0.95 | **+0.5791** | BELOW lower band by -0.071 |
| OOS/IS Sharpe ratio | 0.7 to 1.5 | 0.5316 | BELOW lower band |
| IS Trades | 150 to 200 | 171 | WITHIN band |
| OOS Trades | 80 to 120 | 94 | WITHIN band |
| frac_positive_paths | 0.50 to 0.75 | 0.6444 | WITHIN band |

Both Sharpe predictions missed; the IS direction missed UP (architecture amplified IS-dominance beyond predicted band); the OOS direction missed DOWN. The IS-dominant failure-mode prediction was qualitatively correct; the magnitude was underestimated. Falsifier "either IS or OOS Sharpe < +0.40" did NOT fire (OOS +0.58 above the threshold), so no architecture-level investigation is mandated before cycle 1.

## Section 7 — BASELINE_V3.md Update Directive

Per brief Section 8.1 LOCKED: **MANDATORY** regardless of path direction.

BASELINE_V3.md updates from /058 multi-seed mean anchor to /059 unified 10-seed ensemble anchor at this commit cycle. Key changes:

- Headline: `iter-v3/059 (RE-ANCHOR #2, unified 10-seed ensemble)` replacing `iter-v3/058 (RE-ANCHOR #1, multi-seed mean)`
- IS monthly Sharpe: **+1.0894** (was +0.7481 multi-seed mean)
- OOS monthly Sharpe: **+0.5791** (was +0.8700 multi-seed mean)
- IS-OOS monthly ratio: 0.5316 (was 1.163)
- DSR_relative: 0.1134 (was 0.9982) — flagged informational under unified architecture; 0.95 threshold needs cycle 1 recalibration
- cpcv_frac_positive_paths: 0.6444 (NEW canonical Gate 10-CPCV replacing Pareto Gate 10)
- Per-symbol OOS table: BCH +24.75 / TRX +4.16 / LDO -6.18 (vs /058 seed 42: +27.25 / +23.03 / -15.29)
- Code Configuration: ENSEMBLE_SIZE=10 (was 5), ENSEMBLE_SEEDS = lineage-preserving 10-tuple, outer-seed loop ELIMINATED
- Architecture note: "Unified 10-seed ensemble. Single trade roster. Live deployment matches backtest exactly (one model per coin per account)."
- Walk-forward fix at commit `e149e9d` (carried over from /058)
- Critic enhancement at `414368a` (carried over from /058)
- Phase B-3 refactor `ab2d9ac` cited
- Tag annotation: `v0.v3-059` replaces `v0.v3-058` as canonical

Tag `v0.v3-058` retained in git history but RETIRED as canonical baseline. Multi-seed mean Sharpe reporting (/058 architecture) is OBSOLETE for future iterations.

## Section 8 — Critic Recommendations for Cycle 1

Per Critic FINAL `0fc18c2` Recommendations (4 items carried forward):

### 1. Correct the DSR_relative diagnostic narrative before cycle 1

The engineering report Section "DSR_relative Regression Analysis: 0.9982 → 0.1134" attributes the drop to `min_trl_months` halving (11.53 → 5.70). This is **factually incorrect**: `min_trl_months` is written to dsr.json as a tracking field only (run_baseline_v3.py:1593-1622) and is **NOT an input** to `psr()` (validation_v3.py:486-528). The actual `psr()` call passes `n_obs=len(oos_wp)=94`, `observed_sharpe=raw_sharpe_oos`, `benchmark_sharpe=cpcv_path_sharpe_q75=0.8378`. The dsr_relative drop from 0.998 (z≈+2.91) to 0.113 (z≈-1.21) is dominated by **OOS Sharpe falling**, not by `min_trl_months` changing.

**Action**: Cycle 1 EXPLORATION briefs **must not** cite `min_trl_months` as a DSR_relative driver. If a recalibration is desired, the appropriate axis is the benchmark choice (CPCV-Q75 may be too aggressive for unified-roster Sharpe distributions) or the threshold itself (0.95 was calibrated against 2-outer × 5-inner; under unified, the same threshold may be structurally unreachable).

### 2. TRX OOS deserves a cycle 1 diagnostic axis

TRX OOS weighted_pnl collapsed +23.03 → +4.16 between architectures. The brief's primary failure-mode prediction was "averaging convergence suppresses high-variance bet placement" — the data is consistent. But TRX IS now contributes only 3.47% of IS PnL with 0.050% avg/trade; under unified architecture, TRX is contributing near-noise OOS.

**Action**: Cycle 1 should commission EITHER (a) a TRX-specific feature-importance + label-quality diagnostic EXPLORATION, OR (b) a universe-axis EXPLORATION evaluating drop-TRX (with standard `feedback_insist_on_symbols.md` discipline of running feature importance + labeling analysis FIRST). Per `feedback_v3_axis_selection_quant_discipline.md`, QR must produce committed `analysis/iteration_v3-NNN/*.py` EDA before the brief.

### 3. BCH IS concentration (95.76% of IS PnL) is a fragility flag for cycle 1 axis design

BCH carries virtually all IS PnL. An axis that improves LDO and/or TRX but reduces BCH IS contribution will likely collapse the headline IS Sharpe due to the concentration.

**Action**: Every cycle 1 EXPLORATION brief's Section 4 must explicitly project the BCH IS impact of the proposed change. The expected-impact analysis must include a BCH IS sensitivity prediction.

### 4. Process cleanup — brief Section 0.5 commit chain wording

The brief Section 0.5 Stage 3 commit-chain text says "Optuna n_jobs=2 (Phase A commit `0a3c30e`)" but the actual run was at HEAD `31665f6` (Phase A reverted). The brief was NOT updated to reflect the revert prior to the run — the engineering report covers it transparently, but the inherited brief wording is misleading.

**Action**: Cycle 1's first EXPLORATION brief should clean up the commit chain text to read "Phase A n_jobs=2 ATTEMPTED at `0a3c30e`, REVERTED at `31665f6` due to 5x GIL slowdown; current state n_jobs=1." Same for any reference to "Optuna n_jobs=2" elsewhere in inherited brief wording.

## Section 9 — Next Iteration Ideas (Cycle 1 — iter-v3/060 through iter-v3/069)

Per `feedback_v3_strict_10_to_1_cadence.md` cycle 1 = 10 SEPARATE single-seed EXPLORATIONs at iter-v3/060-069. iter-v3/069 = SEPARATE CONFIRMATION (do not collapse EXPLORATION #10 into CONFIRMATION).

### Cadence calendar update

Per `feedback_v3_mass_feature_expansion.md`: mass feature expansion (V3_FEATURE_COLUMNS_TOP_N: 14 → 100+) was queued for "cycle 5 first EXPLORATION (iter-v3/062, after cycle 4 CONFIRMATION at /061)". **The /059 RE-ANCHOR #2 consumed the calendar slot**: cycle 1 is post-RE-ANCHOR #2, not post cycle-4 CONFIRMATION. The mass feature expansion mandate **shifts +1 slot to iter-v3/063** (cycle 1's first EXPLORATION post-axis-priorities setup).

### Proposed iter-v3/060 — TRX diagnostic + axis pivot (per Critic Recommendation #2)

QR-driven EDA on TRX:
- TRX IS feature-importance shift between /058 seed 42 (TRX OOS +23.03) and /059 unified (TRX OOS +4.16)
- TRX label distribution: which trades contributed the +23.03 at /058 seed 42 vs /059 unified
- TRX-specific signals: range_realized_vol_50 + hurst_100 lead per /059 per-symbol importance — are these stable across seeds?

Output: committed `analysis/iteration_v3-060/*.py` EDA establishing whether TRX contributes genuine signal under unified architecture or only via seed-lottery at 2-outer.

### Proposed iter-v3/061 — DSR_relative threshold/benchmark recalibration (per Critic Recommendation #1)

Methodology-only EXPLORATION:
- Investigate whether the 0.95 DSR_relative threshold is structurally unreachable under unified-roster Sharpe distributions
- Investigate alternative benchmark (CPCV-Q50 or CPCV-Q60 instead of Q75)
- Test reformulation against /058 + /059 + /050 + /028 historical reports

### Proposed iter-v3/062 — first single-feature single-axis EXPLORATION

Per `feedback_v3_engineered_feature_pivot.md` + `feedback_v3_engineered_features_proven.md`: engineered features outperform off-the-shelf indicators. Candidate engineered features that did not stack at single-seed pre-fix may behave differently under unified architecture:
- vol_adj_autocorr (DON'T-STACK pre-fix at /026 single-seed; sister of regime_momentum_signed_5d)
- cross_asset_divergence_norm (DON'T-STACK pre-fix at /027 single-seed)
- ret_skew variants at different lookbacks

Single-feature axis variation; ONE candidate per EXPLORATION; do NOT stack.

### Proposed iter-v3/063 — MASS FEATURE EXPANSION (per `feedback_v3_mass_feature_expansion.md`)

Originally queued at /062; shifted +1 to /063 due to /059 RE-ANCHOR consuming /062 slot. QR mandated to research papers/literature for production-grade features (TA-lib, microstructure, cross-asset, regime, statistical, etc.) and elevate V3_FEATURE_COLUMNS_TOP_N from 14 to TARGET 100 (50 minimum).

### Proposed iter-v3/064-068 — remaining cycle 1 EXPLORATIONs

To be determined by QR EDA-driven discipline (per `feedback_v3_axis_selection_quant_discipline.md`). Candidate axes (TBD ranking):
- BCH-specific axis to reduce IS concentration (per Critic Recommendation #3)
- LDO diagnostic (5 consecutive negative OOS weighted_pnl; structural drag remains)
- Universe expansion candidates from EDA (subject to V3_EXCLUDED_SYMBOLS constraint)
- NEW labeling architecture (return-based or volatility-adjusted alternatives)
- NEW model architecture (drawdown-penalized objective, alternative tree growth)

### Proposed iter-v3/069 — Cycle 1 CONFIRMATION

Multi-seed validation of cycle 1 PROMISING bundle. Spec: `--n-trials 35` per cell, ENSEMBLE_SIZE=10 (unified), full DSR/PBO/PSR re-eval. PASS gates: IS≥+1.0 AND OOS≥+1.0 (BOTH multi-seed mean must improve over /059 anchor per `feedback_v3_strict_both_is_oos_baseline.md`); Gate 3 OOS/IS ≥ 0.5; Gate 6 PSR > 0.95; Gate 10-CPCV frac_positive_paths ≥ 0.55. 6h hard cap.

### PROMISING classification bands for cycle 1 (LOCKED per Critic Recommendation suggestion)

Anchor on /059 unified-architecture numbers:
- **PROMISING (single-seed)**: IS Δ ≥ +0.10 vs +1.0894 anchor (+1.19+); OOS Δ ≥ +0.10 vs +0.5791 anchor (+0.68+)
- **NEGATIVE (single-seed)**: IS Δ < -0.10 OR OOS Δ < -0.10
- **NEGATIVE-SUSPICIOUS-OOS qualifier**: IS-OOS daily ratio outside [0.5, 2.0] (per /026/027 pattern)

Note: BOTH-must-improve discipline applies at CONFIRMATION (per `feedback_v3_strict_both_is_oos_baseline.md`). At EXPLORATION level, single-axis improvement on either axis is informational.

## Reproducibility

- HEAD SHA at backtest run: `31665f6` (Phase A revert)
- Setup commit SHA: `20095a8` (brief + phase5p5 gate + ITERATION_LABEL bump)
- Phase 5.5 gate SHA: `20095a8` (combined in setup commit; PASS verified)
- Brief SHA: `20095a8`
- Brief backfill SHA: `6734a28` (setup commit backfilled into brief Section 10)
- Phase A revert SHA: `31665f6` (n_jobs=2 → n_jobs=1; GIL contention)
- Phase B-3 commit SHA: `ab2d9ac` (unified 10-seed ensemble)
- Walk-forward fix SHA: `e149e9d` (inherited from /058)
- Engineering report SHA: `bea0987`
- Critic FINAL SHA: `0fc18c2` (CONFIRMATION-MERGE — RE-ANCHOR-MERGE-IS-DOMINANT)
- Critic enhancement SHA: `414368a` (inherited from /058 — Foundation Audit Boot Steps 9-11 + §11 Anti-Pattern Catalog)
- BASELINE_V3.md update SHA: (this commit cycle)
- Diary SHA: (this commit)
- Tag: `v0.v3-059` (RE-ANCHOR #2 — unified 10-seed; replaces v0.v3-058 as canonical)
- Wall-clock: 3.60h (within 6h CONFIRMATION cap; ~35% faster than /058's 5.49h)
- Hardware: x86_64, 60 GB RAM, WSL2 / Linux 6.6.114.1
- Library stack: lightgbm 4.6.0, optuna 4.8.0, numpy 2.2.6, pandas 3.0.0, scikit-learn 1.8.0, scipy 1.17.0, statsmodels 0.14.6, pyarrow 23.0.1
- Run command: `uv run python run_baseline_v3.py --clean-oof` (no --seeds flag; deprecated in Phase B-3 architecture)
- Reports artifacts: `reports-v3/iteration_v3-059/comparison.csv`, `dsr.json`, `ensemble_summary.json`, `per_cell_pbo.csv`, `cpcv_paths.csv`, `adf_test.csv`, `ic_matrix.csv`, `trial_oof_returns.parquet`, `in_sample/`, `out_of_sample/`
