# Iteration v2/005 Research Brief

**Type**: EXPLORATION (symbol universe expansion)
**Track**: v2 — diversification arm
**Parent baseline**: iter-v2/004 (OOS Sharpe +1.745 primary, +1.096 10-seed mean)
**Date**: 2026-04-14
**Researcher**: QR

## Section 0: Data Split

```
OOS_CUTOFF_DATE = 2025-03-24    ← FIXED. NEVER CHANGES. NOT NEGOTIABLE.
```

## Motivation

iter-v2/004 established a much stronger v2 baseline but merged with a
concentration near-pass: XRP was 52.6% of signed OOS PnL vs the 50%
hard constraint. The iter-v2/004 diary identified Priority 1 as
"bring XRP cleanly below 50%" and recommended adding a 4th symbol
(dilution strategy) rather than tightening filters (trimming strategy).

iter-v2/005 implements the 4-symbol option using NEARUSDT.

**Why NEARUSDT**:

- Passed the 6-gate screening in iter-v2/001 (v1 corr 0.665, $240M
  daily volume, 4,847 IS candles)
- L1 category (Layer 1 blockchain), distinct from XRP (payment) and
  SOL (L1 but different architecture), adding category diversity
- Lowest v1 correlation among the remaining screening survivors
  (tied with FILUSDT and XRPUSDT at 0.665)
- Long history (4,847 IS candles ≈ 4.4 years on 8h)

**Secondary benefit**: this is EXPLORATION (symbol universe change) per
the v2 skill's exploration/exploitation taxonomy. The rolling 10-iter
exploration rate after iter-v2/004 was 1/4 = 25%, below the 30%
minimum. iter-v2/005 brings the rate to 2/5 = 40%, restoring the
quota. Two birds, one stone.

## Hypothesis

Adding NEARUSDT as a 4th symbol should:

1. **Fix concentration**: XRP share drops from 52.6% to below 50%. If
   NEAR is an "average" contributor (~20% of OOS PnL), XRP's share
   becomes roughly 52.6% × (80/100) = 42%. If NEAR is a weak contributor
   (~10%), XRP ends around 48%. Either way, likely passes.
2. **Preserve aggregate OOS Sharpe**: the existing 3 symbols' per-trade
   profiles are unchanged. NEAR adds ~20-30% more OOS trades. If NEAR
   is approximately break-even or mildly profitable (Sharpe in +0.2 to
   +0.7 range), the aggregate Sharpe lands within ~10% of iter-v2/004's
   +1.75 — acceptable under the diversification exception.
3. **Maintain v2-v1 correlation near zero**: NEAR's v1 correlation is
   0.665 (higher than DOGE's 0.51 but lower than LTC's 0.82). Adding
   it should keep the aggregate v2-v1 correlation below 0.10.
4. **Diversify categories**: DOGE (meme), SOL (L1), XRP (payment),
   NEAR (L1). The category mix is now 1 meme + 2 L1 + 1 payment.

Quantitative prediction (pre-registered):

- **XRP concentration**: 42-48% (PASS 50% limit)
- **OOS Sharpe (primary seed)**: +1.4 to +1.7 range (within 5% of baseline)
- **10-seed mean**: +0.9 to +1.2 (within ~10% of baseline mean)
- **≥ 7/10 seeds profitable**
- **v2-v1 correlation**: still < 0.10 (essentially zero)
- **NEAR standalone OOS Sharpe**: +0.2 to +0.7 (modest positive)

## Failure-mode prediction (pre-registered)

Most likely way to fail:

1. **NEAR is a drag** — if NEAR's OOS PnL is significantly negative, it
   pulls aggregate Sharpe below the 5%-of-baseline tolerance. Would need
   either to drop NEAR or try a different 4th symbol (FIL, NEAR having
   failed screening retrospectively).

