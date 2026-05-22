# iter-v3/122 EDA — ETH cross-asset feature family (cycle-7 EXPLORATION #1)

**Axis**: NEW cross-asset feature family using ETH OHLCV (not crypto-native sentiment data) per BASELINE_V3.md §"Cycle 7 Axis Priorities" axis-1 (HIGH priority) + the /121 closeout candidate menu. Selected per `feedback_v3_axis_selection_quant_discipline.md` (QR-led with committed EDA).

**The 7-FEED VERDICT lineage check** (see `_shared.py` docstring): ETH klines are OHLCV; the 7 closed feeds (funding /019/023/024/082/085, microstructure /015, basis /086) are non-OHLCV derivatives-metadata feeds. ETH cross-asset features are in the same family as the existing baseline `btc_ret_14d` and `sym_vs_btc_ret_7d` features (both non-INERT in /059), not in the 7-FEED scope. ETH is in `V3_EXCLUDED_SYMBOLS` for TRADING but its klines are eligible for cross-asset feature merge via the established `cross_btc_v3.py` pattern.

**Universe**: BCH/LDO/TRX 8h (V3_MODELS canonical, IS only — close_time < 1742774400000).

**Sample sizes**: BCH 5606 / LDO 2620 / TRX 5548 IS rows (with all candidates non-NaN).

**Methodology faithful to /119 + /118**:
- Triple-barrier label, ATR=(2.0, 1.0), timeout 21 bars, fee 0.1%.
- 5-fold expanding-window walk-forward with 22-bar embargo (1% rule).
- Univariate AUC via logistic regression (sklearn) standardised per fold.
- Multivariate AUC via LightGBM depth-4, num_leaves=15, lr=0.05, 100 trees, min_child_samples=20, seed=42.
- Permutation null: 100 trials with shuffled labels per candidate.

---

## Step 1 — T1: candidate catalog (4 candidates, single category: cross-asset ETH OHLCV)

| ID | Formula | Category | Cycle-7 motivation |
|---|---|---|---|
| A1 | `eth_ret_14d` = log(close_eth[t]/close_eth[t-42]) | (v) cross-asset ETH momentum | Symmetric mate to baseline `btc_ret_14d`; ETH regime structurally distinct at multi-week horizon. |
| A2 | `eth_vs_btc_ret_21d` = eth_ret_21d − btc_ret_21d | (v) cross-asset ETH/BTC relative-strength | Alt-rotation regime indicator. 21d horizon avoids overlap with baseline 7d/14d. |
| A3 | `eth_vs_btc_vol_diff_14d` = eth_vol_14d − btc_vol_14d | (v) cross-asset ETH/BTC vol-regime | When ETH leads BTC in vol, risk-on regime → alts (BCH/LDO/TRX) move bigger. |
| A4 | `eth_ret_3d` = log(close_eth[t]/close_eth[t-9]) | (v) cross-asset ETH momentum (short-horizon) | Short-horizon ETH-trend signal; cross-asset analog to /063's removed `btc_ret_3d`. |

**Closure-scope check**:
- NO crypto-native sentiment metadata feed (the 7-FEED scope: funding, microstructure, basis)
- NO direct funding/basis/OI/microstructure features
- ETH is a price OHLCV source structurally identical to the existing BTC OHLCV source already in baseline

---

## Step 2 — T2: Linear Redundancy Pre-Falsifier (R² vs 14-feature anchor)

| Candidate | POOLED R² | Top primitive | Top \|corr\| | Verdict |
|---|---:|---|---:|---|
| A2_eth_vs_btc_ret_21d | 0.1130 | ema_spread_atr_20 | 0.2107 | **PASS** |
| A3_eth_vs_btc_vol_diff_14d | 0.3264 | max_dd_window_50 | 0.4144 | **PASS** |
| A4_eth_ret_3d | 0.4370 | vwap_dev_20 | 0.5598 | **PASS** |
| A1_eth_ret_14d | **0.7017** | btc_ret_14d | **0.8171** | **REJECT (R²≥0.70)** |

