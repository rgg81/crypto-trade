# Iteration 159 Diary

**Date**: 2026-04-08
**Type**: EXPLOITATION (analytical DSR audit)
**Decision**: **NO-MERGE** (analytical iteration, no trading config change)

## Findings

### DSR of v0.152 Baseline

The baseline's statistical significance is N-dependent:

| N trials | E[max] | DSR | Verdict |
|----------|--------|-----|---------|
| 21 | 2.47 | **+1.38** | ✓ Beats random |
| 71 | 2.92 | -0.35 | ✗ Within noise |
| 159 | 3.18 | -1.36 | ✗ Clearly within noise |

Across the full iteration history (N≈159), v0.152's OOS Sharpe +2.83 is
within the range expected from 159 random trials. This does NOT mean the
strategy has no signal — but it means **no single iteration can claim
statistical significance via DSR alone at this iteration count**.

### ΔDSR Confirms iter 158 NO-MERGE

iter 158's +0.023 Sharpe improvement = **0.185σ** in SE units. The
change is invisible at any reasonable confidence threshold. NO-MERGE was
the right call.

### Recommended Magnitude Floor

**Proposed**: Future iterations require **ΔSharpe ≥ +0.10** OR
**OOS Sharpe > baseline × 1.03** as a supplementary MERGE constraint.

Retroactive check:
- iter 147→152: Δ = +0.093. Borderline (just below +0.10, above ×1.03 floor).
- iter 152→158: Δ = +0.023. Clearly below both floors — correctly
  NO-MERGE.

## Interpretation

Post-processing iterations on iter 138's 816 trades have hit a hard
ceiling. The realistic expectation for future iterations:

1. **Retraining-required changes** (new features, new labeling, new
   model type) can deliver ΔSharpe > +0.20 if they work. iter 117's
   meme-model pruning did +0.37.

2. **Post-processing filters** (iter 155-158 category) deliver
   ΔSharpe < +0.10 in practice. These should not merge even if they
   strictly exceed baseline OOS Sharpe.

3. **Incremental parameter tuning** (e.g., iter 158 ADX grid) produces
   ΔSharpe < +0.05 which is indistinguishable from noise under DSR.

## Hard Constraints

N/A — this is an analytical iteration. No new trading config proposed.

## Research Checklist

- **H (Overfitting Audit)**: COMPLETED. DSR computed for v0.152 under
  N ∈ {21, 71, 159}. Confirmed multi-testing concern flagged in iter 158.
- **F (Statistical Rigor)**: COMPLETED. SE(SR) uses observed skew/kurt;
  ΔDSR framework derived for future merges.

## Exploration/Exploitation Tracker

Last 10 iterations: [X, X, X, X, X, E, E, E, X, **X**] (iters 150-159)
Exploration rate: 3/10 = 30% ✓

## Key Recommendations

### For Future Iterations

1. **Adopt magnitude floor**: ΔSharpe ≥ +0.10 for MERGE (supplementary).
2. **Kill micro-iterations**: stop testing post-processing filters on
   iter 138 trades; expected ΔSharpe < +0.05, below DSR detection.
3. **Demand structural change**: next MERGE candidate should require
   retraining with new features/labels/model, not parameter tuning.

### For Deployment

**v0.152 remains the deployment baseline.** DSR is sobering but not
disqualifying: the strategy passes every OTHER rigor check (temporal
stability iter 154, parameter robustness iters 152-155, rule-based
sensitivity iters 157-158). DSR just says "don't overclaim statistical
significance at N=159."

## Next Iteration Ideas

1. **STOP post-processing iteration**. The ceiling is v0.152.

2. **Structural retrains (multi-hour compute per test)**:
   - Event-driven sampling (AFML Ch. 3, prerequisite for sample
     uniqueness)
   - Entropy features (AFML Ch. 18)
   - CUSUM structural breaks (AFML Ch. 17)
   - Primary model retrained with confidence captured (enables proper
     meta-labeling)
   - Per-symbol models for BTC/LINK with symbol-specific features

3. **Implement DSR as official metric**: add `compute_deflated_sharpe()`
   to `backtest_report.py` as a code iteration. Future iterations would
   report DSR alongside raw Sharpe.

4. **Paper trading deployment** (recommended immediate action).
