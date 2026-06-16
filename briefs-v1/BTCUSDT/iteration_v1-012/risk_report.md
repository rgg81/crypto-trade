# Risk Report — iter-v1/012 (BTCUSDT) — Phase 4.7 (Risk-primitive design + IS-only calibration)

**Author:** Risk Engineer (RE), crypto-trade v1 single-symbol track. **Symbol:** BTCUSDT.
**Interval:** 8h (sacred). **Objective: SHARPE (risk-adjusted), NOT absolute return, NOT B&H.**
**Mandate (from iter-011 QR forward-rec + diary Next):** design a **regime-aware, vol-scaled,
LONG-bias position-SIZING primitive** that de-levers the iter-010 let-winners-run book in
down-trends — capture the +2.47 bull edge, survive the bear/correction regimes where the long edge
is dead. **NOT a binary gate** (iter-011 §3.3 ruled gates out: they amplify the recent-sub-period
T3 inversion). A smooth, continuous, stateless scaler in `[floor, 1.0]`, composing with R5.

All numbers come from three committed, re-runnable, **IS-ONLY** scripts under
`analysis/BTCUSDT/iteration_v1-012/`. Each hard-filters `open_time < OOS_CUTOFF_MS = 1742774400000`
(2025-03-24) and asserts `df["open_time"].max() < OOS_CUTOFF_MS` BEFORE any forward quantity. The
expanding walk-forward (faithful to iter-010/011) trains only on candles strictly before each test
window minus an embargo `EMBARGO_C = N+3 = 12` candles (≥ the N=9 label horizon). The trend-regime
signal is **stateless & past-only** (every rolling stat `.shift(1)`). The FLOOR / transition band
are calibrated ONLY on the IS sub-period stability + pooled-Sharpe metric; **no OOS row is ever
read.** Knowing "iter-010 OOS = −1.48" was the MOTIVATING fact; nothing here is fit/selected against
OOS. `src/`, the runner, and OOS are UNMODIFIED.

| script | outputs |
|---|---|
| `trend_scaled_sizing.py` | `grid_calibration.csv`, `subperiod_with_without.csv`, `robustness.csv` |
| `delever_pooled_effect.py` | `floor_sweep.csv`, `seed_robustness_floor25.csv` |
| `traderate_and_stress.py` | `slippage_stress.csv` (+ trade-rate / regime-distribution prints) |

---

## 0. Headline finding (read this first)

**The primitive WORKS — but ONLY on the correct metric.** A continuous, stateless 200-SMA-slope
trend-z multiplier applied LONG-only to the iter-010 let-run book:

- **lifts pooled IS Sharpe +1.957 → +2.326 on the LONG book (Δ +0.37) and +1.870 → +2.040 on the
  FULL book (Δ +0.17)**, and **is seed-robust: all 5 seeds positive on both** (LONG Δ mean +0.411,
  min +0.370; FULL Δ mean +0.205, min +0.170);
- **cuts proxy max-drawdown −30%** (LONG book 429 → 299 cum-pct points), all 5 seeds reduce
  (mean −31.7%);
- **cuts the bear-regime loss contribution 58%** (sum of negative bear-sub-period weighted returns
  −1321 → −549) while **retaining 80% of the bull-regime gain** (4696 → 3750) — exactly the
  "trade some absolute return for a much higher Sharpe / lower drawdown" deal the track mandates;
- **does NOT change trade count** (min multiplier 0.250 > 0 → no trade is gated; FULL book 73.5/mo
  IS, identical ON vs OFF, ≫ the 10/mo floor; OOS rate is unchanged from iter-010 by construction);
- **survives cost-stress**: the FULL-book lift is +0.170 / +0.181 / +0.192 at slippage
  {0, 2, 4} bps/side — it GROWS as costs rise (de-levering the SL-heavy bear regime saves more
  slippage when slippage is higher).

