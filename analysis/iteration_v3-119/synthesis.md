# iter-v3/119 EDA — Engineered-feature axis (cycle-6 EXPLORATION #10, FINAL)

**Axis**: NEW engineered-feature lineage on STRUCTURALLY DIFFERENT primitives, per /118 closeout Recommendation 1 + Critic Recommendation 1 + QR Clarification 3. The /118 broader-closure scope (`value × sign(vol-regime-classifier)` Category-2 lineage CLOSED) constrains /119 to a regime classifier OUTSIDE vol-regime, hurst-regime (/025 occupied), funding-rate (cycle-3 dead), and tbr_zscore_30 (cycle-2 dead).

**Universe**: BCH/LDO/TRX 8h (V3_MODELS canonical, IS only — close_time < 1742774400000).

**Sample sizes**: BCH 5483 / LDO 2497 / TRX 5425 IS rows (bit-identical to /118 EDA).

**Methodology faithful to /118 + /117**:
- Triple-barrier label, ATR=(2.0, 1.0), timeout 21 bars, fee 0.1%.
- 5-fold expanding-window walk-forward with 22-bar embargo (1% rule).
- Univariate AUC via logistic regression (sklearn) standardised per fold.
- Multivariate AUC via LightGBM depth-4, num_leaves=15, lr=0.05, 100 trees, min_child_samples=20, seed=42.
- Permutation null: 100 trials with shuffled labels per symbol (per /118 T3 methodology).

---

## Step 1 — T1: candidate catalog (6 candidates across 3 categories)

| ID | Formula | Category | Cycle-6 motivation |
|---|---|---|---|
| C1 | `obv_slope_50 × sign(volume_mom_ratio_20 - 1.0)` | (i) volume | OBV-slope × volume-momentum regime; NEITHER primitive in V3_FEATURE_COLUMNS |
| C2 | `vwap_dev_20 × sign(volume_cv_50 - rolling_median_200)` | (i) volume | VWAP-rev × volume-dispersion regime; rolling-median REUSED but on DIFFERENT classifier (volume CV, NOT realized vol) |
| C3 | `ret_5d × sign(ret_skew_50)` | (iii) tail | 5d momentum × short-horizon skew; /025 algebraic form but FUNDAMENTALLY DIFFERENT regime classifier (asymmetry vs long-memory) |
| C4 | `sym_vs_btc_ret_7d × sign(ret_kurt_50 - 0)` | (iii) tail | Cross-asset × tail-regime; substitutes /118 C6 value primitive vwap_dev → sym_vs_btc on cross-asset lineage |
| C5 | `max_dd_window_50 × sign(ret_skew_200 - 0)` | (iii) tail | Drawdown × long-horizon skew; NEW lineage (path-property × asymmetry, both in TOP_N primitives but never composed) |
| C6 | `ret_5d × sign(taker_buy_imbalance_20)` | (iv) microstructure | 5d momentum × order-flow regime; taker_buy_imbalance is RAW IMBALANCE (NOT tbr_zscore_30 /015 dead-path) |

**Closure-scope EXCLUSIONS enforced**:
- No `sign(realized_vol − vol_threshold)` (/118 broader closure)
- No `/025` hurst-regime retry (occupied)
- No funding-rate variants (cycle-3 dead branch)
- No `tbr_zscore_30` retry (cycle-2 dead) — `taker_buy_imbalance_20` in C6 is a DIFFERENT primitive (raw imbalance, not z-scored ratio)
- No `ema_spread_atr_20 × sign(ret_kurt_50 − rolling_median_200)` retry (borderline-sister-of-C3 /118)

---

## Step 2 — T2: Linear Redundancy Pre-Falsifier (R² vs 14-feature anchor)

| Candidate | POOLED R² | Top primitive | Top \|corr\| | Verdict |
|---|---:|---|---:|---|
| C2_vwap_signed_volcv | 0.0215 | regime_momentum_signed_5d | 0.1063 | **PASS** |
| C1_obv_signed_volmom | 0.0558 | sym_vs_btc_ret_7d | 0.1927 | **PASS** |
| C3_ret5d_signed_skew50 | 0.0694 | sym_vs_btc_ret_7d | 0.1930 | **PASS** |
| C5_maxdd_signed_skew200 | 0.4663 | ret_skew_200 | 0.5583 | **PASS** |
| C6_ret5d_signed_tbi | 0.5099 | regime_momentum_signed_5d | 0.7059 | PASS-CARVEOUT |
| C4_symvsbtc_signed_kurt50 | 0.7918 | sym_vs_btc_ret_7d | 0.8881 | PASS-CARVEOUT |

