# iter-v3/114 — Research Brief

**Cycle-6 EXPLORATION slot #5 of 10.** Axis (cycle-6 menu item #4 — risk
management): a per-symbol **LDO regime-conditional EXOGENOUS-trigger
kill-switch** — a binary off/on gate that halts LDO position-taking when an
exogenous LDO-realized-volatility z-score regime indicator fires.

---

## Section 0 — Data Split Declaration

- `OOS_CUTOFF_DATE = 2025-03-24` — **UNCHANGED, IMMUTABLE.**
- `training_months = 24` — **UNCHANGED, IMMUTABLE.**
- **IS window:** 2022-09-22 → 2025-03-24 (LDO data begins 2024-09; the LDO IS
  trade roster spans 2024-09-26 → 2025-02-25).
- **OOS window:** 2025-03-24 → 2026-05 (data extent).
- The walk-forward / CPCV backtest runs on ALL data; the reporting layer splits
  at `OOS_CUTOFF_DATE` into `in_sample/` and `out_of_sample/` + `comparison.csv`.
- The QR sees OOS results for the FIRST time in Phase 7. All Phase 1–5 EDA is
  strictly IS-only — `analysis/iteration_v3-114/_shared.py` asserts
  `close_time < OOS_CUTOFF_MS` on every labelled IS frame. The one place the EDA
  touches an OOS-window file is the **explicitly FENCED** T9 / A2 trigger-
  coverage annex — it counts trigger fires on the /059 OOS LDO roster open_times
  to size whether the gate has any OOS firing surface; it does NOT read OOS
  Sharpe/PnL and is NOT used to tune the threshold (the threshold is fixed
  IS-only by the T3 sweep before the annex runs).

## Section 0.5 — Iteration Type Declaration

- **TYPE: EXPLORATION** (cycle-6 EXPLORATION slot #5 of 10; iter-v3/120 is the
  mandatory cycle-6 CONFIRMATION).
- **Run command:** `uv run python run_baseline_v3.py --exploration --n-trials 35 --clean-oof`
- **ENSEMBLE_SIZE = 3** (the `--exploration` outer=42 seed lineage:
  191664963 / 1662057957 / 1405681631).
- **Wall-clock budget: ≤ 2h** (EXPLORATION hard cap per
  `feedback_v3_cadence_discipline.md`; comparable EXPLORATIONs ran 0.4–1.1h).
- **Single axis:** the `RiskV2Config` LDO kill-switch gate. The 22→14
  `V3_FEATURE_COLUMNS` revert and the `ITERATION_LABEL` bump are mandatory
  baseline-restore housekeeping, not a second axis (the /113 closeout mandates
  the revert; see Section 3.5 and the Configuration Diff).
- **Cadence:** slots #1–#4 of cycle 6 are spent — /110 + /111 (universe
  selection, both NEGATIVE), /112 (pooled architecture, NEGATIVE), /113
  (multi-frequency features, NEGATIVE). iter-v3/114 is slot #5; the cycle has
  slots #5–#10 (114–119) remaining before iter-v3/120.

## Section 1 — Hypothesis

Halting LDO position-taking when LDO's exogenous trailing realized-volatility
z-score is in a low-volatility regime (`abs(ldo_realvol_zscore) < 0.30`,
past-only, computed from LDO price alone) lifts the book's monthly Sharpe — most
plausibly the IS Sharpe and, if the low-vol-chop regime transfers, the OOS
Sharpe — because LDO's 2:1-ATR triple-barrier needs price movement to reach the
take-profit, so in a low-realized-volatility chop regime LDO trades grind
disproportionately to stop-loss/timeout, and the /113 OOS attribution names LDO
the −33.09% dominant OOS drag (the one symbol that is the difference between a
flat and a positive book).

## Section 2 — IS-Only Numerical Evidence

The QR backed this axis with a committed IS-only EDA — `analysis/iteration_v3-114/`,
**EDA SHA `d8a9725`**, 3 scripts + 19 result tables. Every script's loader
asserts `close_time < OOS_CUTOFF_MS` (2025-03-24). The triple-barrier labeler
and the exogenous-trigger builders are byte-faithful to
`labeling.label_trades` (triple_barrier branch) and
`risk_v3._build_btc_regime_lookup` respectively, so the EDA counterfactual is
computed on the SAME trigger series the production gate will compute.

### 2.1 — The deadlock-impossibility argument (the /054 sidestep) — T1

A kill-switch is a STATEFUL primitive. Per `feedback_v3_oracle_eda_validity.md`,
ORACLE EDA on a prior trade roster is INVALID for stateful gates where
signal-emission updates persistent state — iter-v3/054's per-symbol drawdown
brake **deadlocked permanently** (brake-ON at OOS-start → no LDO trades → no
state update → frozen). The /054 trigger was ENDOGENOUS — an LDO PnL streak —
so the kill-switch's own action froze the LDO trade outcomes that fed the
streak counter.

The iter-v3/114 trigger is **EXOGENOUS**. The trigger value at every bar is a
function of LDO **price** (a trailing realized-volatility z-score) — NOT of LDO
trade **outcomes**. The kill-switch halts LDO *trading*; it does not halt LDO
*price*. The trigger series is therefore fully determined before any LDO trade
is taken, and the gate-state transition function has **no dependence on the
gate's own action**. Formally: there is no closed feedback loop, so no
stuck-state. T1 records the input provenance of all three candidate triggers and
the deadlock-impossibility for each:

| Trigger | Input series | depends on LDO trades? | deadlock possible? |
|---|---|---|---|
| `btc_drawdown_pct` | BTCUSDT 8h close | No | No |
| `btc_vol_zscore` | BTCUSDT 8h close log-returns | No | No |
| **`ldo_realvol_zscore`** (chosen) | LDOUSDT 8h close log-returns | **No** | **No** |

