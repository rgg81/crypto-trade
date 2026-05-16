# iter-v3/073 Axis-Selection EDA — Synthesis

CYCLE 2 EXPLORATION #3 of 10. QR EDA-driven axis selection per
`feedback_v3_axis_selection_quant_discipline.md`. Committed BEFORE the brief.

## Candidate axes (orchestrator-suggested; QR decides)

- **AXIS A — LDO universe revision**: replace LDOUSDT with a stronger 3rd symbol.
- **AXIS B — model architecture / hyperparameter regime**: XGBoost (closed at /016)
  or LightGBM hyperparameter-space changes.
- **AXIS C — per-symbol triple-barrier asymmetry calibrated to execution**: replace
  the ONE GLOBAL ATR multiplier pair (atr_tp=2.0, atr_sl=1.0) with per-symbol
  multipliers in `V3_ATR_MULTIPLIERS_PER_SYMBOL`, calibrated to each symbol's
  empirical barrier-hit profile. Per Critic /072 Rec #3, any labeling change must
  stay label-execution consistent.

## T0 anchor (byte-exact — `T0_anchor_values.csv`)

/060 EXPLORATION-mode reference, from `reports-v3/iteration_v3-060/comparison.csv`:
IS monthly Sharpe **+0.8325** (line 2), OOS monthly Sharpe **+0.1403** (line 2),
IS/OOS daily Sharpe +1.7115 / +0.3659, IS PF 1.2806 / OOS PF 1.0482, IS 159 / OOS
102 trades. Per-symbol OOS weighted_pnl: BCH **+1.9078** (line 18), LDO **-19.7208**
(line 19), TRX **+23.3119** (line 20).

## AXIS C findings (IS-only)

### C1 — barrier-hit profile at the CURRENT global (2.0, 1.0) pair

`axisC_barrier_hit_profile.csv`. The current global multiplier pair produces an
**SL-saturated label population on every symbol** — the SL barrier is hit far more
often than the TP barrier:

| Symbol | NATR median | LONG TP-hit | LONG SL-hit | LONG tp/sl ratio | SHORT tp/sl ratio |
|---|---:|---:|---:|---:|---:|
| BCHUSDT | 3.70% | 30.2% | 63.7% | 0.475 | 0.516 |
| **LDOUSDT** | **5.01%** | **27.3%** | **69.1%** | **0.395** | 0.500 |
| TRXUSDT | 2.65% | 34.5% | 58.2% | 0.592 | 0.424 |

LDO is the worst: its LONG label is **69.1% stop-outs**, tp/sl ratio 0.395. This
re-confirms the /072 EDA's `axis1_ldo_barrier_diagnosis.csv` finding (TP-hit 27.33%,
SL-hit 69.14%) with a fully independent re-computation. The mechanism is geometric:
LDO has the highest 8h NATR (5.01% median vs BCH 3.70%, TRX 2.65%), so the SL at
1xATR (~5%) is hit by ordinary 8h chop long before the TP at 2xATR (~10%). One
global multiplier pair cannot be barrier-balanced for three symbols whose volatility
differs by ~2x.

### C2 — per-symbol (tp, sl) grid sweep (`axisC_multiplier_grid.csv`)

9-cell grid per symbol (TP in {1.5, 2.0, 2.5}, SL in {0.75, 1.0, 1.25}). The
primary label-economics metric is `directional_spread` = mean(realised fee-net
labeled-direction PnL | label=+1) - mean(... | label=-1) — a DIRECT economics
metric (the realised PnL of the direction the label picks), NOT a label-space
cleanliness proxy. (The /072 EDA's misleading "directional-spread" metric measured
label-space separation; Critic /072 Rec #3 flagged it. This `directional_spread`
is computed on the realised fee-net trade PnL the backtest actually books.) All
grid cells keep label entropy >= 0.99 — balance is never the bottleneck.

### C3 — recommended per-symbol multipliers (`axisC_recommended_multipliers.csv`)

Selection rule (pre-registered in the EDA script): among eligible cells (SL in
[0.75, 1.25], TP in [1.5, 2.5], barrier_balance in [0.55, 1.85], n_labelable >=
0.90x current, entropy >= 0.97), pick max `directional_spread` — and recalibrate
ONLY if the eligible optimum STRICTLY beats the current global cell:

| Symbol | Current (tp, sl) | Current spread | Recommended (tp, sl) | Recommended spread | spread delta | exec_consistency |
|---|---|---:|---|---:|---:|---:|
| BCHUSDT | (2.0, 1.0) | -0.1671 | **(2.0, 1.25)** | **+0.0705** | **+0.2376** | 0.71 -> 0.82 |
| LDOUSDT | (2.0, 1.0) | -0.7085 | **(1.5, 1.25)** | -0.2436 | **+0.4649** | 0.65 -> 0.90 |
| TRXUSDT | (2.0, 1.0) | -0.0558 | **(2.0, 1.0) KEEP** | -0.0558 | 0.0000 | unchanged |

