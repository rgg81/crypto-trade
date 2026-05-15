# iter-v3/073 — Research Brief

**Track**: v3 | **Cycle**: 2 | **EXPLORATION #3 of 10** | **Date**: 2026-05-15
**Branch**: `iteration-v3/073`
**EDA**: `analysis/iteration_v3-073/axis_selection_eda.py` (committed SHA `b004bc9`)

---

## Section 0 — Data Split Declaration

- **OOS_CUTOFF_DATE = 2025-03-24** (IMMUTABLE sacred constant).
- **training_months = 24** (IMMUTABLE sacred constant).
- IS = `open_time < 2025-03-24`; OOS = `open_time >= 2025-03-24`.
- Universe: BCHUSDT, LDOUSDT, TRXUSDT (V3_MODELS — UNCHANGED this iteration).
- Walk-forward embargo: `compute_embargo_candles(10080, 480) = 22` candles;
  `REQUIRED_GAP = (21+1) * 3 = 66` — UNCHANGED (no universe / timeout change).

## Section 0.5 — Iteration Type Declaration

- **TYPE = EXPLORATION** (cycle 2 #3 of 10).
- **Axis** = per-symbol triple-barrier asymmetry — replace the single GLOBAL ATR
  multiplier pair `(atr_tp=2.0, atr_sl=1.0)` with per-symbol multipliers in
  `V3_ATR_MULTIPLIERS_PER_SYMBOL`, calibrated to each symbol's empirical
  barrier-hit profile. QR-chosen with committed EDA backing per
  `feedback_v3_axis_selection_quant_discipline.md` (see Section 10).
- **Run mode** = `--exploration` (`EXPLORATION_ENSEMBLE_SIZE = 3`,
  `ENSEMBLE_SEEDS[0:3]` outer=42 lineage subset), `--n-trials 35`, `--clean-oof`.
  Total Optuna trials = 35 x 3 syms x 3 seeds = 315.
- **Wall-clock budget** = ≤ 2h (EXPLORATION cap). Projection 0.6–1.0h (the axis
  is a labeling-geometry change with zero new code; runtime ≈ /060/072 profile).

## Section 1 — Testable Hypothesis (ONE sentence)

Replacing the single global ATR multiplier pair `(2.0, 1.0)` — which produces an
SL-saturated training label on every v3 symbol (LONG SL-hit 58–69%) — with
per-symbol multipliers `BCH (2.0, 1.25)` and `LDO (1.5, 1.25)` (TRX unchanged),
calibrated so each symbol's barrier-hit profile is less stop-out-dominated, lifts
the M1 training label's directional economics quality (the realised fee-net PnL
separation between long-labeled and short-labeled bars) and thereby IS monthly
Sharpe ≥ +0.10 AND OOS monthly Sharpe ≥ +0.20 vs the /060 anchor.

## Section 2 — IS-Only Numerical Evidence

All tables produced by `analysis/iteration_v3-073/axis_selection_eda.py`
(committed SHA `b004bc9`), IS-only (`open_time < 2025-03-24`).

### Section 2.1 — T0 Anchor-value declaration (Rule 1 compliance)

Per `feedback_v3_iter064_process_lessons.md` Rule 1, every anchor value below is
byte-exact from `reports-v3/iteration_v3-060/comparison.csv`
(`analysis/iteration_v3-073/T0_anchor_values.csv`):

| Metric | /060 IS | /060 OOS | Source |
|---|---:|---:|---|
| monthly_sharpe | +0.8325 | +0.1403 | comparison.csv:2 |
| daily_sharpe | +1.7115 | +0.3659 | comparison.csv:3 |
| max_drawdown | 31.8701% | 35.7804% | comparison.csv:4 |
| profit_factor | 1.2806 | 1.0482 | comparison.csv:5 |
| win_rate | 31.4465% | 39.2157% | comparison.csv:6 |
| n_trades | 159 | 102 | comparison.csv:7 |
| per_symbol BCH OOS wpnl | — | +1.9078 | comparison.csv:18 |
| per_symbol LDO OOS wpnl | — | -19.7208 | comparison.csv:19 |
| per_symbol TRX OOS wpnl | — | +23.3119 | comparison.csv:20 |

### Section 2.2 — T1: per-symbol barrier-hit profile @ the current global pair

`axisC_barrier_hit_profile.csv` — the single global `(2.0, 1.0)` pair produces an
SL-saturated label on every symbol. The SL barrier is hit far more often than the
TP barrier (`tp_to_sl_ratio < 1` everywhere):

| Symbol | NATR median | LONG TP-hit | LONG SL-hit | LONG timeout | LONG tp/sl | SHORT tp/sl |
|---|---:|---:|---:|---:|---:|---:|
| BCHUSDT | 3.696% | 30.24% | 63.65% | 6.11% | 0.475 | 0.516 |
| **LDOUSDT** | **5.007%** | **27.33%** | **69.14%** | 3.54% | **0.395** | 0.500 |
| TRXUSDT | 2.651% | 34.49% | 58.21% | 7.30% | 0.592 | 0.424 |