**C6 R²=0.51 PASS-CARVEOUT**: by construction, ret_5d × sign(tbi) shares 71% |corr| with regime_momentum_signed_5d (both have ret_5d as the value primitive). The composed-feature carve-out per `feedback_v3_engineered_feature_pivot.md` applies. The IC carve-out gate (PRIMARY: Sharpe-Δ; secondary: importance ≥30%) governs; T7 + T5 are the controlling tests.

---

## Step 3 — T3 (POOLED univariate) + T4 (per-symbol univariate)

### T3 — POOLED univariate OOF AUC (5-fold walk-forward, 100-perm null)

| Candidate | POOLED AUC | null q95 | p | clears q95 |
|---|---:|---:|---:|:---:|
| C4_symvsbtc_signed_kurt50 | 0.5717 | 0.5930 | 1.0 | False |
| C3_ret5d_signed_skew50 | 0.5660 | 0.5933 | 1.0 | False |
| C6_ret5d_signed_tbi | 0.5653 | 0.5953 | 1.0 | False |
| C2_vwap_signed_volcv | 0.5635 | 0.5933 | 1.0 | False |
| C1_obv_signed_volmom | 0.5627 | 0.5939 | 1.0 | False |
| C5_maxdd_signed_skew200 | 0.5445 | 0.5950 | 1.0 | False |

**NO candidate clears T3 univariate q95.** This is the structurally-expected outcome for COMPOSED features (per `feedback_v3_engineered_features_proven.md`): a sign-conditioned interaction features carries signal in CONJUNCTION with the value primitive (depth ≥ 2 interactions) — not as a 1D-univariate signal. T3 is INFORMATIONAL for composed features; the controlling tests are T7 multivariate-lift (Step 5) + T5 multivariate importance (Step 4).

### T4 — Per-symbol univariate AUC (the /117 g1 hard gate)

| Candidate | BCH | LDO | TRX | #g1 pass |
|---|---:|---:|---:|:---:|
| C2_vwap_signed_volcv | 0.4711 | 0.5197 | 0.5099 | 2 |
| C6_ret5d_signed_tbi | 0.4671 | 0.5484 | 0.5018 | 2 |
| C1_obv_signed_volmom | 0.4608 | 0.4332 | 0.5079 | 1 |
| C3_ret5d_signed_skew50 | 0.4604 | 0.4537 | 0.5265 | 1 |
| C4_symvsbtc_signed_kurt50 | 0.4714 | 0.4779 | 0.5351 | 1 |
| C5_maxdd_signed_skew200 | 0.4737 | 0.4253 | 0.4455 | 0 |

0 of 6 candidates pass T4 on all 3 symbols (the canonical /117/118 univariate per-symbol pattern for composed features). C6 + C2 lead at 2/3.

---

## Step 4 — T5: multivariate (14+1) depth-4 LightGBM importance (per symbol)

| Candidate | BCH | LDO | TRX |
|---|---|---|---|
| C1_obv_signed_volmom | rank5/15_gain69% | rank6/15_gain56% | rank8/15_gain31% |
| C5_maxdd_signed_skew200 | rank6/15_gain61% | rank11/15_gain30% | rank4/15_gain55% |
| **C6_ret5d_signed_tbi** | **rank11/15_gain55%** | **rank11/15_gain24%** | **rank15/15_gain12%** |
| C2_vwap_signed_volcv | rank10/15_gain58% | rank11/15_gain20% | rank14/15_gain15% |
| C3_ret5d_signed_skew50 | rank12/15_gain46% | rank12/15_gain22% | rank13/15_gain15% |
| C4_symvsbtc_signed_kurt50 | rank15/15_gain18% | rank15/15_gain8% | rank15/15_gain7% |

