# Research Brief — iter-v1/010 (BTCUSDT) — Phase 1/2 (IS-ONLY)

**Author:** Quant Research (crypto-markets). **Symbol:** BTCUSDT. **Interval:** 8h (sacred).
**Scope:** Phases 1 (EDA) + 2 (labeling), IS-ONLY. **Objective: SHARPE (risk-adjusted), NOT
absolute return, NOT beating buy-and-hold.**
**Task:** re-examine the iter-008 regimes through the CORRECT lens — a **let-winners-run book**
(iter-009 mechanism: fixed_horizon directional label, TP non-binding, SL 1.45 ATR, 7d timeout) on a
**SHARPE basis** — and decide ONE iter-010 axis: a regime GATE, or NO-GATE → the N9/3d reserve.

All numbers come from three committed, re-runnable, IS-only scripts under
`analysis/BTCUSDT/iteration_v1-010/`. Each hard-filters `open_time < OOS_CUTOFF_MS = 1742774400000`
(2025-03-24) and asserts `df["open_time"].max() < OOS_CUTOFF_MS` BEFORE any forward quantity; every
forward label / let-run trade / regime variable is computed on the IS slice only (tail rows NaN-mask
— no OOS candle exists in the frame to peek into). Regime variables are stateless & past-only
(`.shift(1)` on every rolling stat). None touches `src/`, the runner, or OOS.

- `regime_gate_letrun_sharpe.py` → `regime_gate_letrun_sharpe.csv` (17-regime let-run Sharpe scan)
- `gate_forensic_and_n9.py` → `gate_stability.csv`, `gate_directional_info.csv`, `reserve_n9_vs_n21.csv`
- `n9_robustness.py` → `n9_stability.csv`, `n9_seed_robustness.csv`

**Simulation (explicit, faithful to iter-009).** The deployed directional specialist is proxied by a
purged forward-chaining CV LightGBM (5 folds, 3-bar embargo, shallow regularized config) on the exact
**iter-009 19-col HYBRID** set, predicting the fixed_horizon N-candle forward return; trade direction
= sign(prediction). The **let-winners-run trade** then enters at the candle close in that direction
and exits at the FIRST of {protective SL at 1.45 ATR adverse, N-candle timeout close} — TP is
**non-binding** (winners run to timeout), exactly the iter-009 `atr_tp=100` design. Trade return is
net of a 0.1% round-trip fee. Sharpe = mean/std of those trade returns, annualized by
`√(trades/yr)`. **Proxy is DIRECTION-ONLY** per the campaign's thrice-confirmed proxy-overprediction
lesson (FE N21 proxy +1.28 → backtest −0.09); magnitudes here are relative ranking signals, not
backtest forecasts.

---

## 0. Headline finding (read this first)

**No regime gate produces timing alpha on a SHARPE basis — every Sharpe-lifting regime is the
iter-008 beta pattern reborn, and crucially it INVERTS in the most-recent IS third (T3, the period
nearest OOS), which is exactly why iter-009 went OOS −0.74. The decisive, seed-robust win is the
reserve axis: shorter horizon N9 (3d) lifts the BLIND ungated hit-rate 34.3% → 44.5%, the model's
annualized Sharpe +0.66 → +1.17 (6/6 seeds, spread 0.25), and — uniquely anywhere in this analysis —
the model BEATS always-LONG ungated, with NO T3 inversion (3/3 thirds positive). RECOMMENDATION:
NO-GATE → fixed_horizon N9 (3d).**

The iter-008 forensic dismissed regimes on a RETURN basis (always-LONG out-returned the model). This
brief re-ran the question on the mandated SHARPE basis, with the actual let-winners-run book. The
verdict is the same — but now it is earned on the correct yardstick, and it points to a concrete,
robust alternative rather than another null.

---

## 1. The regime-gate scan (Sharpe basis, let-winners-run book) — `regime_gate_letrun_sharpe.csv`

17 stateless regimes, IS-only OOF, N=21 (7d) let-run book. `sharpe_ann` = model let-run annualized
Sharpe; `LONG_sharpe_ann` = always-LONG-in-regime annualized Sharpe (the alpha bar); `clears_be` =
payoff > breakeven payoff `(1−WR)/WR`; **TIMING_ALPHA** = model beats BOTH ungated AND
always-LONG-in-regime AND clears breakeven. Trades/mo is the degeneracy guard (≥~10/mo).