**A1 REJECT-R2**: by construction, ETH and BTC 14-day log returns are highly correlated (|corr| 0.82 with `btc_ret_14d`). ETH 14d is essentially a noisy version of BTC 14d at the 14-day horizon. The strict R²<0.70 gate fires per `feedback_v3_lr_pf_methodology.md` — ETH features are NOT composed features, so the composed-feature carve-out does NOT apply.

**A2/A3/A4 PASS the redundancy gate** — these features have distinct information content from the 14-feature anchor.

---

## Step 3 — T3 (POOLED univariate) + T4 (per-symbol univariate)

### T3 — POOLED univariate OOF AUC (5-fold walk-forward, 100-perm null)

| Candidate | POOLED AUC | null q95 | p | clears q95 |
|---|---:|---:|---:|:---:|
| A2_eth_vs_btc_ret_21d | 0.5181 | 0.5062 | 0.00 | **TRUE** |
| A4_eth_ret_3d | 0.5081 | 0.5069 | 0.03 | **TRUE** |
| A1_eth_ret_14d | 0.4942 | 0.5075 | 0.66 | FALSE |
| A3_eth_vs_btc_vol_diff_14d | 0.4731 | 0.5090 | 1.00 | FALSE |

**A2 and A4 clear the univariate q95 gate** — both have genuine 1D directional content. A2 is the stronger univariate signal (+0.012 above q95). A3 is below the random baseline (univariate inert). A1 is at the random baseline.

### T4 — Per-symbol univariate AUC (the /117 g1 hard gate)

| Candidate | BCH | LDO | TRX | #g1 pass |
|---|---:|---:|---:|:---:|
| A2_eth_vs_btc_ret_21d | 0.4694 | **0.5744** | **0.5601** | 2 |
| A4_eth_ret_3d | 0.4629 | **0.5301** | **0.5379** | 2 |
| A1_eth_ret_14d | 0.4666 | 0.4401 | 0.5553 | 1 |
| A3_eth_vs_btc_vol_diff_14d | 0.4767 | 0.4065 | 0.4938 | 0 |

**A2 has the strongest per-symbol pattern: LDO 0.5744 + TRX 0.5601 (both above 0.55)**. A4 is mid-range (LDO 0.5301 + TRX 0.5379). Both share the same weakness: BCH univariate AUC is BELOW 0.50 (anti-signal on BCH).

**The diagnostic per-symbol picture**: ETH cross-asset features systematically work BETTER on the smaller-cap alts (LDO + TRX) and WORSE on BCH. BCH is a BTC-fork; its price action is closely tied to BTC's, so ETH-vs-BTC relative information adds little. LDO + TRX are altcoin assets where alt-rotation dynamics matter more.

This per-symbol asymmetry is the load-bearing diagnostic for the SSC-RISK gate at Step 5.

---

## Step 4 — T5: multivariate (14+1) depth-4 LightGBM importance (per symbol)

| Candidate | BCH | LDO | TRX |
|---|---|---|---|
| A1_eth_ret_14d | rank15/15_gain3.79% | rank12/15_gain2.59% | rank8/15_gain5.38% |
| **A2_eth_vs_btc_ret_21d** | rank15/15_gain3.95% | **rank2/15_gain10.07%** | **rank3/15_gain9.76%** |
| A3_eth_vs_btc_vol_diff_14d | rank15/15_gain3.40% | rank4/15_gain10.91% | rank7/15_gain6.59% |
| A4_eth_ret_3d | rank15/15_gain2.97% | rank11/15_gain4.01% | rank10/15_gain4.25% |

**A2's importance allocation is the standout**: LDO rank 2/15 (10.07% gain) + TRX rank 3/15 (9.76% gain) — strong importance allocation on the two alt symbols. A3 is also strong on LDO (rank 4, 10.91% gain).

