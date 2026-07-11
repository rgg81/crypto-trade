# MN4 IDEA-06 — Funding-Rate PREDICTION (diary)

**Pair:** QR+QE (single). **Model:** Opus 4.8 (Fable rate-limited / user-suspended this phase; per charter directive). **Date:** 2026-07-11/12.

## Decision: NOT BANKED for reveal. IS-gate FAIL (2 of 4).

The construction is frozen, leak-battery-clean, and honestly reported. It does not clear cost on IS. Two of four principle-anchored gates fail. This is one of the tournament's expected failures (charter: "expect most of the 10 to fail").

---

## What worked

1. **Funding-rate prediction IS learnable from microstructure.** Pooled OOF IC = 0.3715, R² = 0.1777, stable across years (2022-2024 IC in [0.29, 0.42]) and regimes (CRASH/MANIA/CHOP IC in [0.31, 0.41]). The 8-config × 5-seed ensemble is well-behaved: per-config-seed IC in [0.337, 0.374] (tight spread, no basin-lottery). G1 (prediction IC ≥ 0.20) PASSES.

2. **The predicted CHANGE has real signal.** Diagnostic: IC of (pred − cur) vs (realized − cur) = **0.3916**. The model captures the deviation-from-persistence component — the genuinely-forward-looking part of the funding signal. IC of (cur) vs (realized − cur) = **−0.4194** (raw funding mean-reverts), so the model is doing something real that raw carry does not.

3. **Leak battery clean.** Corrupt-future on the fit loop: BIT-IDENTICAL predictions for the prior month when corrupting the future OOF block (max abs diff 0.00e+00, 1200 fits). Purge == label-horizon (1 candle), 30/30 months zero overlap. Sealed-holdout guard fires BEFORE any computation. Funding-coverage assertion runs (1 LITUSDT NaN-handled, no silent-zero). 16/16 unit tests pass.

4. **Neutrality works.** Post-hedge β_BTC = +0.008 (median 0.000), β_ETH = +0.007. The BTC+ETH HedgeOverlay cancels directional exposure to G3's standard (|β| ≤ 0.35). G3 PASSES cleanly.

5. **Crisis throttle helps.** The Layer-2 gross_scalar (0.3 in CRASH) lifts Sharpe by +0.146 vs the no-throttle counterfactual (−0.189 → −0.044). It doesn't save the book but it pulls in the right direction (charter §7: per-construction Layer-2 throttle, not a shared machine).

## What failed

### G2: 1× Sharpe = −0.044 (gate ≥ 0.30). Cost kills the book.

Decomposition per candle (1× cost):
- Gross price return: ≈ −1.13e-4 (−12.4% annualized) — the short leg bleeds on price during crowded rallies.
- Funding income: −1.06e-4 (NEGATIVE drag = INCOME, +11.5% annualized) — the short leg earns carry on high-funding names.
- Turnover cost: +9.03e-5 (one-way 0.12/candle × 7.5bps) — 9.9% annualized bleed.
- Net alpha: −7.01e-6/candle → −0.77% arithmetic annual; compounds to −2.26%.

The carry income nearly cancels the price bleed, but turnover cost on top makes the book negative. Sharpe is barely below zero because the mean is small relative to vol.

### G4: CRASH-bucket mean/candle = −9.99e-5 (gate ≥ −5e-5). Blow-up in acute stress.

The book loses in every trend regime:
- **CRASH** (n=637, 12.9% of candles): Sharpe −1.57, mean/candle −9.99e-5.
- **MANIA** (n=912, 18.5%): Sharpe −1.48, mean/candle −1.95e-4.
- **CHOP** (n=3289, 66.8%): Sharpe +0.35, mean/candle +6.30e-5.

Classic funding-carry profile: earns in chop, bleeds in trends (both up and down).

## The core mechanism: model IC dominated by persistence baseline

This is the load-bearing diagnostic. The trivial baseline `funding[t+1] = funding[t]` (raw persistence) achieves pooled IC **0.5158** — HIGHER than the model's IC of 0.3715. **Δ (model − persistence) = −0.1443.** The model is a WORSE predictor of the level than the trivial persistence baseline.

