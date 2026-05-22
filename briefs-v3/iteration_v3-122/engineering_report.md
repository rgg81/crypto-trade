# Engineering Report — iter-v3/122

## Headers

- Iteration: iter-v3/122
- Branch: iteration-v3/122
- Commit SHA: f88415c34a0a91efac9398f7ea08ca59ede467c9
- Hardware: WSL2 Linux 6.6.114.1 / x86-64
- Wall-clock time: 0.70h

---

## 1. Setup Verification

### Branch and commit chain

| Commit | Message |
|---|---|
| `b875272` | analysis(iter-v3/122): cycle-7 EXPLORATION axis-1 EDA |
| `af157d0` | docs(iter-v3/122): research brief |
| `e18b266` | docs(iter-v3/122): phase 5.5 gate PASS |
| `ac0f891` | feat(iter-v3/122): A4 eth_ret_3d cross-asset feature + runner setup |
| `f88415c` | fix(iter-v3/122): pre-flight assertion len==14→15 |

The fix commit corrected a stale assertion guard in `run_baseline_v3.py` left over from the /121 setup (assertion still checked `len == 14`). The backtest ran after the fix commit. Fully reproducible from `f88415c`.

### Pre-flight assertions verified

- `len(V3_FEATURE_COLUMNS_TOP_N) == 15`: PASS
- `"eth_ret_3d" in V3_FEATURE_COLUMNS_TOP_N`: PASS
- ETH klines present: `data/ETHUSDT/8h.csv` (6990+ rows, extent to 2026-05-20)
- NaN count for `eth_ret_3d` < 1% of total rows: PASS (9-bar warm-up only)
- Sacred constants: `OOS_CUTOFF_DATE = 2025-03-24`, `training_months = 24` — UNCHANGED
- Feature isolation: `grep` for `from crypto_trade.features ` in `features_v3/` — empty PASS

### Ruff lint/format

Run and clean before the feat commit. No lint failures.

### Integration tests

Unit test `test_eth_ret_3d_past_only` and integration test `test_eth_ret_3d_integration` (per Section 3 / Section 9 of the brief) verified passing before backtest launch.

### Parquet regeneration

`uv run crypto-trade features --symbols BCHUSDT,LDOUSDT,TRXUSDT --interval 8h --track v3 --format parquet --workers 4` run after the feature commit. BCH/LDO/TRX parquets confirmed to contain `eth_ret_3d` as a non-NaN column on the last 100 IS rows.

---

## 2. Implementation Summary

### Configuration diff vs BASELINE_V3.md (/121)

| Item | /121 baseline | /122 |
|---|---|---|
| `V3_FEATURE_COLUMNS_TOP_N` length | 14 | **15** |
| New feature | — | `eth_ret_3d` (15th element, appended) |
| `ITERATION_LABEL` | `"v3-121"` | `"v3-122"` |
| Pre-flight n_features guard | `== 14` | `== 15` |
| All other knobs | unchanged | **bit-identical** |

### Source changes

- `src/crypto_trade/features_v3/cross_btc_v3.py`: added `_load_eth_v3_features()` function (ETH klines cache, `eth_ret_3d = log(close[t]) − log(close[t−9])`) + extended `add_cross_btc_v3_features` to left-join ETH columns.
- `src/crypto_trade/features_v3/__init__.py`: appended `"eth_ret_3d"` to `V3_FEATURE_COLUMNS_TOP_N`; comment updated with /122 provenance.
- `run_baseline_v3.py`: `ITERATION_LABEL`, pre-flight assertion inverted.

No labeling, risk gate, walk-forward, or model architecture changes. The /116 no_confirm primitive stays enabled per user directive 2026-05-20.

---

## 3. Key Metrics Table