**BUT ALL 4 candidates rank 15/15 on BCH** — uniform rock-bottom importance allocation across the board. BCH (the dominant IS-share symbol at /059's 95.76% and the BTC-fork) systematically declines to use ETH cross-asset information. This is the structural BCH/non-BCH asymmetry showing up in importance.

---

## Step 5 — T7: multivariate-LIFT screen (POOLED + per-symbol) + T9: SSC-RISK gate

### T7 — POOLED multivariate-LIFT (14 vs 14+1 OOF AUC)

| Candidate | Baseline AUC | +Cand AUC | POOLED lift | BCH lift | LDO lift | TRX lift |
|---|---:|---:|---:|---:|---:|---:|
| **A1_eth_ret_14d** | 0.4732 | 0.4800 | **+0.0069** | −0.0005 | −0.0044 | −0.0062 |
| A4_eth_ret_3d | 0.4732 | 0.4744 | +0.0012 | +0.0001 | −0.0034 | −0.0044 |
| A3_eth_vs_btc_vol_diff_14d | 0.4732 | 0.4739 | +0.0007 | −0.0091 | **+0.0203** | −0.0071 |
| A2_eth_vs_btc_ret_21d | 0.4732 | 0.4671 | **−0.0060** | +0.0106 | **+0.0530** | −0.0055 |

**A1 has the strongest pooled lift (+0.0069) — but it fails T2 (R²=0.70). It's redundant with baseline btc_ret_14d.**

**A2's POOLED lift is NEGATIVE (−0.006)** despite a strong LDO lift (+0.053). The multivariate POOLED model cannot simultaneously load A2 positively on LDO+TRX without paying a large BCH cost — A2 ends up net-negative in the pooled fit. This is the SAME failure mode as /118 C3 (where TRX-only-positive + BCH/LDO-negative produced the catastrophic IS-collapse).

**Production-relevance gate** (POOLED lift > +0.003, per /118 + /119 thresholds): **NO candidate clears** (A1 +0.0069 but REJECT-R2 disqualifies; A4 +0.0012 is below threshold).

### T9 — Single-Symbol-Carrier RISK gate

| Candidate | POOLED lift | max single-sym abs | Max carrier | SSC ratio | SSC-RISK |
|---|---:|---:|---|---:|:---:|
| A3_eth_vs_btc_vol_diff_14d | +0.0007 | 0.0203 | LDO | **28.13×** | TRUE |
| A2_eth_vs_btc_ret_21d | −0.0060 | 0.0530 | LDO | 8.81× | TRUE |
| A4_eth_ret_3d | +0.0012 | 0.0044 | TRX | 3.63× | TRUE |
| A1_eth_ret_14d | +0.0069 | 0.0062 | TRX | 0.90× | **FALSE** |

**ONLY A1 clears the SSC-RISK gate — but A1 is REJECT-R2.** All 3 candidates that pass the R² gate FAIL the SSC-RISK gate (3.63× to 28.13×).

The diagnostic: ETH cross-asset features systematically over-load on LDO/TRX (the alt symbols) and produce per-symbol asymmetry far exceeding the 2× SSC-RISK threshold. The /118 catastrophic failure was caused by exactly this single-symbol-carrier asymmetry; A2/A3 would replicate that pattern.

---

## T6 — GO/NO-GO verdict synthesis

| # | Candidate | Cat | T2 | T3 p | T5 importance (B/L/T) | **T7 lift** | **T9 SSC** | Verdict |
|---|---|---|---|---|---|---|---|---|
| 1 | **A4_eth_ret_3d** | (v) | 0.44 | 0.03 | 15/11/10 (3.0/4.0/4.3%) | +0.0012 | 3.63× TRUE | **MARGINAL** |
| 2 | A3_eth_vs_btc_vol_diff_14d | (v) | 0.33 | 1.00 | 15/4/7 (3.4/10.9/6.6%) | +0.0007 | 28.13× TRUE | WEAK |
| 3 | A1_eth_ret_14d | (v) | 0.70 | 0.66 | 15/12/8 (3.8/2.6/5.4%) | +0.0069 | 0.90× FALSE | REJECT-R2 |
| 4 | A2_eth_vs_btc_ret_21d | (v) | 0.11 | 0.00 | 15/2/3 (4.0/10.1/9.8%) | −0.0060 | 8.81× TRUE | REJECT |

---

## RECOMMENDATION: /122 axis = A4_eth_ret_3d (with WEAK signal, brief models NEGATIVE)

**The honest reading of the EDA**: No candidate in the 4-feature catalog is a GO-class entry. The selection criterion for the brief is **least-bad among candidates that survive T2** (i.e., not REJECT-R2).

**Selection rationale**:

1. **A2 has the strongest univariate signal but the worst SSC-RISK + negative POOLED lift**. The /118 + /119 lessons (`feedback_v3_promising_feature_mechanical.md` + SSC-RISK gate) discipline us out of A2: the multivariate POOLED model can't load A2 productively without paying a BCH cost.

2. **A1 has the strongest POOLED lift but the worst T2 redundancy (R²=0.70 with btc_ret_14d)**. Per `feedback_v3_lr_pf_methodology.md`, A1 is an algebraic near-clone of an existing baseline feature; adding it would steal `colsample_bytree` allocation without adding new information.

3. **A4 (eth_ret_3d) is the only candidate that BOTH passes T2 AND has positive POOLED lift, weak as it is**. But T7 lift +0.0012 is below the /118+/119 production-relevance threshold (+0.003), and T9 SSC ratio 3.63× exceeds the 2× gate. T5 importance on BCH is rank 15/15 (the /015/082/085/086 INERT pattern).

**Verdict rationale (why A4 over A1, A2, A3)**:

- **A4 vs A1**: A1 (eth_ret_14d) is algebraically redundant with `btc_ret_14d` at |corr|=0.82 (R²=0.70). Adding A1 would burn colsample_bytree allocation on a feature that the tree already has access to via btc_ret_14d. Per the /027/063 collinearity-trap pattern, this would harm OOS by overfitting noise. A4 has R²=0.44 — distinct information at 3-day horizon vs the 14-day baseline.
- **A4 vs A2**: A2's per-symbol picture (LDO +0.053, BCH +0.0106, TRX -0.0055) produces NEGATIVE POOLED lift because the multivariate model can't simultaneously load A2 on the alts and absorb the BCH+TRX cost. A4 has uniform-weak per-symbol lifts (none positive but none catastrophic).
- **A4 vs A3**: A3 fails the univariate gate (POOLED AUC 0.473 < null q95 0.509). A3 has no 1D directional content; the LDO multivariate lift is likely Optuna lottery noise.

**The pre-registration trajectory**:
- A4's BCH rank 15/15 importance + 3.63× SSC ratio + +0.0012 POOLED lift below threshold = the /082/085/086 INERT-by-importance signature with weak SSC.
- Modal prediction (brief Section 7): **NEGATIVE-no-effect or NEGATIVE-INERT** — A4 ranks 15/15 on BCH at production, mid-table on LDO/TRX, with POOLED lift collapsing in the multi-symbol Optuna landscape.

**Why run the backtest anyway** (PRIME DIRECTIVE):

- The 7-FEED verdict was established empirically on non-OHLCV crypto-native data. The OHLCV-family hypothesis (ETH OHLCV is structurally different) is genuinely untested at production scale.
- A4's weak EDA signature (BCH rank 15 + thin POOLED lift) is the EXACT signature that /082 / /085 / /086 had at EDA — and those went on to fire SUSPICIOUS-OOS-DOMINANT or PROMISING-INERT at production. /122 producing a similar verdict would be a 4th data point on the OHLCV-cross-asset axis (with /063's btc_ret_3d as a prior, also REMOVED for collateral reasons).
- The brief models the modal outcome as NEGATIVE, but the falsifier bands accommodate a surprise OOS lift — which would be a real, publishable finding (the first NEW non-baseline OHLCV cross-asset feature in v3 history).

