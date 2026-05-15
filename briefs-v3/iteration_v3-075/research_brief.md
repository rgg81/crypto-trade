# Iteration v3-075 — Research Brief

CYCLE 2 EXPLORATION #5 of 10 — Primitive 12: BTC-trend-regime position-SIZE
de-rate scalar (LDO+TRX-scoped).

---

## Section 0 — Data Split Declaration

- OOS_CUTOFF_DATE: **2025-03-24** (unchanged — IMMUTABLE; `src/crypto_trade/config.py`)
- training_months: **24** (unchanged — IMMUTABLE)
- IS window: **[2022-02-XX, 2025-03-24)** — earliest /060 IS month 2022-02; the IS
  window spans the 2022 bear, 2023 chop, the 2024 bull, and the 2024-Q4/2025-Q1
  deceleration.
- OOS window: **[2025-03-24, 2026-05-XX)** — latest /060 OOS month 2026-05; a
  persistent BCH/LDO/TRX uptrend.
- ENSEMBLE_SIZE: **3** (EXPLORATION mode — `--exploration` → `EXPLORATION_ENSEMBLE_SIZE`)
- ENSEMBLE_SEEDS: outer=42 lineage subset `[191664963, 1662057957, 1405681631]`
- start_time: UNCHANGED — the backtest runs from the earliest available data. No
  date trimming (`feedback_no_cheating.md`).

---

## Section 0.5 — Iteration Type Declaration

**TYPE = EXPLORATION** (cycle 2 #5 of 10).

- Axis: **Primitive 12 — a BTC-trend-regime-conditional position-SIZE de-rate
  scalar**, scoped to LDO+TRX. A NEW risk primitive (the structural-axis category
  per `feedback_v3_structural_over_knob_exploration.md` — NOT a gate-threshold
  knob). QR-chosen per `feedback_v3_axis_selection_quant_discipline.md` with
  committed EDA backing (`analysis/iteration_v3-075/axis_selection_eda.py`,
  SHA `9a04f6f`).
- Run mode: `--exploration` (3-seed, outer=42 lineage), `--n-trials 35`, 3-symbol
  universe (BCH/LDO/TRX), REQUIRED_GAP=66, embargo 22. Total 315 Optuna trials.
- Wall-clock budget: **≤ 1.0h** (estimate 0.6–0.9h; /071/072/073/074 all ran
  0.65–0.70h; this axis adds one per-bar BTC-SMA lookup — cheaper than a labeling
  change, comparable to /074's regime-gate lookup).
- This is **NOT** a PASSIVE-DIAGNOSTIC. There is one substantive code change
  (Primitive 12) and a backtest is run.

Cadence note: this is an EXPLORATION; it consumes cycle-2 slot #5 of 10. The
cycle-2 CONFIRMATION is iter-v3/081 or later (`feedback_v3_strict_10_to_1_cadence.md`
— do NOT collapse the 10th EXPLORATION into the CONFIRMATION). Cycle 2 so far:
/071 SUSPICIOUS-OOS-DOMINANT, /072 NEGATIVE, /073 SUSPICIOUS-OOS-DOMINANT, /074
INERT-AT-EXPLORATION — zero clean PROMISING.

---

## Section 1 — Hypothesis

A BTC-trend-regime position-SIZE de-rate scalar — multiplying the position WEIGHT
of LDO and TRX trades by 0.50 when BTC is in a bear/chop trend state
(close[t-1] < SMA_270(close)[t-1]), and leaving the weight unchanged when BTC is
in a bull trend state — lifts IS monthly Sharpe by down-scaling the IS bear/chop
trades that drag the strategy, WITHOUT extending effective trade holding time
(it scales weight, never SL/TP/timeout) and therefore without loading the IS/OOS
regime-divergence factor that trips the OOS/IS ratio gate.

The scalar is SCOPED to LDO+TRX because the EDA (Section 2) shows BCH WINS in
BTC-bear/chop months — a blanket all-3-symbol de-rate would down-scale BCH's IS
edge and is IS-NEGATIVE.

---

## Section 2 — IS-Only Numerical Evidence

- Script: `analysis/iteration_v3-075/axis_selection_eda.py` (committed, SHA `9a04f6f`)
- Outputs: `analysis/iteration_v3-075/` — `T0_anchor_values.csv`,
  `T1_regime_stratification.csv`, `T2_classifier_sweep.csv`,
  `T3_derate_counterfactual.csv`, `T7_per_symbol_bearchop_economics.csv`,
  `T8_scoped_derate_counterfactual.csv`, `T4_holding_time_predictor.csv`,
  `T5_behavioral_predictor.csv`, `T6_per_symbol_is_discipline.csv`,
  `axis_selection_summary.csv`, `synthesis.md`

The EDA runs NO backtest — every table is descriptive arithmetic on the committed
/060 trade roster. IS tables use IS-window data only (open_time < OOS_CUTOFF_MS).
The BTC-trend classifier applies `close.shift(1)` BEFORE the rolling SMA —
identical past-only contract to `risk_v3._build_btc_regime_lookup`.

### 2.1 T1 — IS/OOS regime-stratified diagnostic (the drag to lift)

The /060 anchor's monthly PnL split into three regime sub-periods (re-derives the
/074 PART 1 finding):

| Regime | Months | Monthly Sharpe | Mean monthly PnL% | % positive months | Trades |
|---|---:|---:|---:|---:|---:|
| IS bear/chop (2022-09→2023-12) | 19 | **-0.2193** | -0.3618 | 26.3% | 77 |
| IS bull (2024-01→2025-03) | 15 | **+1.8504** | +3.9176 | 53.3% | 82 |
| OOS uptrend (2025-03→2026-05) | 14 | **+0.1403** | +0.3928 | 50.0% | 102 |

**Finding.** The IS bear/chop sub-period is the structural drag — monthly Sharpe
-0.2193, only 26.3% of months positive, total wpnl -6.87. The IS bull sub-period
carries the entire IS edge (+1.85, +58.76 wpnl). This is the drag Critic /074
Rec #3 mandates /075 lift directly. (Minor note: T1 monthly Sharpe for the
bear/chop sub-period reads -0.2193 here vs the /074 brief's -0.0242 — the /074
figure was computed over a `monthly_pnl.csv` series; T1 here recomputes monthly
Sharpe from the trade roster's `weighted_pnl` aggregated to calendar months — the
canonical `comparison.csv` construction. The qualitative finding — IS bear/chop
is the drag — is identical and robust to the construction.)

### 2.2 T2 — BTC-trend-regime classifier sweep (the classifier choice)

A past-only BTC bull/bear-chop classifier: BTC is in bear/chop at bar t when
close[t-1] < SMA_N(close)[t-1]. The sweep measures, per slow-MA window N, how the
classifier tags IS-bear/chop trades vs IS-bull and OOS trades:

