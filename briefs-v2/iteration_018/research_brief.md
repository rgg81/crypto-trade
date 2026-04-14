# Iteration v2/018 Research Brief

**Type**: EXPLORATION (combined portfolio re-analysis with braked v2)
**Track**: v2 → combined portfolio
**Parent baseline**: iter-v2/017 (first braked v2 baseline)
**Date**: 2026-04-14
**Researcher**: QR
**Branch**: `iteration-v2/018` on `quant-research`

## Section 0: Data Split

```
OOS_CUTOFF_DATE = 2025-03-24    ← FIXED. NEVER CHANGES.
```

## Motivation — what changed since iter-v2/011's analysis

iter-v2/011 ran a combined v1+v2 portfolio analysis that reported:

| Portfolio | Sharpe | MaxDD | Recommendation |
|---|---|---|---|
| v1 alone (iter-152) | +4.91 | −20.0% | best |
| v2 alone (iter-v2/005) | +3.35 | −45.3% | satellite only |
| 50/50 combined | +4.48 | −24.2% | Sharpe drag |
| **70/30 recommended** | +4.84 | −22.2% | balanced |

Key constraint at the time: **v2's 45% MaxDD made 50/50 too risky**.
v2 was a 30% satellite.

**iter-v2/017 changed that**. The braked v2 baseline has MaxDD 24.39%
(vs v1's 20.0%), similar to v1 in risk terms. Its Sharpe jumps to
+2.45 (primary seed) or +1.41 (10-seed mean).

The question iter-v2/018 answers: **does the braked v2 unlock a
50/50 or 60/40 blend that's materially better than iter-v2/011's
70/30 recommendation?**

## Hypothesis

With v2's MaxDD halved and its Sharpe materially improved:

1. **50/50 blend becomes viable** (no longer dominated by v1)
2. **Combined worst-day still improves** vs v1 alone (the
   diversification benefit from correlation +0.08 is preserved
   — the brake doesn't affect v2's correlation with v1)
3. **Combined MaxDD lands between 17-22%** (below v1's 20% if
   the brake is effective during combined-period drawdowns)
4. **Combined Calmar improves dramatically** because both tracks
   have lower MaxDD
5. **Optimal blend ratio** shifts from 70/30 toward 50/50 or 60/40

## Methodology — reuse iter-v2/011's pattern

Fork `run_portfolio_combined.py` (iter-v2/011) into
`run_portfolio_combined_v2_017.py` that reads:
- v1 iter-152: `/home/roberto/crypto-trade/reports/iteration_152_min33_max200/`
- **v2 iter-v2/017**: `reports-v2/iteration_v2-017/` (newly generated)

Compute identical metrics: per-track Sharpe, PF, MaxDD, per-symbol
concentration, v1-v2 correlation, diversification benefit,
multiple blend ratios (50/50, 60/40, 70/30, inverse-vol, Sharpe-
weighted).

## Pre-registered failure-mode prediction

**Most likely**: the brake's effect on v2 doesn't translate 1:1 to
the combined portfolio because:
- v1's drawdowns are DIFFERENT dates than v2's (correlation +0.08)
- The brake activates on v2's own SL rate, not v1's
- So on v1's worst day (2025-04-09), v2's brake isn't firing and
  v2 runs at full weight alongside v1's loss
- On v2's worst day (2025-07-20), v1 is fine and not braked
- Net effect: brake only helps the v2 half of combined days

Expected: combined 50/50 Sharpe around +4.6-4.8 (vs iter-011's
+4.48). Combined MaxDD around 19-22% (vs iter-011's 24.15%).
Calmar around +50-60 (vs iter-011's +37).

**Best case**: combined 50/50 Sharpe exceeds v1 alone (+4.91). Rare
but possible if the braked v2 is a strongly-independent positive
contributor.

**Worst case**: combined gains are marginal (<5% on Sharpe/MaxDD)
because v2's braked contribution is diluted by v1 when blended
50/50.

## Configuration

**New script**: `run_portfolio_combined_v2_017.py`. Based on
`run_portfolio_combined.py` from iter-v2/011, but:
- V2_REPORT points at `reports-v2/iteration_v2-017`
- OUT_DIR points at `reports-v2/iteration_v2-018_combined_braked`
- Output tables include the baseline iter-v2/011 result alongside
  the new result for direct comparison

## Success Criteria

This is an analysis iteration, not a competitive one. The goal is
to answer the strategic question: **does the improved v2 shift
the blend recommendation?**

Outputs:
- [ ] Combined 50/50 metrics with braked v2
- [ ] Comparison vs iter-v2/011's original numbers
- [ ] Per-symbol concentration (should preserve or improve vs 011)
- [ ] v2-v1 correlation (should be similar to 011's +0.08)
- [ ] Updated blend recommendation (50/50, 60/40, or 70/30)
- [ ] Combined worst-day analysis

No MERGE. Cherry-pick docs and new runner to `quant-research` as
an analysis artifact.

## Section 6: Risk Management Design

### 6.1 Active gates (unchanged — inherited from iter-v2/017)

All 6 gates active on the v2 side:
- Feature z-score OOD
- Hurst regime check
- ADX gate
- Low-vol filter
- Vol-adjusted sizing
- **Hit-rate feedback gate (iter-v2/017)**

v1 side is unchanged (iter-152's 3 models A/C/D with per-symbol
vol targeting and min_scale=0.33).

### 6.2 Portfolio-level risk

The combined portfolio uses **post-hoc blend reweighting** on the
trade streams. Each track carries its own internal risk layer
(v1 has VT, v2 has the 6 gates). No cross-track risk primitive is
applied at the combined layer.

### 6.3 Pre-registered failure-mode prediction

See §"Pre-registered failure-mode prediction" above. Summary:
combined Sharpe and MaxDD should improve, but only modestly
relative to iter-v2/011 because v1 and v2's drawdowns are on
different dates and the brake only helps v2's worst days.

### 6.4 Expected outcomes

| Metric | iter-v2/011 50/50 | Expected iter-v2/018 50/50 | Δ |
|---|---|---|---|
| Sharpe | +4.48 | +4.6 to +4.8 | +3-7% |
| MaxDD | −24.15% | −19% to −22% | −10-20% |
| Calmar | +37 | +50 to +60 | +35-60% |
| Worst day | −6.78% | −4 to −6% | modest |

### 6.5 Blend recommendation hypothesis

If combined 50/50 Calmar > iter-v2/011's 70/30 Calmar (+47), then
**50/50 becomes the new recommended blend**. Otherwise 70/30 stays.
