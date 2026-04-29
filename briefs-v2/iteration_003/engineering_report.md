# Iteration v2/003 Engineering Report

**Type**: EXPLOITATION (single-symbol ATR multiplier specialization)
**Role**: QE
**Date**: 2026-04-13
**Branch**: `iteration-v2/003` on `quant-research`
**Parent baseline**: iter-v2/002 (OOS Sharpe +1.17, weighted, seed 42)
**Decision (from Phase 7)**: **NO-MERGE** — pre-registered failure mode
confirmed, DOGE IS-overfits with wider barriers

## Run Summary

| Item | Value |
|---|---|
| Models | 3 (E=DOGE 4.0/2.0, F=SOL 2.9/1.45, G=XRP 2.9/1.45) |
| Architecture | Same as iter-v2/002 (individual single-symbol LightGBM, 24-mo WF) |
| Seeds | 1 (fail-fast; full 10-seed not run — see §Diagnosis) |
| Optuna trials/month | 10 |
| Wall-clock | ~200 s (single seed) |
| Output | `reports-v2/iteration_v2-003/` |

## Primary seed 42 — `comparison.csv`

| Metric | iter-v2/002 | iter-v2/003 | Δ |
|---|---|---|---|
| IS Sharpe | +0.538 | **+0.449** | **−0.09** |
| OOS Sharpe | **+1.172** | **+0.845** | **−0.33** |
| OOS Sortino | +1.471 | +1.000 | −0.47 |
| IS MaxDD | 68.80% | **102.20%** | **+33.4 pp (worse)** |
| OOS MaxDD | 54.63% | 50.10% | −4.5 pp |
| IS WR | 41.2% | 42.9% | +1.7 pp |
| OOS WR | 40.3% | 39.7% | −0.6 pp |
| OOS PF | 1.294 | 1.212 | −0.08 |
| OOS trades | 139 | 126 | −13 |
| OOS net PnL | +60.58% | +42.25% | −18.3 pp |
| DSR z (OOS) | +8.34 | +11.85 | — (both strong at N=2-3) |

**OOS Sharpe fails the primary metric**: +0.85 < +1.17 baseline. This is a
**step backward** of 0.33 Sharpe units.

## Per-symbol comparison — the DOGE IS-overfit signal

**DOGEUSDT (ATR multipliers widened 2.9/1.45 → 4.0/2.0)**:

| Metric | iter-v2/002 | iter-v2/003 | Δ |
|---|---|---|---|
| **IS** trades | 139 | 107 | −32 |
| **IS** WR | 42.4% | **48.6%** | **+6.2 pp** |
| **IS** raw PnL | +55.97% | **+86.80%** | **+30.83 pp (+55% relative)** |
| **IS** avg PnL/trade | +0.40% | **+0.81%** | **2.0×** |
| **OOS** trades | 47 | 34 | −13 |
| **OOS** WR | 38.3% | 35.3% | **−3.0 pp** |
| **OOS** raw PnL | −24.02% | **−32.14%** | **−8.12 pp (worse)** |
| **OOS** avg PnL/trade | −0.51% | **−0.95%** | **−87%** |

This is the **textbook IS-overfit pattern** that was pre-registered as
the most likely failure mode in the research brief. DOGE IS jumps by
nearly 2× per-trade while DOGE OOS gets WORSE per-trade by 87%.

**SOLUSDT**: 50 OOS trades, +25.65% raw — **byte-for-byte identical** to
iter-v2/002. Gate stats exactly match (`signals_seen=2515, kill_rate=47.3%`).
The one-variable isolation held: only DOGE changed, SOL/XRP are unchanged.

**XRPUSDT**: 42 OOS trades, +37.56% raw — **byte-for-byte identical** to
iter-v2/002. Same gate stats.

The aggregate OOS deterioration is entirely driven by DOGE's −8.12 pp
OOS PnL regression combined with DOGE's reduced trade count (47 → 34).
Fewer trades at worse per-trade expectancy.

### Why DOGE IS improved but OOS didn't

Two plausible mechanisms:

1. **Training-period regime mismatch**: 2020-2024 IS DOGE had several
   large meme runs (especially 2020-2021). Wider ATR barriers captured
   more of those moves (+30.83 pp IS PnL improvement). 2025-H2 OOS DOGE
   is in a choppier lower-momentum regime where wider barriers let
   losing trades run longer without cutting.

2. **Labeling shift**: widening the SL from 1.45×NATR to 2.0×NATR
   rebalances the triple-barrier labels — more training samples now
   label as "longs hit TP" because the expanded SL gives price more
   room to bounce. This creates a biased training distribution that
   doesn't match the OOS distribution.

Either way, the wider barriers are net negative for DOGE OOS.

