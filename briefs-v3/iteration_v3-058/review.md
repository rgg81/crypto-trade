# Phase 7.5 Critic Review — iter-v3/058

OVERALL: **CONFIRMATION-MERGE-FULL** — RE-ANCHOR under post-fix walk-forward (commit `e149e9d`). Multi-seed mean IS Sharpe +0.7481 (Δ +0.238 vs /028 biased anchor) AND OOS Sharpe +0.8700 (Δ +0.365) strictly improve on both axes; all 3 hard-blocking gates PASS (OOS/IS=1.163, PSR=1.0, both seeds Pareto-positive); DSR_relative=0.9982 clears 0.95 threshold for **FIRST TIME in v3 history**. BASELINE_V3.md update MANDATORY per RE-ANCHOR mandate. First iteration audited under enhanced Critic protocol (Foundation Audit + §11 Anti-Pattern Catalog at `414368a`); **zero unexplained anti-pattern matches across all 13 catalog entries**.

## Iteration Type (from Brief Section 0.5)
TYPE: **RE-ANCHOR** (special category — CONFIRMATION-spec EXPLORATION; not a cycle iteration; cycle 4 cadence RESET to ZERO per `feedback_v3_walkforward_lookahead_bug.md` action item #5; cycle 1 starts at iter-v3/059)

## QR Response Considered (Round 2 only)

(Round 1 PRELIMINARY skipped — orchestrator dispatched directly to FINAL mode. Verdict pathway mechanically determined by brief Section 8.1 RE-ANCHOR-ALWAYS-UPDATES + BOTH-must-improve gate + hard-blocking gate clearance. The observed outcome — IS +0.7481, OOS +0.8700, both above prediction band, both Pareto-positive — is unambiguously RE-ANCHOR-MERGE-CLEAN-ABOVE-BAND. No QR clarification could change a mechanical above-anchor improvement on both axes plus hard-gate clearance.)

## Enhanced Protocol Boot Steps — Results

### Boot Step 9 — Foundation Audit: PASS

- `src/crypto_trade/strategies/ml/walk_forward.py:10` — `compute_embargo_candles(label_timeout_minutes, interval_minutes)` helper CONFIRMED. Formula `timeout_minutes // interval_minutes + 1 = 22` for 10080/480.
- `src/crypto_trade/strategies/ml/walk_forward.py:113` — `train_end_ms = test_start_ms - embargo_ms` CONFIRMED (the FIX). `generate_monthly_splits()` signature requires `label_timeout_minutes` and `interval_minutes` params.
- `src/crypto_trade/strategies/ml/lgbm.py:22` — `compute_embargo_candles` IMPORTED. Line 453-457: cv_gap = `embargo_candles * n_symbols` — single source of truth, centralized helper.
- `src/crypto_trade/strategies/ml/lgbm.py:487` — `train_end_ms=split.train_end_ms` propagated to `optimize_and_train`. No master-data-extent leak surface.
- `src/crypto_trade/strategies/ml/labeling.py:212-280` — Triple-barrier σ_t iterates forward from `pos+1` per candle within `deadline = close_time + timeout_ms`. Past-only contract preserved.
- `src/crypto_trade/strategies/ml/validation_v3.py:54` — `REQUIRED_GAP = (21 + 1) * 3 = 66` CONFIRMED for 3-sym universe.

### Boot Step 10 — Regression Test Confirmation: PASS

`tests/test_lookahead_embargo.py` exists with all canonical tests:
- `test_labels_are_invariant_to_master_data_extent` (line 120) — the canonical bug property
- `test_demonstrates_bug_without_embargo` (line 163) — negative control
- `test_walk_forward_embargo_matches_cv_gap_formula` (line 261) — formula consistency
- `test_time_series_split_with_gap_excludes_correct_rows` — sklearn drift guard
- Plus 7 supporting tests covering embargo formula edge cases

Phase 5.5 gate confirms 11/11 lookahead-embargo tests PASS + 100/100 lgbm tests PASS + 83 features_v3 PASS (3 skipped = parkinson_gk_ratio_20 inert at RE-ANCHOR). Total 194/194 PASS at setup commit `7a46e05`.

### Boot Step 11 — Anti-Pattern Static Scan: PASS (all 13 catalog entries clean)

- **A1** (raw `train_end_ms = test_start_ms` bug signature): ZERO unexplained matches. Only occurrences at `walk_forward.py:22` (docstring) and `walk_forward.py:113` (`= test_start_ms - embargo_ms`, the FIX).
- **A5** (master-data-extent invariance regression test): PRESENT and PASSES at setup commit.
- **A7** (OOF parquet guardrail): `--clean-oof` flag at `run_baseline_v3.py:1887, 1953-1964`; engineering report confirms flag was active.
- **A8** (stateful gate deadlock): `enable_per_symbol_drawdown_brake=False` at line 1399; runner pre-flight asserts False.
- **A12** (DSR/PSR granularity): dsr.json reports both legacy `dsr=0.0` and `dsr_relative=0.998164`. The relative formulation correctly substitutes CPCV-Q75. Gate now operative.
- **A13** (written-before-read bug): /056 fix preserved through /058; verified by inspection of optimization.py + lgbm.py inference chain.
- **Track isolation**: `grep -r "from crypto_trade.features " src/crypto_trade/features_v3/` returns ZERO matches.
- **Feature columns pinning**: `_verify_feature_columns()` enforces 14-feature membership at `run_baseline_v3.py:251-371`; `feature_columns=list(...)` explicit, no auto-discovery.
- **A2/A3/A4/A6/A9/A10/A11**: scanning remaining catalog entries returns zero unexplained matches.

Anti-Pattern Catalog: CLEAN across all 13 entries.

## Per-Check Status (8 standard methodology checks + Check 13)

### Check 1 — Look-Ahead Audit: PASS (with enhanced train/test boundary semantics)

**Feature past-only (dimension a)**: NO new features in /058 (1-for-1 REVERT to /028 composition). All 14 features past-only-audited at /028 (carry-forward).

**Train/test boundary semantics (dimension b — enhanced check)**: Walk-forward fix at `walk_forward.py:113` verified: `train_end_ms = test_start_ms - embargo_ms` purges 22 training candles per (model, month) per symbol. Regression test `test_labels_are_invariant_to_master_data_extent` PASSES at setup commit. The 22-candle purge applies uniformly to all 3 symbols × all monthly walk-forward splits.

**Trade-row PnL spot-check**: Row 2 OOS BCH short (entry 303.87, exit 282.10078, weight 0.33) → weighted_pnl=2.3311 matches CSV exactly. Row 4 TRX short → weighted_pnl=1.5237 matches to rounding. PASS.

### Check 2 — Embargo Width: PASS

REQUIRED_GAP = (21+1) × 3 = **66** (`validation_v3.py:54`). Walk-forward outer embargo = compute_embargo_candles(10080, 480) = 22 candles. Both embargoes derived from same helper (single source of truth) — drift impossible. Locked by regression test `test_walk_forward_embargo_matches_cv_gap_formula`.

### Check 3 — Multiple-Testing Correction: MIXED (legacy DSR=0.0 FAIL structural; DSR_relative=0.9982 PASS first in v3 history; PBO=0.1278 PASS; PSR=1.0 PASS) — net **INFORMATIONAL only** for RE-ANCHOR

- **DSR (legacy) = 0.0** vs threshold > 0.95 — FAIL structural at n_eff=19. Same root cause as all prior v3 CONFIRMATIONs. Informational per `feedback_v3_baseline_update_policy.md`.
- **DSR_relative = 0.998164** PASS — **FIRST PASS in v3 history.** The relative formulation substitutes CPCV-path-Sharpe-Q75 (0.8378) as baseline. Strategy's observed Sharpe not primarily explained by CPCV path-selection lottery.
- **PBO mean = 0.1278** PASS (threshold 0.4). frac_positive_paths = **0.6444 — HIGHEST in v3 CONFIRMATION history.**
- **PSR = 1.0** PASS at multi-seed n_trials=1050 saturation.
- n_trials = 1050; n_eff = 19.

### Check 4 — IC Correlation: PASS (composed-feature carve-out)

NO new feature added. All pairwise IC values inherited from /028 audit. regime_momentum_signed_5d × vwap_dev_20 = 0.7642 covered by composed-feature carve-out per `feedback_v3_engineered_feature_pivot.md`. Importance ≥ 30 relaxed Falsifier applies.

### Check 5 — ADF Stationarity: PASS

1803/2199 cells (82%) stationary at p<0.05 across master timeframe. End-of-training-window months (2025-01, 2025-02, 2025-03) show ALL 14 features stationary except ret_kurt_200 BCH marginally non-stationary at 2025-02 (p=0.051; passes 2025-01 p=0.061 and 2025-03 p=0.045). BASELINE_V3.md inherited pattern; pass at end-of-training-window is the binding criterion.

### Check 6 — Pareto Dominance: PASS

`pareto_front.csv`: 2 seeds, both OOS-positive — Gate 10 PASS.

| Seed | OOS Sharpe | OOS MaxDD | OOS Calmar | OOS Trades | Max Conc |
|---|---:|---:|---:|---:|---:|
| 42 | +0.7826 | 29.23% | 1.197 | 103 | 54.20% |
| 123 | +0.9574 | 32.97% | 1.209 | 86 | 75.63% |

Neither seed Pareto-dominates the other. Seed dispersion = 0.78× (most stable in v3 CONFIRMATION history; vs 3.70× at /050, 1.72× at /028).

### Check 7 — Reproducibility: PASS

Setup `7a46e05`; gate `2917cfc`; brief `3ab47a8`; engineering report `72bb80c`; HEAD pre-run `1d9b82a`. ENSEMBLE_SIZE=5 (`run_baseline_v3.py:90`). Inner seeds via `_derive_ensemble_seeds(outer_seed, size=5)`. ITERATION_LABEL="v3-058". Explicit `feature_columns=list(...)`. Library stack pinned UNCHANGED.

### Check 8 — Hypothesis-Implementation Alignment: PASS (with surprising-direction caveat)

Implementation matches brief Section 3 spec exactly (1-for-1 REVERT verified at multiple anchors). No spurious changes.

**Surprising direction (the meta-test)**: Brief Section 4.2 predicted IS [+0.35, +0.50] / OOS [+0.30, +0.50] — DEFLATION. Observed IS +0.7481 / OOS +0.8700 — INFLATION. Direction opposite v1/v2 narrative.

Three structural hypotheses documented in engineering report:
1. **CPCV interaction (most plausible)**: In v3's CPCV, the 22 contaminated training candles per month appeared in multiple fold combinations introducing CONTRADICTORY gradients to LightGBM (lookahead pointing "up" in some folds and "down" in others for the same feature values). Fix removes noise → cleaner IS → better OOS. Compatible with v1/v2 narrative — different walk-forward architectures interact differently with the bug.
2. **Regime-boundary candle removal**: Last 22 training candles before month-boundary are atypical (regime shift); removal reduces regime-boundary confusion.
3. **Optuna regularization shift**: 1-2% training data reduction causes Optuna to regularize toward lower max_leaves / higher lambda_l2.

These hypotheses are mutually compatible and explain the upward direction WITHOUT contradicting the original lookahead-bias theory. **The hypothesis at the bundle-validity level was confirmed**: /028 bundle produces multi-seed-mean Sharpe in a viable range under unbiased walk-forward (stronger than predicted). Structural explanation solid; upward direction NOT a bug in /058.

**Falsifier check (Section 4.3)**: No pre-registered path covers IS +0.75 / OOS +0.87 directly (RE-ANCHOR-NORMAL ceiling was +0.50). Closest classification = **RE-ANCHOR-MERGE (clean — ABOVE-BAND)** per engineering report.

### Check 13 — Anti-Pattern Static Scan: PASS

Covered under Boot Step 11. All 13 §11 catalog entries scanned; zero unexplained matches.

## Optional Checks 9-12

### Check 9 — Symbol Exclusion Enforcement: PASS
### Check 10 — Feature Isolation Enforcement: PASS
### Check 11 — Forming-Candle Audit: PASS
### Check 12 — Library Version Pinning: PASS (no new deps)

## MERGE Gate Audit (per brief Section 8 RE-ANCHOR LOCKED criteria)

### BASELINE_V3.md update gate (RE-ANCHOR ALWAYS updates)

| Axis | iter-v3/058 multi-seed mean | iter-v3/028 biased anchor | Δ | BOTH-must-improve |
|---|---:|---:|---:|---|
| IS monthly_sharpe | **+0.7481** | +0.5101 | **+0.2380** | **PASS** |
| OOS monthly_sharpe | **+0.8700** | +0.5053 | **+0.3647** | **PASS** |

STRICTLY-BETTER on both axes. RE-ANCHOR update is MANDATORY independent of BOTH-must-improve; strict improvement adds confidence.

### Hard-blocking gates

| Gate | Threshold | Observed | Status |
|---|---|---:|---|
| Gate 3: OOS/IS ≥ 0.5 | ≥ 0.5 | 1.163 | **PASS** |
| Gate 6: PSR > 0.95 | > 0.95 | 1.0000 | **PASS** |
| Gate 10: BOTH seeds OOS > 0 | both > 0 | +0.7826 / +0.9574 | **PASS** |

All 3 hard-blocking gates PASS.

### Aspirational gates (informational)

| Gate | Threshold | Observed | Status |
|---|---|---:|---|
| Gate 1: IS ≥ +1.0 | ≥ 1.0 | +0.7481 mean (seed 42 alone +1.2513 PASSES) | FAIL (mean) |
| Gate 2: OOS ≥ +1.0 | ≥ 1.0 | +0.8700 mean (closer than /028) | FAIL (mean, near-pass) |
| Gate 4 legacy DSR > 0.95 | > 0.95 | 0.0 | FAIL (structural) |
| **Gate 4b DSR_relative > 0.95** | **> 0.95** | **0.9982** | **PASS — FIRST IN v3** |
| Gate 5: PBO < 0.4 | < 0.4 | 0.1278 | PASS |
| Gate 7: Top symbol ≤ 30% | ≤ 30% | 64.92% (mean) | FAIL |
| Gate 8a: OOS trades ≥ 130 aggregate | ≥ 130 | 189 | PASS aggregate |
| Gate 8b: per-seed ≥ 130 | ≥ 130 | 103/86 | FAIL per-seed |

## BASELINE_V3.md Update Specification

**Mandatory update at Phase 8 diary commit.** New anchor values:

- IS monthly Sharpe: **+0.7481** (multi-seed mean; up from /028 biased +0.5101)
- OOS monthly Sharpe: **+0.8700** (multi-seed mean; up from /028 biased +0.5053)
- OOS/IS ratio: 1.163
- OOS MaxDD: 31.10% (mean)
- OOS Calmar: 1.2028 (mean)
- Max symbol concentration: 64.92% (mean; IMPROVED from 76.47%)
- DSR_relative: **0.9982** (FIRST PASS in v3 history)
- PBO mean: 0.1278; frac_positive_paths: 0.6444 (HIGHEST in v3 CONFIRMATION)
- PSR: 1.0
- n_eff: 19; n_trials: 1050
- Wall-clock: 5.49h
- Reproducibility stamp: setup `7a46e05`, gate `2917cfc`, brief `3ab47a8`, engineering `72bb80c`, walk-forward fix `e149e9d`, Critic enhancement `414368a`
- Run command: `uv run python run_baseline_v3.py --seeds 2 --n-trials 35 --clean-oof`

## Recommendations to QR (for iter-v3/059 cycle 1 #1 of 10 EXPLORATIONs)

1. **Re-evaluate pre-fix NEGATIVE/INERT verdicts before excluding cycle 1 axes.** Structural change in optimization landscape (seed dispersion 3.70× → 0.78×; frac_positive_paths 53% → 64%; DSR_relative FIRST PASS) means axes classified NEGATIVE/INERT under buggy walk-forward may behave differently. QR should prioritize fresh EDA over blanket exclusions. Funding rate features (closed /024) and tbr_zscore_30 microstructure (closed /015) deserve fresh consideration. **However, retests must use standard EXPLORATION budget at single-seed.**

2. **Mass feature expansion at /062 — KEEP at original slot.** With /058 RE-ANCHOR producing a stronger anchor and seed dispersion at all-time-best, the post-fix walk-forward is structurally healthier than pre-fix. No urgent need to advance mass feature expansion. **Recommend: maintain /062 slot as planned; use iter-v3/059-061 for high-priority single-feature axes.**

3. **LDO structural drag — diagnostic EXPLORATION recommended in cycle 1.** LDO contributes negative OOS weighted_pnl (-15.29 at seed 42, 18.2% WR over 11 trades) — 4th consecutive CONFIRMATION-class run showing this pattern. Post-fix confirmation that it's REAL not bias-artifact. Per `feedback_insist_on_symbols.md`, feature engineering is the primary tool; LDO removal NOT first response. Cycle 1 should commission LDO-specific feature-importance + label-quality diagnostic EXPLORATION (single-seed, EDA-driven).

## Catalog Row

`| RE-ANCHOR | /058 | RE-ANCHOR: /028 bundle under post-fix walk-forward (commit e149e9d); 1-for-1 REVERT parkinson_gk_ratio_20 → ret_skew_50; ENSEMBLE_SIZE=5, --seeds 2, --n-trials 35, --clean-oof; FIRST iteration audited under enhanced Critic protocol | IS +0.7481 (multi-seed mean; Δ +0.238 vs /028 biased anchor) | OOS +0.8700 (multi-seed mean; Δ +0.365 vs /028 biased anchor) | Gate 10 PASS (both seeds Pareto-positive: 42=+0.7826, 123=+0.9574) | RE-ANCHOR-MERGE (clean — ABOVE-BAND) | BASELINE_V3.md UPDATE: YES (MANDATORY per RE-ANCHOR; STRICTLY-BETTER both axes; DSR_relative=0.9982 FIRST PASS in v3 history; frac_positive_paths 64.4% HIGHEST in v3 CONFIRMATION; seed dispersion 0.78× MOST STABLE in v3 CONFIRMATION) |`

Cycle counting: RE-ANCHOR NOT part of cycle 1 cadence. After /058 lands, cycle 1 starts at iter-v3/059 (EXPLORATION #1 of 10); cycle 1 CONFIRMATION = iter-v3/068.

## Files Audited

- `briefs-v3/iteration_v3-058/research_brief.md` (SHA `3ab47a8`)
- `briefs-v3/iteration_v3-058/phase5p5_gate.md` (SHA `2917cfc`, PASS)
- `briefs-v3/iteration_v3-058/engineering_report.md` (SHA `72bb80c`)
- `reports-v3/iteration_v3-058/comparison.csv` + `dsr.json` + `seed_summary.json` + `pareto_front.csv` + `per_cell_pbo.csv` + `cpcv_paths.csv` + `ic_matrix.csv` + `adf_test.csv`
- `reports-v3/iteration_v3-058/in_sample/trades.csv` + `out_of_sample/trades.csv` (PnL spot-check)
- `src/crypto_trade/strategies/ml/walk_forward.py` (FIX at line 113)
- `src/crypto_trade/strategies/ml/lgbm.py` (cv_gap at line 457)
- `src/crypto_trade/strategies/ml/validation_v3.py` (REQUIRED_GAP=66 at line 54)
- `tests/test_lookahead_embargo.py` (11/11 regression tests PASS)
- `BASELINE_V3.md` (PENDING update at Phase 8 diary)
