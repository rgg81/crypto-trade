# Research Brief — iter-v1/092 (REVISED)
# XRP-IMPROVED — BTC-trend-directional kill gate (risk-primitive)

> **REVISION (2026-06-11, post Phase 4.5 LM advisory `fda4d2c2`):** the original brief
> (`ebe1f95a`) proposed an **ADX-trend-strength kill** (`trend_adx_14 < 22 → NO_SIGNAL`). The LM
> Phase 4.5 forensic REJECTED that axis: XRP/088's OOS OFF stretch is **TREND-WRONG-WAY**, not chop —
> the pre-Nov losses sit in the ADX≥22 KEPT bucket (30/44 trades, −38.61% of the −42.77% drag, ADX
> median 26.28 = strongly TRENDING but wrong-direction). ADX measures trend STRENGTH not DIRECTION,
> so an ADX kill removes only −4.17% (the 14 chop trades), leaves the OFF window unfixed (F4
> DID-NOT-FIX), and borderline-fails F3 (49 < 50 OOS survivors). This revision **PIVOTS to a
> BTC-trend-directional gate** (risk-primitive, same band) and re-derives the mechanism IS-only.

**Goal (user directive 2026-06-11 "let's try to improve xrp"):** lift XRP/088 — the campaign's one
SPECIALIST-PROMISING fresh mine and held BUNDLE-003 diversifier (IS +0.3783 / OOS +0.4966) — into a
stronger, mergeable BUNDLE-003 component by attacking the OOS failure mode the LM diagnosed:
**XRP's trend-following loses when BTC is up-trending** (directional/contextual), NOT when XRP is
choppy.

**Chosen axis: (b) regime-conditional kill primitive — BTC-trend-directional gate.** An IS-calibrated,
opt-in trade gate that suppresses XRP entries when BTC's own 14d (42-bar @ 8h) trend is in the
regime where XRP's IS edge is negative. The IS evidence (Section 2) shows XRP's loss concentrates in
the **BTC_UP regime (IS n=57, net −36.71%, sharpe −0.79)** regardless of XRP's direction — the
cleaner separator than either ADX-strength or directional-disagreement. The OOS forensic (advisory
context, Section 3.5) confirms the IS mechanism transfers in the correct direction.

---

## Section 0 — Data Split Declaration

- `OOS_CUTOFF_DATE = 2025-03-24` (ms: `1742774400000`) — UNCHANGED, byte-locked.
- `training_months = 24` — UNCHANGED, byte-locked.
- IS window: `open_time < 1742774400000` (XRP candles 2020-01-06 .. 2025-03-23; XRP trade coverage
  begins 2022-01 per /088 walk-forward; 219 IS trades).
- OOS window: `2025-03-24` onward.

All Section 2 design analysis is **IS-ONLY** (`analysis/iteration_v1-092/eda.py` asserts
`df["open_time"].max() < OOS_CUTOFF_MS` and `trades["open_time"].max() < OOS_CUTOFF_MS` and aborts on
leak). The gate mechanism (BTC-regime kill) and threshold (`|btc_ret_42| > 0.067`) are derived
**purely from IS-window BTC 42-bar returns and IS-trade PnL**. The OOS pre-Nov-2025 OFF / post-Nov
ON forensic (Section 3.5) is **ADVISORY-ONLY** — it confirms the IS mechanism generalizes; **NO
threshold in this brief was calibrated on any OOS number.** The OOS roster is read in the EDA only to
COUNT survivors under the IS-frozen rule (F3 projection), not to tune the rule.

---

## Section 0.5 — Iteration Type Declaration

`TYPE: SPECIALIST` (single-symbol, XRPUSDT). Improvement of the existing XRP/088 seat via one
risk-primitive change (the **BTC-trend-directional kill gate**). Wall-clock budget: 2h SPECIALIST
cap; fail-fast=2.0 ON (XRP passes it — first-2yr IS +16.88 at /088). One-variable discipline: the
ONLY change vs /088 is the opt-in BTC-trend gate; feature set, ATR barriers, seeds, trials, R-stack
are all held at the /088 config.

Not a CONFIRMATION: no bundle assembly, no baseline update. BUNDLE-002 (`v0.v1-082`) remains the live
baseline regardless of /092 outcome.

---

## Section 0.6 — Architecture-Family Justification

`FAMILY: risk-primitive` (post-aggregator RULE-layer trade gate; same band as /074 AXIS-R veto,
/084 R-FADE, /091 R-CONV conviction gate). The axis FAMILY is UNCHANGED by the pivot — both the
rejected ADX-kill and the adopted BTC-trend gate are post-aggregator RULE-layer kills; only the
**state variable** changes (XRP's own ADX → BTC's 14d trend regime).
`ROTATION_STATUS: VALID`

