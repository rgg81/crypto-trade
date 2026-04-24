# Iteration 164 Diary

**Date**: 2026-04-21
**Type**: EXPLORATION (symbol universe expansion — AVAX Gate 3 screen)
**Decision**: **NO-MERGE (EARLY STOP)** — AVAX fails Gate 3 at year-1 checkpoint

## Results

| Metric | Baseline v0.152 | Iter 164 (partial, IS-only) | Gate 3 pass? |
|---|---:|---:|:-:|
| Total trades | 648 IS / 223 OOS | 23 (IS only, aborted) | no (need 100+) |
| IS Sharpe | +1.07 | **-1.84** | **no** |
| IS WR | 42.9% | 39.1% | borderline |
| IS Profit Factor | 1.26 | 0.59 | no |
| IS Net PnL | +195.7% | -14.87% | no |
| Year-1 PnL check | — | **-34.6%** | **FAIL** |

## Fail-Fast Trigger

The year-1 checkpoint aborted the walk-forward after calendar year 2022:

```
Year 2022: PnL=-34.6% (WR=36.4%, 22 trades)
```

Total wall-clock: 9 minutes (vs. expected 90 min without the fail-fast). This is exactly the use case the checkpoint was built for — a clearly broken configuration caught in 10% of the usual runtime.

## Root Cause Hypothesis

AVAX's volatility regime differs from LINK/BNB enough that ATR multipliers 3.5 × NATR TP / 1.75 × NATR SL produce an execution plan the model cannot predict profitably under baseline config. AVAX NATR in early IS periods was substantially higher than LINK's, pushing TP/SL barriers so wide that most trades hit SL or timed out. The 36.4% WR with a 2:1 RR implies expected value = 0.364 × 2 − 0.636 × 1 = 0.092, but fee drag (0.1% per side) and timeout losses pushed the realized EV negative.

## Research Checklist (Exploration iteration)

- **B — Symbol Universe (AVAX candidate)**: performed. AVAX passed Gates 1 (data quality, 6109 candles from 2020-09) and 2 (assumed liquidity, top-20 cap). Failed Gate 3 (stand-alone profitability) decisively. No need to proceed to Gates 4 and 5.

## Exploration/Exploitation Tracker

Last 10 iterations (155-164): [E, X, X, X, X, X, E, E, E, E]
Exploration rate: 5/10 = **50% ✓** (well above the 30% floor)

## Lessons Learned

1. **Fail-fast works.** 9 minutes of compute gave an unambiguous NO-MERGE, vs. the 90 minutes it would have taken to produce the same conclusion without the checkpoint. Every candidate screen from now on runs with `yearly_pnl_check=True` by default.

2. **One-size-fits-all ATR multipliers don't generalize across L1s.** BTC/ETH use 2.9/1.45; LINK/BNB use 3.5/1.75. AVAX probably needs its own calibration — but that crosses into "per-symbol tuning" which is EXPLOITATION and would normally come AFTER the symbol is confirmed to carry signal, not as a screen.

3. **Cheap screens beat full iterations.** Running just AVAX with fail-fast (9 min) is orders of magnitude cheaper than pooling A+C+AVAX and discovering the problem post-hoc (~4 hours).

## lgbm.py Code Review

Skipped — no issues surfaced in a 9-minute partial run, and no code changes were introduced in this iteration. Full review deferred to the next iteration if it completes.

## Next Iteration Ideas

### 1. Iter 165: Screen the next candidate — **LTC (Litecoin)** — same protocol (PRIORITY)

LTC has ~13 years of price history, top-20 cap, notably lower volatility than AVAX, and meaningfully different macro/narrative cycle from BTC/ETH/LINK. Run the identical Gate 3 runner with `symbols=("LTCUSDT",)` and `yearly_pnl_check=True`. Cost: ~10 min if it fails, ~90 min if it passes.

### 2. Iter 165 (parallel idea): Screen **ATOM (Cosmos)**

Similar profile to LTC: established L1, mid-to-large cap, different sector from BTC/ETH. If LTC fails, queue ATOM.

### 3. Iter 165 alternative: Screen **DOT (Polkadot)**

Third fallback. Different architecture, meaningful history.

User exclusion list (still in effect): DOGE, SOL, XRP, NEAR.

### 4. If two-to-three screens all fail: pivot to architecture — accept A+C as the baseline and work on improving Model A

If none of LTC / ATOM / DOT clears Gate 3, the next move is to accept that no third model is currently available and focus on **improving Model A (BTC+ETH)**. Model A contributes only +0.24 OOS Sharpe alone; there's headroom. Candidate sub-ideas: ATR multiplier sweep for A (2.0, 2.5, 2.9 current, 3.5), colsample_bytree implicit pruning, or per-symbol sub-models for BTC and ETH separately (inside Model A).

### 5. Do NOT retry AVAX with different ATR multipliers

Per the fail-fast protocol ("after early stop, parameter-only changes are banned"), retrying AVAX with e.g. ATR 2.5/1.25 would be a parameter tweak less than 2×, which the skill explicitly forbids after an early stop. If AVAX is to be revisited, it must be as a structural change — e.g. per-symbol model with distinct labeling paradigm, not just tighter barriers.

## Appendix — Gate 3 scorecard for AVAX

| Gate | Criterion | Actual | Pass |
|---|---|---|:-:|
| 1. Data quality | ≥ 1,095 IS candles, starts before 2023-07 | 6,109 candles, starts 2020-09 | ✓ |
| 2. Liquidity | mean daily volume > $10M | top-20 cap (assumed) | ✓ |
| 3a. Stand-alone IS Sharpe | > 0 | -1.84 | ✗ |
| 3b. Stand-alone IS WR | > 33.3% | 39.1% | ✓ |
| 3c. Stand-alone IS trades | ≥ 100 | 23 | ✗ |
| 3d. Year-1 cumulative PnL | ≥ 0 | -34.6% | ✗ |

Gate 3 requires ALL criteria to pass. Three out of four fail → AVAX is rejected as a Model D' replacement candidate.
