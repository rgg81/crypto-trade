# Iteration v2/002 Research Brief

**Type**: EXPLOITATION (single-variable risk-layer fix)
**Track**: v2 — diversification arm
**Baseline**: None yet — iter-v2/001 was NO-MERGE (EARLY STOP)
**Date**: 2026-04-13
**Researcher**: QR
**Parent iteration**: iter-v2/001

## Section 0: Data Split

```
OOS_CUTOFF_DATE = 2025-03-24    ← FIXED. NEVER CHANGES. NOT NEGOTIABLE.
```

Shared with v1.

## Motivation

iter-v2/001 produced:

- **Raw** (unweighted) OOS Sharpe: +0.479 (DSR p≈1, v2-v1 OOS correlation +0.011)
- **Weighted** (RiskV2Wrapper applied) OOS Sharpe: −0.324 (fails +0.5 target)
- **Regime-stratified OOS**: −1.85 Sharpe in low-ATR trending bucket,
  +1.45 in high-ATR trending bucket

Diagnosis (from iter-v2/001 diary §Root Cause): the `RiskV2Wrapper` vol-adjusted
sizing formula `vol_scale = 1 − atr_pct_rank_200` is **sign-inverted** for
this strategy. OOS edge concentrates in the high-vol trending quadrant
which the iter-v2/001 formula shrinks to 0.3×, while low-vol losing trades
run at full size. Per-symbol XRP raw +37.56% became weighted **−6.65%** —
sign literally flipped.

iter-v2/001 diary Priority 1 proposed three fixes:

1. Disable vol-scaling
2. **Invert** the formula (`vol_scale = atr_pct_rank_200`) — recommended
3. Hurst-based sizing

iter-v2/002 implements the recommended fix: **option 2**. One variable
change, clean attribution. All other configuration is byte-for-byte
identical to iter-v2/001.

## Hypothesis

Inverting the vol-scaling formula will raise the weighted OOS Sharpe from
−0.324 to **at least** the raw unweighted level (+0.479). Because the
inverted formula amplifies winning high-vol trades (scale → 1.0) while
shrinking losing low-vol trades (scale → 0.3), the weighted Sharpe should
actually EXCEED the raw level — the formula acts as an implicit "filter
low-vol losses" overlay.

Quantitative prediction (pre-registered):

- Weighted OOS Sharpe: **≥ +0.48** (lower bound = raw level)
- Weighted OOS Sharpe most likely range: **+0.7 to +1.2**
- 10-seed mean OOS Sharpe: > 0, ≥7/10 profitable
- v2-v1 OOS correlation: unchanged from iter-v2/001 (+0.011) — the trade
  set is the SAME, only weights change
- DSR > 0 for weighted OOS
- OOS MaxDD: similar or slightly worse (larger positions on winners scale
  drawdowns too)

Failure mode prediction (pre-registered): if the inverted formula does
NOT raise OOS Sharpe above +0.48, the vol-scaling concept itself is wrong
for this strategy (not just the sign). iter-v2/003 would then disable
vol-scaling entirely and fall back to engine-level uniform sizing.

## Configuration

| Setting | iter-v2/001 | iter-v2/002 | Changed? |
|---|---|---|---|
| Interval | 8h | 8h | — |
| Training window | 24 months | 24 months | — |
| Labeling | ATR 2.9/1.45 via `natr_21_raw` | Same | — |
| Timeout | 7 days | 7 days | — |
| Cooldown | 2 candles | 2 candles | — |
| Feature set | 35 (`V2_FEATURE_COLUMNS`) | Same | — |
| Feature parquets | `data/features_v2/` | Same | — |
| Models | E=DOGE, F=SOL, G=XRP | Same | — |
| Optuna trials | 10 | 10 | — |
| CV splits | 5 | 5 | — |
| Primary seed | 42 | 42 | — |
| Seeds for validation | 1 (early stop) | 10 | Yes (validation) |
| `RiskV2Config` enables | vol+ADX+Hurst+z-score | Same | — |
| **`_vol_scale` formula** | **`1 − atr_pct_rank`** | **`atr_pct_rank`** | **Yes** |
| `vol_scale_floor` | 0.3 | 0.3 | — |
| `vol_scale_ceiling` | 1.0 | 1.0 | — |
| ADX threshold | 20 | 20 | — |
| Hurst percentile band | 5-95 | 5-95 | — |
| z-score threshold | 3.0 | 3.0 | — |

**One variable changed**: the `_vol_scale` formula in `RiskV2Wrapper`.

## Research Checklist Coverage

iter-v2/002 is a narrow-scope EXPLOITATION iteration with one variable. Per
the v2 skill §Phase Quick Reference, after 1 iteration of NO-MERGE/EARLY
STOP the QR still has not passed the "3+ consecutive NO-MERGE" threshold,
so the full research checklist is not mandatory. The mandatory Category I
(Risk Management Analysis) is completed in Section 6 below. No additional
checklist categories are run this iteration.

## Success Criteria (iter-v2/001 relaxed — still no prior baseline)

Same criteria as iter-v2/001. All must pass:

