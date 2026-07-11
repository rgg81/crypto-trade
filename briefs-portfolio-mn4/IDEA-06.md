# MN4 IDEA-06 — Funding-Rate PREDICTION (frozen construction brief)

**Idea seed (charter row 06):** "Funding-Rate Prediction — predict next funding from microstructure; trade the predicted-vs-implied convergence. Model the RATE, not its level."

**Pair:** QR+QE (single pair). **Model:** Opus 4.8 (Fable rate-limited / user-suspended this phase; disclosed per charter).

**Status:** FROZEN byte-exact. IS-gate verdict: **FAIL** (2 of 4 gates). **Banked-for-reveal: NO.** The leak battery passes; the construction is honest; the book does not clear cost on IS. Reported with full scorecard per charter §3-§4.

---

## 1. The Construction (frozen)

### 1.1 Target
Next-candle funding rate `funding[t+1]` (the cost that will settle over the NEXT 8h candle). 1-candle forward horizon, raw rate, **no winsorization**. Per-name scalar in typical range ±1e-4 to ±1e-3 (mean +7.5e-5, std 1.2e-3 over the OOF span).

### 1.2 Features (24, frozen tuple, reused VERBATIM from MN3-G)
- Funding (5): `fund_lvl_xz`, `fund_lvl_ownpctl`, `fund_mom21_xz`, `fund_mom63_xz`, `fund_abs_xz`
- OI (5): `oi_chg9_xz`, `oi_chg90_xz`, `oi_per_dvol_xz`, `toptrader_ls_xz`, `taker_ls_oi_xz`
- Taker imbalance (3): `ti3_xz`, `ti9_xz`, `ti21_xz`
- Vol structure (3): `rvratio_xz`, `range9_xz`, `rv_ownpctl`
- Residual momentum (3): `resmom21_xz`, `resmom63_xz`, `resmom189_xz`
- Liquidity (2): `amihud30_xz`, `dvol_rank`
- Market context (3): `mkt_regime`, `mkt_corr`, `mkt_fund_agg`

All past-only at the [k-1] decision lag; PIT cross-sectional membership (no survivorship backfill); OI consumed at `.shift(1)` (5-min bar aggregation lag). All feature coverage > 97% on member-rows except OI-based features (~64% — OI archive starts 2020-09) and the two toptrader/taker L/S ratios (~43%).

### 1.3 Model
- **LightGBM regression** (L2 objective), `lr=0.05`, `n_estimators=300`, no early stopping, `feature_fraction=0.8`, `bagging_fraction=0.8/freq=1`, `deterministic=True`.
- **8-config grid** (`num_leaves{15,31}` × `min_data_in_leaf{200,500}` × `lambda_l2{1,10}`) × **5 seeds** (`{42,123,456,789,1001}`) = 40-member ensemble. The ensemble MEAN is the prediction. **Zero Optuna, zero IS-outcome-driven HP selection.**
- **Monthly walk-forward** retrain; trailing 24-month window; **purge = label horizon = 1 candle** (verified by `assert_no_label_overlap` at 30/30 months, max overlap 0 candles).
- OOF span: 2022-01 .. 2024-06 (30 months, all inside MN3 IS). No metric computed during OOF generation (pure-read input for the scorecard).

### 1.4 Signal (the HEADLINE trade; frozen)
`signal_level = -pred_mean` (HIGH = want LONG). Rank cross-sectionally on the predicted next funding level: short names whose predicted funding is HIGH (longs will pay → price pressure down → SHORT), long names whose predicted funding is LOW (predicted to flip negative → shorts will pay → price pressure up → LONG). This is the charter's "rank cross-sectionally on the PREDICTED funding" trade.

**Sensitivity (NOT the frozen gate, reported for transparency):** `signal_change = cur_fund - pred_mean` — the pure-convergence signal on the predicted CHANGE. Computed and scored; the level signal is the headline.

### 1.5 Book construction
- **Universe:** PIT top-40 by trailing 30-candle quote-volume (≥270-candle history filter; the MN3-G/`DIAG-J` convention).
- **Weighting:** `rank_neutral` (rank-demeaned dollar-neutral L/S).
- **Rebal:** every 3 8h-candles (DAILY — per charter seed).
- **Gross:** 1.0 (`sum|w|`); per-name `weight_cap=0.10`; `min_members=20` (skip rebal otherwise).
- **Beta hedge:** explicit BTC + ETH `HedgeOverlay` (past-only 270-candle betas at [k-1]; ETH leg armed at |β| > 0.10).
- **Crisis throttle (Layer-2, per-construction, charter §7):** `gross_scalar = 0.3` in CRASH regime, `1.0` elsewhere. CRASH label = frozen 90-candle -15% BTC return rule (constants a-priori, not IS-fit).
- **Cost (honest, charter §1):** taker 5bps + slippage 2.5bps per side on one-way turnover; funding on every leg. **GROUND-TRUTH 2x-cost twin** re-run for cost-robustness.

