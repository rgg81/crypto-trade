# Iteration 122 Diary

**Date**: 2026-04-02
**Type**: EXPLORATION (entropy features for meme model)
**Model Track**: Combined portfolio (BTC/ETH + DOGE/SHIB with entropy features)
**Decision**: **NO-MERGE** — OOS Sharpe -0.42 (baseline +1.18), catastrophic collapse

## Hypothesis

Adding 3 entropy features (Shannon entropy, approximate entropy) to the meme model would capture market "randomness" — a signal dimension not represented by existing features. High entropy = noisy/unpredictable, low entropy = patterned/tradeable.

## Results

### Combined OOS vs Baseline (iter 119)

| Metric | Iter 122 | Baseline (119) | Change |
|--------|----------|----------------|--------|
| OOS Sharpe | **-0.42** | +1.18 | **-136%** |
| OOS WR | **39.0%** | 43.6% | -4.6pp |
| OOS PF | **0.93** | 1.22 | -24% |
| OOS MaxDD | **163.9%** | 46.4% | +253% (catastrophic) |
| OOS Trades | 213 | 188 | +13% |
| OOS Net PnL | **-43.6%** | +100.2% | **-143pp** |
| IS Sharpe | 0.37 | 0.86 | -57% |
| IS/OOS Ratio | N/A (OOS negative) | 0.72 | N/A |

### OOS Per-Symbol

| Symbol | Trades | WR | Net PnL | vs Baseline |
|--------|--------|----|---------|-------------|
| ETHUSDT | 55 | 45.5% | +52.1% | ETH improved (-0.5pp WR but -1.7 PnL) |
| BTCUSDT | 52 | 38.5% | +16.8% | BTC improved (+5.2pp WR, +19.5 PnL) |
| 1000SHIBUSDT | 53 | 41.5% | **-27.7%** | SHIB collapsed (was +65.8%) |
| DOGEUSDT | 53 | 30.2% | **-84.8%** | DOGE collapsed (was -16.7%) |

## Root Cause Analysis

Two confounding changes occurred simultaneously:

### 1. Parquet Regeneration Changed BTC/ETH Features
Model A uses `feature_columns=None` (auto-discovery). The parquet regeneration added entropy features to all parquets, so auto-discovery picked up 196 features instead of 185. This is an uncontrolled variable — Model A results are not comparable to the baseline.

BTC/ETH actually improved slightly (BTC from -2.7% to +16.8%, ETH from +53.8% to +52.1%), suggesting the 196 features didn't hurt Model A much. But this is a confound.

### 2. Entropy Features Destroyed Meme Model Signal
The meme model went from OOS +49.1% (SHIB +65.8, DOGE -16.7) to OOS **-112.4%** (SHIB -27.7, DOGE -84.8). This is a catastrophic regression.

**Why entropy features hurt:**
- Entropy is a **high-cardinality continuous feature** — LightGBM's split-finding algorithm gives it disproportionate importance (MDI bias)
- With only 46 features and ~4,400 training samples, adding 3 highly-variable entropy features may have displaced more stable features in Optuna's optimization
- The removed features (stat_skew_10, stat_autocorr_lag1, meme_indecision) may have been more important than their low MDI rank suggested — MDI is biased toward continuous features, which is exactly what entropy is

### 3. More Trades But Worse Quality
Trade count increased from 188 to 213 (13% more). The entropy features may have lowered Optuna's selected confidence thresholds (encouraging the model to trade when it shouldn't), leading to lower-quality trades.

## Hard Constraints

| Constraint | Threshold | Iter 122 | Pass? |
|------------|-----------|----------|-------|
| OOS Sharpe > baseline | > +1.18 | -0.42 | **FAIL** |
| OOS MaxDD ≤ 1.2 × baseline | ≤ 55.6% | 163.9% | **FAIL** |
| OOS Trades ≥ 50 | ≥ 50 | 213 | PASS |
| OOS PF > 1.0 | > 1.0 | 0.93 | **FAIL** |
| IS/OOS Sharpe ratio > 0.5 | > 0.5 | N/A | **FAIL** |

## Label Leakage Audit

- Model A (BTC/ETH): CV gap = 44 (22 × 2 symbols). Verified.
- Model B (DOGE/SHIB): CV gap = 44 (22 × 2 symbols). Verified.

## lgbm.py Code Review

No code changes. The entropy features are clean (no lookahead, rolling window only). The issue is signal quality, not bugs.

## Gap Quantification

Combined OOS WR 39.0%, break-even 33.3%, gap +5.7pp (was +10.3pp). The meme model's WR collapsed below break-even for DOGE (30.2% < 33.3%).

## What We Learned

1. **Entropy features hurt the meme model.** Shannon entropy and approximate entropy, despite their theoretical appeal (AFML Ch. 18), did not add predictive value for DOGE/SHIB. They likely absorbed Optuna's optimization budget away from better features.

2. **Never regenerate parquets AND change features in the same iteration.** The parquet regen changed Model A's feature count from 185 to 196, introducing an uncontrolled variable. In future: regenerate parquets in a separate iteration with no other changes.

3. **Low-importance features may still be important.** The features removed (stat_skew_10, stat_autocorr_lag1, meme_indecision) had low MDI importance, but removing them and adding high-cardinality entropy features caused catastrophic collapse. MDI undervalues low-cardinality/binary features.

4. **This iteration confirms the user's feedback: test single models independently.** Had we only run Model B (meme), this would have taken ~1h instead of 4h and isolated the entropy effect cleanly.

## Exploration/Exploitation Tracker

Last 10 iterations: [X, E, E, E, X, E, X, X, X, **E**] (iters 113-122)
Exploration rate: 6/10 = 60%
This iteration: EXPLORATION (entropy features)

## Research Checklist

- **A** (features): Entropy features as novel signal dimension — FAILED
- **D** (feature frequency): Window sizes 20 and 50 tested — produced high-cardinality features that destabilized the model

## Next Iteration Ideas

Per user feedback: **develop new individual models first, test single-model only**.

1. **Revert meme model to iter 118 features** (EXPLOITATION, single-model only) — Run ONLY Model B with the original 46 features, no entropy. Confirm the meme model baseline is still intact after parquet regeneration. This is a diagnostic run.

2. **Model C: L1 alts (SOL+AVAX)** (EXPLORATION, single-model) — Screen SOL and AVAX through the 5-gate protocol. If they pass, build a new L1 altcoin model with the meme model's proven architecture (pruned features, ATR labeling, 5-seed ensemble). Different market dynamics from BTC/ETH and meme — potential for decorrelated returns.

3. **Model C: DeFi tokens (AAVE+UNI)** (EXPLORATION, single-model) — Alternative new model track. DeFi tokens have fundamentally different drivers (TVL, protocol revenue) than price-action-driven meme coins. May capture a different signal dimension.

4. **CUSUM structural breaks for meme model** (EXPLORATION, single-model) — Instead of entropy, try CUSUM break features. These are binary/low-cardinality (break happened yes/no), avoiding the MDI bias problem that sank entropy features.
