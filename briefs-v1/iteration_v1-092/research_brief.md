# Research Brief — iter-v1/092
# XRP-IMPROVED — ADX-trend-strength regime-conditional kill gate (risk-primitive)

**Goal (user directive 2026-06-11 "let's try to improve xrp"):** lift XRP/088 — the campaign's
one SPECIALIST-PROMISING fresh mine and held BUNDLE-003 diversifier (IS +0.3783 / OOS +0.4966) —
into a stronger, mergeable BUNDLE-003 component by directly attacking BLOCKER 1 (the
regime-contingent OOS edge that fired the /089 regime-conditionality falsifier).

**Chosen axis: (b) regime-conditional kill primitive.** An IS-calibrated, opt-in trade gate that
suppresses entries when XRP's own ADX-14 trend-strength is below an IS-calibrated threshold — the
choppy/range regime where XRP's trend-following loses money. The IS evidence (Section 2) shows
XRP's edge is sharply regime-conditional on its own ADX, and the loss regime is detectable and
sticky enough to be actionable forward. This is the highest-leverage axis because it attacks the
exact blocker (regime-contingency) with a mechanism that is IS-calibratable and generalizable —
NOT a fit to the OOS OFF window.

---

## Section 0 — Data Split Declaration

- `OOS_CUTOFF_DATE = 2025-03-24` (ms: `1742774400000`) — UNCHANGED, byte-locked.
- `training_months = 24` — UNCHANGED, byte-locked.
- IS window: `open_time < 1742774400000` (XRP candles 2020-01-06 .. 2025-03-23; XRP trade coverage
  begins 2022-01 per /088 walk-forward).
- OOS window: `2025-03-24` onward.

All Section 2 analysis is **IS-ONLY** (`analysis/iteration_v1-092/eda.py` asserts
`df["open_time"].max() < OOS_CUTOFF_MS` and `trades["open_time"].max() < OOS_CUTOFF_MS` and aborts
on leak). The OOS pre-Nov-2025 OFF / post-Nov ON split is the **KNOWN MOTIVATION** only; it is
printed at the END of the script behind a fence and **NO threshold in this brief was calibrated on
any OOS number**. The ADX-kill threshold is derived purely from IS-window ADX and IS-trade PnL.

---

## Section 0.5 — Iteration Type Declaration

`TYPE: SPECIALIST` (single-symbol, XRPUSDT). Improvement of the existing XRP/088 seat via one
risk-primitive change (the ADX kill gate). Wall-clock budget: 2h SPECIALIST cap; fail-fast=2.0 ON
(XRP passes it — first-2yr IS +16.88 at /088). One-variable discipline: the ONLY change vs /088 is
the opt-in ADX kill gate; feature set, ATR barriers, seeds, trials, R-stack are all held at the
/088 config.

Not a CONFIRMATION: no bundle assembly, no baseline update. BUNDLE-002 (`v0.v1-082`) remains the
live baseline regardless of /092 outcome.

---

## Section 0.6 — Architecture-Family Justification

`FAMILY: risk-primitive` (post-aggregator RULE-layer trade gate; same band as /074 AXIS-R veto,
/084 R-FADE, /091 R-CONV conviction gate).
`ROTATION_STATUS: VALID`

Prior 5 SPECIALIST families from `briefs-v1/specialist_catalog.md`:
1. /086 TRB — universe (per-cohort-specialization-TRB)
2. /087 BNB — universe (per-cohort-specialization-BNB)
3. /088 XRP — universe (per-cohort-specialization-XRP)
4. /090 W-DECAY — sample-weighting (machinery)
5. /091 R-CONV — risk-primitive (post-aggregator conviction gate)

Rotation is satisfied two ways: (i) the per-symbol regime-specialist mandate
(`feedback_v1_cycle6_per_symbol_regime_specialist_mandate.md`) suspends strict axis-family
rotation for the current cycle; (ii) even under strict rotation this is VALID — the prior 5 are
NOT all the same family (3 universe + 1 sample-weighting + 1 risk-primitive). The /091 R-CONV
precedent is the same family but a DIFFERENT mechanism (conviction/SNR filter on ensemble agreement
vs regime-state filter on ADX trend-strength), so this is not knob-tuning inertia within one
mechanism.