| Metric | IS | OOS | Ratio |
|---|---:|---:|---:|
| Monthly Sharpe | **+0.9710** | **+1.1642** | 1.1989 |
| Daily Sharpe | 2.5243 | 2.3286 | 0.9225 |
| Max Drawdown | 33.21% | 28.25% | 0.8506 |
| Profit Factor | 1.511 | 1.356 | 0.8974 |
| Win Rate | 40.2% | 43.1% | 1.2083 |
| N Trades | 179 | 102 | 0.5698 |
| Total PnL | 74.09 | 36.52 | 0.4929 |
| Monthly Calmar | 2.23 | 1.29 | 0.5795 |
| DSR | 0.0 (EXPLORATION artifact) | — | — |
| PBO | **0.1412** (PASS < 0.40) | — | — |
| PSR | **1.0** (PASS > 0.95) | — | — |
| frac_positive_paths | **0.644** (PASS > 0.55) | — | — |
| n_trials | 315 | — | — |
| n_eff | 19 | — | — |

### Comparison vs anchors

| Anchor | IS Sharpe | OOS Sharpe | IS Δ | OOS Δ |
|---|---:|---:|---:|---:|
| /121 multi-seed CONFIRMATION (canonical) | +1.3108 | +0.9682 | **−0.3398** | **+0.1960** |
| /121 architecturally-adjusted EXPLORATION estimate | +1.06 | +0.85 | **−0.089** | **+0.314** |

DSR = 0.0 is an EXPLORATION-mode structural artifact per `feedback_v3_dsr_mode_artifact.md` (n_trials = 315, E[max_SR] at this scale places the PSR denominator too close to SR, producing 0 numerically). INFORMATIONAL ONLY. PSR = 1.0 and PBO = 0.1412 are the operative quality metrics at EXPLORATION mode.

---

## 4. Per-Symbol IS Attribution vs /121 Baseline

| Symbol | /121 IS trades | /122 IS trades | Δ trades | /121 IS PnL | /122 IS PnL | IS PnL Δ | /121 IS WR | /122 IS WR | WR Δ |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| BCH | 85 | 85 | 0 | 119.15 | 54.53 | **−64.62** | 50.6% | 40.0% | −10.6pp |
| TRX | 79 | 82 | +3 | 7.31 | 39.76 | **+32.45** | 34.2% | 41.5% | +7.3pp |
| LDO | 9 | 12 | +3 | 9.53 | 1.48 | **−8.05** | 33.3% | 33.3% | 0.0pp |

IS aggregate: BCH IS WR collapsed −10.6pp (50.6% → 40.0%). TRX IS lifted substantially. LDO IS PnL fell with unchanged WR (roster shifted to lower-avg-PnL trades). Net IS Sharpe degraded −0.3398 vs /121 multi-seed.

---

## 5. Per-Symbol OOS Attribution vs /121 Baseline

| Symbol | /121 OOS trades | /122 OOS trades | Δ trades | /121 OOS PnL | /122 OOS PnL | OOS PnL Δ | /121 OOS WR | /122 OOS WR | WR Δ |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| BCH | 35 | 41 | +6 | 52.48 | 47.67 | **−4.81** | 48.6% | 43.9% | −4.7pp |
| TRX | 51 | 49 | −2 | 13.09 | 28.77 | **+15.68** | 43.1% | 46.9% | +3.8pp |
| LDO | 12 | 12 | 0 | −10.77 | −28.02 | **−17.25** | 25.0% | 25.0% | 0.0pp |

OOS net: +0.1960 Sharpe vs /121 multi-seed, driven by TRX OOS PnL +15.68. BCH OOS slightly negative (−4.81), LDO OOS deepened its loss (−17.25). The OOS-positive headline conceals a concerning LDO OOS deterioration (same WR, much worse total loss — this is a roster-shift to larger-loss trades, not a WR change).

**SSC pattern check**: TRX is positive IS and OOS. BCH is negative IS but only marginally negative OOS (boosted by +6 additional OOS trades). The SSC structure (TRX positive, BCH/LDO negative) is partially present IS but partially masked OOS by BCH's +6 extra trades.

---

## 6. A4 Feature Importance

### Per-symbol importance ranks (production, IS last month)

| Symbol | EDA T5 predicted rank | Production rank | Importance score | Share |
|---|---:|---:|---:|---:|
| BCH | **15/15 (INERT)** | **14/15** | 41.0 | 3.0% |
| LDO | 11/15 | **13/15** | 124.7 | 4.6% |
| TRX | 10/15 | **15/15** (dead last) | 39.7 | 3.3% |