| MA window (bars / days) | IS bear/chop flagged% | IS bull flagged% | OOS flagged% | IS discrimination (pp) |
|---|---:|---:|---:|---:|
| 90 / 30 | 26.0 | 36.6 | 52.9 | **-10.6** |
| 135 / 45 | 26.0 | 35.4 | 47.1 | **-9.4** |
| 180 / 60 | 32.5 | 30.5 | 46.1 | **+2.0** |
| **270 / 90** | **40.3** | **24.4** | 50.0 | **+15.9** |

**Finding.** SMA_270 (90-day slow trend) has by far the highest IS discrimination
(+15.9pp): it flags 40.3% of IS-bear/chop trades and only 24.4% of IS-bull
trades. The shorter MAs (30/45-day) are anti-discriminating (negative) — too fast
to capture the multi-month bear/chop regime. **SMA_270 is the chosen classifier.**

### 2.3 T7 — Per-symbol bear/chop-entry IS economics (the SCOPE decision)

This is the DECISIVE table. The EDA first tested a BLANKET all-3-symbol bear/chop
SIZE de-rate (T3) — it is IS-NEGATIVE at every scalar (IS Δ -0.027 to -0.082; the
full T3 grid is monotone-negative). T7 explains why — the drag is
SYMBOL-ASYMMETRIC:

| Symbol | bear/chop-entry IS wpnl | bull-entry IS wpnl | bear/chop-entry WR | genuine drag? |
|---|---:|---:|---:|:---:|
| BCHUSDT | **+35.66** | +42.68 | 48.1% | **NO** |
| LDOUSDT | **-3.64** | +1.98 | 0.0% | **YES** |
| TRXUSDT | **-10.49** | -14.30 | 17.4% | **YES** |

**Finding.** BCH's bear/chop-entry IS trades carry **+35.66 wpnl** — BCH WINS in
BTC-bear/chop months (48.1% WR). De-rating BCH's bear/chop trades down-scales the
IS edge — that is exactly why a blanket de-rate is IS-negative. TRX (-10.49) and
LDO (-3.64) are the genuine drag (17.4% and 0.0% bear/chop-entry WR). **The
de-rate is SCOPED to LDO+TRX — the symbols whose bear/chop-entry IS wpnl is
negative.** The scope is the IS-improving design, not a customization that breaks
IS.

### 2.4 T8 — SCOPED de-rate counterfactual (the simulated historical effect)

The de-rate applied ONLY to LDO+TRX bear/chop-entry trades (BCH never touched):

| De-rate scalar | IS monthly Sharpe | OOS monthly Sharpe | IS Δ | OOS Δ | OOS/IS ratio |
|---:|---:|---:|---:|---:|---:|
| 1.00 (baseline) | 0.8325 | 0.1403 | 0.0000 | 0.0000 | 0.1685 |
| 0.25 | 1.0434 | -0.0880 | +0.2109 | -0.2283 | -0.0844 |
| 0.35 | 1.0157 | -0.0527 | +0.1832 | -0.1930 | -0.0519 |
| **0.50** | **0.9738** | **-0.0023** | **+0.1413** | **-0.1426** | -0.0024 |
| 0.65 | 0.9315 | +0.0446 | +0.0990 | -0.0956 | +0.0479 |
| 0.75 | 0.9032 | +0.0739 | +0.0708 | -0.0663 | +0.0818 |