**CRITICAL METHODOLOGICAL FINDING — why the obvious metric is the WRONG one.** Sharpe is
**invariant to a constant size multiplier within a window**. The QR's iter-011 unifying metric
(per-sub-period Sharpe) therefore **cannot be moved by a sizing primitive**: scaling a whole bear
sub-period by 0.4× leaves its own Sharpe unchanged, and where the multiplier *varies* within the
window it can even *lower* that window's Sharpe by chance (§1). My first script confirmed this — the
per-sub-period table shows the negative sub-periods get slightly **worse**, not better. **This is
not a failure of the primitive; it is a category error in the metric.** A de-lever sizing primitive
does not repair a bear sub-period's internal risk/reward — it shrinks that regime's CONTRIBUTION to
the **pooled** return distribution (the thing Sharpe is actually computed on at deployment) and to
**drawdown** (the thing the track de-levers to protect). On those correct metrics (§2–§3) the
primitive delivers a clean, seed-robust, cost-robust lift. **The iter-011 conclusion that "no lever
closes the gap" was correct for model/feature/window/gate levers and for the per-sub-period Sharpe
metric — it is NOT correct for a sizing primitive measured on pooled Sharpe + drawdown.**

**SPEC (full detail in §6): a LONG-only, smooth, stateless `trend_scale ∈ [0.25, 1.0]` multiplier
driven by the past-only 200-SMA-slope z-score, inserted as one more `vt_scale = vt_scale *
trend_scale` step in the backtest pipeline.** Needs a NEW `run_model`/`BacktestConfig` field + QE
wiring (flagged §6.3). Predicted IS effect: FULL-book Sharpe +1.87 → ~+2.04, max-DD −30%,
trade-rate unchanged. Pre-registered both-positive coherence falsifier in §7.

---

## 1. The metric trap — per-sub-period Sharpe CANNOT be the target for a SIZING primitive

`trend_scaled_sizing.py §2`. Chosen grid config (slope_lb=20, z_lo=−0.5, z_hi=0.0, floor=0.30 —
the per-sub-period-score-best); per-sub-period LONG Sharpe WITH vs WITHOUT the multiplier:

| sub-period | regime | n | Sharpe OFF | Sharpe ON | Δ | avg mult |
|---|---|---:|---:|---:|---:|---:|
| 2021-01 | bull | 427 | +0.345 | +0.867 | **+0.522** | 0.798 |
| 2021-07 | bull | 370 | +2.143 | +1.854 | −0.290 | 0.832 |
| **2022-01** | **NEG** | 301 | **−0.952** | **−1.309** | **−0.356** | **0.417** |
| **2022-07** | **NEG** | 293 | **−0.889** | **−1.103** | **−0.213** | **0.413** |
| 2023-01 | bull | 291 | +1.312 | +0.781 | −0.530 | 0.905 |
| 2023-07 | bull | 336 | +1.597 | +1.153 | −0.444 | 0.757 |
| 2024-01 | bull | 214 | +1.712 | +1.815 | +0.103 | 0.963 |
| 2024-07 | bull | 248 | +0.918 | +1.097 | +0.179 | 0.668 |
| **2025-01** | **NEG** | 69 | **−0.757** | **−0.742** | **+0.015** | 0.735 |

**Read this carefully — it is the load-bearing methodological point of the report.** The multiplier
**correctly identifies and de-levers the bear sub-periods** (avg mult 0.41–0.42 in 2022-H1/H2 vs
0.80–0.96 in the bull sub-periods — the trend signal is doing exactly what it should). And yet the
per-sub-period **Sharpe** of those negative windows gets slightly WORSE. This is purely mechanical:
Sharpe = mean/std × √(annualization), and a constant multiplier `c` scales both mean and std by `c`,
leaving the ratio unchanged; the only residual effect is from the multiplier *varying* within the
window, which here happens to correlate with the better trades, nudging the ratio down. **A sizing
primitive structurally cannot lift a sub-period's own Sharpe — so per-sub-period Sharpe is the wrong
falsifier for this axis.** (This is also why the iter-011 BULL-gate "fix" looked attractive on
headline Sharpe but failed on stability: a gate changes *which* trades exist, a scaler changes only
their *size*.) Honest reporting demands I flag this rather than cherry-pick the metric — and then
measure the primitive on the metric it actually moves.

