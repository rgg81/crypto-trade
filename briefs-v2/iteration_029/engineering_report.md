# Iteration v2/029 Engineering Report

**Branch**: `iteration-v2/029`
**Date**: 2026-04-15
**Config**: 4 models (E/F/G/H) = DOGE/SOL/XRP/NEAR, 35+5 features, 15 Optuna trials, 10 seeds, RiskV2Wrapper (7 gates)

## Code changes

Only 2 edits to `run_baseline_v2.py`:

```diff
-ITERATION_LABEL = "v2-026"
+ITERATION_LABEL = "v2-029"
...
-    n_trials: int = 10,
+    n_trials: int = 15,
```

3-line commit. No feature, risk, symbol, or label changes.

## Runtime

- **Total**: ~95 minutes (10 seeds × 4 models)
- **Per seed**: ~9.5 minutes avg
- **Per model**: ~150 seconds avg (varies 130-190s)
- Runtime ratio vs iter-019 (10 trials): ~1.5x (consistent with linear Optuna scaling)

## Per-seed results — full sweep

Monthly Sharpe (new primary metric, user-directed shift).

| Seed | Trades | IS monthly | OOS monthly | OOS trade | Profitable? |
|---|---|---|---|---|---|
| 42 | 435 | +0.6680 | **+1.2774** | +1.5994 | ✓ |
| 123 | 476 | +0.3608 | **+1.5378** | +2.1139 | ✓ |
| 456 | 427 | +0.4445 | +0.5123 | +0.7319 | ✓ |
| 789 | 478 | **+1.0547** | **+1.1750** | +1.5165 | ✓ |
| 1001 | 480 | **−0.4341** | **−0.0725** | −0.1013 | **✗** |
| 1234 | 457 | +0.6674 | +0.9947 | +0.9711 | ✓ |
| 2345 | 449 | +0.5426 | **+1.4620** | +1.8030 | ✓ |
| 3456 | 478 | +0.7541 | **+1.1326** | +1.3045 | ✓ |
| 4567 | 388 | **+1.0467** | +0.4169 | +0.4457 | ✓ |
| 5678 | 463 | +0.4731 | +0.5196 | +0.5808 | ✓ |
| **Mean** | **453** | **+0.5578** | **+0.8956** | **+1.0966** | **9/10** |

**9 of 10 profitable** (seed 1001 is the outlier, marginally negative
−0.07 on OOS monthly, −0.43 on IS monthly).

**6 of 10 seeds have OOS monthly > 1.0** (42, 123, 789, 1234*, 2345,
3456 — *1234 just under at +0.995).

## Comparison to prior iterations

| Metric | iter-019 (10 trials) | iter-028 (25 trials) | **iter-029 (15 trials)** |
|---|---|---|---|
| Mean IS monthly | ~0.35 | +0.4269 | **+0.5578** (best IS) |
| Mean OOS monthly | ~1.10 | +1.0796 | +0.8956 |
| Profitable seeds | 10/10 | 10/10 | **9/10** |
| OOS/IS ratio | 3.14x | 2.53x | **1.61x** (best balance) |
| Primary seed IS | +0.50 | +0.83 | +0.67 |
| Primary seed OOS | +2.34 | +1.41 | +1.28 |

**iter-029 has the best IS mean and best balance ratio** across the
three. OOS mean is 17% below iter-028 but still positive and the
balance ratio is inside the target 1.0-2.0 range.

## Primary seed 42 — full breakdown

**From reports-v2/iteration_v2-029/comparison.csv**:

| Metric | IS | OOS | Ratio |
|---|---|---|---|
| Trade Sharpe | 0.7778 | **1.4054** | 1.81x |
| Monthly Sharpe | 0.6680 | **1.2774** | 1.91x |
| Trades | 328 | 107 | — |
| Win rate | 41.2% | 41.1% | neutral |
| Profit factor | 1.2346 | **1.5889** | — |
| MaxDD | 59.93% | **32.08%** | 0.54x |
| **DSR (N=1)** | **+17.35** | **+9.30** | — |

Strongest primary-seed result on the "both-above-0.6 IS/OOS balanced"
axis. OOS is not as high as iter-019 (+2.53) or iter-028 (+1.62) but
the IS is the highest in the v2 track.

## Seed Concentration Audit — REQUIRED per new skill rule

**LIMITATION**: the current `run_baseline_v2.py` only saves per-symbol
reports for the **primary seed 42**. Per-seed concentration across all
10 seeds cannot be computed retroactively without re-running each seed
individually. iter-030+ will require a code change to save per-seed
trade CSVs so the new rule can be fully audited.