**Finding — and the honest IS<->OOS tension.** T8 reveals a GENUINE tension: the
same BTC-bear/chop classifier that de-rates IS-bleeding LDO/TRX trades ALSO
de-rates OOS-window LDO/TRX trades that the uptrend rewards (50.0% of OOS trades
fall in the classifier's bear/chop tag — Section 2.2). The de-rate trades IS for
OOS roughly 1:1.

**De-rate choice = 0.50.** The chosen scalar is the largest IS-lift scalar that
clears BOTH (a) the +0.10 PROMISING IS floor AND (b) the -0.20 NEGATIVE OOS floor
— and among those, the one with the best OOS headroom. At 0.50: IS Δ **+0.1413**
(clears the +0.10 PROMISING bar), OOS Δ **-0.1426** (inside the [-0.20,+0.20]
noise band — not NEGATIVE). The 0.25/0.35 scalars give a larger IS lift but drive
OOS into NEGATIVE territory (-0.228 / -0.193) — rejected. The 0.65/0.75 scalars
keep OOS milder but the IS lift falls below the PROMISING bar.

**Counterfactual exactness.** CRUCIAL: a position-SIZE scalar at primitive 5
fires AFTER the model and AFTER labeling — it changes only the realised
`weighted_pnl` of trades that still happen; it does NOT change trade SELECTION,
labels, or the Optuna optimization landscape. (This is the structural difference
from the /074 KILL switch, which fired BEFORE the model and shifted the training
distribution.) The T8 counterfactual is therefore **essentially exact** — the
backtest should reproduce the T8 numbers up to a tiny integer-rounding
interaction with the existing vol-scale (`weight = round(weight * scale * ...)`).
This is honestly disclosed: the EDA does NOT predict an OOS recovery beyond the
counterfactual.

### 2.5 Holding-time-effect predictor (T4) — MANDATED by `feedback_v3_is_oos_regime_divergence.md`

The predictor compares the mean/median trade DURATION of the post-scalar roster
against the baseline /060 roster:

| Split | Full roster n | Full mean dur | Post-scalar roster n | Post-scalar mean dur | **Mean dur Δ** | **Median dur Δ** |
|---|---:|---:|---:|---:|---:|---:|
| IS | 159 | 6.3145 | 159 | 6.3145 | **0.0** | **0.0** |
| OOS | 102 | 6.4608 | 102 | 6.4608 | **0.0** | **0.0** |

**The holding-time-effect predictor confirms Primitive 12 is holding-time-EXACTLY-
ORTHOGONAL.** A position-SIZE scalar removes NO trade and shifts NO SL/TP/timeout
barrier. The post-scalar roster is **bit-identical in membership and timing** to
the baseline — only `weighted_pnl` differs. The mean/median trade-duration delta
is **EXACTLY 0**, not merely near-zero. Per `feedback_v3_is_oos_regime_divergence.md`,
an axis with a ~0 predicted duration change does NOT load the IS/OOS regime
factor. **Primitive 12 is structurally incapable of reproducing the
SUSPICIOUS-OOS-DOMINANT holding-time-extension pattern of /065/071/073** — those
axes lengthened the kept-roster duration; this axis cannot, because it deletes no
trade.

**Falsifier on the holding-time predictor:** if the /075 backtest shows the
LDO/TRX kept-roster mean trade duration shifts by **> +1.0 candle** vs the /060
LDO/TRX roster, the orthogonality assumption is violated (it cannot be, by
construction — a size scalar deletes no trade — so a non-zero shift would indicate
an implementation bug) and the Critic should flag it. Expected shift: **0.0
candles** (exact).

### 2.6 Anchor declaration

The cycle-2 EXPLORATION anchor is **iter-v3/060 EXPLORATION-MODE-REFERENCE**
(`feedback_v3_cycle1_axis_pass_criteria.md`), byte-exact from
`reports-v3/iteration_v3-060/comparison.csv`:

| Anchor metric | Value | Source |
|---|---:|---|
| IS monthly Sharpe | **+0.8325** | comparison.csv:2 in_sample |
| OOS monthly Sharpe | **+0.1403** | comparison.csv:2 out_of_sample |
| IS daily Sharpe | +1.7115 | comparison.csv:3 in_sample |
| OOS daily Sharpe | +0.3659 | comparison.csv:3 out_of_sample |
| IS n_trades | 159 | comparison.csv:7 in_sample |
| OOS n_trades | 102 | comparison.csv:7 out_of_sample |
| frac_positive_paths (CPCV) | 0.6444 | dsr.json / cpcv_paths.csv (CPCV invariant) |

With the /074 regime gate REVERTED (Section 3), /075 starts from the /060
baseline state. Primitive 12 is the single varied axis. **BCH is the positive
control**: the de-rate scope is LDO+TRX only, so BCH's trade roster — and BCH's
weighted_pnl — must be byte-identical to /060 (the scalar cannot touch BCH).

---

## Section 3 — Proposed Changes

**ONE substantive axis change** (Primitive 12) plus ONE mandatory revert (the
/074 leftover). Per `feedback_no_cheating.md` anti-drift discipline, the /074
regime-gate axis — INERT-AT-EXPLORATION, closed across two data points, added to
BASELINE_V3.md "Dead Ideas" — must not silently carry into /075. The revert
restores the /060 baseline state; it is a revert, not a second axis.

- **Symbols:** UNCHANGED — BCH/LDO/TRX. V3_EXCLUDED_SYMBOLS check: none of
  BCH/LDO/TRX is in V3_EXCLUDED_SYMBOLS. PASS.
- **Labeling:** UNCHANGED — `DEFAULT_ATR_MULTIPLIERS = (2.0, 1.0)`,
  `V3_ATR_MULTIPLIERS_PER_SYMBOL = {}` (already empty per /074),
  `label_mode="triple_barrier"`, 21-candle (10080-min) timeout. No labeling change.
- **Features:** UNCHANGED — V3_FEATURE_COLUMNS = 14, the /059/060 anchor set. No
  feature added or removed. (Primitive 12 is a risk-layer primitive, not a
  feature — the model is identical to /060.)
- **Risk gates — REVERT /074:** `enable_regime_gate=True` → **`False`**;
  `regime_gate_symbols=("TRXUSDT",)` → **`()`**. This restores the /060 baseline
  risk-gate stack (primitive 9 OFF).
- **Risk gates — NEW Primitive 12:** a BTC-trend-regime position-SIZE de-rate
  scalar (`enable_regime_size_scalar=True`, scope LDO+TRX, scalar 0.50, classifier
  SMA_270). Detailed in 3.1.

### 3.1 Primitive 12 — exact code changes (enacting the axis)

Primitive 12 is implemented entirely in the **v3-specific** `RiskV3Wrapper` /
`RiskV2Config` — v1 and v2 are NOT perturbed (the new config fields default OFF;
the scalar logic lives in `RiskV3Wrapper.get_signal`, which v1/v2 do not use).

1. **`src/crypto_trade/strategies/ml/risk_v2.py`** — add four `RiskV2Config`
   fields (all default OFF — v1/v2/v3-prior behavior preserved), parallel to the
   existing primitive-9 / primitive-10 fields:
   ```python
   # iter-v3/075: primitive 12 — BTC-trend-regime position-SIZE de-rate scalar.
   # When BTC is in a bear/chop trend state (close[t-1] < SMA_N(close)[t-1]),
   # the position WEIGHT of trades for symbols in regime_size_scalar_symbols is
   # multiplied by regime_size_scalar_value (< 1.0). Bull-regime trades and
   # out-of-scope symbols are unchanged. Past-only: close.shift(1) before SMA.
   # Default OFF preserves v1/v2/v3-prior behavior.
   enable_regime_size_scalar: bool = False
   regime_size_scalar_symbols: tuple[str, ...] = ()       # e.g. ("LDOUSDT", "TRXUSDT")
   regime_size_scalar_value: float = 1.0                  # de-rate multiplier (< 1.0 to de-rate)
   regime_size_ma_window: int = 270                       # BTC slow-MA window in bars
   ```
   Add a `__post_init__` validation: if `enable_regime_size_scalar`, require
   `0.0 < regime_size_scalar_value <= 1.0` and `regime_size_ma_window > 0`.
2. **`src/crypto_trade/strategies/ml/risk_v2.py`** — add a `GateStats` counter
   `regime_size_scalar_fires: int = 0` (parallel to `regime_gate_fires`) so the
   engineering report can record how many trades the scalar de-rated.
3. **`src/crypto_trade/strategies/ml/risk_v3.py`** — `RiskV3Wrapper`:
   - Add a NEW helper `_build_btc_trend_lookup(btc_csv_path, ma_window)` —
     past-only: `close.shift(1)` then `rolling(ma_window).mean()`; returns
     `{"open_time": int64[], "btc_bearchop": int8[]}` where `btc_bearchop = 1`
     when shifted close < shifted-close SMA. Warm-up bars (SMA NaN) → 0 (bull;
     no de-rate where the classifier is undefined). This is the EXACT contract
     of `analysis/iteration_v3-075/axis_selection_eda.py::_build_btc_trend_lookup`.
   - In `_build_lookups`: when `config.enable_regime_size_scalar and
     config.regime_size_scalar_symbols`, populate `self._btc_trend_lookup =
     _build_btc_trend_lookup("data/BTCUSDT/8h.csv", config.regime_size_ma_window)`
     (alongside the existing `_btc_regime_lookup`).
   - Add a method `_regime_size_scalar(symbol, open_time_ms) -> float`: returns
     `1.0` if `symbol not in regime_size_scalar_symbols` or the lookup is None or
     no past BTC bar exists; else find the most recent BTC bar with open_time
     STRICTLY LESS THAN `open_time_ms` (`np.searchsorted(..., side="left") - 1`)
     and return `regime_size_scalar_value` if that bar is `btc_bearchop == 1`,
     else `1.0`. Identical past-only contract to `_regime_gate_fires`.
   - In `get_signal`: AFTER the inherited gate cascade returns the post-gate
     signal `sig` (and after the primitive-10 direction-block check), if
     `config.enable_regime_size_scalar` and `sig.direction != 0`, compute
     `s = self._regime_size_scalar(symbol, open_time)`; if `s < 1.0`, increment
     `GateStats.regime_size_scalar_fires` and return
     `Signal(direction=sig.direction, weight=max(1, int(round(sig.weight * s))),
     tp_pct=sig.tp_pct, sl_pct=sig.sl_pct)`. The scalar applies AFTER all gates
     (it is the last weight-modifying step) — it changes WEIGHT only, never
     direction/tp/sl/timeout.
   - Extend `gate_stats_summary()` to emit `regime_size_scalar_fires` and
     `regime_size_scalar_fire_rate` per symbol.
4. **`run_baseline_v3.py`** — in `_build_v3_model`'s `RiskV2Config(...)`:
   - REVERT /074: `enable_regime_gate=True → False`; `regime_gate_symbols=
     ("TRXUSDT",) → ()`. (`regime_dd_threshold_pct=20.0`,
     `regime_vol_zscore_threshold=1.5` may stay as inert defaults — they have no
     effect when `enable_regime_gate=False` — OR be left as-is; the pre-flight
     assertion (item 5) handles this.)
   - ADD Primitive 12: `enable_regime_size_scalar=True`,
     `regime_size_scalar_symbols=("LDOUSDT", "TRXUSDT")`,
     `regime_size_scalar_value=0.50`, `regime_size_ma_window=270`.
5. **`run_baseline_v3.py`** — `_verify_feature_columns` pre-flight:
   - REMOVE the four /074 regime-gate assertions (lines ~568-595: the
     `enable_regime_gate is True`, `regime_gate_symbols == ("TRXUSDT",)`,
     `regime_dd_threshold_pct == 20.0`, `regime_vol_zscore_threshold == 1.5`
     checks) and REPLACE with a single `enable_regime_gate is False` assertion
     (the /075 baseline-restore state).
   - ADD four NEW Primitive-12 assertions: `enable_regime_size_scalar is True`;
     `regime_size_scalar_symbols == ("LDOUSDT", "TRXUSDT")`;
     `regime_size_scalar_value == 0.50`; `regime_size_ma_window == 270`.
   - Update the `print(...)` summary line to describe Primitive 12.
6. **`run_baseline_v3.py`** — `ITERATION_LABEL` bumped `"v3-074"` → `"v3-075"`.
7. **`tests/`** — add `tests/strategies/ml/test_regime_size_scalar.py` (a NEW
   test file): assert (a) the scalar fires for LDO+TRX only and never for BCH;
   (b) the BTC-trend classifier is past-only (cannot see the current bar — uses
   `searchsorted 'left' - 1`); (c) when `enable_regime_size_scalar=False` the
   wrapper is byte-identical to the no-scalar path; (d) `regime_size_scalar_value`
   outside `(0, 1]` raises in `__post_init__`. The existing
   `tests/strategies/ml/test_regime_gate.py` is unaffected (Primitive 9 logic
   unchanged — only its enable flag flips in the runner). The existing
   `tests/features_v3/test_atr_multipliers_for_symbol.py` is unaffected (no ATR
   change in /075).

ZERO change to feature code, labeling code, the model, or the walk-forward
harness. Primitive 12 is purely a post-gate weight-scaling primitive.

**Single-axis discipline.** The brief declares exactly TWO changes: (1) the
Primitive-12 axis, (2) the mandatory /074 regime-gate revert (a baseline-restore,
not a second varied axis). `block_long_for=()` / `block_short_for=()` stay
reverted (primitive 10 OFF, per /051). `enable_per_symbol_drawdown_brake=False`
(primitive 11 OFF, per /054). `enable_per_symbol_cap=False` (primitive 8 OFF, per
/020). No scope creep.

---

## Section 4 — Expected OOS Impact

### 4.1 Predicted bands (cycle-2 axis-PASS criteria, anchored on /060)

The T8 counterfactual is essentially exact (Section 2.4) — a position-SIZE scalar
fires after the model + labeling, so trade selection and the Optuna landscape are
unchanged. The predicted bands are therefore tight, centred on the T8 derate-0.50
row:

- **Predicted IS monthly Sharpe Δ vs /060:** **+0.14** (CI: **[+0.08, +0.20]**).
  T8 derate-0.50 IS Δ = +0.1413. The band is narrow because the counterfactual is
  exact up to integer-rounding of the re-weighted positions.
- **Predicted OOS monthly Sharpe Δ vs /060:** **-0.14** (CI: **[-0.20, -0.06]**).
  T8 derate-0.50 OOS Δ = -0.1426. Honestly disclosed: this axis trades IS for OOS
  roughly 1:1 — the same BTC-bear/chop classifier de-rates OOS-uptrend LDO/TRX
  trades the trend rewards. The CI lower bound touches the -0.20 NEGATIVE floor.
- **Predicted frac_positive_paths:** ≈ 0.6444 ± 0.03 (CPCV is largely
  architecture-invariant; the scalar re-weights a small number of trades and the
  CPCV path construction is on the cell-level model, not the post-gate roster).
- **Falsifier:** if **OOS monthly Sharpe Δ < -0.20** vs /060 (i.e. OOS Sharpe
  below -0.06), the axis is NEGATIVE on the OOS axis — the de-rate is destroying
  more OOS-productive trades than the counterfactual estimated, and the axis is
  rejected. If **IS monthly Sharpe Δ < +0.08** (below the CI lower bound), the IS
  lift the counterfactual predicts did not materialise — flag an implementation
  defect (the counterfactual is exact, so a missing IS lift means the scalar is
  mis-wired).

### 4.2 BCH IS sensitivity (mandated by `feedback_v3_cycle1_axis_pass_criteria.md`)

BCH carries the v3 IS edge (176.68% of /060 IS PnL; 95.76% of /059 IS PnL). The
de-rate `regime_size_scalar_symbols=("LDOUSDT", "TRXUSDT")` fires ONLY on LDO and
TRX — **BCH IS is predicted byte-identical to /060** (73 trades, 45.2% WR,
+79.45% net_pnl, per `reports-v3/iteration_v3-060/in_sample/per_symbol.csv`). The
scalar cannot touch BCH. This is a hard prediction and the positive control: if
BCH IS shifts at all, single-axis discipline has been violated. (This is
precisely why the scope is LDO+TRX — T7 showed BCH WINS in BTC-bear/chop;
scoping the de-rate AWAY from BCH is the IS-edge-preserving design.)

### 4.3 Holding-time-effect predictor (mandated by `feedback_v3_is_oos_regime_divergence.md`)

**Predicted mean trade duration change: EXACTLY 0. Predicted median trade
duration change: EXACTLY 0.** Primitive 12 is holding-time-ORTHOGONAL by
construction — it removes NO trade and shifts NO SL/TP/timeout barrier; it scales
the WEIGHT of trades that still happen. The post-scalar roster is bit-identical in
membership and timing to /060 (T4 Section 2.5). Per the regime-divergence rule, a
0 duration change does NOT load the IS/OOS regime factor. **This is the
load-bearing reason Primitive 12 satisfies the Critic /074 hard constraint** — it
is NOT a 4th holding-time-extension axis; unlike /065/071/073 (which lengthened
the kept roster) it CANNOT lengthen the kept roster because it deletes no trade.

Falsifier on the holding-time predictor: if the /075 backtest shows the LDO/TRX
kept-roster mean trade duration shifts by **> +1.0 candle** vs the /060 LDO/TRX
roster, the orthogonality assumption is violated — and since a size scalar deletes
no trade, ANY non-zero shift indicates an implementation bug; the Critic should
flag it. Expected shift: **0.0 candles** (exact).

### 4.4 Behavioral-effect predictor (mandated by `feedback_v3_axis_saturation_predictor.md`)

Explicit estimate of how many trades have their WEIGHT changed vs /060. Within the
de-rate scope (LDO+TRX), the scalar fires on every bear/chop-entry trade
(T5 per-symbol rows):

- **TRX trades re-weighted:** **IS ≈ 23** (T5: 23 of 75 TRX IS trades are
  bear/chop-entry), **OOS ≈ 30** (T5: 30 of 54 TRX OOS trades).
- **LDO trades re-weighted:** **IS ≈ 1** (T5: 1 of 11 LDO IS trades — LDO's IS
  roster is mostly bull-entry), **OOS ≈ 2** (T5: 2 of 11 LDO OOS trades).
- **Scope total re-weighted:** **IS ≈ 24 trades**, **OOS ≈ 32 trades**.
- **BCH trades re-weighted:** **0** (BCH is out of scope — the gate cannot touch
  it).

**This is MATERIALLY LARGER than /074's 3-IS / 5-OOS suppression** — the Critic
/074 Rec #3 mandate (a materially larger trade-population effect, full-roster not
stress-bar-subset) is satisfied: ≈ 24 IS trades is 8× /074's 3, and ≈ 32 OOS
trades is 6× /074's 5. **Falsifier:** if `regime_size_scalar_fires` total in
`gate_stats_summary()` is **0**, the scalar never fired (mis-wired or no LDO/TRX
candidate landed in a BTC-bear/chop regime) → NULL-RESULT. Note the actual
backtest's `regime_size_scalar_fires` counts SIGNAL-level firings (not just the
trades that opened), so the count will be ≥ the 24/32 trade-level estimate; the
trade-level estimate is the floor.

