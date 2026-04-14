# Iteration v2/014 Research Brief

**Type**: EXPLOITATION (per-symbol drawdown brake feasibility)
**Track**: v2 — risk arm
**Parent baseline**: iter-v2/005 (10-seed mean +1.297)
**Date**: 2026-04-14
**Researcher**: QR
**Branch**: `iteration-v2/014` on `quant-research`

## Section 0: Data Split

```
OOS_CUTOFF_DATE = 2025-03-24    ← FIXED. NEVER CHANGES.
```

## Motivation — response to iter-v2/013's NO-MERGE

iter-v2/013 productionized a portfolio-level drawdown brake (Config
C 8%/16%) into `run_baseline_v2.py`. 10-seed validation passed
Sharpe (+1.146) and profitability (9/10) but strict-failed the
concentration rule: XRP weighted share jumped from 47.75% to
**78.55%**.

**Root cause (from iter-v2/013 engineering report)**: during the
July-August 2025 drawdown, the portfolio brake enters flatten state
and zeros ALL trades. DOGE had losses in that window (brake saved
−21.5 PnL for DOGE); SOL and NEAR had winners in the same window
(brake killed their +29 and +21 contributions respectively). The
blanket flatten can't distinguish winners from losers.

**The fix**: replace the portfolio-level brake with a **per-symbol
brake**. Each model tracks its own compound equity DD. A brake only
fires for the model whose own OOS PnL is in drawdown. DOGE's brake
fires during July 2025 (DOGE is bleeding); SOL and NEAR's brakes
don't fire (their own PnLs are still profitable that month).

## Hypothesis

A per-symbol brake with the SAME Config C thresholds (8%/16%/0.5)
will deliver:

1. **MaxDD reduction**: primary seed 42 OOS MaxDD < 25% (less than
   iter-v2/013's 16.41% because fewer trades flattened, but still
   well below baseline 59.88%)
2. **Sharpe preservation**: 10-seed mean OOS Sharpe ≥ +1.2 (less
   drag than iter-v2/013's −0.152 because fewer winning trades
   flattened)
3. **Concentration preservation**: XRP weighted share within 5 pp
   of baseline 47.75% → ≤ 52.5% (strict fail threshold 50% may
   still be violated marginally, but not by 28 pp)
4. **Per-symbol PnL: no symbol flips from positive to negative**

## Methodology

### Phase 1 — post-hoc feasibility (this iteration)

Analogous to iter-v2/012's portfolio-brake feasibility but with a
per-symbol decomposition. Loads iter-v2/005's OOS trades, groups
them by symbol, applies the brake to each symbol's stream
INDEPENDENTLY (each symbol tracks its own shadow equity starting
at 1.0), then recombines.

Tests the same 4 configurations as iter-v2/012:
- A (5/10), B (6/12), **C (8/16)**, D (4/8)

Plus a "None" baseline.

Output: `reports-v2/iteration_v2-014_per_symbol_brake/`
- `summary.json` — per-config aggregate metrics
- `per_symbol_summary.csv` — per-(config, symbol) breakdown
  including concentration check

### Phase 2 — (iter-v2/015) productionize if feasibility passes

If any config achieves MaxDD < 25% AND Sharpe > +1.3 AND
concentration ≤ 55%, iter-v2/015 will productionize via
`on_trade_closed` callback on the Strategy Protocol. iter-v2/014
is feasibility only.

## Pre-registered failure-mode prediction

The most likely way per-symbol brake fails:

**"Per-symbol DD is too noisy to brake effectively."** Each model
has only 20-40 OOS trades. The compound equity of a single model
can be −8% after just 2-3 bad trades, triggering shrink on
legitimate vol. The brake fires on single-trade noise instead of
regime-scale events. Result: Sharpe drops because routine drawdowns
get attenuated, not just tail events.

**Alternative failure**: the per-symbol brake fires too rarely
because single-symbol DDs stay below 8% most of the time. The brake
has no effect and MaxDD is unchanged.

**Sweet spot prediction**: Config C still wins (loose thresholds,
fires only on meaningful per-symbol DDs). DOGE's brake fires during
its 2022 IS bear (out of scope post-OOS-cutoff) and during
July 2025. Concentration stays near baseline 47.75%. Aggregate
Sharpe drags −0.05 to −0.15.

## Configuration

**New script**: `analyze_per_symbol_brake.py`. Reads
`reports-v2/iteration_v2-005/out_of_sample/trades.csv`, applies the
per-symbol brake to each symbol's trade subset independently,
reports per-config aggregate and per-symbol breakdowns.

