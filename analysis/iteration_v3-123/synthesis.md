# iter-v3/123 — Cycle-7 EXPLORATION #2 EDA Synthesis

## Axis under test

Sub-axis **B1 = `eth_realized_vol_50 / sym_realized_vol_50`** — ETH-vs-symbol 50-bar realized-vol REGIME RATIO. The PRIMARY candidate per the QR prompt, with 3 sister candidates (B1a log-transformed; B1b W=25 shorter-cadence; B1c W=100 longer-cadence).

**Hypothesis structural claim** (the /122 lesson applied): when ETH's 50-bar vol regime is elevated relative to the symbol's own 50-bar vol regime, this signals cross-asset risk-on regime where alt idiosyncratic moves are conditioned by ETH-led volatility. The vol-ratio is a SECOND-MOMENT cross-asset primitive — structurally orthogonal to the /122 IC-spanning incumbents `vwap_dev_20` and `regime_momentum_signed_5d` which are both FIRST-MOMENT primitives.

## /122 lesson applied

At /122 EDA, `eth_ret_3d` (a first-moment ETH primitive) passed the joint-R² screen with R²=0.44 but FAILED at production with EXPLORATION-NEGATIVE-INERT verdict. Post-mortem (Critic FINAL `9e0eeb6`) identified the missing diagnostic: pairwise IC with `vwap_dev_20` was 0.5613 and with `regime_momentum_signed_5d` was 0.5280 — substantially spanned by 2-3 incumbents at the 0.50-0.56 |IC| range.

The /122 Critic Recommendation 1 mandated: "EDA must show pairwise |IC| < 0.40 with `vwap_dev_20` and `regime_momentum_signed_5d` specifically. Joint-R² is insufficient diagnostic for ETH-derived primitives."

The /123 EDA implements this strict pairwise-IC gate.

## EDA tables produced (8 CSVs)

| Table | File | Description |
|---|---|---|
| T1 | `T1_candidate_catalog.csv` | 4 candidates: B1, B1a, B1b, B1c with categories, formulas, motivations |
| T2 | `T2_linear_redundancy_pre_falsifier.csv` | Joint R² + pairwise IC vs `vwap_dev_20` and `regime_momentum_signed_5d` (strict 0.40 gate) |
| T3 | `T3_walkforward_pooled_auc.csv` | POOLED walk-forward univariate OOF AUC + 100-permutation null |
| T4 | `T4_per_symbol_auc.csv` | Per-symbol univariate AUC (BCH/LDO/TRX) |
| T5 | `T5_importance_rank_multivariate.csv` | Per-symbol depth-4 LightGBM 14+1 importance rank + gain |
| T7 | `T7_multivariate_lift_screen.csv` | 14-feat baseline POOLED + per-symbol AUC and lift with candidate |
| T9 | `T9_ssc_risk_gate.csv` | Single-Symbol-Carrier RISK gate (the /119-NEW per /118 closeout) |
| T6 | `T6_go_nogo_verdict.csv` | GO/NO-GO synthesis combining T2/T3/T5/T7/T9 |
| T8 | `T8_adf_stationarity.csv` | ADF stationarity audit per candidate × symbol (mandatory v3 gate) |

## T6 verdict synthesis

| Candidate | Verdict | T2 R² | IC vwap_dev_20 | IC regime_momentum | T5 ranks (BCH/LDO/TRX) | T7 POOLED lift | SSC ratio |
|---|---|---:|---:|---:|---|---:|---:|
| **B1 (PRIMARY)** | **GO-SSC-RISK** | 0.3937 | **0.069** | **0.021** | 15/1/4 | **+0.0063** | 3.43× |
| B1a (log) | GO-SSC-RISK | 0.4730 | 0.066 | 0.050 | 14/1/5 | +0.0059 | 3.65× |
| B1c (W=100) | MARGINAL — ADF-FAIL | 0.3951 | 0.073 | 0.002 | 14/4/2 | +0.0021 | 2.02× |
| B1b (W=25) | REJECT (NEG lift) | 0.3152 | 0.041 | 0.052 | 15/3/3 | -0.0029 | 5.65× |

## Critical findings

### 1. Pairwise-IC gate PASSED with MATERIAL margin

The /122 Critic Rec 1 strict gate (pairwise IC < 0.40 with the two spanning incumbents) is cleared by ALL 4 candidates with substantial margin:
- B1: IC_vwap_dev_20 = **0.0687** (vs /122 eth_ret_3d's 0.5613 — **8.2× reduction**); IC_regime_momentum = **0.0205** (vs /122 eth_ret_3d's 0.5280 — **25.8× reduction**)
- B1a: 0.0664 / 0.0495
- B1b: 0.0407 / 0.0522
- B1c: 0.0725 / 0.0024