- **BCH -> (2.0, 1.25)**: directional_spread flips negative -> positive (+0.2376),
  barrier_balance 0.50 -> 0.62, mean_labeled_pnl 4.02 -> 4.88, exec_consistency
  0.71 -> 0.82. All four economics metrics agree.
- **LDO -> (1.5, 1.25)**: largest spread improvement (+0.4649), barrier_balance
  0.45 -> 0.80, mean_labeled_pnl 4.59 -> 6.26, exec_consistency 0.65 -> 0.90.
  HONEST CAVEAT: LDO's directional_spread is NEGATIVE across the ENTIRE 9-cell
  grid — at NO (tp, sl) does LDO's label population separate winners from losers
  with a positive spread. The recalibration corrects the SL-saturation pathology
  (balance, exec_consistency, mean PnL all improve materially) but it does NOT
  manufacture a positive spread. LDO's IS signal is structurally weak independent
  of barrier geometry. The axis is "fix the barrier pathology," not "fix LDO."
- **TRX -> KEEP (2.0, 1.0)**: TRX's higher-spread grid cells (e.g. (2.5, 0.75)
  spread +0.20) are all SL-saturated (barrier_balance 0.29 < 0.55) and excluded
  by the balance band; the eligible optimum (1.5, 1.0) at -0.0740 does NOT beat
  the current -0.0558. No data-snoop: TRX keeps the global pair.

So the proposed axis is a TWO-symbol recalibration: BCH (2.0, 1.25), LDO
(1.5, 1.25), TRX unchanged at the global default. Net feature count, universe,
model architecture, risk-gate stack, ENSEMBLE_SIZE, REQUIRED_GAP, embargo — all
UNCHANGED. The single varied axis is `V3_ATR_MULTIPLIERS_PER_SYMBOL`.

## AXIS A findings — LDO replacement IS-edge screen (`axisA_replacement_screen.csv`)

The cycle-2 axis #3 directive states a universe replacement "must clear an IS-edge
screen, not just feature-space distance." The 5 /069-shortlisted candidates (ADA,
FIL, ATOM, ALGO, VET — all cleared /069's Gate 1+2) were screened with a fast
IS-momentum Sharpe proxy:

| Symbol | Role | IS Sharpe proxy | frac pos months | beats LDO? |
|---|---|---:|---:|---|
| LDOUSDT | INCUMBENT | -0.1132 | 0.419 | — |
| ADAUSDT | candidate | -0.1383 | 0.339 | NO |
| FILUSDT | candidate | +0.1341 | 0.593 | YES |
| ATOMUSDT | candidate | -0.2724 | 0.468 | NO |
| ALGOUSDT | candidate | -0.3261 | 0.379 | NO |
| VETUSDT | candidate | -0.2646 | 0.387 | NO |

Only 1 of 5 (FIL) beats LDO's IS-edge proxy. AXIS A is DOMINATED:
1. /052 ALREADY ran the LDO-removal investigation (`analysis/iteration_v3-052/
   ldo_removal_eda.py`) and pre-falsified it at single-seed EXPLORATION scope —
   the 2-symbol counterfactual produced IS delta -0.16 and an IS-OOS daily ratio
   3.58 OUT-OF-BAND (PATH C-suspicious by construction). /052 explicitly DEFERRED
   LDO removal to multi-seed CONFIRMATION. Re-running an LDO-removal EXPLORATION
   now repeats closed work.
2. /069 ALREADY tested universe EXPANSION (+ADA) and it ran INERT — and ADA
   here screens BELOW LDO. A 4th-symbol addition is closed at catalog level.
3. The single candidate that beats LDO (FIL) does so by a thin proxy margin
   (+0.13 vs -0.11). A FIL-for-LDO swap would be a 2-axis change (drop LDO
   model + add FIL model + REQUIRED_GAP recompute) — outside single-axis
   EXPLORATION discipline — and the proxy is not the runner's 7-gate, 24-month
   walk-forward number. The proxy edge is too thin to justify a swap.

## AXIS B findings — model architecture

DOMINATED: XGBoost head-to-head was tested at /016 (NEGATIVE-clean; model-arch
axis closed). LightGBM hyperparameter-space changes are knob-tuning — cycle 1
exhausted the knob space, and `feedback_v3_structural_over_knob_exploration.md`
deprioritises knobs below NEW feature families / labeling / risk primitives.
There is no EDA-identifiable structural bottleneck in the model that AXIS B
targets — the bottleneck the EDA DOES surface is the barrier geometry (AXIS C).

## QR AXIS DECISION

**SELECTED: AXIS C — per-symbol triple-barrier asymmetry calibrated to execution.**

Per-symbol multipliers: BCH (atr_tp=2.0, atr_sl=1.25), LDO (atr_tp=1.5,
atr_sl=1.25), TRX unchanged at the global (2.0, 1.0). Wired via
`V3_ATR_MULTIPLIERS_PER_SYMBOL = {"BCHUSDT": (2.0, 1.25), "LDOUSDT": (1.5, 1.25)}`.