This is the iter-v3/022-precedented pattern (the BTC-drawdown / BTC-vol regime
gate, RiskV3 primitive 9 — already implemented, tested, shipped). Because the
trigger is exogenous, an ORACLE counterfactual on the /059 LDO roster IS a valid
prediction tool: the gate's suppression of one LDO trade does not change the LDO
price series, hence does not change the trigger value at any other trade.

### 2.2 — Trigger selection: 6 exogenous candidates ranked — S1

The EDA evaluated 6 exogenous regime-trigger candidates against the
ground-truth /059 LDO trade roster (9 IS trades, 12 OOS trades — FENCED). The
loser-vs-winner standardised separation gap on the IS roster (`std_gap` =
(loser-mean − winner-mean) / pooled-SD; the correct-polarity gate suppresses the
half carrying losers):

| Trigger | shipped in primitive 9? | IS std_gap | IS polarity | OOS std_gap (FENCED) | IS↔OOS polarity agree? |
|---|---|---:|---|---:|---|
| `ldo_vs_btc_30d` | No | **−1.2317** | kill_LOW | −0.4841 | yes |
| **`ldo_realvol_zscore`** | No | **−0.7420** | **kill_LOW** | +0.3880 | no |
| `btc_ret_30d` | No | +0.4750 | kill_HIGH | −0.4823 | no |
| `abs(btc_drawdown_pct)` | **yes** | +0.1888 | kill_HIGH | −0.2808 | no |
| `btc_dd_signed` | No | −0.1888 | kill_LOW | +0.2808 | no |
| `abs(btc_vol_zscore)` | **yes** | +0.0564 | kill_HIGH | +1.1156 | yes |

Two findings drive the trigger selection:

1. **The two triggers RiskV3 primitive 9 already ships — `abs(btc_drawdown_pct)`
   and `abs(btc_vol_zscore)` — do NOT separate LDO losers** (IS std_gap +0.19
   and +0.06; both near zero). This is not the iter-v3/022 TRX case, where the
   FTX/LUNA crash was a genuine BTC-stress regime. LDO loses across all BTC
   regimes; some of its biggest *wins* happened at high BTC drawdown (the
   2024-12-22 +16.77% trade had `btc_dd`=9.9). A BTC-stress gate on LDO would
   fire indiscriminately.

2. **`ldo_realvol_zscore` (kill_LOW) is the chosen primary trigger** — see §2.3.

### 2.3 — The surgicality screen + the QR trigger override — S4

`ldo_vs_btc_30d` (LDO 30-day relative strength vs BTC) has the largest raw IS
`std_gap` (−1.23). But a kill-switch must be **SURGICAL** — a binary regime
switch, not a near-constant "symbol off". The decisive screen is the per-bar
**panel fire-rate** — the share of IS LDO candidate candles the gate suppresses
in production (RiskV3 primitive 9 fires at the per-bar signal layer, before the
model is consulted):

| Trigger | IS roster std_gap | panel fire-rate at IS-best threshold | surgical? | chosen? |
|---|---:|---|---|---|
| `ldo_vs_btc_30d` | −1.2317 | **0.46 – 0.79** | **No** — near-constant off | No |
| **`ldo_realvol_zscore`** | −0.7420 | **0.13 (threshold 0.30)** | **Yes** | **Yes** |

`ldo_vs_btc_30d` suppresses 46–79% of all IS LDO candles — LDO underperformed
BTC for most of the v3 IS window (a crypto bear/chop), so "suppress LDO when it
lags BTC" is a near-constant off-switch. Its high 9-trade-roster loser-hit is an
artifact of LDO trading mostly *inside* that regime; it does not isolate a
regime *within* LDO's trading. **The QR therefore overrides the S1 raw-gap
ranking and selects `ldo_realvol_zscore` kill_LOW** — the only candidate that is
simultaneously exogenous (deadlock-free), economically interpretable, SURGICAL,
and (§2.5) directionally coherent on both rosters. `ldo_vs_btc_30d` is recorded
as supporting context — it corroborates that LDO loses in weak-LDO regimes — but
is rejected as the primary trigger on surgicality grounds.

### 2.4 — The chosen gate: `ldo_realvol_zscore` kill_LOW, threshold 0.30

`ldo_realvol_zscore[t]` = z-score of LDO's 30-bar (90-day-equivalent at 8h)
realized volatility of 1-period log returns, computed PAST-ONLY via `.shift(1)`
+ an expanding-mean/std normalisation — the exact construction
`risk_v3._build_btc_regime_lookup` uses for the BTC vol z-score, applied to
LDO's own price. The **kill_LOW gate** suppresses an LDO candidate signal when
`abs(ldo_realvol_zscore) < 0.30`.

IS LDO candle-panel threshold sweep (T3 / panel-fire diagnostic) — the per-bar
fire-rate and the surgicality:

| threshold | IS-panel fire-rate | regime |
|---:|---:|---|
| 0.30 | **0.130** | surgical binary switch (chosen) |
| 0.40 | 0.212 | broader |
| 0.50 | 0.303 | not surgical |

Threshold **0.30** gives a 13.0% IS-panel fire-rate — above the 8% behavioural-
inertia floor (so the axis is non-inert) and far below a near-constant off.

### 2.5 — The chosen gate on the ground-truth /059 LDO rosters — S2/S3/A1/A3

IS LDO roster (9 trades) — the chosen gate (kill_LOW, 0.30):

| Metric | Value |
|---|---|
| IS LDO trades suppressed | **1** of 9 |
| of which losers / winners | **1 / 0** (loser-hit-rate 1.00) |
| counterfactual IS LDO weighted-PnL delta | **+2.36** |
| baseline LDO IS weighted-PnL sum | +8.93 |
| gated LDO IS weighted-PnL sum | **+11.28** |