Why? The 24-feature set + LightGBM regression with `min_data_in_leaf{200,500}` + `lambda_l2{1,10}` is regularized toward the cross-sectional mean. Funding rates are extremely persistent (IC 0.52 baseline), and the regularized model underweights this persistence — it tries to predict deviations, but the deviation component is small relative to the persistence component. The result: the model's predicted LEVEL is a noisier approximation of `funding[t]` than `funding[t]` itself.

Ranking on the level signal therefore approximates a NOISIER carry trade than ranking on raw current funding. The book earns carry but pays extra in turnover (noise → ranking flips → trades).

The predicted CHANGE tells a different story: IC 0.39 vs realized change — the model IS predicting the deviation. But ranking on the change is even noisier (turnover 206/yr, Sharpe −1.53) — the deviation signal is too small to harvest at daily cadence against taker+slip+funding cost.

## What I would try next (out of scope for this tournament entry)

The charter pins each pair to ONE frozen construction, so these are recorded as future axes, not pursued here:

1. **Predict the CHANGE directly (residual target).** Train the model on `(funding[t+1] - funding[t])` or on the residual after a persistence prior, with the level as a feature. This forces the model to focus its capacity on the deviation (where it has IC 0.39) rather than re-learning persistence (where it loses to the baseline).

2. **Slower cadence.** Daily rebal at 8h is too fast for this signal (turnover 132-206/yr). Weekly (rebal=21) would cut turnover 5-7× and might let the alpha survive cost. The charter seed says "daily"; a weekly variant is a different construction.

3. **Slow-funding signal blend.** Combine the predicted funding change with a slow carry signal — the change component provides the timing/exit, the slow carry provides the steady income. This is closer to "IDEA-10 born-diverse ensemble" territory.

4. **Funding-regime conditioning.** Trade the funding-prediction signal ONLY when aggregate funding is dislocated (high `mkt_fund_agg`). In normal funding regimes the carry edge is too thin; in dislocated regimes the convergence alpha is richer.

## Lessons

1. **A high prediction IC is NOT sufficient for a tradable book.** The model achieves IC 0.37 (a clear G1 PASS) but the book loses because (a) the prediction is dominated by an even-stronger persistence baseline and (b) the alpha per candle is too small to cover taker+slip+funding cost. IC ≠ edge ≠ tradable.

2. **Always compare to the persistence baseline FIRST.** Δ (model − persistence) = −0.14 was the key diagnostic — it would have flagged the construction as level-predictive-only before any backtest ran. Persistence baseline checks should be a standard pre-backtest gate for any funding-rate model.

3. **Cost-survival is the binding constraint on this dataset (again).** The charter's honest prior held: 8h/daily funding-carry doesn't survive taker+slip+funding. The two-year holdout is unlikely to be kinder.

4. **The leak battery is the win.** The construction is frozen, the OOF generation passed corrupt-future bit-identically, the purge invariant holds, the sealed-holdout guard fires before any computation, the funding-coverage assertion catches silent-zero. The negative result is honest and uncontaminated — the methodology worked even though the alpha didn't.

## Honest prior on the reveal

This is a FAIL on the IS gate. Per charter §PROCESS, a construction that fails IS does not consume a holdout reveal token. The 2-year holdout remains pristine for genuinely-better constructions. The negative result is itself a structural finding: funding-rate prediction IC ≠ tradable alpha at daily cadence on Binance perp cost structure, and a model that doesn't beat the persistence baseline on the LEVEL is not worth backtesting.

## Files (all namespaced; no git commits)

- `analysis/portfolio/mn4_idea06_construction.py`
- `analysis/portfolio/mn4_idea06_oof.py`
- `analysis/portfolio/mn4_idea06_score.py`
- `tests/test_mn4_idea06.py` (16/16 pass)
- `data/mn4_idea06/oof_predictions.parquet`, `oof_manifest.json`, `scorecard.json`
- `briefs-portfolio-mn4/IDEA-06.md`
- `diary-portfolio-mn4/IDEA-06.md` (this file)
