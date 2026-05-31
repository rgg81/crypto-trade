# iter-v1/038 EDA Findings — Per-Symbol Vol-Target Ceiling

**Axis**: risk-primitive, sizing-side gate.
**Mechanism**: at trade-entry, if symbol's rolling 30d-annualized realized vol (`rv_30d_ann`, computed past-only from 8h log returns) exceeds a long-run upper percentile, scale position size down by 0.5×.
**Scope**: IS-only (close_time < `2025-03-24` OOS_CUTOFF). 5 baseline symbols (BTC / ETH / LINK / LTC / DOT).
**Source files**:
- Panel: `data/features/{SYM}_8h_features.parquet` (close-only; log returns computed in EDA)
- Trade roster: `reports-v1/iteration_v1-baseline/in_sample/trades.csv` (621 IS trades; 620 matched after as-of merge)

---

## 1. Per-Symbol RV Percentiles (annualized, log-return basis, 30d rolling window)

| Symbol  | n_bars | mean RV | std RV |   p5  |  p25  |  p50  |  p75  |  p85  |  p90  |  p95  |
|---------|-------:|--------:|-------:|------:|------:|------:|------:|------:|------:|------:|
| BTCUSDT |   5637 |  0.5778 | 0.2307 | 0.300 | 0.426 | 0.530 | 0.676 | 0.746 | 0.842 | 1.080 |
| ETHUSDT |   5637 |  0.7380 | 0.3019 | 0.355 | 0.525 | 0.690 | 0.877 | 0.968 | 1.100 | 1.327 |
| LINKUSDT|   5588 |  1.0133 | 0.3581 | 0.548 | 0.750 | 0.959 | 1.206 | 1.364 | 1.459 | 1.630 |
| LTCUSDT |   5597 |  0.8500 | 0.3257 | 0.421 | 0.600 | 0.807 | 1.050 | 1.177 | 1.280 | 1.489 |
| DOTUSDT |   4935 |  0.9427 | 0.3893 | 0.389 | 0.682 | 0.906 | 1.157 | 1.322 | 1.451 | 1.584 |

RV scale is heterogeneous: BTC sits a full 40% lower than LINK/DOT. A single global ceiling makes no sense — per-symbol calibration is the correct unit.

---

## 2. Recommended Ceiling Threshold (per symbol)

**Recommend 75th percentile** as the operating ceiling, with the same fractional sizing (0.5×) applied uniformly across symbols. Rationale:

- 85th percentile produces too few above-ceiling trades to meaningfully change sizing (LTC = 2 trades, DOT = 1 trade across IS — sample size collapse).
- 75th percentile gives 7-19% above-ceiling shares — enough to actually move the needle without becoming a near-no-op.
- Below the 75th, the percentile becomes too aggressive and starts cutting healthy mid-vol regimes, defeating the "extreme-vol-only" mechanism semantics.

| Symbol | Ceiling (75th, ann. RV) | Share of IS trades above |
|--------|------------------------:|-------------------------:|
| BTC    |                  0.6758 |              15.9% (18 of 113) |
| ETH    |                  0.8770 |              19.3% (28 of 145) |
| LINK   |                  1.2058 |              10.3% (15 of 146) |
| LTC    |                  1.0499 |               8.9% (11 of 123) |
| DOT    |                  1.1566 |               3.2% (3 of 93)   |

DOT's 3.2% above-ceiling share at the 75th is concerning — DOT's IS coverage starts later (4935 panel rows vs 5727 BTC/ETH) AND the existing R2 brake (DOT-only) already filters extreme-vol regimes, leaving fewer high-RV bars to coincide with R2-permitted entries.

---

## 3. Trade-Roster Impact Prediction (linear 0.5× sizing approximation, NO model retraining)

Treating the IS roster as fixed and re-weighting only the above-ceiling trades to 50% sizing:

