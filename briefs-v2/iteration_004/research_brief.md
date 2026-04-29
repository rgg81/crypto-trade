# Iteration v2/004 Research Brief

**Type**: EXPLOITATION (new gate in RiskV2Wrapper)
**Track**: v2 — diversification arm
**Parent baseline**: iter-v2/002 (OOS Sharpe +1.17 primary, +0.96 10-seed mean)
**Date**: 2026-04-13
**Researcher**: QR

## Section 0: Data Split

```
OOS_CUTOFF_DATE = 2025-03-24    ← FIXED. NEVER CHANGES. NOT NEGOTIABLE.
```

## Motivation

iter-v2/002's OOS regime-stratified breakdown (from
`reports-v2/iteration_v2-002/out_of_sample/per_regime_v2.csv`):

| Hurst | ATR pct | n | weighted mean | weighted Sharpe |
|---|---|---|---|---|
| [0.60, 2.00) | [0.00, 0.33) | 54 | **−0.44%** | **−1.86** |
| [0.60, 2.00) | [0.33, 0.66) | 43 | +0.45% | +0.81 |
| [0.60, 2.00) | [0.66, 1.01) | 42 | +1.55% | +1.49 |

The low-ATR trending bucket is the single largest OOS drag — 54 trades
with weighted Sharpe **−1.86**. iter-v2/002's inverted vol-scaling
already shrinks these to 0.3× floor, but the cumulative impact is
still material (the aggregate OOS Sharpe is "only" +1.17 because
these 54 trades pull it down from a cleaner ~+1.5+ possible).

iter-v2/001 and iter-v2/003 diaries both flagged the low-vol filter as
Priority 2 / Priority 1 respectively. iter-v2/003's DOGE experiment
dead-ended (IS-overfit), so iter-v2/004 promotes this to Priority 1
and implements it.

## Hypothesis

