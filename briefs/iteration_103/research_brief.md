# Research Brief — Iteration 103

**Type**: EXPLORATION
**Hypothesis**: Enriched meta-labeling with regime-aware features (NATR, ADX, symbol) produces useful trade filtering without the over-filtering problem of iter 102's minimal meta-features.

## Section 0: Data Split (Verbatim)

```
OOS_CUTOFF_DATE = 2025-03-24    (FIXED. NEVER CHANGES.)
```

## Section 1: Problem Statement

Iter 102 showed meta-labeling with [confidence, direction] filters to 2% pass rate — redundant with the confidence threshold. The meta-model needs features that capture WHY certain predictions profit and others don't, beyond just confidence level.

## Section 2: Changes from Iter 102

**Meta-features (5 instead of 2):**
1. `confidence`: max(P(long), P(short))
2. `direction`: 1 (long) or -1 (short)
3. `natr`: vol_natr_21 — volatility regime at prediction time
4. `adx`: trend_adx_14 — trend strength at prediction time
5. `symbol_id`: 0/1 encoding — per-symbol filtering

These features let the meta-model learn patterns like:
- "BTC longs in low-ADX (<15) environments rarely profit"
- "ETH shorts in high-volatility environments tend to profit"
- "High confidence matters more in trending (high ADX) markets"

**Meta-model capacity (increased):**
- max_depth: 2 → 3 (8 leaves vs 4)
- n_estimators: 50 → 100
- This allows more nuanced regime-dependent filtering

**Meta threshold (lowered):**
- 0.5 → 0.4
- Increases pass rate to target ~20-40% (vs 2% in iter 102)

## Section 3: Risk Assessment

More meta-features and capacity increase overfitting risk. Mitigations:
- Still a simple model (depth=3, 8 leaves, 100 trees)
- Meta-features are regime indicators, not arbitrary columns
- Lower threshold (0.4) prevents excessive filtering