---

## ADF stationarity audit (T8)

12/12 (symbol, candidate) cells PASS ADF p<0.05 (`T8_adf_stationarity.csv`). All 4 ETH candidates are decisively stationary on all 3 IS panels. Expected by construction — log-returns and vol-differences are structurally stationary.

| Candidate | BCH ADF p | LDO ADF p | TRX ADF p |
|---|---:|---:|---:|
| A1_eth_ret_14d | 0.0e0 | 0.0e0 | 0.0e0 |
| A2_eth_vs_btc_ret_21d | 0.0e0 | 0.0e0 | 0.0e0 |
| A3_eth_vs_btc_vol_diff_14d | 0.0e0 | 9.9e-5 | 0.0e0 |
| A4_eth_ret_3d | 0.0e0 | 0.0e0 | 0.0e0 |

---

## Past-only invariant (verified)

ETH features are computed past-only by construction (same math as `cross_btc_v3.py`):
- `eth_ret_{N}d`: log(close[t]) − log(close[t−window]); a shift-style window, never reads future
- `eth_vol_14d`: `pd.Series(.).rolling(42, min_periods=42).std()` — pandas canonical past-only rolling
- Merge into symbol panel is left-join on `open_time`; the symbol's existing past-only features are unchanged.

The merge convention is identical to the /059 `sym_vs_btc_ret_7d` and `btc_ret_*` features which passed look-ahead audits in every prior v3 Critic review. No new look-ahead surface introduced.