LDO is the worst: its LONG label is **69.14% stop-outs** (tp/sl 0.395). This
independently re-confirms the /072 EDA's `axis1_ldo_barrier_diagnosis.csv` (LDO
LONG TP-hit 27.33%, SL-hit 69.14%). The mechanism is geometric: LDO has the
highest 8h NATR (5.01% median vs BCH 3.70%, TRX 2.65%), so the SL at 1xATR (~5%)
is hit by ordinary 8h chop long before the TP at 2xATR (~10%). One global pair
cannot be barrier-balanced for three symbols whose volatility differs ~2x.

### Section 2.3 — T2: per-symbol (tp, sl) grid sweep — THE DECISIVE TABLE

`axisC_multiplier_grid.csv` — 9-cell grid per symbol (TP {1.5, 2.0, 2.5}, SL
{0.75, 1.0, 1.25}). The primary label-economics metric is `directional_spread` =
mean(realised fee-net labeled-direction PnL | label=+1) − mean(... | label=−1) —
a DIRECT economics metric computed on the realised fee-net trade PnL the backtest
books (NOT a label-space-cleanliness proxy; the /072 EDA's misleading
"directional-spread" metric measured label-space separation and Critic /072
Rec #3 flagged it). All 27 grid cells keep label entropy ≥ 0.99 — balance is
never the bottleneck. Current global cell + the eligible per-symbol optimum:

| Symbol | (tp, sl) | reward:risk | barrier_balance | directional_spread % | mean_labeled_pnl % | exec_consistency |
|---|---|---:|---:|---:|---:|---:|
| BCH | (2.0, 1.0) **current** | 2.00 | 0.4953 | **−0.1671** | 4.0224 | 0.7143 |
| BCH | **(2.0, 1.25) chosen** | 1.60 | 0.6154 | **+0.0705** | 4.8784 | 0.8151 |
| LDO | (2.0, 1.0) **current** | 2.00 | 0.4454 | **−0.7085** | 4.5866 | 0.6549 |
| LDO | **(1.5, 1.25) chosen** | 1.20 | 0.8024 | **−0.2436** | 6.2624 | 0.8975 |
| TRX | (2.0, 1.0) **current=chosen** | 2.00 | 0.5027 | −0.0558 | 3.2167 | 0.7174 |

`barrier_balance` = mean(TP-hit) / mean(SL-hit) across both sides; → 1.0 means a
balanced barrier, < 1 means SL-saturated. `exec_consistency` = fraction of
labelable bars whose labeled direction has POSITIVE realised fee-net PnL.

### Section 2.4 — T3: recommended per-symbol multipliers

`axisC_recommended_multipliers.csv`. Selection rule (pre-registered IN the EDA
script before this brief): among eligible cells (SL ∈ [0.75, 1.25], TP ∈
[1.5, 2.5], `barrier_balance` ∈ [0.55, 1.85], `n_labelable` ≥ 0.90× current,
entropy ≥ 0.97) pick max `directional_spread`, and recalibrate ONLY if the
eligible optimum STRICTLY beats the current global cell:

| Symbol | Current | Recommended | spread Δ | barrier_balance Δ | decision |
|---|---|---|---:|---:|---|
| BCH | (2.0, 1.0) | **(2.0, 1.25)** | **+0.2376** | 0.495 → 0.615 | RECALIBRATE |
| LDO | (2.0, 1.0) | **(1.5, 1.25)** | **+0.4649** | 0.445 → 0.802 | RECALIBRATE |
| TRX | (2.0, 1.0) | **(2.0, 1.0)** | 0.0000 | unchanged | KEEP (no data-snoop) |

- **BCH → (2.0, 1.25)**: `directional_spread` flips negative → positive; all four
  economics metrics (spread, balance, mean PnL, exec_consistency) improve.
- **LDO → (1.5, 1.25)**: largest spread improvement (+0.4649); balance 0.45 →
  0.80; mean PnL 4.59 → 6.26; exec_consistency 0.65 → 0.90. **HONEST CAVEAT** —
  LDO's `directional_spread` is NEGATIVE across the ENTIRE 9-cell grid. The
  recalibration corrects the SL-saturation pathology; it does NOT manufacture a
  positive LDO label spread. LDO's IS signal is structurally weak independent of
  barrier geometry. This axis is "fix the barrier pathology," NOT "fix LDO."
- **TRX → KEEP (2.0, 1.0)**: TRX's higher-`directional_spread` grid cells (e.g.
  (2.5, 0.75) at +0.20) are all SL-saturated (`barrier_balance` 0.29 < 0.55) and
  excluded by the balance band; the eligible optimum (1.5, 1.0) at −0.0740 does
  not beat the current −0.0558. TRX keeps the global pair — discipline guard
  fires, no data-snoop.

### Section 2.5 — T4: AXIS A (LDO universe revision) rejection evidence

`axisA_replacement_screen.csv` — IS-momentum Sharpe proxy for the 5
/069-shortlisted LDO replacement candidates (all cleared /069 Gate 1+2):