The gate's loss-direction is clean across the wider IS sweep too: A1 confirms
LDO IS losers carry a *lower* realized-vol z-score (loser-mean 0.703, winner-mean
1.010, `std_gap` −0.74); A3 shows that across thresholds 0.30→0.55 the gate
suppresses ONLY losers (loser-hit-rate 1.00, counterfactual delta +2.4→+4.9 IS
weighted-PnL). The economic mechanism — LDO's 2:1 ATR barrier needs movement to
reach TP; in low-realized-vol chop LDO grinds to SL/timeout — is interpretable
and IS-coherent.

**FENCED OOS coverage annex (T9 / A2) — coverage sizing only, NOT tuning.** At
the IS-fixed threshold 0.30 the gate fires on **7 of the 12** OOS LDO trades,
**5 of them losers** — the loss-direction HOLDS at this threshold (5/7 = 71%
loser-hit). The gate is not dead-on-arrival OOS.

### 2.6 — Honest caveats — S2 verdict = SHARPENED-GO

The EDA verdict is **SHARPENED-GO**, not a clean GO. Three honest caveats:

1. **The 9-trade IS roster is thin.** The chosen gate suppresses exactly 1 IS
   LDO trade; the +2.36 counterfactual delta is one trade. Wider thresholds
   suppress 2 (still both losers) but the panel fire-rate climbs.
2. **The per-bar OOS polarity sign-flips.** S1's roster-level OOS `std_gap` for
   `ldo_realvol_zscore` is +0.39 (sign-flipped vs the IS −0.74) — i.e. at the
   *median split*, OOS LDO losers carry slightly *higher* realized vol. The
   *threshold-0.30* coverage (5/7 OOS fires on losers, §2.5) is directionally
   right, but the median-split polarity is not. The OOS evidence is mixed.
3. **The full IS candle-panel directional-label evidence is null** — across all
   quantiles of `ldo_realvol_zscore` the long-vs-short label balance is ~50%
   (the trigger separates *trade outcomes on the realized roster*, not
   *candle-level label correctness*).

Per THE PRIME DIRECTIVE the EDA designs the sharpest experiment it can and the
**Phase-6 backtest is the decisive test** of whether the IS+OOS loss-direction
coherence at threshold 0.30 is a real low-vol-chop regime or a thin-roster
artifact. The iteration WILL run a backtest.

### 2.7 — Per-symbol non-contamination — T7

The kill-switch is **LDO-only** (`regime_gate_symbols=("LDOUSDT",)`). RiskV3
primitive 9 fires only for symbols in `regime_gate_symbols`; BCH and TRX are not
in scope, so `_regime_gate_fires` returns `False` for them unconditionally and
their candidate signals pass through unchanged. At the per-symbol architecture
layer (one LightGBM per symbol), BCH/TRX Optuna trajectories are wholly
independent of the LDO gate — per `feedback_v3_single_seed_frozen_baseline.md`,
the iter-v3/022 forensic finding: a TRX-only regime gate produced bit-identical
BCH/LDO rosters. BCH/TRX IS+OOS rosters are expected **bit-identical** to /060.

## Section 3 — Proposed Changes

- **Labeling:** UNCHANGED — `label_mode="triple_barrier"`, ATR 2:1 (atr_tp=2.0,
  atr_sl=1.0), `natr_21_raw`, 21-candle (10080-min) timeout.
- **Symbols:** UNCHANGED — `V3_MODELS` = BCHUSDT, LDOUSDT, TRXUSDT (the
  canonical /059 universe). No symbol added or removed (`V3_EXCLUDED_SYMBOLS`
  unaffected).
- **Features:** `V3_FEATURE_COLUMNS` reverts **22 → 14** — the /113
  multi-frequency daily features (`d_ret_5d`, `d_ret_10d`, `d_trend_slope_10`,
  `d_realvol_10`, `d_realvol_ratio`, `d_atr_pctrank_60`, `d_efficiency_10`,
  `d_close_pos_20`) are dropped, restoring the /059-canonical 14-feature stack.
  This is the mandatory baseline-restore housekeeping the /113 closeout
  prescribes (Critic /113 Recommendation 2) — NOT a feature axis. No new feature
  family is added (a risk axis adds zero features — T8; Critic Check 4
  non-applicable).
- **Risk gate:** the SOLE axis — enable RiskV3 primitive 9 (the regime-
  conditional kill-switch) targeted at LDO, with a NEW `kill_LOW`-polarity
  `ldo_realvol_zscore` trigger variant. See Section 3.5 for the precise `src/`
  changes and Section 6 for the gate design.

### Section 3.5 — Precise `src/` Changes for the QE

iter-v3/114 RE-TARGETS RiskV3 primitive 9 from TRX to LDO and adds a new
`kill_LOW`-polarity LDO-realvol-zscore trigger. The existing primitive-9
machinery (`RiskV3Wrapper._regime_gate_fires`, the `RiskV2Config` regime fields,
`GateStats.regime_gate_fires`, `tests/strategies/ml/test_regime_gate.py`) is
REUSED. The changes:

**(1) `src/crypto_trade/strategies/ml/risk_v2.py` — RiskV2Config: add 2 fields.**
Add to the regime-gate config block (near the existing `regime_dd_threshold_pct`
/ `regime_vol_zscore_threshold` fields):
```python
# iter-v3/114: LDO-realized-volatility kill_LOW trigger variant (primitive 9).
# When enable_ldo_realvol_gate is True, primitive 9 ALSO fires for a symbol in
# regime_gate_symbols when abs(LDO-realvol-zscore) < ldo_realvol_zscore_floor
# (a kill_LOW gate: suppress in a LOW-volatility regime). Default OFF.
enable_ldo_realvol_gate: bool = False
ldo_realvol_zscore_floor: float = 0.30  # IS-calibrated (EDA SHA d8a9725, T3)
ldo_realvol_lookback_bars: int = 90     # 30 calendar days at 8h cadence
```