**CROSS-TRACK-OVERLAP FLAG (carried from /088):** XRPUSDT is traded independently in BOTH v1 (this
specialist) AND v2 (live). Combined v1+v2 XRP notional, concentration, and backtest↔live parity
MUST be checked at any future bundle assembly or live deployment. Documented and accepted per user
directive; not a methodology violation. The kill gate is a v1-local strategy primitive and does
NOT couple to the v2 XRP head.

---

## Section 1 — Hypothesis

XRP/088's edge is **trend-regime-conditional on XRP's own ADX-14 trend strength**: in trending
regimes (ADX ≥ IS-median) the trend-following specialist makes money; in choppy/range regimes (ADX
below threshold) it loses. The pre-Nov-2025 OOS OFF stretch is the OOS manifestation of the same
structure (a low-trend regime). An **opt-in, IS-calibrated ADX kill gate** that suppresses entries
below an ADX threshold will (i) lift standalone IS Sharpe by removing the net-negative chop trades,
and — the load-bearing claim — (ii) make the OOS edge **less regime-contingent** by suppressing the
loss-making OFF-regime entries, so the OOS improvement is NOT concentrated only in the post-Nov ON
window.

---

## Section 2 — IS-Only Numerical Evidence

Produced by committed `analysis/iteration_v1-092/eda.py` (5 CSVs + `candidate_adf.csv` +
`summary.txt`). IS-only; leak-asserted.

### 2.1 — XRP's IS struggle is concentrated in the CHOP regime (`is_regime_edge.csv`)

XRP's 219 IS trades, sliced by the decision candle's regime state (each trade's `open_time` joined
to its decision candle via `candle.close_time`; 219/219 matched). Regime thresholds are
IS-median-calibrated within the IS window:

| Regime axis | State | Trades | Net PnL % | Win-rate | Sharpe-proxy |
|---|---|---:|---:|---:|---:|
| **XRP ADX-14** | **CHOP** (ADX < IS-median 25.45) | 115 | **−64.55** | 36.5% | **−1.02** |
| **XRP ADX-14** | **TREND** (ADX ≥ 25.45) | 104 | **+103.30** | 49.0% | **+1.44** |
| XRP vol (rv30) | HIVOL | 75 | +27.55 | 46.7% | +0.39 |
| XRP vol (rv30) | LOVOL | 144 | +11.20 | 40.3% | +0.17 |
| XRP dir (ret30) | DOWN | 112 | +32.29 | 43.8% | +0.46 |
| XRP dir (ret30) | UP | 107 | +6.45 | 41.1% | +0.10 |
| BTC trend | BTC_DOWN | 44 | +41.13 | 45.5% | +0.81 |
| BTC trend | BTC_FLAT | 118 | +34.32 | 44.9% | +0.51 |
| BTC trend | BTC_UP | 57 | **−36.71** | 35.1% | **−0.79** |

**The ADX axis is the dominant discriminator of XRP's IS edge.** The entire net IS edge lives in
the TREND regime (+103.30%); the CHOP regime is a −64.55% drag with sharpe-proxy −1.02. This is the
**IS analog of the OOS pre-Nov OFF stretch** — trend-following losing in low-trend conditions. The
ADX cut separates the edge far more cleanly than vol, direction, or BTC-trend (those axes are
milder; BTC_UP is a secondary negative regime but smaller and noisier, n=57).

### 2.2 — The CHOP regime is detectable and sticky (forward-actionable)

From `eda.py` ADX-state-persistence diagnostic:
- IS ADX-14 median = **25.455**.
- ADX-state 1-bar persistence `P(state_t+1 = state_t)` = **0.967** — the trend/chop state is highly
  sticky; once you observe CHOP you remain in CHOP with 96.7% probability next bar.
- CHOP run length: mean **30.4 bars** (median 23 ≈ 8 days at 8h). TREND run length: mean 30.6 bars.
- Fraction of IS candles in CHOP ≈ **0.501**.

Stickiness is the property that makes the gate forward-applicable: you act on the **observed** ADX
of the decision candle (past-only, already in the feature frame), and the regime persists long
enough that the read is not stale by the time the trade resolves.

### 2.3 — ADX-kill threshold is robust across a wide band (NOT a knife-edge fit)

IS-trade PnL split by ADX-at-entry threshold (gate KEEPS trades with ADX ≥ thr, KILLS below). Each
trade's entry-candle ADX read from `candle.close_time → trend_adx_14`:

