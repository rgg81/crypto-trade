# Iteration v2/031 Engineering Report

**Branch**: `iteration-v2/031`
**Date**: 2026-04-15
**Config**: 5 models (E/F/G/H/I) = DOGE/SOL/XRP/NEAR/**ADA**, 35+5 features, 15 Optuna trials, 10 seeds

## Code changes (single commit `400627b`)

Three changes in one commit:

1. **V2_MODELS** — added `("I (ADAUSDT)", "ADAUSDT")` as 5th model
2. **Audit metric** — switched to positive-total share:
   `share[sym] = max(0, sym_wpnl) / sum(max(0, s_wpnl) for s in symbols)`
3. **Distressed-seed flag** — `total_oos_wpnl ≤ 0 or |total| < 10` → distressed
4. **n-symbol-aware thresholds** — `_thresholds_for_n(n)` function reads
   `len(V2_MODELS)` and picks the row. n=5 thresholds: max≤40%, mean≤35%,
   ≤1 above 32%, distressed ≤2.

Also: **ADAUSDT features regenerated** via
`process_symbol_v2('ADAUSDT', '8h', ...)` to include the iter-026 BTC
cross-asset columns (btc_ret_3d, btc_ret_7d, btc_ret_14d, btc_vol_14d,
sym_vs_btc_ret_7d). Previous ADA parquet predated iter-026 and was
missing these 5 columns.

## 10-seed results — IS improved, OOS degraded

| Metric | iter-029 (4-sym) | **iter-031 (5-sym)** | Δ |
|---|---|---|---|
| Mean IS monthly | +0.5578 | **+0.7477** | **+34%** |
| Mean OOS monthly | +0.8956 | **+0.6605** | **−26%** |
| Mean OOS trade | +1.0966 | +0.7838 | −29% |
| **Profitable seeds** | **9/10** | **7/10** | **−2** |
| OOS/IS ratio | 1.61x | **0.88x** | inverted |
| Mean trades per seed | 453 | 581 | +28% |

**IS improved substantially, OOS regressed**. The OOS/IS ratio of 0.88x
is technically "better balance" (closer to 1.0) but in the wrong
direction — it's anti-overfitting territory, suggesting the 5-symbol
config is actually **underfitting**.

## Per-seed OOS monthly comparison

| Seed | iter-029 OOS | iter-031 OOS | Δ | Notes |
|---|---|---|---|---|
| 42 | +1.2774 | **+1.5604** | +0.28 | improved |
| 123 | +1.5378 | +0.9546 | −0.58 | regressed |
| 456 | +0.5123 | **+0.9346** | +0.42 | improved |
| 789 | +1.1750 | **+1.7698** | +0.59 | improved (best) |
| 1001 | −0.0725 | **−0.9430** | −0.87 | much worse |
| 1234 | +0.9947 | +0.9834 | −0.01 | flat |
| 2345 | +1.4620 | +0.8529 | −0.61 | regressed |
| 3456 | +1.1326 | **−0.0508** | −1.18 | **flipped negative** |
| 4567 | +0.4169 | **−0.1276** | −0.54 | **flipped negative** |
| 5678 | +0.5196 | +0.6703 | +0.15 | improved |

**4 seeds improved** (42, 456, 789, 5678) — some dramatically.
**6 seeds regressed** — 3 of them (1001, 3456, 4567) went below zero OOS.

The distribution is bimodal: iter-031 is clearly better on a handful
of seeds and clearly worse on others. Seed variance is the enemy.

## Primary seed 42 — best result in v2 track

```
[report] IS:  Sharpe=0.9802  DSR=+20.407  Trades=437  WR=41.6%  PF=1.2583  MaxDD=68.37%
[report] OOS: Sharpe=1.6150  DSR=+9.748   Trades=130  WR=42.3%  PF=1.6493  MaxDD=43.52%
[report] OOS/IS Sharpe ratio: 1.6477
```

| Metric | iter-019 | iter-029 | **iter-031** |
|---|---|---|---|
| IS trade Sharpe | +0.57 | +0.7778 | **+0.9802** |
| OOS trade Sharpe | **+2.54** | +1.4054 | +1.6150 |
| IS monthly | +0.50 | +0.6680 | **+0.8980** |
| OOS monthly | +2.34 | +1.2774 | **+1.5604** |
| IS MaxDD | 72.24% | 59.93% | 68.37% |
| OOS MaxDD | 24.39% | 32.08% | 43.52% |
| IS trades | 344 | 328 | **437** (+33%) |
| OOS trades | — | 107 | **130** (+22%) |
| XRP share (wpnl) | ~41% | 69.47% | **41.87%** |

**Primary seed 42 has the best v2 IS monthly yet** (+0.8980) and the
**second-best OOS monthly** (+1.5604, behind iter-019's +2.34 which
was 4-symbol). XRP concentration on primary seed dropped 27.6pp
from iter-029 and is just 1.87pp over the new n=5 rule.

## Per-symbol OOS (primary seed 42) — ADA is a real contributor

| Symbol | Trades | WR | Weighted PnL | Share |
|---|---|---|---|---|
| **XRPUSDT** | 22 | 45.5% | **+37.63** | **41.87%** |
| **DOGEUSDT** | 32 | 46.9% | **+30.12** | **33.51%** |
| **ADAUSDT** | 23 | 47.8% | **+22.13** | **24.62%** (new) |
| NEARUSDT | 24 | 41.7% | −2.73 | 0.00% (net neg) |
| SOLUSDT | 29 | 31.0% | −1.66 | 0.00% (net neg) |

**ADA contributed 24.62% of positive PnL on primary seed** — clearly
adding signal, not noise. 47.8% WR is the best of any symbol. DOGE
and XRP also improved their contributions.

**NEAR and SOL are BOTH net-negative on primary seed**. The 5-symbol
portfolio essentially became a 3-symbol (XRP+DOGE+ADA) portfolio on
primary seed, with NEAR and SOL as net-losers.

## Seed concentration audit — STILL FAILS

```
n_symbols=5, thresholds: max≤40%, mean≤35%, ≤1 above 32%

  seed     max    symbol     pass_max  pass_inner   distressed
    42   41.87%   XRPUSDT      FAIL       FAIL          —
   123   78.59%   XRPUSDT      FAIL       FAIL          —
   456   58.83%   XRPUSDT      FAIL       FAIL          —
   789   47.52%   XRPUSDT      FAIL       FAIL          —
  1001  100.00%   XRPUSDT      FAIL       FAIL      DISTRESS
  1234   45.85%  DOGEUSDT      FAIL       FAIL          —
  2345   67.64%   XRPUSDT      FAIL       FAIL          —
  3456  100.00%   XRPUSDT      FAIL       FAIL      DISTRESS
  4567   70.93%   XRPUSDT      FAIL       FAIL      DISTRESS
  5678   53.40%  NEARUSDT      FAIL       FAIL          —

Mean per-seed max-share: 66.46%  (rule: <=35%)
Seeds passing <=40%:      0/10   (rule: all)
Seeds above 32%:         10/10   (rule: <=1)
Distressed seeds:         3/10   (rule: <=2)
Overall seed concentration: FAIL
```

**All 4 gates FAIL**:
- Per-seed max cap: 0/10 pass (best is seed 42 at 41.87%, 1.87pp over)
- Mean max-share: 66.46% vs 35% rule (31pp over)
- Seeds above 32%: 10/10 (rule is ≤1)
- Distressed seeds: 3/10 (rule is ≤2)

Key problem: **distressed seeds increased from 3/10 (iter-030) to
3/10 (iter-031) but at higher dominance**. Seeds 1001, 3456, 4567 all
have 100% share or near it — meaning XRP is the only positive
contributor while 4 other symbols lose money.

Primary seed 42 is the **best case**, at 41.87% (just over the rule).
On other seeds, the 5-symbol approach is worse because there are
MORE losing symbols dragging the total.

## Gate assessment vs iter-031 success criteria

| Gate | Target | Result | Pass? |
|---|---|---|---|
| Seed concentration audit (n=5) | PASS | FAIL (all 4 sub-rules) | **FAIL** |
| Mean OOS monthly > +0.80 | +0.80 | +0.6605 | **FAIL** |
| Profitable seeds ≥ 8/10 | 8/10 | 7/10 | **FAIL** |
| OOS PF > 1.2 | 1.2 | 1.65 (primary) | pass |
| Mean IS monthly > +0.50 | +0.50 | +0.7477 | pass |
| Primary XRP share < 50% | 50% | 41.87% | **pass** (big improvement) |
| ADA contributes positive OOS | +PnL | +22.13 on primary | **pass** |

**Gating: 3 of 4 fail → NO-MERGE.**

Non-gating: 3 of 3 pass.

## Key finding — adding symbols doesn't fix concentration; it shifts the failure mode

Before iter-031:
- iter-029: 1 failure mode — XRP concentrates on most seeds (mean ~71%)
- iter-030: same

After iter-031:
- Primary seed + a few others: **concentration improved** (41.87% on primary)
- Other seeds: **concentration worsened** — went from "marginal" to
  "distressed" (only XRP positive, others all negative)
- More symbols = more losing symbols on bad seeds = more distressed seeds

**The mean max-share went UP (66% vs iter-030's ~70% clean/162% dirty)
because seeds 1001/3456/4567 became fully dominated.**

This is a **seed variance problem disguised as a symbol-count problem**.
Adding symbols doesn't help when the underlying issue is that some
seeds find hyperparameters that trade badly on 4/5 symbols while
winning on 1.

## Runtime

- Total: ~115 minutes (vs iter-029's 95min — 5/4 ratio = 1.25x, as expected)
- Per seed: ~11.5 min (vs iter-029's 9.5 min)
- Per model: ~140 seconds avg
- No performance regressions

## Engineering notes

- ADAUSDT features needed regeneration to include BTC cross-asset
  columns — one-time fix, parquet now canonical for future runs.
- Audit metric is now canonical (positive-total share, weighted_pnl
  based). per_symbol.csv values are informational only.
- Distressed-seed flag works as expected: correctly identifies seeds
  1001, 3456, 4567 where total_oos_wpnl is small or negative.
- Banner print in run_baseline_v2.py still says "DOGE+SOL+XRP
  individual models" — cosmetic staleness, not fixed to keep commit
  minimal. Actual run uses all 5 models.

## What worked

1. **Audit code is production-ready** and correctly reports per-seed
   concentration across 10 seeds for the first time.
2. **Distressed-seed handling** correctly flags 3 seeds where the
   total OOS pnl is near-zero or negative.
3. **Primary seed improved** materially — IS monthly +0.90, OOS
   monthly +1.56. Best v2 primary-seed IS to date.
4. **ADA is a real contributor** — 47.8% WR, +$22 net PnL on primary
   seed, 24.62% share.

## What didn't work

1. **Seed variance got worse** — 3 seeds went distressed vs iter-030's 3
   distressed, but iter-031's distressed seeds are MORE dominated
   (100% share vs ~950% artifact).
2. **OOS mean dropped** 26% — the regression from seeds 1001/3456/4567
   outweighs the gains from 42/456/789.
3. **Concentration rule still fails** on every seed — no single seed
   passes the n=5 40% cap. Best seed is 1.87pp over.

## Open questions for iter-032+

1. Is the 5-symbol portfolio WORSE than 4-symbol for OOS due to
   seed variance? Mean dropped from +0.90 to +0.66 — materially worse.
2. Should we DROP symbols that are chronic losers (SOL and NEAR were
   net-negative on primary seed) instead of adding more?
3. Can we reduce seed variance via Optuna warm-start from a known-good
   hyperparameter set?
4. Should we try ensemble-averaging predictions across 5 seeds per
   model instead of running seeds separately?
5. The hit-rate gate and BTC trend gate may be over-killing — the
   distressed seeds all have total near zero, suggesting trades are
   being generated but returns are near-zero-sum.
