# Engineering Report — iter-v3/092

## Headers

- Iteration: iter-v3/092
- Type: CONFIRMATION (cycle-3 CONFIRMATION — multi-seed verdict closing the cross-sectional `LGBMRanker` line)
- Branch: iteration-v3/092
- Setup commit SHA: a6217d3ff5fe5545de3807cb60153901cfdd6670
- Wall-clock time: 3h 46m (exit 0)
- Hardware: WSL2 / Linux 6.6.114.1

---

## Configuration Diff vs Baseline

iter-v3/092 is not a per-symbol baseline run. It is a multi-seed CONFIRMATION-grade run of the cross-sectional
`LGBMRanker` architecture (runner: `run_cross_sectional_v3.py`, strategy: `CrossSectionalRankStrategy`).

| Component | /092 value | Change from /091 |
|---|---|---|
| `score_mode` | `"trained"` | unchanged (the model-free path is left intact but unused) |
| `XS_HORIZON` | 21 | unchanged (the corrected /091 horizon-EDA best; the /089 H=3 incumbent is the trained ranker's worst horizon) |
| `XS_HOLD_BARS` | 21 | unchanged |
| Feature stack | 13-feature `XS_FEATURE_COLUMNS` | unchanged (the /090 downside expansion stays reverted) |
| Label | `label_cross_sectional_rank` horizon-matched at H=21 | unchanged |
| Cost-aware construction | quintile legs (0.20), 21-bar overlapping holds, no-trade band 0.020, turnover ceiling 0.138 | unchanged |
| Embargo | `embargo_ms = (XS_HORIZON+1) * interval_ms`; CPCV gap 484 | unchanged (the corrected /091 embargo) |
| **Outer seeds** | **{42, 123} — `CONFIRMATION_OUTER_SEEDS`** | **NEW: multi-seed CONFIRMATION support** |
| **Inner ensemble** | **5 models/outer seed via `_derive_ensemble_seeds`** | **NEW: copied verbatim from `run_baseline_v3.py` lines 119-128** |
| **Total models/cell** | **10 (5 inner × 2 outer)** | **NEW** |
| **Optuna trials** | **35/model (n_trials × ENSEMBLE_SIZE × n_outer_seeds = 350 total)** | unchanged default; applied to 10× more models |
| `ITERATION_LABEL` | `"v3-092"` | updated |

`OOS_CUTOFF_DATE = 2025-03-24` and `training_months = 24` are UNCHANGED (sacred constants verified).

---

## Key Metrics Block

All numbers sourced directly from runner artifacts — file citations per metric.

### Multi-seed aggregate (source: `reports-v3/iteration_v3-092/comparison.csv`, `dsr.json`)

| Metric | In-Sample | Out-of-Sample | OOS/IS Ratio |
|---|---|---|---|
| **Monthly Sharpe (net)** | **+0.0885** | **+0.3194** | **3.61** |
| Monthly Sharpe (gross) | +0.1537 | +0.3473 | 2.26 |
| Max Drawdown | 1.1546 | 0.7311 | 0.633 |
| OOS rank-IC mean | — | +0.0358 | — |
| Turnover/bar (IS) | 0.0243 | — | — |
| Turnover ceiling gate | PASS (0.0243 <= 0.138) | — | — |
| frac_positive_paths (mean) | 0.578 | — | — |
| n_seeds | 2 | — | — |
| n_trials_total | 350 | — | — |

Source: `reports-v3/iteration_v3-092/comparison.csv` rows 2-11.

| DSR/PBO/PSR metric | Value | Source |
|---|---|---|
| DSR | 0.0 | `reports-v3/iteration_v3-092/dsr.json` |
| PBO | NaN (not computable — see note) | `reports-v3/iteration_v3-092/dsr.json` |
| PSR | 0.0 | `reports-v3/iteration_v3-092/dsr.json` |
| n_eff | 0 | `reports-v3/iteration_v3-092/dsr.json` |
| n_trials | 350 | `reports-v3/iteration_v3-092/dsr.json` |

Note on DSR/PBO/PSR: the aggregate book's OOS net monthly Sharpe is +0.3194, which is a real number above zero but far below the per `feedback_v3_dsr_mode_artifact.md` CONFIRMATION-mode E[max_SR] threshold. DSR=0.0 and PSR=0.0 reflect that the observed Sharpe does not clear the trials-deflated threshold — the cross-sectional book at 350 trials/cell produces n_eff=0 effective trials, meaning the signal is too faint relative to the search budget to register as statistically significant. PBO=NaN means the CPCV path structure did not produce a valid PBO estimate (the path-level Sharpe distribution has zero discriminative power at this signal level). These are honest sentinel values per Section 4.3 of the brief.

### Per-seed breakdown (source: `reports-v3/iteration_v3-092/ensemble_summary.json`, `seed_*/comparison.csv`)

| Metric | Seed 42 | Seed 123 | Multi-seed mean | Multi-seed min |
|---|---|---|---|---|
| IS monthly Sharpe (net) | +0.0169 | +0.1602 | +0.0885 | +0.0169 |
| OOS monthly Sharpe (net) | +0.4328 | +0.2060 | +0.3194 | +0.2060 |
| IS monthly Sharpe (gross) | +0.0813 | +0.2260 | +0.1537 | — |
| OOS monthly Sharpe (gross) | +0.4587 | +0.2360 | +0.3473 | — |
| OOS rank-IC mean | +0.0382 | +0.0333 | +0.0358 | — |
| frac_positive_paths | 0.489 | 0.667 | 0.578 | — |
| IS turnover/bar | 0.0243 | 0.0242 | 0.0243 | — |
| OOS net positive | true | true | — | — |
| OOS/IS ratio (net) | 25.63 | 1.29 | 3.61 | — |

Source: `reports-v3/iteration_v3-092/ensemble_summary.json`; per-seed ratios computed from `seed_42/comparison.csv` row 2 and `seed_123/comparison.csv` row 2.

### CPCV paths (source: `seed_42/cpcv_paths.csv`, `seed_123/cpcv_paths.csv`)

Each seed runs 45 CPCV paths (N=22 symbols, the cross-sectional CPCV with XS_REQUIRED_GAP=484).

| | Seed 42 | Seed 123 |
|---|---|---|
| Positive paths | 22/45 | 30/45 |
| frac_positive_paths | 0.489 | 0.667 |
| Path Sharpe range | [-0.0673, +0.0811] | [-0.0593, +0.0660] |
| Path n_trades range | 670-672 | 670-672 |

The CPCV path Sharpe values are an order of magnitude below the +1.0 IS floor in absolute terms — each individual 45-path draw is bounded roughly within [-0.07, +0.08]. This is consistent with a faint-signal architecture.

---

## FINDING 1 — NO-MERGE: G1 and G2 both FAIL by an order of magnitude

**The result is NO-MERGE.** The multi-seed mean IS monthly Sharpe is +0.0885 and the OOS monthly Sharpe is +0.3194. Both are an order of magnitude below the +1.0 absolute merge floors (G1 and G2). This is not a marginal shortfall — it is a decisive, pre-registered outcome. The brief's Section 2.4 pre-registered exactly this: "A best-faith IS net monthly Sharpe of +0.0944 cannot, on any honest reading, produce an OOS multi-seed mean clearing the +1.0 OOS floor."

The observed multi-seed IS (+0.0885) is consistent with and slightly below the pre-registered EDA's best-faith single-seed +0.0944 (M2 35-trial EDA), confirming the EDA was runner-faithful. The multi-seed mean did not lift IS — as expected, multi-seed averaging tightened rather than boosted the IS book.

**Classification: CONFIRMATION-NO-MERGE (pre-registered modal outcome at ≈70% probability, Section 7-8 of the brief).** The cross-sectional `LGBMRanker` momentum-rank line is formally closed as a route to a merge-grade book.

---

## FINDING 2 — OOS/IS ratio 3.61, driven by seed-42 divergence (ratio 25.63)

**The aggregate OOS/IS ratio is 3.61** — above the v3 suspicious heuristic of 3.0 (the healthy band is approximately [0.5, 2.0]). The ratio is asymmetrically driven:

- **Seed 42**: IS +0.0169, OOS +0.4328 — ratio 25.63. A near-flat IS book against a positive OOS book is the textbook single-seed lottery pattern (`feedback_v3_engineered_features_dont_stack.md`, `feedback_v3_single_seed_frozen_baseline.md`; the /091 Critic Item 4 root-cause). The IS book is close to zero (0.0169), so a modest OOS positive produces an extreme ratio. This is the regime-exposure/lottery signature: seed 42's inner-ensemble draw found a configuration that happened to be positive OOS on the current 14-month OOS window.
- **Seed 123**: IS +0.1602, OOS +0.2060 — ratio 1.29. Comparatively healthy; the IS book is meaningful and the OOS/IS ratio sits inside the normal band.

**The OOS positivity — the first positive-OOS-net cross-sectional book in the /088-092 line — sits on a near-flat IS book (multi-seed mean IS +0.0885, with seed 42 contributing IS +0.0169).** The OOS +0.32 multi-seed mean must NOT be presented as a durable edge. The brief's Section 7 ≈10% failure mode explicitly named this: "one or both outer seeds draw a lucky OOS window... the multi-seed mean is dragged up by one seed but G10 (both seeds positive) and/or the +1.0 floors still fail." Both seeds are individually OOS-positive (G10 PASS), but the +1.0 floors still fail decisively. The characterization is factual: this is the CONFIRMATION-NO-MERGE case where one seed drew a favorable OOS window, consistent with a faint-IC architecture at seed=42.

---

## CONFIRMATION Gate Evaluations

Evaluated against the multi-seed-aggregate runner artifacts per brief Section 4.2.

| Gate | Threshold | Observed | Result | Source |
|---|---|---|---|---|
| G1 — IS monthly Sharpe | ≥ +1.0 | +0.0885 | **FAIL** | `comparison.csv` row 2 in_sample |
| G2 — OOS monthly Sharpe | ≥ +1.0 | +0.3194 | **FAIL** | `comparison.csv` row 2 out_of_sample |
| G3 — OOS/IS ratio | ≥ 0.5 (both positive) | 3.61 | PASS (but G1+G2 govern — both fail) | `comparison.csv` row 2 ratio |
| G4 — DSR | > 0.95 | 0.0 | **FAIL** | `dsr.json` "dsr" |
| G5 — PBO | < 0.4 | NaN (uncomputable) | **FAIL** | `dsr.json` "pbo" |
| G6 — PSR | > 0.95 | 0.0 | **FAIL** | `dsr.json` "psr" |
| G7 — OOS trade count | ≥ 130 | seed 42: 27,653; seed 123: 26,825 | PASS | `seed_42/out_of_sample/per_symbol.csv`, `seed_123/out_of_sample/per_symbol.csv` (row sums) |
| G8 — Top-symbol OOS concentration | ≤ 30% | seed 42: 16.24% (AAVE); seed 123: 11.93% (CRV) | PASS | `seed_42/out_of_sample/per_symbol.csv`, `seed_123/out_of_sample/per_symbol.csv` |
| G9 — OOS rank-IC | > 0 | +0.0358 (mean); seed 42: +0.0382; seed 123: +0.0333 | PASS | `dsr.json` "rank_ic_mean_oos" |
| G10 — 2-seed Pareto | both seeds OOS-net-positive | seed 42 OOS +0.4328 (true); seed 123 OOS +0.2060 (true) | PASS | `ensemble_summary.json` "pareto_both_oos_positive" |
| F3 — Turnover ceiling | ≤ 0.138/bar | 0.0243 (seed 42); 0.0242 (seed 123) | PASS | `seed_42/dsr.json`, `seed_123/dsr.json` "turnover_per_bar_is" |

**CONFIRMATION-MERGE conjunct: G1 FAIL AND G2 FAIL AND G4 FAIL AND G5 FAIL AND G6 FAIL => CONFIRMATION-NO-MERGE.**

BASELINE_V3.md is UNCHANGED. The /059 canonical baseline (IS +1.0894 / OOS +0.5791) remains the anchor; tag `v0.v3-059` is NOT superseded.

---

## Per-Symbol Concentration Audit

### Seed 42 — IS per_symbol (source: `seed_42/in_sample/per_symbol.csv`)

| Symbol | Weighted PnL | n_trades | Concentration % |
|---|---|---|---|
| ICPUSDT | -0.1243 | 3,353 | **13.46%** (IS max) |
| TRXUSDT | +0.1098 | 3,333 | 11.89% |
| FILUSDT | +0.0837 | 3,297 | 9.06% |
| BCHUSDT | +0.0806 | 3,282 | 8.73% |
| EOSUSDT | +0.0467 | 3,119 | 5.06% |

### Seed 42 — OOS per_symbol (source: `seed_42/out_of_sample/per_symbol.csv`)

| Symbol | Weighted PnL | n_trades | Concentration % |
|---|---|---|---|
| AAVEUSDT | +0.0283 | 1,258 | **16.24%** (OOS max) |
| LDOUSDT | +0.0213 | 1,258 | 12.24% |
| ADAUSDT | +0.0177 | 1,235 | 10.17% |

### Seed 123 — IS per_symbol (source: `seed_123/in_sample/per_symbol.csv`)

| Symbol | Weighted PnL | n_trades | Concentration % |
|---|---|---|---|
| ICPUSDT | -0.1560 | 3,208 | **15.35%** (IS max) |
| TRXUSDT | +0.1335 | 3,348 | 13.14% |
| FILUSDT | +0.0987 | 3,224 | 9.71% |

### Seed 123 — OOS per_symbol (source: `seed_123/out_of_sample/per_symbol.csv`)

| Symbol | Weighted PnL | n_trades | Concentration % |
|---|---|---|---|
| CRVUSDT | +0.0182 | 1,258 | **11.93%** (OOS max) |
| LDOUSDT | +0.0167 | 1,258 | 10.92% |
| ADAUSDT | +0.0096 | 780 | 6.31% |

No symbol exceeds 30% OOS concentration in either seed. G8 PASS across both seeds.

---

## Label Leakage Audit

- Walk-forward embargo: `embargo_ms = (XS_HORIZON+1) * interval_ms = 22 * 28800000 = 633,600,000 ms` (22 bars at H=21). Verified at `cross_sectional.py` line 998 and `run_cross_sectional_v3.py` line 915 (the /091 Phase-5.5-BLOCK fix; confirmed present at setup commit `a6217d3`).
- CPCV purge gap: `XS_REQUIRED_GAP = (H+1)*N = 22*22 = 484`. Verified in `cross_sectional.py`.
- These values were verified by the /091 Critic at Critic Checks 1 and 2 (Critic FINAL `c6a03ed`) and remain unchanged in /092. No new leakage vector introduced — /092 adds only the outer-seed loop and inner-ensemble averaging; neither touches the embargo or purge logic.

---

## Seed Concentration Audit

| Metric | Seed 42 | Seed 123 | Multi-seed mean |
|---|---|---|---|
| IS monthly Sharpe (net) | +0.0169 | +0.1602 | +0.0885 |
| OOS monthly Sharpe (net) | +0.4328 | +0.2060 | +0.3194 |
| OOS/IS ratio | 25.63 | 1.29 | 3.61 |
| frac_positive_paths | 0.489 | 0.667 | 0.578 |
| Both OOS positive | true | true | — |

The two outer seeds produce meaningfully different IS books (seed 42 IS ≈ 0; seed 123 IS +0.16). Both are OOS-positive. The 3.61 aggregate ratio is entirely explained by seed 42's near-zero IS vs positive OOS (ratio 25.63). Seed 123 at ratio 1.29 is healthy. This asymmetry is the key diagnostic: the multi-seed mean OOS positivity is real but cannot be attributed to a robust repeatable edge — it reflects one seed (42) drawing a favorable OOS configuration at near-floor IS fitness.

---

## Gate Efficacy Table

The cross-sectional architecture is risk-managed by construction (dollar-neutral long-short + quintile diversification + inverse-vol weighting + 21-bar overlapping holds + no-trade band + turnover ceiling). No per-symbol v3 risk gates (ADX, Hurst, OOD z-score, drawdown brake, BTC contagion, isolation forest) apply to the cross-sectional path — this scope was established at /088 and confirmed by the /089/091 briefs.

| Construction control | IS fire rate | OOS fire rate | Note |
|---|---|---|---|
| Turnover ceiling (0.138/bar) | No fires (IS 0.0243/bar) | — | F3 PASS both seeds |
| No-trade band (τ=0.020) | Active (reduces churn) | Active | Structural; no per-bar fire rate |
| 21-bar overlapping hold | Active (tranching) | Active | Structural |
| Quintile long-short | Active (4-5 names/leg) | Active | Structural |

---

## Anomaly Notes

1. **Seed 42 IS ≈ 0 pattern**: IS monthly Sharpe +0.0169 is effectively zero. This is not a bug — the 5-model inner ensemble at seed 42 finds a configuration that is near-flat IS but happens to be OOS-positive. This is consistent with the /091 Critic Item 4 root-cause of the reference book's OOS +0.4613 (frac_positive_paths 0.356 — IS-weak single-seed fit drawing a lucky OOS window). At multi-seed, seed 42 reproduces this pattern at reduced magnitude.

2. **ICPUSDT IS drag**: ICPUSDT is the worst IS symbol by weighted PnL in both seeds (seed 42: -0.1243, IS concentration 13.46%; seed 123: -0.1560, IS concentration 15.35%). ICPUSDT is structurally a momentum-rank drag in IS across the cross-sectional line (/088-092). This is an IS-persistent pattern, not a random draw. It does not materially affect the verdict (the verdict is driven by the +1.0 floor miss, not by per-symbol decomposition), but is noted for the cycle-4 QR's signal-class analysis.

3. **OOS rank-IC stability**: OOS rank-IC is +0.0382 (seed 42) and +0.0333 (seed 123), mean +0.0358. This is consistent with the /088-091 line's +0.03 to +0.04 range. The signal transfer (rank-IC) is real and stable across seeds and iterations — the architecture has genuine predictive content. The limitation is that the signal is too faint to overcome trading costs at the OOS book level: G9 PASS while G2 FAIL.

4. **Trade-row spot check (seed 42 OOS)**: Random inspection of 10 rows from `seed_42/out_of_sample/trades.csv` — entry/exit timestamps consistent with H=21-bar overlapping hold cadence; weights positive (long) or negative (short) per quintile leg; no NaN PnL, no NaN weights. Spot check: no anomalies.

5. **n_trials_total = 350**: `35 trials × 5 inner models × 2 outer seeds = 350`. Confirmed in `comparison.csv` row 10. This is the correct CONFIRMATION budget per the brief Section 3.2.

---

## Status

OVERALL=READY-FOR-CRITIC

Pre-registered outcome confirmed: **CONFIRMATION-NO-MERGE**. G1 (IS +0.0885 vs floor +1.0) and G2 (OOS +0.3194 vs floor +1.0) both FAIL by an order of magnitude. G4/G5/G6 (DSR/PBO/PSR) all FAIL. G3, G7, G8, G9, G10 all PASS. The cross-sectional `LGBMRanker` momentum-rank line, in its best-faith form (H=21, 10 models/cell, corrected embargo), does not reach a merge-grade book. BASELINE_V3.md UNCHANGED; /059 canonical baseline retained. The `cross_sectional.py` code infrastructure is RETAINED (not deleted).
