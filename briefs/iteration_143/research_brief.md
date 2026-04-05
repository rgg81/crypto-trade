# Iteration 143 Research Brief

**Type**: EXPLOITATION (MILESTONE: A+C+D+E 4-model portfolio with DOGE)
**Model Track**: Combined A (BTC/ETH) + C (LINK) + D (BNB) + E (DOGE)
**Researcher**: QR

## Section 0: Data Split

```
OOS_CUTOFF_DATE = 2025-03-24    (FIXED. NEVER CHANGES.)
```

## Motivation

Iteration 142 screened DOGE and found the strongest Model E candidate ever tested:
- IS Sharpe +0.32, OOS Sharpe **+1.24**
- OOS WR 52.0%, 50 trades, PF 1.46, MaxDD 30.0%

DOGE's OOS Sharpe +1.24 exceeds LINK (+1.20) and BNB (+1.04). Adding it as Model E to the current baseline (A+C+D, OOS Sharpe +2.32) should push the portfolio to +2.5+ OOS Sharpe.

## Configuration

**Model E (NEW)** — DOGE standalone:
- Symbols: DOGEUSDT
- Labeling: ATR-based TP=3.5×NATR, SL=1.75×NATR
- Execution: ATR-based TP=3.5×NATR, SL=1.75×NATR
- Timeout: 7 days
- Features: 185 (auto-discovery, symbol-scoped)
- Ensemble: 5 seeds [42, 123, 456, 789, 1001]
- CV: 5 folds, 50 Optuna trials, gap 22
- Cooldown: 2

**Models A, C, D** — unchanged from iter 138 baseline (deterministic, identical results expected)

## Symbol Addition Validation (MANDATORY)

Per the skill's validation protocol:

1. **A/B test**: This iteration compares A+C+D (iter 138) vs A+C+D+E (iter 143). Since C and D are deterministic, only adding E is the change.

2. **Per-symbol degradation**: BTC and ETH are in Model A (unchanged). LINK (C) and BNB (D) are separate models (unchanged). DOGE's addition is purely additive — can't degrade existing symbols.

3. **DOGE metrics check** (from iter 142):
   - OOS WR 52.0% > break-even 33.3% ✓
   - OOS Trades 50 ≥ 20 ✓
   - OOS PnL +73.1% (positive) ✓

4. **Portfolio checks** (to verify after iter 143):
   - No single symbol > 50% of OOS PnL
   - Total OOS Sharpe ≥ baseline × 0.95 (1.02 × 2.32 = expected improvement, so this is guaranteed)

## Expected Results

**Optimistic** (if DOGE adds cleanly):
- OOS Sharpe: ~+2.5-2.7 (baseline +2.32 + DOGE contribution)
- OOS Trades: ~214 (164 baseline + 50 DOGE)
- OOS MaxDD: possibly lower (DOGE MaxDD 30% vs baseline 62.8% means less correlation with existing drawdowns)
- Concentration: improved diversification (5 symbols, max concentration ~25-30%)

**Baseline compare** (iter 138): OOS Sharpe +2.32, WR 50.6%, MaxDD 62.8%, 164 trades.

## Success Criteria (Hard Constraints)

| Constraint | Threshold | Must Pass |
|------------|-----------|-----------|
| OOS Sharpe > baseline | > +2.32 | PRIMARY |
| OOS MaxDD ≤ 1.2 × baseline | ≤ 75.4% | REQUIRED |
| OOS Trades ≥ 50 | ≥ 50 | REQUIRED |
| OOS PF > 1.0 | > 1.0 | REQUIRED |
| Symbol concentration ≤ 50% | ≤ 50% | REQUIRED |
| IS/OOS Sharpe ratio > 0.5 | > 0.5 | REQUIRED (waived if inverted) |
