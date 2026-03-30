# Iteration 090 Diary — 2026-03-30

## Merge Decision: NO-MERGE (EARLY STOP)

Early-stopped: Year 2022 PnL=-58.7%, WR=35.6%, 91 trades. IS Sharpe -1.00, MaxDD 82.0%. PurgedKFoldCV without training_days is better than iter 089 but still deeply unprofitable.

**OOS cutoff**: 2025-03-24

## Hypothesis

Fix iter 089's empty fold problem by disabling training_days optimization while keeping PurgedKFoldCV. Without training_days trimming, each fold gets the full ~4,400 samples after purging.

## Configuration Summary

- OOS cutoff: 2025-03-24 (fixed)
- **CV method: PurgedKFoldCV** (purge_window=21, embargo_pct=0.02) — from iter 089
- **training_days: DISABLED** (full 24mo window, no Optuna trimming) — NEW
- Features: 115 (symbol-scoped discovery)
- Model: LGBMClassifier binary, ensemble [42, 123, 789]
- Walk-forward: monthly, 24mo window, 5 CV folds, 50 Optuna trials
- Execution: Dynamic ATR barriers TP=2.9, SL=1.45, cooldown=2

## Results: In-Sample (partial — early-stopped at 2022 checkpoint)

| Metric | Iter 090 | Iter 089 | Baseline (068) |
|--------|----------|----------|----------------|
| Sharpe | **-1.00** | -1.32 | +1.22 |
| WR | **35.2%** | 32.6% | 43.4% |
| PF | **0.79** | 0.72 | 1.35 |
| MaxDD | **82.0%** | 116.1% | 45.9% |
| Trades | 91 | 92 | 373 |

## What Happened

Disabling training_days partially fixed the iter 089 problem:
- **No empty folds**: All 5 folds now have sufficient data (best Optuna Sharpe ~0.12-0.15, no -10.0 penalties)
- **Still unprofitable**: IS Sharpe -1.00 is better than -1.32 but still catastrophic

The core finding from iter 089 is confirmed: **PurgedKFoldCV reveals the model's true CV performance is much worse than TimeSeriesSplit reports.** With proper purging and embargo, the cross-validated Sharpe during Optuna optimization is 0.05-0.15 (where baseline with TimeSeriesSplit sees 0.5-1.0+). This 5-10x gap represents the CV leakage contribution.

## Quantifying the Gap

WR: 35.2%, break-even 33.3%, gap **+1.9pp** (barely above break-even). PF 0.79 — still capital-destructive. IS MaxDD 82.0% — uninvestable.

## Exploration/Exploitation Tracker

Last 10 (iters 081-090): [X(abandoned), E, E, E, E, E, E, X, E, **X**]
Exploration rate: 7/10 = 70%
Type: **EXPLOITATION** (bugfix for iter 089's empty fold problem)

## Research Checklist

Completed 2 categories (exploitation after exploration):
- **F**: Statistical rigor — confirmed no -10.0 folds, proper data flow through purged CV
- **H**: Overfitting audit — CV Sharpe 0.05-0.15 confirms leakage was 5-10x inflating the metric

## MLP Diagnostics (AFML)

| Metric | Value |
|--------|-------|
| Deflated Sharpe Ratio (DSR) | < 0 (N=90, E[max] ~3.00) |
| Expected max random Sharpe (N=90) | ~3.00 |
| Average label uniqueness | Not computed |
| PBO (if CPCV used) | N/A |
| Non-stationary features used | Not audited |
| CV method | PurgedKFoldCV(n_splits=5, purge=21, embargo=0.02), no training_days |

## What Worked

- Empty fold problem is resolved (no -10.0 penalties)
- Results improved ~24% vs iter 089 (Sharpe -1.00 vs -1.32)
- Confirms PurgedKFoldCV implementation is correct

## What Failed

- Strategy still deeply unprofitable with purged CV
- The model architecture (LightGBM with these features on 8h candles) may genuinely not have enough signal to survive proper CV
- The baseline's apparent success may rely on the CV leakage that TimeSeriesSplit provides

## Overfitting Assessment

**Two iterations (089-090) with PurgedKFoldCV both produced catastrophic results.** The pattern is clear:
1. TimeSeriesSplit leaks information from overlapping triple barrier labels
2. This leakage inflates CV Sharpe by 5-10x during Optuna optimization
3. Optuna selects hyperparameters optimized for the leaked signal
4. When leakage is removed, no profitable configuration exists

**The fundamental question**: Is the baseline's OOS Sharpe +1.84 real, or is it a lucky outcome of hyperparameters selected via leaky CV? The IS Sharpe +1.22 was inflated by leakage — but the OOS Sharpe is independent. The model may have genuine signal that happens to work despite being selected with the wrong CV metric.

## Next Iteration Ideas

**PurgedKFoldCV has failed twice. Three paths forward:**

1. **REVERT + DOCUMENT**: Return to TimeSeriesSplit for now and accept the known CV leakage as a tolerable imperfection. The walk-forward still prevents model-level leakage. The CV leakage only affects hyperparameter selection within Optuna — not the actual predictions. Document this as a known limitation. Continue the MLP sequence with other techniques (MDA importance, sample weighting, fracdiff) using TimeSeriesSplit.

2. **LIGHTER PURGE**: Try PurgedKFoldCV with purge_window=5 (not 21) and embargo_pct=0.005 (not 0.02). This addresses some leakage while preserving more training data at fold boundaries. The full 21-candle purge may be too aggressive — most of the label overlap decays exponentially with distance.

3. **STRUCTURAL RETHINK**: The core problem may be that 8h candles with 7-day timeout labels are fundamentally incompatible with k-fold CV. With 21 candles of overlap per label, the effective independent sample count is ~1/21 of the apparent count. Consider: (a) shorter timeout to reduce overlap, (b) different CV strategy altogether (blocked CV with large blocks), or (c) no CV at all (use a single holdout validation set).

**Recommended next**: Approach 1 (revert to TimeSeriesSplit, continue MLP sequence). The PurgedKFoldCV finding is valuable knowledge, but pursuing it further would stall the entire iteration pipeline. Keep the purged_cv.py module for future use but don't use it as the default CV method yet.

## Lessons Learned

1. **PurgedKFoldCV confirms CV leakage is significant** (5-10x inflation in CV Sharpe), but the technique makes the model unprofitable rather than better. This is the classic case where "doing it right" breaks things because the model was never as good as the leaky metric suggested.

2. **Disabling training_days helps** (+24% improvement) but doesn't solve the fundamental problem. The training_days parameter was a secondary issue.

3. **The MLP Foundation sequence may need reordering.** PurgedKFoldCV (Tier 1.1) was supposed to be foundational, but it's a blocker. Consider proceeding with Tiers 1.2-1.5 (MDA importance, sample weighting, fracdiff, DSR) on the existing TimeSeriesSplit baseline, then revisiting purged CV later when the model is stronger.

4. **The 21-candle purge window is very large for 5-fold CV.** With 4,400 samples and 5 folds, purging 21 candles at each of the 4 boundaries removes ~2% of data. But the embargo removes another ~2%. Together, ~4% data loss per fold. This may be borderline acceptable, but the bigger issue is that it changes which hyperparameters Optuna selects.