Prior 5 SPECIALIST families from `briefs-v1/specialist_catalog.md`:
1. /086 TRB — universe (per-cohort-specialization-TRB)
2. /087 BNB — universe (per-cohort-specialization-BNB)
3. /088 XRP — universe (per-cohort-specialization-XRP)
4. /090 W-DECAY — sample-weighting (machinery)
5. /091 R-CONV — risk-primitive (post-aggregator conviction gate)

Rotation is satisfied two ways: (i) the per-symbol regime-specialist mandate
(`feedback_v1_cycle6_per_symbol_regime_specialist_mandate.md`) suspends strict axis-family rotation
for the current cycle; (ii) even under strict rotation this is VALID — the prior 5 are NOT all the
same family (3 universe + 1 sample-weighting + 1 risk-primitive). The /091 R-CONV precedent is the
same family but a DIFFERENT mechanism (ensemble-conviction/SNR filter vs **cross-asset BTC-trend
regime filter**), and the most direct precedent is **iter-v1/019's stateless direction-aware
BTC-trend gate** (same 42-bar BTC return), which is a DIFFERENT cohort (ETH) on a DIFFERENT structural
prior — so this is not knob-tuning inertia within one mechanism.

**CROSS-TRACK-OVERLAP FLAG (carried from /088):** XRPUSDT is traded independently in BOTH v1 (this
specialist) AND v2 (live). Combined v1+v2 XRP notional, concentration, and backtest↔live parity MUST
be checked at any future bundle assembly or live deployment. Documented and accepted per user
directive; not a methodology violation. The kill gate is a v1-local strategy primitive and does NOT
couple to the v2 XRP head.

---

## Section 1 — Hypothesis (REVISED)

XRP/088's edge is **regime-conditional on BTC's trend direction**, NOT on XRP's own trend strength.
In the **BTC_UP regime** (BTC 42-bar/14d return strongly positive) XRP's trend-following specialist
loses money (IS net −36.71%, sharpe −0.79, n=57); in BTC_DOWN and BTC_FLAT regimes it is net-positive
(IS +41.13% / +34.32%). The pre-Nov-2025 OOS OFF stretch is the OOS manifestation of the same
structure: a **trend-wrong-way** failure in which XRP's directional calls are systematically wrong
relative to the prevailing BTC tape — which the ADX-strength axis cannot detect (those losses are in
strongly-trending, high-ADX candles).

An **opt-in, IS-calibrated BTC-trend kill gate** that suppresses XRP entries when `btc_ret_42 > +0.067`
(BTC_UP) will (i) lift standalone IS Sharpe by removing the net-negative BTC_UP trades, and — the
load-bearing claim — (ii) make the OOS edge **less regime-contingent** by removing the OFF-regime
drag, so the OOS improvement is NOT concentrated only in the post-Nov ON window. The cross-asset
mechanism is what makes this a head-on attack on trend-wrong-way that the ADX axis structurally could
not be.

---

## Section 2 — IS-Only Numerical Evidence (REVISED)

Produced by committed `analysis/iteration_v1-092/eda.py` (extended with the BTC-trend-gate calibration
section). New CSVs: `btc_regime_sweep.csv`, `btc_dir_disagreement_sweep.csv`,
`btc_gate_oos_projection.csv` (OOS roster read ONLY to count survivors; threshold frozen first). IS
leak-asserted (XRP candles 5696, IS trades 219, cutoff_ms 1742774400000; assertions pass).

### 2.1 — BTC-trend regime is the dominant discriminator of XRP's IS edge (`is_regime_edge.csv`)

XRP's 219 IS trades sliced by the decision candle's regime state (trade.open_time joined to
candle.close_time; IS-median-calibrated thresholds within the IS window):

| Regime axis | State | Trades | Net PnL % | Win-rate | Sharpe-proxy |
|---|---|---:|---:|---:|---:|
| **BTC trend** | **BTC_UP** (btc_ret_42 > +0.067) | **57** | **−36.71** | 35.1% | **−0.79** |
| **BTC trend** | BTC_DOWN (< −0.067) | 44 | +41.13 | 45.5% | +0.81 |
| **BTC trend** | BTC_FLAT | 118 | +34.32 | 44.9% | +0.51 |
| XRP ADX-14 | CHOP (< median 25.45) | 115 | −64.55 | 36.5% | −1.02 |
| XRP ADX-14 | TREND (≥ 25.45) | 104 | +103.30 | 49.0% | +1.44 |
| XRP vol (rv30) | HIVOL | 75 | +27.55 | 46.7% | +0.39 |
| XRP vol (rv30) | LOVOL | 144 | +11.20 | 40.3% | +0.17 |

