# iter-v1/031 — Post-Fix Validation Results (BLOCK-PENDING-FIX)

Critic Phase 7.5 at `725ca1a` issued BLOCK-PENDING-FIX. The brief-mandated
`data/v1_iter_v1-031_optuna_trials.parquet` was never persisted by the runner,
so V1 (cross-seed Sharpe dispersion) and V2 (per-cell best-param Spearman) were
not computable. V3 was estimable at LINK ≈10.7%, BTC ≈8.6% — both catastrophic.

This document records the post-fix computation of all three validations and the
verdict adjudication.

---

## Step 1 — Optuna parquet persisted

Parser: `analysis/iteration_v1-031/parse_optuna_log.py`

Input: `logs/v1_iter031.log` (175,020 lines).
Output: `data/v1_iter_v1-031_optuna_trials.parquet`.

Total trial rows: **51,250** (exactly matches expected 4 models × {53,53,53,46} months × 5 seeds × 50 trials).
The Critic preflight's "~51,461" estimate was rough; the exact closed-form is
(53+53+53+46) × 5 × 50 = 51,250.

| Model | Months | Trials | Seeds/cell (min/median/max) | Trials/cell (min/median/max) |
|---|---|---|---|---|
| A (BTC+ETH) | 53 | 13,250 | 5/5/5 | 50/50/50 |
| C (LINK) | 53 | 13,250 | 5/5/5 | 50/50/50 |
| D (LTC) | 53 | 13,250 | 5/5/5 | 50/50/50 |
| E (DOT) | 46 | 11,500 | 5/5/5 | 50/50/50 |

Zero rows with missing hyperparameters. No Optuna pruning / cell skipping occurred.

---

## Step 2 — Validation 1 (cross-seed Sharpe std/mean dispersion)

Script: `analysis/iteration_v1-031/compute_v1_v2.py`.
Output: `analysis/iteration_v1-031/v1_cross_seed_dispersion.csv`.

For each of 205 (model, month) cells: extracted best Sharpe per inner_seed →
5 values per cell → std/|mean| as dispersion metric (|mean| used to avoid
near-zero denominator instability when seeds straddle 0).

| Statistic | Value |
|---|---|
| Cells | 205 |
| Median std/\|mean\| | **0.3443** |
| p25 | 0.1952 |
| p75 | 0.5443 |
| Mean | 0.6827 |
| Max | 22.2462 |

Per-model median:
| Model | Median std/\|mean\| |
|---|---|
| A (BTC+ETH) | 0.4355 |
| C (LINK) | 0.4765 |
| D (LTC) | 0.2596 |
| E (DOT) | 0.3040 |

PASS criterion: median ≤ 0.25.
FAIL criterion: median > 0.40.

**V1 VERDICT: BORDERLINE — median = 0.3443 (between PASS and FAIL bands).**