**Portfolio rank: 14/15**, share 3.9% (importance 205.3 out of 5291.7 total).

**EDA T5 prediction vs production**: the brief predicted BCH rank 15/15 INERT, LDO rank 11/15, TRX rank 10/15. Production showed BCH rank 14/15 (near-INERT, within 1 of prediction), LDO rank 13/15 (WORSE than predicted — moved toward INERT end), TRX rank 15/15 (dead last — dramatically worse than predicted 10/15). The TRX rank drop is a carrier-inversion at the importance-allocation level: the EDA T9 SSC predicted TRX as the carrier (TRX would most use eth_ret_3d), but production shows LightGBM allocated more split-gain to eth_ret_3d on BCH (rank 14) and LDO (rank 13) than on TRX (rank 15).

**IS PnL vs importance rank dissociation**: TRX IS PnL improved +32.45 while TRX importance rank fell to 15/15 (dead last). This dissociation pattern — positive IS PnL change without importance allocation — matches the /119 C6 mechanism: eth_ret_3d reorganizes the TRX Optuna loss surface and changes which other features Optuna selects (threshold and depth changes), producing a roster change that improves TRX IS PnL, but LightGBM at prediction time does not split on eth_ret_3d at the TRX leaf level. This is loss-surface reorganization, not direct signal.

---

## 7. IC Matrix Check

| Feature | |IC| with eth_ret_3d | Signed IC |
|---|---:|---:|
| `vwap_dev_20` | **0.5613** | +0.5613 |
| `regime_momentum_signed_5d` | **0.5280** | +0.5280 |
| `btc_ret_14d` | 0.4055 | +0.4055 |
| `ema_spread_atr_20` | 0.3273 | +0.3273 |
| All others | < 0.20 | — |

**Max |IC| = 0.5613** with `vwap_dev_20`. The correlation chain `eth_ret_3d → vwap_dev_20` (|IC|=0.56) and `eth_ret_3d → regime_momentum_signed_5d` (|IC|=0.53) reflects that ETH's 3-day return is highly correlated with the same cross-asset momentum signal that `regime_momentum_signed_5d = ret_5d × sign(hurst_100 − 0.5)` already encodes for each symbol. The |IC|=0.41 with `btc_ret_14d` is expected (ETH 3d return is correlated with BTC 14d return in crypto bull/bear cycles). The high correlation with `regime_momentum_signed_5d` (0.528) and `vwap_dev_20` (0.561) explains why importance allocation is low: the information content of `eth_ret_3d` is substantially spanned by incumbents already in the 14-feature stack. This is a structural redundancy that the T2 R²=0.44 screen at EDA did not fully capture (T2 measures linear redundancy vs the full 14-feature set jointly; the pairwise ICs now reveal the specific incumbent features providing coverage).

---

## 8. ADF Stationarity

`eth_ret_3d` is stationary by construction (log-return). ADF test results per the ADF CSV:

- BCH: adf_stat = −11.84, p = 0.0, stationary = True (from full IS window)
- LDO: adf_stat = −7.51, p = 0.0, stationary = True
- TRX: adf_stat = −11.59, p = 0.0, stationary = True

All 3 symbols PASS stationarity at all IS months (after the 2-month burn-in where insufficient lags exist). PASS.

---

## 9. Falsifier Evaluation (central section)

### 9.1 Architecture-gap correction

/122 runs at EXPLORATION 3-seed mode vs /121's 10-seed CONFIRMATION. The /077 vs /059 anchor-staleness analysis measured IS compression of ~−0.27 (3-seed vs 10-seed proba-averaging). The brief's architecturally-adjusted exploration-mode estimate is IS +1.06 / OOS +0.85. All falsifier bands are evaluated vs this anchor; NEGATIVE-catastrophic uses the /121 multi-seed baseline directly (per Section 8).

### 9.2 Section 4 falsifier walkthrough

**F1 (catastrophic NEGATIVE)**: IS Δ < −0.40 vs /121 multi-seed OR OOS Δ < −0.30.
- IS Δ = −0.3398. NOT < −0.40. F1 NOT triggered.
- OOS Δ = +0.1960. NOT < −0.30. F1 NOT triggered.