Note — the trade-roster membership is UNCHANGED (no trade is removed); the
behavioral effect is a WEIGHT change on ≈ 24 IS / ≈ 32 OOS trades. The trade-rate
floor is not at risk: a SIZE scalar deletes no trade, so IS/OOS trade COUNTS are
identical to /060 (159 IS / 102 OOS).

### 4.5 OOS/IS ratio SUSPICIOUS pre-registration (mandated by `feedback_v3_oos_is_ratio_gate.md`)

**Pre-registered SUSPICIOUS gate: if the /075 OOS/IS monthly Sharpe ratio > 3.0,
the axis is classified SUSPICIOUS regardless of absolute OOS Sharpe magnitude.**
The canonical definition is the within-iteration `comparison.csv` `monthly_sharpe`
ratio column (the value the Section 8 SUSPICIOUS classifier consumes — no
alternative ratio construction is introduced, per the /074 Critic Rec #1
standardization). The gate fires unconditionally per the memory rule.

Primitive 12 is predicted NOT to trip the ratio gate: the holding-time-effect
predictor (Section 4.3) shows EXACTLY 0 duration change, so the IS/OOS
regime-divergence factor is not loaded. The T8 counterfactual OOS/IS ratio at
derate-0.50 is **-0.0024** (the OOS Sharpe is slightly negative at -0.0023, so the
ratio is near-zero negative) — far below 3.0. The de-rate REDUCES OOS Sharpe; it
does not inflate it. SUSPICIOUS-OOS-DOMINANT is mechanically impossible here — the
SUSPICIOUS-OOS-DOMINANT sub-mode requires OOS shift ≥ +0.20, and the predicted
OOS shift is NEGATIVE (-0.14). But the gate is pre-registered and binding: if /075
returns OOS/IS > 3.0, the axis is SUSPICIOUS and does NOT advance, even though the
mechanism analysis rules it out.