---

## 2. The CORRECT metric — pooled Sharpe + drawdown + regime loss-contribution (FLOOR sweep)

`delever_pooled_effect.py`. Pooled annualized Sharpe of size-weighted per-trade returns (the
deployment-relevant figure), proxy max-DD (running-sum equity, additive book), and the
bear/bull regime loss/gain decomposition. LONG-bias multiplier (longs scaled, shorts size 1.0).
Fixed band slope_lb=20, z_lo=−0.5, z_hi=0.0; FLOOR is the single load-bearing knob:

| floor | LONG pooled Sharpe | FULL pooled Sharpe | LONG maxDD | bear loss-sum | bull gain-sum | avg mult (long) |
|---:|---:|---:|---:|---:|---:|---:|
| **1.00 (OFF)** | +1.957 | +1.870 | 429.4 | −1321.3 | 4695.6 | 1.000 |
| 0.50 | +2.243 | +2.012 | 342.6 | −806.2 | 4065.1 | 0.800 |
| 0.40 | +2.284 | +2.027 | 325.3 | −703.1 | 3939.0 | 0.760 |
| 0.35 | +2.301 | +2.033 | 316.6 | −651.6 | 3875.9 | 0.740 |
| 0.30 | +2.315 | +2.038 | 307.9 | −600.1 | 3812.9 | 0.720 |
| **0.25 (CHOSEN)** | **+2.326** | **+2.040** | **299.2** | **−548.6** | **3749.8** | **0.700** |
| 0.20 | +2.334 | +2.042 | 295.4 | −497.1 | 3686.7 | 0.680 |
| 0.15 | +2.339 | +2.041 | 295.1 | −445.6 | 3623.7 | 0.660 |
| 0.10 | +2.339 | +2.039 | 294.8 | −394.0 | 3560.6 | 0.640 |
| 0.00 | +2.330 | +2.029 | 294.1 | −291.0 | 3434.5 | 0.600 |

**Reads:**
- **Pooled Sharpe rises monotonically as the floor drops to ~0.15–0.20, then plateaus and turns
  over** (FULL-book peak +2.042 at floor 0.20; LONG-book +2.339 at floor 0.10–0.15). The lift is
  REAL and large on the metric that matters at deployment.
- **Max-drawdown falls sharply** (LONG 429 → 299 at floor 0.25, −30%; full-book DD bottoms ~298 then
  rises slightly below floor 0.10 as the bull gain starts thinning the equity drift).
- **The bear loss-sum shrinks monotonically** (−1321 → −549 at floor 0.25, a 58% cut) — this is the
  primitive doing its job: it removes the bleed from the down-trend regimes.
- **CHOSEN FLOOR = 0.25.** It captures ~essentially all of the Sharpe lift (FULL +2.040 vs the
  +2.042 peak), a −30% DD cut, and a 58% bear-loss cut, while **retaining 80% of the bull gain**
  (3750/4696) and **never collapsing to a near-zero floor** that would (a) be an unstable extreme on
  a single knob and (b) erode the bull edge with no Sharpe payoff. Floors below 0.20 keep cutting
  bear-loss but the Sharpe is flat-to-down and the bull gain keeps eroding — diminishing returns and
  rising fragility. 0.25 is the IS-best balance, deliberately NOT the knife-edge optimum.

---

## 3. Seed robustness — the pooled-Sharpe lift + DD reduction hold for ALL 5 seeds

`delever_pooled_effect.py §SEED`. Chosen floor 0.25, expanding WF, 5 seeds:

