# Iteration v2/031 Research Brief

**Type**: EXPLORATION (5th symbol, n-aware audit, structural fix)
**Track**: v2 — reduce concentration via dilution
**Parent baseline**: iter-v2/029 (forced reset)
**Date**: 2026-04-15
**Researcher**: QR (autopilot)
**Branch**: `iteration-v2/031` on `quant-research`

## Section 0: Data Split

```
OOS_CUTOFF_DATE = 2025-03-24    ← FIXED. NEVER CHANGES.
```

## Motivation — iter-030's findings

iter-v2/030's audit revealed structural concentration:
- 0/10 seeds passed the 50% concentration rule
- 7/10 seeds dominated by XRP
- 3/10 seeds distressed (negative total OOS PnL with XRP still dominant by positive-total)
- XRP's "real" concentration (by weighted_pnl) was 69.47% on primary seed,
  not 60.86% as reported via per_symbol.csv

The root cause: **the portfolio is really a 2-symbol (XRP+NEAR) strategy
with DOGE/SOL as random filler**. Adding more dimensions should mechanically
reduce concentration by giving the dominant symbols a larger denominator.

## Hypothesis

Adding ADAUSDT as a 5th model (Model I) will:

1. **Dilute concentration**: with 5 symbols, the perfect-diversification
   share is 20% per symbol. The n-symbol-aware rule for n=5 is max ≤ 40%.
2. **Add signal**: ADA is a major L1/payment token with ~6 years of 8h
   history; likely to contribute meaningful trades rather than noise.
3. **Not break the existing 4-model setup**: iter-031 is additive, not
   replacement, so models E/F/G/H continue producing identical trades.

The user's directive ("YES, adapt per symbol the skill") also pushes
the concentration rule to be n-symbol-aware in the skill itself.

## Changes vs iter-029/030

1. **ADAUSDT added** as 5th symbol (Model I) to `V2_MODELS` in
   `run_baseline_v2.py`.
2. **ADAUSDT features regenerated** with iter-026 BTC cross-asset
   features (the previous ADA parquet was from before iter-026 and
   was missing btc_ret_3d etc.).
3. **Audit metric fixed**: switched to **positive-total share**
   (`max(0, sym_wpnl) / sum(max(0, s_wpnl) for s)`). Always in [0, 1].
   The previous total-based metric produced nonsensical >100% shares
   on distressed seeds.
4. **Distressed-seed flag**: seeds with `total_oos_wpnl ≤ 0` or
   `|total_oos_wpnl| < 10.0` are flagged. Rule: ≤ 2 of 10 distressed.
5. **n-symbol-aware thresholds**: the audit now reads `len(V2_MODELS)`
   and picks the rule row for that n. n=5: max ≤ 40%, mean ≤ 35%,
   ≤1 seed above 32%, distressed ≤ 2.
6. **Skill file updated**: new "n-symbol-aware concentration thresholds"
   table plus documentation of the weighted_pnl vs net_pnl_pct
   discrepancy and the distressed-seed handling.

## Section 6: Risk Management Design

Same 7 active gates (vol-scale, ADX, Hurst, z-score OOD, low-vol,
hit-rate, BTC trend). ADA inherits all of them automatically via
`RiskV2Wrapper`.

### Pre-registered failure-mode prediction

**Most likely failure mode**: adding ADA pulls XRP's share below 50%
(success on the old rule) but stays above 40% (failure on the new n=5
rule). Range 40-50% on primary seed, similar distribution across
seeds. Distressed-seed count stays around 2-3 out of 10 due to seed
1001's persistent failure.

**Less likely but possible**: ADA itself doesn't contribute much
(trades but low Sharpe), acting as another DOGE/SOL-like filler. In
that case concentration doesn't change much.

**Pre-registered OOS mean**: roughly +0.95 to +1.10 monthly. ADA
should slightly improve overall because the model gets another real
symbol to trade.

## Success criteria

**Gating** (required for MERGE):
- Seed concentration audit passes n=5 thresholds:
  - Per-seed max ≤ 40%
  - Mean max-share ≤ 35%
  - ≤1 seed above 32%
  - ≤2 distressed seeds
- Mean OOS monthly > +0.80
- ≥8/10 profitable seeds
- OOS PF > 1.2

**Non-gating** (directional):
- Mean IS monthly > +0.50
- Primary seed XRP share < 50% (improvement direction)
- ADA contributes positive OOS PnL

## Exploration/Exploitation

**Exploration** — new symbol, new audit metric, new thresholds. First
exploration iter after the iter-029 baseline reset.
