# Iteration 142 Research Brief

**Type**: EXPLORATION (Multi-symbol screening — AVAX, ATOM, DOGE)
**Model Track**: Model E screening
**Researcher**: QR

## Section 0: Data Split

```
OOS_CUTOFF_DATE = 2025-03-24    (FIXED. NEVER CHANGES.)
```

## Motivation

After 3 failed Model A exploitation attempts (iters 136, 139, 140), pivoting to exploration of
untested symbols. The A(ATR)+C+D baseline (OOS Sharpe +2.32) is strong, but further gains
likely come from adding new symbols, not tweaking existing models.

**Screening scorecard so far** (8 symbols tested):
- ✅ LINK (Model C), BNB (Model D) — STRONG PASS
- ⚠️ SOL — MARGINAL
- ❌ BTC, ETH, ADA, XRP, DOT — FAIL standalone

**Untested candidates with good data coverage**:
- **AVAX** (L1, high-volume, since 2020) — never screened
- **ATOM** (Cosmos/IBC ecosystem, since 2020) — different dynamics, different beta
- **DOGE** (meme, since 2020) — only tested in pair with SHIB (iter 114-117 meme model)

## Research Checklist Categories

### B. Symbol Universe & Diversification

**Gate 1 (Data quality)**:
| Symbol | First | IS candles | Status |
|--------|-------|-----------|--------|
| AVAX | 2020-09-23 | 4,929 | PASS |
| ATOM | 2020-02-07 | 5,615 | PASS |
| DOGE | 2020-07-10 | 5,153 | PASS |

All pass Gate 1 (≥1,095 IS candles, first candle before 2023-07-01).

**Gate 3 (Standalone profitability)** — Testing this iteration. Each symbol must achieve:
- IS Sharpe > 0.0
- IS WR > 33.3% (break-even for 2:1 TP/SL)
- ≥ 100 IS trades

### E. Trade Pattern Analysis

The 3 symbols represent 3 distinct crypto segments:
- **AVAX**: Smart contract L1, correlated with ETH (alt-L1 narrative)
- **ATOM**: IBC/cosmos ecosystem, lower correlation with BTC
- **DOGE**: Meme/retail-driven, different volatility regime

Hypothesis: At least one will pass Gate 3 given LINK/BNB's success with similar configs.

## Configuration (per symbol)

Matching Model C/D (LINK/BNB) template — proven working config:

| Parameter | Value |
|-----------|-------|
| Symbols | [SYMBOL] (single) |
| Labeling | ATR: TP=3.5×NATR, SL=1.75×NATR |
| Execution | ATR: TP=3.5×NATR, SL=1.75×NATR |
| Training months | 24 |
| Timeout | 7 days (10080 min) |
| Features | Auto-discovery (symbol-scoped) |
| Ensemble | 5 seeds [42, 123, 456, 789, 1001] |
| CV | 5 folds, 50 Optuna trials |
| CV gap | 22 (22 × 1 symbol) |
| Cooldown | 2 candles |
| Fee | 0.1% |

## Screening Criteria

**PASS**:
- IS Sharpe > +0.3 (matching LINK/BNB-level signal)
- IS WR > 40%
- IS trades ≥ 100
- OOS Sharpe > 0 (profitable OOS)
- OOS trades ≥ 30

**MARGINAL**:
- IS Sharpe between 0 and +0.3
- (Not worth adding to portfolio)

**FAIL**:
- IS Sharpe ≤ 0 OR IS WR ≤ 33.3% OR OOS Sharpe < 0

## Next Steps

If multiple PASS → test adding the strongest to A+C+D portfolio in iter 143.
If only one PASS → same, with that one symbol.
If all FAIL → different screening approach (different ATR multipliers, or different symbols).