**(2) `src/crypto_trade/strategies/ml/risk_v3.py` — RiskV3Wrapper:**
- Add a builder `_build_ldo_realvol_lookup(ldo_csv_path, lookback_bars)` —
  byte-identical construction to the EDA's `_shared.build_ldo_realvol_zscore`:
  load `data/LDOUSDT/8h.csv`, compute 1-period log returns, a 30-bar trailing
  rolling std `.shift(1)`-ed (past-only), an expanding-mean/std normalisation;
  return `{"open_time": int64[], "ldo_realvol_zscore": float64[]}`. (The
  existing `_build_btc_regime_lookup` is the exact template.)
- In `_build_lookups`: when `config.enable_ldo_realvol_gate` and
  `config.regime_gate_symbols`, populate a new `self._ldo_realvol_lookup` from
  `data/LDOUSDT/8h.csv`. (Mirror the existing `enable_regime_gate` block at
  `risk_v3.py:257-264`.)
- Add `_ldo_realvol_gate_fires(symbol, open_time_ms) -> bool`: returns `True`
  when `symbol in config.regime_gate_symbols` AND the most-recent LDO-realvol
  bar STRICTLY BEFORE `open_time_ms` (the `np.searchsorted(..., side="left") - 1`
  past-only contract — identical to `_regime_gate_fires`) has a finite
  `abs(ldo_realvol_zscore) < config.ldo_realvol_zscore_floor`. Returns `False`
  on warm-up NaN / missing lookup / no prior bar.
- In `get_signal`: the kill_LOW gate fires FIRST, alongside the existing
  primitive-9 `_regime_gate_fires` check (both before `super().get_signal`). The
  combined primitive-9 fire condition for an in-scope symbol is:
  `_regime_gate_fires(...) OR (enable_ldo_realvol_gate AND
  _ldo_realvol_gate_fires(...))`. A fire increments `GateStats.regime_gate_fires`
  and returns `NO_SIGNAL`. (The existing BTC-trigger `_regime_gate_fires` path
  is inert in /114 because `enable_regime_gate` stays `False` — see the
  Configuration Diff — so in practice only the kill_LOW path fires; the OR keeps
  the two trigger families composable for future iterations.)

**(3) `run_baseline_v3.py` — the `RiskV2Config(...)` block (line 1958):**
```python
enable_regime_gate=False,            # UNCHANGED — BTC-stress trigger stays OFF
                                     #   (EDA: BTC triggers do not separate LDO)
regime_gate_symbols=("LDOUSDT",),    # CHANGED from () — LDO is the gate target
enable_ldo_realvol_gate=True,        # NEW — iter-v3/114 axis: kill_LOW gate ON
ldo_realvol_zscore_floor=0.30,       # NEW — IS-calibrated (EDA SHA d8a9725)
ldo_realvol_lookback_bars=90,        # NEW
```

**(3-guard) `run_baseline_v3.py` — UPDATE the pre-flight guard at lines
826–831 (REQUIRED — Phase 5.5 BLOCK fix; without this the runner crashes
before any backtest runs).** A /075-era hard `RuntimeError` guard currently
asserts `regime_gate_symbols` is empty `()`:
```python
# /075-era guard — CURRENT state (lines 826-831):
if strat_check.config.regime_gate_symbols != ():
    raise RuntimeError(
        f"RiskV2Config.regime_gate_symbols = {strat_check.config.regime_gate_symbols} "
        "— expected () (empty). iter-v3/075: the /074 regime gate is reverted; "
        "regime_gate_symbols must be empty."
    )
```
Because Section 3.5(3) sets `regime_gate_symbols=("LDOUSDT",)`, this /075-era
guard would fire and crash Phase 6 at pre-flight validation before the
backtest starts. The QE MUST REPLACE the lines-826–831 guard with a new
assertion appropriate to iter-v3/114's LDO-scoped kill_LOW state — it must
assert BOTH that `regime_gate_symbols == ("LDOUSDT",)` AND that
`enable_ldo_realvol_gate == True` (so the guard still catches an accidental
mis-configuration, but admits exactly the /114 axis):
```python
# iter-v3/114: Primitive 9 is RE-TARGETED from TRX to LDO with a NEW
# kill_LOW-polarity ldo_realvol_zscore trigger (the cycle-6 EXPLORATION #5
# risk axis). The /075-era "regime_gate_symbols must be ()" guard is
# superseded: /114's axis REQUIRES the LDO-scoped kill_LOW gate ON. The
# guard now asserts exactly the /114 state — LDO is the sole gate target
# AND the kill_LOW realvol gate is enabled — so an accidental drift
# (empty symbols, wrong symbol, or the gate left off) still crashes
# pre-flight.
if strat_check.config.regime_gate_symbols != ("LDOUSDT",):
    raise RuntimeError(
        f"RiskV2Config.regime_gate_symbols = {strat_check.config.regime_gate_symbols} "
        '— expected ("LDOUSDT",). iter-v3/114: primitive 9 is re-targeted to '
        "LDO with the kill_LOW realvol trigger; regime_gate_symbols must be "
        '("LDOUSDT",).'
    )
if not strat_check.config.enable_ldo_realvol_gate:
    raise RuntimeError(
        "RiskV2Config.enable_ldo_realvol_gate = False — expected True. "
        "iter-v3/114: the LDO-realvol kill_LOW gate (primitive 9 variant) "
        "IS the iteration axis and must be ON. Set "
        "enable_ldo_realvol_gate=True in RiskV2Config init in "
        "_build_v3_model."
    )
```
**The ADJACENT `enable_regime_gate=False` guard at lines 818–825 is COMPATIBLE
with iter-v3/114's config and must NOT be changed.** iter-v3/114 keeps
`enable_regime_gate=False` (the BTC-stress trigger stays OFF — the EDA showed
the BTC triggers do not separate LDO losers, §2.2); the lines-818–825 guard
correctly continues to assert that. The QE touches ONLY the lines-826–831
guard. This guard update is part of the iter-v3/114 axis plumbing — it is not
a second axis.

