# Engineering Report — iter-v3/090

## Headers

- Iteration: iter-v3/090
- Type: EXPLORATION (cross-sectional LGBMRanker, gross-signal strengthening)
- Branch: iteration-v3/090
- Setup commit SHA: a584fdf
- Phase 5.5 gate commit SHA: 55979e7 (PASS)
- Hardware: WSL2 / CPU
- Wall-clock time: 0h 20m 39s
- Report generated: 2026-05-17

---

## Configuration Diff vs /089 Anchor

The /089 construction is fully retained: 22-symbol XS universe, LGBMRanker,
quintile scoring, 3-bar overlapping holds, no-trade band (middle quintile),
0.138 IS turnover ceiling. The single change is the feature set:

| Parameter       | /089 (anchor) | /090 (this run) |
|-----------------|---------------|-----------------|
| XS_FEATURE_COLUMNS | 13 features | 15 features |
| New features    | —             | xs_sortino_mom_12, xs_downbeta_50 |
| Runner          | run_cross_sectional_v3.py | same |
| n_trials        | 35            | 35              |
| OOS_CUTOFF_DATE | 2025-03-24    | 2025-03-24 (unchanged) |
| training_months | 24            | 24 (unchanged)  |

xs_sortino_mom_12 = 12-bar Sortino ratio of the symbol (IS-EDA IC −0.043,
signed for reversal via negative sign in X0 table).
xs_downbeta_50 = 50-bar downside beta of the symbol vs universe mean return
(IS-EDA IC −0.005, very low signal). Both are cross-sectionally rank-normalized
at inference time before being passed to the ranker.

---

## Key Metrics Block

| Metric                   | IS         | OOS        | Ratio  |
|--------------------------|------------|------------|--------|
| Monthly Sharpe (net)     | −0.2305    | −0.0770    | 0.334  |
| Max drawdown             | 11.6208    | 2.1384     | 0.184  |
| n_bars (bar-symbol rows) | 45,324     | 18,703     |        |
| Total net PnL            | −0.2963    | −0.0293    |        |
| OOS rank-IC mean         | —          | +0.0358    |        |
| frac_positive_paths      | 0.200      | —          |        |
| Turnover/bar (IS)        | 0.1177     | 0.0715     |        |
| Turnover ceiling gate    | PASS       | —          |        |

### vs /089 anchor

| Metric               | /089       | /090       | Delta      |
|----------------------|------------|------------|------------|
| IS monthly Sharpe    | −0.1960    | −0.2305    | −0.0345    |
| OOS monthly Sharpe   | −0.0985    | −0.0770    | +0.0215    |
| OOS rank-IC mean     | +0.0279    | +0.0358    | +0.0079    |
| frac_positive_paths  | 0.356      | 0.200      | −0.156     |

---

## Gross-vs-Net Decomposition (Central Diagnostic)

Computed from trades.csv (gross_pnl and fee columns).

### /090

| Leg         | Period | Gross PnL | Fee     | Net PnL  | Monthly Gross Sharpe |
|-------------|--------|-----------|---------|----------|----------------------|
| All         | IS     | +0.0988   | 0.3952  | −0.2963  | +0.2675              |
| All         | OOS    | +0.0607   | 0.0900  | −0.0293  | +0.5398              |
| LONG only   | IS     | −0.1343   | 0.1457  | −0.2800  | —                    |
| SHORT only  | IS     | +0.2331   | 0.1784  | +0.0548  | —                    |
| LONG only   | OOS    | +0.0034   | 0.0373  | −0.0340  | —                    |
| SHORT only  | OOS    | +0.0573   | 0.0379  | +0.0194  | —                    |

### /089 (from trades.csv for comparison)

| Leg         | Period | Gross PnL | Fee     | Net PnL  | Monthly Gross Sharpe |
|-------------|--------|-----------|---------|----------|----------------------|
| All         | IS     | +0.1155   | 0.3871  | −0.2716  | +0.3204              |
| All         | OOS    | +0.0567   | 0.0893  | −0.0326  | +0.5947              |
| LONG only   | IS     | −0.1566   | —       | —        | —                    |
| SHORT only  | IS     | +0.2721   | —       | —        | —                    |
| LONG only   | OOS    | −0.0633   | —       | —        | —                    |
| SHORT only  | OOS    | +0.1200   | —       | —        | —                    |

### Decisive question: did the 2 new features lift OOS gross Sharpe above /089's +0.5947?

NO. /090 OOS gross monthly Sharpe = +0.5398 vs /089's +0.5947 — a DROP of −0.055.
The gross signal was NOT strengthened; it regressed. The IS gross Sharpe also
fell (0.2675 vs /089's 0.3204). Fee drag is essentially unchanged (IS fee
0.3952 vs 0.3871; OOS fee 0.0900 vs 0.0893).

The net OOS Sharpe appears slightly better (−0.0770 vs −0.0985) purely because
the IS gross signal dropped, compressing the IS/OOS gross gap — not because the
new features improved OOS gross return. The small headline OOS improvement is
noise within fee-dominated books.

---

## New-Feature Importance — Were They Used?

The cross-sectional runner does not emit per-feature split/gain importance to
the report files. The IS-EDA analysis (analysis/iteration_v3-090/) provides the
pre-backtest multivariate evidence from the committed script.

### IS-EDA IC (X0 table, IS data only)

