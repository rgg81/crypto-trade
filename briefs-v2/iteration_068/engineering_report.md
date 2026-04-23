# iter-v2/068 Engineering Report — z-score OOD 2.5 → 2.4

## Build

- Branch: `iteration-v2/068` from `quant-research` at `46ea581`
- Code: single param change, `RiskV2Config.zscore_threshold=2.5 → 2.4`
- Same 4 baseline symbols. All other config identical to iter-v2/059-clean.

## Results

| Metric | iter-v2/059-clean | **iter-v2/068** | Δ |
|---|---|---|---|
| IS monthly Sharpe | +1.042 | +0.978 | −6.1% |
| IS daily Sharpe | +0.974 | +1.069 | +9.7% |
| OOS monthly Sharpe | +1.659 | +1.445 | **−13%** |
| OOS daily Sharpe | +1.663 | +1.384 | −17% |
| Combined monthly | +2.701 | +2.424 | −10% |
| OOS PF | 1.78 | 1.65 | −7.4% |
| OOS MaxDD | 22.61% | 22.61% | identical |
| OOS WR | 49.1% | 47.2% | −1.9pp |
| OOS trades | 57 | 53 | −7% |
| OOS net PnL | +79.98 | +65.90 | −18% |

## Per-symbol OOS (weighted-PnL share, authoritative)

| Symbol | OOS trades | wpnl | Share |
|---|---|---|---|
| NEARUSDT | 14 | +40.54 | **56.10%** (was 44.44%) |
| XRPUSDT | 6 | +19.85 | 27.47% |
| SOLUSDT | 18 | +11.87 | 16.42% |
| DOGEUSDT | 15 | −6.37 | 0.0% |

**NEAR concentration got WORSE** (+11.7pp). Tighter z-score preferentially
killed signals on non-NEAR symbols while NEAR signals survived. DOGE
flipped to net-negative OOS.

## Why tighter didn't help

iter-v2/050 (z=3.0) → iter-v2/059-clean (z=2.5): OOS monthly +8%, IMPROVED.
iter-v2/059-clean (z=2.5) → iter-v2/068 (z=2.4): OOS monthly −13%, DEGRADED.
iter-v2/060 (z=2.25): OOS trades <50, FAILED earlier.

**z=2.5 is the local optimum.** 2.4 falls on the wrong side.

## MERGE criteria

| # | Criterion | Target | Actual | Pass |
|---|---|---|---|---|
| 1 | Combined monthly ≥ 2.70 | ≥ 2.70 | 2.42 | FAIL |
| 2 | OOS monthly ≥ 1.41 | ≥ 1.41 | 1.45 | PASS (marginal) |
| 3 | IS monthly ≥ 0.88 | ≥ 0.88 | 0.98 | PASS |
| 4 | OOS MaxDD ≤ 27.1% | ≤ 27.1% | 22.61% | PASS |
| 5 | PF, trades, Sharpe>0 | — | 1.65, 53, +1.38 | PASS |
| 6 | Concentration ≤ 50% | ≤ 50% | 56.10% | FAIL |

2 FAILs. **NO-MERGE.**

## What we learned for iter-v2/069

iter-v2/068 is the 6th consecutive NO-MERGE. Per the updated skill:
- Category A (feature analysis) is NOW DUE
- Need ≥4 categories from A-H covered in the next brief
- Need a BOLD idea (not just parameter tweaks)

Fortunately Category A is already done — see
`briefs-v2/iteration_068/qr_phase1_findings.md`. Key findings for
iter-v2/069's brief:

1. **40 features contain 8 pairs with |rho|>0.85** (4 near-identical
   volatility estimators)
2. **8 features non-stationary** (mean drift >0.3σ between IS halves)
3. **Fracdiff_logclose_d04 is the strongest predictor** (mean
   rho −0.073)
4. **Many features have near-zero univariate rho** — candidates for
   replacement

iter-v2/069 plan: **feature pruning + bold replacement**. Drop 6
redundant features, add 3-4 new feature families (RSI divergence,
liquidity impact, gap feature). This is a BOLD iteration.