## Why the 10-seed validation was skipped

Per the v2 skill §Seed Robustness Validation, 10-seed MERGE validation
is **mandatory before merging**, not before rejecting. The decision to
NO-MERGE is made on the primary-seed result because:

1. **Primary metric fails by 0.33 Sharpe** — a substantial gap, well
   above the noise floor of ~0.20 seen in iter-v2/002's 10-seed std.
2. **The failure pattern is pre-registered** — DOGE IS raw PnL jumped
   +55% relative while DOGE OOS got worse. The hypothesis is directionally
   wrong, not a seed artifact.
3. **Seed 42 is typically median** — in iter-v2/002's 10-seed sweep, seed
   42's OOS Sharpe was +1.17 and the mean was +0.96, so seed 42 was
   slightly ABOVE the mean. If seed 42 is already below baseline here,
   the 10-seed mean is very likely to be even lower.
4. **Compute budget discipline** — 40 min of compute to confirm a
   clearly-wrong hypothesis is wasteful. iter-v2/004 has a more promising
   variable (the low-vol filter) and should be prioritized.

## Hard Constraints

| Constraint | Target | Actual | Pass? |
|---|---|---|---|
| **Primary: OOS Sharpe > +1.17** | +1.17 | **+0.845** | **FAIL** |
| OOS trades ≥ 50 | 50 | 126 | PASS |
| OOS PF > 1.1 | 1.1 | 1.212 | PASS |
| No single symbol > 50% OOS PnL | ≤50% | XRP 121%, DOGE −103% | **FAIL** (worse concentration than iter-v2/002) |
| DSR > +1.0 | +1.0 | +11.85 | PASS (but misleading — low N) |
| IS/OOS Sharpe ratio > 0.5 | 0.5 | 1.88 | PASS |

Primary fails. Concentration also worse (DOGE as a bigger drag makes
the signed ratio more skewed).

## Pre-registered failure-mode prediction — validated

The brief §6.3 predicted: "DOGE IS raw PnL jumps substantially (e.g.,
+55.97% → +80%+) while DOGE OOS stays negative or worsens. The signal
would be a DOGE IS WR rise of +5pp or more with flat/worse OOS WR."

**Actual**: DOGE IS raw PnL rose from +55.97% to +86.80% (+55% relative,
within the predicted range). DOGE IS WR rose +6.2 pp (matching the "≥5pp"
prediction). DOGE OOS WR DROPPED by 3 pp (matching "flat/worse"). DOGE
OOS raw PnL got worse (−24.02% → −32.14%).

The failure mode was correctly anticipated. This is strong evidence that
the DOGE-multiplier-widening hypothesis is directionally wrong for OOS —
not a noise artifact.

## Artifacts

- `reports-v2/iteration_v2-003/comparison.csv`
- `reports-v2/iteration_v2-003/{in_sample,out_of_sample}/{quantstats.html, trades.csv, per_symbol.csv}`
- `reports-v2/iteration_v2-003/seed_summary.json` (1 entry, primary seed only)

## Label Leakage Audit

- CV gap: `(10080/480 + 1) × 1 = 22` rows per model (unchanged)
- Walk-forward: unchanged
- Feature isolation: unchanged (no v1 imports into `features_v2/`)
- Symbol exclusion: unchanged
- DOGE's label computation uses the new multipliers correctly (verified
  by the DOGE IS PnL shift — wider SL would not produce different labels
  unless the backtest engine reads the multipliers correctly)

No leakage detected.

## Conclusion

iter-v2/003's single variable change (DOGE ATR multipliers 2.9/1.45 →
4.0/2.0) produces the **pre-registered failure mode**: DOGE IS PnL jumps
+55% relative while DOGE OOS gets worse by 87% per-trade. Aggregate OOS
Sharpe drops from baseline +1.17 to +0.85. **NO-MERGE**.

The widening hypothesis is wrong for OOS DOGE. iter-v2/004 should try
option 2 from the iter-v2/001 diary: **replace DOGE with NEARUSDT**.
NEAR is the fourth-strongest screening candidate (v1 corr 0.665,
~4,847 IS rows, $240M daily volume) and preserves portfolio diversity
without the meme-specific labeling mismatch.

Alternative: skip the DOGE fix entirely and take the concentration
caveat — move on to iter-v2/004's **low-vol filter** (the Priority 2
item from the iter-v2/002 diary), which targets the low-vol trending
bucket with weighted Sharpe −1.86. That's structurally cleaner and
doesn't fight with DOGE's dynamics at all.

**Recommendation**: iter-v2/004 = low-vol filter. iter-v2/005 = DOGE
replacement with NEAR if the concentration caveat is still material
after the low-vol filter lands.