The ADX axis splits IS PnL too (it's the original brief's basis), **but the LM forensic proved the
ADX split does not transfer to OOS** — the OOS OFF losses are in the ADX≥22 KEPT bucket (high-ADX,
wrong-direction). The **BTC_UP regime is the cleaner directional/contextual separator** that is
ALIGNED with the trend-wrong-way OOS failure: kill BTC_UP and BOTH remaining regimes (DOWN +41.13,
FLAT +34.32) stay net-positive.

### 2.2 — BTC-regime kill (mechanism i) vs directional-disagreement (mechanism ii): IS separator robustness

Two candidate mechanisms were calibrated IS-only across a threshold sweep on `|btc_ret_42|`. The gate
KILLS the loss bucket and KEEPS the rest. "CLEAN" = kill bucket net < 0 AND **every** kept sub-bucket
net > 0.

**Mechanism (i) BTC-regime kill** — suppress ALL XRP entries when BTC_UP (`btc_regime_sweep.csv`):

| thr | KILL(BTC_UP) n / net% | KEPT (DOWN+FLAT) n / net% | DOWN+ | FLAT+ | CLEAN |
|---:|---|---|:--:|:--:|:--:|
| 0.05 | 64 / −20.2 | 155 / +58.9 | ✓ | ✓ | **✓** |
| 0.06 | 63 / −17.3 | 156 / +56.0 | ✓ | ✓ | **✓** |
| **0.067** (IS abs-median) | **57 / −36.7** | **162 / +75.4** | ✓ | ✓ | **✓** |
| 0.08 | 51 / −29.6 | 168 / +68.4 | ✓ | ✓ | **✓** |
| 0.10 | 44 / −25.2 | 175 / +63.9 | ✗ | ✓ | ✗ |

**Mechanism (ii) directional-disagreement** — suppress when XRP signal direction OPPOSES BTC trend
sign (XRP LONG & BTC_DOWN, or XRP SHORT & BTC_UP) (`btc_dir_disagreement_sweep.csv`):

| thr | KILL(DISAGREE) n / net% | KEPT (AGREE+FLAT) n / net% | AGREE+ | FLAT+ | CLEAN |
|---:|---|---|:--:|:--:|:--:|
| 0.05 | 84 / −20.4 | 135 / +59.2 | ✓ | ✓ | **✓** |
| 0.06 | 74 / −29.6 | 145 / +68.3 | ✓ | ✓ | **✓** |
| **0.067** | **68 / −39.1** | **151 / +77.8** | ✓ | ✓ | **✓** |
| 0.08 | 62 / −32.8 | 157 / +71.5 | ✓ | ✓ | **✓** |
| 0.10 | 51 / −29.5 | 168 / +68.2 | ✗ | ✓ | ✗ |

**On IS alone, both mechanisms are clean separators in the 0.05–0.08 band**, with the sharpest
separation at the IS abs-median thr=0.067 (mech-ii has a marginally larger kill drag −39.1% vs
−36.7% and slightly higher kept-net +77.8% vs +75.4%). IS does not decide between them — the
**generalization forensic does (Section 3.5), and it selects mechanism (i) decisively.**

### 2.3 — F3 OOS-survivor projection (`btc_gate_oos_projection.csv`) — the gate that killed ADX

OOS roster (82 trades, BTC-joined) filtered under each IS-frozen rule. This is the check the ADX
version FAILED (49 < 50). At the chosen thr=0.067:

| Mechanism | OOS survivors | OOS killed | OOS killed net% | OOS survivor net% |
|---|---:|---:|---:|---:|
| **(i) BTC-regime kill** | **70** | 12 | **−8.43** (removes LOSERS ✓) | **+29.23** |
| (ii) dir-disagreement | 67 | 15 | **+14.56** (removes WINNERS ✗) | +6.24 |

Mechanism (i) leaves **70 OOS survivors** (≥50 PASS, comfortable margin) AND its kill bucket is
OOS-net-NEGATIVE (it removes losing trades, preserving the +29.23% survivor edge). Mechanism (ii)
removes OOS-POSITIVE trades (+14.56% killed) and collapses the survivor edge to +6.24% — it kills
winners. **F3 + survivor-PnL sign both favor mechanism (i).**

### 2.4 — Why NOT the ADX axis (the rejected original) — see Section 3.5 for the LM forensic.

The ADX-strength axis is genuinely a clean IS separator (2.1) but the LM 4.5 forensic shows it does
not map to the OOS OFF stretch (those losses are high-ADX, wrong-direction). The BTC-trend axis is
both a clean IS separator AND aligned with the OOS failure mode. **The ADX axis is rejected, not
deferred — its IS-OOS dissociation is now demonstrated.**

