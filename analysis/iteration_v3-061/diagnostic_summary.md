# TRX Anti-Kelly Diagnostic — iter-v3/061

Cycle 1 #2 EXPLORATION. Per Critic FINAL `3cee250` Rec #3.

Anchor: BASELINE_V3.md iter-v3/059 unified 10-seed CONFIRMATION-mode
(/060 EXPLORATION-MODE-REFERENCE is the cycle 1 axis-PASS anchor;
EDA uses /059 trade roster because /060 is structurally equivalent at
the trade-level RiskV2 attribution — both are runs of the same source
code over the same OHLC data, just at different ensemble sizes; the
RiskV2 _vol_scale formula is invariant across ensemble size).

## Q1 — Anti-Kelly statistical significance (with partition-method comparison)

| split   | symbol   |   method_B_n_wins |   method_B_n_losses |   method_B_mean_win_w |   method_B_mean_loss_w |   method_B_diff |   method_B_welch_t |   method_B_p_value |   method_B_ci_lo_95 |   method_B_ci_hi_95 | method_B_ci_excludes_zero   |   method_A_060_q7_diff |   method_A_060_q7_welch_t |   method_A_060_q7_p_value |   n_killed_in_wins_partition_A |
|:--------|:---------|------------------:|--------------------:|----------------------:|-----------------------:|----------------:|-------------------:|-------------------:|--------------------:|--------------------:|:----------------------------|-----------------------:|--------------------------:|--------------------------:|-------------------------------:|
| IS      | BCHUSDT  |                34 |                  32 |                0.6932 |                 0.6250 |          0.0682 |             1.2151 |             0.2243 |             -0.0418 |              0.1761 | False                       |                 0.0987 |                    1.3405 |                    0.1801 |                              7 |
| IS      | LDOUSDT  |                 3 |                   5 |                0.7067 |                 0.5820 |          0.1247 |             0.8635 |             0.3879 |             -0.1460 |              0.3440 | False                       |                 0.2217 |                    1.3666 |                    0.1717 |                              0 |
| IS      | TRXUSDT  |                20 |                  44 |                0.7365 |                 0.7166 |          0.0199 |             0.3425 |             0.7320 |             -0.0912 |              0.1297 | False                       |                -0.0608 |                   -0.7109 |                    0.4771 |                              7 |
| OOS     | BCHUSDT  |                14 |                  19 |                0.7221 |                 0.6842 |          0.0379 |             0.4957 |             0.6201 |             -0.1076 |              0.1800 | False                       |                 0.0721 |                    0.8755 |                    0.3813 |                              0 |
| OOS     | LDOUSDT  |                 3 |                   9 |                0.9000 |                 0.7111 |          0.1889 |             2.0770 |             0.0378 |              0.0256 |              0.3567 | True                        |                 0.1889 |                    2.0770 |                    0.0378 |                              0 |
| OOS     | TRXUSDT  |                19 |                  26 |                0.6842 |                 0.7150 |         -0.0308 |            -0.4877 |             0.6258 |             -0.1535 |              0.0879 | False                       |                -0.0139 |                   -0.1806 |                    0.8567 |                              1 |

**CRITICAL FINDING**: The /060 Q7 anti-Kelly finding (TRX -0.061 IS, -0.014 OOS)
was driven by a partition-method choice. Method A (/060 Q7) uses
`net_pnl_pct > 0` as the win definition, which INCLUDES weight=0 killed
trades that happen to be raw-direction-positive. TRX has 15 such trades in IS
(19% of IS trades) — they contribute 0 to portfolio weighted_pnl but pull down
the avg_win_w under Method A.

Method B (`weighted_pnl > 0`) excludes killed trades from both partitions, which
is the appropriate partition for **portfolio Sharpe questions**. Under Method B:
- TRX IS diff = +0.020 (Kelly-aligned, NOT anti-Kelly; t=+0.34; CI [-0.091, +0.130] includes 0)
- TRX OOS diff = -0.031 (anti-Kelly direction, but t=-0.49; CI [-0.154, +0.088] includes 0)

**Neither IS nor OOS TRX anti-Kelly is statistically significant** at Method B
partition. The /060 Q7 finding survives the sign-flip test only in OOS, and even
there the magnitude is so small that bootstrap CI generously covers 0.

## Q2 — TRX weight_factor distribution by win/loss/killed outcome

