# iter-v2/070 Diary

**Date**: 2026-04-24
**Type**: EXPLORATION (bold: 2 new feature families)
**Parent baseline**: iter-v2/069
**Decision**: **NO-MERGE** — OOS −38%, MaxDD +73%, new features added noise

## Summary

BOLD exploration: added `liquidity_impact_20` + `return_zscore_20`
(34 → 36 features). Pre-registered failure signature was "OOS monthly
< +1.79 → NO-MERGE". Actual OOS monthly +1.30 (−38% vs baseline +2.108).

## What I got wrong

I trusted univariate Spearman rho too much. `return_zscore_20` had
rho = −0.027 on 3-bar forward returns (2nd strongest after fracdiff).
I concluded it was a strong feature. But univariate predictive power
is a CRUDE metric — it doesn't measure whether the new feature ADDS
information given the existing features.

Turns out `return_zscore_20` correlated 0.27 with `vwap_dev_20` and
0.14 with `btc_ret_3d`. Not redundant on the 0.85 threshold, but
enough that the model wasted colsample picks on it when it already
had similar signal from other features.

Similar for `liquidity_impact_20` (correlated 0.79 with
`parkinson_gk_ratio_20`).

## Pattern vs iter-v2/069

- **iter-v2/069 PRUNING** (34 → 34, drop 6 near-identical): OOS +27%, MERGE.
- **iter-v2/070 ADDING** (34 → 36, add 2 uncorrelated-to-each-other-but-
  correlated-to-existing): OOS −38%, NO-MERGE.

**Empirical rule emerging**: for this ensemble architecture, LESS is MORE.
Prune redundant features (iter-v2/069 win). Don't add features unless
you have strong evidence they carry independent signal (iter-v2/070 loss).

## MERGE criteria

| # | Criterion | Target | Actual | Pass |
|---|---|---|---|---|
| 1 | Combined monthly ≥ 2.98 | ≥ 2.98 | 2.03 | FAIL |
| 2 | OOS monthly ≥ 1.79 | ≥ 1.79 | 1.30 | FAIL |
| 3 | IS monthly ≥ 0.74 | ≥ 0.74 | 0.73 | FAIL |
| 4 | OOS MaxDD ≤ 22.6% | ≤ 22.6% | 32.61% | FAIL |
| 5 | PF>1, trades>=50, SR>0 | — | 1.70, 51, +1.40 | PASS |
| 6 | Concentration outer ≤50% | — | 40.60% | PASS |
| 7 | Concentration inner ≤40% | ≤40% | 40.60% | FAIL |

6 FAILs. **NO-MERGE.** Cherry-pick docs only. Feature code stays on
iteration-v2/070 branch.

## Next Iteration Ideas — iter-v2/071

### Primary: BTC trend filter tightening (IS-informed EXPLOITATION)

From iter-v2/068 QR analysis, the 2024-11 disaster (16 shorts, all
losing, −33.22 wpnl) was partially caught by BTC trend filter (8 of 16
zeroed). The 8 that SURVIVED had BTC 14d return between +3.2% and
+19.74% — below the current 20% threshold. Tighter threshold could
catch more.

**Proposal**: BTC_TREND_CONFIG.threshold_pct 20.0 → 12.0.

Forecast:
- Saves ~−20 wpnl in Nov 2024 (the surviving 8 shorts)
- Will also kill some trades in other months
- Net effect unknown without run

This is EXPLOITATION (tuning existing gate) not EXPLORATION (new
architecture). Fine — iter-v2/069 and iter-v2/070 satisfied the
bold-idea quota.

### Alternative: SHAP-based feature replacement

Train one baseline model, extract SHAP values, identify weak features
(low SHAP importance), replace with candidates. Better than blind
addition (iter-v2/070's mistake). Requires infrastructure — save for
iter-v2/072.

### Alternative: ATR labeling tuning

Current: `atr_tp_multiplier=2.9, atr_sl_multiplier=1.45` (inherited
from v1's Model A). Could try different TP/SL ratios. Low-risk
EXPLOITATION. Save for after iter-v2/071.

**Recommended iter-v2/071**: BTC trend filter 20% → 12%. Single
variable change with specific IS-derived hypothesis.