| ADX thr | ~% candles killed | Kept trades | Killed trades | Kept net % | Killed net % |
|---:|---:|---:|---:|---:|---:|
| 18.00 | 20% | 179 | 40 | +41.13 | **−2.39** |
| 20.00 | 29% | 161 | 58 | +67.06 | **−28.32** |
| 22.00 | 37% | 143 | 76 | +87.37 | **−48.63** |
| **25.45** (IS-median) | 50% | 104 | 115 | **+103.30** | **−64.55** |
| 28.00 | 57% | 84 | 135 | +64.15 | −25.40 |
| 30.00 | 63% | 77 | 142 | +82.32 | −43.58 |

The killed bucket is **net-negative at every threshold** in the band and the kept bucket is
**net-positive at every threshold** — the gate removes losing trades and keeps winners across the
entire 18–30 ADX range. This is the opposite of a knife-edge fit. Baseline IS net (no gate) =
+38.74%; any threshold in the band raises kept-net materially.

### 2.4 — Why NOT option (a) autocorr-persistence feature head (`autocorr_*` CSVs)

The lag-5 autocorr signal is a real *feature* (importance rank 3 at /088) but its **standalone
forward edge is thin**, so a feature head sharpening it is lower-leverage than the regime gate:
- IS return-autocorr persistence half-life ≈ **4 lags**; `stat_autocorr_lag5` mean −0.0027, frac
  positive 0.493 (near-symmetric — no strong directional persistence on average).
- Forward 5-bar momentum-continuation edge conditioned on AC5 tercile
  (`autocorr_persistence_edge.csv`): AC5_HIGH(persist) gives mom-continuation fwd5 = **+0.43%**,
  hit-rate **48.4%**, Spearman(mom5, fwd5) = **+0.017** — barely above noise even in the best
  tercile. AC5_LOW = +0.25%/47.5%/−0.019.
- Orthogonality of proposed head features (`candidate_feature_orthogonality.csv`): two of four
  candidates (`ac_persist_score` |corr|=0.50, `ac5_z_90` |corr|=0.78 vs `stat_autocorr_lag5`) would
  partly DUPLICATE the existing differentiator; only `ac5_signed_mom` (|corr|=0.002) and
  `ac_decay_ratio_1_5` (|corr|=0.002) are genuinely orthogonal, and those ride the thin forward
  edge above. ADF p=0.0 for all four (stationary), but a near-noise forward edge is not worth a
  new feature surface. **Option (a) deferred, not refuted.**

Option (c) longer-horizon labeling is also lower-leverage: the persistence half-life (4 lags ≈ 1.3
days) is already close to the existing label horizon, so a longer label would not match a longer
persistence timescale — there isn't one.

**Decision: option (b) is the highest-leverage axis** — it attacks BLOCKER 1 directly, the
mechanism is IS-calibratable and robust (2.3), and the loss regime is detectable and sticky (2.2).

---

## Section 2.5 — HIGH-RISK Axis Declaration

`HIGH-RISK: NO` → `NORMAL-RISK`

Reason: the ADX kill gate is a **post-aggregator RULE layer** applied AFTER the Optuna-trained model
emits its signal and BEFORE the Signal is built (same band as /074/084/091). It does NOT change
Optuna's training-objective domain — the model, feature columns, seeds, trials, and per-month
objective are bit-identical to /088. With `enable_adx_kill_gate=False` the run is byte-identical to
/088. Single-seed (50-inner-seed SPECIALIST ensemble) is appropriate; NO multi-seed required.

Mitigation: opt-in default-OFF flag; pre-registered threshold (Section 3); trade-rate floor F3
guards against over-killing (the gate must leave ≥50 OOS trades).

---

## Section 3 — Proposed Changes

**ONE variable: an opt-in ADX-trend-strength kill gate. No feature changes; global PRUNED stays 48.**

### 3.1 — New opt-in gate in `src/crypto_trade/strategies/ml/lgbm.py`

Mirror the /091 R-CONV wiring exactly (constructor flag + threshold; applied in the specialist
predict path at the post-aggregator RULE band, before the Signal is built):

```python
# constructor (alongside enable_r_conv_gate / r_conv_tau):
enable_adx_kill_gate: bool = False,      # default OFF → bit-identical to /088 when unset
adx_kill_threshold: float = 22.0,        # IS-calibrated; pre-registered (Section 3.3)
adx_kill_feature: str = "trend_adx_14",  # the regime feature read from the decision candle
```