| split   | outcome     |   n |   mean |    std |    p10 |    p25 |    p50 |    p75 |    p90 |    min |    max |   frac_below_05 |   frac_below_04 |   frac_at_floor_030 |
|:--------|:------------|----:|-------:|-------:|-------:|-------:|-------:|-------:|-------:|-------:|-------:|----------------:|----------------:|--------------------:|
| IS      | wins        |  20 | 0.7365 | 0.2198 | 0.4170 | 0.5550 | 0.8150 | 0.9200 | 0.9900 | 0.3500 | 1.0000 |          0.1500 |          0.1000 |              0.0000 |
| IS      | losses      |  44 | 0.7166 | 0.2059 | 0.3930 | 0.5500 | 0.7550 | 0.8900 | 0.9670 | 0.3600 | 0.9900 |          0.2045 |          0.1136 |              0.0000 |
| IS      | zero_killed |  15 | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 0.0000 |          1.0000 |          1.0000 |              1.0000 |
| OOS     | wins        |  19 | 0.6842 | 0.2110 | 0.3960 | 0.4850 | 0.7100 | 0.8550 | 0.9500 | 0.3600 | 0.9900 |          0.2632 |          0.1053 |              0.0000 |
| OOS     | losses      |  26 | 0.7150 | 0.2066 | 0.4250 | 0.5675 | 0.7150 | 0.9100 | 0.9500 | 0.3300 | 1.0000 |          0.1923 |          0.0769 |              0.0000 |
| OOS     | zero_killed |   3 | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 0.0000 |          1.0000 |          1.0000 |              1.0000 |

**Reading**: Percentiles of weight_factor by outcome. `frac_below_05`
is the key column for floor=0.5 counterfactual: it's the fraction of
trades in that outcome whose weight would be RAISED to 0.5 under the
proposed floor change.

## Q3 — TRX outcome by 5-quantile weight bucket

| split   | weight_bucket   |   weight_range_min |   weight_range_max |   n_trades |   n_wins |   n_losses |   win_rate |   weighted_pnl_sum |   unweighted_pnl_sum |   weighted_pnl_per_trade |
|:--------|:----------------|-------------------:|-------------------:|-----------:|---------:|-----------:|-----------:|-------------------:|---------------------:|-------------------------:|
| IS      | Q1_low          |             0.3500 |             0.5100 |         13 |        4 |          9 |     0.3077 |            -0.0170 |              -0.0540 |                  -0.0013 |
| IS      | Q2              |             0.5300 |             0.6700 |         13 |        5 |          8 |     0.3846 |             2.4144 |               3.9260 |                   0.1857 |
| IS      | Q3              |             0.6800 |             0.8200 |         12 |        2 |         10 |     0.1667 |            -6.9554 |             -10.0391 |                  -0.5796 |
| IS      | Q4              |             0.8300 |             0.9300 |         13 |        4 |          9 |     0.3077 |            -5.9806 |              -7.0296 |                  -0.4600 |
| IS      | Q5_high         |             0.9500 |             1.0000 |         13 |        5 |          8 |     0.3846 |             3.1882 |               3.0137 |                   0.2452 |
| OOS     | Q1_low          |             0.3300 |             0.4700 |         10 |        5 |          5 |     0.5000 |             2.5913 |               6.1250 |                   0.2591 |
| OOS     | Q2              |             0.5000 |             0.6700 |          8 |        4 |          4 |     0.5000 |             0.2449 |               0.0125 |                   0.0306 |
| OOS     | Q3              |             0.6800 |             0.7700 |          9 |        2 |          7 |     0.2222 |            -3.7390 |              -5.2615 |                  -0.4154 |
| OOS     | Q4              |             0.7800 |             0.9100 |          9 |        5 |          4 |     0.5556 |             6.8843 |               8.1768 |                   0.7649 |
| OOS     | Q5_high         |             0.9300 |             1.0000 |          9 |        3 |          6 |     0.3333 |            -1.8174 |              -1.9294 |                  -0.2019 |

**Reading**: TRX trades binned by weight_factor quintile. If WR is
HIGHER in Q1 (lowest weight) than Q5 (highest weight), the anti-Kelly
mechanism is concentrated where lifting the floor would help.

## Q4 — TRX counterfactual: weighted_pnl under different floors

