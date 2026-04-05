# Iteration 157 Engineering Report

## Methodology

Post-processing rule-based meta-filter on iter 138 trades. All rules are
derived from IS aggregate statistics (bucket WR/PnL analysis). No ML, no
per-trade model. VT from iter 152 (target=0.3, lookback=45, floor=0.33)
applied to kept trades.

## Rules Tested

| Rule | Condition | Trades Dropped |
|------|-----------|----------------|
| baseline | — | 0 |
| A_no_short | direction = -1 | 401 |
| B_targeted_short | direction = -1 AND symbol ∈ {BTC, BNB, LINK} | 299 |
| C_hour23 | hour_of_day = 23 | 277 |
| D_adx_q3 | 19.6 < sym_ADX_14 ≤ 34.6 | 403 |
| E_B_plus_C | B OR C | 478 |
| F_weak_bucket | (B) AND (hour=23 OR ADX_Q3) | 189 |
| G_hour23_adx_q3 | hour=23 OR (19.6 < ADX_14 ≤ 34.6) | 546 |

## Results

| Rule | IS n | OOS n | IS Sharpe | OOS Sharpe | IS MaxDD | OOS MaxDD | OOS PF |
|------|------|-------|-----------|-----------|----------|-----------|--------|
| **baseline** | 652 | 164 | **+1.3320** | **+2.8286** | 76.89% | 21.81% | 1.76 |
| A_no_short | 346 | 69 | +1.3874 | +1.8703 | 52.44% | 20.09% | 1.84 |
| B_targeted_short | 430 | 87 | +1.4658 | +2.3478 | 59.41% | 20.09% | 1.87 |
| C_hour23 | 427 | 112 | +1.6612 | +2.6606 | 37.35% | 15.78% | 1.96 |
| **D_adx_q3** | 326 | 87 | +1.6957 | **+2.9462** | 31.93% | 16.79% | 2.43 |
| E_B_plus_C | 281 | 57 | +1.5606 | +2.4133 | 37.24% | 10.96% | 2.29 |
| **F_weak_bucket** | 505 | 122 | +1.7713 | **+2.9231** | 55.50% | 20.09% | 1.96 |
| **G_hour23_adx_q3** [IS-best] | 211 | 59 | **+1.8342** | +2.5994 | 17.85% | 13.31% | 2.72 |

**Every rule improves IS Sharpe and OOS MaxDD vs baseline.**

## IS-Best Selection → OOS Validation

Per the research brief: "max IS Sharpe with ≥ 150 IS trades." → **G_hour23_adx_q3**.

| Metric | Baseline | G_hour23_adx_q3 | Δ |
|--------|----------|-----------------|---|
| IS Sharpe | +1.3320 | +1.8342 | +0.50 (+38%) |
| IS trades | 652 | 211 | -68% |
| OOS Sharpe | **+2.8286** | **+2.5994** | **-0.23 (-8.1%)** |
| OOS MaxDD | 21.81% | 13.31% | -39% (improvement) |
| OOS PF | 1.76 | 2.72 | +55% |
| OOS Calmar | 5.46 | 5.15 | -6% |
| OOS PnL | +119.1% | +68.6% | -42% |

**IS-best fails primary OOS Sharpe constraint.**

## Hard Constraints (IS-best G)

| Constraint | Threshold | Actual | Pass? |
|------------|-----------|--------|-------|
| OOS Sharpe > baseline | > +2.83 | +2.60 | **FAIL (-8.1%)** |
| OOS MaxDD ≤ 38.7% | ≤ 38.7% | 13.31% | PASS |
| OOS trades ≥ 50 | ≥ 50 | 59 | PASS |
| OOS PF > 1.0 | > 1.0 | 2.72 | PASS |
| Concentration ≤ 50% | ≤ 50% | ETH 33.0% | PASS |
| IS/OOS ratio > 0.5 | > 0.5 | 0.71 | PASS (improved vs 0.47) |

**Decision: NO-MERGE** (primary constraint fails).

## Honorable Mentions (Not Selectable Under IS-Best)

**D_adx_q3** (simple: drop ADX_Q3 bucket):
- IS Sharpe: +1.70, OOS Sharpe: +2.95 (**+4.2% vs baseline**)
- OOS MaxDD: 16.79%, OOS PF: 2.43, OOS Calmar: 5.44
- 1-parameter rule, interpretable

**F_weak_bucket** (compound: BTC/BNB/LINK SHORTs × (hour=23 OR ADX_Q3)):
- IS Sharpe: +1.77, OOS Sharpe: +2.92 (**+3.3% vs baseline**)
- OOS MaxDD: 20.09%, OOS PF: 1.96, OOS Calmar: 5.45
- More conservative (drops 189 vs G's 546)

Both beat baseline OOS Sharpe, but neither is IS-best. Claiming them would
be look-ahead.

## IS-Selection Rule Pathology

The IS-best rule (G) picks the MOST aggressive filter (drops 84% of
trades) because that config has the highest IS Sharpe. But aggressive
filtering concentrates trade count on the IS period, inflating IS Sharpe
while reducing OOS robustness.

**t-stat-adjusted IS Sharpe** (Sharpe × sqrt(n)) would pick differently:
| Rule | IS Sharpe | IS n | Sharpe×sqrt(n) |
|------|-----------|------|---------------|
| baseline | 1.33 | 652 | 33.9 |
| G | 1.83 | 211 | 26.6 |
| **F** | **1.77** | **505** | **39.8** ⭐ |
| D | 1.70 | 326 | 30.7 |

F wins on t-stat-adjusted. But this selection rule wasn't specified in the
research brief, so G is the walk-forward-valid winner.

## Code Quality / Label Leakage

No engine changes, post-processing only. Rules are constants derived from
bucket analysis — no per-trade learning. Walk-forward valid by construction:
IS buckets were computed from IS data only, OOS trades classified by
rule at open_time.

## Conclusion

Rule-based meta-filter fails walk-forward-valid IS-best selection. However,
the research reveals that SIMPLER, LESS AGGRESSIVE rules (D, F) beat
baseline OOS Sharpe while the IS-best rule (G) overfits. This suggests
the IS-selection metric needs refinement (t-stat adjustment or minimum
trade count) rather than abandoning rule-based filtering entirely.