**Confirmed**: ETH realized-vol-ratio is structurally orthogonal to the two /122 IC-spanning incumbents at empirical evidence. The non-IC-spanned hypothesis is the right structural axis.

### 2. T7 POOLED lift profile

B1 produces POOLED lift **+0.0063** — above the /118+/119 production-relevance threshold (+0.003). B1a is sister-equivalent at +0.0059. B1c is below threshold (+0.0021). B1b is NEGATIVE (-0.0029).

For context: /122 A4_eth_ret_3d had POOLED lift +0.0012 (below the +0.003 threshold). B1's +0.0063 is **5.25× higher** than /122's selection — and the IC profile is cleaner. The T7 result is the strongest "GO" signal in cycle-7 axis-1 to date.

### 3. T5 multivariate importance

B1 importance allocation is the strongest in EDA history for ANY cross-asset feature on the BCH/LDO/TRX cohort:
- **LDO rank 1/15** (gain share 14.0% — the TOP feature on LDO)
- **TRX rank 4/15** (gain share 9.07%)
- BCH rank 15/15 (gain share 4.46%) — the controlling INERT signature on BCH

The asymmetry pattern is identical to /122: BCH is a BTC fork tightly BTC-coupled, structurally insensitive to ETH cross-asset signals. LDO and TRX are alts where ETH's vol regime carries real information. B1's allocation is materially stronger than /122's eth_ret_3d (which was BCH 14, LDO 11, TRX 10 — all mid-table or dead-last; B1 is BCH 15 / LDO 1 / TRX 4).

### 4. T9 SSC-RISK: TRUE (3.43× — LDO carrier)

B1's SSC ratio is 3.43× with LDO as the carrier — above the 2.0 SSC-RISK threshold. The /119 SSC-RISK band-tightening convention applies: tighten upper bounds of the predicted bands in the brief.

**Note on carrier identity**: /122 had TRX as the PnL-level carrier (despite INERT importance rank 15/15 — the /082/085/086/119 C6 dissociation pattern). B1 at EDA has LDO as the importance-level carrier (rank 1/15, gain share 14.0%) which is ALIGNED with the PnL-carrier prediction. This is a CLEANER pattern than /122 — the importance-allocation and PnL-attribution prediction are coherent rather than dissociated.

### 5. T3 univariate AUC: BELOW null q95

B1 POOLED univariate AUC = 0.4694 (q95 null = 0.5069; p=1.0). This is BELOW the null distribution at significance — a SECOND-MOMENT primitive does not directly forecast direction, only conditions it. This is structurally expected: vol-ratio is not a direction signal, it's a regime classifier that interacts MULTIVARIATELY with other features (per the T7 +0.0063 lift result).

The univariate AUC is informational ONLY for vol-ratio features per the /117 g1 hard gate convention — multivariate lift (T7) is the controlling diagnostic. (Same convention used in /118 / /119 / /122 where vol-related candidates passed multivariate but not univariate.)

### 6. T8 ADF stationarity

| Candidate | BCH | LDO | TRX |
|---|---|---|---|
| B1 (W=50) | PASS p=0.0045 | PASS p=0.0078 | PASS p=0.0076 |
| B1a (log W=50) | PASS p=0.0049 | PASS p=0.0052 | PASS p=0.0180 |
| B1b (W=25) | PASS p=0.0002 | PASS p=0.0008 | PASS p=0.0004 |
| B1c (W=100) | **FAIL p=0.139** | **FAIL p=0.114** | **FAIL p=0.124** |

B1c (longer-cadence W=100) fails ADF — the slow regime indicator does not satisfy the stationarity gate. B1 (W=50) passes cleanly across all 3 symbols.

## Selection: B1 = `eth_realized_vol_50 / sym_realized_vol_50`

**Decision**: PRIMARY candidate B1 is selected for the /123 backtest.

Rationale:
1. **Strongest non-IC-spanned profile** — clears pairwise-IC strict gate by 6-25× margin vs /122's eth_ret_3d
2. **T7 POOLED lift +0.0063** — 2.1× the +0.003 threshold; 5.25× /122's eth_ret_3d
3. **T5 importance** — LDO rank 1/15 (the strongest cross-asset feature allocation in v3 EDA history)
4. **T9 SSC-RISK** — TRUE 3.43×, but the importance-level carrier (LDO) aligns with the PnL-attribution prediction, cleaner than /122's dissociation
5. **T8 ADF** — PASS across all 3 symbols at p < 0.01
6. **Sister B1a is close** — log-transform produces sister-equivalent signal; B1 selected for simplicity (no log transform) and minor T7 edge (+0.0063 vs +0.0059)

## Pre-registered modal prediction