### 1.6 IS-gate thresholds (principle-anchored, NOT IS-fit)
| Gate | Threshold | Rationale |
|---|---|---|
| G1 prediction IC | ≥ 0.20 | cross-section must contain real microstructure signal (above noise) |
| G2 1x Sharpe | ≥ 0.30 | cost-survival floor (the binding constraint per charter §4) |
| G3 \|β_BTC\| post-hedge | ≤ 0.35 | neutrality: not a directional BTC bet |
| G4 CRASH mean/candle | ≥ -5e-5 | no blow-up in acute stress (~-5.5% annualized floor) |

---

## 2. IS Scorecard (honest)

### 2.1 Prediction quality (pooled OOF, n=109,134)
| Metric | Value |
|---|---|
| Pooled IC (ensemble vs realized funding[t+1]) | **0.3715** |
| Pooled R² | 0.1777 |
| Persistence baseline IC (funding[t] → funding[t+1]) | **0.5158** |
| Persistence baseline R² | 0.2735 |
| **Δ (model − persistence) IC** | **−0.1443** |
| Per-config-seed IC (min / med / max) | 0.337 / 0.359 / 0.374 |
| Per-year IC (2022 / 2023 / 2024) | 0.414 / 0.292 / 0.419 |
| Per-regime IC (CRASH / MANIA / CHOP) | 0.413 / 0.402 / 0.308 |

**Prediction-change diagnostic:** IC of (pred − cur) vs (realized − cur) = **0.3916** — the model's predicted CHANGE has real cross-sectional signal. But IC of (cur) vs (realized − cur) = **−0.4194** — raw funding mean-reverts. The model's value-add lives in the change component, not the level.

### 2.2 Headline engine metrics (LEVEL signal — frozen)
| Cost | Sharpe | Ann | MaxDD | Turnover/yr | Win |
|---|---|---|---|---|---|
| 1× (5+2.5bps + funding) | **−0.044** | −2.26% | −32.70% | 131.8 | 26.4% |
| 2× GT (10+5bps + funding) | −0.606 | −11.58% | −53.44% | 131.8 | — |
| 1× no-throttle | −0.189 | −5.35% | −36.63% | — | — |

Throttle delta Sharpe = +0.146 (crisis throttle HELPS; cuts losses in CRASH).

**Sensitivity (predicted-CHANGE signal):** Sharpe **−1.528**, ann −24.68%, maxDD −72.59%, turnover 205.9/yr. The pure-convergence trade is dramatically WORSE (turnover explosion + noisy change signal).

### 2.3 Per-year / per-half / per-regime (1× LEVEL signal)
- Per-year Sharpe: 2022 = +0.55, 2023 = +0.13, 2024 = −1.74 (degrading).
- Per-half: H1 (2020-Q1 2022) = +1.03, H2 (Q2 2022-H1 2024) = −0.28.
- Per-regime (1× LEVEL): **CRASH** n=637, Sharpe **−1.57**, mean/candle −9.99e-5; **MANIA** n=912, Sharpe **−1.48**, mean/candle −1.95e-4; **CHOP** n=3289, Sharpe **+0.35**, mean/candle +6.30e-5.

### 2.4 Neutrality (post-hedge, LEVEL signal)
- Rolling β_BTC (270c post-hedge): mean **+0.008**, median +0.000.
- Rolling β_ETH (270c post-hedge): mean +0.007, median +0.000.
- Bucket β_BTC: CRASH +0.002, MANIA +0.002, CHOP +0.007.
- Hedge: 0 ETH-armed rebals, 0 skipped rebals (BTC leg fires every rebal; ETH residual never crosses the 0.10 arming threshold on this book).

### 2.5 Cost coverage
- Turnover mean/candle = 0.1203 (one-way); cost/candle = 9.03e-5.
- Net alpha/candle = −7.01e-6.
- Funding flow/candle = −1.06e-4 (NEGATIVE = INCOME; the short leg EARNS carry on high-funding names, +11.5% annualized).
- Decomposition: gross price return ≈ −12.4% annualized; +11.5% from funding income; −9.9% turnover cost; → −10.6% arithmetic net (compounds to −2.26%).