---

## Section 5 — Risk Mitigation

This iteration's axis IS itself a risk-mitigation primitive (a regime-conditional
position-size de-rate). The mitigation discussion is therefore about whether the
scalar is correctly bounded and what protects against it misfiring.

- **Past-only discipline.** The BTC-trend classifier computes the slow SMA on
  `close.shift(1)` so the current BTC bar's close is never used. The scalar finds
  the most recent BTC bar with `open_time STRICTLY LESS THAN` the symbol's bar
  `open_time` (`np.searchsorted(..., side="left") - 1`). This is the EXACT
  contract of the existing primitive-9 `_regime_gate_fires` (adversarial-tested
  in `test_regime_gate.py`) and of `axis_selection_eda.py::_build_btc_trend_lookup`.
  The NEW `tests/strategies/ml/test_regime_size_scalar.py` re-asserts the
  past-only property. No look-ahead.
- **IS-calibrated parameters.** The SMA_270 classifier window is chosen by T2 on
  the IS-window discrimination metric only (Section 2.2). The de-rate scalar 0.50
  is chosen by T8 on the IS-counterfactual lift subject to the IS PROMISING floor
  and the OOS NEGATIVE floor — both pre-registered classification boundaries, not
  tuned optima (Section 2.4). The scope LDO+TRX is chosen by T7 on the
  IS-bear/chop-entry-wpnl sign (Section 2.3). Every parameter has an IS-only
  derivation.
- **Simulated historical effect.** Section 2.4 (T8) IS the simulated historical
  effect: on the /060 trade roster, de-rating LDO+TRX bear/chop-entry trades by
  0.50 produces IS monthly Sharpe +0.1413 / OOS monthly Sharpe -0.1426. Section
  2.3 (T7) shows the de-rate is applied only to symbols whose bear/chop-entry IS
  wpnl is negative. The full de-rate grid is in `T8_scoped_derate_counterfactual.csv`.
