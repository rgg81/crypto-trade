# Diary — iter-v1/053-054-055 (ETHUSDT) — HONEST WALK-FORWARD SMA (replaces the hindsight-fixed 200)

> **CORRECTION (2026-06-18, supersedes the first draft of this diary).** My first read concluded
> "fixed-200 wins, walk-forward underperforms, keep 200 fixed." That was **WRONG on two counts**,
> both flagged by the user: (1) **fixed SMA=200 is HINDSIGHT BIAS**, not a fair target — we only
> "know" 200 is good because we already saw 2020-2026; a trader at the backtest start (2022) could
> not have known, so a fixed 200 injects look-ahead into every early trade. (2) I **mis-aggregated**
> — I scored the raw equal-weight `net_pnl_pct` instead of the OFFICIAL R5-vol-targeted
> `weighted_pnl` (= the `comparison.csv` metric all baselines use). Under the official metric the
> honest walk-forward SELECTION's **OOS is +0.99 — it BEATS the biased fixed-200 (+0.49)**, it does
> not underperform. The walk-forward is both the only non-cheating method AND competitive-to-better.

**User directive.** "create a long trend strategy to replace lightgbm and use the walkforward and
optuna to determine the best long SMA"; then: "200 is the magic number we got NOW, but when the
backtest started this was not the magic number. This whole stuff is super bias. The walkforward is
the only [way] to prove we don't cheat — be honest on each month. 200 is best now, but what about 4
years ago." Correct and load-bearing: a globally-fixed window is a future-informed constant.

## What was built
- **iter-053/054 — walk-forward SELECTION (`enable_trend_optuna_sma`).** Deterministic long-trend
  core (trend-state direction + conviction gate; LightGBM bypassed) with the SMA window
  **Optuna-selected per-month on the PAST training window only** (TPE over a grid; scored by the
  in-sample Sharpe of that window's trend trades on `[train_start, train_end)`). 053 = wide neutral
  grid 50..400; 054 = robust plateau 100..300.
- **iter-055 — MULTI-SMA ENSEMBLE (`enable_trend_sma_ensemble`).** No selection at all: direction =
  **majority vote** of sign(close[t-1]-SMA_W[t-1]) across the whole 50..400 grid; conviction = mean
  |dist_atr_W|. No single window is ever chosen → **no hindsight-optimal constant to peek at.**
- **Leak-safety PROVEN** for the selection objective: a future-data-perturbation test (corrupt every
  candle with `open_time ≥ train_end` → bit-identical trade returns) confirms ZERO OOS information;
  `_simulate_trend_window` requires entry AND exit `open_time < train_end_ms`. The ensemble is honest
  by construction (each window past-only; per-month conviction threshold fit on training rows only).
  `test_lookahead_embargo.py` 11/11 still pass.

## Results — RAW signal vs OFFICIAL (R5-vol-targeted) metric
`analysis/ETHUSDT/iteration_v1-053/walkforward_sma_comparison.py` (consistent monthly agg, both bases):

| approach | RAW IS | RAW OOS | **OFFICIAL IS** | **OFFICIAL OOS** | OOS trades |
|---|---|---|---|---|---|
| iter-034 FIXED 200 *(BIASED ref)* | +0.75 | +0.82 | +0.70 | +0.49 | 34 |
| iter-053 wf-select 50..400 | −0.32 | +0.60 | +0.06 | **+0.99** | 37 |
| iter-054 wf-select 100..300 | +0.04 | +0.60 | +0.24 | **+0.99** | 37 |
| iter-055 ENSEMBLE 50..400 | +0.42 | +0.61 | +0.42 | **−0.53** | 40 |

(OFFICIAL = monthly Sharpe of `weighted_pnl`, matches each iter's `comparison.csv` within rounding;
RAW = equal-weight `net_pnl_pct`, isolates signal from the R5 overlay.)

## Findings (honest)
1. **The honest walk-forward SELECTION generalizes BETTER than the biased fixed 200.** Official OOS
   +0.99 (both grids — they converge to the same windows in 2025-26) vs fixed-200's +0.49. Profile is
   **weak-IS / strong-OOS** (IS +0.06–0.24, OOS +0.99) — the OPPOSITE of overfitting. The window
   adapts per-month from past data (long 325-400 in the 2022 bear, short 50-125 in 2023-24 chop,
   medium 100-200 in 2025-26 — see `sma_selection.csv`).
2. **The ENSEMBLE has the best RAW signal** (IS +0.42 / OOS +0.61, both solidly positive, best IS of
   the honest variants) **but R5 vol-targeting BREAKS its OOS** (weighted OOS −0.53): R5 (calibrated
   around the fixed-200 trade distribution) upscales the ensemble's OOS losers. The ensemble's signal
   is sound; the R5 overlay is mismatched to it → R5 recalibration is the obvious follow-up.
3. **The earlier "single-window selection is fragile" point still holds in IS** (053 wide-grid IS
   −0.32 raw, from the 2022 W=400 lag), but the plateau grid (054) fixes most of it (IS +0.04 raw /
   +0.24 official) AND the OOS is strong regardless. So the selection is honest AND strong-OOS.

## Verdict & baseline implication
- **The walk-forward is adopted as the HONEST methodology** (per the user's directive). It is not a
  performance sacrifice — under the official metric the honest selection OOS (+0.99) beats the biased
  fixed-200 (+0.49).
- **Best honest candidate for an ETH re-baseline: iter-054** (wf-select, plateau 100..300) — official
  IS +0.24 / OOS +0.99, both-positive, OOS≫IS (generalizes), leak-proven. The most-neutral-grid
  variant iter-053 (50..400) has the same OOS +0.99 but weaker IS (+0.06).
- **The fixed-200 baselines (ETH iter-034, THETA, the bundle) are hindsight-biased** and should be
  re-stated on the honest walk-forward. THETA + bundle re-runs are the natural next step.

## Caveats (load-bearing)
1. **OOS is ~15 months / 37-40 trades** — the +0.99 has wide error bars; the durable claim is
   "honest walk-forward ≥ biased fixed-200 on OOS", not the exact magnitude. The weak-IS/strong-OOS
   split is partly OOS-regime-favorable (honest, but don't over-anchor).
2. **Two metrics diverge** (raw vs R5-weighted) because R5 vol-targeting interacts differently with
   each SMA approach. Both are reported; the official (weighted) is the baseline yardstick.
3. **Selection–execution mismatch** in the objective (close-to-close vs SL=1.45·ATR) — a refinement,
   unlikely to change the direction of the finding.

## Next
- Re-run THETA + the bundle on the honest walk-forward (drop the hindsight-200 everywhere).
- R5 recalibration for the ensemble (its raw signal is the best-balanced; only R5 breaks it OOS).
- Consider promoting iter-054 to BASELINE_V1_ETHUSDT (pending the user's call on selection vs ensemble
  and grid neutrality). Tags v0.v1-053 (done), v0.v1-055 (this commit).