| seed | LONG OFF | LONG ON | LONG Δ | FULL OFF | FULL ON | FULL Δ | LONG maxDD OFF→ON | DD red. |
|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 42 | +1.957 | +2.326 | +0.370 | +1.870 | +2.040 | +0.170 | 429→299 | −30.3% |
| 123 | +1.834 | +2.237 | +0.403 | +1.752 | +1.959 | +0.207 | 423→309 | −26.9% |
| 456 | +1.697 | +2.126 | +0.429 | +1.544 | +1.759 | +0.215 | 443→295 | −33.4% |
| 789 | +1.756 | +2.202 | +0.446 | +1.663 | +1.897 | +0.233 | 402→268 | −33.2% |
| 1001 | +1.869 | +2.277 | +0.407 | +1.785 | +1.987 | +0.202 | 402→263 | −34.6% |

**LONG Δ mean +0.411 (min +0.370, max +0.446; ALL positive). FULL Δ mean +0.205 (min +0.170; ALL
positive). max-DD reduction mean −31.7% (ALL reduce).** Per `feedback_v1_basin_lottery_vigilance`,
the per-seed spread on the FULL-book lift is 0.063 (≪ 0.50) — **this is NOT a basin-lottery
artifact**; the de-lever benefit is a property of the data/regime structure, not of a particular
model draw. This mirrors the iter-011 §3.1 finding that the bear sub-period signs are
seed-deterministic — the same regime structure that makes the bleed seed-stable makes the de-lever
fix seed-stable.

---

## 4. Mechanism + robustness checks

`traderate_and_stress.py`.

**(A) Trade-count invariance + trade-rate.** Min multiplier across all long trades = **0.250 > 0**
→ no trade is ever gated off; trade COUNT is identical ON vs OFF by construction. FULL book =
**73.5 trades/mo IS** (≫ 10/mo floor; PASS), LONG book 40.6/mo. Because entries are untouched, the
**OOS trade count equals iter-010's** — iter-010 ran 98 OOS trades over ~16 months (~6.1/mo full)
across both sides; the FULL-book OOS rate is preserved. **Per `feedback_v1_trade_rate_floor_50_per_specialist`
the OOS specialist floor is ≥50 OOS trades — iter-010's 98 OOS trades clears it, and this primitive
does not change that count.**

**(B) The de-lever is regime-targeted, not random.** Cross-checked against the INDEPENDENT iter-011
200-SMA-slope-SIGN regime label (a different functional form from my continuous z-score):
- BULL-regime long trades (n=1425): avg multiplier **1.000**
- BEAR-regime long trades (n=1124): avg multiplier **0.319**
- de-lever ratio (bear/bull) = **0.32** — the primitive concentrates de-levering almost entirely in
  the bear regime, confirming the trend signal is correctly identifying the regime to cut.

**(C) Slippage cost-stress** (pooled Sharpe OFF vs ON at slippage {0, 2, 4} bps/side, round-trip 2×):

| slippage bps/side | RT drag % | LONG OFF | LONG ON | LONG Δ | FULL OFF | FULL ON | **FULL Δ** |
|---:|---:|---:|---:|---:|---:|---:|---:|
| 0 | 0.00 | +1.957 | +2.326 | +0.370 | +1.870 | +2.040 | **+0.170** |
| **2 (merge)** | 0.04 | +1.788 | +2.178 | +0.390 | +1.626 | +1.807 | **+0.181** |
| 4 | 0.08 | +1.619 | +2.030 | +0.411 | +1.381 | +1.573 | **+0.192** |

**The de-lever lift GROWS under cost stress** (+0.170 → +0.181 → +0.192). De-levering the bear
regime — which is SL-heavy and gives back more to slippage — saves disproportionately more cost when
slippage is higher. The primitive is robustly accretive at the merge cost assumption and at 2× it.

---

## 5. Kelly sizing derivation (4.7b) — informational; the merge sizing knob is `max_amount_usd`/VT