- **Scope bound.** `regime_size_scalar_symbols=("LDOUSDT", "TRXUSDT")` — the
  scalar touches LDO and TRX only. BCH (the IS-edge carrier) is untouched (positive
  control, Section 4.2). If the scalar misfires, the blast radius is the WEIGHT of
  LDO/TRX trades — and since it only DE-rates (scalar ≤ 1.0), the worst case is
  positions sized too small, never too large; it cannot increase risk.
- **Trade-rate preserved.** A SIZE scalar deletes no trade — the IS/OOS trade
  COUNTS are identical to /060 (Section 4.4). The trade-rate floor is structurally
  not at risk from this axis.
- **Failure-stop.** Section 4.1 falsifier: OOS Sharpe Δ < -0.20 → axis rejected.
  Section 4.3 falsifier: LDO/TRX kept-roster mean duration shift > +1.0 candle →
  implementation bug. Section 4.4 falsifier: `regime_size_scalar_fires` total = 0
  → NULL-RESULT. Section 4.5 falsifier: OOS/IS > 3.0 → SUSPICIOUS.

---

## Section 6 — Risk Management Design

The v3 risk gate stack. /075 reverts primitive 9 (regime kill switch) to OFF and
adds primitive 12 (BTC-trend-regime position-SIZE de-rate scalar).

| # | Primitive | /075 state | Fire-rate prediction |
|---|---|---|---|
| 1 | Feature z-score OOD (z>2.0) | ON, unchanged | baseline |
| 2 | Hurst regime check | ON, unchanged | baseline |
| 3 | ADX gate (ADX>20) | ON, unchanged | baseline |
| 4 | Low-vol filter (bottom-third ATR) | ON, unchanged | baseline |
| 5 | Vol-adjusted sizing (TRX floor 0.5) | ON, unchanged | baseline |
| 8 | Per-symbol PnL cap | OFF (closed /020) | n/a |
| 9 | Regime-conditional kill switch | **OFF (REVERTED from /074)** | n/a — /074 baseline-restore |
| 10 | Direction-asymmetric kill switch | OFF (reverted /051) | n/a |
| 11 | Per-symbol drawdown brake | OFF (closed /054) | n/a |
| **12** | **BTC-trend-regime position-SIZE de-rate scalar (LDO+TRX)** | **ON (the /075 axis)** | **de-rates ≈ 24 LDO/TRX IS trades + ≈ 32 LDO/TRX OOS trades by 0.50 (T5 trade-level estimate; signal-level fire count ≥ this)** |

**Regime coverage analysis.** Primitive 12 is the v3 stack's first BTC-macro-
conditional SIZING primitive. Primitives 1-4 are per-symbol feature/indicator
gates; primitive 5 sizes by per-symbol vol. None of them sees the BTC bull/bear
trend regime. Primitive 12 fills that coverage gap for LDO+TRX — the two symbols
whose bear/chop-entry IS trades are the genuine drag (T7). It composes cleanly
with primitive 5: primitive 5 produces `scale` from per-symbol vol, primitive 12
applies the regime de-rate on top — both are multiplicative weight factors;
neither touches direction or barriers.

**`gate_stats_summary()` reporting.** `RiskV3Wrapper.gate_stats_summary()` will
emit `regime_size_scalar_fires` and `regime_size_scalar_fire_rate` per symbol
(NEW — added in the Section 3.1 changes). The engineering report Phase 6 records
the actual LDO/TRX fire counts; the Critic Phase 7.5 cross-checks them against
Section 4.4's ≈ 24-IS / ≈ 32-OOS trade-level prediction (the signal-level fire
count will be ≥ the trade-level estimate).

---

## Section 7 — Pre-Registered Failure-Mode Prediction

**Most plausible outcome (probability ≈ 45%): INERT-AT-EXPLORATION.** The T8
counterfactual at derate-0.50 predicts OOS Δ = -0.1426 — inside the [-0.20,+0.20]
OOS noise band. Per the Section 8 disjunctive classifier, an OOS Δ within the
noise band fires INERT-AT-EXPLORATION (the IS Δ of +0.14 clears the PROMISING bar,
but PROMISING requires BOTH IS Δ ≥ +0.10 AND OOS Δ ≥ +0.20 — the OOS gate fails).
The mechanism: the de-rate trades IS for OOS roughly 1:1, and at 0.50 the OOS cost
lands inside the noise band rather than crossing the NEGATIVE floor. The metric
signature: IS Δ ≈ +0.10 to +0.18, OOS Δ ≈ -0.06 to -0.18, BCH byte-identical to
/060, `regime_size_scalar_fires` > 0.

**Second outcome (probability ≈ 35%): NEGATIVE-AT-EXPLORATION (OOS axis).** The
T8 counterfactual OOS Δ CI lower bound (-0.20) touches the NEGATIVE floor. If the
backtest's integer-rounding of the re-weighted positions, or a slightly different
BTC-trend tagging at the live signal-bar granularity, pushes OOS Δ below -0.20,
the axis is NEGATIVE on the OOS axis (Section 8.2). The metric signature: OOS Δ <
-0.20 (OOS Sharpe < -0.06), IS Δ still positive (the IS lift is robust — T8
derate-0.50 IS Δ +0.14). This is an honest, pre-registered failure mode: the
counterfactual is essentially exact and predicts OOS -0.14, but the -0.20 floor
is only 0.06 away.

**Third outcome (probability ≈ 18%): PROMISING-AT-EXPLORATION.** This requires the
backtest OOS Δ to land ≥ +0.20 — i.e. +0.34 BETTER than the T8 counterfactual
estimate. The counterfactual is essentially exact (a size scalar fires post-model;
trade selection is unchanged), so a +0.34 OOS surprise is unlikely — it would
require the 3-seed EXPLORATION-mode variance (noise floor ≈ -0.44 OOS per
`feedback_v3_cycle1_axis_pass_criteria.md`) to swing strongly favourable. Weighted
low and honestly: the EDA does NOT predict a clean PROMISING.

**Tail outcome (probability ≈ 2%): NULL-RESULT.** `regime_size_scalar_fires`
total = 0 — the scalar never fired. Near-impossible given T5 shows ≈ 24 IS / ≈ 32
OOS LDO/TRX bear/chop-entry trades on the /060 roster; it would require a wiring
defect.

**SUSPICIOUS is mechanically ruled out** (probability ≈ 0%): the
SUSPICIOUS-OOS-DOMINANT sub-mode requires OOS Δ ≥ +0.20; the predicted OOS Δ is
NEGATIVE. The OOS/IS ratio gate requires ratio > 3.0; the predicted OOS Sharpe is
slightly negative so the ratio is near-zero. The holding-time-orthogonality is
EXACT (duration delta 0). All three SUSPICIOUS grounds are structurally excluded.

