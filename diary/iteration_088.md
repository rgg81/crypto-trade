# Iteration 088 Diary — 2026-03-30

## Merge Decision: NO-MERGE (EARLY STOP)

Early-stopped: Year 2022 PnL=-4.9%, WR=37.6%, 101 trades. IS Sharpe -0.06, MaxDD 95.7%. Ternary with neutral_threshold=1.0% catastrophically worse than 2.0%.

**OOS cutoff**: 2025-03-24

## Hypothesis

Lower ternary neutral threshold from 2.0% (iter 080) to 1.0% to retain more training samples and generate more trades while filtering only the most ambiguous timeout candles.

## Configuration Summary

- OOS cutoff: 2025-03-24 (fixed)
- **Ternary labeling**: neutral_threshold_pct=1.0% (was 2.0% in iter 080)
- Threshold range: [0.50, 0.85] (same as baseline)
- Features: 115 (global intersection)
- Model: LGBMClassifier multiclass, ensemble [42, 123, 789]
- Walk-forward: monthly, 24mo window, 5 CV folds, 50 Optuna trials
- Execution: Dynamic ATR barriers TP=2.9, SL=1.45, cooldown=2

## Results: In-Sample (partial — 2022 only, early-stopped)

| Metric | Iter 088 | Baseline (068) | Iter 080 (ternary 2.0%) |
|--------|----------|----------------|------------------------|
| Sharpe | **-0.06** | +1.22 | +1.26 |
| WR | **38.2%** | 43.4% | 44.6% |
| PF | **0.985** | 1.35 | 1.38 |
| MaxDD | **95.7%** | 45.9% | 56.1% |
| Trades | 102 (2022 only) | 373 (full IS) | 314 (full IS) |

## What Happened

**The neutral class at 1.0% was too small for LightGBM multiclass classification.**

First training window (2020-2022) produced: long 54.8%, short 40.4%, neutral **4.8%**. With only 212 out of 4,386 samples in the neutral class, LightGBM couldn't learn a meaningful boundary. The 3-class model was worse than both binary and ternary-2.0%.

This is NOT a gradual degradation — it's a qualitative failure. The model with 4.8% neutrals is fundamentally different from one with 16.7% neutrals. Below some critical mass (~10%?), the neutral class destabilizes the entire classification.

**BTC was particularly devastated**: 32.4% WR (below break-even), -8.3% PnL. ETH was marginal at 41.2% WR.

**The SL rate of 55.9% is extremely high** (vs ~50% for baseline). More trades hit stop-loss, indicating the model's directional accuracy degraded substantially.

## Quantifying the Gap

WR: 38.2%, break-even 33.3%, gap **+4.9pp**. But PF 0.985 means the strategy loses money net of fees. IS MaxDD 95.7% — effectively total capital destruction. The strategy is uninvestable.

Compared to iter 080 (ternary 2.0%): WR gap is -6.4pp, MaxDD gap is +39.6pp. The 1.0% threshold is dramatically worse in every metric.

## Exploration/Exploitation Tracker

Last 10 (iters 079-088): [E, X, X(abandoned), E, E, E, E, E, E, **X**]
Exploration rate: 7/10 = 70%
Type: **EXPLOITATION** (1-variable parameter change within ternary approach)

## Research Checklist

Completed 4 categories:
- **A**: Feature verification — 115 global intersection features confirmed, no slow features
- **C**: Labeling analysis — detailed neutral threshold comparison (0.5% to 3.0%), IS label distributions
- **E**: Trade pattern analysis — identified filtered candle quality by threshold band
- **F**: Statistical rigor — binomial tests, trade count estimation, PnL gap analysis

**Key finding from C**: Neutral threshold 1.0% only filters 7.9% of labels (vs 16.7% at 2.0%). The filtered candles (WR 49.4%) are genuinely ambiguous. But the 1-2% band candles (WR 45.9%) retained by 1.0% are still weak — and keeping them doesn't help enough to offset the damage from a tiny neutral class.

## lgbm.py Code Review

No bugs found. The ternary labeling and multiclass code work correctly. The problem is structural: the neutral class proportion, not the implementation. The `neutral_threshold_pct` parameter correctly controls the threshold, and the multiclass training pipeline handles 3-class labels properly.

## Lessons Learned

1. **Ternary labeling requires a minimum neutral class size of ~10-15%.** Below this, the multiclass model is worse than binary. The neutral class needs enough samples to be a meaningful decision boundary, not just noise.

2. **2.0% neutral threshold (iter 080) is near-optimal for ternary.** It produces 16.7% neutrals — large enough for stable learning, small enough to retain most training data. Going lower (1.0%) breaks the model.

3. **The 1-2% return band is NOT worth keeping as training labels.** These candles have WR 45.9% — better than random but poor. Including them as long/short labels adds noise. Iter 080's decision to neutralize them was correct.

4. **IS MaxDD 95.7% in the first year is an immediate red flag.** Any strategy with Year 1 MaxDD > 50% should be considered fundamentally broken.

5. **Feature count changed from 106 (baseline) to 115 (current global intersection).** This is a confounding variable — the 9 extra features may have contributed to the failure. Future iterations that compare to iter 080 should verify the feature count matches.

## Next Iteration Ideas

**After 12 consecutive NO-MERGE (077-088), structural changes are mandatory. Parameter-only changes within the current approach are exhausted.**

1. **EXPLOITATION: Exact iter 080 reproduction** — Run iter 080's exact config (ternary 2.0%, 106 features) on current parquets to verify it still produces OOS Sharpe ≈ +1.00. If it does, ternary 2.0% is confirmed as the second-best config. If not, the parquet changes (115 vs 106 features) explain the degradation.

2. **EXPLORATION: Per-symbol models** — Train separate LightGBM for BTC and ETH. BTC had 32.4% WR here (below break-even) while ETH had 41.2%. Different models could specialize. This is the biggest untested structural change from the exploration bank.

3. **EXPLORATION: Binary baseline with 115 features** — Test whether the 115-feature global intersection (vs baseline's 106) degrades the binary model. This isolates the feature change confound.

4. **EXPLORATION: Completely different approach** — After 88 iterations, the LightGBM framework may be at its ceiling. Consider: (a) simpler rule-based strategies using the identified feature signals, (b) different ML model (XGBoost, CatBoost), (c) fundamentally different trade timing (not candle-close entry).