**Thresholds to test**: same as iter-v2/012
- A (5/10), B (6/12), C (8/16), D (4/8), None

**Scoping**: the brake still activates at OOS_CUTOFF_MS, identical
to iter-v2/013's `activate_at_ms` logic.

## Research Checklist Coverage

This is the 7th consecutive NO-MERGE (006, 007, 008, 009, 010, 013,
and iter-v2/014 as a feasibility study — not technically a
NO-MERGE, but the count is for pivot discipline). Per the skill's
"3+ consecutive NO-MERGE" rule, the brief covers all 9 research
categories explicitly.

### Category A — strategy family

No change. LightGBM with triple-barrier labeling, per-symbol
pooled training, 24-month walk-forward window.

### Category B — feature set

No change. 35 v2 features from the iter-v2/005 baseline.

### Category C — labeling

No change. ATR barriers at 2.9/1.45, timeout 10080 min.

### Category D — risk layer

**This is the axis being modified.** Iter-v2/014 introduces a
per-symbol drawdown brake as a feasibility study. Each symbol's
brake operates on its own compound equity, independent of other
symbols. Thresholds 8%/16% with 0.5 shrink factor.

### Category E — hyperparameters

No change. 10 Optuna trials, same search space.

### Category F — training window

No change. 24 months.

### Category G — symbol selection

No change. DOGE + SOL + XRP + NEAR.

### Category H — seeding / ensembling

No change. 10 seeds for MERGE validation, same FULL_SEEDS list.

### Category I — risk management analysis (mandatory per skill)

The per-symbol brake addresses iter-v2/013's concentration failure
mode. The asymmetric per-symbol impact from the portfolio brake is
eliminated because each brake sees only its own model's DD. Cross-
symbol contamination is impossible by construction.

## Success Criteria

Feasibility passes if ANY of the 4 configs achieves ALL of:

- [ ] OOS MaxDD < 25% (post-hoc, primary seed 42 trades)
- [ ] OOS Sharpe ≥ +1.3 (trade level)
- [ ] Concentration (weighted) ≤ 55% (strict rule is 50% but I
      allow 5 pp cushion since per-symbol brake may still affect
      XRP's share slightly)
- [ ] No per-symbol contribution flips from positive to negative
- [ ] OOS PF > 1.3

If feasibility passes, iter-v2/015 productionizes the winning
config via the `on_trade_closed` callback.

## Section 6: Risk Management Design

### 6.1 Active gates (unchanged from iter-v2/005)

- Feature z-score OOD (|z| > 3)
- Hurst regime check (5th/95th IS percentile)
- ADX gate (threshold 20)
- Low-vol filter (atr_pct_rank_200 < 0.33)
- Vol-adjusted sizing (scale = atr_pct_rank_200, clipped 0.3-1.0)

### 6.2 New gate — per-symbol drawdown brake (POST-HOC SIMULATION)

- Scope: each symbol is braked independently on its own compound
  equity DD
- Shrink threshold: −8% per-symbol DD → weight × 0.5
- Flatten threshold: −16% per-symbol DD → weight × 0
- Activation: brake active from OOS_CUTOFF_MS onwards; shadow
  equity resets to 1.0 at activation
- Self-releasing: shadow equity driven by unbraked per-symbol PnL

### 6.3 Pre-registered failure-mode prediction

See §"Pre-registered failure-mode prediction" above. Summary:
either the per-symbol DD is too noisy (brake fires on single-trade
moves) or too quiet (brake never fires because single-symbol DDs
stay below 8%). Config C expected to be the sweet spot. Main
risk: Sharpe drag larger than expected because DOGE's
individual drawdown ≥ 16% during July 2025 flattens half of
DOGE's OOS stream.

### 6.4 Expected gate firing rates

| Symbol | Expected shrink fires | Expected flatten fires |
|---|---|---|
| DOGE | 2-5 | 5-15 (July-August losses) |
| SOL | 0-2 | 0 (SOL is profitable through July) |
| XRP | 0-2 | 0-2 |
| NEAR | 1-3 | 2-8 (NEAR has higher per-symbol vol) |

### 6.5 Black-swan replay

Per-symbol brake should catch DOGE's July-August 2025 loss stretch
on DOGE's brake only, NOT on SOL's or NEAR's. Verification: the
firing log should show DOGE brake fires in July 2025 with SOL/XRP/
NEAR brakes staying off during those same dates.