| Symbol | role | IS Sharpe proxy | frac pos months | beats LDO? |
|---|---|---:|---:|---|
| LDOUSDT | INCUMBENT | −0.1132 | 0.419 | — |
| ADAUSDT | candidate | −0.1383 | 0.339 | NO |
| FILUSDT | candidate | +0.1341 | 0.593 | YES |
| ATOMUSDT | candidate | −0.2724 | 0.468 | NO |
| ALGOUSDT | candidate | −0.3261 | 0.379 | NO |
| VETUSDT | candidate | −0.2646 | 0.387 | NO |

Only 1 of 5 (FIL) beats LDO's IS-edge proxy. AXIS A is DOMINATED: (1) /052 ALREADY
ran the LDO-removal investigation (`analysis/iteration_v3-052/ldo_removal_eda.py`)
and pre-falsified it at single-seed scope (IS Δ −0.16, IS-OOS daily ratio 3.58
OUT-OF-BAND = PATH C-suspicious by construction); re-running it now repeats closed
work. (2) /069 ALREADY ran universe EXPANSION (+ADA) INERT — and ADA here screens
BELOW LDO. (3) The single candidate that beats LDO (FIL) does so by a thin proxy
margin (+0.13 vs −0.11); a FIL-for-LDO swap is a 2-axis change (drop LDO model +
add FIL model + REQUIRED_GAP recompute) outside single-axis EXPLORATION discipline.

### Section 2.6 — T5: AXIS B (model architecture) rejection evidence

DOMINATED — no fresh table needed. XGBoost head-to-head was tested at /016
(NEGATIVE-clean; model-arch axis closed). LightGBM hyperparameter-space changes
are knob-tuning; cycle 1 exhausted the knob space and
`feedback_v3_structural_over_knob_exploration.md` deprioritises knobs. The EDA
surfaces no structural model bottleneck; the bottleneck it DOES surface is the
barrier geometry (AXIS C).

### Section 2.10 — EXPLORATION anchor confirmation

The anchor for this EXPLORATION is **iter-v3/060 EXPLORATION-MODE-REFERENCE**
(IS monthly Sharpe **+0.8325** / OOS monthly Sharpe **+0.1403**), the unified
10-seed-architecture 3-seed EXPLORATION-mode reference. Consistent with the /071
and /072 briefs, the cycle-2 EXPLORATION baseline carries the /061
`vol_scale_floor_per_symbol={"TRXUSDT": 0.5}` as inherited state and is treated
as `/060-trade-roster-equivalent` once the single `label_mode` revert (Section
3.1 Edit 2) restores the /060 triple-barrier labeling rule. /071 and /072 both
ran this exact baseline state and the /071 Critic certified the
roster-equivalence framing clean. The ONLY intentional difference vs that
established cycle-2 baseline is the single varied axis
`V3_ATR_MULTIPLIERS_PER_SYMBOL` (Edit 1). BASELINE_V3.md remains canonical at
`v0.v3-059` (IS +1.0894 / OOS +0.5791); /059 is the CONFIRMATION-mode anchor, NOT
this EXPLORATION's anchor (per `feedback_v3_cycle1_axis_pass_criteria.md` two-tier
evaluation — EXPLORATION-mode Δ measured vs /060).

## Section 3 — Proposed Changes (LOCKED — single-axis variation)

The single varied axis is **`V3_ATR_MULTIPLIERS_PER_SYMBOL`** (the per-symbol ATR
triple-barrier multiplier dict). Everything else — V3_MODELS, V3_FEATURE_COLUMNS
(14, unchanged), ENSEMBLE_SIZE, ENSEMBLE_SEEDS, REQUIRED_GAP, embargo, the 7-gate
risk stack, BacktestConfig, n_trials — is UNCHANGED.

### Section 3.1 — Code edits (specification for the Engineer; QR does not write src/)

**Edit 1 — the axis (`src/crypto_trade/features_v3/__init__.py:251`).** Set:

```python
V3_ATR_MULTIPLIERS_PER_SYMBOL: dict[str, tuple[float, float]] = {
    "BCHUSDT": (2.0, 1.25),   # iter-v3/073: barrier-balance recalibration (was global (2.0,1.0))
    "LDOUSDT": (1.5, 1.25),   # iter-v3/073: SL-saturation correction (was global (2.0,1.0))
    # TRXUSDT omitted — falls back to DEFAULT_ATR_MULTIPLIERS (2.0, 1.0); EDA keep-decision.
}
```

`atr_multipliers_for_symbol()` already routes this dict; `_build_v3_model`
(`run_baseline_v3.py:1486-1498`) already threads `_atr_tp, _atr_sl` per symbol
into `LightGbmStrategy(atr_tp_multiplier=..., atr_sl_multiplier=...)`. The
mechanism is proven — `run_baseline_v3.py:1485` documents the same per-symbol ATR
path ran at iter-v3/032 with LDO `(1.5, 0.75)`. **ZERO new strategy/model code.**

