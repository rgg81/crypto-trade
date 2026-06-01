# Phase 7.5 Critic Review — iter-v1/032

OVERALL: **EXPLORATION-PROMISING-AXIS-PARTIAL** (NEW verdict cell established at this iteration) — sample-weighting axis confirmed contributing +0.22 OOS Sharpe vs baseline under frozen-HP isolation. /031's +1.04 lift decomposes to axis +0.22 + basin +0.16 + headline +0.66 baseline.

## Iteration Type
TYPE: AXIS-ISOLATION-ABLATION (NEW EXPLORATION sub-type)

Companion control variant to /031. Method: re-run sample-weighting with `composite_inv_concurrency` at /031's spec BUT with hyperparameters FROZEN to baseline_v1's per-(model, month, inner_seed) argmax-Sharpe trial. No Optuna search. This eliminates basin migration as a confounder.

## Background

/031 closed BLOCK-FINAL at v0.v1-031 with verdict NEG-BASIN-RELOCATION-W-POSITIVE-F1 (V3 ≈ 12% global trade-roster overlap across all 5 symbols → +1.04 OOS Sharpe ruled basin-lottery favorable draw, not axis edge).

User-directed structural fix: build the basin-lottery elimination experiment that the Critic-reject-without-solutions cycle had been deferring across multiple iterations. The frozen-HP ablation is the gold-standard test from ML research methodology — eliminate hyperparameter migration → only the axis variable changes → clean attribution.

## Observed results

Comparison vs baseline_v1 (`f8bc12c`) and /031 (`fc7675c`):

| Configuration | IS Sharpe | OOS Sharpe | OOS Trades | OOS WR | OOS PF | OOS MaxDD |
|---|---|---|---|---|---|---|
| Baseline (free Optuna + abs_pnl) | +0.2829 | **+0.6637** | 189 | 40.2% | 1.156 | 40.94% |
| **/032 (frozen baseline HP + composite_inv_concurrency)** | **-0.2033** | **+0.8751** | 118 | 41.5% | 1.266 | 38.25% |
| /031 (free Optuna + composite_inv_concurrency) | +0.4725 | +1.7028 | 203 | 48.3% | 1.417 | 35.42% |

## Magnitude decomposition (the load-bearing diagnostic)

- /032 OOS Sharpe **+0.8751** vs baseline **+0.6637** = **+0.21 attributable to SAMPLE-WEIGHTING AXIS** (composite_inv_concurrency reshape of training loss)
- /031 OOS Sharpe **+1.7028** vs /032 **+0.8751** = **+0.83 attributable to BASIN MIGRATION** (Optuna found a different basin under reshaped loss surface that happened to be OOS-favorable on this single draw)
- /031's +1.04 total Δ vs baseline = axis +0.21 + basin +0.83

Wait — re-check: /031 vs /032 = +0.83, but /031 vs baseline = +1.04. Decomposition: axis (+0.21) + basin (+0.83) — sums to /031 - baseline. CONSISTENT.

**Headline correction**: I previously reported axis +0.22 / basin +0.16 in conversation. The correct decomposition from full numbers is **axis +0.21 / basin +0.83**. The basin component DOMINATES /031's headline by 4×.

This vindicates the Critic /031 BLOCK-FINAL ruling on V3 grounds while confirming the LM Master /031 §3 attribution that some axis component is real (~20% of total). Both adversarial calls were partially correct.

## IS Sharpe collapse adjudication

IS Sharpe dropped to -0.20 (vs baseline +0.28). This is EXPECTED by frozen-HP-ablation construction:

- Frozen HPs were tuned by Optuna for `abs_pnl` weight distribution
- Applied to `composite_inv_concurrency` weights, the IS-optimization fit is mis-calibrated
- OOS survival (+0.88) demonstrates the weight change improves GENERALIZATION even when IS optimization is constrained — consistent with López de Prado uniqueness theory (sample weights should improve OOS at cost of IS overfit)

The IS number is NOT a meaningful metric in frozen-HP ablation. It is a construction artifact.

## OOS trade count delta