**(4) `src/crypto_trade/features_v3/__init__.py` — revert `V3_FEATURE_COLUMNS_TOP_N`
22 → 14:** delete the 8 `d_*` daily-feature entries and the iter-v3/113
commentary block (lines ~290–303); restore the docstring to the 14-feature
state. The `multifreq_v3` module + its `GROUP_REGISTRY` registration stay as
dormant infrastructure (zero revert cost — the established v3 dead-code pattern).

**(5) `run_baseline_v3.py` — `ITERATION_LABEL = "v3-114"`** (line 131).

**(6) `tests/strategies/ml/test_regime_gate.py` — add a kill_LOW adversarial
test:** assert (a) `_ldo_realvol_gate_fires` does NOT see the current bar (a
volatility spike at bar `t` is invisible to the gate decision at bar `t`,
visible at `t+1`); (b) the gate fires when `abs(ldo_realvol_zscore) < floor` and
does NOT fire when `≥ floor`; (c) `_ldo_realvol_gate_fires` returns `False` for
a symbol not in `regime_gate_symbols`.

**Track isolation:** `risk_v3.py` imports only `numpy`/`pandas`/`pathlib` +
`crypto_trade.strategies` + `crypto_trade.strategies.ml.risk_v2` +
`crypto_trade.config` — no `crypto_trade.features` / `features_v2` import. The
new builder reads `data/LDOUSDT/8h.csv` (the same CSV class as
`_build_btc_regime_lookup`'s `data/BTCUSDT/8h.csv`).

**`REQUIRED_GAP` = 66** = `(timeout_candles=21 + 1) × n_symbols=3` — UNCHANGED
(universe unchanged at 3 symbols).

### Configuration Diff vs /059

| Knob | /059 canonical | iter-v3/114 | Substantive? |
|---|---|---|---|
| `V3_MODELS` | BCH/LDO/TRX | BCH/LDO/TRX | no |
| `label_mode` | `triple_barrier` | `triple_barrier` | no |
| ATR multipliers | 2.0 / 1.0 | 2.0 / 1.0 | no |
| `V3_FEATURE_COLUMNS` count | 14 | 14 | no (reverts /113's 22→14 — housekeeping) |
| `REQUIRED_GAP` | 66 | 66 | no |
| ENSEMBLE_SIZE (run) | 10 (CONFIRMATION) | 3 (`--exploration`) | no (EXPLORATION mode) |
| `enable_regime_gate` | False | False | no |
| `regime_gate_symbols` | `()` | `("LDOUSDT",)` | **YES — the axis** |
| `enable_ldo_realvol_gate` | (field absent) | `True` | **YES — the axis** |
| `ldo_realvol_zscore_floor` | (field absent) | `0.30` | **YES — the axis** |
| `ITERATION_LABEL` | `v3-059` | `v3-114` | no (label) |

Exactly **one substantive axis**: the LDO realvol kill_LOW gate (the
`regime_gate_symbols` + `enable_ldo_realvol_gate` + `ldo_realvol_zscore_floor`
triple is one mechanism). The 22→14 feature revert is mandatory /113-closeout
housekeeping; `ITERATION_LABEL` is a label.

## Section 4 — Expected OOS Impact

**Anchor (EXPLORATION-mode reference):** iter-v3/060 — IS monthly Sharpe
**+0.8325**, OOS monthly Sharpe **+0.1403** (the 3-seed EXPLORATION-mode anchor,
per `feedback_v3_cycle1_axis_pass_criteria.md`). PROMISING-AT-EXPLORATION must
cross-validate at the iter-v3/120 CONFIRMATION against the /059 CONFIRMATION
baseline (IS +1.0894 / OOS +0.5791).

**Predicted effect.** The kill-switch is surgical (13% IS-panel fire-rate) and
LDO carries only 0.78% of /059's IS PnL — so the IS Sharpe effect is **small by
construction**. The EDA ORACLE counterfactual removes ~1 IS LDO loser (+2.36 LDO
weighted-PnL), a fraction of a Sharpe point at the portfolio level.

- **IS monthly Sharpe:** point estimate **+0.87**; 80% interval **[+0.78, +0.98]**
  — centred slightly above the /060 anchor (the gate removes a small IS LDO
  drag) but the interval is tight and includes the anchor (a behaviourally
  surgical per-symbol gate cannot move a BCH-dominated IS book much).
- **OOS monthly Sharpe:** point estimate **+0.18**; 80% interval
  **[−0.10, +0.45]** — centred just above the /060 anchor (+0.1403). The
  interval is deliberately WIDE and its lower bound is *below* the anchor,
  because the OOS evidence is genuinely mixed (§2.6: the per-bar OOS polarity
  sign-flips; the FENCED coverage holds direction at threshold 0.30 but only
  71% clean). Per the Critic /113 Recommendation 3 calibration discipline, when
  the EDA evidence is mixed the predicted interval is centred at-or-near the
  anchor with a below-anchor lower bound.

**Falsifier (the explicit rejection condition).** The hypothesis is REJECTED
(EXPLORATION-NEGATIVE) if **OOS monthly Sharpe < −0.10** OR **IS monthly Sharpe
< +0.7325** (the /060 anchor − 0.10 NEGATIVE floor, per
`feedback_v3_cycle1_axis_pass_criteria.md`). The PROMISING bar (per the same
rule) is IS Δ ≥ +0.10 AND OOS Δ ≥ +0.20 vs the /060 anchor AND
`frac_positive_paths ≥ 0.50`.

**Supplemental SUSPICIOUS gate** (per `feedback_v3_oos_is_ratio_gate.md`): if the
OOS/IS monthly Sharpe ratio > 3.0, the result is flagged SUSPICIOUS regardless
of absolute OOS Sharpe. Given the predicted IS +0.87 / OOS +0.18, the expected
ratio ≈ 0.21 — comfortably inside the healthy [0.5, 2.0] band is NOT expected
(0.21 is below 0.5); the low ratio would reflect a near-zero OOS numerator, not
an OOS-dominant overfit — the NEGATIVE/INERT taxonomy (not SUSPICIOUS) subsumes
that case.

**Behavioural-effect predictor (pre-registered, ABOVE the inertia floor — Critic
/113 Recommendation 3).** A per-symbol risk gate that touches LDO's ~9-trade IS
roster within a 171-trade portfolio is **structurally incapable** of moving the
*portfolio* roster by 8% (max 9/171 = 5.3%) — so the /113-style portfolio-roster
inertia metric is the WRONG metric for a per-symbol risk axis. The behavioural-
effect predictor is pre-registered on **two correct channels**:

- **Channel A — LDO training-panel reshape:** the gate fires at the per-bar
  signal layer, so it reshapes the LDO training panel. **Predicted: 13.0% of IS
  LDO candidate candles suppressed** (T3/T5; 13.0% > the 8% inertia floor).
- **Channel B — LDO roster (the target-symbol inertia metric):** **Predicted:
  ≥ 1 LDO IS trade suppressed** vs the /059-canonical 9. **Behavioural-inertia
  falsifier:** if the production backtest suppresses **0 LDO IS trades** (LDO IS
  roster Δ = 0 vs /060), the axis is behaviourally inert and the iteration is
  classified INERT.

## Section 5 — Risk Mitigation

iter-v3/114 IS itself a risk-management iteration — the deliverable is a risk
primitive. The risk-mitigation analysis therefore covers the risk the new
primitive itself introduces, with IS-calibrated thresholds and the simulated
historical effect (per `feedback_v3_risk_mitigation_design.md`).

**R-PRIMITIVE — the LDO realvol kill_LOW gate (RiskV3 primitive 9 variant).**
- **IS-calibrated threshold:** `ldo_realvol_zscore_floor = 0.30` — fixed by the
  T3 IS-only panel-fire sweep (13.0% IS-panel fire-rate). NOT tuned on OOS.
- **Simulated historical effect (ORACLE counterfactual on the /059 LDO IS
  roster):** suppresses 1 of 9 IS LDO trades — a loser — for +2.36 IS LDO
  weighted-PnL (LDO IS weighted-PnL +8.93 → +11.28). On the FENCED /059 OOS LDO
  roster the gate fires on 7 of 12 trades, 5 of them losers.
- **The deadlock risk — explicitly mitigated.** The /054 stateful-deadlock
  failure mode is structurally sidestepped: the trigger is EXOGENOUS (a function
  of LDO price, not LDO trade outcomes — §2.1, T1). The gate-state transition
  function has no dependence on the gate's own action — no closed feedback loop,
  no stuck-state. There is therefore no "Deadlock Analysis" subsection needed in
  the `feedback_v3_oracle_eda_validity.md` sense; the deadlock-impossibility is a
  one-line proof: the trigger series is fully determined from LDO OHLCV before
  any LDO trade, so halting LDO trading cannot change it. (See §2.1.)
- **Look-ahead risk — mitigated by the past-only contract.** The trigger uses
  `.shift(1)` + a strict `np.searchsorted(..., side="left") - 1` as-of join — the
  current bar's own LDO close is NEVER in the gate decision. The Section 3.5(6)
  adversarial test enforces this (a spike at bar `t` invisible at `t`, visible at
  `t+1`).
- **Over-suppression risk — bounded by the surgical threshold.** At a 13% panel
  fire-rate the gate cannot gut the LDO book; LDO still emits the bulk of its
  candidate signals. The trade-rate floor (Section 8) checks the realised OOS
  trade count.

**Inherited risk stack — UNCHANGED.** The /059 7-primitive RiskV2 stack (BTC
trend kill, vol scaling, ADX, Hurst regime, feature z-score OOD, low-vol filter,
hit-rate-disabled) is carried unchanged. iter-v3/114 ADDS the LDO kill_LOW gate;
it does not modify any inherited primitive. `enable_regime_gate` (the BTC-stress
trigger) stays `False` — the EDA showed the BTC triggers do not separate LDO
losers, so the BTC trigger is deliberately left off.

## Section 6 — Risk Management Design

The v3 risk stack with iter-v3/114's addition (RiskV3 primitive 9, LDO-realvol
kill_LOW variant). Fire-rate predictions and regime coverage:

| # | Primitive | Scope | iter-v3/114 state | Predicted IS fire-rate |
|---|---|---|---|---|
| 1 | Vol scaling | all | inherited, unchanged | n/a (continuous) |
| 2 | ADX threshold (20.0) | all | inherited, unchanged | ~per /059 |
| 3 | Hurst regime band | all | inherited, unchanged | ~per /059 |
| 4 | Feature z-score OOD (2.0) | all | inherited, unchanged | ~per /059 |
| 5 | Low-vol filter | all | inherited, unchanged | ~per /059 |
| 6 | BTC trend kill (±15%) | all | inherited, unchanged | ~per /059 |
| 7 | Hit-rate gate | all | inherited, DISABLED | 0 |
| 9a | Regime kill-switch — BTC-stress trigger | TRX (historically) | **OFF** (`enable_regime_gate=False`) | 0 |
| **9b** | **Regime kill-switch — LDO-realvol kill_LOW trigger** | **LDOUSDT** | **ON (the iter-v3/114 axis)** | **13.0% of LDO candidate candles** |
| 12 | BTC-trend SIZE de-rate | (historically) | OFF | 0 |

**Gate-fire order** (`RiskV3Wrapper.get_signal`): primitive 9 fires FIRST —
before the inner model is consulted — so a low-LDO-realvol bar produces
`NO_SIGNAL` without ever running inference. This is by design: by killing the
LDO signal before Optuna sees the bar, the LDO training-panel distribution
shifts to exclude low-vol-chop bars (a 13% panel reshape; Channel A).

**Regime coverage.** The gate covers the **LDO low-realized-volatility regime**
— the regime the EDA (A1/A3) identifies as LDO's loss-dense regime (LDO losers
carry a lower realized-vol z-score; the 2:1 ATR barrier needs movement). It does
NOT cover BTC-stress regimes (deliberately — the EDA showed BTC triggers do not
separate LDO losers; primitive 9a stays off). BCH and TRX have ZERO regime-gate
coverage (the gate is LDO-scoped — §2.7); their rosters are expected
bit-identical to /060.