| Symbol | Above-ceiling trades | Sum weighted PnL (current) | Sum weighted PnL (adj 0.5×) | Δ PnL pct |
|--------|---------------------:|---------------------------:|-----------------------------:|----------:|
| BTC    |   18 (15.9%)         |                    -15.026 |                       -8.863 |     **+6.16** |
| ETH    |   28 (19.3%)         |                    -15.973 |                      -11.160 |     **+4.81** |
| LTC    |   11 ( 8.9%)         |                     +5.464 |                       +9.040 |     **+3.58** |
| DOT    |    3 ( 3.2%)         |                    -16.188 |                      -22.430 |     **-6.24** |
| LINK   |   15 (10.3%)         |                    +96.401 |                      +63.462 |    **-32.94** |
| **TOTAL** | 75 (12.1% of 620) |                   +54.678 |                      +29.049 |    **-25.63** |

**THIS IS THE HEADLINE FINDING AND IT IS UNFAVORABLE.** Across the IS portfolio the simple per-symbol 75th-percentile RV ceiling at 0.5× sizing would have **destroyed ~26% of IS portfolio PnL**. The driver is structural:

- **LINK alone contributes -32.94 PnL pct** under the ceiling. LINK's IS edge is concentrated in HIGH-vol regimes (deciles 8-10 of its own RV distribution; see §4).
- **DOT contributes another -6.24** because its tiny above-ceiling sample (3 trades) happens to contain DOT's single-best decile cluster (decile 8: 7/7 wins, +7.67% mean net PnL).
- BTC, ETH, LTC each benefit modestly (+3.58 to +6.16) — the ceiling correctly clips drawdown-prone high-vol trades for these symbols.

Two of five symbols WORSEN under the rule. The asymmetry table makes this stark.

---

## 4. Vol-Regime Asymmetry (mean net_pnl_pct above vs below ceiling)

| Symbol | Ceiling | mean_net_pnl ABOVE | mean_net_pnl BELOW | wr_above | wr_below | Asymmetry (below − above) |
|--------|--------:|-------------------:|-------------------:|---------:|---------:|--------------------------:|
| BTC    |   p75   |             -0.768 |             -0.247 |    33.3% |    33.7% |   **+0.521** (good fit)  |
| ETH    |   p75   |             +0.090 |             -0.139 |    32.1% |    40.2% |   **-0.229** (wrong sign)|
| LTC    |   p75   |             -0.662 |             +0.100 |    54.5% |    38.4% |   **+0.761** (good fit)  |
| LINK   |   p75   |             +3.454 |             +0.155 |    60.0% |    43.5% |   **-3.299** (HOSTILE)   |
| DOT    |   p75   |            +10.408 |             -0.051 |    66.7% |    41.1% |  **-10.459** (CATASTROPHIC) |

**The asymmetry test is the killer.** A vol-ceiling rule presumes the strategy LOSES MORE on high-vol entries — i.e. mean_net_pnl_above < mean_net_pnl_below. That holds for BTC and LTC, but is **inverted for ETH, LINK, and DOT**, where the model's highest-vol entries are its BEST entries. This is consistent with v1's known per-symbol edge structure (`BASELINE_V1.md`):

- LINK is the dominant IS PnL contributor (+72% IS net PnL); its edge concentrates in regime transitions that coincide with elevated RV.
- DOT's small above-ceiling sample (3 trades) sits in DOT's all-time best decile (D8: +7.67% mean, 6/7 wins).
- ETH is mildly inverted but not catastrophically so.

A naive per-symbol vol-ceiling would PUNISH the very regimes where the model has its strongest edge for the majority of the v1 universe (3 of 5 symbols).

---

## 5. Per-Symbol Decile Patterns Worth Noting

(Full decile table: `analysis/iteration_v1-038/decile_table.csv`)