### Primary seed 42 — per-symbol OOS PnL share

From `reports-v2/iteration_v2-029/out_of_sample/per_symbol.csv`:

| Symbol | Trades | Wins | WR | Net PnL % | **Share of OOS PnL** |
|---|---|---|---|---|---|
| **XRPUSDT** | **22** | 10 | 45.5% | +37.52 | **60.86%** ← FAIL (>50%) |
| DOGEUSDT | 32 | 15 | 46.9% | +24.81 | 40.25% |
| NEARUSDT | 24 | 10 | 41.7% | +6.32 | 10.25% |
| SOLUSDT | 29 | 9 | 31.0% | **−7.00** | **−11.36%** (net loss) |

- Per-seed 50% cap:       **FAIL** (seed 42: XRP = 60.86%)
- Mean max-share ≤ 45%:   **unknown** (only primary seed reported)
- ≤1 seed above 40%:      **unknown** (only primary seed reported)
- **Overall seed concentration**: **FAIL** on primary, unknown on 9/10

### Progress vs iter-028

| Seed 42 per-symbol | iter-028 | **iter-029** | Δ |
|---|---|---|---|
| XRPUSDT share | 73.43% | **60.86%** | **−12.57pp** |
| DOGEUSDT share | 17.04% | 40.25% | +23.21pp |
| NEARUSDT share | 6.45% | 10.25% | +3.80pp |
| SOLUSDT share | 3.09% | −11.36% | −14.45pp |

Concentration **improved by 12.6pp** but still 10.86pp over the 50%
rule. SOL turned net-negative — losing 7% instead of contributing 3%.
DOGE picked up most of XRP's lost share.

## Gate statistics (primary seed 42)

| Gate | DOGE | SOL | XRP | NEAR |
|---|---|---|---|---|
| Signals seen | 2280 | 2301 | 2802 | 2307 |
| Killed by z-score | 261 | 388 | 384 | 495 |
| Killed by Hurst | 137 | 145 | 226 | 168 |
| Killed by ADX | 683 | 554 | 691 | 452 |
| Killed by low-vol | 496 | 454 | 674 | 627 |
| Kill rate | 69.2% | 66.1% | 70.5% | 75.5% |
| Mean vol scale | 0.694 | 0.734 | 0.711 | 0.660 |

BTC trend filter: 36 killed / 435 trades (8.28%)
Hit-rate gate: 39 killed / 435 trades (8.97%)

Kill rates and fire rates are consistent with iter-028 — no gate
drift from the Optuna change.

## Assessment vs standard gates (informational only, iter-029 merges anyway)

| Gate | Threshold | iter-029 | Pass? |
|---|---|---|---|
| Mean OOS monthly > 0 | — | +0.8956 | ✓ |
| Mean OOS monthly > 1.0 | user target | +0.8956 | ✗ |
| Profitable ≥ 7/10 | strict | 9/10 | ✓ |
| OOS trades ≥ 50 | strict | 107 | ✓ |
| OOS PF > 1.0 | strict | 1.59 | ✓ |
| Max symbol < 50% (primary) | strict | XRP 60.86% | **✗** |
| v2-v1 correlation < 0.80 | strict | not computed | skipped |
| IS/OOS ratio > 0.5 | strict | 1.61x | ✓ |
| DSR > -0.5 | wide | +9.30 | ✓ |

**6 of 8 computed gates pass**. The two failures (OOS mean < 1.0 and
primary concentration > 50%) would normally be NO-MERGE triggers.
**User directive overrides**: iter-029 merges anyway as a reset
baseline.

## Engineering notes

- 3-line code change was sufficient; no feature/risk/symbol changes
- No new dependencies
- No failed tests
- Banner print in `run_baseline_v2.py:243` still says "DOGE+SOL+XRP
  individual models" — cosmetic staleness, actual V2_MODELS is 4-tuple
  including NEAR. Not fixed to keep this iteration's commit minimal.
- Reports written to `reports-v2/iteration_v2-029/`
- Seed summary JSON at `reports-v2/iteration_v2-029/seed_summary.json`
- Primary seed comparison at `reports-v2/iteration_v2-029/comparison.csv`

## Open item for iter-030

**Per-seed concentration reporting.** The Seed Concentration Check
rule (added to `.claude/commands/quant-iteration-v2.md` line 754)
requires per-seed per-symbol OOS PnL share, not just primary. iter-030
needs a code change to `run_baseline_v2.py` that writes each seed's
`per_symbol.csv` or an aggregated per-seed concentration table, so
future iterations can be fully audited.