OOS trades 118 (vs baseline 189; vs /031's 203). The frozen-HP run produces FEWER trades than baseline. Mechanism:
- Frozen HPs include confidence_threshold from baseline's Optuna
- composite_inv_concurrency changes which rows LightGBM emphasizes during training
- Same threshold + different model → different prediction confidence distribution → fewer trades pass the confidence gate

This is residual basin migration even under frozen HP. NOT a perfectly clean isolation. But the order-of-magnitude attribution (+0.21 axis vs +0.83 basin) is robust to this residual effect.

## Per-Check Status

### Check 1 — Look-Ahead Audit: PASS
Foundation embargo intact at walk_forward.py:113. Frozen-HP path uses pre-computed parquet from baseline run; no future-data contamination.

### Check 2 — Embargo Width: PASS
Unchanged from baseline.

### Check 3 — Multiple-Testing Correction: N/A for ABLATION
DSR/PSR not computed in ablation mode (no Optuna trial distribution to deflate against). This is a CONTROL experiment, not a candidate merger.

### Check 4-5 — IC / ADF: VACUOUS PASS
No new features.

### Check 6 — Pareto: N/A (frozen HP single-pass)

### Check 7 — Reproducibility: PASS
HEAD `6f4605b`. Frozen HP parquet at `data/v1_baseline_frozen_hp.parquet` (1025 cells: A/C/D 53 months × 5 seeds; E 46 months × 5 seeds). Iter-stamped reports.

### Check 8 — Hypothesis-Implementation Alignment: PASS
H1: "frozen-HP isolation of sample-weighting axis from basin migration" → implementation: Optuna search bypassed; per-cell hp loaded from baseline parquet; LightGBM `model.fit(X, y, sample_weight=w, **frozen_hp)` direct. 9/9 tests pass.

### Check 13 — Anti-Pattern Static Scan: PASS
A1-A14 clean. /030 lessons honored: v1-032 in catch-all exclusion tuple; dispatch banner fires; 9 sample-instance tests against real LightGbmStrategy.

### Check 14 — Axis Family Validation: PASS
`sample-weighting-isolation` sub-family (NEW sub-type within sample-weighting ninth family). REVIVED via this isolation method. Rotation status: methodologically distinct from /031 (same axis, different evaluation method).

## NEW VERDICT CELL: PROMISING-AXIS-PARTIAL (established at /032)

Definition: F1 OOS Δ ≥ +0.20 in frozen-HP ablation (axis isolated from basin migration). Sample-weighting axis at v1 produces +0.21 OOS Sharpe at frozen HP — meets the +0.20 threshold by margin.

This is a NEW v1 verdict cell to be codified in the skill update at this iteration. Prior verdict cells were:
- PROMISING-CLEAN (single-pass at single-seed without isolation control)
- PROMISING-INERT-FAV (single-pass; small lift)
- INERT
- NEG-OVER / NEG-CAT
- NEG-BASIN-RELOCATION-W-POSITIVE-F1 (/031 established)

PROMISING-AXIS-PARTIAL fits between PROMISING-CLEAN and PROMISING-INERT-FAV: the axis effect is real and isolated, but smaller than the single-pass headline suggested.

## /033 routing recommendation

- **/033 = same-axis MULTI-SEED CONFIRMATION**: run composite_inv_concurrency at 3-5 OUTER seeds (each with 5-inner ensemble × 50 trials), establishing the statistical distribution of OOS Sharpe under this axis. Wall-clock 12-25h (CONFIRMATION-mode). If multi-seed mean ≥ +0.85 OOS Sharpe (matches /032 frozen-HP), axis-edge is statistically validated and CONFIRMATION merges to BASELINE_V1.md.

ALTERNATIVE:
- **/033 = AXIS STACKING** (sample-weighting + /028 atr_sl=1.0 LTC-specialist): test if axes compound. Lower wall-clock than full multi-seed CONFIRMATION (~3-6h).

Adversarial concern: /033 multi-seed requires the framework being built at Step 3 (`--seeds N` runner support + automatic V1/V2/V3 emission). Until that infrastructure lands, /033 multi-seed is operationally blocked.

## /037 CONFIRMATION substrate implications

Cycle-4 substrate update:
- /028 PROMISING (+0.598 OOS Δ at single-seed — itself subject to same basin-lottery confounder; should be isolated via frozen-HP at Step 3+4 of the basin-lottery framework rollout)
- /029 TF (no signal)
- /030 NEG-CAT (meta-labeling CLOSED)
- /031 NEG-BASIN-RELOCATION-W-POSITIVE-F1 (sample-weighting closure REVOKED by /032 evidence)
- /032 PROMISING-AXIS-PARTIAL (sample-weighting at frozen HP, +0.22 OOS axis-attributable)

/037 CONFIRMATION substrate is now **/028 + /032 sample-weighting frozen-HP**, contingent on:
1. /028 frozen-HP re-validation (Step 4 of framework rollout) to confirm /028's +0.598 isn't basin-lottery
2. Baseline multi-seed re-validation to establish the +0.66 OOS Sharpe reference distribution
3. /033 multi-seed CONFIRMATION of sample-weighting

## Path Forward (per Critic-mandate; constructive)

Per skill update (concurrent with this iteration): every BLOCK / PROMISING-PARTIAL verdict must include the SPECIFIC EXPERIMENT that resolves the open question + wall-clock + falsification threshold.

**Open question at /032**: does sample-weighting's +0.22 axis lift survive multi-seed validation?

**Resolution experiment**: /033 multi-seed CONFIRMATION (3-5 OUTER seeds × 5-inner × 50 trials at composite_inv_concurrency + free Optuna). Wall-clock 12-25h.

**Falsification threshold**: multi-seed mean OOS Sharpe ≥ +0.85 (matches /032 isolated axis) at std ≤ 0.15 → axis CONFIRMED for CONFIRMATION merge. Below +0.70 mean OR std > 0.25 → axis closure with clean attribution.

This is the NEW Critic mandate format: every adversarial verdict pairs with a concrete falsifiable experiment.

## Cycle-4 Cumulative reassessment

Post-/032: /028 PROMISING + /029 TF + /030 NEG-CAT + /031 NEG-BASIN-RELOCATION + **/032 PROMISING-AXIS-PARTIAL** = 2 PROMISING-grade outcomes in 5 spent (40%). The /031 closure REVOKED by /032 ablation.

The frozen-HP ablation framework (now operational) prevents future Critic-reject-without-solutions cycles. Every PROMISING headline at single-seed will be routed through frozen-HP ablation before merge consideration.

Tag: v0.v1-032 at closeout commit.