At signal time (after `_final_signed` / `_sp_direction` computed, same site as the R-CONV gate at
`lgbm.py:2194`), read the decision candle's ADX from the existing single-row feature frame
`feat_df_sp[self._adx_kill_feature]` (the column is in PRUNED-48, always present). If the gate is
enabled and `adx < adx_kill_threshold`, return `NO_SIGNAL` and emit a `decision_log` entry:

```python
if self._enable_adx_kill_gate:
    _adx_val = float(feat_df_sp[self._adx_kill_feature].iloc[0]) \
        if self._adx_kill_feature in feat_df_sp.columns else None
    if _adx_val is not None and np.isfinite(_adx_val) and _adx_val < self._adx_kill_threshold:
        decision_log.log({
            "kind": "adx_kill_skip", "symbol": symbol, "ot": open_time,
            "month": candle_month, "adx": _adx_val,
            "adx_kill_threshold": self._adx_kill_threshold,
            "decision": "skipped:adx_below_kill_threshold",
        })
        return NO_SIGNAL
```

Stateless; reads only the past-only ADX of the decision candle. The skip happens BEFORE the
dispersion append (mirrors R-CONV — skipped candles must not pollute the dispersion diagnostic).
QE: also wire a backtest-mode `decision_log` sink to `reports-v1/iteration_v1-092/decision_log.jsonl`
(per the /091 secondary finding — `decision_log.log()` is a no-op in backtest mode; without this
the kill-skip entries are dropped and F2 attribution is unreconstructable).

### 3.2 — Runner `run_iteration_092.py` + `run_baseline_v1.py` "/v1-092" dispatch

Fork `run_iteration_088.py` exactly (XRP-only, specialist_mode=50 seeds × 30 trials, ENSEMBLE_SIZE=1,
atr_tp=2.9 / atr_sl=1.45, R1=OFF / R2=OFF / R3=ON@0.70 / R5=ON@0.3, fail_fast_is_years=2.0,
`feature_columns=list(V1_FEATURE_COLUMNS_PRUNED)` (48)) and add only:
`enable_adx_kill_gate=True, adx_kill_threshold=<Section 3.3 value>`.

### 3.3 — Pre-registered threshold