| gate | n | trades/mo | WR | payoff | be_payoff | clears_be | **model Sₐₙₙ** | **LONG Sₐₙₙ** | TIMING_ALPHA |
|---|---|---|---|---|---|---|---|---|---|
| **UNGATED (all OOF)** | 4552 | 72.6 | 0.343 | 2.041 | 1.920 | ✓ | **+0.656** | +1.438 | ✗ |
| TREND100 up | 2483 | 39.6 | 0.365 | 2.046 | 1.741 | ✓ | +1.305 | +1.533 | ✗ |
| TREND100 down | 2069 | 33.0 | 0.316 | 2.056 | 2.168 | ✗ | −0.379 | +0.486 | ✗ |
| TREND50 up | 2365 | 37.7 | 0.353 | 2.090 | 1.836 | ✓ | +1.033 | +1.151 | ✗ |
| TREND200 up (slow) | 2541 | 40.5 | 0.350 | 2.126 | 1.861 | ✓ | +1.059 | +1.850 | ✗ |
| VOL high (natr>p67) | 1478 | 23.6 | 0.404 | 1.526 | 1.476 | ✓ | +0.211 | +0.437 | ✗ |
| VOL mid | 1317 | 21.0 | 0.321 | 2.331 | 2.113 | ✓ | +0.566 | +1.847 | ✗ |
| VOL low (natr<p33) | 1757 | 28.0 | 0.307 | 2.399 | 2.260 | ✓ | +0.387 | +0.177 | ✗ (Sₐₙₙ<ungated) |
| **ADX≥25 (trend)** | 2352 | 37.5 | 0.362 | 2.098 | 1.761 | ✓ | **+1.351** | +1.729 | ✗ |
| ADX<20 (chop) | 1296 | 20.7 | 0.339 | 1.904 | 1.952 | ✗ | −0.148 | +0.525 | ✗ |
| funding z≥0 | 2461 | 39.2 | 0.331 | 2.137 | 2.020 | ✓ | +0.442 | +0.574 | ✗ |
| funding z<0 | 2091 | 33.3 | 0.356 | 1.934 | 1.810 | ✓ | +0.486 | +1.460 | ✗ |
| TREND100up & VOLhigh | 799 | 12.7 | 0.426 | 1.542 | 1.350 | ✓ | +0.643 | +0.687 | ✗ |
| **TREND100up & ADX≥25** | 1244 | 19.8 | 0.363 | 2.240 | 1.752 | ✓ | **+1.400** | +2.025 | ✗ |
| VOLhigh & ADX≥25 | 1032 | 16.5 | 0.422 | 1.496 | 1.372 | ✓ | +0.458 | +1.059 | ✗ |
| TREND100up & fund z<0 | 1156 | 18.4 | 0.367 | 1.868 | 1.726 | ✓ | +0.458 | +1.082 | ✗ |
| ADX≥25 & fund z<0 | 1049 | 16.7 | 0.382 | 2.010 | 1.616 | ✓ | +1.124 | +1.491 | ✗ |

**Reads (Sharpe basis, NOT return):**
- **Zero regimes earn TIMING_ALPHA.** The four regimes that lift the model's Sharpe the most
  (TREND100up +1.31, ADX≥25 +1.35, TREND100up&ADX≥25 +1.40, ADX≥25&fund-z<0 +1.12) are exactly the
  regimes where **always-LONG-in-regime lifts MORE** (+1.53, +1.73, +2.02, +1.49). Gating to a
  trending regime raises the model's Sharpe — but only by riding the regime's directional drift; it
  never beats simply being long in that drift. **This is beta, not timing alpha**, now confirmed on
  the Sharpe yardstick (iter-008 found the same on the return yardstick).
- The one regime where model beats always-LONG (**VOL-low**, +0.39 vs +0.18) is a *low-absolute*
  Sharpe BELOW the ungated +0.66, with a 30.7% WR — it fails the "beats ungated" leg. It is the
  calm regime with little directional payoff to capture; not a deployable edge.
- Several gates clear the breakeven payoff hyperbola handsomely (VOL-low payoff 2.40 vs be 2.26),
  but a clearing payoff with a sub-ungated Sharpe is the positive-skew/lumpy profile that does not
  help the objective.

**The gate scan alone is not the kill — a higher always-LONG Sharpe does NOT by itself reject a
gate** (the deployed book is the model, not always-LONG). The kill is the stability forensic below.