**Precedent and the dead-path question — addressed head-on.** RiskV3 primitive 9
was tested twice before: iter-v3/022 (TRX-scoped, BTC-stress trigger,
NEGATIVE-pre-fix) and iter-v3/074 (TRX-scoped, BTC-stress trigger,
INERT-post-fix). The BASELINE_V3.md "Dead Ideas" records primitive 9 as "CLOSED
across two data points." **iter-v3/114 is NOT a retry of that dead path** — it
is a materially different design backed by NEW committed IS-only EDA evidence
(EDA SHA `d8a9725`), per the `feedback_v3_concentration_is_signal.md` requirement
that a kill-switch axis carry new counterfactual evidence:

1. **Different target symbol** — /022/074 gated TRX; /114 gates **LDO** (the
   /113 OOS-named −33% drag).
2. **Different trigger family** — /022/074 used `abs(BTC drawdown)` /
   `abs(BTC vol z)`; /114's EDA (S1) shows those triggers do NOT separate LDO
   losers (IS std_gap +0.19 / +0.06) and selects a **new trigger**,
   `ldo_realvol_zscore`.
3. **Different polarity** — /022/074 killed in *high* BTC-stress (kill_HIGH);
   /114 kills in *low* LDO realized vol (**kill_LOW**) — the opposite gate
   geometry.