**Edit 2 — REVERT /072 leftover (`run_baseline_v3.py:1506`).** The runner is
currently on `label_mode="fixed_horizon"` (the /072 NEGATIVE axis). Revert to
`label_mode="triple_barrier"`. The per-symbol ATR multipliers ONLY take effect
under the triple-barrier label path — this revert is mandatory for the axis to
fire AND to restore the /060 anchor labeling rule.

**Edit 3 — cosmetic.** `ITERATION_LABEL = "v3-073"` (`run_baseline_v3.py:128`).

**`vol_scale_floor_per_symbol` — DELIBERATELY UNCHANGED at `{"TRXUSDT": 0.5}`.**
This dict was introduced at /061. /071 and /072 BOTH ran with it (the /071 brief
change table explicitly lists "TRX vol_scale_floor 0.5 (per-symbol, /061) —
unchanged") and BOTH anchored against /060 as `/060-trade-roster-equivalent`; the
/071 Critic certified that framing clean. It is therefore the ESTABLISHED cycle-2
EXPLORATION baseline state. Reverting it now would (a) deviate from the cycle-2
baseline /071+/072 ran and (b) introduce a SECOND varied axis (a TRX vol_scale
change). It stays. The Phase-5.5 wiring assertion at `run_baseline_v3.py:674-690`
continues to expect `{"TRXUSDT": 0.5}` — NO change.

**Edit 4 — adversarial tests.** Add `tests/features_v3/test_per_symbol_atr_v3-073.py`
with ≥5 assertions: (a) `atr_multipliers_for_symbol("BCHUSDT") == (2.0, 1.25)`;
(b) `atr_multipliers_for_symbol("LDOUSDT") == (1.5, 1.25)`; (c)
`atr_multipliers_for_symbol("TRXUSDT") == (2.0, 1.0)` (DEFAULT fallback); (d)
`atr_multipliers_for_symbol("UNKNOWN") == DEFAULT_ATR_MULTIPLIERS`; (e) the dict
has exactly 2 keys. v1/v2 backward-compat: V3_ATR_MULTIPLIERS_PER_SYMBOL is a
v3-only symbol — v1/v2 paths never read it; existing 53-test v1/v2 suite must
still pass (Engineer confirms).

### Section 3.2 — Disambiguation: label barriers vs trade-exit barriers (Critic /072 Rec #3)

This axis is **label-execution consistent BY CONSTRUCTION** — the explicit
satisfaction of Critic /072 Rec #3 ("any labeling change must keep the label
target consistent with TP/SL execution"). The /072 fixed-horizon axis FAILED
precisely because it DECOUPLED the label (a fixed-horizon return sign) from the
execution (a barrier exit). AXIS C cannot decouple them:

- **Training label** — `labeling.py::label_trades` with `use_atr_labeling=True`
  uses `tp_dist = atr * atr_tp_multiplier`, `sl_dist = atr * atr_sl_multiplier`
  (lgbm.py:352-353) — the per-symbol multipliers.
- **Live-execution exit** — at predict time `lgbm.py:705-713` computes the
  `Signal.tp_pct = natr * atr_tp_multiplier`, `Signal.sl_pct = natr *
  atr_sl_multiplier` — the SAME per-symbol multipliers. The `Signal` carries
  these into the backtest, OVERRIDING `BacktestConfig`'s static `stop_loss_pct`/
  `take_profit_pct`.

Changing `V3_ATR_MULTIPLIERS_PER_SYMBOL` moves the training label AND the
execution barrier IN LOCKSTEP. The label always describes exactly the outcome the
backtest will realise. `BacktestConfig.timeout_minutes` (10080) and
`label_timeout_minutes` (10080) are UNCHANGED — the `_verify_timeout_consistency`
assertion at `run_baseline_v3.py` continues to hold.

### Section 3.3 — Anchor / baseline-state checklist (for the Phase 5.5 gate)

The Phase 5.5 anchor-byte gate (per `feedback_v3_iter064_process_lessons.md`
Rule 1) must verify the cycle-2 EXPLORATION baseline state (the state /071 and
/072 ran) is restored except the single varied axis:

- `label_mode == "triple_barrier"` (Edit 2 — REVERT of the /072 axis).
- `V3_ATR_MULTIPLIERS_PER_SYMBOL == {"BCHUSDT": (2.0, 1.25), "LDOUSDT": (1.5,
  1.25)}` — the single varied axis (Edit 1).
- `vol_scale_floor_per_symbol == {"TRXUSDT": 0.5}` — UNCHANGED (cycle-2 baseline
  state /071+/072 ran; NOT a varied axis).
- `DEFAULT_ATR_MULTIPLIERS == (2.0, 1.0)` (TRX falls back to this).
- `BacktestConfig.timeout_minutes == label_timeout_minutes == 10080`.
- V3_MODELS = (BCH, LDO, TRX); REQUIRED_GAP = 66; embargo = 22.
- `block_long_for == () == block_short_for`; `enable_per_symbol_drawdown_brake ==
  False`; `enable_per_symbol_cap == False`; `enable_regime_gate == False`.
- `atr_multipliers_for_symbol`: BCH → (2.0, 1.25), LDO → (1.5, 1.25), TRX →
  (2.0, 1.0).

The ONLY intentional difference vs the /071/072 cycle-2 baseline is
`V3_ATR_MULTIPLIERS_PER_SYMBOL` (Edit 1). Edit 2 (`label_mode`) is the REVERT of
the /072 axis — without it the ATR multipliers would not fire (they only take
effect under the triple-barrier path) and iter-v3/073 would stack on the failed
/072 label.

## Section 4 — Expected OOS Impact (LOCKED — predicted bands)

Anchor = /060 (IS +0.8325 / OOS +0.1403). Per
`feedback_v3_cycle1_axis_pass_criteria.md` cycle-2 axis-PASS thresholds.

### Section 4.1 — PROMISING-AT-EXPLORATION bands

PROMISING requires IS shift ≥ +0.10 AND OOS shift ≥ +0.20 vs /060:
- IS monthly Sharpe ≥ **+0.9325** (Δ ≥ +0.10).
- OOS monthly Sharpe ≥ **+0.3403** (Δ ≥ +0.20).
- `frac_positive_paths` ≥ 0.50 (EXPLORATION-relaxed; 0.55 at CONFIRMATION).
- No Critic methodology FAIL.

Mechanism if PROMISING: the per-symbol barrier recalibration lifts the M1 training
label's directional-economics quality on BCH+LDO (the two recalibrated symbols),
the M1 trees learn a less stop-out-noisy target, and the cleaner labels translate
into better directional precision in BOTH windows. Best-estimate point: IS
**+0.95**, OOS **+0.30** — note OOS lands just BELOW the +0.34 PROMISING floor at
the point estimate; PROMISING is the upside tail, not the modal outcome (see
Section 7).

### Section 4.2 — NEGATIVE bands (closes axis at catalog level — DISJUNCTIVE OR)

NEGATIVE if IS Δ < −0.10 (IS < +0.7325) **OR** OOS Δ < −0.20 (OOS < −0.0597).
Either single gate fail is sufficient (disjunctive OR per Section 8.4 / `feedback_v3_iter064_process_lessons.md` Rule 4).

### Section 4.3 — INERT-AT-EXPLORATION zone

INERT if IS Δ ∈ [−0.10, +0.10] (IS ∈ [+0.7325, +0.9325]) OR OOS Δ ∈ [−0.20,
+0.20] (OOS ∈ [−0.0597, +0.3403]) without firing NEGATIVE or SUSPICIOUS — the
noise band. INERT closes the axis at catalog level; does not advance to a bundle.

### Section 4.4 — SUSPICIOUS gate (OOS/IS ratio — MANDATORY per `feedback_v3_oos_is_ratio_gate.md`)

**Pre-registered LOCKED: OOS/IS monthly Sharpe ratio > 3.0 → SUSPICIOUS**,
regardless of absolute OOS Sharpe magnitude. This axis is at NON-TRIVIAL risk of
tripping this gate: **all recalibrations widen the SL** (BCH 1.0→1.25, LDO
1.0→1.25). SL-widening is the canonical regime-exposure failure mode — /065
SL-widening, /042 SL-tightening and the /070 CONFIRMATION all produced
SUSPICIOUS-OOS-DOMINANT outcomes (the IS-collapse + OOS-soar signature). A wider
SL lets each stop-out lose MORE; if the OOS window happens to favour the wider
barrier and the IS window does not, the ratio gate fires. SUSPICIOUS classifies
the axis as regime-exposed and NOT bundle-grade. The mitigating distinction (the
EDA's rationale): the current barrier is pathologically SL-SATURATED (66% SL-hit),
so a wider SL here REBALANCES toward TP-hits — the OPPOSITE of /065 (which widened
an already-balanced barrier). But the brief does NOT rely on that distinction
holding; the SUSPICIOUS gate is pre-registered and binding.

### Section 4.5 — Behavioral-effect predictor + saturation falsifier (per `feedback_axis_saturation_predictor.md`)

The axis changes label GEOMETRY for 2 of 3 symbols — it WILL change the trade
roster (unlike a saturated knob). Predicted IS trade-count change vs /060's 159:
**+10 to +35** (LDO's 1.5×ATR TP is closer/easier to hit → more LDO labels resolve
to a directional outcome; BCH's wider SL slightly shifts entry timing). Predicted
OOS trade-count change vs /060's 102: **+5 to +25**. **Saturation falsifier**: if
the IS trade count lands within ±3 of /060's 159 AND per-symbol IS roster shifts
are all < ±5 trades, the axis did NOT meaningfully re-label → NULL-RESULT (the
multipliers were too close to the global pair to matter). The EDA's `n_labelable`
column shows the labelable population is unchanged (the timeout is unchanged), but
the LABEL DIRECTION distribution and barrier OUTCOMES change materially — so a
genuine roster shift is expected.

### Section 4.6 — Per-symbol Δ prediction (falsifier)

| Symbol | /060 OOS wpnl | Predicted /073 OOS wpnl | Falsifier |
|---|---:|---|---|
| BCH | +1.9078 | [−10, +20] | the (2.0,1.25) recalibration should not COLLAPSE BCH; if BCH OOS wpnl < −15, the axis broke BCH (a NEGATIVE-direction symptom). |
| LDO | −19.7208 | [−30, +5] | LDO is structurally weak (EDA: negative spread at all grid cells); the axis aims to REDUCE LDO drag, not reverse it. If LDO OOS wpnl < −35, the SL-widening made LDO's bleed deeper — a SUSPICIOUS/NEGATIVE symptom. |
| TRX | +23.3119 | [+10, +30] | TRX is UNCHANGED at the global pair; TRX OOS wpnl should stay near /060. A TRX shift > ±15 means cross-symbol contamination via the shared walk-forward / Optuna trajectory (a known single-seed artifact per `feedback_v3_single_seed_frozen_baseline.md`) — NOT axis signal. |

### Section 4.7 — BCH IS concentration sensitivity (per Critic /059 Rec #3)

/060's BCH IS share is ~177% (3-seed-averaging structural artifact; one-sided
lower-bound gate ≥ 80% per `feedback_v3_cycle1_axis_pass_criteria.md`). The BCH
(2.0, 1.25) recalibration shifts BCH's own label economics — if it LIFTS BCH IS
contribution the headline IS Sharpe holds; if it REDUCES BCH IS contribution
(BCH IS share drops below ~80%) while LDO/TRX do not compensate, the headline IS
Sharpe likely regresses → NEGATIVE. The EDA's BCH `directional_spread` flips
positive (−0.167 → +0.071) and `mean_labeled_pnl` rises (4.02 → 4.88), which
predicts BCH IS contribution is PRESERVED or LIFTED — but this is an IS-label
metric, not the runner's gated walk-forward number. Monitored, not asserted.

## Section 5 — Risk Mitigation

This iteration introduces NO new risk primitive — the 7-gate v3 risk stack is
UNCHANGED (BTC trend kill, vol scaling, ADX, Hurst regime, feature z-score OOD,
low-vol filter, hit-rate DISABLED). The axis is a labeling-geometry change.

The relevant risk-mitigation question is the SL-widening exposure (Section 4.4).
The IS-calibrated mitigation already in place: the EDA's eligible-cell selection
rule constrained SL to [0.75, 1.25] (a NARROW band — no aggressive widening) and
required `barrier_balance ∈ [0.55, 1.85]` (the chosen cells are 0.62 BCH / 0.80
LDO — neither pathologically SL- nor TP-saturated). The recalibration is a
correction TOWARD barrier balance, calibrated on IS-only data, with the
discipline guard that TRX (whose grid optimum did not beat current) was NOT
changed. Simulated historical effect: the EDA grid sweep IS the simulation —
across the full IS window, the chosen cells lift `directional_spread` on both
recalibrated symbols and lift `exec_consistency` (BCH 0.71→0.82, LDO 0.65→0.90).

## Section 6 — Risk Management Design

7-primitive v3 risk gate stack — UNCHANGED, all fire-rates inherited from /060:

| # | Primitive | State | Fire-rate (inherited /060 profile) |
|---|---|---|---|
| 1 | BTC trend kill (±15%, 42-bar) | ACTIVE | ~25% of OOS candidates killed |
| 2 | Vol scaling | ACTIVE | continuous position scaling |
| 3 | ADX threshold (20.0 global) | ACTIVE | low-ADX entries suppressed |
| 4 | Hurst regime check | ACTIVE | mean-revert/trend gating |
| 5 | Feature z-score OOD (|z|>2.0, 14-D) | ACTIVE | tail-feature entries gated |
| 6 | Low-vol filter | ACTIVE | min-NATR gate |
| 7 | Hit-rate feedback | DISABLED | — |

No primitive threshold changes. Regime gate DISABLED (/022). Per-symbol cap
DISABLED (/020). Per-symbol drawdown brake DISABLED (/054). Primitive 10
`block_long_for=()` (/051 REVERT).

Regime coverage: the IS window (2022-09 LDO listing → 2025-03) spans the 2022 bear,
2023 recovery, 2024 bull and 2024-Q4/2025-Q1 chop; the OOS window (2025-03 →
2026-05) spans the 2025 trend + recent chop. The barrier recalibration is applied
identically across all IS regimes (it is a label-geometry constant, not a
regime-conditional gate) — no regime is preferentially exposed by the MECHANISM.
The SUSPICIOUS gate (Section 4.4) is the guard against the OUTCOME nonetheless
being regime-skewed.

## Section 7 — Pre-Registered Failure-Mode Prediction

**Most plausible failure (NEGATIVE, ~35%).** The single-axis change at single-seed
n_trials=35 widens the SL on 2 of 3 symbols. The dominant NEGATIVE mechanism: a
wider SL means every stop-out books a deeper loss. The current barrier is
SL-saturated (66% SL-hit), and even at the rebalanced (2.0,1.25)/(1.5,1.25) cells
the SL is still hit more often than the TP (BCH chosen-cell long_sl_rate 0.57 >
long_tp_rate 0.34; LDO 0.58 > 0.40). So MOST trades still stop out — now at a
DEEPER loss per stop. If the M1 label-economics improvement (the EDA's
`directional_spread` lift) does not translate into enough additional TP-hit
precision to offset the deeper losers, IS Sharpe regresses below +0.7325 and the
axis closes NEGATIVE. The metric signature: IS profit_factor falls (deeper losers),
IS MaxDD widens, OOS PF falls. This is the /065 SL-widening failure mechanism —
weighted ≥ 25% per `feedback_v3_iter064_process_lessons.md` Rule 3, and at 35%
here because all recalibrations are SL-widening and /065 is a direct precedent.

**Second failure (SUSPICIOUS-OOS-DOMINANT, ~20%).** The same SL-widening, but the
2025 OOS window's trend lets the wider barrier's winners run while the IS
chop/bear window lets the wider barrier's losers bleed → IS regresses, OOS soars,
OOS/IS ratio > 3.0 fires the Section 4.4 gate. This is the /065 + /070 pattern.
The gate catches it; the axis does not advance to a bundle.

**Third outcome (INERT/NULL-RESULT, ~25%).** The per-symbol multipliers are close
enough to the global pair that the re-labeled trade roster barely moves; IS/OOS
shifts land in the noise band; the Section 4.5 saturation falsifier fires.

**PROMISING (~20%).** The label-economics lift (EDA `directional_spread`: BCH
−0.167→+0.071, LDO −0.709→−0.244) genuinely improves M1 directional precision in
both windows; IS ≥ +0.9325 AND OOS ≥ +0.3403. This is the upside tail — the EDA
evidence supports a label-QUALITY improvement, but label-quality at single-seed
n_trials=35 has a documented weak link to OOS Sharpe (the /060 14-feature
local-optimum sensitivity, `feedback_v3_iter064_process_lessons.md` Rule 5), and
the SL-widening direction caps the upside. PROMISING ≤ 25% per Rule 3.

What the gates should catch: the Section 4.4 OOS/IS ratio > 3.0 gate catches the
regime-exposure mode; the Section 8.2 disjunctive-OR NEGATIVE gate catches the
deeper-losers IS-regression mode; the Section 4.5 saturation falsifier catches the
null-effect mode; the Section 4.6 per-symbol falsifiers catch a single-symbol
collapse or cross-symbol contamination.

## Section 8 — Pre-Registered MERGE/NO-MERGE Numerical Criteria (LOCKED)

This is an EXPLORATION — no MERGE. The classification is locked BEFORE the
backtest. Anchor = /060 (IS +0.8325 / OOS +0.1403).

### Section 8.1 — PROMISING-AT-EXPLORATION (conjunctive AND — all 4 must hold)

1. IS monthly Sharpe ≥ **+0.9325** (Δ ≥ +0.10 vs /060), AND
2. OOS monthly Sharpe ≥ **+0.3403** (Δ ≥ +0.20 vs /060), AND
3. `frac_positive_paths` ≥ 0.50, AND
4. No Critic methodology FAIL (13 checks + §11 anti-pattern scan).

→ PROMISING-AT-EXPLORATION; axis carries forward as a cycle-2 CONFIRMATION
bundle candidate.

### Section 8.2 — NEGATIVE-CLOSE (disjunctive OR — either single gate fails)

IS monthly Sharpe < **+0.7325** (Δ < −0.10) **OR** OOS monthly Sharpe < **−0.0597**
(Δ < −0.20). → NEGATIVE; axis CLOSED at catalog level.

### Section 8.3 — INERT-AT-EXPLORATION (and NULL-RESULT sub-flavor)

IS Δ ∈ [−0.10, +0.10] OR OOS Δ ∈ [−0.20, +0.20], without NEGATIVE or SUSPICIOUS
firing. → INERT; axis closed at catalog level. NULL-RESULT sub-flavor if the
Section 4.5 saturation falsifier ALSO fires (roster barely moved).

### Section 8.4 — Disjunctive SUSPICIOUS gate (OOS/IS ratio — MANDATORY)

**OOS/IS monthly Sharpe ratio > 3.0 → SUSPICIOUS-OOS-DOMINANT**, regardless of
absolute OOS Sharpe magnitude (per `feedback_v3_oos_is_ratio_gate.md`).
**Precedence**: per the established /071 precedent, SUSPICIOUS takes
classification precedence over NEGATIVE when both fire concurrently (no magnitude
qualifier). A SUSPICIOUS axis is regime-exposed and NOT eligible to advance to a
cycle-2 CONFIRMATION bundle as an edge ingredient. The disjunctive OR across
Sections 8.1–8.4: evaluate SUSPICIOUS first, then NEGATIVE, then PROMISING, then
INERT.

### Section 8.5 — Trade-rate-floor safety net

Per `feedback_v3_trade_rate_floor_bundle_level.md`, the v3 trade-rate floor (≥10
trades/month OOS, ≥130 OOS total) applies at the CONFIRMATION-bundle level, NOT
per EXPLORATION row. This EXPLORATION records its OOS trade count (predicted
107–127, Section 4.5) as INFORMATIONAL; a low count does not by itself change the
8.1–8.4 classification. If this axis is later bundled into a cycle-2 CONFIRMATION,
the bundle-level floor applies there.

## Section 9 — Library Stack Declaration

No new libraries. The axis uses only the existing `LightGbmStrategy` ATR path.
Pinned stack (verified at brief time via `uv run python -c "import ..."`):

- lightgbm 4.6.0
- optuna 4.8.0
- numpy 2.2.6
- pandas 3.0.0
- scikit-learn 1.8.0
- scipy 1.17.0
- statsmodels 0.14.6
- pyarrow 23.0.1

CPCV/PBO/PSR/DSR are computed in-repo (`validation_v3.py` + `dsr.json` writer); no
mlfinlab/mlfinpy/pypbo/fracdiff dependency. Walk-forward harness `walk_forward.py`
retained (post-fix `e149e9d` state — `train_end_ms = test_start_ms - embargo_ms`,
embargo 22 candles); REQUIRED_GAP 66 is well within the training window — no
edge-case purge-overrun.

## Section 10 — QR Audit Trail (per `feedback_v3_axis_selection_quant_discipline.md`)

**Axis selection process.** This iteration's axis was chosen by the QR with
committed EDA backing per `feedback_v3_axis_selection_quant_discipline.md` rules
1–3 (EDA precedes axis selection; QR makes the call; brief Section 2 contains the
EDA-derived numerical tables).

- **EDA commit**: `b004bc9` — `analysis(iter-v3/073): axis-selection EDA —
  per-symbol triple-barrier asymmetry`. Script:
  `analysis/iteration_v3-073/axis_selection_eda.py`. Outputs:
  `T0_anchor_values.csv`, `axisC_barrier_hit_profile.csv`,
  `axisC_multiplier_grid.csv`, `axisC_recommended_multipliers.csv`,
  `axisA_replacement_screen.csv`, `axis_selection_summary.csv`, `synthesis.md`.
- **Orchestrator-suggested candidates** (4): (1) LDO universe revision; (2) model
  architecture / hyperparameter regime; (3) triple-barrier parameter refinement
  that stays label-execution consistent; (4) risk primitive / NEW feature family
  (funding/OI/basis).
- **QR decision**: candidate #3 — per-symbol triple-barrier asymmetry — SELECTED.
  Not superseding an orchestrator setup commit (no setup commit was made
  ad-hoc); the QR EDA evaluated all candidates and selected the one with the
  strongest IS-data evidence. Candidate #4 (funding/OI/basis) was implicitly
  evaluated and rejected upstream — the /072 EDA already established the funding
  family is CLOSED (best |AUC−0.5| = 0.0347) and no OI/basis feature module
  exists in `features_v3/`.
- **Quantitative basis for selecting candidate #3**: the EDA surfaces a concrete,
  quantified bottleneck — the single global `(2.0, 1.0)` pair produces an
  SL-saturated label on every symbol (LONG SL-hit 58–69%, worst LDO 69%,
  `axisC_barrier_hit_profile.csv`). The 9-cell-per-symbol grid sweep shows 2 of
  3 symbols have an eligible cell with strictly higher `directional_spread`
  (BCH +0.2376 flips spread positive; LDO +0.4649) at improved `barrier_balance`
  and `exec_consistency` (`axisC_multiplier_grid.csv`,
  `axisC_recommended_multipliers.csv`). Candidates #1 and #2 are DOMINATED:
  AXIS A — only 1/5 /069-shortlisted candidates beats LDO's IS-edge proxy, /052
  already pre-falsified LDO removal, /069 already ran +ADA INERT
  (`axisA_replacement_screen.csv`); AXIS B — XGBoost closed at /016, LightGBM
  hyperparameter changes are knob-tuning.
- **Why this axis satisfies Critic /072 Rec #3**: AXIS C is label-execution
  consistent BY CONSTRUCTION (Section 3.2) — the runner derives both the training
  label and the live-execution `Signal` exit from the SAME per-symbol multipliers.
  The /072 fixed-horizon NEGATIVE was caused by label-execution DECOUPLING; AXIS C
  structurally cannot decouple them.
- **Honest caveats carried into Sections 4.4 and 7**: (a) all recalibrations
  widen the SL — the regime-exposure failure mode; the SUSPICIOUS OOS/IS ratio
  gate is pre-registered and binding; (b) LDO's `directional_spread` is negative
  across the entire grid — the axis corrects the barrier pathology, it does NOT
  "fix LDO"; (c) the single `label_mode` revert (Edit 2) restores the /072 axis to
  triple-barrier so the ATR multipliers fire and iter-v3/073 does not stack on the
  failed /072 fixed-horizon label — verified at the Phase 5.5 anchor-byte gate.
  `vol_scale_floor_per_symbol={"TRXUSDT": 0.5}` is DELIBERATELY kept (the cycle-2
  baseline state /071+/072 ran) — reverting it would be a second axis.

**Setup commit SHA**: (backfilled after the setup commit per the standard
two-commit flow).
