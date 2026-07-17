# team-05 IS report — CANONICAL (numbers from `cli.py team-run`, `out/is_metrics.json`)

Active family: **t05-volume-liquidity-anomalies-v1** (menu #6; pivot from falsified
t05-lowvol-bab-v1, orchestrator-approved redirect after the STR veto — see Appendix A).

The headline metrics below are the canonical `cli.py team-run --team team-05` output
(`out/is_metrics.json`, both cost tiers), which reproduces the exp-016 research artifact
(`out/scratch/results_b5_amihud_divergence.json`) BIT-IDENTICALLY: @1× Sharpe
0.3500406620057439, @2× Sharpe 0.3423412001392022, maxDD −0.4286333053055349, ann turnover
0.9151988641888337, breadth 24/24, mean_net −2.3e-19, mean_gross 1.0. The QE's built
`strategy.py` (Amihud K=252 rank book) is the source; the family experiment table below is
evaluator output archived in `out/scratch/results_b4_abnvol_anchor.json`,
`results_b5_amihud_divergence.json`, `results_b6_amihud_refine.json`. No number in this
report exists outside those artifacts.

## Selected configuration (research_brief.md FINAL SPEC)

Amihud illiquidity rank book: `illiq = mean_252(|ret| / dollar_volume)` (min 126 valid days),
long illiquid / short liquid, centered cross-sectional ranks, no tranching, no overlays.

| Metric (exp-016 artifact) | @1× cost | @2× cost |
|---|---|---|
| net IS Sharpe (monthly, √12) | **+0.350** | **+0.342** |
| maxDD | −0.429 | −0.429 |
| ann turnover | 0.9 | 0.9 |
| median names long/short | 24 / 24 | 24 / 24 |
| mean net / mean gross | −0.000 / 1.000 | −0.000 / 1.000 |
| regime Sharpe bull / bear / chop | +0.410 / +0.593 / −0.178 | — |

Diagnostics (computed from the evaluator net series with approved `ct.msharpe`; labeled
diagnostics, not headline metrics): 2010→2015 sub-Sharpe +0.255; 2015→2024H1 +0.397;
melt-up core 2020-04→2021-02 +1.664; β(net, EW-market) +0.18.

## Family experiment table (11 material experiments, exp-011…exp-021)

| exp | config | Sharpe@1× | Sharpe@2× | maxDD@1× | turn | verdict |
|---|---|---|---|---|---|---|
| 011 | abn_vol W60 F5 H10 long-high | −0.153 | −0.467 | −0.739 | 37.8 | dead |
| 012 | abn_vol H5 | −0.327 | −0.793 | −0.818 | 54.0 | dead |
| 013 | abn_vol H20 | −0.224 | −0.444 | −0.740 | 26.2 | dead |
| 014 | abn_vol F1 H10 | −0.239 | −0.658 | −0.794 | 53.2 | dead |
| 015 | Amihud K=126 rank | +0.272 | +0.258 | −0.447 | 1.7 | plateau |
| 016 | **Amihud K=252 rank** | **+0.350** | **+0.342** | **−0.429** | **0.9** | **SELECTED (plateau center)** |
| 017 | divergence D20 H10 | −0.373 | −0.675 | −0.638 | 29.8 | dead |
| 018 | divergence D60 H10 | −0.533 | −0.710 | −0.758 | 16.8 | dead |
| 019 | Amihud K=504 rank | +0.246 | +0.240 | −0.452 | 0.6 | plateau |
| 020 | inverse-$-volume control | +0.115 | +0.109 | −0.585 | 0.7 | isolation control |
| 021 | Amihud K=252 quantile 15/15 | +0.281 | +0.272 | −0.406 | 1.0 | fails adoption rule |

Negative results reported with the same precision as positive ones: two of three seeded
sub-mechanisms (abnormal-volume attention, volume-price divergence) are dead on this
universe at these costs; no sign flip was run or claimed for either (pre-registered sign
discipline). The surviving Amihud branch shows an all-positive plateau across K ∈
{126, 252, 504} at BOTH cost tiers; selection took the plateau center, not a peak. The
isolation control (exp-020) shows the |ret|/$vol numerator matters: static size alone earns
a third of the Sharpe and is negative pre-2015.

Honest caveats: quasi-static long-illiquid/short-mega book; β(net,mkt) ≈ +0.18; weak in
chop (−0.18); melt-up-loving (+1.66 in 2020–21 core). Modest edge, near-total cost
immunity (1×→2× loses 0.008 Sharpe), breadth 24/24 vs floor 5.

Budget: 21/40 material experiments used (10 lowvol + 11 volume family) + 4
registration/pivot lines.

---

## Appendix A — falsified primary family t05-lowvol-bab-v1 (10 experiments, exp-001…010)

Pre-registered kill (a) fired: every config negative at both tiers. Best config: canonical
Frazzini–Pedersen beta-sort with leg-balancing, Sharpe −0.031 @1× / −0.070 @2×, maxDD
−0.637. Full table and autopsy preserved in `research_brief.md` (FALSIFICATION VERDICT) and
`out/scratch/results_b1_lookback_plateau.json`, `results_b2_bab_balance.json`,
`results_b3_infamily_closure.json`. Key findings: plain book is a disguised short-market
position (β ≈ −0.30); the |net| ≤ 0.25 cap makes beta-neutrality structurally unreachable
(residual β ≈ −0.15…−0.20); cap-feasible alpha remainder negative post-2015 in all variants.