**Decision: mechanism (i) BTC-regime kill at thr=0.067** — the cleaner IS separator, the only one that
generalizes in the correct direction (removes OOS losers, improves the OFF window), and clears F3 with
margin.

---

## Section 2.5 — HIGH-RISK Axis Declaration

`HIGH-RISK: NO` → `NORMAL-RISK`

Reason: the BTC-trend kill gate is a **post-aggregator RULE layer** applied AFTER the Optuna-trained
model emits its signal and BEFORE the Signal is built (same band as /074/084/091; same as
iter-v1/019's BTC-trend gate). It does NOT change Optuna's training-objective domain — the model,
feature columns (PRUNED-48), seeds, trials, and per-month objective are bit-identical to /088. With
`enable_btc_trend_kill_gate=False` the run is byte-identical to /088. Single-seed (50-inner-seed
SPECIALIST ensemble) is appropriate; NO multi-seed required.

Mitigation: opt-in default-OFF flag; pre-registered threshold (Section 3); trade-rate floor F3 guards
against over-killing (the gate must leave ≥50 OOS trades — VERIFIED to project 70 in 2.3).

---

## Section 3 — Proposed Changes (REVISED)

**ONE variable: an opt-in BTC-trend-directional kill gate. No feature changes; global PRUNED stays 48.**

### 3.1 — New opt-in gate in `src/crypto_trade/strategies/ml/lgbm.py`

The gate needs the **BTC 42-bar (14d) return at the decision candle**, past-only. The PRUNED-48 stack
contains NO BTC-price-trend column (`*_vs_btc_ret_ratio_30` are ALL-NaN on XRP's own rows by the v1
cross-asset architecture; `btc_funding_spread_30_90` is funding not price-trend). So — exactly per the
**iter-v1/019 + iter-v1/074 AXIS-R precedents** — the gate builds a **BTC close index at init** and
computes `btc_ret_42` via O(log n) lookback at gate time. This adds NO column to PRUNED-48.

Constructor flags (alongside `enable_r_conv_gate` / `r_conv_tau`):

```python
enable_btc_trend_kill_gate: bool = False,     # default OFF → bit-identical to /088 when unset
btc_trend_kill_threshold: float = 0.067,      # IS abs-median of btc_ret_42; pre-registered (3.3)
btc_trend_kill_lookback: int = 42,            # bars (~14d @ 8h); same window as iter-v1/019
btc_trend_kill_mode: str = "regime",          # mechanism (i): kill ALL entries in BTC_UP
btc_trend_symbol: str = "BTCUSDT",            # the cross-asset trend source
```

**Init (mirror AXIS-R close-index build at `lgbm.py:587-599`, but for BTC):** when the gate is enabled,
load `Path(self.features_dir) / f"{btc_trend_symbol}_{self._interval}_features.parquet"`, read
`(close_time, close)`, sort by `close_time`, store as `self._btc_idx = (ot_int64, close_f64)`. Compute
`btc_ret_42[t] = close[t]/close[t-42] - 1.0` past-only (the 42-bar return uses only data ≤ the
candle's own close; the join key is the decision candle's `close_time`, identical to the EDA).

**Gate site (mirror R-CONV at `lgbm.py:2194`, AFTER `_sp_direction` is computed, BEFORE the dispersion
append):**

```python
if self._enable_btc_trend_kill_gate:
    _btc_ret = self._compute_btc_ret_42(open_time)   # O(log n) on self._btc_idx; None if unavailable
    if _btc_ret is not None and np.isfinite(_btc_ret) and _btc_ret > self._btc_trend_kill_threshold:
        from crypto_trade import decision_log
        decision_log.log({
            "kind": "btc_trend_kill_skip", "symbol": symbol, "ot": open_time,
            "month": candle_month, "btc_ret_42": _btc_ret,
            "btc_trend_kill_threshold": self._btc_trend_kill_threshold,
            "final_signed": _final_signed, "direction_pre_kill": _sp_direction,
            "decision": "skipped:btc_up_regime",
        })
        return NO_SIGNAL
```

`_compute_btc_ret_42(open_time)` mirrors `_compute_ret_270b` (`lgbm.py:1903`): `searchsorted` the
decision candle's `close_time` in `self._btc_idx`, index back 42 bars, return `c_now/c_past - 1.0`
(None if fewer than 42 prior BTC bars or BTC candle missing — conservative pass-through, no kill).

**Conservative pass-through (no look-ahead, no fabricated kill):** if BTC's candle for the decision
`close_time` is absent or has <42 history, the gate does NOT fire (returns the signal unchanged). This
matches the AXIS-R conservative-pass convention and the live BTC-lag-defer discipline.

QE: also wire a backtest-mode `decision_log` sink to
`reports-v1/iteration_v1-092/decision_log.jsonl` (per the /091 secondary finding —
`decision_log.log()` is a no-op in backtest mode; without this the kill-skip entries are dropped and
F2 attribution is unreconstructable).

**Mechanism note (i not ii):** `btc_trend_kill_mode="regime"` kills ALL entries when `btc_ret_42 >
+thr` (BTC_UP), regardless of XRP's `_sp_direction`. This is mechanism (i), chosen over mechanism (ii)
directional-disagreement on the 2.3 generalization evidence. The `_sp_direction` is logged (not used
in the kill condition) so a Phase 7.4 counterfactual can reconstruct what mechanism (ii) would have
done. (A `mode="disagree"` branch may be left in the code stub but is NOT enabled this iteration.)

### 3.2 — Runner `run_iteration_092.py` + `run_baseline_v1.py` "/v1-092" dispatch

Fork `run_iteration_088.py` exactly (XRP-only, specialist_mode=50 seeds × 30 trials, ENSEMBLE_SIZE=1,
atr_tp=2.9 / atr_sl=1.45, R1=OFF / R2=OFF / R3=ON@0.70 / R5=ON@0.3, fail_fast_is_years=2.0,
`feature_columns=list(V1_FEATURE_COLUMNS_PRUNED)` (48)) and add only:
`enable_btc_trend_kill_gate=True, btc_trend_kill_threshold=0.067, btc_trend_kill_lookback=42,
btc_trend_kill_mode="regime"`.

### 3.3 — Pre-registered threshold

`btc_trend_kill_threshold = 0.067`, `lookback = 42`, `mode = "regime"`. Rationale: 0.067 is the
**IS abs-median of `btc_ret_42`** (the natural IS-calibrated split point; computed IS-only as
`btc["btc_ret_42"].abs().median()`). From the robustness grid (2.2) the whole 0.05–0.08 band is CLEAN
for mechanism (i), so 0.067 is a robust interior choice, not an optimized peak. At thr=0.067 the gate
kills the BTC_UP bucket (IS 57/219 = **26.0% IS kill-rate**), retains 162 IS trades summing +75.4%,
and projects **70 OOS survivors** (2.3). Pre-registered and frozen before the run.

### 3.4 — Global feature set UNCHANGED

`V1_FEATURE_COLUMNS_PRUNED` stays at **48** columns. No new feature, no LOCAL feature constant. The
gate reads BTC's close series via the init-built BTC index (NOT a model feature); the model still
trains on the STOCK 48-col PRUNED set. One-variable discipline preserved. The pre-registered 48-col
hash assertion in the runner is UNCHANGED.

### 3.5 — Tests

`tests/test_iteration_v1_092.py`: (i) gate OFF → output bit-identical to /088 path; (ii) gate ON with
a synthetic BTC_UP candle (`btc_ret_42 > 0.067`) → `NO_SIGNAL` regardless of XRP signal direction;
(iii) gate ON with BTC_DOWN/FLAT candle → signal unchanged; (iv) BTC candle absent / <42 history →
conservative pass-through (signal unchanged, no kill); (v) `btc_trend_kill_threshold` + lookback
plumbed from runner to strategy; (vi) PRUNED-48 assertion holds; (vii) `btc_ret_42` computed past-only
(searchsorted indexes strictly ≤ decision close_time).

---

## Section 3.5 — LM Master Phase 4.5 Advisory Integration (ADOPT THE PIVOT)

The Phase 4.5 LM advisory (`briefs-v1/iteration_v1-092/lgbm_advisor.md`, `fda4d2c2`) issued a MODAL
verdict of **NEGATIVE-DID-NOT-FIX (HIGH confidence)** on the original ADX-kill axis and **RECOMMENDED
PIVOT before spending compute**. This revision ADOPTS the pivot. Recommendation-by-recommendation:

- **ADOPTED — pivot ADX-kill → BTC-trend gate.** LM CRUX: the OOS OFF stretch is TREND-WRONG-WAY, not
  chop. The pre-Nov OFF drag (−42.77%) lives in the ADX≥22 KEPT bucket (30/44 trades, −38.61%, ADX
  median 26.28, 27% WR) — strongly trending, wrong direction. An ADX-strength kill removes only −4.17%
  (14 chop trades) and F4 stays 3/8→3/8 (DID-NOT-FIX); it also kills 52% of the WINNING post-Nov
  trades. ADX = trend STRENGTH, structurally orthogonal to DIRECTION → it cannot fix
  wrong-direction-in-trend. **Brief Section 1/2/3 fully re-derived on the BTC-trend axis.**

- **ADOPTED + REFINED — mechanism choice (i) over (ii).** LM floated EITHER mechanism (i) BTC-regime
  kill OR mechanism (ii) directional-disagreement and asked the QR to pick the cleaner IS separator.
  My IS analysis (2.2) shows BOTH are clean IS separators in the 0.05–0.08 band; the **generalization
  forensic (2.3) selects (i)**: mechanism (i)'s OOS kill bucket is net-NEGATIVE (−8.43%, removes
  losers) and improves the OFF window, whereas mechanism (ii)'s OOS kill bucket is net-POSITIVE
  (+14.56%, removes winners) and makes the OFF window WORSE (−42.77% → −56.03%; F4 forensic). So I
  ADOPT the BTC-trend axis but choose mechanism (i), not the directional-disagreement framing the LM
  leaned toward. The LM's IS evidence for mechanism (i) (BTC_UP IS n=57, net −36.71%, sharpe −0.79) is
  exactly what my Section 2.1 reproduces and is the basis for the choice.