`adx_kill_threshold = 22.0`. Rationale: from the robustness grid (2.3), thr=22 kills ~37% of
candles and leaves 143 kept IS trades (well above the ≥50 floor with OOS headroom), with kept net
+87.37% vs killed −48.63%. It is deliberately **below** the IS-median (25.45) to preserve trade-rate
(the median kills 50% → risks the OOS ≥50 floor given /088's 84 OOS trades) while still removing the
bulk of the negative-PnL chop trades. The whole 18–30 band works (2.3), so 22 is a robust interior
choice, not an optimized peak. Pre-registered and frozen before the run.

### 3.4 — Global feature set UNCHANGED

`V1_FEATURE_COLUMNS_PRUNED` stays at **48** columns. No new feature, no LOCAL feature constant. The
gate reads an existing PRUNED-48 column (`trend_adx_14`). One-variable discipline preserved.

### 3.5 — Tests

`tests/test_iteration_v1_092.py`: (i) gate OFF → output bit-identical to /088 path; (ii) gate ON
with a synthetic low-ADX candle → `NO_SIGNAL`; (iii) gate ON with high-ADX candle → signal
unchanged; (iv) `adx_kill_threshold` plumbed from runner to strategy; (v) PRUNED-48 assertion holds.

---

## Section 3.5 — LM Master Phase 4.5 Advisory (PLACEHOLDER)

Phase 4.5 LM Master advisory not yet authored at brief time. This section is the integration anchor;
on Phase 4.5 emission, brief Section 3 will be amended to explicitly address each LM recommendation
(adopt / modify / reject). Anticipated LM focus areas given the axis: (a) whether the post-aggregator
gate interacts with the R3 OOD gate (both can suppress entries — LM may flag double-counting of the
low-trend/OOD overlap); (b) confirmation that the gate does not alter the Optuna objective; (c)
whether `trend_adx_14`'s own importance (rank 2 at /088) means the model already partially encodes
the regime (gate as redundancy-vs-complement question). QR will respond per the v1 Phase 4.5
discipline.

---

## Section 4 — Pre-Registered Falsifiers

**F1 — IS edge lift (standalone).** IS Sharpe with the ADX kill gate ON must be **≥ +0.20 ABOVE**
XRP/088's IS +0.3783 (i.e. IS Sharpe ≥ **+0.578**). If IS Sharpe Δ < +0.20 vs /088 →
EXPLORATION-NEGATIVE (the gate did not lift the standalone edge). Rationale: the IS-trade PnL math
(2.3) implies a large kept-vs-killed separation; a real lift should clear +0.20.

**F2 — Mechanism engaged.** The `adx_kill_skip` decision-log must show the gate fired on roughly the
predicted fraction: **20–45% of candidate entries suppressed** (consistent with thr=22 killing ~37%
of candles). If the suppressed fraction is < 10% (gate inert) or > 60% (gate over-firing,
threshold mis-plumbed) → mechanism-disengaged; the verdict cannot be PROMISING regardless of F1.
Requires the backtest-mode decision_log sink (Section 3.1).

**F3 — Trade-rate floor.** OOS trades with the gate ON must be **≥ 50** (per
`feedback_v1_trade_rate_floor_50_per_specialist.md`). /088 had 84 OOS trades; thr=22 kills ~37% of
candidate entries → expect ~50–55 OOS trades. If OOS trades < 50 → reject (or fall back to a lower
threshold only if pre-committed; not this run). 30–49 → 7-outer-seed validation per the floor rule.

**F4 — REGIME-BREADTH (THE KEY FALSIFIER — does it FIX the blocker?).** The improvement must make
the OOS edge **LESS regime-contingent**, not merely amplify the post-Nov ON window. Pre-registered
test at Phase 7: split OOS into the same pre-Nov-2025 (8mo) and post-Nov (7mo) windows as the /089
falsifier. The gate FIXES the blocker iff the **pre-Nov-equivalent OFF window improves materially**
— concretely, pre-Nov OOS net PnL rises from /088's **−17.24% toward break-even or better** (target:
pre-Nov net ≥ −5% AND ≥ 3/8 months positive, vs /088's 1/8). 
- **PRE-REGISTERED DID-NOT-FIX-THE-BLOCKER VERDICT:** if the OOS improvement is **again concentrated
  in the post-Nov window** (post-Nov gains while pre-Nov stays ≈ −17% / ≤ 1-of-8 positive), then the
  gate did NOT fix the regime-contingency — it is the SAME blocker as /089, and the verdict is
  EXPLORATION-NEGATIVE-DID-NOT-FIX (no BUNDLE-003 re-candidacy on this iteration), even if headline
  OOS Sharpe rises. F4 is the load-bearing acceptance criterion; F1/F3 are necessary but not
  sufficient. (The gate suppresses low-ADX entries in BOTH windows by construction, so a genuine fix
  must show in the pre-Nov OFF window — this is the mechanistic test of "did we remove the OFF-regime
  drag", and it is calibrated on the IS structure of 2.1, not on the OOS numbers.)

---

## Section 5 — Risk Mitigation

Config matches the /088 SPECIALIST pattern (one-variable discipline) PLUS the new gate as the
risk-primitive under test:

- R1 = OFF (CATALOG-CLOSED for SPECIALIST mode).
- R2 = OFF (Model A baseline — no drawdown scaling).
- R3 = ON (Mahalanobis OOD, cutoff 0.70, 16 scale-invariant `V1_OOD_FEATURE_COLUMNS`).
- R5 = ON (vol_targeting=True, vt_target_vol=0.3, vt_lookback_days=45, vt_min_scale=0.33).
- **R6 (NEW, under test) = ON: ADX kill gate, `adx_kill_threshold=22.0`** — opt-in, IS-calibrated.

ATR barriers: atr_tp=2.9 / atr_sl=1.45 (Model A ETH cell vol-class match; UNCHANGED).

**Simulated historical effect (IS-calibrated, Section 2.3):** at thr=22 the gate would have removed
76 of 219 IS trades whose summed net PnL was **−48.63%**, retaining 143 trades summing **+87.37%**.
The R3 OOD gate already suppresses ~30% of candles on a different axis (distribution outliers); the
ADX gate suppresses on the regime axis — Phase 7.4 LM should audit the overlap (a candle can be both
low-ADX and OOD). The gate cannot increase exposure (it only removes entries), so it strictly
reduces gross notional and tail exposure on the chop regime.

All thresholds IS-calibrated; none derived from OOS.

---

## Section 6 — Risk Management Design

| Primitive | Config | Prediction |
|---|---|---|
| Vol-adjusted size | vt_target_vol=0.3 | ~30% vol-adj fire rate |
| ADX kill gate (R6, NEW) | thr=22 on trend_adx_14 | ~37% candidate entries suppressed (F2) |
| Z-score OOD (R3) | cutoff=0.70, 16 features | ~30% candles blocked (overlap w/ R6 audited Phase 7.4) |
| Drawdown brake (R2) | OFF | no scaling |
| Consecutive-SL (R1) | OFF | catalog-closed for specialist |
| BTC contagion | OFF | N/A |
| Liquidity floor | XRPUSDT top-5 perpetual | no liquidity risk |

Expected IS trade rate after gate: ~9–12 trades/month (from ~15/mo at /088, minus ~37%). Expected
OOS trades: ~50–55 (F3 floor).

---

## Section 7 — Pre-Registered Failure-Mode Prediction

**Most plausible failure:** the gate removes the chop-regime trades in OOS but the OOS pre-Nov OFF
stretch was NOT actually a low-ADX regime (the OOS OFF stretch could be a different failure mode —
e.g. low-ADX is not the OOS chop signature, or the chop was high-ADX false trends). Then F4 fires:
the pre-Nov window stays ≈ −17% and the gain is again post-Nov only → DID-NOT-FIX-THE-BLOCKER. This
is the genuine risk that the IS-calibrated regime axis does not transfer to the OOS regime
structure; F4 is designed precisely to catch it.

**Secondary failure:** the gate over-kills and drops OOS trades below 50 (F3), making the OOS Sharpe
untrustworthy even if positive. Mitigated by the deliberately-below-median thr=22.

**Tertiary failure (NEGATIVE-NO-EFFECT):** the model's own use of `trend_adx_14` (importance rank 2)
already encodes the regime, so the explicit gate is redundant and the IS lift is < +0.20 (F1). In
that case the gate is informative-but-inert and the verdict is EXPLORATION-NEGATIVE.

Gates that should catch failures: F1 (IS lift), F2 (mechanism engaged), F3 (trade-rate), F4
(regime-breadth — the acceptance gate).

---

## Section 8 — Pre-Registered MERGE/NO-MERGE Numerical Criteria

This is a SPECIALIST EXPLORATION; it does NOT merge a baseline. Verdict criteria:

**EXPLORATION-PROMISING (BUNDLE-003 re-candidacy)** requires ALL:
1. fail-fast PASSED (XRP first-2yr IS > 0 — expected, /088 was +16.88).
2. F1: IS Sharpe ≥ +0.578 (Δ ≥ +0.20 vs /088 +0.3783).
3. F2: 20–45% of candidate entries suppressed (mechanism engaged, decision_log).
4. F3: OOS trades ≥ 50.
5. **F4: pre-Nov OOS window improves (net ≥ −5% AND ≥ 3/8 months positive) — the gate makes the
   edge LESS regime-contingent.** This is the load-bearing gate.
6. σ_SR ≤ 0.50 across the 50 inner seeds (basin-lottery guard) AND specialist_dispersion.csv
   committed.

**EXPLORATION-NEGATIVE-DID-NOT-FIX** (pre-committed): F1/F2/F3 pass but F4 fails (gain again post-Nov
only) → the regime-contingency blocker is NOT fixed; no re-candidacy this iteration; the axis is
LEARNED (IS-ADX-regime does not map to the OOS OFF stretch) and a future iteration must try a
different OFF-regime detector (e.g. the BTC_UP secondary regime from 2.1, or a vol-state gate).

**EXPLORATION-NEGATIVE** (any of F1/F2/F3 fails). BASELINE_V1.md UNCHANGED regardless of /092 outcome.

---

## Section 9 — Library Stack Declaration

- LightGBM, Optuna: project `uv.lock` versions; no new library introduced.
- statsmodels: used in `eda.py` for candidate-feature ADF (`adfuller`) — already installed; no new
  dependency.
- No mlfinlab / mlfinpy / pypbo / fracdiff dependency introduced. Fallbacks: N/A.
- The ADX kill gate reuses the /091 R-CONV opt-in-gate wiring pattern (`lgbm.py`); no new
  infrastructure. Backtest-mode decision_log sink is the one new plumbing item (per /091 finding).