- OOS Sharpe > +0.5 (modest starting bar)
- ≥7/10 seeds profitable
- Mean OOS Sharpe > 0 across 10 seeds
- OOS trades ≥ 50
- Profit factor > 1.1
- No single symbol > 50% of OOS PnL
- DSR > −0.5
- **v2-v1 OOS correlation < 0.80** (non-negotiable)

## Expected Runtime

- 10 seeds × ~4 min/seed ≈ 40 minutes of wall-clock
- Feature parquets: no regeneration needed (already present from iter-v2/001)

---

## Section 6: Risk Management Design

### 6.1 Risk Primitives Active This Iteration

| Primitive | Status | Parameters | Change from iter-v2/001 |
|---|---|---|---|
| Vol-adjusted sizing | ENABLED | floor=0.3, ceiling=1.0, **formula=atr_pct_rank_200** (sign inverted) | **Changed** — this is the one variable under test |
| ADX gate | ENABLED | threshold=20 | — |
| Hurst regime check | ENABLED | 5/95 pct of training `hurst_100` | — |
| Feature z-score OOD | ENABLED | `|z|>3` threshold | — |
| Drawdown brake | DISABLED | — | Deferred (iter-v2/003+) |
| BTC contagion | DISABLED | — | Deferred |
| Isolation Forest | DISABLED | — | Deferred |
| Liquidity floor | DISABLED | — | Deferred |

### 6.2 Questions the QR Must Answer

**1. Regime coverage**: Unchanged from iter-v2/001. Same IS window, same
training data, same Hurst distribution. The regime coverage gap (no
sustained low-vol ranging regimes in OOS) still applies.

**2. Expected gate firing rate**: Unchanged from iter-v2/001. The sign flip
does not affect which gates fire — it only affects the `weight_factor`
applied to the survivors. The z-score OOD, Hurst, and ADX gates will fire
at the same rates as iter-v2/001 (~11-16%, ~6-9%, ~24-28% respectively).

**3. Black-swan scenario replay**: Still identical to iter-v2/001. The new
scaling logic means a black swan spike (atr_pct_rank near 1.0) now scales
the SURVIVING trade UP to the ceiling, which is riskier in absolute terms.
This is intentional — the post-mortem will check whether the net effect
across the training window is positive.

**4. Known-unknown failure modes**:

- **Slow monotone bleed**: same as iter-v2/001. No progress on this risk
  vector until the drawdown brake is enabled (deferred).
- **Over-concentration in high-vol**: the inverted formula risks piling
  into a single high-vol event and losing disproportionately. Mitigated
  by the 7-day timeout, ATR-scaled SL, and cooldown — but worth watching
  in the per-regime and drawdown metrics.
- **IS over-weights low-vol wins**: the iter-v2/001 IS per-regime breakdown
  showed IS low-vol bucket Sharpe +0.58 (positive!). Under the inverted
  formula this profitable IS bucket gets shrunk, so IS Sharpe may actually
  DROP vs iter-v2/001. This is the most likely downside: weighted IS/OOS
  may flip in ratio (OOS ratio > 1 because IS edge is partly killed).
  That's a known trade-off and acceptable as long as OOS clears the bar.

**5. Deferred primitives rationale**: unchanged from iter-v2/001.

### 6.3 Pre-Registered Failure-Mode Prediction

The most likely way iter-v2/002 fails is: **the inverted vol-scaling
formula works directionally (weighted OOS Sharpe positive) but
over-concentrates in a small number of high-vol events, producing a
large per-trade std and a non-trivial MaxDD spike that fails the
"no single symbol > 50% of OOS PnL" constraint**. The gates that should
catch it are: none enabled today — this failure mode needs the drawdown
brake. If the failure materializes, the loss will look like: one of the
3 models (probably DOGE or SOL — larger NATR than XRP) owning > 50% of
OOS PnL with a few big winners followed by a single-trade drawdown
> 25%. In that case, iter-v2/003 enables the drawdown brake and keeps
the inverted vol-scaling.

A less likely but possible failure: **the IS Sharpe drops enough that
the IS/OOS Sharpe ratio falls below 0.5** (overfitting gate), even
though OOS is above 0.5. Would still require NO-MERGE under the strict
constraint, but the diagnosis is clean: the inverted scaling has
opposite effects on IS (positive low-vol bucket) and OOS (negative
low-vol bucket). iter-v2/003 could then resolve via the Hurst-based
sizing (option 3 from the iter-v2/001 diary) rather than the ATR
percentile.

### 6.4 Exit Conditions

Unchanged from iter-v2/001. Gates fire at signal time only; open positions
honor TP/SL/timeout.

### 6.5 Post-Mortem Template

After the backtest, the QR reports per gate in the diary:

- Fire rate (% of signals)
- PnL of killed trades
- PnL of scaled-down trades (delta vs full size) — this iteration the
  "scaled-down" set is the LOW-vol set, which is the key attribution
  question
- Gate ROI
- Comparison of per-regime OOS Sharpe vs iter-v2/001 (the critical before/after)