2. **NEAR's IS labels are weird** — because NEAR launched in 2020
   during a rally, early IS trades may hit TP often and create an
   unrealistic training distribution. OOS NEAR could underperform
   relative to its IS-optimistic training.

3. **Kill rate cascades worse** — NEAR's ATR distribution may put
   more signals in the low-vol bucket, pushing combined kill rate
   from 66-71% to 75%+. Trade count could drop below 50 minimum.

4. **Seed 42 under-represents** — if seed 42 happens to show a weak
   result but 10-seed mean is fine. Known issue: primary seed can
   diverge from mean by 0.3-0.6 Sharpe units in either direction.

## Configuration (one variable changed from iter-v2/004)

| Setting | iter-v2/004 | iter-v2/005 | Changed? |
|---|---|---|---|
| **V2_MODELS** | 3 (E,F,G) | **4 (E,F,G,H=NEAR)** | **Yes** |
| ATR multipliers (all models) | 2.9/1.45 | 2.9/1.45 | — |
| Features, gates, seeds | Same | Same | — |
| RiskV2Wrapper configuration | Same | Same | — |

## Research Checklist Coverage

EXPLORATION iteration with one variable. Category B (Symbol Universe)
re-activated — the new symbol was pre-screened via iter-v2/001's 6-gate
protocol; no re-screening needed because NEAR is a known candidate and
no new symbol candidates are being evaluated.

Category I (Risk Management Analysis) — §6 below.

## Success Criteria

Primary: **OOS Sharpe > +1.745** (iter-v2/004 baseline) — STRICT.

Hard constraints:

- ≥ 7/10 seeds profitable
- Mean OOS Sharpe > +1.096 (iter-v2/004 baseline mean)
- OOS trades ≥ 50
- OOS PF > 1.1
- **No single symbol > 50% OOS PnL** (STRICT — no override; iter-v2/005 exists to fix this)
- DSR > +1.0
- v2-v1 OOS correlation < 0.80
- IS/OOS Sharpe ratio > 0.5

**Diversification exception** (v2 skill, §Baseline Comparison Rules):
May MERGE even if OOS Sharpe doesn't strictly improve IF all of:

- OOS Sharpe ≥ baseline × 0.95 (within 5%)
- OOS MaxDD improves by > 10%
- Concentration moves closer to passing
- All other hard constraints pass

iter-v2/005 adds NEARUSDT (a new symbol), so the exception is eligible.

## Section 6: Risk Management Design

### 6.1 Active primitives

Unchanged from iter-v2/004. Same 5 gates (vol sizing, ADX, Hurst regime,
feature z-score OOD, low-vol filter), same thresholds.

### 6.2 Expected fire rates

Per-symbol rates unchanged for DOGE/SOL/XRP. NEAR is new — expected
combined kill rate in the same 65-75% range based on similar ATR/Hurst
distributions (NEAR is L1-like, similar to SOL).

### 6.3 Pre-registered failure-mode prediction

"The most likely way iter-v2/005 fails is that NEAR is a net drag on
aggregate OOS Sharpe — if its standalone OOS Sharpe is below +0.2,
the aggregate drops below the 5%-of-baseline tolerance and the primary
metric strict-fails. In that case, the failure signal is NEAR per-symbol
weighted PnL < +5% on OOS, driving aggregate Sharpe below +1.66."

Secondary prediction: "If NEAR's IS Sharpe is negative while OOS is
positive, the IS aggregate will also drop materially — IS MaxDD could
balloon past 100% even though OOS is fine. This would be a known
acceptable trade-off because OOS is what we deploy."

### 6.4 Exit Conditions

Unchanged.

### 6.5 Post-Mortem Template

Phase 7 will report:
- NEAR standalone OOS trades, WR, weighted Sharpe, PnL
- New concentration table (4 symbols) vs iter-v2/004's 3-symbol
- Aggregate comparison table
- Pre vs post v2-v1 correlation
- Per-regime breakdown (now includes NEAR trades)
