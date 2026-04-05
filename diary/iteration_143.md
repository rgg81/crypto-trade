# Iteration 143 Diary

**Date**: 2026-04-05
**Type**: EXPLOITATION (MILESTONE: A+C+D+E 4-model portfolio)
**Model Track**: Combined A (BTC/ETH) + C (LINK) + D (BNB) + E (DOGE)
**Decision**: **NO-MERGE** — OOS Sharpe +2.30 < baseline +2.32 AND MaxDD exceeds 1.2x threshold.

## Results vs Baseline

| Metric | Iter 143 (A+C+D+E) | Baseline 138 (A+C+D) | Change |
|--------|-------------------|----------------------|--------|
| OOS Sharpe | **+2.30** | +2.32 | **-0.9%** |
| OOS Sortino | +3.19 | +3.41 | -6.5% |
| OOS WR | 50.9% | 50.6% | +0.3pp |
| OOS PF | 1.48 | 1.49 | -0.7% |
| OOS MaxDD | **92.5%** | 62.8% | **+47%** |
| OOS Trades | 214 | 164 | +30% |
| OOS Net PnL | +245.5% | +172.4% | +42% |
| OOS Calmar | 2.65 | 2.74 | -3.3% |

## Analysis

### DOGE is strong standalone but doesn't improve the portfolio

DOGE screening (iter 142) showed OOS Sharpe +1.24 — stronger than LINK (+1.20) and BNB (+1.04). Yet adding it to the portfolio produces:
- **No Sharpe improvement** (-0.9%)
- **MaxDD explodes +47%** (62.8% → 92.5%)
- Higher absolute PnL (+42%) but proportional volatility

### Why does a strong individual model fail to improve the portfolio?

The mechanism is temporal correlation of drawdowns. DOGE's losing trades cluster with the other models' losing trades, amplifying aggregate drawdowns without proportionally smoothing returns.

Consider: DOGE standalone had MaxDD of only 30%. A+C+D baseline had 62.8%. Naively combining independent returns would expect aggregate MaxDD around 40-50% (diversification benefit). Instead, 92.5%. This means DOGE's drawdowns OVERLAP with the portfolio's drawdowns — no diversification in drawdown timing.

### The diversification paradox

**Per-symbol concentration is excellent**:
- DOGE 29.8%, ETH 24.5%, LINK 22.8%, BNB 15.4%, BTC 7.5%
- First time we meet the strict 30% concentration constraint

But **temporal correlation is poor**:
- All 5 models lose money during the same crypto-wide drawdowns
- DOGE's retail-driven crashes coincide with BTC-driven drawdowns
- No regime-level diversification

This is a known portfolio construction lesson: high Sharpe individually ≠ high Sharpe in combination. What matters is the **covariance structure of returns**, not just individual Sharpes.

### Symbol concentration constraint passes

DOGE 29.8% is the first time any iteration passes the strict ≤30% concentration constraint. This represents genuine symbol diversification at the PnL level. But diversification at the temporal/drawdown level is what matters for risk, and that did not improve.

### Gap quantification

Portfolio gap: OOS Sharpe +2.30 vs baseline +2.32 = -0.02 (marginal). MaxDD gap: 92.5% vs 75.4% threshold = +17.1pp over.

## Hard Constraints Analysis

- **Primary (Sharpe)**: FAIL by 0.9% (within noise range)
- **MaxDD**: FAIL by 23% — the significant failure
- **All others**: PASS

The MaxDD failure is decisive. Even if we waived the marginal Sharpe regression, 92.5% MaxDD is too risky.

## Label Leakage Audit

Used deterministic trade outputs from iter 138 and iter 142. No new label leakage concerns.

## Research Checklist

- **B (Symbol Universe)**: DOGE's standalone Sharpe didn't translate to portfolio improvement. Key insight: covariance matters more than individual Sharpe.
- **E (Trade Pattern)**: DOGE added 50 OOS trades (+30%), improving concentration but amplifying MaxDD.

## Exploration/Exploitation Tracker

Last 10 iterations: [E, E, X, E, X, X, E, X, X, **X**] (iters 134-143)
Exploration rate: 4/10 = 40% ✓

## Next Iteration Ideas

1. **ACCEPT baseline +2.32 as final** (no more iteration) — After 7 Model A/symbol tweaks since iter 138 (all failed to improve), the A+C+D portfolio may be at a local maximum. DOGE is individually strong but doesn't help. The MaxDD constraint is hard to beat structurally.

2. **Position sizing: reduce DOGE weight** (EXPLORATION) — Instead of equal weighting, test DOGE at 0.5× weight. Would reduce its drawdown contribution while keeping some diversification benefit.

3. **Trade correlation analysis** (EXPLORATION, analytical) — Compute actual temporal correlation of losing trades across A/C/D/E. Identify whether the 92.5% MaxDD happens on a specific event (e.g., a single bad week) or is structurally distributed.

4. **Alternative Model E symbols** (EXPLORATION) — Try NEAR, SUI, INJ, or other symbols not yet tested. Maybe one has lower temporal correlation with BTC/ETH/LINK/BNB drawdowns.

5. **Different Model E barrier config** (EXPLOITATION) — DOGE with wider barriers (4x/2x) might produce fewer, higher-quality trades that don't align with portfolio drawdowns.