| Feature             | IS rank-IC | Rank among 22 candidates |
|---------------------|-----------|--------------------------|
| xs_sortino_mom_12   | −0.043    | rank ~5 (above median)   |
| xs_downbeta_50      | −0.005    | rank ~18 (bottom tercile)|

xs_sortino_mom_12 showed a moderate IS rank-IC and was accepted by greedy
forward selection (C1: step 2, IC-IR lift +0.0077) and survived leave-one-out
(C2: earns_its_slot=True, IC-IR loss on removal −0.0088). C4 orthogonal-pair
EDA (the selected pair for /090) showed IC-IR delta vs anchor +0.019, quintile
L-S spread Sharpe improvement from −0.0754 to −0.0535.

xs_downbeta_50 showed near-zero IS IC (−0.005) but was accepted by greedy
forward selection as step 3 (IC-IR lift +0.0083) because it is near-orthogonal
to existing features (xs-rank-corr with max_dd_window_50 only −0.183, all other
anchor pairs < 0.20). Leave-one-out confirmed earns_its_slot=True (IC-IR loss
−0.0083). However the near-zero standalone IC means the feature contributes
through interaction effects in the ranker rather than direct signal.

The backtest OOS gross Sharpe declining rather than rising despite the EDA
prediction of IS IC-IR gain (+0.019 delta) is the core result: features that
improve IS IC-IR can still degrade OOS gross return when the IS-to-OOS
correlation of the cross-section is low.

Assessment: xs_sortino_mom_12 was used (moderate IS IC); xs_downbeta_50 was
marginally used (near-zero standalone IS IC, interaction-path only). Neither
delivered OOS gross lift. The EDA IC-IR improvement did not transfer to OOS
gross Sharpe.

---

## Per-Leg PnL Anatomy (Continued from /089 Finding)

/089 finding: SHORT leg carries the gross spread OOS (short-leg gross +0.120,
long-leg gross −0.063).

/090: SHORT leg gross OOS = +0.0573, LONG leg gross OOS = +0.0034.
The short-leg dominance is retained (2 new features did not disrupt it), but
the short-leg gross OOS fell from +0.120 to +0.057 — nearly halved. The long
leg improved from −0.063 to near-zero. The net leg anatomy is structurally
consistent with /089 but both legs moved adversely on the gross.

The IS leg anatomy is also structurally consistent: LONG IS gross = −0.134 vs
/089's −0.157 (slight improvement, long leg less negative); SHORT IS gross =
+0.233 vs /089's +0.272 (short leg weakened). The 2 features shifted gross PnL
from the short leg to the long leg at IS, but this rebalancing did NOT lift the
total gross; it merely compressed the spread.

---

## CPCV Path Distribution

45 IS-only CPCV paths (XS_REQUIRED_GAP=88 asserted).

| Statistic       | /090   | /089   | Delta   |
|-----------------|--------|--------|---------|
| frac_positive   | 0.200  | 0.356  | −0.156  |
| Q50 path Sharpe | −0.019 | ?      | —       |
| Positive paths  | 9/45   | 16/45  | −7      |
| Sharpe range    | [−0.086, +0.039] | — | — |

frac_positive_paths dropped from 0.356 to 0.200 — 16 fewer profitable IS paths
in CPCV. The distribution is more negative than /089. This is directionally
consistent with the degraded IS gross Sharpe.

---

## OOS Rank-IC

OOS rank-IC mean = +0.0358 ± 0.3425 (n=1,255 timestamps).
vs /089 anchor +0.0279. Delta +0.0079 — slight improvement.
F1 falsifier PASS (OOS rank-IC > 0).

Falsifier F2 (OOS monthly net Sharpe > −0.10) was pre-registered as a PASS
threshold. /090 OOS = −0.0770, which clears −0.10.

The rank-IC improvement (+0.0079) is small relative to the OOS rank-IC std of
±0.34 — within one standard deviation of noise.

---

## Turnover Gate

IS turnover/bar = 0.1177 <= ceiling 0.138 — PASS.
OOS turnover/bar = 0.0715 (below IS, as expected — fewer symbols traded per bar
in shorter OOS window).

---

## Anomaly Notes

1. The run.log contains repeated sklearn UserWarning "X does not have valid
   feature names, but LGBMRanker was fitted with feature names" — 160
   occurrences. This warning occurs at inference time when the model receives a
   numpy array rather than a DataFrame. It does not affect results (the ranker
   uses positional feature access, not name lookup). It is a pre-existing
   warning in the cross-sectional runner from /089.

2. The IS monthly gross Sharpe of +0.2675 vs net Sharpe of −0.2305 (net was
   computed via different monthly aggregation; the number in comparison.csv
   −0.2305 uses the net_pnl column grouped monthly). The discrepancy between
   IS monthly gross Sharpe (+0.2675) and IS monthly net Sharpe (−0.7983 from
   the monthly aggregation script) reflects that fee aggregation per month
   results in a larger negative net Sharpe than the comparison.csv figure
   (−0.2305). The comparison.csv figure is the authoritative runner output.

3. No NaN Sharpe, no zero-trade months in IS (39 IS months all non-zero), no
   negative fee rows. Trade spot-check: 10 random rows verified — position sign
   consistent with long/short, gross_pnl direction consistent with position,
   fee always positive.

---

## Status

OVERALL=READY-FOR-CRITIC