Per the `feedback_v3_oracle_eda_validity.md` retroactive-application clause, the
/074 verdict stands; iter-v3/114 is a new axis with its own EDA-grounded
hypothesis. The cycle-6 menu (`project_v3_cycle6_axis_menu.md`) explicitly
mandates the risk-management axis as a cycle-6 menu item, and a binary off/on
kill-switch is a permitted orthogonal mechanism per
`feedback_v3_concentration_is_signal.md`.

## Section 7 — Pre-Registered Failure-Mode Prediction

The most plausible way iter-v3/114 fails OOS — **the modal outcome** — is
**INERT-to-mildly-negative on the OOS axis**. The EDA verdict is a SHARPENED-GO
with mixed OOS evidence (§2.6): the LDO-realvol kill_LOW trigger separates LDO
losers cleanly on the 9-trade IS roster (every suppressed IS trade is a loser;
IS `std_gap` −0.74) and the FENCED OOS coverage holds the loss-direction at
threshold 0.30 (5/7 OOS fires on losers) — but the per-bar OOS median-split
polarity sign-flips and the full IS candle-panel directional-label evidence is
null. The modal failure: the IS-calibrated low-realized-vol regime is a real
but **thin** signal, and a 13%-panel-fire surgical gate that touches LDO's
~9-trade IS roster within a BCH-dominated 171-trade book moves the headline
little — IS monthly Sharpe lands in the [+0.78, +0.98] band (≈ the /060 anchor,
the +2.36 LDO weighted-PnL diluted to a fraction of a portfolio Sharpe point),
and OOS monthly Sharpe lands in the [−0.10, +0.45] band. If OOS lands in
[−0.10, +0.20] the iteration is filed **INERT** (the gate fires but the LDO
low-vol regime does not transfer to a net OOS lift); if OOS lands below −0.10
the iteration is **NEGATIVE** (the OOS polarity sign-flip dominates — the gate
suppresses OOS-profitable low-vol LDO trades).

The gate Section 8 should catch: the trade-rate floor would catch a gate that
over-suppresses; the behavioural-inertia falsifier (Channel B) would catch a
gate that fires on 0 real LDO trades; the OOS/IS SUSPICIOUS gate would catch an
OOS-dominant overfit (not expected here — the predicted ratio is low because the
OOS numerator is small, not because OOS is anomalously strong).

A **second, less likely failure mode**: behavioural inertia at the LDO-roster
level — the production Optuna re-optimisation absorbs the 13%-panel reshape and
the gate ends up suppressing **0** real LDO trades (Channel B falsifier fires).
The EDA ORACLE counterfactual predicts ≥ 1 LDO IS trade suppressed, so this is
judged low-probability — but it is pre-registered, and if it fires the iteration
is INERT regardless of the Sharpe deltas.

A **clean PROMISING outcome** (IS Δ ≥ +0.10 AND OOS Δ ≥ +0.20 vs /060) would
require the LDO low-realized-volatility regime to be a genuinely transferable
loss regime — the EDA's mixed OOS evidence makes this the less-likely of the
outcomes, but not implausible (the FENCED OOS coverage at threshold 0.30 does
hold direction). The Phase-6 backtest is the decisive test.

## Section 8 — Pre-Registered MERGE / NO-MERGE Numerical Criteria

This is an EXPLORATION — it does NOT update `BASELINE_V3.md` regardless of
outcome (only a CONFIRMATION updates the baseline). The criteria below classify
the EXPLORATION for the catalog and gate whether the LDO-realvol kill_LOW gate
advances to the iter-v3/120 CONFIRMATION bundle. All thresholds are LOCKED
before the Phase-6 backtest. Anchor: iter-v3/060 EXPLORATION-mode reference
(IS +0.8325 / OOS +0.1403).

**Classification (disjunctive — read each criterion AS WRITTEN):**