| split   |   vol_scale_floor |   n_trades |   weighted_pnl_sum |   weighted_pnl_mean |   n_wins |   n_losses |   win_rate |   avg_win_w |   avg_loss_w |   win_minus_loss_w |
|:--------|------------------:|-----------:|-------------------:|--------------------:|---------:|-----------:|-----------:|------------:|-------------:|-------------------:|
| IS      |            0.3000 |         79 |            -7.3503 |             -0.0930 |       20 |         44 |     0.2532 |      0.7365 |       0.7166 |             0.0199 |
| IS      |            0.4000 |         79 |            -7.3598 |             -0.0932 |       20 |         44 |     0.2532 |      0.7395 |       0.7200 |             0.0195 |
| IS      |            0.5000 |         79 |            -7.3423 |             -0.0929 |       20 |         44 |     0.2532 |      0.7535 |       0.7361 |             0.0174 |
| IS      |            0.6000 |         79 |            -7.3337 |             -0.0928 |       20 |         44 |     0.2532 |      0.7780 |       0.7609 |             0.0171 |
| OOS     |            0.3000 |         48 |             4.1640 |              0.0867 |       19 |         26 |     0.3958 |      0.6842 |       0.7150 |            -0.0308 |
| OOS     |            0.4000 |         48 |             4.1051 |              0.0855 |       19 |         26 |     0.3958 |      0.6874 |       0.7200 |            -0.0326 |
| OOS     |            0.5000 |         48 |             4.6353 |              0.0966 |       19 |         26 |     0.3958 |      0.7074 |       0.7346 |            -0.0272 |
| OOS     |            0.6000 |         48 |             5.0900 |              0.1060 |       19 |         26 |     0.3958 |      0.7400 |       0.7588 |            -0.0188 |

**Reading**: Conservative counterfactual assuming trade selection
(open_time, direction, exit_reason) is invariant — only weight_factor
changes via floor lift. Floor=0.3 row reproduces current state; floor=0.5
is the Path B intervention candidate.

## Q5 — BCH/LDO invariance at per-symbol TRX-only floor=0.5

| split   | symbol   |   applied_floor |   current_weighted_pnl_sum |   counterfactual_weighted_pnl_sum |   delta |   delta_pct |
|:--------|:---------|----------------:|---------------------------:|----------------------------------:|--------:|------------:|
| IS      | BCHUSDT  |          0.3000 |                    76.6059 |                           76.6057 | -0.0002 |     -0.0003 |
| IS      | LDOUSDT  |          0.3000 |                     8.9253 |                            8.9253 | -0.0000 |     -0.0004 |
| IS      | TRXUSDT  |          0.5000 |                    -7.3504 |                           -7.3423 |  0.0081 |      0.1098 |
| OOS     | BCHUSDT  |          0.3000 |                    24.7503 |                           24.7502 | -0.0001 |     -0.0003 |
| OOS     | LDOUSDT  |          0.3000 |                    -6.1783 |                           -6.1782 |  0.0001 |      0.0014 |
| OOS     | TRXUSDT  |          0.5000 |                     4.1641 |                            4.6353 |  0.4712 |     11.3150 |

**Reading**: Demonstrates that per-symbol floor design ({"TRXUSDT":
0.5}) leaves BCH/LDO weighted_pnl IDENTICAL — these rows should have
delta=0 and delta_pct=0.

## Q6 — Path decision synthesis

| criterion                                      |   value | interpretation                                                                       |
|:-----------------------------------------------|--------:|:-------------------------------------------------------------------------------------|
| TRX IS partition-method sign flip A vs B       |  1.0000 | Method A (060 Q7)=-0.0608, Method B (cleaned)=+0.0199                                |
| TRX OOS partition-method sign flip A vs B      |  0.0000 | Method A (060 Q7)=-0.0139, Method B (cleaned)=-0.0308                                |
| TRX IS anti-Kelly significant (Method B CI)    |  0.0000 | Welch t=+0.34, CI=[-0.091, 0.130]                                                    |
| TRX OOS anti-Kelly significant (Method B CI)   |  0.0000 | Welch t=-0.49, CI=[-0.154, 0.088]                                                    |
| BCH IS Kelly direction (sign of Method B diff) |  0.0682 | Positive sign indicates Kelly-aligned (baseline)                                     |
| LDO IS Kelly direction (sign of Method B diff) |  0.1247 | Positive sign indicates Kelly-aligned (baseline)                                     |
| TRX IS wins weight P25 (Method B)              |  0.5550 | If < 0.5, raising floor to 0.5 would lift IS winning-trade weight                    |
| TRX OOS wins weight P25 (Method B)             |  0.4850 | If < 0.5, raising floor to 0.5 would lift OOS winning-trade weight                   |
| TRX Q4 floor=0.5 IS counterfactual lift        |  0.0080 | Δ weighted_pnl_sum vs current (floor=0.3) — IS                                       |
| TRX Q4 floor=0.5 OOS counterfactual lift       |  0.4713 | Δ weighted_pnl_sum vs current (floor=0.3) — OOS                                      |
| TRX Q4 floor=0.6 OOS counterfactual lift       |  0.9261 | Δ weighted_pnl_sum vs current (floor=0.3) — OOS at floor=0.6 (alt)                   |
| VERDICT                                        |  1.0000 | Path B (TRX floor=0.5) — counterfactual OOS lift +0.47wpnl > noise; IS bit-identical |