**F2 (importance INERT at production)**: rank ≥ 14/15 on > 1 symbol AND POOLED lift not materially > 0.
- BCH rank 14/15, TRX rank 15/15 → 2 symbols at ≥ 14/15. YES.
- Portfolio-level: rank 14/15 (share 3.9% vs expected ~6.7% for a neutral feature). POOLED lift estimate < +0.005. YES.
- **F2 TRIGGERED.**

**F3 (suspicious-OOS-dominant)**: OOS Δ vs /121 multi-seed > +0.15 BUT IS Δ < +0.00.
- OOS Δ = +0.1960 > +0.15. YES.
- IS Δ = −0.3398 < +0.00. YES.
- **F3 TRIGGERED.** The /082/085/086 OOS-spike-artifact pattern is present: OOS outperforms IS despite the feature being importance-INERT. The mechanism is loss-surface reorganization (TRX IS PnL gain without importance allocation; same as /119 C6) generating a trade-roster shuffle that happens to improve OOS Sharpe net. This is not repeatable signal.

**F4 (TRX-carrier SSC realized)**: TRX IS PnL Δ > +5pp AND BCH IS PnL Δ < −1pp AND LDO IS PnL Δ < +1pp.
- TRX IS PnL Δ = +32.45 > +5pp. YES.
- BCH IS PnL Δ = −64.62 < −1pp. YES.
- LDO IS PnL Δ = −8.05 < +1pp. YES.
- **F4 TRIGGERED.** The T9 SSC TRX-carrier prediction materialized at the IS PnL level. However the importance rank shows TRX rank FELL to 15/15 — the carrier is a loss-surface effect, not an importance-allocation effect (dissociation confirmed).

### 9.3 SSC-RISK band-tightening assessment

The A4 SSC ratio was 3.63× (TRX carrier) at EDA. Band-tightening applied: upper bound IS Δ ≤ +0.10 / OOS Δ ≤ +0.10. Observed: IS Δ = −0.089 vs exploration anchor (below even the lower band modal range), OOS Δ = +0.314 (well above the tightened upper bound). The OOS spike violates the SSC-tightened upper bound: the brief modeled SSC risk as reducing the expected OOS lift (upper bound tightened to ≤ +0.10), but production OOS Δ = +0.314 exceeded this, consistent with F3 (suspicious-OOS-dominant) being triggered. The OOS lift is not due to reliable signal — it is the /082/085/086 OOS-spike-artifact pattern driven by the TRX loss-surface reorganization.

### 9.4 Carrier-inversion finding

EDA T9 predicted TRX as the primary eth_ret_3d carrier (TRX lift-to-POOLED ratio = 3.63×). Production importance shows TRX at rank 15/15 (dead last) while BCH is 14/15 and LDO 13/15. The TRX IS PnL gain (+32.45) occurred WITHOUT importance allocation — a dissociation matching the /119 C6 precedent. This means eth_ret_3d does not provide a direct signal to TRX; instead, its presence in the feature matrix shifted Optuna's hyperparameter optimization to a different threshold regime for TRX that happened to produce better IS trades. This is not robust signal.

---

## 10. Section 8 First-Match-Wins Verdict

Walking through Section 8 criteria in order:

1. **NEGATIVE-catastrophic**: IS Δ −0.3398 (not below −0.40), OOS Δ +0.1960 (not below −0.30). NOT triggered.
2. **NEGATIVE-no-effect**: IS Δ −0.3398 not in [−0.05, +0.05]. NOT triggered.
3. **NEGATIVE-INERT**: (a) rank ≥ 14/15 on > 1 symbol [BCH 14/15, TRX 15/15: YES]; (b) POOLED lift < +0.005 [portfolio rank 14/15, share 3.9%: YES]; (c) IS Δ vs exploration-mode anchor < +0.05 [−0.089 < 0.05: YES]. **ALL THREE CONDITIONS MET. FIRST MATCH. VERDICT: EXPLORATION-NEGATIVE-INERT.**