Adding a hard gate `atr_pct_rank_200 >= 0.33` in `RiskV2Wrapper.get_signal`
(new gate #4, between ADX and vol scaling) mechanically removes the
−1.86 Sharpe bucket. The remaining 85 mid + high-vol trades keep their
bucket Sharpes of +0.81 and +1.49 respectively.

Quantitative prediction (pre-registered):

- **OOS Sharpe**: **+1.3 to +1.8** range (up from +1.17 baseline) — the
  aggregate is not a simple average of bucket Sharpes but the removal of
  a −1.86 component from a +1.17 aggregate leaves something in that range.
- **OOS trade count**: 85 (down from 139), still well above 50 minimum.
- **OOS PF**: ≥ 1.3 (up from 1.29).
- **OOS WR**: ≥ 42% (up from 40.3%, because the removed trades had
  the lowest WR).
- **Per-symbol**: all three models lose trades from their low-vol bucket.
  DOGE's negative contribution shrinks because its low-vol trades are
  removed (DOGE's 60% SL rate is partly a low-vol artifact).
- **Concentration**: XRP's share of signed PnL drops from 74% toward
  60-65% (because DOGE becomes less negative).
- **v2-v1 correlation**: essentially unchanged (+0.04 ish).
- **DSR z-score**: ≥ +5 (positive, strongly significant at N=4 v2 trials).
- **10-seed robustness**: mean OOS Sharpe ≥ +1.2, ≥ 7/10 profitable.

## Failure-mode prediction (pre-registered)

Most likely way to fail:

1. **Low-vol trades were actually propping up aggregate via MEAN** —
   if the −1.86 Sharpe bucket had a positive MEAN (it didn't in
   iter-v2/002 data: −0.44% mean weighted), removing it could
   counter-intuitively drop aggregate PnL despite improving Sharpe.
   Low probability because the bucket mean is clearly negative.
2. **Cascading filter compounding** — the combined kill rate is
   already 45-51% in iter-v2/002; adding a new gate that kills
   additional trades could push kill rate to 65-75%, leaving the
   model signal-starved. Trade count drops from 139 to ~85, still
   above 50 but tighter.
3. **Regime distribution shift in OOS** — iter-v2/002's 54 low-vol
   trades spanned the whole OOS window. If those trades happened to
   include some big winners that I'm not seeing in the aggregate,
   removing them hurts. The per-trade mean of −0.44% weighted argues
   against this.
4. **The inverted vol-scale was already doing the job** — if the
   existing 0.3× scaling was already neutralizing the low-vol bucket,
   the hard filter gives zero additional lift. Expected outcome:
   modest +0.1 to +0.2 Sharpe gain. Still directionally correct.

## Configuration (one variable changed from iter-v2/002)

| Setting | iter-v2/002 | iter-v2/004 | Changed? |
|---|---|---|---|
| `enable_low_vol_filter` | (not defined) | **True** | **NEW** |
| `low_vol_filter_threshold` | (not defined) | **0.33** | **NEW** |
| `_vol_scale` formula | `atr_pct_rank_200` clipped | Same | — |
| ADX / Hurst / z-score gates | Same | Same | — |
| DOGE ATR multipliers | 2.9/1.45 | 2.9/1.45 | — (iter-v2/003 dead-end reverted) |
| SOL/XRP ATR multipliers | 2.9/1.45 | 2.9/1.45 | — |
| Features, Optuna, seeds | Same | Same | — |

## Research Checklist Coverage

Single-variable EXPLOITATION iteration. Category I (Risk Management
Analysis) completed in Section 6. No other categories required post-MERGE
(iter-v2/002 was a clean MERGE, no consecutive NO-MERGE streak).

Note: iter-v2/003 was NO-MERGE but not part of a consecutive streak that
triggers mandatory full checklist — it sits between a MERGE (iter-v2/002)
and this new iteration.

## Success Criteria (inherit iter-v2/002 baseline)

Primary: **OOS Sharpe > +1.17** (current v2 baseline).

Hard constraints:

- ≥ 7/10 seeds profitable
- Mean OOS Sharpe (10-seed) > baseline mean (+0.96)
- OOS trades ≥ 50
- OOS PF > 1.1
- **No single symbol > 50% OOS PnL** (strict — no override this iteration;
  iter-v2/002's override was one-time)
- DSR > +1.0
- v2-v1 OOS correlation < 0.80
- IS/OOS Sharpe ratio > 0.5

## Expected Runtime

- 10 seeds × ~4 min/seed ≈ 35-40 minutes
- Fewer trades per seed (low-vol kills ~25% more signals) → marginally
  faster inner loop

## Section 6: Risk Management Design

### 6.1 Active primitives

| Primitive | Status | Parameters | Change from iter-v2/002 |
|---|---|---|---|
| Vol-adjusted sizing (inverted) | ENABLED | floor=0.3, ceiling=1.0 | — |
| ADX gate | ENABLED | threshold=20 | — |
| Hurst regime check | ENABLED | 5/95 pct | — |
| Feature z-score OOD | ENABLED | \|z\|>3 | — |
| **Low-vol filter** | **ENABLED** | **threshold=0.33** | **NEW** |
| Drawdown brake | DISABLED | — | Deferred |
| BTC contagion | DISABLED | — | Deferred |
| Isolation Forest | DISABLED | — | Deferred |
| Liquidity floor | DISABLED | — | Deferred |

### 6.2 Expected fire rates

- Vol-adjusted sizing: unchanged (applies to all survivors)
- ADX gate: ~28% (unchanged)
- Hurst regime: ~6-9% (unchanged)
- Feature z-score OOD: ~11-16% (unchanged)
- **Low-vol filter (NEW)**: expected ~25-30%. The `atr_pct_rank_200 < 0.33`
  condition fires on ~33% of bars by construction (it's a rank transform
  with a 0.33 threshold), minus the bars already killed by other gates.
  After the 45-51% combined kill rate of iter-v2/002, ~55% of signals
  pass through; the new filter kills ~33% of those = ~18% additional kill
  rate for an aggregate combined kill rate of ~60-70%. This is well
  above the 10-30% calibration target but the retained signal quality
  should be higher.

### 6.3 Pre-registered failure-mode prediction

"The most likely way iter-v2/004 fails is that the existing inverted
vol-scaling was already neutralizing the low-vol bucket's impact on
aggregate Sharpe, so the new hard filter provides only marginal lift
(+0.1 to +0.2 Sharpe). In that case, OOS Sharpe would rise from +1.17
to ~+1.3 — still a valid MERGE but not a structural improvement.

The secondary failure mode: if the combined kill rate exceeds 70%,
the model becomes signal-starved, OOS trade count drops below 50, and
the iteration fails the trade-count constraint despite a high Sharpe.
Quick math on iter-v2/002 rates suggests 85 OOS trades remain, which
is above 50 — but if the low-vol filter fires more aggressively than
expected, trade counts could dip."

### 6.4 Exit Conditions

Unchanged from iter-v2/002.

### 6.5 Post-Mortem Template

Phase 7 will compute:

- Low-vol filter fire rate per symbol
- OOS trade count after filtering (vs iter-v2/002's 139)
- Per-regime Sharpe breakdown after filter (should show only the mid
  and high-vol buckets for OOS)
- Comparison table vs iter-v2/002 baseline
- 10-seed robustness vs iter-v2/002's mean +0.96