---

## 2. Gate stability forensic — every gate INVERTS in T3 — `gate_stability.csv`

Model let-run annualized Sharpe per chronological IS third (T1 ..2022-06, T2 ..2023-10, T3 ..2025-03,
i.e. T3 is the IS slice nearest OOS):

| gate | T1 | T2 | **T3 (nearest OOS)** | thirds+ | LONG T1/T2/T3 |
|---|---|---|---|---|---|
| UNGATED | +0.35 | +0.91 | **−0.18** | 2/3 | +0.14 / +1.04 / +1.57 |
| TREND100 up | +1.00 | +1.32 | **−0.08** | 2/3 | +0.85 / +1.01 / +0.87 |
| ADX≥25 | +1.17 | +1.26 | **−0.51** | 2/3 | +0.92 / +1.18 / +1.01 |
| TREND100up & ADX≥25 | +0.87 | +1.68 | **−0.25** | 2/3 | +0.58 / +2.05 / +1.14 |
| ADX≥25 & fund z<0 | +0.58 | +1.24 | **−0.00** | 2/3 | +0.66 / +1.40 / +0.58 |

**Decisive:** the model's "edge" in every candidate gate is the 2021–2023 bull/recovery thirds; it
goes **negative in T3** (the recent regime, the IS slice that most resembles OOS) in all of them,
while always-LONG stays strongly positive in T3 (+0.87 to +1.14). This is the precise mechanism that
produced iter-009's IS +0.04% net / OOS −15.94%: the model is period-fragile, and the failing period
is the recent one. **Gating to these regimes would lock in the fragile, sign-inverting beta exposure
— the exact profile the v1 merge gate was rewritten to reject — not fix the hit rate.**

### Directional-info forensic — the model adds nothing over always-LONG — `gate_directional_info.csv`

| gate | n | dir_acc | frac_short | **model − always-LONG mean (paired)** |
|---|---|---|---|---|
| UNGATED | 4552 | 0.4947 | 0.349 | **−0.187%** |
| TREND100 up | 2483 | 0.5155 | 0.362 | **−0.086%** |
| ADX≥25 | 2352 | 0.5200 | 0.266 | **−0.136%** |
| TREND100up & ADX≥25 | 1244 | 0.5185 | 0.267 | **−0.287%** |
| ADX≥25 & fund z<0 | 1049 | 0.5491 | 0.205 | **−0.216%** |

dir_acc creeps to 0.52–0.55 in trending regimes, but the model's per-trade let-run mean is **below**
always-LONG's on the SAME candles in EVERY gate — and the most negative gap is in the highest-dir_acc
gate. The model's shorts (frac_short 0.20–0.36) destroy value relative to staying long in a drifting
regime. **No regime turns the N=21 model into a Sharpe-positive timing alpha that beats
always-LONG-in-regime.** The gates are ruled out on the Sharpe basis, with the numbers shown — not
dismissed on return.

---

## 3. Reserve axis — N9 (3d) — the robust win — `reserve_n9_vs_n21.csv`, `n9_*.csv`

A shorter horizon trades payoff for hit-rate. The result is unambiguous (UNGATED, no gate needed):

| horizon | n | trades/mo | **WR** | payoff | be_payoff | clears | **model Sₐₙₙ** | **LONG Sₐₙₙ** |
|---|---|---|---|---|---|---|---|---|
| N=21 (7d) — iter-009 | 4552 | 72.6 | 0.343 | 2.041 | 1.920 | ✓ (margin 0.12) | +0.656 | +1.438 |
| **N=9 (3d) — reserve** | 4560 | 72.7 | **0.445** | 1.371 | 1.247 | ✓ (margin 0.12) | **+1.069** | +0.808 |

The shorter horizon lifts the blind WR 34.3% → **44.5%**. Payoff drops (2.04 → 1.37) but breakeven
drops in lockstep (1.92 → 1.25), so it clears by the same margin — while the higher WR sharply
reduces per-trade dispersion, lifting the Sharpe. **And for the first time anywhere in this analysis,
the model BEATS always-LONG ungated (+1.07 vs +0.81) — genuine directional information, no gate
required.**

### N9 stability — NO T3 inversion — `n9_stability.csv`