The iter-010 let-run book IS profile: WR ≈ 0.434, payoff (avg win / |avg loss|) ≈ 1.41 (diary-010).
Fractional-Kelly for an asymmetric-payoff book: `f* = W − (1−W)/b` where W=0.434, b=1.41 →
`f* = 0.434 − 0.566/1.41 = 0.434 − 0.401 = 0.033` full-Kelly. This is the per-bet edge fraction of
a *symmetric* Kelly; the let-run book's positive skew makes a naive Kelly fragile, so a **¼-Kelly**
posture (`≈ 0.008`) is the conservative reading. **The practical takeaway: the iter-010 book's blind
edge is THIN (full-Kelly 3.3%), which is exactly why the regime-conditional de-lever matters — the
edge is concentrated in the bull regime and the bear regime has NEGATIVE Kelly (W≈0.40, b<breakeven
→ f*<0), confirming that bear exposure should be cut toward zero, not held at the blended fraction.**
The trend-scale multiplier IS a regime-conditional Kelly fraction: full size (bull, positive Kelly)
→ floor 0.25 (bear, negative Kelly). It does NOT change `max_amount_usd` / `weight_factor` *base*
sizing (that stays at the iter-010 setting); it modulates exposure within it. **Recommendation:
keep `max_amount_usd` at iter-010; do NOT add an absolute-Kelly cap on top — the thin blended edge
means a global Kelly cap would over-shrink the bull regime where the edge lives.** The de-lever
multiplier is the correct, regime-aware expression of Kelly here.

---

## 6. STRESS MATRIX summary (4.7c)

| scenario | metric | OFF (iter-010) | ON (trend-scale, floor 0.25) | verdict |
|---|---|---:|---:|---|
| **Vol/bear-regime replay** | bear sub-period loss-sum (LONG) | −1321 | −549 | −58% bleed |
| **Regime-shift sensitivity** | bull-regime gain retained | 4696 | 3750 | 80% kept |
| | bear-regime avg multiplier | 1.00 | 0.319 | de-levered |
| **Tail-loss** | worst single LONG trade (pct) | −15.88 | −10.60 | −33% tail |
| | LONG proxy max-DD | 429 | 299 | −30% |
| **Slippage 2 bps/side (merge)** | FULL pooled Sharpe lift | — | +0.181 | accretive |
| **Slippage 4 bps/side** | FULL pooled Sharpe lift | — | +0.192 | accretive |
| **OOD pocket** | n/a — primitive concentrates de-lever in trend-down, the OOD-rich regime | — | — | see §6.4 |

**§6.4 OOD note.** The 3 negative IS sub-periods (2022-H1/H2 LUNA/3AC/FTX, 2025-Q1 correction) are
precisely the highest-dispersion, most-out-of-distribution windows for a bull-trained model. The
de-lever cuts exposure exactly there (avg mult 0.32 in bear) — it is structurally aligned with the
R3 OOD Mahalanobis intent (cut size when the feature vector is far from the bull-dominated training
distribution), via a stateless trend proxy rather than a covariance distance. The primitive does NOT
concentrate PnL in OOD pockets; it does the opposite.

### 6.1 Trend-regime signal (stateless, leak-free, past-only) — EXACT formula

```
sma200_t       = SMA(close, 200)                      # using closes up to bar t-1 (.rolling(200).shift(1))
slope_t        = (sma200_t − sma200_{t−20}) / sma200_{t−20}    # fractional 200-SMA slope over 20 candles
slope_std_t    = rolling_std(slope, 250) at t−1       # past-only normalizer (.rolling(250).std().shift(1))
trend_z_t      = slope_t / slope_std_t                # unitless, vol-adaptive trend strength
```
All rolling stats `.shift(1)` → uses only information available at bar t-1 (no look-ahead). Warmup
(< 200+20+250 ≈ 470 candles, or any NaN): `trend_z = NaN`. The 200-SMA-slope form (not price-vs-SMA)
is the chosen signal; the price-vs-SMA-z variant was tested (`robustness.csv`) and gives a similar
overall lift (+2.292 vs +2.326) but a slightly worse worst-sub-period — slope-z is preferred.

### 6.2 Size-multiplier mapping (smooth piecewise-linear, NOT binary) — IS-calibrated

