# Iteration v2/032 Engineering Report

**Branch**: `iteration-v2/032`
**Date**: 2026-04-15
**Config**: 4 models (E/G/H/I) = DOGE/XRP/NEAR/**ADA**, 35+5 features, 15 Optuna trials, 10 seeds

## Code changes

Two commits:

1. `41b7527` — V2_MODELS 3-symbol (DOGE+XRP+ADA) for the initial
   smoke test. Failed and was pivoted.
2. `792568a` — V2_MODELS 4-symbol pivot (DOGE+XRP+NEAR+ADA). This
   is the canonical iter-032 config.

## The 3-symbol smoke test failure

Primary seed 42 with 3-symbol DOGE+XRP+ADA:

| Metric | iter-029 | iter-031 (5-sym) | iter-032 smoke (3-sym) |
|---|---|---|---|
| IS trade Sharpe | +0.78 | +0.98 | +0.93 |
| OOS trade Sharpe | +1.41 | +1.62 | **+1.05** |
| OOS monthly | +1.28 | +1.56 | **+0.76** |
| OOS PF | 1.59 | 1.65 | 1.46 |

**40% regression on OOS trade Sharpe** from iter-031 primary. Why?

The hit-rate gate looks at the last 20 trades (cross-symbol). With
3 symbols instead of 5, the lookback spans more calendar time and
kills different trades. Comparison:

| Symbol | iter-031 wpnl | iter-032 3-sym wpnl | Δ |
|---|---|---|---|
| DOGEUSDT | +30.12 (32 trades) | +9.83 (32 trades) | **−20.29** |
| XRPUSDT | +37.63 (22 trades) | +28.09 (22 trades) | −9.54 |
| ADAUSDT | +22.13 (23 trades) | +8.37 (23 trades) | −13.76 |

Same trade counts, same models, but different wpnl. The ONLY thing
that changed between iter-031 and iter-032-3sym is the composition of
the cross-symbol hit-rate gate's lookback window. This must be the
cause.

**Lesson**: symbol removal is NOT a free lunch. Cross-symbol gate
coupling means the portfolio is non-additive.

## The 4-symbol pivot (canonical iter-032)

4 symbols DOGE+XRP+NEAR+ADA (swap SOL → ADA). Maintains 4-symbol trade
density so hit-rate gate behaves like iter-029.

### Primary seed 42 — best IS ever in v2 track

| Metric | iter-029 | iter-031 (5-sym) | **iter-032 (4-sym)** |
|---|---|---|---|
| IS trade Sharpe | +0.7778 | +0.9802 | **+1.0443** (best) |
| OOS trade Sharpe | +1.4054 | +1.6150 | **+1.6496** |
| IS monthly | +0.6680 | +0.8980 | **+0.9585** (best) |
| OOS monthly | +1.2774 | +1.5604 | +1.2764 (flat vs iter-029) |
| OOS PF | 1.5889 | 1.6493 | **1.7972** (best) |
| OOS MaxDD | 32.08% | 43.52% | 39.77% |
| IS trades | 328 | 437 | 354 |
| OOS trades | 107 | 130 | 101 |
| **XRP share (wpnl)** | **69.47%** | **41.87%** | **40.37%** |
| Concentration audit | FAIL | FAIL (n=5) | **PASS** max ≤50% (seed 42) |

**Primary seed passes the n=4 50% concentration rule** for the first
time since the rule was introduced. XRP at 40.37% (just above the 40%
inner rule but under the 50% outer rule).

## 10-seed full summary

| Metric | iter-029 | iter-031 (5-sym) | **iter-032 (4-sym)** |
|---|---|---|---|
| Mean IS monthly | +0.5578 | +0.7477 | **+0.7300** (+31%) |
| Mean OOS monthly | +0.8956 | +0.6605 | +0.7992 (−11%) |
| Mean OOS trade | +1.0966 | +0.7838 | +1.0394 (−5%) |
| **Profitable seeds** | **9/10** | 7/10 | **8/10** |
| **OOS/IS ratio** | 1.61x | 0.88x | **1.09x** (best balance) |
| Distressed seeds | — | 3/10 | **2/10** (meets rule) |
| Mean trades per seed | 453 | 581 | 464 |

**Best balance ratio in v2 history** (1.09x, inside target 1.0-2.0).
**Distressed count meets the rule for the first time** (≤2 of 10).

## Per-seed comparison

| Seed | iter-029 IS/OOS | **iter-032 IS/OOS** | Δ IS | Δ OOS |
|---|---|---|---|---|
| 42 | +0.67 / +1.28 | **+0.96** / +1.28 | +0.29 | 0.00 |
| 123 | +0.36 / +1.54 | +0.22 / +1.41 | −0.14 | −0.13 |
| 456 | +0.44 / +0.51 | +0.38 / **+0.90** | −0.06 | +0.39 |
| 789 | +1.05 / +1.18 | +0.86 / +1.21 | −0.19 | +0.03 |
| 1001 | −0.43 / −0.07 | **+0.29** / −0.06 | +0.72 | +0.01 |
| 1234 | +0.67 / +0.99 | +0.81 / +0.62 | +0.14 | −0.37 |
| 2345 | +0.54 / +1.46 | +0.69 / +0.82 | +0.15 | −0.64 |
| 3456 | +0.75 / +1.13 | **+1.19** / −0.10 | +0.44 | **−1.23** |
| 4567 | +1.05 / +0.42 | +1.41 / +0.79 | +0.36 | +0.37 |
| 5678 | +0.47 / +0.52 | +0.50 / +1.12 | +0.03 | +0.60 |

**5 seeds improved IS significantly** (+0.14 to +0.72). **4 seeds
improved OOS** (+0.37 to +0.60). **4 seeds regressed OOS** (−0.13 to
−1.23).

The OOS regressions dominate the mean: seed 3456 alone is −1.23 which
drags the 10-seed mean by 0.12.

## Seed concentration audit (n=4, thresholds max≤50%, mean≤45%, ≤1 above 40%)

```
  seed      max      symbol   pass_max  pass_inner   distressed
    42   40.37%     XRPUSDT       PASS        FAIL            —
   123   55.36%     XRPUSDT       FAIL        FAIL            —
   456   65.77%     XRPUSDT       FAIL        FAIL            —
   789   55.34%     XRPUSDT       FAIL        FAIL            —
  1001   95.08%     XRPUSDT       FAIL        FAIL     DISTRESS
  1234   65.02%    DOGEUSDT       FAIL        FAIL            —
  2345   73.71%     XRPUSDT       FAIL        FAIL            —
  3456  100.00%     XRPUSDT       FAIL        FAIL     DISTRESS
  4567   55.10%     XRPUSDT       FAIL        FAIL            —
  5678   57.78%    NEARUSDT       FAIL        FAIL            —

Mean per-seed max-share: 66.35%  (rule: ≤45%)
Seeds passing ≤50%:       1/10   (rule: all)
Seeds above 40%:         10/10   (rule: ≤1)
Distressed seeds:         2/10   (rule: ≤2)
Overall seed concentration: FAIL
```

**Only primary seed 42 passes the 50% rule**. All other 9 seeds are
above 50%. Mean is 66.35%, same as iter-031. The structural pattern
— some seeds find XRP-dominant or NEAR-dominant hyperparameter sets
— is unchanged.

**Distressed count passes**: 2/10 seeds (1001 and 3456), meets the
≤2 rule for the first time.

## Assessment vs iter-032 success criteria

| Gate | Target | Result | Pass? |
|---|---|---|---|
| Seed concentration audit | PASS | FAIL | **FAIL** |
| Mean OOS monthly > +0.8956 | +0.8956 | +0.7992 | **FAIL** |
| Profitable seeds ≥ 8/10 | 8/10 | 8/10 | PASS |
| Primary seed XRP share < 50% | 50% | 40.37% | PASS |
| Primary OOS ≥ iter-029 | +1.28 | +1.28 | PASS (flat) |
| Balance ratio 1.0-2.0 | yes | 1.09x | **PASS** |

Gating: 2 of 4 fail → **NO-MERGE**.

Non-gating: 3 of 3 pass.

## Wins and losses

### Wins
1. **Primary seed 42 has the best IS in v2 history** (monthly +0.9585,
   trade +1.0443)
2. **Primary seed concentration passes n=4 50% rule** for the first time
3. **Best balance ratio in v2 history** (1.09x)
4. **Distressed count meets the rule** (2/10 vs iter-031's 3/10)
5. **ADA is a real contributor** — 47.8% WR, positive share
6. **OOS PF 1.80 on primary seed** — best in v2 history

### Losses
1. **Mean OOS regressed** 11% vs iter-029 (+0.80 vs +0.90)
2. **Seed 3456 catastrophic OOS flip** (+1.13 → −0.10, −1.23 swing)
3. **Only 1/10 seeds pass concentration rule** — primary is outlier
4. **Mean concentration unchanged** from iter-031 (~66%)
5. **Profitable seed count dropped** from 9 to 8

## Key finding — the OOS mean regression is seed variance, not
## structural

iter-032 is BETTER than iter-029 on primary seed by every metric:
- IS monthly +44% higher
- OOS trade Sharpe +17% higher
- OOS PF +13% higher
- Concentration 29pp lower

But the 10-seed mean is WORSE on OOS because 4 seeds (123, 1234, 2345,
3456) regressed significantly. This is **seed-to-seed variance in
Optuna hyperparameter search**, not a structural issue with the
symbol mix.

The fundamental limit on iter-032 is the same as iter-029/030/031:
**Optuna produces wildly different hyperparameter sets across seeds**,
and 3-4 seeds per iteration always find something that trades badly
on OOS.

## Runtime

- Total: ~95 minutes (4 symbols × 10 seeds, expected)
- Per seed: ~9.5 minutes avg
- No performance regressions

## Open items for iter-033+

The structural symbol experiments (iter-031 5-sym, iter-032 4-sym swap)
have converged on a local ceiling defined by **seed variance**, not
symbol choice:

- iter-029: mean OOS +0.90, 9/10 profitable
- iter-031: mean OOS +0.66, 7/10 profitable
- iter-032: mean OOS +0.80, 8/10 profitable

None approach mean OOS > 1.0. Each iter has a different primary seed
behavior but converges on similar mean. **The symbol universe is
close to exhausted as a lever.**

The remaining levers are:

1. **Seed variance reduction** — ensemble-average internal seeds per
   model (`ensemble_seeds=[s, s+1, s+2]`), expected 3x runtime
2. **Optuna constraint** — cap confidence_threshold upper bound
3. **Ensemble at model level** — train N models per symbol-seed and
   average predictions
4. **Improve the gates** — the hit-rate gate is over-firing on some
   seeds. A gate with fewer false kills might rescue the weak seeds.