| third | n | **model Sₐₙₙ** | WR | dir_acc | LONG Sₐₙₙ | model>LONG |
|---|---|---|---|---|---|---|
| T1 (..2022-06) | — | **+0.548** | 0.462 | 0.525 | −0.189 | ✓ |
| T2 (..2023-10) | — | **+0.727** | 0.430 | 0.502 | +0.629 | ✓ |
| **T3 (..2025-03)** | — | **+0.631** | 0.443 | 0.509 | +1.230 | ✗ |

**3/3 thirds positive — and no T3 inversion** (T3 +0.63, vs every N=21 gate going negative in T3).
The model beats always-LONG in the bear/sideways T1+T2 (where always-LONG is weak/negative: T1 LONG
−0.19) and stays solidly positive in the bull T3. Always-LONG wins T3 (1.23 vs 0.63) — expected and
ACCEPTABLE on a Sharpe basis: the model is positive, just less than levered long-beta in a raging
bull. That is the controlled-drawdown, regime-robust profile we want; it is NOT the fragile
sign-inverting profile the gates show.

### N9 seed robustness — sign AND magnitude robust — `n9_seed_robustness.csv`

6 seeds {42,123,456,789,1001,2024}, ungated annualized Sharpe: **mean +1.167, min +1.060, max
+1.311, spread 0.251, 6/6 positive, 6/6 beat always-LONG.** Spread 0.25 is well under v1's
basin-lottery threshold (0.50) — by contrast iter-009's N=21 19-col proxy had spread >0.50 (the flag
fired). **N9 is the cleanest sign-and-magnitude-robust signal of the whole campaign.**

---

## 4. RECOMMENDATION — NO-GATE → fixed_horizon N9 (3d)

**Decisive choice: NO-GATE. iter-010 = KEEP the let-winners-run execution, KEEP the 19-col HYBRID
feature set, SHORTEN the directional label horizon from fixed_horizon N=21 (7d) to fixed_horizon
N=9 (3d), and shorten the execution timeout to 9 candles (3d). No regime gate.**

Why not a gate (Sharpe-basis, per the mandate — NOT return): no regime earns timing alpha. Every
Sharpe-lifting regime (a) is out-Sharpe'd by always-LONG-in-regime (beta, not alpha), (b) inverts in
the most-recent IS third T3, and (c) shows model−always-LONG < 0 on the same candles. A gate built on
these would lock in the period-fragile beta that produced iter-009's OOS −0.74. These are the
Sharpe-basis numbers that rule the gates out (§1–§2), not a return-basis dismissal.

Why N9 (the reserve, promoted to PRIMARY): it directly attacks the diagnosed binding constraint
(the blind hit rate) at the source. WR 34.3% → 44.5%; ungated model annualized Sharpe +0.66 → +1.17;
the model beats always-LONG ungated (timing alpha, finally); 3/3 thirds positive with no T3
inversion; 6/6 seeds positive, spread 0.25 (no basin-lottery). It needs no regime conditioning, so it
adds no fragile state.

### Exact iter-010 config
- **Feature columns (19, all in parquet — no regen):** the iter-009 HYBRID set verbatim —
  `trend_adx_7, vol_garman_klass_10, vol_atr_5, vol_taker_buy_ratio, vol_taker_buy_ratio_sma_5,
  vol_mfi_7, mom_rsi_9, stat_autocorr_lag1, mr_pct_from_high_5, vol_cmf_10, ent_shannon_10,
  trend_adx_14, trend_supertrend_14_3, btc_funding_spread_30_90, funding_rate_zscore_30,
  stat_autocorr_lag5, vol_range_spike_72, mr_rsi_extreme_14, stat_kurtosis_20`.
- **Label:** `label_mode="fixed_horizon"`, `label_timeout_minutes=4320` (= 9 candles = 3d at 8h;
  N = `timeout_minutes // 480`). `use_atr_labeling=False` (barriers not scanned in fixed_horizon).
- **Execution (KEEP iter-009 let-winners-run, ONLY shorten timeout):** `atr_tp=100.0` (TP
  NON-BINDING — winners run), `atr_sl=1.45` (cut losers), **exec timeout = 9 candles (3d)** to match
  the label horizon (iter-009 used 21/7d; this is the single coupled change). R2 OFF.
- **Cadence/budget:** EXPLORATION first — K=3 seeds, n_trials=18, 2h cap, slippage 2 (honest costs),
  training_days unchanged (sacred range). If EXPLORATION holds, advance to K=20 confirmation.