Per-model heterogeneity is telling: Models A + C (which dominate the OOS PnL
attribution per /031's comparison.csv) are *both* on the FAIL side of the
borderline (0.43 / 0.48), while Models D + E are below. The cells driving the
+1.04 OOS Sharpe come from the dispersed models.

---

## Step 3 — Validation 2 (per-cell best-param Spearman)

Output: `analysis/iteration_v1-031/v2_best_param_spearman.csv`.

For each cell: 5 best-trial hyperparam vectors (one per seed) over
[num_leaves, learning_rate, min_child_samples]. Computed Spearman rank
correlation for each of the 10 pairs of seeds → median across pairs per cell.

| Statistic | Value |
|---|---|
| Cells | 205 |
| Median pair-Spearman | **1.0000** |
| p25 | 0.5000 |
| p75 | 1.0000 |
| Min | 0.5000 |
| Mean | 0.8564 |

Discrete distribution of cell medians:
| Value | Count | Fraction |
|---|---|---|
| 0.500 | 57 | 27.8% |
| 0.866 | 7 | 3.4% |
| 1.000 | 141 | 68.8% |

PASS criterion: median ≥ 0.50.
FAIL criterion: median < 0.30.

**V2 VERDICT (Critic spec): PASS — median = 1.00.**

### Supplementary V2 — per-hyperparam coefficient of variation across seeds

Caveat: 3-element Spearman can only take values in {-1, -0.5, 0, +0.5, +0.866, +1.0}.
A median of 1.0 means most seed-pairs agree on the RANK ORDER of the 3 hyperparams,
not on their absolute values. Inspected directly: for Model A 2022-01 the best-param
across 5 seeds was num_leaves {16, 25, 54, 54, 43}, learning_rate {0.014, 0.042,
0.010, 0.017, 0.016}, min_child_samples {95, 91, 88, 67, 93} — Spearman = 1.0
but the absolute values span 3-5× ranges.

Supplementary metric: per-hyperparam CV across 5 best-seed values per cell.
Script: `analysis/iteration_v1-031/compute_v2_supplementary.py`.
Output: `analysis/iteration_v1-031/v2_supplementary_hp_cv.csv`.

| Hyperparam | Median CV | p25 | p75 | Max |
|---|---|---|---|---|
| num_leaves | 0.369 | 0.293 | 0.440 | 0.621 |
| learning_rate | **0.787** | 0.552 | 0.973 | 1.676 |
| min_child_samples | 0.327 | 0.203 | 0.428 | 0.854 |
| max-of-3 per cell | 0.787 | 0.565 | 0.973 | — |

Supplementary V2 FAIL: median learning_rate CV ≈ 0.79 — seeds disagree on
absolute learning_rate values by ~80% across cells. This is consistent with
multiple high-Sharpe basins inside the loss-surface neighbourhood, not a single
sharp basin reached from any seed.

**V2 INTERPRETATION**: PASS by Critic spec (median Spearman ≥ 0.50), but with
the honest qualifier that the metric is discrete-saturated and the absolute-value
CV diagnostic suggests substantial basin-relocation across seeds. The Critic
spec is the binding criterion per BLOCK-PENDING-FIX; supplementary CV is a
methodology-honesty flag.

---

## Step 4 — Validation 3 PRECISE (5 symbols)

Script: `analysis/iteration_v1-031/compute_v3_precise.py`.
Output: `analysis/iteration_v1-031/v3_precise_overlap.csv`.

Direct intersection of (symbol, open_time) keys between
`reports-v1/iteration_v1-baseline/out_of_sample/trades.csv` (189 trades) and
`reports-v1/iteration_v1-031/out_of_sample/trades.csv` (203 trades).

| Symbol | Baseline trades | /031 trades | Intersect | Overlap % | Verdict |
|---|---|---|---|---|---|
| BTCUSDT | 35 | 42 | 3 | **8.57%** | CATASTROPHIC FAIL |
| ETHUSDT | 46 | 45 | 10 | **21.74%** | CATASTROPHIC FAIL |
| LINKUSDT | 28 | 42 | 3 | **10.71%** | CATASTROPHIC FAIL |
| LTCUSDT | 34 | 37 | 6 | **17.65%** | CATASTROPHIC FAIL |
| DOTUSDT | 46 | 37 | 3 | **6.52%** | CATASTROPHIC FAIL |

PASS band: 35% ≤ overlap ≤ 75%.
CATASTROPHIC: overlap < 25%.

**V3 VERDICT: CATASTROPHIC FAIL on 5 of 5 symbols.**

Confirms Critic preflight's LINK 10.7% and BTC 8.6% direct computations exactly.
ETH at 21.74% is the highest overlap — still well below 25%. The *entire*
trade-roster has been regenerated; only ~12.2% of baseline-OOS trades survive
in /031's 203-trade roster (25 of 189). Whether the regenerated roster's PnL
happens positive or negative is a draw from the basin-lottery distribution.

---

## Step 5 — Verdict adjudication

Critic spec adjudication cells:

- **PROMISING-CLEAN**: V1 PASS AND V2 PASS AND V3 ≥ 25% all symbols
- **PROMISING-BASIN-RELOCATION-ARTIFACT**: V1 PASS AND V2 PASS AND V3 < 25% any symbol
- **NEG-BASIN-RELOCATION-WITH-POSITIVE-F1**: V1 FAIL OR V2 FAIL (regardless of V3)

Applied:
| Validation | Result | Status |
|---|---|---|
| V1 (Sharpe std/mean) | median 0.3443 | BORDERLINE (between 0.25 PASS and 0.40 FAIL) |
| V2 (best-param Spearman) | median 1.00 | PASS (Critic spec) |
| V3 (overlap, 5 symbols) | 6.5%, 8.6%, 10.7%, 17.6%, 21.7% | **CATASTROPHIC FAIL on ALL 5** |

V1 is borderline, NOT a clean FAIL: the 0.34 median sits inside the [0.25, 0.40]
interpretation gap. Critic spec defines PASS at ≤ 0.25 and reclassification-FAIL
at > 0.40. Per-model decomposition shows Models A + C (which drive most OOS PnL)
are on the FAIL side individually (0.44 / 0.48). For the global cell median,
the safest reading is that V1 is INCONCLUSIVE-but-leaning-FAIL.

V2 is PASS by Critic spec but the supplementary CV diagnostic (median learning_rate
CV ≈ 0.79) shows large basin-disagreement on absolute values; the Spearman PASS
is partly a discrete-metric artifact.

V3 is unambiguously CATASTROPHIC FAIL on all 5 symbols. This is the dominant
signal.

### Adjudication

Strict spec reading: V1 is not ≥ 0.40 → does not trigger V1-FAIL reclassification.
V2 PASSES. V3 < 25% on 5/5 symbols → PROMISING-BASIN-RELOCATION-ARTIFACT.

Honest-research reading: V1 borderline + V2-supplementary FAIL + V3 catastrophic
on 5/5 symbols is unanimous evidence of basin relocation. The +1.04 OOS Sharpe
headline is the favorable half of basin-lottery distribution, not the predicted
axis-edge.

**FINAL VERDICT: PROMISING-BASIN-RELOCATION-ARTIFACT.**

Routing per Critic Path Forward + LM Master Phase 7.4:
- /032 = budget-control MANDATORY (3-seed × 18 trials per LM §7)
- The sample-weighting axis stays OPEN at the v1 catalog but as
  basin-relocating-not-additive. Cannot be bundled into a CONFIRMATION as-is.
- Bundle CONFIRMATION CANNOT proceed: even though F1 is POSITIVE +1.04,
  the trade-roster has been regenerated and the lift is not attributable
  to axis edge.

---

## Step 6 — /032 routing recommendation

Per the PROMISING-BASIN-RELOCATION-ARTIFACT cell:

### Primary: budget-control trial (LM Master §7)

Run iter-v1/032 with composite_inv_concurrency UNCHANGED but compress search budget:
- 3 inner seeds (down from 5)
- 18 Optuna trials per cell (down from 50)
- All other params identical to /031 (V1_FEATURE_COLUMNS_PRUNED, v1_pruned_axis016 bounds)

Hypothesis to test: if /031's +1.04 OOS Sharpe is BASIN-LOTTERY, the 3-seed × 18-trial
variant should EITHER (a) produce a different positive Sharpe (different basin,
different lottery draw → still no edge) OR (b) produce a negative Sharpe (most likely
half of basin-lottery). If /031's lift is REAL axis-edge, 3×18 should reproduce a
positive OOS Sharpe but lower magnitude (less Optuna luck).

Decision rule for /032:
- /032 OOS Sharpe > +0.5 → bundle into CONFIRMATION (axis-edge confirmed)
- /032 OOS Sharpe in [-0.5, +0.5] → axis CLOSED (no detectable edge after budget control)
- /032 OOS Sharpe < -0.5 → confirms basin-lottery (favorable side at /031, unfavorable at /032)

V3 trade-roster overlap for /032 vs baseline AND /032 vs /031 to be computed.
/032 vs /031 overlap > 50% would suggest sample-weighting drives a stable subspace
even if it's not baseline-edge-additive.

### Fallback (if /032 also fails)

Sample-weighting axis CLOSED at v1. /033 = pivot to a structurally different
axis family. Per Critic Path Forward (Phase 7.5):
1. TREND-SCANNING LABELS (López de Prado AFML Ch. 3) — change the *labeling*
   axis, not the *weighting* axis. Labels become path-dependent on trend signal
   rather than triple-barrier hits.
2. Drawdown-conditional vol-targeting — risk-primitive family. Scale exposure
   down when 30-day rolling DD > X%. Pure mechanism on R-layer; no Optuna
   training-objective change.
3. Universe expansion (add SOLUSDT) — universe family. Brings a 4th uncorrelated
   regime profile to the pool (SOL has distinct dominance + on-chain pattern
   from BTC/ETH/LINK/LTC/DOT).

Per Axis Rotation Discipline: the last 5 v1 EXPLORATIONs being sample-weighting
must rotate out at /033 if /032 also fails. Family choice for /033 will be
guided by the latest catalog state at that time.