Given:
- **EDA signal STRONGER than /122** (5.25× T7 lift, 6-25× IC reduction, top-1 importance on LDO)
- **SSC-RISK TRUE** (band-tightening required)
- **Per-symbol asymmetry** (BCH structurally insensitive, LDO+TRX carriers)
- **/119 C6 dissociation pattern lurking** (importance allocation doesn't always translate to OOS Sharpe at production scale)

Modal outcome at production is split-distribution:
- **Mode 1 (Modal success)**: 25% — production IS Sharpe lift +0.05 to +0.20 vs /121 EXPLORATION-mode estimate
- **Mode 2 (INERT at production)**: 25% — the /082/085/086/119 C6 / /122 pattern repeats; importance EDA-strong but production loss-surface flat
- **Mode 5 (No-effect)**: 15% — common-trade fraction with /121 > 95%, no behavioral change
- **Mode 6 (SUSPICIOUS-OOS-dominant)**: 15% — single-seed loss-surface reorganization artifact (the /082/085/086 pattern repeated)
- **Mode 3 (Per-symbol role-reversal)**: 10% — LDO IS PnL NEGATIVE despite T7 LDO lift +0.0215 (the SSC inversion)
- **Mode 4 (Catastrophic)**: 5% — IS Δ < -0.40 OR OOS Δ < -0.30
- **Mode 7 (IS-overfit)**: 5% — IS spike with OOS collapse

The EDA's MARGINAL+ classification (T7 +0.0063 above threshold, T5 LDO rank 1, but SSC-RISK TRUE) brings Mode 1 probability up to 25% — materially higher than /122's 10% — but the /119 C6 dissociation pattern + SSC-RISK convention keeps the modal expectation below 50%.

## Past-only invariant + OOS-leak audit

All 4 candidates use `pandas.rolling(W, min_periods=W).std()` — canonical past-only convention identical to the parquet's `range_realized_vol_50` (verified parity with `multioffset_24h.py:296`).

OOS-leak audit (assert-style, logged in `eth_vol_ratio_screen.py` main):
- BCHUSDT: 5606 IS rows / 0 OOS rows
- LDOUSDT: 2620 IS rows / 0 OOS rows
- TRXUSDT: 5548 IS rows / 0 OOS rows

Zero OOS leakage across all 3 symbols.

## Lineage discipline cross-check

The /123 axis is NOT a re-walk of any closed path:
- /122 eth_ret_3d (cycle-7 slot 1) — FIRST-MOMENT ETH primitive; closed as IC-spanned. B1 is SECOND-MOMENT (vol-ratio) — structurally orthogonal.
- /119 C6 ret5d_signed_tbi — composed FIRST-MOMENT engineered feature; B1 is non-composed SECOND-MOMENT cross-asset. Different family.
- 7-FEED structural verdict — applies to NON-OHLCV derivatives-metadata feeds (funding, microstructure, basis). B1 is OHLCV-family (computed from close prices via log-returns and rolling std). Same OUT-OF-SCOPE status as /122.
- /088 cross-sectional re-architecture used 22-symbol XS_UNIVERSE with lambdarank; /123 keeps per-symbol architecture entirely.
- BASELINE_V3.md "Cycle 7 Axis Priorities" #1 = "HIGH — Cross-asset/external feeds: STRUCTURALLY DIFFERENT primitives than the 7 prior INERT-by-importance crypto-native feeds". B1 satisfies this.

## Hand-chosen parameter declaration

| Parameter | Value | Provenance |
|---|---|---|
| W (rolling window) | 50 bars (16.7 days at 8h) | INHERITED from the baseline `range_realized_vol_50` 50-bar canonical window (per `multioffset_24h.py:296`). NOT tuned for /123. |
| Realized-vol estimator | `rolling(50, min_periods=50).std()` of 1-bar log returns | INHERITED past-only convention from baseline. NOT tuned. |
| Ratio operator | element-wise `eth_rv_50 / sym_rv_50` with 1e-12 epsilon | Structural; epsilon prevents division-by-zero on degenerate vol values. NOT tuned. |
| ETH source CSV | `data/ETHUSDT/8h.csv` | INHERITED from /122 — same fetcher convention as BCH/LDO/TRX/BTC. |
| Merge convention | left-join on `open_time` | INHERITED from /122 `cross_btc_v3.py` pattern. |

**ZERO tuned scalars in /123.** Every numeric design choice is either inherited from the existing v3 baseline pattern or structurally fixed by the algebraic form. The 50-bar window matches the existing `range_realized_vol_50` baseline anchor feature — this is the strongest possible inheritance signal (the symbol's own realized vol at exactly this window IS a baseline feature, the cross-asset ratio extends that into ETH cross-asset territory at the same window).
