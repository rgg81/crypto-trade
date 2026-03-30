# Research Brief: 8H LightGBM Iteration 089

**Type**: EXPLORATION (MLP Foundation — Purged k-Fold CV with Embargo)
**Date**: 2026-03-30

## 0. Data Split & Backtest Approach

- OOS cutoff date: 2025-03-24 (project-level constant, applies to all iterations)
- The researcher used ONLY IS data (before 2025-03-24) for all design decisions below
- The walk-forward backtest runs on the FULL dataset (IS + OOS) as one continuous process
- Monthly retraining with PurgedKFoldCV, 24-month training window
- The report layer splits backtest results at OOS_CUTOFF_DATE into two report batches

## Core Hypothesis

**Replace TimeSeriesSplit with Purged k-Fold CV + embargo to eliminate information leakage from overlapping triple-barrier labels.**

The current CV implementation (sklearn TimeSeriesSplit, 5 folds) has a fundamental flaw identified by Marcos Lopez de Prado (AFML Ch. 7): triple barrier labels with timeout=7 days (10,080 minutes) span 21 candles on 8h data. When fold boundaries fall within a label's forward-looking window, training samples near the boundary contain labels whose outcomes depend on validation-period price data. This is information leakage at the CV level.

This is NOT model-level leakage (the walk-forward handles that). This is leakage within the Optuna optimization loop — the CV folds used to select hyperparameters are contaminated. The result: Optuna selects hyperparameters that overfit to the leaked information, producing models that appear better in-sample than they actually are.

## Expected Impact

- **IS metrics should decrease slightly**: Less leakage = lower apparent CV performance during optimization = different (potentially worse-looking) hyperparameter selections
- **OOS/IS ratio should improve**: The gap between IS and OOS narrows because IS is no longer inflated by CV leakage
- **OOS metrics could go either way**: If the current hyperparameters happen to be good despite the leaky CV, OOS may not change much. If they were overfit to the leakage, OOS could improve.
- **This is a methodological correction, not a strategy change**: The model, features, labeling, symbols — all stay identical to baseline (iter 068).

## Research Analysis (Checklist Categories)

### A. Feature Contribution — No Change
Features: same 106 as baseline (symbol-scoped discovery for BTCUSDT+ETHUSDT). No pruning or addition this iteration. The focus is purely on CV methodology.

### F. Statistical Rigor — Leakage Quantification

**Purge window calculation:**
- Triple barrier timeout = 10,080 minutes = 168 hours = 21 candles at 8h
- Each label's outcome depends on up to 21 future candles from the entry candle
- With TimeSeriesSplit (5 folds, ~880 samples/fold), labels within 21 candles of each fold boundary contaminate the adjacent fold

**Embargo calculation:**
- Even after purging, serial correlation exists between nearby candles (price autocorrelation, volatility clustering)
- Embargo = 2% of training set = 0.02 * 4,400 = 88 candles = ~29 days
- This is conservative — ensures the validation fold starts in a genuinely independent market state

**Effective training size impact:**
- 4 fold boundaries * 21 purged samples = 84 samples lost to purging
- Plus 88 samples lost to embargo
- Total loss: ~172 samples out of ~4,400 = ~4% loss
- Effective training per fold: ~3,300 (down from ~3,520) — negligible impact

### G. Stationarity & Memory — Deferred
This category is deferred to iteration 092 (fractional differentiation). No stationarity changes in this iteration.

### H. Overfitting Audit — Motivation

With N=88 completed iterations:
- E[max(SR_0)] ~ sqrt(2 * ln(88)) ~ sqrt(8.95) ~ 2.99
- Baseline OOS Sharpe +1.84 is below the expected random maximum of 2.99
- DSR < 0 — the baseline is NOT statistically significant against the multiple testing null

This motivates the MLP Foundation sequence: we need methodological rigor to produce results that ARE statistically significant. Fixing CV leakage is step 1.

## 1. Labeling

- Method: Triple barrier (unchanged from baseline iter 068)
- Parameters: TP=8%, SL=4%, timeout=10,080 min (7 days)
- Label function: existing `label_trades()` in labeling.py
- Binary classification (no ternary)

## 2. Symbol Universe

- Approach: Pooled model, BTC+ETH (unchanged from baseline)
- Symbols: BTCUSDT, ETHUSDT

## 3. Data Filtering

- No changes from baseline
- No outlier handling, no date exclusions

## 4. Feature Candidates

- Use existing 106 features from baseline (symbol-scoped discovery)
- No new features, no pruning this iteration
- Feature selection method: none (same as baseline)

## 4b. Stationarity Assessment (AFML Ch. 5)

- Deferred to iteration 092

## 5. Model Spec

- Model: LightGBM (LGBMClassifier)
- Task: Binary classification
- Hyperparameters: Optuna-optimized (same search space as baseline)
- Class weighting: is_unbalance=True
- Ensemble: 3 seeds [42, 123, 789]
- Confidence threshold: Optuna 0.50-0.85

## 5b. Sample Weighting (AFML Ch. 4)

- Deferred to iteration 091
- Current: abs(PnL) normalized to [1, 10] (unchanged)

## 5c. Cross-Validation (AFML Ch. 7) — THIS IS THE CHANGE

- Method: **PurgedKFoldCV** (replaces TimeSeriesSplit)
- n_splits: 5 (same as baseline)
- purge_window: 21 candles (timeout_minutes / candle_hours = 10080 / (8*60) = 21)
- embargo_pct: 0.02 (2% of training set)
- Effective training per fold after purging: ~3,300 samples (vs ~3,520 with TimeSeriesSplit)

**Implementation spec:**
- New file: `src/crypto_trade/strategies/ml/purged_cv.py`
- Class: `PurgedKFoldCV(n_splits, purge_window, embargo_pct)`
- Method: `split(X, y=None, open_times=None)` -> yields (train_indices, val_indices)
- The open_times parameter is required for time-based purging
- Drop-in replacement: change `tscv = TimeSeriesSplit(n_splits=cv_splits)` to `tscv = PurgedKFoldCV(n_splits=cv_splits, purge_window=21, embargo_pct=0.02)` and pass open_times to `split()`

## 5d. Overfitting Budget (AFML Ch. 11)

- Current trial count: 88 iterations
- Expected max random Sharpe: ~2.99
- Baseline OOS Sharpe: +1.84 (DSR < 0)
- This iteration will be trial 89

## 6. Walk-Forward Configuration

- Retraining frequency: monthly (unchanged)
- Minimum training window: 24 months (unchanged)
- CV method: **PurgedKFoldCV** with embargo (NEW — replaces TimeSeriesSplit)
- CV folds: 5
- Purge window: 21 candles
- Embargo: 2% of training set

## 7. Backtest Requirements

- Position sizing: fixed 100% weight per trade
- Fees: 0.1% per side (Binance futures taker)
- Slippage: none (assumed filled at close)
- Max positions: 1 per symbol
- Signal cooldown: 2 candles (16h)
- Dynamic ATR barriers: TP=2.9*NATR_21, SL=1.45*NATR_21

## 8. Report Requirements

Standard split reports: in_sample/ and out_of_sample/ with comparison.csv.