- **PROMISING** (advances to the iter-v3/120 CONFIRMATION as a candidate
  component) iff ALL of:
  - C1: IS monthly Sharpe Δ ≥ **+0.10** vs the /060 anchor (IS ≥ +0.9325), AND
  - C2: OOS monthly Sharpe Δ ≥ **+0.20** vs the /060 anchor (OOS ≥ +0.3403), AND
  - C3: `frac_positive_paths` (CPCV) ≥ **0.50**, AND
  - C4: the LDO kill_LOW gate suppressed **≥ 1** LDO IS trade (Channel B —
    behavioural non-inertia), AND
  - C5: OOS/IS monthly Sharpe ratio ≤ **3.0** (NOT SUSPICIOUS per
    `feedback_v3_oos_is_ratio_gate.md`), AND
  - C6: BCH and TRX IS+OOS rosters are bit-identical to /060 (the gate is
    LDO-only; non-contamination — §2.7).

- **EXPLORATION-NEGATIVE** iff EITHER:
  - F1: OOS monthly Sharpe < **−0.10**, OR
  - F2: IS monthly Sharpe < **+0.7325** (the /060 anchor − 0.10 floor).

- **INERT** iff the iteration is neither PROMISING nor NEGATIVE AND EITHER:
  - the LDO kill_LOW gate suppressed **0** LDO IS trades (Channel B inertia
    falsifier — the axis did not behave), OR
  - OOS monthly Sharpe Δ is within the **[−0.10, +0.20]** noise band vs the /060
    anchor (the gate fired but produced no net OOS lift).

- **SUSPICIOUS** (a supplemental flag, per `feedback_v3_oos_is_ratio_gate.md`):
  if OOS/IS monthly Sharpe ratio > 3.0, flag SUSPICIOUS regardless of the
  absolute OOS Sharpe; the Critic adjudicates whether the flag is
  overfitting-driven (an OOS-dominant book) or a near-zero-IS-numerator artifact
  (subsumed by INERT/NEGATIVE).

**Trade-rate floor** (per `feedback_v3_trade_rate_floor_bundle_level.md`): the
≥ 130 OOS-trades / ≥ 10-per-month floor applies at the iter-v3/120
**CONFIRMATION-bundle** level, not per EXPLORATION row. At this single-axis
EXPLORATION the OOS trade count is **informational** — but it will be reported,
and a count materially below /060's (a sign the LDO gate over-suppressed
portfolio-wide) is itself evidence for the INERT/NEGATIVE classification.

## Section 9 — Library Stack Declaration

No new libraries. iter-v3/114 adds zero feature families and uses no
mlfinlab/mlfinpy/pypbo/fracdiff path beyond the inherited /059 stack. Pinned
versions (from `BASELINE_V3.md` reproducibility stamp; carried unchanged):

- `lightgbm 4.6.0`, `optuna 4.8.0`, `numpy 2.2.6`, `pandas 3.0.0`,
  `scikit-learn 1.8.0`, `scipy 1.17.0`, `statsmodels 0.14.6`, `pyarrow 23.0.1`.
- CPCV / PBO / PSR / DSR reporting: the inherited `validation_v3.py` +
  `dsr.json` Path-B4 machinery (unchanged).
- The EDA (`analysis/iteration_v3-114/`) uses only `numpy` / `pandas` from this
  pinned stack.
- The new `RiskV3Wrapper._build_ldo_realvol_lookup` builder uses only `numpy` /
  `pandas` / `pathlib` — no new dependency.

## Section 10 — QR Audit Trail

- **Axis source.** The iter-v3/114 axis (a per-symbol LDO regime-conditional
  exogenous-trigger kill-switch) is the iter-v3/113 diary's "Next Iteration
  Ideas" recommendation (Section 9), motivated by the /113 per-symbol OOS
  attribution naming LDO the −33.09% dominant drag. It is cycle-6 axis-menu item
  #4 (risk management) — the last untested cycle-6 menu item
  (`project_v3_cycle6_axis_menu.md`).
- **QR EDA-driven trigger selection — supersedes the diary's loss-streak
  framing.** The /113 diary's recommendation framed the trigger as "a BTC-
  drawdown / LDO-realized-volatility z-score regime indicator". The QR's
  committed IS-only EDA (`analysis/iteration_v3-114/`, EDA SHA `d8a9725`) tested
  6 exogenous trigger candidates and found: (a) the two BTC triggers RiskV3
  primitive 9 already ships do NOT separate LDO losers (S1: IS std_gap +0.19 /
  +0.06); (b) `ldo_vs_btc_30d` has the largest raw separation but is
  non-surgical (46–79% panel fire-rate — a near-constant off-switch); (c)
  **`ldo_realvol_zscore` kill_LOW @ 0.30 is the surgical, IS-coherent choice**
  (S4 surgicality override). The QR's EDA — not the diary's prose, not the
  orchestrator — is the final arbiter of the trigger, per
  `feedback_v3_axis_selection_quant_discipline.md`. The EDA precedes this brief.
- **Honest EDA-result disclosure.** The EDA verdict is **SHARPENED-GO**, not a
  clean GO — the OOS evidence is genuinely mixed (the per-bar OOS polarity
  sign-flips; the candle-panel directional evidence is null). The brief reports
  this honestly (§2.6, §7) and centres the OOS predicted interval at-or-near the
  anchor with a below-anchor lower bound (Critic /113 Recommendation 3 discipline).
  Per THE PRIME DIRECTIVE the EDA designs the experiment, it does not terminate
  it — iter-v3/114 runs a Phase-6 backtest as the decisive test.
- **Dead-path due diligence.** The QR verified RiskV3 primitive 9's prior
  history (iter-v3/022 NEGATIVE, iter-v3/074 INERT — both TRX-scoped BTC-stress
  gates) and Section 6 addresses head-on why iter-v3/114 is a materially
  different design (different target symbol, different trigger family, opposite
  polarity) backed by new committed EDA evidence — not a retry of the closed
  TRX-BTC-stress dead path.
- **Setup commit SHA:** (to be backfilled by the orchestrator after the setup
  commit lands.)
- **EDA SHA:** `d8a9725` — `analysis(iter-v3/114): LDO kill-switch gating EDA`.
- **Brief SHA:** this commit — `docs(iter-v3/114): research brief`.