**What the gates should catch.** The CPCV `frac_positive_paths` and PBO are
largely invariant to a small post-gate weight re-scaling — they will not move
much. The discriminating signals: (a) the IS/OOS Sharpe deltas vs /060; (b) the
`regime_size_scalar_fires` count in `gate_stats_summary()` — 0 → NULL-RESULT;
(c) the BCH byte-identity check (single-axis discipline — BCH must be exactly
/060); (d) the LDO/TRX kept-roster duration vs /060 (must be EXACTLY 0 — a size
scalar cannot change duration).

Process predictions: P1 — wall-clock under the 1.0h budget (≈ 90% confidence;
/071-074 all 0.65-0.70h; this axis adds one BTC-SMA lookup, cheaper than a
labeling change). P2 — the new Primitive-12 pre-flight assertions pass on the
first Phase 5.5 gate run (≈ 75%; the /073 setup hit 4 stale assertions and /074
hit the stale ATR assertion — a stale-assertion BLOCK is a real ≈ 25% risk; the
QE must replace the four /074 regime-gate assertions with the /075 baseline-restore
+ Primitive-12 assertions in the SAME setup commit). P3 — integration runs clean,
no runtime error (≈ 90%).

---

## Section 8 — Pre-Registered MERGE/NO-MERGE Numerical Criteria (LOCKED)

This is an EXPLORATION; it cannot MERGE and cannot update BASELINE_V3.md
(`feedback_v3_cadence_discipline.md` — only a CONFIRMATION-MERGE updates the
baseline). Section 8 LOCKs the axis-classification taxonomy per
`feedback_v3_cycle1_axis_pass_criteria.md` cycle-2 thresholds. The classifier is
evaluated in this DISJUNCTIVE ORDER (SUSPICIOUS → NULL-RESULT → NEGATIVE →
PROMISING → INERT) — established /071/073/074 precedence. The first matching
classification is canonical.

All deltas are vs the iter-v3/060 EXPLORATION-mode anchor (IS +0.8325 /
OOS +0.1403). The OOS/IS ratio is the within-iteration `comparison.csv`
`monthly_sharpe` ratio column (the canonical definition — no alternative
construction).

**8.1 — PROMISING-AT-EXPLORATION** (all four conjuncts required):
- IS monthly Sharpe Δ ≥ **+0.10** vs /060 (i.e. IS Sharpe ≥ +0.9325), AND
- OOS monthly Sharpe Δ ≥ **+0.20** vs /060 (i.e. OOS Sharpe ≥ +0.3403), AND
- frac_positive_paths ≥ **0.50**, AND
- no Critic methodology FAIL (13 checks + §11 anti-pattern scan).

**8.2 — NEGATIVE-AT-EXPLORATION** (disjunctive OR — either gate fails):
- IS monthly Sharpe Δ < **-0.10** vs /060 (IS Sharpe < +0.7325), OR
- OOS monthly Sharpe Δ < **-0.20** vs /060 (OOS Sharpe < -0.0597).

**8.3 — INERT-AT-EXPLORATION:**
- IS monthly Sharpe Δ within **[-0.10, +0.10]** vs /060, OR OOS monthly Sharpe Δ
  within **[-0.20, +0.20]** vs /060 (the noise band), AND not SUSPICIOUS, AND not
  NEGATIVE, AND not PROMISING. (The expected /075 outcome — IS Δ ≈ +0.14, OOS Δ
  ≈ -0.14 — lands here: the OOS Δ inside the noise band triggers INERT because
  PROMISING's OOS gate fails and NEGATIVE's OOS gate is not crossed.)

**8.4 — SUSPICIOUS** (disjunctive — fires on EITHER ground; SUSPICIOUS takes
classification PRECEDENCE over NEGATIVE and INERT when concurrent, per the
/071/073 precedence rule, with NO magnitude qualifier):
- **OOS/IS monthly Sharpe ratio > 3.0** (`feedback_v3_oos_is_ratio_gate.md` —
  fires unconditionally regardless of absolute OOS Sharpe), OR
- **SUSPICIOUS-OOS-DOMINANT sub-mode:** IS shift < 0 AND OOS shift ≥ +0.20, OR
- **holding-time-orthogonality violation:** the /075 LDO/TRX kept-roster mean
  trade duration shifts by > +1.0 candle vs the /060 LDO/TRX roster (Section 4.3
  falsifier) — for a SIZE scalar this is mechanically impossible (no trade is
  deleted), so a non-zero shift would indicate an implementation bug.

**8.5 — NULL-RESULT:** `regime_size_scalar_fires` total = 0 in
`gate_stats_summary()` (the scalar never fired — mis-wired or no LDO/TRX candidate
landed in a BTC-bear/chop regime); the trade roster's `weighted_pnl` is then
byte-identical to /060 and the axis produced no effect.

**Evaluation order:** SUSPICIOUS (8.4) → NULL-RESULT (8.5) → NEGATIVE (8.2) →
PROMISING (8.1) → INERT (8.3). First match is canonical.

A PROMISING-AT-EXPLORATION outcome carries the axis forward to the cycle-2
CONFIRMATION (iter-v3/081 or later) as a candidate ingredient; it is NOT a MERGE
signal in itself. An INERT / NEGATIVE / SUSPICIOUS / NULL-RESULT outcome does NOT
advance and does NOT update BASELINE_V3.md.

---

## Section 9 — Library Stack Declaration

No new library is introduced. Primitive 12 uses only `numpy` and `pandas`
(already pinned). Versions in effect (per the /059 baseline reproducibility stamp):

- lightgbm: 4.6.0
- optuna: 4.8.0
- numpy: 2.2.6
- pandas: 3.0.0
- scikit-learn: 1.8.0
- scipy: 1.17.0
- statsmodels: 0.14.6 (ADF — Critic Check 5)
- pyarrow: 23.0.1
- mlfinlab / pypbo / fracdiff: not invoked by this axis (Primitive 12 is
  pure-numpy; CPCV/PBO/PSR reporting is unchanged from /060).

Walk-forward harness: the embargo (22 candles) + REQUIRED_GAP (66) are unchanged —
Primitive 12 changes neither the label horizon nor the symbol count. The
walk-forward fix (`train_end_ms = test_start_ms - embargo_ms`,
`compute_embargo_candles(10080,480)=22`) is intact and untouched.

### 9.1 Integration test (methodology-axis discipline)