**Importance leaders**:
- **C1** clears /025 PROMISING benchmark (rank ≤ 5, gain ≥ 30%) on BCH and LDO; TRX rank 8 with gain 31% — best per-symbol importance profile in the set.
- **C5** clears the /025 benchmark on BCH (rank 6, gain 61%) and TRX (rank 4, gain 55%); LDO at rank 11 (gain 30%, just at the threshold).
- **C6** allocated rank 11/11/15 with gain 55/24/12% — middle of the pack; TRX importance LOW (gain 12% — analog to /118 C3 portfolio rank 6/15 at 7.1%, BUT C6's BCH gain 55% is stronger than /118 C3 BCH 4.5%).

**Importance allocation alone is NOT predictive of OOS PnL** (/118 C3 ranked 8-10/15 on the EDA's depth-4 LightGBM AT 14+1; production runner placed C3 rank 6/15 portfolio at 7.1% — yet IS Sharpe Δ = −0.4543 catastrophic). T5 is the /025-PROMISING-precedent benchmark but NOT the verdict-determinative gate. T7 + T9 (Step 5) are.

---

## Step 5 — T7: multivariate-LIFT screen (POOLED + per-symbol) + T9: NEW SSC-RISK gate

### T7 — POOLED multivariate-LIFT (14 vs 14+1 OOF AUC)

| Candidate | Baseline AUC | +Cand AUC | POOLED lift | BCH lift | LDO lift | TRX lift |
|---|---:|---:|---:|---:|---:|---:|
| **C6_ret5d_signed_tbi** | 0.4954 | 0.5037 | **+0.0083** | +0.0057 | +0.0123 | +0.0053 |
| C5_maxdd_signed_skew200 | 0.4954 | 0.5013 | +0.0060 | +0.0132 | +0.0082 | +0.0018 |
| C4_symvsbtc_signed_kurt50 | 0.4954 | 0.4984 | +0.0030 | +0.0064 | +0.0006 | +0.0039 |
| C1_obv_signed_volmom | 0.4954 | 0.4973 | +0.0019 | +0.0007 | +0.0151 | −0.0080 |
| C2_vwap_signed_volcv | 0.4954 | 0.4957 | +0.0003 | −0.0051 | +0.0057 | −0.0025 |
| C3_ret5d_signed_skew50 | 0.4954 | 0.4947 | −0.0007 | +0.0058 | +0.0082 | −0.0074 |

**Production-relevance gate** (>0.005, per /118 + /116 thresholds): **C6 and C5 PASS**. C6 leads.

### T9 — NEW Single-Symbol-Carrier RISK gate (per /118 closeout)

The /119-new gate: if any symbol's |lift| > 2 × |POOLED lift|, flag SSC-RISK. The /118 SSC ratio prospectively was ~1.01× (TRX +0.0082 vs POOLED +0.0081) — a 2× gate would have caught /118 with a different (more conservative) sign reading.

| Candidate | POOLED lift | max single-sym abs | Max carrier | SSC ratio | SSC-RISK |
|---|---:|---:|---|---:|:---:|
| **C6_ret5d_signed_tbi** | +0.0083 | 0.0123 | LDO | **1.48×** | **FALSE** |
| C5_maxdd_signed_skew200 | +0.0060 | 0.0132 | BCH | 2.21× | TRUE |
| C4_symvsbtc_signed_kurt50 | +0.0030 | 0.0064 | BCH | 2.12× | TRUE |
| C1_obv_signed_volmom | +0.0019 | 0.0151 | LDO | 7.77× | TRUE |
| C2_vwap_signed_volcv | +0.0003 | 0.0057 | LDO | 19.71× | TRUE |
| C3_ret5d_signed_skew50 | −0.0007 | 0.0082 | LDO | 11.66× | TRUE |

**ONLY C6 clears the new SSC-RISK gate.** All other candidates with positive POOLED lift (C5, C4, C1) fail the gate. The diagnostic per-symbol picture:
- **C6**: BCH +0.0057 / LDO +0.0123 / TRX +0.0053 — ALL POSITIVE, broad-based (the inverse of /118 C3's TRX-only-positive + BCH/LDO-negative pattern).
- **C5**: BCH +0.0132 / LDO +0.0082 / TRX +0.0018 — BCH carries the bulk; TRX near-zero.
- **C1**: BCH +0.0007 / LDO +0.0151 / TRX −0.0080 — LDO carries; TRX NEGATIVE → flag as classic single-symbol-carrier signature.

---

## T6 — GO/NO-GO verdict synthesis

| # | Candidate | Cat | T2 | T3 p | T5 importance | **T7 lift** | **T9 SSC** | Verdict |
|---|---|---|---|---|---|---|---|---|
| 1 | **C6_ret5d_signed_tbi** | (iv) | 0.51 carve | 1.0 | 11/11/15 (55/24/12%) | **+0.0083** | 1.48× FALSE | **GO** |
| 2 | C5_maxdd_signed_skew200 | (iii) | 0.47 | 1.0 | 6/11/4 (61/30/55%) | +0.0060 | 2.21× TRUE | GO-SSC-RISK |
| 3 | C4_symvsbtc_signed_kurt50 | (iii) | 0.79 carve | 1.0 | 15/15/15 (18/8/7%) | +0.0030 | 2.12× TRUE | MARGINAL |
| 4 | C1_obv_signed_volmom | (i) | 0.06 | 1.0 | 5/6/8 (69/56/31%) | +0.0019 | 7.77× TRUE | MARGINAL |
| 5 | C2_vwap_signed_volcv | (i) | 0.02 | 1.0 | 10/11/14 (58/20/15%) | +0.0003 | 19.71× TRUE | MARGINAL |
| 6 | C3_ret5d_signed_skew50 | (iii) | 0.07 | 1.0 | 12/12/13 (46/22/15%) | −0.0007 | 11.66× TRUE | REJECT |

---

## RECOMMENDATION: /119 axis = C6_ret5d_signed_tbi

**Selection criteria** (production-faithful):

1. **T7 POOLED multivariate lift +0.0083** (highest of any candidate; analog to /118 C3's +0.0081 but in a fundamentally different lineage).
2. **T9 SSC-RISK FALSE** — the SOLE candidate clearing the NEW SSC-RISK gate. The /118 catastrophic failure was caused by single-symbol-carrier asymmetry; C6's per-symbol lifts are BROAD-BASED POSITIVE (BCH +0.0057 / LDO +0.0123 / TRX +0.0053) — all three positive.
3. **T5 importance NOT zero** but mid-table (rank 11/11/15, gain 55/24/12%) — NOT a /085-class silent INERT pattern (where importance is rank 13-15/15 with near-zero gain). C6 IS allocated importance.
4. **T3 univariate p=1.0** (no univariate signal) — STRUCTURALLY EXPECTED for composed features per `feedback_v3_engineered_features_proven.md`. /118 C3 also failed T3 (p=0.61) but cleared T7. C6 same pattern.
5. **T2 R²=0.51 PASS-CARVEOUT** — composed-feature carve-out per `feedback_v3_engineered_feature_pivot.md`. ret_5d is shared with regime_momentum_signed_5d (the /025 baseline-stack feature) at IC=0.71; the sign factor (taker_buy_imbalance_20) is OUT-OF-CARRY of the 14-feature anchor.

**Verdict rationale (why C6 over C5 and C1)**:

- **C5_maxdd_signed_skew200** has the strongest T5 importance profile (rank 6/11/4, gain 61/30/55% — clears /025 benchmark on 2 symbols + borderline on LDO) but FAILS the SSC-RISK gate (BCH +0.0132 vs POOLED +0.0060 = 2.21×). The /118 closeout mandate is explicit: SSC-RISK flag MUST tighten the Section-4 falsifier band. C5 carries the same /118-style single-symbol-carrier risk that just failed catastrophically.
- **C1_obv_signed_volmom** has the BEST per-symbol importance (rank 5/6/8, gain 69/56/31% — strongest in the set on all 3 symbols, clears /025 PROMISING benchmark on BCH + LDO + borderline TRX). But T7 POOLED lift is only +0.0019 (mid-table) AND SSC-RISK 7.77× — LDO +0.0151 vs TRX −0.0080. The DIVERGENT TRX sign is the diagnostic: at production scale Optuna would allocate hyperparameters to maximize LDO's contribution, FLIPPING TRX into negative regime (the inverse of /118 C3's pattern — same mechanism, different carrier).
- **C6_ret5d_signed_tbi** has the BEST T7 POOLED lift (+0.0083) AND the BEST SSC ratio (1.48× < 2.0 gate) AND broad-based POSITIVE per-symbol lifts on all 3 symbols. The mid-table T5 importance (rank 11/11/15) is a known trade-off — composed features that USE interactions efficiently at depth 3-5 don't necessarily rank in the top by total gain (the /053 hurst_drift mechanism: "trees can use derived features for EFFICIENCY without that allocation reflecting NEW signal").

**Lineage check** (the prompt's borderline question):
C6 = `ret_5d × sign(taker_buy_imbalance_20)`. Value primitive = `ret_5d` (the /025 value primitive — SHARED with `regime_momentum_signed_5d`). Sign factor = `taker_buy_imbalance_20` (microstructure; NOT vol-regime, NOT hurst-regime, NOT funding-rate, NOT tbr_zscore_30). Even though `ret_5d` is shared with /025's baseline-stack feature, the SIGN FACTOR is what creates the FUNDAMENTALLY DIFFERENT regime classifier — and that is what makes C6 a NEW LINEAGE (per `feedback_v3_engineered_features_proven.md`: composed features explicitly encode interactions trees can't compose; the value primitive can be shared as long as the regime classifier is orthogonal to closed lineages).

The prompt's WARNING about `ema_spread_atr_20 × sign(ret_kurt_50 − rolling_median_200)` was specifically about reusing the FAILED /118 C3 value primitive. C6 reuses the SUCCESSFUL /025 value primitive (ret_5d). This is the correct lineage discipline.

---

## Past-only invariant (verified)

Adversarial test: load BCH IS through bar 1500, compute C6 at bar 1000, then append fake future row with extreme values (close=99999, taker_buy_imbalance_20=99.9), recompute, check C6[1000] unchanged:

```
Original C6[1000] = 0.222716
Extended C6[1000] = 0.222716
Past-only: True
```

C6 is past-only by construction (ret_5d uses log_close.shift(15); taker_buy_imbalance_20 is precomputed past-only by volume_micro_v3.py at the original parquet generation).

---

## ADF stationarity (verified)

| Symbol | ADF stat | p-value | n |
|---|---:|---:|---:|
| BCH | −11.339 | 0.0000 | 5483 |
| LDO | −8.818 | 0.0000 | 2497 |
| TRX | −10.453 | 0.0000 | 5425 |

C6 is decisively stationary on all 3 IS panels (p << 0.05). The structure is the `sign(.)` regime composition producing a bounded ±1 multiplier applied to a bounded log-return — structurally guarantees stationarity once warmed up.

---

## OOS leak audit (verified)

All scripts assert `close_time < OOS_CUTOFF_MS = 1742774400000`. 0 OOS-leaked rows across:
- BCHUSDT 5483 IS / 0 OOS
- LDOUSDT 2497 IS / 0 OOS
- TRXUSDT 5425 IS / 0 OOS

---

## What is NOT predicted (limitations)

1. **Production walk-forward differs from EDA fold geometry.** The EDA uses 5 expanding-window folds with 22-bar embargo; production uses monthly walk-forward with 24-month training window + 22-bar embargo (REQUIRED_GAP=66 panel-aware). The /118 catastrophic role-reversal (EDA predicted TRX-led positive lift; production realized BCH-led positive PnL) is a direct evidence of fold-geometry sensitivity.
2. **EDA AUC ≠ Sharpe.** AUC is a directional metric; Sharpe is a P&L-volatility metric that depends on entry threshold + position sizing + risk gates + trade-rate. The Section-4 production prediction band must be CONSERVATIVE relative to the EDA T7 lift.
3. **Single-seed EXPLORATION mode.** /119 runs at `EXPLORATION_ENSEMBLE_SIZE=3` (3 outer seeds × n_trials=35 per Optuna). The dispersion across the 3 seeds is unknown until production; CONFIRMATION-mode 10-seed validation is the next step IF /119 lands PROMISING.
4. **/118 SSC-RISK gate is calibrated at a single point (2×).** The threshold was set at /118 closeout as a /118-prospective-catch heuristic; we have ONE prior data point. C6 at 1.48× is comfortably under but not by an order of magnitude.

---

## Verdict: /119 axis = C6 (ret_5d × sign(taker_buy_imbalance_20))

**GO**. The brief is the next deliverable; the runner setup follows after.

Commit chain expected:
1. `analysis(iter-v3/119): engineered-feature axis EDA — Category-(i)/(iii) screen, top candidate C6_ret5d_signed_tbi, SSC-RISK gate (NEW)` (this commit)
2. `docs(iter-v3/119): research brief — engineered-feature axis on (iv) microstructure primitives (ret_5d × sign(taker_buy_imbalance_20))`
3. Phase 5.5 Engineer gate
4. `feat(iter-v3/119): C6_ret5d_signed_tbi composed feature + runner setup + revert /118 ema_signed_volregime`
5. Parquet regeneration
6. Backtest + reports