Rationale:
1. **Strongest IS-data evidence.** The EDA surfaces a concrete, quantified
   bottleneck: the single global (2.0, 1.0) pair produces an SL-saturated label
   on every symbol (LONG SL-hit 58-69%), worst on LDO (69%, tp/sl 0.395). Two of
   three symbols have an eligible grid cell with strictly higher directional_spread
   (BCH +0.2376 flips spread positive; LDO +0.4649). This is a measured constraint,
   not a category match — exactly what `feedback_v3_axis_selection_quant_discipline.md`
   requires.
2. **Label-execution consistent BY CONSTRUCTION** — the decisive contrast with the
   /072 fixed-horizon axis. The v3 runner derives BOTH the training label
   (`labeling.py::label_trades` ATR path, lgbm.py:352-353) AND the live-execution
   `Signal.tp_pct` / `Signal.sl_pct` (lgbm.py:705-713 predict path) from the SAME
   per-symbol `atr_tp_multiplier` / `atr_sl_multiplier`. Changing the multipliers
   moves the label and the execution barrier IN LOCKSTEP. /072 NEGATIVE was
   caused by label-execution DECOUPLING (a fixed-horizon label vs a barrier exit);
   AXIS C cannot decouple them. This directly satisfies Critic /072 Rec #3.
3. **ZERO new code.** `V3_ATR_MULTIPLIERS_PER_SYMBOL` is the entire interface;
   `atr_multipliers_for_symbol()` already routes it; `_build_v3_model` already
   threads `_atr_tp, _atr_sl` per symbol (the (1.5, 0.75) LDO comment at
   run_baseline_v3.py:1485 confirms this exact mechanism ran at /032). The setup
   commit changes only `V3_ATR_MULTIPLIERS_PER_SYMBOL` + the /061 leftover revert
   (`vol_scale_floor_per_symbol={}`, see below) + `label_mode="triple_barrier"`
   revert (see below) + ITERATION_LABEL.
4. **A different label DEFINITION at the structural level** — per-symbol barrier
   GEOMETRY, not a universal multiplier knob. Cycle 1 exhausted the UNIVERSAL
   ATR-multiplier knob (/065 widening, /042 tightening — both failed). Per-symbol
   asymmetry is a structurally distinct axis: it does not move all symbols the
   same way; it calibrates each symbol's barrier to its own volatility.
5. AXIS A and AXIS B are genuinely dominated/closed (see above) — AXIS C is the
   only candidate with a fresh, EDA-surfaced bottleneck.

### HONEST CAVEATS (must be pre-registered in the brief)

- **All recalibrations widen the SL** (BCH 1.0->1.25, LDO 1.0->1.25, both also
  lower the reward:risk). SL-widening is the canonical regime-exposure failure
  mode flagged by `feedback_v3_oos_is_ratio_gate.md` (/065 SL-widening, /042
  SL-tightening, /070 CONFIRMATION all SUSPICIOUS-OOS-DOMINANT). The EDA's
  rationale is that the CURRENT barrier is pathologically SL-SATURATED (66% SL-hit)
  so a wider SL rebalances toward TP-hits — the OPPOSITE of /065 (which widened
  an already-balanced barrier). But a wider SL also means each stop-out loses
  MORE; the EDA's `directional_spread` and `exec_consistency` metrics do not
  fully capture the Sharpe impact of deeper individual losers. The brief Section 4
  MUST pre-register the OOS/IS monthly Sharpe ratio > 3.0 SUSPICIOUS gate, and
  Section 7 MUST weight NEGATIVE >= 25% per `feedback_v3_iter064_process_lessons.md`
  Rule 3.
- **LDO's directional_spread is negative across the ENTIRE grid.** The axis
  corrects the LDO barrier PATHOLOGY (SL-saturation -> balance) but does NOT
  manufacture a positive LDO label spread. The brief must NOT claim this "fixes
  LDO" — LDO's IS signal is structurally weak independent of barrier geometry.
  The honest framing: the axis improves label-economics QUALITY on BCH+LDO; it is
  not an LDO rescue.
- **One leftover-state revert the setup commit must apply.** The runner is
  currently on `label_mode="fixed_horizon"` (run_baseline_v3.py:1506, the /072
  axis) — the setup commit MUST revert it to `"triple_barrier"`. This is NOT a
  second axis: it is the REVERT of the /072 NEGATIVE axis, and the per-symbol ATR
  multipliers only take effect under the triple-barrier label path. Without the
  revert, iter-v3/073 would stack the ATR axis on top of the failed /072 label.
  NOTE on `vol_scale_floor_per_symbol={"TRXUSDT": 0.5}` (run_baseline_v3.py:1566):
  this dict is /061 state, but /071 AND /072 BOTH ran with it and both anchored
  against /060 as trade-roster-equivalent (the /071 brief change table explicitly
  lists it "unchanged"; the /071 Critic certified that framing clean). It is the
  ESTABLISHED cycle-2 EXPLORATION baseline state — iter-v3/073 KEEPS it. Reverting
  it would deviate from the /071/072 baseline and introduce a SECOND axis.