- The ONLY changes vs iter-009 are the **label horizon 21→9** and the **coupled exec timeout 21→9**.
  Features, execution-asymmetry, costs, seeds, and the runner wiring are otherwise byte-identical —
  QE keeps /002–/009 wiring intact and changes only `label_timeout_minutes` + exec timeout.

### Predicted IS Sharpe effect
Real backtest IS Sharpe predicted to flip from iter-009's **−0.09** to **clearly positive** (sign
high-confidence; magnitude DIRECTION-ONLY per the proxy lesson — do NOT bank the +1.17 proxy). The
mechanism: WR 34.3%→44.5% pushes the realized payoff comfortably above breakeven (margin held at
0.12 in payoff terms) AND smooths the per-trade equity curve (the dispersion that gave iter-009 a
negative Sharpe despite +4.43% net). Trade rate ~72/mo, far above the ≥10/mo floor — no degeneracy.

### Risk Mitigation
- **No new state introduced** (no gate) → no new fragility surface vs iter-009. The let-winners-run
  SL at 1.45 ATR is the loss-cut primitive; the 3d timeout caps single-trade exposure tighter than
  iter-009's 7d (lower per-trade tail).
- R3 OOD Mahalanobis gate and the confidence-threshold trade filter remain as in the iter-009 wiring
  (unchanged) — they provide the OOD/low-conviction screen without regime conditioning.
- Concentration N/A (single symbol). Trade-rate floor satisfied (~72/mo ≫ 10/mo).

### Pre-registered both-positive coherence FALSIFIER (NEGATIVE verdict if any holds)
1. Confirmation IS Sharpe (multi-seed mean) is **≤ 0**; OR
2. The profile inverts — always-LONG / B&H beta beats the model's directional **Sharpe** ungated at
   confirmation (the lift was BTC drift, not the model's higher-WR timing) — i.e. the §3 "model beats
   always-LONG ungated" result fails to reproduce in the real backtest; OR
3. Fewer than **7/20** confirmation seeds are positive (sign not robust at full cadence); OR
4. The recent-period (T3-analog) sub-window Sharpe is **negative** while earlier sub-windows carry
   the result (the N=21 T3-inversion failure mode recurs at N9).
Any of these → the shorter-horizon axis is FALSIFIED for BTC 8h and the next QR should pivot the axis
(e.g. an even shorter N=6/2d hit-rate push, or a confidence-threshold trade filter on top of N9).

### Kill-switch (mid-flight)
Abort the EXPLORATION run if the exit mix shows TP exits firing (would mean the non-binding-TP design
broke — TP must stay non-binding so winners run), or if EXPLORATION K=3 mean IS Sharpe < −0.20 (worse
than iter-009 — the horizon change backfired and N9 is not the lever).

---

### Appendix — methodology / OOS-vigilance attestation
- All three scripts hard-filter `open_time < OOS_CUTOFF_MS` and assert `df["open_time"].max() <
  OOS_CUTOFF_MS` BEFORE any forward computation; `df_full` produces ONLY the IS slice; OOS rows
  (open_time ≥ cutoff) are never read.
- Forward labels (fixed_horizon N=21 / N=9 forward return) and the let-winners-run trade simulation
  are built on the IS slice only; the forward reach at the IS tail NaN-masks (no OOS candle to index)
  — no peeking. OOF candles only (purged 5-fold, 3-bar embargo) enter every statistic.
- Regime variables are stateless & past-only: SMA-slope signs use `.shift(1)`; NATR terciles use
  rolling-250 quantiles with `.shift(1)`; ADX is a past-only indicator; `funding_rate_zscore_30` is
  the already-lagged parquet column.
- The let-run trade faithfully reproduces the iter-009 execution: enter at close in model direction,
  exit at min(SL 1.45 ATR adverse, N-candle timeout), TP non-binding, 0.1% round-trip fee; ATR uses
  the runner convention `close × vol_natr_21 / 100` (`lgbm.py:758`).
- The LightGBM directional read is a faithful DIRECTION-ONLY proxy of the deployed bagged specialist;
  per the campaign's thrice-confirmed proxy-overprediction lesson, magnitudes are relative ranking
  signals, not backtest forecasts. `src/`, the runner, and OOS are UNMODIFIED.
- Scripts re-runnable; lint clean (`ruff check`, ignoring idiomatic `X`/`Xm` design-matrix and
  `rowsA/B/C` section-label naming, consistent with iter-008/009 convention).