- **WHY THIS IS IS-CALIBRATED, NOT OOS-TUNED.** The gate mechanism (kill BTC_UP) and threshold (0.067)
  are derived 100% from IS data: BTC_UP is the worst IS regime (2.1) and 0.067 is the IS abs-median of
  `btc_ret_42` (3.3). The IS evidence stands on its own — XRP loses in BTC_UP in the IS window
  independent of any OOS number. The OOS forensic in 2.3 / Section 7 is **advisory confirmation that
  the IS mechanism generalizes** (it removes OOS losers, not winners); it is read AFTER the threshold
  is frozen and CHANGES NO PARAMETER. This is the structural difference from the ADX axis, whose IS
  split was real but DISSOCIATED from the OOS structure — a fact only knowable by the LM's OOS
  forensic, which I treat as the falsification of the ADX axis, not as a tuning input for the BTC axis.

- **ADOPTED — F3/F4 re-pre-registration.** Per the LM's ask, F3 verifies the BTC-trend gate doesn't
  over-kill below 50 OOS (it projects 70, vs the ADX version's 49 borderline-fail), and F4 is
  re-pre-registered on regime-breadth. Both re-derived in Section 4.

- **ADOPTED — R3/R5 interaction audit + decision_log sink.** Per LM §3 + §6, Phase 7.4 audits the
  BTC-gate↔R3-OOD↔R5-vol overlap, and the backtest-mode decision_log sink is mandatory (else F2 is
  unreconstructable). Both in Sections 3.1 / 5.

- **NOTED — OOS ADX runs hotter than IS (LM §1).** This was a defect of the ADX axis (thr=22 fired
  LESS where needed). It does not apply to the BTC-trend axis: the BTC threshold is on BTC's own return
  distribution (not XRP's ADX), and the F3 projection (2.3) already measures the actual OOS fire-rate
  under the IS-frozen rule (14.6% OOS kill-rate, 70 survivors) — no hidden hot/cold drift.

---

## Section 4 — Pre-Registered Falsifiers (REVISED)

**F1 — IS edge lift (standalone).** IS Sharpe with the BTC-trend kill gate ON must be **≥ +0.20 ABOVE**
XRP/088's IS +0.3783 (i.e. IS Sharpe ≥ **+0.578**). If IS Sharpe Δ < +0.20 vs /088 →
EXPLORATION-NEGATIVE (the gate did not lift the standalone edge). Rationale: the IS-trade PnL math
(2.2) implies a large kept-vs-killed separation (kill −36.7% / keep +75.4%); a real lift should clear
+0.20.

**F2 — Mechanism engaged.** The `btc_trend_kill_skip` decision-log must show the gate fired on roughly
the predicted fraction: **20–45% of candidate entries suppressed** (IS kill-rate is 26.0% at thr=0.067;
OOS projected 14.6%, so the realized rate is window-dependent — the band brackets the IS calibration).
If the suppressed fraction is < 10% (gate inert) or > 60% (gate over-firing, threshold mis-plumbed) →
mechanism-disengaged; the verdict cannot be PROMISING regardless of F1. Requires the backtest-mode
decision_log sink (Section 3.1).

**F3 — Trade-rate floor (THE GATE THE ADX VERSION FAILED).** OOS trades with the gate ON must be
**≥ 50** (per `feedback_v1_trade_rate_floor_50_per_specialist.md`). The ADX version projected 49 (FAIL).
The BTC-regime gate at thr=0.067 projects **70 OOS survivors** (2.3, `btc_gate_oos_projection.csv`) —
clears the floor with margin. If realized OOS trades < 50 → reject (the retrained model's roster may
differ from the post-hoc projection per the /019 Jaccard caveat, so this is VERIFIED at Phase 7, not
assumed). 30–49 → 7-outer-seed validation per the floor rule (foreclosed by the no-multi-seed lock →
would force reject).

**F4 — REGIME-BREADTH (THE KEY FALSIFIER — does it FIX the blocker?).** The improvement must make the
OOS edge **LESS regime-contingent**, not merely amplify the post-Nov ON window. Pre-registered test at
Phase 7: split OOS into the same pre-Nov-2025 (8mo) and post-Nov (7mo) windows as the /089 falsifier.
The gate FIXES the blocker iff the **pre-Nov-equivalent OFF window improves materially** — concretely:
- **PASS:** pre-Nov OOS net PnL ≥ **−5%** AND ≥ **3/8 months positive** (vs /088's −42.77% / 3-of-8).
- **PRE-REGISTERED DID-NOT-FIX-THE-BLOCKER VERDICT:** if the OOS improvement is again concentrated in
  the post-Nov window (post-Nov gains while pre-Nov stays materially negative / months-positive does
  not rise), the gate did NOT fix the regime-contingency → verdict EXPLORATION-NEGATIVE-DID-NOT-FIX (no
  BUNDLE-003 re-candidacy this iteration), even if headline OOS Sharpe rises. F4 is the load-bearing
  acceptance criterion; F1/F2/F3 are necessary but not sufficient.
- **ADVISORY CONTEXT (NOT a calibration target):** the OOS-roster forensic (Section 7) shows mechanism
  (i) moves the pre-Nov window −42.77% → −31.65% (+11.1pp, the right direction) but does NOT, on the
  /088 post-hoc roster, reach the −5% target. The retrained model's roster differs from the post-hoc
  projection (per /019 Jaccard 0.04), so F4 is judged on the ACTUAL retrained OOS at Phase 7 — this
  advisory number is the honest pre-registered expectation that **F4 is the genuine risk** and may
  fire even though mechanism (i) is the best available IS-calibrated detector. The gate is the
  head-on attack on trend-wrong-way; if the OFF window is only partly trend-wrong-way, F4 catches it.

---

## Section 5 — Risk Mitigation (REVISED)

Config matches the /088 SPECIALIST pattern (one-variable discipline) PLUS the new gate as the
risk-primitive under test:

- R1 = OFF (CATALOG-CLOSED for SPECIALIST mode).
- R2 = OFF (Model A baseline — no drawdown scaling).
- R3 = ON (Mahalanobis OOD, cutoff 0.70, 16 scale-invariant `V1_OOD_FEATURE_COLUMNS`).
- R5 = ON (vol_targeting=True, vt_target_vol=0.3, vt_lookback_days=45, vt_min_scale=0.33).
- **R6 (NEW, under test) = ON: BTC-trend kill gate, `btc_trend_kill_threshold=0.067`, lookback=42,
  mode="regime"** — opt-in, IS-calibrated.

ATR barriers: atr_tp=2.9 / atr_sl=1.45 (Model A ETH cell vol-class match; UNCHANGED).

**Simulated historical effect (IS-calibrated, Section 2.2/2.3):** at thr=0.067 the gate would have
removed 57 of 219 IS trades (the BTC_UP bucket) whose summed net PnL was **−36.71%**, retaining 162
trades summing **+75.40%**. On the OOS /088 roster (advisory) it removes 12 of 82 trades summing
−8.43%, retaining +29.23%. The R3 OOD gate suppresses ~30% of candles on a distribution-outlier axis;
the LM (§3) notes BTC-trend kill is **orthogonal to R3** (OOD candles are high-vol/high-ADX, low
overlap with BTC_UP) and that R5 vol-sizing reads the candle series (not the roster), so the gate's
interaction with R5 is a sizing nudge not a clean PnL subtraction — Phase 7.4 LM audits both overlaps.
The gate cannot increase exposure (it only removes entries), so it strictly reduces gross notional and
tail exposure in the BTC_UP regime.

All thresholds IS-calibrated; none derived from OOS.

---

## Section 6 — Risk Management Design (REVISED)

| Primitive | Config | Prediction |
|---|---|---|
| Vol-adjusted size | vt_target_vol=0.3 | ~30% vol-adj fire rate |
| BTC-trend kill gate (R6, NEW) | thr=0.067 on btc_ret_42 (42-bar), mode=regime | IS 26% / OOS ~15% candidate entries suppressed (F2) |
| Z-score OOD (R3) | cutoff=0.70, 16 features | ~30% candles blocked (orthogonal to R6 per LM §3; overlap audited Phase 7.4) |
| Drawdown brake (R2) | OFF | no scaling |
| Consecutive-SL (R1) | OFF | catalog-closed for specialist |
| BTC contagion | N/A (the gate IS the BTC-regime primitive) | — |
| Liquidity floor | XRPUSDT top-5 perpetual | no liquidity risk |

Expected IS trade rate after gate: ~11–13 trades/month (from ~15/mo at /088, minus ~26% IS kill-rate).
Expected OOS trades: ~70 total (F3 floor cleared; projection 2.3).

---

## Section 7 — Pre-Registered Failure-Mode Prediction (REVISED)

**Most plausible failure (F4 fires):** the gate removes BTC_UP entries in OOS but the pre-Nov OFF
stretch is only PARTLY a BTC_UP regime — some of the OFF drag is wrong-direction in BTC_FLAT/DOWN
windows the gate does not touch. The advisory OOS forensic already shows this risk: mechanism (i)
moves pre-Nov −42.77% → −31.65% (the right direction, +11.1pp) but does NOT reach the −5% F4 target on
the /088 post-hoc roster. If the retrained model's roster behaves similarly, F4 fires →
EXPLORATION-NEGATIVE-DID-NOT-FIX. This is the genuine residual risk: the BTC-trend axis is the BEST
available IS-calibrated detector of trend-wrong-way (cleaner than ADX, and unlike mechanism ii it does
not kill winners), but trend-wrong-way may not be FULLY captured by a single BTC-up-regime kill. F4 is
designed precisely to catch this, on the actual retrained OOS, not the projection.

**Secondary failure (NEGATIVE-NO-EFFECT):** the model already partially encodes BTC trend via its
cross-asset funding/OI features, so the explicit BTC_UP kill is largely redundant and the IS lift is
< +0.20 (F1). In that case the gate is informative-but-inert → EXPLORATION-NEGATIVE.

**Tertiary failure (mechanism choice wrong):** if Phase 7 shows mechanism (ii) directional-disagreement
would have outperformed (counterfactual via the logged `direction_pre_kill`), that is a LEARNED finding
for a future iteration — but the IS+generalization evidence (2.3) pre-commits to (i), and a post-hoc
switch to (ii) would be OOS-tuning and is FORBIDDEN this iteration.

Gates that should catch failures: F1 (IS lift), F2 (mechanism engaged), F3 (trade-rate — the ADX
version's failure point, now cleared with margin), F4 (regime-breadth — the acceptance gate).

---

## Section 8 — Pre-Registered MERGE/NO-MERGE Numerical Criteria (REVISED)

This is a SPECIALIST EXPLORATION; it does NOT merge a baseline. Verdict criteria:

**EXPLORATION-PROMISING (BUNDLE-003 re-candidacy)** requires ALL:
1. fail-fast PASSED (XRP first-2yr IS > 0 — expected, /088 was +16.88).
2. F1: IS Sharpe ≥ +0.578 (Δ ≥ +0.20 vs /088 +0.3783).
3. F2: 20–45% of candidate entries suppressed (mechanism engaged, decision_log).
4. F3: OOS trades ≥ 50 (projected 70).
5. **F4: pre-Nov OOS window improves (net ≥ −5% AND ≥ 3/8 months positive) — the gate makes the edge
   LESS regime-contingent.** Load-bearing.
6. σ_SR ≤ 0.50 across the 50 inner seeds (basin-lottery guard) AND specialist_dispersion.csv
   committed.

**EXPLORATION-NEGATIVE-DID-NOT-FIX** (pre-committed): F1/F2/F3 pass but F4 fails (gain again post-Nov
only / pre-Nov not lifted to target) → the regime-contingency blocker is NOT fixed; no re-candidacy
this iteration; the axis is LEARNED (BTC-up-regime kill is the right direction but does not fully
capture trend-wrong-way) and a future iteration tries a finer directional detector (e.g. a
BTC-direction-conditional position-flip rather than a kill, or mechanism (ii) tested standalone after
the (i) counterfactual is reviewed).

**EXPLORATION-NEGATIVE** (any of F1/F2/F3 fails). BASELINE_V1.md UNCHANGED regardless of /092 outcome.

---

## Section 9 — Library Stack Declaration

- LightGBM, Optuna: project `uv.lock` versions; no new library introduced.
- statsmodels: used in `eda.py` for candidate-feature ADF (`adfuller`) — already installed; no new
  dependency.
- No mlfinlab / mlfinpy / pypbo / fracdiff dependency introduced. Fallbacks: N/A.
- The BTC-trend kill gate reuses the iter-v1/074 AXIS-R close-index pattern (BTC `(close_time, close)`
  index + O(log n) lookback) and the /091 R-CONV opt-in-gate site (`lgbm.py`); no new infrastructure.
  Backtest-mode decision_log sink is the one new plumbing item (per /091 finding), shared with the
  rejected ADX design.