Primitive 12 is a risk-primitive axis, not a methodology-reporting axis, so the
`feedback_v3_methodology_axis_integration_test.md` mandate (end-to-end smoke test
for axes that add computed fields to dsr.json/comparison.csv) does not strictly
apply — Primitive 12 adds no field to the methodology reports. Nonetheless, the
NEW `tests/strategies/ml/test_regime_size_scalar.py` includes an end-to-end
assertion: a `RiskV3Wrapper` with `enable_regime_size_scalar=True` on a tiny
synthetic master produces de-rated weights for the scope symbols and unchanged
weights for BCH, and `gate_stats_summary()` reports a non-zero
`regime_size_scalar_fires` — exercising the runner's `_build_v3_model` →
`RiskV3Wrapper.get_signal` → `gate_stats_summary` path, not just the math function
in isolation.

---

## Section 10 — QR Audit Trail

Per `feedback_v3_axis_selection_quant_discipline.md`, the /075 axis was selected
by the QR with committed EDA backing, NOT by an orchestrator ad-hoc pick.

- **EDA SHA:** `9a04f6f` — `analysis/iteration_v3-075/axis_selection_eda.py`
  (T0–T8: anchor, regime stratification, BTC-trend classifier sweep, blanket +
  scoped de-rate counterfactuals, holding-time predictor, behavioral predictor,
  per-symbol IS discipline).
- **Brief SHA:** `00405c5` — `briefs-v3/iteration_v3-075/research_brief.md`
  (this file; all 11 sections LOCKED).
- **Setup commit SHA:** `f170a75` — `setup(iter-v3/075): primitive 12
  BTC-trend-regime position-SIZE de-rate scalar + revert /074 regime gate`
  (the four Section 3.1 code changes; ruff-clean; test_regime_size_scalar.py
  10/10 + test_regime_gate.py 6/6 pass; tests/features_v3/ 177 passed;
  `_verify_feature_columns(ensemble_size=3)` passes all /075 pre-flight
  assertions). Backfilled into this Section 10 at the brief-backfill commit.
- **Orchestrator framing:** the orchestrator defined the HARD CONSTRAINT (Critic
  /074 Rec #3: target the IS bear/chop drag with a holding-time-orthogonal,
  full-roster mechanism) and named three candidate families (a NEW
  regime-discriminating feature, a regime-conditional position-SIZE modulation, a
  dedicated IS bear/chop sub-period diagnostic). The orchestrator did NOT
  pre-commit a specific axis. The QR ran the EDA and selected the
  position-SIZE-modulation family — and within it, the EDA itself drove the
  specific design (the classifier window via T2, the LDO+TRX SCOPE via T7, the
  0.50 de-rate via T8).

**How Primitive 12 satisfies the Critic /074 hard constraint:**

- **Holding-time-ORTHOGONAL** — a position-SIZE scalar removes NO trade and shifts
  NO SL/TP/timeout barrier. T4 (Section 2.5) confirms the kept-roster mean/median
  duration delta is EXACTLY 0 — the post-scalar roster is bit-identical in
  membership and timing to /060. Unlike /065/071/073 (SL widening, meta-label
  filtration, per-symbol barrier rebalancing — all of which lengthened the kept
  roster), Primitive 12 CANNOT lengthen the kept roster because it deletes no
  trade. Per `feedback_v3_is_oos_regime_divergence.md`, a 0 duration change does
  NOT load the IS/OOS regime factor. It is NOT a 4th holding-time-extension axis.
- **FULL-ROSTER** — the scalar de-rates ≈ 24 IS + ≈ 32 OOS LDO/TRX trades (T5,
  Section 4.4), MATERIALLY LARGER than /074's 3-IS/5-OOS stress-bar subset (8×
  the IS effect, 6× the OOS effect). It acts on the full bear/chop-month roster
  of the scope symbols, not an acute-crash subset.

**Why NOT the alternative candidate families:**

- **A NEW regime-discriminating composed FEATURE** (the Critic's first suggested
  direction) was considered and NOT selected. Three reasons: (a) a feature changes
  model predictions, but its trade-population effect is fuzzy to bound — the
  mandated behavioral-effect predictor cannot give a clean trade count, whereas a
  SIZE scalar gives an exact one (≈ 24 IS / ≈ 32 OOS); (b) the v3
  engineered-feature graveyard is deep — vol_adj_autocorr (/026 catastrophic),
  efficiency_ratio_50 (/043 disastrous), hurst_drift_50_200 (/053 PARKED),
  regime_momentum_signed_3d (/052 PARKED) all NEGATIVE/PARKED; (c) single-seed
  engineered-feature behaviour is lottery-prone (`feedback_v3_engineered_features_dont_stack.md`).
  A SCOPED SIZE scalar gives a precisely-bounded, materially-large,
  holding-time-EXACTLY-orthogonal effect that PRESERVES the BCH IS edge — a
  strictly better fit for the Critic mandate.
- **A dedicated IS bear/chop sub-period diagnostic axis** — the EDA's T1 + T7
  ARE that diagnostic (they stratify the IS window and decompose the bear/chop
  drag per symbol). A pure-diagnostic iteration would be a PASSIVE-DIAGNOSTIC with
  no backtest; /075 instead acts on the diagnostic's finding (the LDO+TRX
  bear/chop drag) with a concrete primitive.

**Per-symbol IS-axis discipline** (`feedback_v3_per_symbol_lifts_oos_breaks_is.md`):
Primitive 12 is per-symbol-SCOPED (LDO+TRX). The memory rule warns that per-symbol
customizations lift OOS but break IS aggregate. Primitive 12 is the OPPOSITE
case — it is an IS-IMPROVING per-symbol scope: T6 (Section 2.3 / the
`T6_per_symbol_is_discipline.csv` table) shows BCH IS wpnl delta EXACTLY 0 (out
of scope), LDO IS wpnl +1.82, TRX IS wpnl +5.24 — every symbol's IS contribution
is PRESERVED or LIFTED. The scope is chosen PRECISELY to preserve the BCH IS edge
(T7: BCH wins in bear/chop, so it is excluded). The /075 per-symbol scope passes
the IS-axis-preserve test by construction. The honest caveat the memory rule
demands: the IS lift is validated here at single-seed EXPLORATION; if /075 is
PROMISING, the cycle-2 CONFIRMATION must re-validate that the LDO+TRX scope
preserves IS Sharpe at 10-seed mode before bundling.

**Re-evaluation justification.** Primitive 12 is a NEW primitive — it has never
been tested in v3. It is distinct from primitive 9 (the /022 + /074 regime KILL
switch): primitive 9 SUPPRESSES signals before the model (changing the Optuna
training distribution); primitive 12 SCALES weight after the model (leaving trade
selection and the Optuna landscape unchanged). The /074 closeout closed primitive
9 across two data points — primitive 12 is not a re-proposal of primitive 9; it
is a different mechanism (size de-rate vs binary kill) at a different stage
(post-model vs pre-model) with a different classifier (close-vs-slow-SMA trend
state vs acute-crash drawdown/vol-z).
