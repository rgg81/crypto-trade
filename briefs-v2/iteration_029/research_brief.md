# Iteration v2/029 Research Brief

**Type**: EXPLOITATION + BASELINE RESET (user-directed)
**Track**: v2 — seeking balanced IS/OOS monthly Sharpe
**Parent**: iter-v2/028 (NO-MERGE, concentration 73.43%)
**Date**: 2026-04-15
**Researcher**: QR
**Branch**: `iteration-v2/029` on `quant-research`

## Section 0: Data Split

```
OOS_CUTOFF_DATE = 2025-03-24    ← FIXED. NEVER CHANGES.
```

## Motivation — two overlapping directives

### 1. Fix iter-028's concentration failure

iter-v2/028 produced a breakthrough-but-blocked result:
- Mean OOS monthly Sharpe: **+1.0796** — first time above 1.0
- Primary seed 42 IS trade Sharpe: **+1.1280** — first time above 1.0
- Profitable seeds: 10/10
- **Primary seed XRP concentration: 73.43%** (strict rule: ≤50%)

The 25-trial Optuna found highly profitable XRP signals (15 trades
averaging +3.6% per trade on OOS) but over-weighted XRP at the expense
of the other 3 symbols. NEAR and SOL got fewer trades; DOGE stayed
middling.

### 2. User directive (mid-iteration)

After iter-028 was declared NO-MERGE, user said:
> "run again the baseline with 10 seeds, we need to avoid seed concentration"

Then:
> "from now on, update the skill v2 with this info — before we make
> it baseline we need to ensure no seed concentration. It's a big risk."

Then:
> "and the result of this iteration will be the baseline from now on.
> No matter if it is worst"

This makes iter-029 a **baseline reset** — a one-time exception to
the new concentration rule, to give future iterations a clean reference
point instead of continued exploration.

## Hypothesis

**15 Optuna trials (middle ground between iter-019's 10 and iter-028's
25) will preserve most of the OOS mean improvement while reducing the
selectivity that caused iter-028's 73% concentration.**

Reasoning: more Optuna trials → hyperparameter sets more selective →
fewer "marginal" trades kept → trades cluster on the strongest signals
(XRP on iter-028). 15 trials should find better-than-10 hyperparameter
sets without over-selecting.

Expected:
- Mean OOS monthly Sharpe: between iter-019 (+0.69 BTC-features mean)
  and iter-028 (+1.08) — call it +0.85-1.00
- Concentration: 55-65% (below iter-028's 73% but possibly still above
  50% strict rule)
- IS monthly: better than iter-028 (+0.43) — likely +0.50-0.60

## Changes vs iter-028

| Parameter | iter-028 | **iter-029** |
|---|---|---|
| `n_trials` (default) | 25 | **15** |
| Features | 40 (35 v2 + 5 BTC cross) | 40 (unchanged) |
| Symbols | E=DOGE, F=SOL, G=XRP, H=NEAR | unchanged |
| Risk gates | 7 active | unchanged |
| Seeds | 10 | 10 |
| Training window | 24mo | 24mo |

**Only the Optuna trial count changed.** This is a pure hyperparameter
depth tuning iteration — no feature, symbol, or risk-layer changes.

## Section 6: Risk Management Design

No new primitives; 7 active gates from iter-019 retained:

1. Vol-adjusted position sizing via `atr_pct_rank_200`
2. ADX gate (threshold 20)
3. Hurst regime check (train 5/95 percentile band)
4. Feature z-score OOD alert (|z|>3 any feature)
5. Low-vol filter (`atr_pct_rank_200 >= 0.33`)
6. Hit-rate feedback gate (window=20, SL threshold=0.65) — OOS only
7. BTC trend-alignment filter (14d ±20%) — full period

### Pre-registered failure-mode prediction

The most likely failure mode for iter-029 is **XRP still concentrates
above 50%**. The 25→15 reduction may move concentration from 73% to
~60-65%, which remains over the strict rule. Secondary failure: if
Optuna finds less selective hyperparameters, it might also generate
more marginal trades that hurt IS mean instead of helping it.

**If failure-1 happens AND the user directive to merge unconditionally
stands, iter-029 merges anyway** and becomes a reference point for
iter-030 onwards, which will be held to the new concentration rule
strictly.

## Success criteria

Per user directive: **none gate the merge**. iter-029 is a forced
reset. The diary will still report the full seed-concentration audit
for future reference. The Seed Concentration Check rule (now in the
skill) applies from iter-030 onwards.

Standard targets for comparison (non-gating):
- Mean OOS monthly > +0.8 (salvage some of iter-028's OOS gain)
- Mean IS monthly > +0.4 (match/beat iter-028's +0.43)
- Profitable seeds ≥ 9/10 (loose fallback from iter-028's 10/10)
- Primary seed concentration < 70% (improvement direction, not absolute)