Note: Section 8 criterion 8 (SUSPICIOUS-OOS-DOMINANT: OOS Δ > +0.30 AND IS Δ ∈ [−0.10, +0.05]) is also met (OOS Δ = +0.314, IS Δ = −0.089), but criterion 3 fires first per the listed order. The F3 falsifier (Section 4) is also triggered independently. Both classifications point to the same root cause.

---

## 11. Mechanism Analysis

**Was the SSC-RISK TRX-carrier prediction borne out?**

Partially. At the IS PnL level: YES — TRX IS PnL gained +32.45 while BCH lost −64.62 and LDO lost −8.05, exactly matching the F4 condition. At the importance-allocation level: INVERTED — TRX importance rank fell to 15/15 (dead last) while the brief predicted rank 10/15. The carrier is real at the PnL-roster level but absent at the split-gain level.

**Did eth_ret_3d contribute direct signal or loss-surface reorganization?**

Loss-surface reorganization, matching the /119 C6 mechanism. The evidence: TRX IS PnL improved while TRX importance rank is 15/15 (dead last). LightGBM did not split on eth_ret_3d at the TRX prediction boundary; instead, the addition of eth_ret_3d to the feature matrix changed the Optuna hyperparameter search trajectory (colsample_bytree, max_depth, num_leaves interactions), placing TRX into a threshold regime with different trade-entry decisions — not because eth_ret_3d is directionally informative, but because the expanded feature space changed the local optimization landscape.

The high IC with incumbents (`vwap_dev_20` IC=0.561, `regime_momentum_signed_5d` IC=0.528) explains why importance allocation is near-zero: the incumbents already capture the same cross-asset momentum information; `eth_ret_3d` adds marginal information that trees at depth 3-5 cannot exploit beyond what the correlation-spanning incumbents provide.

The OOS Sharpe improvement (+0.196 vs /121 multi-seed) is a single-seed 3-seed-mode lottery artifact. The CPCV path distribution (frac_positive = 0.644, q25 = −0.243, q50 = +0.335) shows the median path is positive but the left tail is substantial — not evidence of reliable signal.

---

## 12. Mechanical Classification

**EXPLORATION-NEGATIVE-INERT**

First-match trigger: Section 8 criterion 3 (all 3 conditions met). Secondary confirming signals: F2 (importance INERT on 2/3 symbols at production), F3 (suspicious-OOS-dominant pattern), F4 (TRX-carrier confirmed at PnL level but absent at importance-allocation level), IC analysis (eth_ret_3d is spanned by vwap_dev_20 + regime_momentum_signed_5d incumbents at |IC| 0.56 + 0.53).

**Axis-closure implication per Section 8 criterion 1 footnote**: Section 8 criterion 1 (NEGATIVE-catastrophic) would have closed the broader OHLCV-cross-asset hypothesis. Criterion 3 (NEGATIVE-INERT) is a softer result: it closes **eth_ret_3d specifically** (this primitive is INERT due to IC-spanning by incumbents) but does NOT automatically close all ETH OHLCV derivatives. ETH-based features that are NOT spanned by the existing incumbent set (e.g., ETH realized volatility vs symbol volatility ratio, ETH regime classifier, ETH OI-weighted direction) remain testable in subsequent cycle-7 EXPLORATION slots. This is for the QR to adjudicate at /123 brief.

---

## Anomaly Notes

- The pre-flight assertion fix commit (`f88415c`) was required: the /121 setup left the guard at `len == 14`. This is a routine setup artifact from the METHODOLOGY-BOOTSTRAP; the fix was committed before the backtest ran.
- No NaN Sharpe, no zero-trade months in IS (minimum 1 trade in every active IS month).
- Random spot-check of 10 OOS trades: entry/exit math consistent, exit_reason distribution normal (TP/SL/timeout), weight_factor = 1.0 throughout (no BTC contagion fires in OOS).
- LDO OOS deepened from −10.77 to −28.02 despite unchanged WR and trade count. The worsening is in avg_pnl_pct (−0.90 → −2.34 per trade) — the LDO OOS roster shifted to worse-average-outcome trades, likely because eth_ret_3d changed the threshold at which LDO signals fire.

---

## Status

OVERALL = READY-FOR-CRITIC
