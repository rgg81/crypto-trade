# Iteration v2/020 Research Brief

**Type**: EXPLORATION (combined portfolio re-analysis with iter-019 baseline)
**Track**: v2 → combined portfolio
**Parent baseline**: iter-v2/019 (BTC trend filter + hit-rate gate)
**Date**: 2026-04-14
**Researcher**: QR
**Branch**: `iteration-v2/020` on `quant-research`

## Section 0: Data Split

```
OOS_CUTOFF_DATE = 2025-03-24    ← FIXED. NEVER CHANGES.
```

## Motivation — does the IS improvement carry into combined portfolio?

iter-v2/018 ran the combined v1+v2 portfolio analysis with the
iter-v2/017 baseline (hit-rate gate only). It found that 50/50
blend becomes optimal (Sharpe +5.44, MaxDD −17.10%) because
v2's standalone Sharpe jumped to +4.79.

iter-v2/019 added the BTC trend filter, improving v2 primarily
on the IS side but also slightly on OOS (+2.45 → +2.54 Sharpe,
+119.94 → +125.82 total PnL).

**Question iter-020 answers**: does the iter-019 v2 baseline
deliver an even better combined 50/50 blend, or does the
additional BTC filter leave the combined OOS metrics roughly
unchanged since most of the improvement is IS-side?

## Hypothesis

**Primary**: combined 50/50 Sharpe improves modestly (from
+5.44 to +5.55-+5.65), because v2's OOS improvements (+5% Sharpe,
+5% PnL) carry over proportionally.

**MaxDD**: essentially unchanged at ~−17% (v2's OOS MaxDD
is unchanged at 24.39%).

**Concentration**: slightly different per-symbol shares because
XRP's iter-019 OOS contribution is +52.08 vs iter-017's +46.19.

## Methodology

Fork `run_portfolio_combined_v2_017.py` to
`run_portfolio_combined_v2_019.py` that points at
`reports-v2/iteration_v2-019/` instead of `iteration_v2-017/`.
Same analysis pipeline, new v2 input.

## Success Criteria

This is an analysis iteration, not a competitive one.

- [ ] Combined 50/50 Sharpe ≥ iter-018's +5.44
- [ ] Combined 50/50 MaxDD ≤ iter-018's −17.10%
- [ ] Combined max symbol concentration ≤ 50%
- [ ] Clear deployment recommendation for v0.v2-019

No MERGE. Cherry-pick to `quant-research` as analysis artifact.

## Section 6: Risk Management Design

No new gates. This iteration uses iter-v2/019's gates via the
trade stream from `reports-v2/iteration_v2-019/`.

### 6.3 Pre-registered failure-mode prediction

Most likely: combined metrics are essentially unchanged from
iter-018 because the BTC filter's main wins are IS-side, and the
combined analysis is computed on OOS trades only. Expected:
- Combined 50/50 Sharpe: +5.45 to +5.55 (small improvement)
- Combined 50/50 MaxDD: ~−17% (same as iter-018)
- Best blend: still 50/50 or 60/40

Unlikely: combined metrics materially improve. The BTC filter
adds ~6 OOS PnL which is small relative to v1's ~119.