---

## OOS leak audit (verified)

All scripts assert `close_time < OOS_CUTOFF_MS = 1742774400000`. 0 OOS-leaked rows across:
- BCHUSDT 5606 IS / 0 OOS
- LDOUSDT 2620 IS / 0 OOS
- TRXUSDT 5548 IS / 0 OOS

---

## What is NOT predicted (limitations)

1. **Production walk-forward differs from EDA fold geometry.** The EDA uses 5 expanding-window folds with 22-bar embargo; production uses monthly walk-forward with 24-month training window. The /118 catastrophic IS-collapse was a direct evidence of fold-geometry sensitivity. A4's thin POOLED lift may or may not survive the production fold geometry.

2. **EDA AUC ≠ Sharpe.** AUC is a directional metric; Sharpe depends on entry threshold + position sizing + risk gates + trade-rate. The Section 4 production prediction band must be CONSERVATIVE relative to the EDA T7 lift.

3. **Single-seed EXPLORATION mode.** /122 runs at `EXPLORATION_ENSEMBLE_SIZE=3` (3 outer seeds × n_trials=35 per Optuna). The dispersion across the 3 seeds is unknown until production; CONFIRMATION-mode 10-seed validation is the next step IF /122 lands PROMISING (unlikely given the EDA's WEAK signal).

4. **Cross-asset features have higher fold-geometry sensitivity than symbol-internal features**. The ETH klines panel has its own structural breaks (Dec 2017, May 2021, June 2022 deleveraging cycle); the per-symbol panels are jointly conditioned on the BTC + ETH macro-crypto regime which may not partition cleanly across walk-forward folds.

---

## Verdict: /122 axis = A4 (eth_ret_3d) with MARGINAL EDA signal

**Top candidate**: A4 (`eth_ret_3d`). Brief models the modal outcome as **NEGATIVE-no-effect or NEGATIVE-INERT** per the BCH rank 15/15 + thin POOLED lift + SSC ratio 3.63× signature. The PRIME DIRECTIVE runs the backtest regardless; the EDA's WEAK GO is itself a publishable finding (the OHLCV-cross-asset hypothesis is structurally distinct from the 7-FEED verdict's scope, and a 4th data point — even a negative one — sharpens the lineage discipline going forward).

The brief is the next deliverable; the runner setup follows after.

Commit chain expected:
1. `analysis(iter-v3/122): cycle-7 EXPLORATION axis-1 EDA — ETH cross-asset feature family; top candidate A4_eth_ret_3d` (this commit)
2. `docs(iter-v3/122): research brief — cycle-7 EXPLORATION axis-1 (ETH cross-asset; A4_eth_ret_3d)`
3. Phase 5.5 Engineer gate
4. `feat(iter-v3/122): A4_eth_ret_3d ETH cross-asset feature + runner setup`
5. Parquet regeneration (add ETH-derived feature group; `data/features_v3/<sym>_8h_features.parquet` 14-feat → adds A4)
6. Backtest + reports