### 2.6 IS-GATE verdict
| Gate | Threshold | Observed | Verdict |
|---|---|---|---|
| G1 prediction IC | ≥ 0.20 | 0.3715 | **PASS** |
| G2 1× Sharpe | ≥ 0.30 | −0.044 | **FAIL** |
| G3 \|β_BTC\| post-hedge | ≤ 0.35 | 0.008 | **PASS** |
| G4 CRASH mean/candle | ≥ −5e-5 | −9.99e-5 | **FAIL** |

**Banked-for-reveal: NO.**

---

## 3. Leak battery (charter §3 — all PASS)

| Check | Result |
|---|---|
| Corrupt-future positive control on the fit loop (1200 fits, OOF month 2023-04 corrupted) | **BIT-IDENTICAL** predictions for prior month 2023-03 (max abs diff 0.00e+00) |
| Corrupt-future on the funding label (`forward_funding_label`) | unit-tested: corrupting fund[t0:] leaves label[:t0-1] bit-identical |
| Purge == label-horizon invariant | verified: purge=1 = forward-1 horizon, 30/30 months zero overlap |
| Decision-lag | OOF generator trains only on rows `t_idx <= b-1-1` (purge=1); engine consumes signal[k-1] at rebal k — standard one-candle lag |
| Signal-finite membership | uses PIT top-40 universe (`build_universe` from `mn3_diag_j`); no survivorship backfill |
| Append-invariance | holds (signal pipeline has no lookback beyond the rolling feature windows) |
| Sealed-holdout guard | `mn3_guard_grid` called BEFORE any computation; the matrix builder refuses grids past the IS cutoff |
| Funding-coverage silent-zero guard | `assert_funding_coverage` runs; 1 top-40 ever-member (LITUSDT) lacks funding and is NaN-handled (not silent-zero) |

---

## 4. Mechanism (why the book fails)

The model IS a good funding-rate predictor (IC 0.37, stable across years and regimes). But:

1. **Funding rates are extremely persistent.** The trivial baseline `funding[t+1] = funding[t]` achieves pooled IC **0.52** — HIGHER than the model's 0.37. LightGBM with `min_data_in_leaf{200,500}` + `lambda_l2{1,10}` regularizes toward the mean and underweights the persistence component. **The model's level prediction is a WORSE carry proxy than raw current funding.**

2. **The level-signal book is a noisy carry trade.** Ranking on `-pred_mean` approximates ranking on `-cur_fund` (carry), with extra noise from the model's deviation-from-persistence. The book earns +11.5% annualized from funding flow on the short leg (carry income), loses −12.4% on price (crowded-long names run against the shorts in trends), and pays −9.9% in turnover cost. Net: roughly flat-negative (Sharpe −0.044).

3. **The pure change-signal (predicted change) is noisier still.** IC of pred-change vs realized-change is 0.39 (real signal), but the cross-sectional RANKING on the change is unstable day-to-day → turnover explodes to 206/yr → cost kills it (Sharpe −1.53).

4. **Regime concentration:** the book wins in CHOP (Sharpe +0.35, 67% of candles) and loses badly in CRASH (-1.57) and MANIA (-1.48) — the classic funding-carry profile. Crowded-long names keep rising in MANIA (shorts bleed on price); funding spikes during CRASH liquidation cascades whipsaw the shorts.

5. **The charter's convergence angle doesn't materialize at daily cadence on this dataset.** The alpha source (predicted funding change) is real in IC terms but too small relative to taker+slip+funding cost to harvest at 8h/daily frequency. This matches the charter's honest prior: "Cost-survival has been the binding constraint on this dataset."

---

## 5. Files (all namespaced `mn4_idea06_*`; no other pair's files touched)

- `analysis/portfolio/mn4_idea06_construction.py` — frozen construction (constants, label, matrix builder, slices, crisis scalar).
- `analysis/portfolio/mn4_idea06_oof.py` — walk-forward OOF runner (1200 fits; corrupt-future leak check).
- `analysis/portfolio/mn4_idea06_score.py` — IS scorecard (level + change signals; full engine metrics; gate verdict).
- `tests/test_mn4_idea06.py` — 16 unit tests (leak battery + invariants), all pass.
- `data/mn4_idea06/oof_predictions.parquet` — 109,440 rows × 40 prediction columns.
- `data/mn4_idea06/oof_manifest.json` — grid/seed/month/purge/corrupt-future manifest.
- `data/mn4_idea06/scorecard.json` — full scorecard JSON.
- `logs/mn4_idea06_oof.log`, `logs/mn4_idea06_score.log` — run transcripts.
- `diary-portfolio-mn4/IDEA-06.md` — this construction's diary (FAIL verdict + mechanism).

**No git commits** (charter: orchestrator commits centrally).