```
trend_scale(z) = FLOOR                                          if z ≤ Z_LO    (confirmed down-trend)
trend_scale(z) = 1.0                                            if z ≥ Z_HI    (confirmed up-trend)
trend_scale(z) = FLOOR + (1−FLOOR)·(z − Z_LO)/(Z_HI − Z_LO)     otherwise      (smooth transition)
trend_scale    = 1.0                                            if z is NaN    (FAIL-OPEN — never silently de-levers)
```
**IS-CALIBRATED VALUES (pre-registered):** `FLOOR = 0.25`, `Z_LO = −0.5`, `Z_HI = 0.0`,
`SLOPE_LB = 20`, `STD_LB = 250`. **LONG-BIAS: apply only when `signal.direction > 0`; SHORT trades
keep `trend_scale = 1.0`** (the IS evidence shows the risk and the edge both live in the long book;
shorts are flat and held up better OOS in iter-010 — do not touch them).

### 6.3 Code insertion point + QE wiring flag

- **Cleanest insertion point:** `src/crypto_trade/backtest.py`, inside the `vt_scale` pipeline,
  **AFTER R5 vol-target and AFTER vol_ceiling** (≈ line 587, immediately before `create_order` at
  line 588). Add one composing step, gated LONG-only:
  ```python
  # iter-v1/012: LONG-bias trend-scaled de-lever (composes with R5/VT/R2/vol_ceiling).
  if config.trend_scale_enabled and signal.direction > 0:
      _tz = trend_z_lookup.get((sym, ot), float("nan"))   # past-only trend-z, built at init
      if not math.isnan(_tz):
          _ts = trend_scale_from_z(_tz, config)            # piecewise-linear, [floor, 1.0]
          vt_scale = vt_scale * _ts
  # NaN _tz -> fail-OPEN (no de-lever), matching the §6.2 spec.
  ```
  This **composes with** (never replaces) the existing `vt_scale = vt_scale * r5_scale` step — it is
  one more multiplicative factor, exactly the established pattern of R2/R5/vol_ceiling.
- **The `trend_z_lookup` is built ONCE at backtest init** (mirror the `r5_natr_lookup` /
  `vol_ceiling_rv_lookup` pattern at lines 257–293 / 231–256): read the symbol's feature parquet,
  compute `trend_z` from `close` (stateless past-only, as §6.1 — there is no precomputed
  `trend_sma_200` column, so compute SMA-200 from `close` directly, IS+OOS rows alike since the
  formula is past-only and identical to live), keyed `(sym, open_time)`. **Build it from the FULL
  parquet (IS+OOS) — the signal is past-only so this is leak-free; the IS-only constraint was on
  CALIBRATION (the FLOOR/band), which is locked here.**
- **NEW `BacktestConfig` / `run_model` fields needed (QE WIRING FLAG):**
  | field | default | iter-012 value |
  |---|---|---|
  | `trend_scale_enabled` | `False` | `True` |
  | `trend_scale_floor` | `0.25` | `0.25` |
  | `trend_scale_z_lo` | `-0.5` | `-0.5` |
  | `trend_scale_z_hi` | `0.0` | `0.0` |
  | `trend_scale_slope_lb` | `20` | `20` |
  | `trend_scale_std_lb` | `250` | `250` |
  Default `trend_scale_enabled=False` preserves byte-identical behavior for all prior iterations.
  **QE must:** (1) add the 6 fields to `BacktestConfig` (frozen dataclass) + `run_model` plumbing;
  (2) add the init-time `trend_z_lookup` build (parquet read + past-only SMA-200/slope/z compute);
  (3) add the LONG-only composing step at ≈ line 587; (4) add a `[TREND-SCALE/012]` IS/OOS
  fire-counter print mirroring the R5/vol_ceiling counters; (5) mirror in `LiveConfig` for
  backtest-live parity (the live engine must compute the same past-only trend-z at decision time —
  flag for the engine-parity check). This is a genuinely NEW primitive, not an existing-field
  remap — budget the wiring accordingly.

### 6.4 Why this is NOT a gate (and composes safely)

- It never zeroes exposure (floor 0.25 > 0) → trade count unchanged → no T3-inversion from throwing
  away bear-regime trades (the iter-011 §3.3 gate failure mode). It de-levers, it does not delete.