- **BTC**: decile structure noisy; modest wins at D5-D7 (mid-vol), losses at D8-D10. Vol-ceiling at D8-D10 (~p75) is consistent with the data.
- **LTC**: clearest "low-vol-best" symbol — D1+D2 deliver +1.97 + +0.71 mean weighted PnL, D5-D7 lose, D8 recovers. Vol-ceiling at the top makes sense.
- **LINK**: D8 alone delivers +5.05 mean weighted PnL (55.6 sum / 11 trades, 7/11 wins). D8 lives ABOVE p75. Capping LINK above p75 cuts LINK's strongest decile in half.
- **DOT**: D8 = 7/7 wins, +2.79 mean weighted PnL, sitting at the top of DOT's RV distribution. Capping DOT above p75 cuts DOT's strongest decile in half.
- **ETH**: D9 is the worst (-1.48 mean, 2/12 wins, sits below p85 by definition) but D8 and D10 are positive. The high-vol band is bimodal, not monotonically bad.

---

## 6. Outputs (committed-ready under `analysis/iteration_v1-038/`)

- `rv_percentiles.csv` — per-symbol annualized RV distribution percentiles
- `trades_with_rv.csv` — IS trade roster with entry-time RV merged
- `decile_table.csv` — per-symbol IS PnL bucketed by symbol-specific RV decile
- `asymmetry_test.csv` — above-vs-below ceiling PnL comparison (p75 + p85)
- `trade_impact_prediction.csv` — linear 0.5× sizing-reduction PnL delta per symbol

---

## 7. Recommendation to Brief (Phase 5)

**Reduce expected lift; consider abandoning the symmetric ceiling formulation.** The EDA produces a sharp prediction: a uniform 0.5× sizing reduction above the per-symbol 75th-percentile RV destroys ~26% of IS portfolio PnL because LINK and DOT have INVERSE asymmetry — their edge LIVES in high-RV regimes.

Options for the brief Section 3 (Proposed Changes):

1. **Symbol-selective ceiling**: apply ceiling ONLY to {BTC, LTC} (the 2 of 5 with the correct asymmetry sign). Predicted IS delta on those two symbols ≈ **+9.74 weighted PnL pct**. NEGATIVE: brittle "data-snooping by elimination" — borderline ineligible under "no per-symbol carve-outs" discipline; better as a follow-up exploration only.

2. **Tighter ceiling (p85)**: across all 5 symbols, p85 cuts the cap-share to 1-8% (too narrow on DOT/LTC at 1-2 trades — sample collapse). Predicted IS delta ≈ **-27.07** (mostly LINK + ETH inversion at p85 too). REJECT.

3. **Drop the symmetric mechanism**, replace with **drawdown-conditional ceiling**: only apply the cap if the symbol is BOTH high-RV AND in a recent-loss streak (e.g. last 3 trades all losing). Falls in line with the R1 cool-down semantics rather than R2-style scaling. Re-test in EDA before committing.

4. **PROCEED with the symmetric p75 0.5× rule as-specified anyway**, but DECLARE the EDA prediction as the falsifier: if OOS doesn't show LINK/DOT regression matching the IS prediction (within 1σ), the model is doing something the EDA missed and the result is informative regardless. **This is the bold path** under the PRIME DIRECTIVE — the EDA is unfavorable but the experiment still resolves a question (whether the IS-roster-linear approximation generalizes to a retrained-with-sizing model).

Most defensible Phase 5 choice: **Option 4 with explicit pre-registered falsifier**. The EDA says expect -26% IS portfolio PnL; if OOS shows similar regression and per-symbol attribution matches the asymmetry table, axis is CLOSED. If OOS surprises positive (model retraining absorbs the sizing change and reallocates trades to lower-vol bars), we have learned the IS-linear approximation is wrong and the mechanism deserves cycle-6 follow-up.

**Risk classification (Section 2.5)**: NORMAL-RISK — the change is a stateless sizing gate downstream of model predictions; does not alter Optuna training-objective domain. Single-seed EXPLORATION is appropriate.

**Axis family declaration (Section 0.6)**: `risk-primitive`. Prior 5 EXPLORATION families per `exploration_catalog.md` should be confirmed before brief commit.
