# Iteration 183 — XLM screen with R1+R2

**Date**: 2026-04-22
**Type**: EXPLORATION (new candidate, low-correlation)
**Baseline**: v0.176

## Section 0 — Data Split (non-negotiable)

- OOS cutoff: 2025-03-24 (fixed, from `src/crypto_trade/config.py`)
- IS data: 2020-01-20 → 2025-03-24 (5,653 bars for XLM)
- OOS data: 2025-03-24 onwards (1,026 bars for XLM)
- Walk-forward: 24-month training windows, labeling confined to window

## Phase 1 — EDA (IS only)

`analysis/iteration_183/xlm_eda.py` decomposition:

```
=== XLMUSDT ===
  IS annualized vol: 98.92%
  Year-by-year IS PnL and annualized vol:
    2020: PnL  +98.8%  vol 105.5%
    2021: PnL +108.3%  vol 135.8%
    2022: PnL  -73.3%  vol 77.3%
    2023: PnL  +81.7%  vol 67.2%
    2024: PnL +157.6%  vol 93.2%
    2025: PnL  -14.9%  vol 103.8%
```

**Volatility is comparable to LTC/LINK/DOT — 99% annualized means strategy-viable signal without being illiquid-thin.**

**2022 drawdown −75.7%**, on par with peers: BTC −67%, LTC −71.5%, LINK −80.7%, DOT −85.9%.

## Phase 2 — Labeling (IS only)

Use the same ATR-based triple-barrier as LTC/LINK/DOT: `atr_tp_multiplier=3.5`, `atr_sl_multiplier=1.75`, `timeout_minutes=10080` (7 days). Rationale: this labeling has won on three altcoin symbols already; no evidence XLM needs a different regime.

## Phase 3 — Symbol Universe Analysis (IS only)

Correlation matrix of daily log returns 2023-01-01 → OOS cutoff:

| pair | ρ |
|---|---:|
| XLM ↔ BTC | **0.468** |
| XLM ↔ ETH | **0.498** |
| XLM ↔ LINK | 0.516 |
| XLM ↔ LTC | 0.548 |
| XLM ↔ DOT | 0.654 |
| (within baseline portfolio) BTC ↔ ETH | 0.810 |
| (within baseline portfolio) LINK ↔ DOT | 0.726 |
| (within baseline portfolio) ETH ↔ DOT | 0.714 |

**XLM is the lowest-correlation candidate found so far.** Lowest pair with BTC is 0.47 — a genuine diversifier. All other portfolio members correlate 0.57–0.81 with BTC.

This is the core exploitation case: adding a symbol with `<0.5` correlation to BTC mechanically reduces portfolio variance even if its standalone Sharpe matches peers.

## Phase 4 — Data Filtering (IS only)

No filter changes. Standard cooldown=2, vol_targeting enabled with target 0.3.

## Phase 5 — Risk Mitigation Design

XLM inherits the same R1+R2 risk stack LTC/DOT use:

- **R1 (consecutive-SL cooldown)**: `K=3, C=27` — pause XLM for 27 bars after 3 consecutive stop-losses.
- **R2 (drawdown scaling)**: `trigger=7%, anchor=15%, floor=0.33` — same schedule that stabilized DOT in iter 176.

This is conservative: if R1+R2 are over-aggressive for XLM they'll simply remove trades, never add risk. If XLM's 2022 exposure materializes as consecutive SLs (as ATOM's did), R1 will damp the bleed.

## Hypothesis

Adding XLM to the portfolio with R1+R2 active:

1. Survives `yearly_pnl_check` (year-1 PnL ≥ −30%, year-2 cumulative PnL ≥ 0) because R1+R2 tame 2022 as they did for DOT.
2. Produces OOS Sharpe ≥ 1.0 standalone (Gate 3) given XLM's vol profile matches passing-grade peers.
3. **Pooled into v0.176**, improves portfolio Sharpe via correlation-driven variance reduction — even if XLM's raw Sharpe is merely OK.

## Decision Rules

- **MERGE** iff pooled portfolio: IS Sharpe ≥ 1.2, OOS Sharpe ≥ 1.0, **MaxDD ≤ 30%**, XLM standalone has ≥ 20 OOS trades, no single symbol > 60% of OOS PnL (diversification exception allowed).
- **NO-MERGE** otherwise.

## Commit plan

- `docs(iter-183): research brief`
- `feat(iter-183): XLM screening runner`
- `docs(iter-183): engineering report` — after backtest
- `docs(iter-183): diary entry` — final commit