- It is multiplicative on `vt_scale`, so it composes cleanly with R5 vol-target (high-NATR ceiling)
  and R2 drawdown-scaling: a trade in a high-vol down-trend gets BOTH the R5 NATR cut AND the trend
  cut. The composition is conservative-stacking (all factors ≤ 1.0), which is the desired direction.
- Stateless + past-only + explainable (a slope sign/magnitude) — satisfies the "prefer
  state-discontinuous/explainable over opaque proportional knobs" rule via a transparent piecewise-
  linear map, while staying smooth (the QR's binary-gate objection is satisfied).

---

## 7. RISK-PRIMITIVE SPEC for iter-012 (pre-registered)

**Primitive:** `trend_scale` — a LONG-only, stateless, smooth position-size multiplier that
de-levers the iter-010 let-run book in down-trends. Composes with R5 vol-target.

- **Trend signal:** `trend_z = [(SMA200_{t-1} − SMA200_{t-21}) / SMA200_{t-21}] / rolling_std_250(slope)_{t-1}`
  (past-only; SMA200 from `close`, slope over 20 candles, z-normalized by 250-candle rolling std).
- **Mapping:** piecewise-linear `trend_scale(z) ∈ [FLOOR, 1.0]`, FLOOR at `z ≤ Z_LO`, 1.0 at
  `z ≥ Z_HI`, linear between; NaN → 1.0 (fail-open). **LONG trades only; shorts unscaled.**
- **IS-CALIBRATED, pre-registered values:** `FLOOR=0.25`, `Z_LO=−0.5`, `Z_HI=0.0`, `SLOPE_LB=20`,
  `STD_LB=250`.
- **Code insertion:** `backtest.py` `vt_scale` pipeline, AFTER R5/vol_ceiling, LONG-only step (§6.3).
  **NEW `BacktestConfig`/`run_model` fields + init-time `trend_z_lookup` + LiveConfig parity — QE
  WIRING REQUIRED (§6.3).**
- **Predicted IS effect (DIRECTION-ONLY per the campaign proxy lesson):** FULL-book pooled IS Sharpe
  **+1.87 → ~+2.04** (Δ ~+0.17, seed-robust, all 5 seeds positive), LONG-book +1.96 → ~+2.33;
  **max-DD −30%**; bear-regime bleed −58%, bull gain retained 80%; **worst single trade −33%**.
- **Trade-rate:** UNCHANGED from iter-010 (size scaled, not trade count). FULL ~73.5/mo IS; OOS
  count = iter-010's 98 trades (≥50 specialist floor, PASS).
- **Slippage cost-stress (pre-registered merge assumption):** judge the merge at
  **`slippage_bps_per_side = 2.0`** (round-trip 0.04%, the v1 standard). Re-run the K=5 confirmation
  also at 4 bps/side; the FULL-book Sharpe lift must stay positive at both (IS-proxy: +0.181 / +0.192).

### Pre-registered both-positive COHERENCE FALSIFIER (NEGATIVE verdict if ANY holds)

1. **Confirmation FULL-book IS Sharpe (K=5 mean) does NOT rise vs the iter-010 K=5 no-primitive run
   by ≥ +0.10** — the pooled-Sharpe lift (IS-proxy +0.17) fails to materialize in the real backtest.
2. **The K=5 per-seed FULL-book Sharpe-lift spread > 0.30** (basin-lottery vigilance: the IS-proxy
   spread was 0.063; a real spread > 0.30 means the lift is a draw artifact, not structural).
3. **Fewer than 4/5 confirmation seeds show a positive FULL-book Sharpe lift** vs the no-primitive run.
4. **max-DD does NOT fall** (the primitive's core promise — cut drawdown — is unmet in the real run).
5. **Trade count changes** by > 1% ON vs OFF (the primitive leaked into entry logic — it must scale
   size only; any count change is a wiring defect).
6. **COHERENCE (the genuine prize):** if BOTH the K=5 IS Sharpe AND OOS Sharpe are positive, this is
   the campaign's first both-positive config and the de-lever thesis is CONFIRMED. If OOS stays
   negative WHILE the IS lift + DD-cut hold, the primitive is validated as a risk control (it did
   reduce drawdown and pooled risk as designed) but the OOS regime was a sustained down-trend deeper
   than the floor can fully neutralize — report as PARTIAL (risk-accretive, regime-limited), NOT a
   failure of the primitive. The falsifier targets the PRIMITIVE'S claims (Sharpe lift + DD cut +
   trade-count invariance), which are IS-measurable and seed-robust — not a forced OOS-positive.

### Kill-switch (mid-flight)
Abort the K=5 run if the `[TREND-SCALE/012]` counter shows the multiplier firing on SHORT trades
(LONG-only gating broke), or if the trade count diverges ON vs OFF (entry-logic leak), or if FULL-book
K=5 mean IS Sharpe < iter-010's no-primitive K=5 mean (the lift inverted — wiring or signal defect).

---

## 8. Handoff to Quant Research

QR may adopt, modify, or reject. My recommendation: **ADOPT the trend_scale primitive at the
pre-registered §7 values for a K=5 EXPLORATION screen on the iter-010 N=9 let-run config.** Rationale:
(1) it is the iter-011 QR's own forward-rec, now IS-calibrated and seed-robust on the correct
(pooled-Sharpe + DD) metric; (2) it is the first lever in the campaign that lifts IS Sharpe AND cuts
DD without changing trade count or touching the signal; (3) the cost-stress and seed-robustness
evidence is clean. **Caveats QR must fold in:** (a) the per-sub-period-Sharpe metric is the WRONG
falsifier here (§1) — the brief must pre-register the pooled-Sharpe + DD + trade-count-invariance
falsifier (§7), not a per-sub-period one; (b) the OOS gap will NOT necessarily close — the primitive
caps the down-trend bleed at a 0.25 floor, it does not flip a sustained bear into profit; the honest
claim is "smaller, drawdown-bounded OOS loss in a hostile regime; both-positive in a benign one"; (c)
this needs genuine QE wiring (NEW config fields + init lookup + live parity), not an existing-field
remap — budget for it.

---

## Appendix — methodology / OOS-vigilance attestation

- All three scripts hard-filter `open_time < OOS_CUTOFF_MS = 1742774400000` and assert
  `df["open_time"].max() < OOS_CUTOFF_MS` BEFORE any forward computation (`trend_scaled_sizing.py:251-252`,
  `delever_pooled_effect.py:184-185`, `traderate_and_stress.py:162-163`). The IS frame is the ONLY
  frame; OOS rows are never read. Knowing iter-010 OOS = −1.48 informed the QUESTION; the FLOOR/band
  were calibrated ENTIRELY on IS pooled-Sharpe + DD + sub-period stability.
- The expanding walk-forward trains only on candles strictly before each monthly test window minus
  `EMBARGO_C = N+3 = 12` candles (≥ N=9 label horizon); the forward label terminates at/before the
  test-window start (purged). The let-run trade reproduces the iter-009/010/011 execution verbatim
  (enter at close, exit at min{SL 1.45·ATR adverse, 9-candle timeout}, TP non-binding, 0.1% fee;
  ATR = close × vol_natr_21 / 100).
- The trend-regime signal is stateless & past-only: SMA-200, its 20-candle slope, and the 250-candle
  slope-std all use `.shift(1)`. The multiplier is computed from this signal alone — no forward info.
- The LightGBM read is a faithful DIRECTION-ONLY proxy of the deployed bagged specialist; magnitudes
  are relative ranking signals, not backtest forecasts (campaign proxy-overprediction lesson, applied
  here as "the +0.17 IS Sharpe lift is a direction-positive prediction, not a point forecast").
- Scripts re-runnable; lint clean modulo the idiomatic uppercase design-matrix (`X`) + the
  `CHOSEN_FLOOR` calibration constant + docstring-line-length carve-out, consistent with the
  iter-008/009/010/011 convention.
