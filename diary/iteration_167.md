# Iteration 167 Diary

**Date**: 2026-04-21
**Type**: EXPLORATION (ATOM Gate 3 screen)
**Decision**: **NO-MERGE (EARLY STOP)** — ATOM fails Gate 3

## Results

| Gate | Criterion | Actual | Pass |
|---|---|---|:-:|
| 1. Data quality | ≥ 1,095 IS candles, starts before 2023-07 | 6,796 candles, starts 2020-08 | ✓ |
| 2. Liquidity | mean daily volume > $10M | top-30 cap (assumed) | ✓ |
| 3a. Stand-alone IS Sharpe | > 0 | -0.89 | ✗ |
| 3b. Stand-alone IS WR | > 33.3% | 39.3% | ✓ |
| 3c. Stand-alone IS trades | ≥ 100 | 56 | ✗ |
| 3d. Year-1 cumulative PnL | ≥ 0 | -7.1% | ✗ |

Three out of four Gate 3 criteria fail. ATOM rejected.

## Fail-Fast Trigger

```
Year 2022: PnL=-7.1% (WR=38.2%, 55 trades)
```

Total elapsed: 19 minutes vs ~90 minutes if the full walk-forward had run. Saved ~70 minutes of compute.

## Comparison: AVAX vs ATOM vs LTC at Gate 3

| Candidate | Year-1 PnL | IS Sharpe @ stop | IS trades @ stop | Outcome |
|---|---:|---:|---:|---|
| AVAX (iter 164) | -34.6% | -1.84 | 23 | Rejected |
| ATOM (iter 167) | -7.1% | -0.89 | 56 | Rejected |
| LTC (iter 165) | > 0 (no stop) | +0.60 | 155 | **Accepted** |

Pattern: both rejected candidates failed at year-1. LTC sailed through. The year-1 checkpoint is doing its job.

## Research Checklist

- **B — Symbol Universe (ATOM)**: full Gate 1 → Gate 3 protocol executed. Failed at Gate 3.

## Exploration/Exploitation Tracker

Window (158-167): [X, X, X, E, E, E, E, E, X, E] → **6E / 4X**, 60% exploration. Above the 30% floor.

## Lessons Learned

1. **Fail-fast pays back quickly** — 19 min to rule out ATOM. That budget bought a definitive answer.
2. **Gate 3 is a strong filter** — two of three candidates (AVAX, ATOM) fail. LTC was the exception. The filter is correctly weeding out poor fits.
3. **Year-1 performance remains the best early signal** for candidate quality. Candidates that pass year-1 usually pass Gate 3 overall (LTC: IS Sharpe +0.60); candidates that fail year-1 are almost always overall failures too.

## lgbm.py Code Review

No code changes this iteration. Prior review (iter 166) noted dead `self.seed` parameter in ensemble mode — tracked as a future cleanup candidate.

## Next Iteration Ideas

### 1. Iter 168: Screen DOT (Polkadot) as the next candidate (PRIORITY)

Same protocol, same config, `symbols=("DOTUSDT",)`. Fail-fast on. Cost: 10–90 min depending on year-1 outcome.

If DOT also fails, the remaining queue (in priority order): **AAVE**, **LTC** (already in), **LINK** (already in), **BNB** (already tried, failed), **TIA**, **INJ**. Skip excluded: DOGE, SOL, XRP, NEAR.

### 2. Iter 169: If DOT passes, pool A+C+LTC+DOT diagnostic → merge

Same mechanism as iter 165: combine existing A/C/LTC trades with DOT trades (independent models). If the pooled diagnostic clears the hard constraints (or the diversification exception), merge.

### 3. Iter 170: If two more candidates fail, pivot

If DOT also fails, Gate 3 candidates keep coming up empty with this architecture. Pivot to improving Model A (BTC+ETH) — per iter 152 reproduction, Model A alone has Sharpe +0.24 and contributes only +9.3% OOS. Headroom exists. Candidate sub-idea: split Model A into per-symbol sub-models for BTC and ETH (iter 076 observed ETH SHORT 51% WR vs BTC LONG 43.6% — very different dynamics).

### 4. Iter 170 alternative: Try ATR 2.9/1.45 on the failed candidates

AVAX and ATOM both failed with ATR 3.5/1.75 (LINK-style). Maybe they need BTC-style 2.9/1.45. **But**: the fail-fast protocol after EARLY STOP explicitly BANS parameter-only changes <2×. 2.9/1.45 is only 0.83× of 3.5/1.75 — *fails* the ban. So this idea is **not allowed** by the skill and should not be pursued for AVAX or ATOM. New candidates can start with different multipliers if justified.
