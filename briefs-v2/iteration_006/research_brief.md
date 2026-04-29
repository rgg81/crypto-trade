# Iteration v2/006 Research Brief

**Type**: EXPLOITATION (ADX threshold tuning)
**Track**: v2 — diversification arm
**Parent baseline**: iter-v2/005 (10-seed mean +1.297, 10/10 profitable, primary seed 42 +1.671)
**Date**: 2026-04-14
**Researcher**: QR

## Section 0: Data Split

```
OOS_CUTOFF_DATE = 2025-03-24    ← FIXED. NEVER CHANGES. NOT NEGOTIABLE.
```

## Motivation

iter-v2/005 merged the 4-symbol baseline with concentration strict-passing
at 47.8%. The iter-v2/005 diary flagged the **combined gate kill rate
(66-76% across symbols)** as a known over-killing issue. The ADX gate
alone fires at 24-28% per symbol with its current threshold of 20.0.

The v2 skill's design target for combined kill rate is 10-30%. v2 has
been running at 2-3× that target since iter-v2/004's low-vol filter was
added, which is fine *when the retained signal is strong*, but it
leaves signal recovery on the table.

iter-v2/006 implements the iter-v2/005 diary's Priority 1: **lower the
ADX threshold from 20 to 15**. Expected outcome:

- ADX gate fire rate drops from 24-28% to ~10-15% per symbol
- Combined kill rate drops from 66-76% to ~50%
- OOS trade count rises from 117 to ~150
- 10-seed mean Sharpe flat-to-modestly-up (the retained trades near
  ADX 15-20 should be break-even at worst)

## Hypothesis

Lowering ADX threshold from 20 to 15 should:

1. Let through trades in the **mildly trending** band (ADX 15-20). These
   are borderline signals that the ADX gate was previously killing. If
   the model's confidence threshold is calibrated well, it will already
   skip the weakest of these; the rest should have break-even-to-mild-
   positive expectancy.
2. Preserve or slightly improve OOS Sharpe (more trades, similar
   per-trade expectancy, diversification benefit from wider regime coverage).
3. Modestly improve 10-seed mean (recovered signal).

Quantitative prediction (pre-registered):

- **Primary 10-seed mean Sharpe**: +1.25 to +1.40 (range bracketing baseline +1.30)
- **OOS trade count (primary seed)**: 140-170
- **10-seed profitable**: ≥ 8/10
- **Combined kill rate**: ~50-55% (down from 66-76%)
- **OOS MaxDD**: ±5pp of baseline (broadly unchanged)
- **Concentration**: XRP share stays ≤ 50%
- **v2-v1 correlation**: essentially unchanged (~0)

## Failure-mode prediction (pre-registered)

Most likely way to fail:

1. **Retained trades are low-quality**. The ADX 15-20 band may be the
   part of the distribution where the model's confidence threshold is
   weakest. If those trades are near break-even at best, the aggregate
   Sharpe stays flat but trade count grows, hurting per-trade efficiency
   without helping PnL.

2. **IS degradation**. Lowering ADX means more IS trades too. If the
   model's training-window edge is already marginal (iter-v2/005 IS
   Sharpe is +0.12), more borderline trades could push IS to zero or
   negative. Watch the IS/OOS Sharpe ratio — if it falls below 0.5,
   that's a researcher-overfitting warning even if OOS improves.

3. **OOS-only improvement** (the riskier pattern). If OOS Sharpe rises
   but IS falls materially, the strategy is getting lucky on OOS — the
   ADX 15-20 band happens to work in 2025 but might not in other regimes.
   A negative IS/OOS correlation is a red flag.

## Configuration (one variable changed from iter-v2/005)

| Setting | iter-v2/005 | iter-v2/006 | Changed? |
|---|---|---|---|
| **`adx_threshold`** | **20.0** | **15.0** | **Yes** |
| Everything else | Same | Same | — |

## Research Checklist Coverage

EXPLOITATION iteration with one variable. Category I (Risk Management
Analysis) in §6 below. Exploration/exploitation rolling rate: 2/6 =
33%, still above the 30% minimum.

## Success Criteria (inherits iter-v2/005 baseline, clarified primary rule)

Primary: **10-seed mean OOS Sharpe > +1.297** (iter-v2/005 baseline mean).

Hard constraints:

- ≥ 7/10 seeds profitable
- OOS trades ≥ 50
- OOS PF > 1.1
- No single symbol > 50% OOS PnL (STRICT — iter-v2/005 achieved this
  cleanly; don't regress)
- DSR > +1.0
- v2-v1 OOS correlation < 0.80
- OOS MaxDD ≤ 1.2 × baseline (53.42% × 1.2 = 64.1%)
- **IS/OOS Sharpe ratio > 0.5** (researcher overfitting gate —
  this iteration has extra attention on this rule)

## Section 6: Risk Management Design

### 6.1 Active primitives

Unchanged from iter-v2/005 except `adx_threshold: 20 → 15`.

### 6.2 Expected fire rates

- Vol-adjusted sizing: unchanged
- ADX gate: **~10-15%** (down from 24-28%)
- Hurst regime: unchanged (~6-9%)
- Feature z-score OOD: unchanged (~11-19%)
- Low-vol filter: unchanged (~19-29%)
- **Combined kill rate**: target ~50-55% (down from 66-76%)

If the combined kill rate lands above 60%, the change isn't delivering
the expected signal recovery. If it lands below 40%, the gates aren't
doing enough.

### 6.3 Pre-registered failure-mode prediction

"The most likely way iter-v2/006 fails is that the ADX 15-20 band
contains trades that are IS-negative but OOS-positive — a regime-
specific pattern that looks good on 2025 OOS but would reverse in
other regimes. Signal: IS Sharpe drops meaningfully while OOS Sharpe
rises. If IS Sharpe falls below zero while OOS is positive, that's a
**strong** flag that the strategy is working by accident, not by
design. The IS/OOS Sharpe ratio should stay above 0.5 (strictly) for
MERGE."

### 6.4 Exit Conditions

Unchanged.

### 6.5 Post-Mortem Template

Phase 7 will report:
- Combined kill rate per symbol (vs 10-30% target)
- OOS trade count change
- IS/OOS Sharpe ratio (watch this carefully)
- Per-symbol weighted Sharpes
- Comparison table vs iter-v2/005
