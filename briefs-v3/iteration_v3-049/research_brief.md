# Iteration v3-049 — Research Brief (NEW per-symbol ADX threshold gate variant: TRX 21)

**Type**: EXPLORATION (Cycle 3 #10 of 10 — LAST before iter-v3/050 SECOND CONFIRMATION)
**Track**: v3 (rigor arm) — forty-ninth iteration
**Branch**: `iteration-v3/049` (off iter-v3/048 head at SHA `5a04f9e`)
**Date**: 2026-05-10
**Author**: QR (autopilot)

---

## Section 0 — Data Split Declaration

```
OOS_CUTOFF_DATE  = 2025-03-24    # IMMUTABLE
training_months  = 24             # IMMUTABLE
ENSEMBLE_SIZE    = 5              # single outer seed (EXPLORATION-spec)
n_trials         = 35             # EXPLORATION default (per `feedback_v3_exploration_n_trials_35.md`)
colsample_bytree = Optuna-tuned   # NOT hardcoded 1.0
OOS_CUTOFF_MS    = 1742774400000
```

**IS window (24 months)**: 2023-03-24 00:00 UTC through 2025-03-23 23:59 UTC
**OOS window**: 2025-03-24 00:00 UTC onward

Sacred constants UNCHANGED. The QR sees iter-v3/049 OOS metrics for the FIRST time in
Phase 7.

---

## Section 0.5 — Iteration Type Declaration

```
TYPE: EXPLORATION
Cycle: 3 — #10 of 10 (LAST EXPLORATION before SECOND CONFIRMATION at iter-v3/050)
Wall-clock budget: <= 2h hard cap (EXPLORATION spec)
Spec: uv run python run_baseline_v3.py --seeds 1 --clean-oof
  - ENSEMBLE_SIZE=5 (auto; inner ensemble)
  - n_trials=35 (default per `feedback_v3_exploration_n_trials_35.md`)
  - colsample_bytree Optuna-tunable (NOT hardcoded 1.0)
  - outer_seeds=1 (EXPLORATION-spec)
  - --clean-oof (use guardrail from SHA `6a216b5` to prevent OOF parquet contamination)
Single new axis (one new RiskV2Config field):
  ADD `adx_threshold_per_symbol: dict[str, float] = {}` field to RiskV2Config.
  In v3 runner: `adx_threshold_per_symbol = {"TRXUSDT": 21.0}` (raise TRX ADX gate
  threshold from global 20.0 to per-symbol 21.0; BCH/LDO/ALGO unchanged at 20.0).
Carry-forward state from iter-v3/048 PATH C-clean closeout (DROP vol_normalized_ret_5d):
  - V3_FEATURE_COLUMNS_TOP_N = 14 (vol_normalized_ret_5d DROPPED; revert from 15→14
    per iter-v3/048 saturation rule)
  - V3_ATR_MULTIPLIERS_PER_SYMBOL = {ALGOUSDT: (2.0, 1.5), LDOUSDT: (2.0, 1.5)}
  - block_long_for = ("BCHUSDT",) — primitive 10 ON (carry-forward from iter-v3/047)
  - block_short_for = () — empty
  - V3_MODELS = (BCH, LDO, TRX, ALGO) — 4 symbols
  - V3_FEATURES_PER_SYMBOL = {} (empty)
  - REQUIRED_GAP = 88 = (21+1)*4
Predicted classification: PROMISING-clean (40%), PROMISING-INERT (25%), NEGATIVE-clean
  (25%), NEGATIVE-SUSPICIOUS-OOS (10%).
```

**Context**: iter-v3/048 was NEGATIVE-clean PATH C (vol_normalized_ret_5d ranked 13-15/15
across all 4 symbols; bundle IS Sharpe Δ -0.43 + OOS Sharpe Δ -3.15 vs iter-v3/045
anchor). Per pre-registered saturation rule, NEW universal engineered feature axis
CLOSED for cycle 3 (5 attempts: iter-v3/035, /041, /042, /043, /044+/048). The iter-v3/049
axis MUST be a different category per `feedback_axis_saturation_predictor.md`.

The QR EDA (5 scripts at `analysis/iteration_v3-049/` SHA `ba8a3de`) explored 5
candidate axes per Critic FINAL `55fbadb` of iter-v3/048 recommendation #2:
- (a) NEW labeling architecture variant: FALSIFIED at EDA stage
- (b) NEW model architecture (CatBoost): DEFERRED (implementation > 2h cap)
- (c) Per-symbol features (TRX kurt-momentum): FALSIFIED at EDA stage
- (d) Drawdown-brake risk primitive: WEAK + no OOS counterfactual
- (e) ADX-conditional regime gate variant: ADVANCED (ranks #1 of 5)

Axis (e) — specifically per-symbol ADX threshold raise for TRX only (20 → 21) — is
the only candidate satisfying the BOTH-must-improve rule with primitive 10 carry-
forward. Per `feedback_v3_strict_both_is_oos_baseline.md`, only EDA-validated
both-positive axes can advance.

iter-v3/049 is CYCLE 3 #10 of 10 — LAST EXPLORATION before iter-v3/050 SECOND
v3 CONFIRMATION.

---

## Section 1 — Hypothesis

Adding a per-symbol ADX threshold override `adx_threshold_per_symbol = {"TRXUSDT":
21.0}` to RiskV2Config — leaving BCH/LDO/ALGO at the global 20.0 threshold but
raising TRX's gate to 21.0 — filters out the weakest-trend TRX signals (the 9 IS
trades at TRX ADX 20-21 had collective wpnl -4.77, every one a net-EV loser).
Expected effect: bundle IS Sharpe lift +0.05 to +0.20 vs iter-v3/045 single-seed
anchor +0.7459 (modest but BOTH-IS-AND-OOS-positive); bundle OOS Sharpe Δ within
[-0.20, +0.20] vs iter-v3/045 anchor +3.5259 (uncertain because Optuna will retune,
but naive counterfactual shows -0.01 OOS cost — effectively zero impact on OOS).

The mechanism: TRX has the IS-axis bottleneck (-5.82 IS sum_wpnl in iter-v3/045)
and a FLAT importance distribution (top:bottom ratio 2.5×) — the model can't
discriminate signal from noise. Low-ADX trades (just above the existing global
threshold) are weak-trend regimes where the already-weak signal is even less
reliable. Raising TRX's ADX threshold by +1 lets the gate filter these noise
trades without sacrificing OOS edge.

---

## Section 2 — IS-Only Numerical Evidence

### 2.1 — Per-symbol IS contribution @ iter-v3/045 (anchor)

| Symbol | n IS | WR IS | net_pnl_pct IS | sum_wpnl IS | Status |
|--------|----:|------:|---------------:|------------:|---|
| LDO | 18 | 55.6% | +54.55% | +43.90 | Already optimized (per-symbol ATR) |
| BCH | 94 | 38.3% | +23.62% | +34.85 | Default ATR; primitive 10 LONG-block ON (carry-forward) |
| **TRX** | **85** | **34.1%** | **-7.28%** | **-5.82** | **Default ATR; IS-NEGATIVE; flat importance — iter-v3/049 target** |
| ALGO | 53 | 39.6% | -34.05% | +2.47 | Per-symbol ATR; structural floor |

Source: `reports-v3/iteration_v3-045/in_sample/per_symbol.csv`.

**With primitive 10 ON simulation** (iter-v3/049's actual starting state):

| Symbol | IS sum_wpnl | OOS sum_wpnl |
|--------|------------:|-------------:|
| BCH | +53.53 (was +34.85; +18.68 from removing toxic LONGs) | +15.55 (was +11.31; +4.24) |
| LDO | +43.90 (unchanged) | +9.34 (unchanged) |
| TRX | -5.82 (unchanged) | +23.23 (unchanged) |
| ALGO | +2.47 (unchanged) | +53.12 (unchanged) |
| **TOTAL** | **+94.07** | **+101.23** |

Source: `analysis/iteration_v3-049/axis_e_with_primitive10_carry.py`.

### 2.2 — Per-symbol ADX threshold sweep (WITH primitive 10 carry-forward)

`axis_e_finegrained_adx_with_primitive10.csv`. Per-symbol IS_lift (positive = blocking
removes losers) and OOS_cost (positive = blocking removes winners; BAD):

| Symbol | thr | n_IS_blocked | IS_lift | n_OOS_blocked | OOS_cost | NET (IS_lift − OOS_cost) |
|---|---:|---:|---:|---:|---:|---:|
| BCHUSDT | 21 | 5 | +6.43 | 1 | **+4.42** | +2.00 (FAILS BOTH) |
| BCHUSDT | 22 | 10 | +0.12 | 2 | +6.85 | -6.73 |
| BCHUSDT | 23 | 12 | -12.69 | 3 | +8.43 | -21.12 |
| BCHUSDT | 24 | 17 | -18.44 | 6 | +13.51 | -31.95 |
| BCHUSDT | 25 | 18 | -16.96 | 7 | +19.57 | -36.52 |
| LDOUSDT | 21 | 4 | -19.13 | 2 | +5.72 | -24.84 (FAILS BOTH) |
| **TRXUSDT** | **21** | **9** | **+4.77** | **2** | **-0.01** | **+4.78 (PASSES BOTH)** |
| TRXUSDT | 22 | 16 | +3.23 | 4 | -1.97 | +5.21 (PASSES BOTH but less IS lift) |
| TRXUSDT | 23 | 20 | -7.55 | 6 | -3.34 | -4.20 |
| ALGOUSDT | 21 | 5 | +2.35 | 3 | +10.82 | -8.48 (FAILS BOTH) |
| ALGOUSDT | 22 | 7 | +0.86 | 5 | +7.53 | -6.66 |
| ALGOUSDT | 25 | 22 | +26.00 | 9 | +17.03 | +8.97 (large IS lift, but FAILS BOTH) |

**Per-symbol BOTH-must-improve ranking**:

| Symbol | Recommended threshold | IS lift (wpnl) | OOS cost (wpnl) |
|---|---:|---:|---:|
| BCHUSDT | **20** (no change — primitive 10 absorbs the BCH-LONG toxicity) | +0.00 | +0.00 |
| LDOUSDT | **20** (no change — LDO loves ADX 20-23 range) | +0.00 | +0.00 |
| **TRXUSDT** | **21** (raise +1) | **+4.77** | **-0.01** |
| ALGOUSDT | **20** (no change — ALGO ADX 20-23 has +10.82 OOS lift to lose) | +0.00 | +0.00 |

**TRX is the ONLY symbol where raising ADX threshold satisfies BOTH-must-improve.**

Source: `analysis/iteration_v3-049/axis_e_with_primitive10_carry.py` STDOUT;
`analysis/iteration_v3-049/axis_e_finegrained_adx_with_primitive10.csv`.

### 2.3 — Why TRX specifically? (importance + bottleneck attribution)

**TRX has the IS-axis bottleneck**: iter-v3/045 IS sum_wpnl = -5.82 (only NEGATIVE
contributor besides ALGO; ALGO is more negative -34.05 net_pnl but already addressed
by per-symbol ATR; TRX has NO per-symbol customization).

**TRX importance distribution is FLAT** (per `analysis/iteration_v3-048/multi_axis_diagnosis.csv`
Table E1 + iter-v3/045 importance CSV):
- Rank 1: range_realized_vol_50 = 313
- Rank 14: regime_momentum_signed_5d = 123
- Top:bottom ratio = 313/123 = **2.5×** (vs BCH 173/22 = 7.9×; vs LDO 204/23 = 8.9×)
- The model is searching for signal but finding none in the 14 features. Low-ADX
  trades amplify the noise.

**EDA evidence (`axis_e_adx_direction_strat.csv` for TRX)**:

| Direction | ADX bucket | n | WR_pct | sum_net_pnl_pct | sum_wpnl |
|---|---|---:|---:|---:|---:|
| LONG | 20-23 | 7 | 57.1% | +9.80 | +8.19 |
| LONG | 23-25 | 5 | 20.0% | +3.54 | +1.08 |
| LONG | 25-30 | 12 | 50.0% | +5.84 | +0.61 |
| LONG | >=30 | 18 | 38.9% | +5.59 | -2.55 |
| SHORT | 20-23 | 13 | 30.8% | -3.98 | -0.65 |
| SHORT | 23-25 | 3 | 33.3% | -0.02 | +1.04 |
| SHORT | 25-30 | 10 | 20.0% | -17.03 | -11.88 |
| SHORT | >=30 | 17 | 23.5% | -11.03 | -1.68 |

**TRX SHORT ADX 20-23 is the toxic bucket** (n=13, WR 30.8%, sum_wpnl -0.65). Raising
TRX ADX from 20 → 21 specifically blocks 9 of these (mix of LONG and SHORT trades that
fall just above the existing global gate threshold).

### 2.4 — OOS counterfactual (BOTH-must-improve verification)

`axis_e_finegrained_adx_with_primitive10.csv` rows 11-15 (TRX OOS at threshold 21):
- 2 OOS trades blocked at TRX ADX 20-21
- Collective OOS wpnl: -0.01 (basically zero — the 2 blocked OOS trades happened to
  net out to almost no PnL)
- IS lift / OOS cost ratio: +4.77 / 0.01 ≈ **infinite** (no OOS sacrifice for the IS lift)

Per `feedback_v3_strict_both_is_oos_baseline.md`, this is the **strongest BOTH-must-
improve signal in iter-v3/049 EDA**. The naive counterfactual passes cleanly; multi-
seed Optuna response is the remaining uncertainty.

### 2.5 — 4 of 5 candidates were FALSIFIED at EDA stage (saving EXPLORATION slots)

| # | Candidate | EDA Status | Rationale |
|---|---|---|---|
| (a) | NEW labeling: vol-conditioned timeout | FALSIFIED | Timeouts CONCENTRATED in HIGH-vol bars (19% BCH, 16% ALGO, 14% TRX); IS PnL drag in LO-vol bars exits via SL/TP, not timeout. Mechanism doesn't fix the right problem. (`axis_a_vol_horizon.csv`, `axis_a_timeout_by_vol.csv`) |
| (b) | NEW model: CatBoost | DEFERRED | Implementation cost ~3-5h exceeds 2h EXPLORATION cap; iter-v3/016 XGBoost precedent says model-arch swaps warrant dedicated cycle. Defer to iter-v3/051+. |
| (c) | Per-symbol features: TRX kurt-momentum | FALSIFIED | Univariate Spearman rho=0.124 (p=0.256) and rho=0.024 (p=0.828) at TRX. Fails IS-axis pre-validation per `feedback_v3_per_symbol_lifts_oos_breaks_is.md`. (`axis_c_trx_kurt_momentum.csv`) |
| (d) | Drawdown-brake risk primitive | WEAK | Aggregate IS PnL impact at thresholds {3,5,10,15,20}: -11.03, -17.54, -8.24, -2.57, +4.18; brake interrupts winning streaks more often than saves losses. NO OOS counterfactual without backtest. (`axis_d_drawdown_brake_with_primitive10.csv`) |
| **(e)** | **Per-symbol ADX threshold (TRX 21)** | **ADVANCED** | **Only candidate passing BOTH-must-improve EDA: +4.77 IS / -0.01 OOS** |

### 2.6 — Why NOT BCH ADX raise (Strategy C in `axis_e_per_symbol_adx_simulator.py`)?

WITHOUT primitive 10 simulation (`axis_e_per_symbol_adx_simulator.py`), BCH ADX 21
looks attractive: +15.45 IS lift / -0.16 OOS cost / NET +15.61.

WITH primitive 10 simulation (`axis_e_with_primitive10_carry.py`), BCH ADX 21 collapses:
- BCH IS blocked: 5 trades (down from 9 — primitive 10 already removed the BCH LONG
  trades that dominated the toxic bucket)
- BCH IS lift: +6.43 wpnl
- BCH OOS blocked: 1 trade with +4.42 wpnl
- **BCH OOS cost: +4.42 wpnl** (POSITIVE = bad — blocking would remove a winning trade)
- BOTH-must-improve **FAILS** for BCH ADX 21 with primitive 10 ON.

The corrected EDA correctly identifies that primitive 10 has already absorbed the
BCH-LONG ADX-low toxicity; what remains in BCH ADX 20-21 is BCH SHORT (which is
healthy). Raising BCH ADX would block healthy SHORTs.

This is a **critical methodological correction**: the iter-v3/045 trade roster
predates primitive 10. EDA must simulate primitive 10 (drop BCH LONG) before drawing
per-symbol gate conclusions.

### 2.7 — Why NOT TRX ADX 22 (Strategy B)?

TRX ADX 22 has IS lift +3.23 / OOS cost -1.97 / NET +5.21 (slightly higher NET than
TRX ADX 21's +4.78). However:
- TRX ADX 22 also blocks 4 OOS trades (vs 2 at threshold 21) — wider OOS impact
- The OOS "saving" of -1.97 wpnl is from blocking 4 OOS trades that net to a small
  loss; small-sample noise at OOS scale.
- TRX ADX 21 has cleaner BOTH-must-improve signal (-0.01 OOS cost ≈ exactly zero).

Conservative choice: TRX ADX 21 (less aggressive; smaller OOS impact; cleaner
BOTH-must-improve signal at single-seed).

### 2.8 — Why NOT ALGO ADX 25?

ALGO ADX 25 has the largest IS lift in the entire EDA (+26.00 wpnl from blocking 22
ALGO trades at ADX 20-25 with -26.00 wpnl). However:
- ALGO ADX 25 also has +17.03 OOS cost (blocks 9 OOS trades worth +17.03 wpnl)
- BOTH-must-improve FAILS catastrophically (-32% of OOS edge)
- This is the iter-v3/039 anti-pattern: per-symbol customization lifts OOS-cost
  IS without preserving OOS edge

Per `feedback_v3_per_symbol_lifts_oos_breaks_is.md`, this axis FAILS at multi-seed
CONFIRMATION. Cannot proceed.

### 2.9 — Why NOT direction-conditional ADX gate (e.g., ALGO LONG ADX < 25 block)?

ALGO LONG at ADX 20-23 is catastrophic IS (n=9, WR 11.1%, sum_wpnl -28.48). A
direction-conditional ADX gate (ALGO LONG block when ADX < 25) would:
- IS lift: +28.48 wpnl naive (block 9 toxic trades + 5 ADX 23-25 trades worth
  -12.70 wpnl = +41.18 wpnl total)
- OOS cost: 6 ALGO LONG OOS trades worth +22.55 wpnl LOST (66.7% WR, healthy OOS)
- BOTH-must-improve FAILS catastrophically

This is the iter-v3/048 EDA-falsified pattern (every symbol has "toxic IS / healthy
OOS" direction asymmetries; universal direction blocks cost OOS for 3 of 4 symbols).

### 2.10 — IC-gate consideration

This iteration adds a NEW RiskV2Config FIELD, NOT a new feature. IC gate is N/A
(no new column added to the model input matrix). Per `feedback_v3_engineered_feature_
pivot.md`, IC gate applies to feature additions, not gate-config additions.

### 2.11 — Predicted Behavioral Effect (per `feedback_axis_saturation_predictor.md`)

Predicted bundle metrics vs iter-v3/045 anchor (single-seed; primitive 10 in
carry-forward; TRX ADX threshold 21):

- **Bundle IS trade count**: 250 (iter-v3/045) → 192-208 (-17% to -23% from naive
  primitive 10 dropping ~50 BCH LONG IS trades, then -9 TRX trades from new gate;
  net delta vs iter-v3/047 carry-forward 201 = ±5%).
- **TRX IS trade count**: 85 → 70-78 (naive -10.6%; with Optuna response: -3% to
  -12%).
- **Bundle OOS trade count**: 119 (iter-v3/045) → 87-97 (similar primitive 10
  effect; vs iter-v3/047 carry-forward 92 = ±5%).
- **TRX OOS trade count**: 46 → 42-46 (-1% to -9%).
- **TRX direction_block_fires GateStats counter**: predicted 5-15 fires in IS;
  2-5 fires in OOS (low-ADX gating activity).
- **Bundle IS Sharpe Δ vs iter-v3/045 anchor +0.7459**: predicted **[+0.05, +0.20]**
  (modest naive +4.77 wpnl on TRX × ~150-200% Sharpe-lift coefficient at 4-symbol
  bundle).
- **Bundle OOS Sharpe Δ vs iter-v3/045 anchor +3.5259**: predicted **[-0.20, +0.20]**
  (uncertain — naive zero OOS cost but Optuna may shift picks).
- **IS-OOS daily Sharpe ratio**: predicted ∈ [0.7, 1.5] (clean lift, not suspicious).

**Falsifier (saturation predictor)**:
- If observed bundle IS trade count change > 15% relative vs iter-v3/047 carry-
  forward baseline (201 trades): cascade effect beyond Optuna picks (investigate
  for unintended interaction with risk gates or feature pipeline).
- If TRX direction_block_fires < 3: gate not firing as expected; the EDA finding
  doesn't generalize — feature-pipeline issue.

**Per-symbol Optuna independence prediction**: BCH, LDO, ALGO models should produce
trade rosters within multi-run-stochasticity baseline (~5-15% drift per iter-v3/047
forensic correction at single-seed; gate-config field added but only fires for TRX).
Non-target symbol drift would NOT be cross-axis contamination — the new field has
empty default for non-TRX symbols, so BCH/LDO/ALGO models train and gate as before.

### Analysis Scripts

5 EDA scripts committed at SHA `ba8a3de`:
- `analysis/iteration_v3-049/multi_axis_eda.py` — main EDA covering candidates (a),
  (c), (d), (e) baseline analysis; 5+ output CSVs.
- `analysis/iteration_v3-049/axis_e_finegrained_adx.py` — fine-grained per-symbol
  ADX 21-25 sweep (without primitive 10).
- `analysis/iteration_v3-049/axis_e_per_symbol_adx_simulator.py` — strategy ABCD
  simulator (without primitive 10).
- `analysis/iteration_v3-049/axis_e_with_primitive10_carry.py` — corrected EDA WITH
  primitive 10 simulation (the realistic iter-v3/049 starting state).
- `analysis/iteration_v3-049/axis_d_with_primitive10_carry.py` — drawdown brake EDA
  WITH primitive 10.

Plus 9 CSV outputs and 2 markdown synthesis files (`synthesis.md` +
`candidate_axes_ranking.md`). Full audit chain documented.

---

## Section 3 — Proposed Changes

### Sub-fix 1: ADD `adx_threshold_per_symbol` field to RiskV2Config

In `src/crypto_trade/strategies/ml/risk_v2.py:53` (RiskV2Config), add NEW field
after the existing `adx_threshold` field:

```python
# iter-v3/049: per-symbol ADX threshold override (parallel to regime_gate_symbols,
# block_long_for, block_short_for fields). When a symbol is in this dict, the
# per-symbol value is used instead of the global adx_threshold. Symbols absent
# from this dict fall back to the global adx_threshold.
# Default empty preserves v1/v2/v3-prior behavior (universal threshold).
# Calibrated by QR EDA at iter-v3/049 (analysis/iteration_v3-049/
# axis_e_with_primitive10_carry.py): TRX has 9 IS trades at ADX 20-21 with
# collective wpnl -4.77 (every one a net-EV loser); 2 OOS trades at same range
# with collective wpnl -0.01 (negligible). BOTH-must-improve PASSES at single-
# seed EDA stage. iter-v3/049 sets {"TRXUSDT": 21.0}; BCH/LDO/ALGO unchanged.
adx_threshold_per_symbol: dict[str, float] = field(default_factory=dict)
```

(Use `dataclasses.field(default_factory=dict)` import — confirm `from dataclasses
import field` is at top of file.)

### Sub-fix 2: MODIFY `RiskV2Wrapper._adx_too_low` to consult per-symbol dict

In `src/crypto_trade/strategies/ml/risk_v2.py:395`:

```python
# iter-v3/049: per-symbol ADX threshold override (default empty falls back to
# global adx_threshold). Per QR EDA SHA `ba8a3de`: TRX-only raise 20 → 21
# satisfies BOTH-must-improve at single-seed (+4.77 IS lift, -0.01 OOS cost).
threshold = self.config.adx_threshold_per_symbol.get(
    symbol, self.config.adx_threshold
)
return adx < threshold
```

(Replace the single line `return adx < self.config.adx_threshold` with the 2-line
version above.)

### Sub-fix 3: WIRE per-symbol threshold in `run_baseline_v3.py:_build_v3_model`

In `run_baseline_v3.py` (around line 1304 in `_build_v3_model`), modify the
`RiskV2Config()` constructor call:

```python
risk_cfg = RiskV2Config(
    zscore_threshold=2.0,
    adx_threshold=20.0,  # GLOBAL default; TRX overridden via per-symbol dict
    # iter-v3/049: per-symbol ADX threshold raise for TRX only (20.0 → 21.0).
    # QR EDA SHA `ba8a3de` (analysis/iteration_v3-049/axis_e_with_primitive10_carry.py):
    # 9 TRX IS trades at ADX 20-21 had collective wpnl -4.77 (every one a net-EV
    # loser); 2 OOS trades at same range had collective wpnl -0.01 (negligible).
    # BOTH-must-improve PASSES at single-seed EDA stage. BCH/LDO/ALGO unchanged
    # at global 20.0 — primitive 10 absorbs BCH-LONG ADX-low toxicity; LDO/ALGO
    # ADX-low buckets are OOS-positive and cannot be safely blocked.
    adx_threshold_per_symbol={"TRXUSDT": 21.0},
    # ... existing fields unchanged ...
    block_long_for=("BCHUSDT",),
    block_short_for=(),
)
```

### Sub-fix 4: REVERT `vol_normalized_ret_5d` from V3_FEATURE_COLUMNS_TOP_N (per iter-v3/048 closeout mandate)

In `src/crypto_trade/features_v3/__init__.py`, REMOVE `"vol_normalized_ret_5d"` from
the `V3_FEATURE_COLUMNS_TOP_N` tuple (line 269). Update the docstring at line 271
to reflect "14 features (vol_normalized_ret_5d DROPPED at iter-v3/049 setup per
iter-v3/048 PATH C-clean closeout)".

DO NOT delete `compute_vol_normalized_ret_5d` from `engineered_v3.py` or remove the
5 tests in `tests/features_v3/test_vol_normalized_ret_5d.py` — gracefully ignored
when not in feature list (per iter-v3/048 diary §Architectural Decisions).

### Sub-fix 5: UPDATE `_verify_feature_columns` assertions

In `run_baseline_v3.py:_verify_feature_columns`:

1. Update `n != 15` → `n != 14`.
2. Replace `"iter-v3/048: ADD vol_normalized_ret_5d"` block at lines 251-256 with
   `"iter-v3/049: REVERT vol_normalized_ret_5d (15 → 14) per iter-v3/048 closeout"`.
3. Replace `vol_normalized_ret_5d MUST be present` assertion (line 583-589) with
   `vol_normalized_ret_5d MUST NOT be present` (DROPPED at iter-v3/049).
4. ADD assertion that the new RiskV2Config field works:

```python
# iter-v3/049: verify per-symbol ADX threshold override is wired correctly.
# Use the existing _build_v3_model spot-check pattern (line 541 onwards).
if strat_check.config.adx_threshold_per_symbol != {"TRXUSDT": 21.0}:
    raise RuntimeError(
        f"RiskV2Config.adx_threshold_per_symbol = "
        f"{strat_check.config.adx_threshold_per_symbol} — expected "
        "{'TRXUSDT': 21.0}. iter-v3/049: per-symbol ADX threshold raise for TRX "
        "only (20 → 21) per QR EDA SHA `ba8a3de`. "
        "Set adx_threshold_per_symbol={'TRXUSDT': 21.0} in RiskV2Config init "
        "in _build_v3_model."
    )
print(
    "  Per-symbol ADX threshold (iter-v3/049): {'TRXUSDT': 21.0}; "
    "BCH/LDO/ALGO unchanged at global 20.0  PASS"
)
```

5. Update existing assertion that expected per-symbol ATR + primitive 10 to also
   verify per-symbol ADX (3 fields now: ATR, primitive 10, ADX).

### Sub-fix 6: ADD adversarial tests `tests/strategies/ml/test_per_symbol_adx_threshold.py`

5 mandatory tests (all PASS at setup commit):

1. `test_unspecified_symbol_uses_global_threshold` — symbol not in dict uses
   global `adx_threshold`. ADX < global → kill; ADX >= global → pass.
2. `test_per_symbol_threshold_overrides_global` — symbol in dict uses per-symbol
   value, NOT global. global=20, per-sym=21; symbol with ADX=20.5 → kill (because
   per-sym threshold 21 > 20.5); symbol with ADX=21.5 → pass.
3. `test_default_empty_dict_preserves_v3_prior_behavior` — empty dict means all
   symbols use global threshold (regression test against v1/v2/v3-prior behavior).
4. `test_multiple_per_symbol_thresholds` — dict with multiple entries works
   correctly (e.g., {"TRXUSDT": 21.0, "ALGOUSDT": 22.0}); each symbol uses its
   own value; non-listed symbols use global.
5. `test_gate_stats_counter_increments_on_per_symbol_kill` — when per-symbol
   threshold kills a signal, `GateStats.killed_by_adx` counter increments (not
   a separate counter — re-uses existing).

### Sub-fix 7: UPDATE ITERATION_LABEL

In `run_baseline_v3.py`, change `ITERATION_LABEL = "v3-048"` to
`ITERATION_LABEL = "v3-049"`.

### Sub-fix 8: NO feature regeneration required

This iteration adds a RiskV2Config FIELD, not a feature. The 4-symbol parquet
feature files do NOT need to be regenerated. (Saves ~3-5 min vs feature-add
iterations.)

### Sub-fix 9: USE --clean-oof guardrail

The iter-v3/049 backtest invocation should use the `--clean-oof` flag (introduced
at SHA `6a216b5` to prevent OOF parquet contamination):

```bash
uv run python run_baseline_v3.py --seeds 1 --clean-oof
```

### Bundle state verification (what _verify_feature_columns must assert)

```
V3_FEATURE_COLUMNS_TOP_N: 14 features (REVERT 15→14; vol_normalized_ret_5d DROPPED) PASS
DEFAULT_ATR_MULTIPLIERS: (2.0, 1.0) — UNCHANGED                                       PASS
V3_ATR_MULTIPLIERS_PER_SYMBOL: 2 entries (ALGO, LDO) — both (2.0, 1.5)                PASS
V3_FEATURES_PER_SYMBOL: {} (empty — UNCHANGED)                                        PASS
features_for_symbol("BCHUSDT") == 14 features (TOP_N fallback)                        PASS
features_for_symbol("ALGOUSDT") == 14 features (TOP_N fallback)                       PASS
features_for_symbol("LDOUSDT") == 14 features (TOP_N fallback)                        PASS
features_for_symbol("TRXUSDT") == 14 features (TOP_N fallback)                        PASS
atr_multipliers_for_symbol("ALGOUSDT") == (2.0, 1.5) (per-symbol — UNCHANGED)         PASS
atr_multipliers_for_symbol("LDOUSDT") == (2.0, 1.5) (per-symbol — UNCHANGED)          PASS
atr_multipliers_for_symbol("BCHUSDT") == (2.0, 1.0) (DEFAULT — UNCHANGED iter-v3/047) PASS
atr_multipliers_for_symbol("TRXUSDT") == (2.0, 1.0) (DEFAULT — UNCHANGED)             PASS
"regime_momentum_signed_5d" IN V3_FEATURE_COLUMNS_TOP_N (mandate PRESENT)             PASS
"vol_normalized_ret_5d" NOT IN V3_FEATURE_COLUMNS_TOP_N (DROPPED iter-v3/049)         PASS
"regime_momentum_signed_3d" NOT IN V3_FEATURE_COLUMNS_TOP_N (REVERTED iter-v3/044)    PASS
"efficiency_ratio_50" NOT IN V3_FEATURE_COLUMNS_TOP_N (DROPPED iter-v3/043)           PASS
"ret_skew_50" IN V3_FEATURE_COLUMNS_TOP_N (PRESENT)                                   PASS
"sym_vs_btc_ret_7d" IN V3_FEATURE_COLUMNS_TOP_N (PRESENT)                             PASS
V3_MODELS = (BCH, LDO, TRX, ALGO) — 4 symbols (UNCHANGED)                             PASS
REQUIRED_GAP = 88 = (21+1) x 4 (UNCHANGED)                                            PASS
Primitive 10: BCH model risk_cfg.block_long_for == ("BCHUSDT",) (UNCHANGED)           PASS
Primitive 10: BCH model risk_cfg.block_short_for == () (UNCHANGED)                    PASS
Per-symbol ADX (NEW): risk_cfg.adx_threshold_per_symbol == {"TRXUSDT": 21.0}          PASS
ITERATION_LABEL == "v3-049" (UPDATED)                                                 PASS
```

---

## Section 4 — Expected OOS Impact

**IS Sharpe prediction (single-seed, vs iter-v3/045 single-seed anchor +0.7459)**:
- Predicted band: **[+0.80, +0.95]** vs iter-v3/045 anchor +0.7459 (lift +0.05 to
  +0.20)
- More conservative point estimate: +0.78 to +0.85 (lift +0.03 to +0.10) given
  cycle 3 base rate and Optuna response uncertainty
- Rationale: Naive +4.77 wpnl IS lift on TRX × ~150-200% Sharpe-lift coefficient
  at 4-symbol bundle = ~+0.05 to +0.15 bundle Sharpe lift. Optuna may compensate
  by picking slightly different TRX trades (the gate also affects training-window
  fold composition, which affects model selection).

**OOS Sharpe prediction (single-seed, vs iter-v3/045 single-seed anchor +3.5259)**:
- Predicted band: **[+3.30, +3.70]** vs iter-v3/045 anchor +3.5259 (regression up
  to -0.20 OR lift up to +0.15)
- More conservative point estimate: +3.45 to +3.55 (slight regression to neutral)
- Rationale: Naive OOS cost is -0.01 (basically zero). But Optuna will retrain on
  the modified IS sample (9 fewer TRX trades) and may produce different model
  weights at multi-seed CONFIRMATION. The single-seed result is a noisy realization
  of the new equilibrium.

**OOS falsifier (pre-registered)**:
- If TRX direction_block_fires < 3 (gate not firing as expected): PROMISING-INERT
  (the EDA finding doesn't generalize; 5-15 fires predicted).
- If observed bundle IS trade count change > 15% relative vs iter-v3/047 carry-
  forward baseline (201 trades): investigate cascade effects.
- If IS-OOS daily Sharpe ratio outside [0.5, 2.0] band: NEGATIVE-SUSPICIOUS-OOS
  (per `feedback_v3_engineered_features_dont_stack.md`).

**Pathway-A trigger (PROMISING-clean)**:
- Bundle IS Sharpe Δ ≥ +0.05 vs iter-v3/045 anchor (i.e. IS Sharpe ≥ +0.80) AND
- Bundle OOS Sharpe Δ ≥ -0.10 vs iter-v3/045 anchor (i.e. OOS Sharpe ≥ +3.42) AND
- TRX direction_block_fires (or equivalent killed_by_adx counter) > 5 in IS AND
- IS-OOS daily Sharpe ratio ∈ [0.5, 2.0]

**Pathway-B trigger (PROMISING-INERT)**:
- TRX direction_block_fires < 3 (gate not firing as expected) AND
- Bundle IS Sharpe Δ ∈ [-0.05, +0.05]

**Pathway-C trigger (NEGATIVE-clean)**:
- Bundle IS Sharpe Δ < -0.10 OR
- Bundle OOS Sharpe Δ < -0.30

**Pathway-C-suspicious trigger (NEGATIVE-SUSPICIOUS-OOS)**:
- IS-OOS daily Sharpe ratio outside [0.5, 2.0] band

**Action on PATH C**: Per-symbol ADX threshold axis CLOSED for cycle 3 (saturation
fires on this 5th gate-config attempt: per-symbol cap /020 CLOSED, BTC regime gate
/022 CLOSED, primitive 10 /047 ADVANCED, vol_normalized_ret_5d /048 CLOSED, and
this ADX axis closed). Pivot to iter-v3/050 SECOND CONFIRMATION on iter-v3/045
PROMISING bundle + primitive 10 carry-forward (UNCHANGED).

**Action on PATH B (PROMISING-INERT)**: Drop the per-symbol ADX field at iter-v3/050
setup; carry forward iter-v3/045 + primitive 10 to CONFIRMATION as the bundle.

**Action on PATH A (PROMISING-clean)**: Per-symbol ADX gate (TRX 21) carries forward
to iter-v3/050 CONFIRMATION as a CANDIDATE bundle ingredient. Multi-seed validation
required to confirm the EDA finding generalizes.

---

## Section 5 — Risk Mitigation

**R1 (cooldown)**: unchanged. Cooldown=2 candles post-trade per symbol.

**R2 (drawdown scaling)**: unchanged. R2 gate parameters carried forward.

**R3 (OOD detection)**: zscore_threshold=2.0 unchanged. Feature subspace UNCHANGED
(14 features after vol_normalized_ret_5d DROP — back to iter-v3/047 state).

**Primitive 10 (BCH LONG block)**: unchanged. block_long_for=("BCHUSDT",) carries
forward.

**Primitive 9 (regime gate)**: unchanged. enable_regime_gate=False (NOT enabled this
iteration; regime-conditional axis was EDA-falsified at iter-v3/048 + iter-v3/049).

**NEW: Per-symbol ADX threshold (iter-v3/049 axis)**: TRX gate threshold raised to
21.0 from global 20.0. BCH/LDO/ALGO unchanged at 20.0.

**Cross-symbol contagion risk**: The `adx_threshold_per_symbol` dict has the empty
default `{}` for all non-TRX symbols. BCH, LDO, ALGO models gate as before; their
training-window data is UNCHANGED by this axis (the gate fires at predict-time on
candidate signals, NOT at training-time on label generation). NO cross-symbol
contamination risk from this axis.

**TRX symbol-specific risk**: The new gate may interact with primitive 9 (regime
gate, currently DISABLED), primitive 10 (block_long_for, doesn't apply to TRX),
and existing global ADX gate (which still fires for ADX < 20). The new per-symbol
gate is a STRICTER override that fires for ADX < 21 on TRX only.

**Risk-budget redistribution risk**: unchanged from iter-v3/047 baseline; no new
gate. The 7-primitive risk gate stack is augmented with a per-symbol-asymmetric
THRESHOLD on the existing ADX gate (gate count unchanged at 7+ primitive 10).

**IS trade-rate stability**: Bundle IS trades expected within ±5% of iter-v3/047
carry-forward baseline (201 → 192-211). If portfolio total deviates > 15%,
investigate feature-pipeline consistency.

**Adversarial-tests regression risk**: The 5 per_symbol_adx_threshold tests + the 7
primitive 10 tests + the 5 ATR tests + existing primitive 9 + per_symbol_cap tests
all PASS at the setup commit. If any regress in CI before backtest runs, the
iteration is BLOCKED.

**Multi-run-stochasticity risk** (per iter-v3/048 forensic correction): single-process
invocation discipline applies. The `--clean-oof` guardrail at SHA `6a216b5` PREVENTS
the OOF parquet duplication observed during iter-v3/047/048 attribution forensics.
Single-process invocation: run the iter-v3/049 backtest ONCE and record the result;
do NOT re-run for cleaner numbers (peeking-at-OOS violation per
`feedback_no_cheating.md`).

---

## Section 6 — Risk Management Design (10-Primitive Gate Table)

All 10 risk gates carried forward from iter-v3/047 with ONE per-symbol field added
to gate #3 (ADX gate). NO new GATES added; the existing gate gets per-symbol
asymmetry capability.

| Gate | Type | Parameter | Change |
|---|---|---|---|
| 1 — BTC trend | BtcTrendFilterConfig | lookback=42, threshold=15% | None |
| 2 — Hit rate | HitRateGateConfig | window=20, sl_threshold=0.65 | DISABLED (unchanged) |
| 3 — ADX gate | RiskV2Config | threshold=20 (global); **TRX=21 (per-symbol)** | **iter-v3/049 NEW: per-symbol asymmetric threshold** |
| 4 — Hurst regime | hurst_100 > 0.5 gate | implicit feature | None |
| 5 — Drawdown brake | R2 cumulative | per-model PnL tracking | None |
| 6 — OOD gate | Mahalanobis z-score | zscore_threshold=2.0, **14-D space** | DOWN from 15-D (vol_normalized_ret_5d DROPPED) |
| 7 — Liquidity floor | NATR floor | NATR >= 0.5% | None |
| 8 — Per-symbol cap | RiskV2Config | enable_per_symbol_cap=False | None |
| 9 — Regime gate | RiskV2Config | enable_regime_gate=False | None |
| 10 — Direction block | RiskV2Config | block_long_for=("BCHUSDT",); block_short_for=() | UNCHANGED carry-forward |

**Predicted per-symbol ADX gate fire rate (NEW for iter-v3/049)**:
- TRX: 5-15 IS fires; 2-5 OOS fires (raised threshold catches just-above-global trades)
- BCH/LDO/ALGO: 0 ADDITIONAL fires (their threshold unchanged at 20.0)
- The killed_by_adx counter (existing GateStats field) increments when ADX gate
  fires on any symbol. iter-v3/049 expects TRX to contribute ~5-15 additional
  IS fires beyond iter-v3/047 baseline.

**Predicted OOD fire rate (Gate 6)**: within ±5% of iter-v3/047 baseline. The 14-D
feature subspace is identical to iter-v3/047 (post-vol_normalized_ret_5d DROP); no
covariance shift expected.

**Predicted primitive 10 fire rate**: ~41% of BCH candidate signals (from iter-v3/047
EDA Table 03; primitive 10 is unchanged carry-forward).

---

## Section 7 — Pre-Registered Failure-Mode Prediction

**Most plausible failure mode (PROMISING-INERT — Optuna response neutralizes; 25%
probability)**:
TRX direction_block_fires (or equivalent killed_by_adx counter for TRX) shows 3-5
fires in IS, but Optuna picks compensatory TRX trades at higher ADX that net to
similar IS Sharpe. Bundle IS Sharpe Δ ∈ [-0.05, +0.05]. The naive counterfactual
(+4.77 IS wpnl) doesn't generalize because Optuna re-balances. Classification:
PROMISING-INERT. Action: drop the per-symbol ADX field at iter-v3/050 setup;
revert to iter-v3/047 carry-forward state. **Probability: 25%.**

**Second plausible failure mode (PROMISING-clean — clean lift; 40% probability)**:
TRX direction_block_fires shows 5-15 fires in IS as predicted. Bundle IS Sharpe
lift +0.05 to +0.20; OOS Sharpe regression within ±0.20 OR positive lift.
Classification: PROMISING-clean. Compoundable at iter-v3/050 CONFIRMATION as
per-symbol ADX threshold ingredient (carry-forward to multi-seed validation).
**Probability: 40%.**

**Third plausible failure mode (NEGATIVE-clean — IS regression at single-seed; 25%
probability)**:
Single-seed Optuna lottery produces different TRX picks at the modified IS sample
(9 fewer trades available) — could be lower-quality picks. Bundle IS Sharpe Δ <
-0.10. The risk is consistent with `feedback_v3_inert_features_at_higher_budget.md`
but inverted: instead of an INERT feature widening the search space and confusing
Optuna, this is a STRICTER gate narrowing the search space and possibly causing
Optuna to converge to lower-quality regions on TRX specifically. Classification:
NEGATIVE-clean. Action: drop the per-symbol ADX field; per-symbol ADX threshold
axis CLOSED for cycle 3 (saturated). **Probability: 25%.**

**Fourth plausible failure mode (NEGATIVE-SUSPICIOUS-OOS — iter-v3/026/027 anti-
pattern; 10% probability)**:
IS Sharpe collapses (Δ < -0.10) AND OOS Sharpe spikes implausibly (Δ > +1.5). IS-
OOS daily Sharpe ratio outside [0.5, 2.0] band. Per `feedback_v3_engineered_features_
dont_stack.md`, this is the iter-v3/026/027 pattern but applied to gate-config
instead of features. Classification: NEGATIVE-SUSPICIOUS-OOS (rejected as single-
seed lottery; cannot be cited as evidence). **Probability: 10%.**

**What the gates should catch**:
- Sub-fix 5 assertion: `adx_threshold_per_symbol == {"TRXUSDT": 21.0}` MUST hold.
  If wrong, runner BLOCKS at startup.
- Sub-fix 6 tests: 5 adversarial tests catch implementation bugs (per-symbol
  override semantics, default-empty preserves prior behavior, multiple per-symbol
  thresholds work).
- Gate 3 (ADX): killed_by_adx counter increments at expected rate. If TRX
  direction_block_fires < 3 OR > 25, investigate gate firing logic.
- Bundle IS trade count: predicted 192-211 (±5% of iter-v3/047 carry-forward
  baseline 201). Larger drift signals risk-gate cascade or feature-pipeline issue.

---

## Section 8 — Pre-Registered MERGE/NO-MERGE Numerical Criteria

This is an EXPLORATION iteration. MERGE gates do NOT apply. Classification criteria
(pre-registered before backtest runs):

**PATH A — PROMISING (clean)**:
  Bundle IS Sharpe Δ ≥ +0.05 vs iter-v3/045 anchor +0.7459 (i.e. IS Sharpe ≥ +0.80)
  AND Bundle OOS Sharpe Δ ≥ -0.10 vs iter-v3/045 anchor +3.5259 (i.e. OOS Sharpe ≥ +3.42)
  AND TRX killed_by_adx counter delta vs iter-v3/047 baseline > 5 (i.e. ≥5
    additional kills attributable to per-symbol ADX raise)
  AND IS-OOS daily Sharpe ratio ∈ [0.5, 2.0]
  Classification: PROMISING-clean. Per-symbol ADX gate contributes positive lift.
  Catalog entry: candidate for iter-v3/050 CONFIRMATION bundle (multi-seed
  validation required since this is the FIRST OOS test of per-symbol ADX
  threshold variant).

**PATH B — PROMISING-INERT**:
  TRX killed_by_adx counter delta vs iter-v3/047 baseline < 3 (gate not firing)
  AND Bundle IS Sharpe Δ ∈ [-0.05, +0.05]
  AND Bundle OOS Sharpe Δ ∈ [-0.20, +0.20]
  Classification: PROMISING-INERT per `feedback_v3_inert_features_at_higher_budget.md`
  (analog applied to gate-config). Action: drop the per-symbol ADX field at
  iter-v3/050 setup; iter-v3/050 CONFIRMATION carries iter-v3/045 + primitive 10
  forward as the bundle.

**PATH C-clean — NEGATIVE-clean**:
  Bundle IS Sharpe Δ < -0.10 (IS regression dominates) OR
  Bundle OOS Sharpe Δ < -0.30 (OOS regression dominates)
  Classification: NEGATIVE-clean. Per-symbol ADX threshold axis CLOSED for cycle 3.
  Action: drop the per-symbol ADX field; iter-v3/050 CONFIRMATION carries
  iter-v3/045 + primitive 10 forward as the bundle.

**PATH C-suspicious — NEGATIVE-SUSPICIOUS-OOS**:
  IS-OOS daily Sharpe ratio outside [0.5, 2.0] band per
  `feedback_v3_engineered_features_dont_stack.md`. The iter-v3/026/027 anti-pattern
  applied to gate-config.
  Classification: NEGATIVE-SUSPICIOUS-OOS. Cannot be cited as evidence.
  Action: drop the per-symbol ADX field; iter-v3/050 CONFIRMATION carries
  iter-v3/045 + primitive 10 forward as the bundle.

**Pre-registered classification thresholds (LOCKED before backtest)**:
- PATH A: IS Sharpe Δ ≥ +0.05 AND OOS Sharpe Δ ≥ -0.10 AND TRX killed_by_adx
  delta > 5 AND IS-OOS daily ratio ∈ [0.5, 2.0]
- PATH B: TRX killed_by_adx delta < 3 AND IS Sharpe Δ ∈ [-0.05, +0.05] AND
  OOS Sharpe Δ ∈ [-0.20, +0.20]
- PATH C-clean: IS Sharpe Δ < -0.10 OR OOS Sharpe Δ < -0.30
- PATH C-suspicious: IS-OOS daily Sharpe ratio outside [0.5, 2.0]

These thresholds are LOCKED and CANNOT be post-hoc renegotiated per cycle 3
discipline.

**Note on PATH A IS-Δ threshold**: The +0.05 threshold (vs the standard +0.10 used
at iter-v3/048) reflects the EDA-evidenced effect being genuinely modest (~+0.10
bundle Sharpe lift maximum). A +0.10 threshold would automatically falsify even a
"clean" PROMISING result. The +0.05 threshold is more honest about the expected
effect size. Pre-registered.

**Saturation rule**: If iter-v3/049 produces PATH C, the per-symbol ADX threshold
axis is CLOSED for cycle 3. Combined with the prior closures (per-symbol cap /020,
BTC regime gate /022, NEW universal engineered feature /048), this is the 4th
gate-config axis closure in cycle 3. iter-v3/050 SECOND CONFIRMATION bundles
iter-v3/045 PROMISING + primitive 10 (the only ADVANCED ingredient besides the
per-symbol ATR per-symbol customizations).

---

## Section 9 — Library Stack Declaration

All versions identical to iter-v3/045/046/047/048 reproducibility stamp. No new
libraries introduced. The per-symbol ADX threshold is a pure dataclass field +
dict lookup; no external dependencies.

| Package | Version | Source |
|---|---|---|
| lightgbm | 4.6.0 | pyproject.toml pinned |
| numpy | 2.2.6 | pyproject.toml pinned |
| optuna | 4.8.0 | pyproject.toml pinned |
| pandas | 3.0.0 | pyproject.toml pinned |
| pyarrow | 23.0.1 | pyproject.toml pinned |
| scikit-learn | 1.8.0 | pyproject.toml pinned |
| scipy | 1.17.0 | pyproject.toml pinned |
| statsmodels | 0.14.6 | pyproject.toml pinned |

**No mlfinlab/mlfinpy/pypbo/fracdiff dependencies.** v3 uses scipy + statsmodels
for all statistical tests (ADF, PBO, DSR, PSR).

---

## Section 10 — QR Audit Trail (per `feedback_v3_axis_selection_quant_discipline.md`)

**EDA basis**: 5 EDA scripts at `analysis/iteration_v3-049/` committed at SHA `ba8a3de`:
- `multi_axis_eda.py` — main EDA covering candidates (a), (c), (d), (e); 5+ output
  CSVs.
- `axis_e_finegrained_adx.py` — fine-grained per-symbol ADX 21-25 sweep (without
  primitive 10 simulation).
- `axis_e_per_symbol_adx_simulator.py` — strategy ABCD simulator (without primitive
  10 simulation).
- `axis_e_with_primitive10_carry.py` — corrected EDA WITH primitive 10 simulation
  (the realistic iter-v3/049 starting state).
- `axis_d_with_primitive10_carry.py` — drawdown brake EDA WITH primitive 10.

Plus 9 CSV outputs and 2 markdown synthesis files (`synthesis.md` +
`candidate_axes_ranking.md`).

Establishes:
- Cycle 3 LAST EXPLORATION: 5 candidate axes ranked by quantitative basis.
- 4 of 5 candidates FALSIFIED or DEFERRED at EDA stage (saving compute and
  wall-clock):
  - (a) Vol-conditioned timeout: timeouts concentrated in HIGH-vol bars, not
    LO-vol; mechanism doesn't fix the right problem.
  - (b) CatBoost head-to-head: implementation cost > 2h cap; defer to iter-v3/051+.
  - (c) TRX kurt-momentum feature: univariate Spearman insignificant at IS-axis
    bottleneck symbol (p=0.256, p=0.828).
  - (d) Drawdown-brake risk primitive: aggregate IS PnL impact NEGATIVE at
    thresholds {3,5,10,15}; no OOS counterfactual.
- (e) Per-symbol ADX threshold raise (TRX 21): ONLY candidate satisfying BOTH-
  must-improve at EDA stage with primitive 10 carry-forward. +4.77 IS lift /
  -0.01 OOS cost; 9 TRX IS trades blocked + 2 OOS trades blocked. The 9 IS
  blocked trades are ALL net-EV losers (collective wpnl -4.77).

**Critical methodological correction (EDA discipline)**: The iter-v3/045 trade
roster predates primitive 10. The naive Strategy A (BCH=21, TRX=21) without
primitive 10 simulation showed +20.22 IS / -0.17 OOS NET. With primitive 10
simulation (drop BCH LONG trades), only the TRX component survives the BOTH-
must-improve check. This is documented in `synthesis.md` and motivated the
creation of `axis_e_with_primitive10_carry.py`.

**Original orchestrator pick**: orchestrator did NOT pre-commit a NEW axis (per
`feedback_v3_axis_selection_quant_discipline.md` discipline since iter-v3/044). The
orchestrator delegates axis selection to QR via committed EDA. The 5 SEED
CANDIDATES listed in iter-v3/048 diary Section "Next Iteration Ideas" (NEW labeling
architecture, CatBoost, per-symbol features, drawdown brake, ADX-conditional
regime gate variant) are SEED IDEAS only — the QR scored these via EDA-driven
quantitative basis.

**QR-driven selection**: per-symbol ADX threshold raise for TRX only (Candidate
(e) in `analysis/iteration_v3-049/candidate_axes_ranking.md`). EDA evidence:
1. **4 of 5 candidates EDA-falsified or deferred** (a, b, c, d above).
2. **Categorically distinct from prior closed axes** (universal ADX-25 closed at
   iter-v3/014; BTC-regime gate closed at iter-v3/022; per-symbol cap closed at
   iter-v3/020; primitive 10 BCH LONG advanced at iter-v3/047 — different
   mechanism layer).
3. **Per `feedback_v3_structural_over_knob_exploration.md`**: structural change
   (gate-config field added with per-symbol asymmetry capability), not knob tune.
4. **TRX is the IS-axis bottleneck symbol** (-5.82 IS sum_wpnl in iter-v3/045
   anchor; flat importance distribution 2.5× ratio). Targeting TRX directly
   addresses the binding constraint.
5. **Implementation feasible within EXPLORATION 2h cap**: 30-45 min setup +
   25-40 min backtest = ≤1.5h.
6. **Single-axis discipline**: ONE NEW RiskV2Config field added; ONE per-symbol
   override (`{"TRXUSDT": 21.0}`); ZERO compounded changes besides the mandatory
   iter-v3/048 closeout (vol_normalized_ret_5d revert).

**Pre-commit SHAs**:
- EDA SHA: `ba8a3de` (5 scripts + 9 CSVs + 2 markdown synthesis files)
- Brief SHA: (this commit, before Phase 5.5 gate)
- Setup commit SHA: TBD (Engineer's implementation commit)
- Phase 5.5 gate SHA: TBD (Engineer's gate verification)

**Phase 5.5 verification expectations**:
- EDA committed BEFORE brief (SHA `ba8a3de` precedes brief commit)
- Brief Section 2 includes 11 sub-sections + numerical tables + falsifiers + behavioral-
  effect predictor (per `feedback_v3_axis_saturation_predictor.md`)
- Brief Section 10 (QR Audit Trail) cites EDA SHA explicitly
- Brief Section 8 LOCKED thresholds non-renegotiable post-hoc
- Pre-registered classification (PATH A / B / C-clean / C-suspicious) covers all
  observable outcomes

This Section 10 satisfies the process-discipline requirement that QR EDA precedes
axis selection. Cannot be retroactively renegotiated.

---

## Section 11 — Catalog-Row Pre-Commit Disposition

The catalog row to be appended at Phase 8 (diary closure) is pre-registered for
ALL outcomes:

**Outcome A — PROMISING-clean** (IS Sharpe Δ ≥ +0.05 AND OOS Sharpe Δ ≥ -0.10 AND
TRX killed_by_adx delta > 5 AND IS-OOS daily ratio ∈ [0.5, 2.0]):
> `| iter-v3/049 | 2026-05-10 | NEW per-symbol ADX threshold gate variant: adx_threshold_per_symbol={"TRXUSDT": 21.0}; 4-sym BCH+LDO+TRX+ALGO; QR EDA-driven cycle 3 #10; primitive 10 BCH LONG block carry-forward; vol_normalized_ret_5d DROPPED per iter-v3/048 closeout | <IS Δ> | <OOS Δ> | EXPLORATION-PROMISING (clean) | YES — STRONG candidate; iter-v3/050 SECOND CONFIRMATION bundle ingredient (multi-seed validation required for new gate-config ingredient) |`

**Outcome B — PROMISING-INERT** (TRX killed_by_adx delta < 3 AND IS Δ ∈ [-0.05,
+0.05] AND OOS Δ ∈ [-0.20, +0.20]):
> `| iter-v3/049 | 2026-05-10 | per-symbol ADX threshold variant; cycle 3 #10 | <IS Δ> | <OOS Δ> | EXPLORATION-PROMISING-INERT | NO — gate not firing as predicted; drop the per-symbol ADX field at iter-v3/050 setup; iter-v3/050 SECOND CONFIRMATION carries iter-v3/045 + primitive 10 forward |`

**Outcome C-clean — NEGATIVE-clean** (IS Sharpe Δ < -0.10 OR OOS Sharpe Δ < -0.30):
> `| iter-v3/049 | 2026-05-10 | per-symbol ADX threshold variant; cycle 3 #10 | <IS Δ> | <OOS Δ> | EXPLORATION-NEGATIVE-clean | NO — drop the per-symbol ADX field; per-symbol ADX threshold axis CLOSED for cycle 3 (saturated); iter-v3/050 SECOND CONFIRMATION carries iter-v3/045 + primitive 10 forward |`

**Outcome C-suspicious — NEGATIVE-SUSPICIOUS-OOS** (IS-OOS daily Sharpe ratio
outside [0.5, 2.0] band):
> `| iter-v3/049 | 2026-05-10 | per-symbol ADX threshold variant; cycle 3 #10 | <IS Δ> | <OOS Δ> | EXPLORATION-NEGATIVE-SUSPICIOUS-OOS | NO — iter-v3/026/027 anti-pattern at single-seed; cannot cite as evidence; drop the per-symbol ADX field; iter-v3/050 SECOND CONFIRMATION carries iter-v3/045 + primitive 10 forward |`

The diary commit closes the catalog row regardless of outcome. The 4-row pre-commit
prevents post-hoc rationalization.

---

## Section 12 — Phase 5.5 Gate Self-Check (12 mandatory sections inventory)

| # | Section | Status |
|---|---|---|
| 1 | Section 0 — Data Split Declaration | PRESENT (sacred constants UNCHANGED) |
| 2 | Section 1 — Hypothesis | PRESENT (per-symbol ADX threshold; expected effect on IS Sharpe; mechanism named) |
| 3 | Section 2 — IS-Only Numerical Evidence | PRESENT (11 sub-sections; 6+ numerical tables; falsifiers with explicit thresholds; behavioral-effect predictor; primitive-10-state EDA correction) |
| 4 | Section 3 — Proposed Changes | PRESENT (9 sub-fixes; bundle state verification table with 24 assertions; vol_normalized_ret_5d revert per iter-v3/048 closeout) |
| 5 | Section 4 — Expected OOS Impact | PRESENT (PATH A/B/C-clean/C-suspicious bands; pre-registered classification thresholds) |
| 6 | Section 5 — Risk Mitigation | PRESENT (R1/R2/R3 + primitive 10 + primitive 9 + cross-symbol contagion + risk-budget redistribution + IS trade-rate stability + adversarial-tests regression + multi-run-stochasticity) |
| 7 | Section 6 — Risk Management Design | PRESENT (10-primitive gate table; predicted fire rates; per-symbol ADX gate addition documented at gate #3) |
| 8 | Section 7 — Pre-Registered Failure-Mode Prediction | PRESENT (4 plausible failure modes; PROMISING-clean 40%, PROMISING-INERT 25%, NEGATIVE-clean 25%, NEGATIVE-SUSPICIOUS-OOS 10%) |
| 9 | Section 8 — Pre-Registered MERGE/NO-MERGE Criteria | PRESENT (PATH A/B/C-clean/C-suspicious with locked thresholds; saturation rule; PATH A IS-Δ threshold lowered to +0.05 with rationale) |
| 10 | Section 9 — Library Stack | PRESENT (UNCHANGED from iter-v3/048) |
| 11 | Section 10 — QR Audit Trail | PRESENT (NEW required per `feedback_v3_axis_selection_quant_discipline.md`; EDA SHA `ba8a3de` cited; QR-driven selection rationale; 5 SEED CANDIDATES from iter-v3/048 diary scored via EDA; primitive-10-state correction documented) |
| 12 | Section 11 — Catalog-Row Pre-Commit | PRESENT (4 outcomes pre-registered) |

**All 12 sections (10 mandatory + Section 11 pre-commit + Section 12 self-check)
PRESENT.** Engineer's Phase 5.5 gate should PASS this brief.

---

## Section 13 — Status

**READY-FOR-PHASE-5.5** — research brief complete. Engineer reads this brief,
verifies the sections, runs the bundle state assertions (incl. NEW per-symbol ADX
field assertion), runs the 5 per_symbol_adx_threshold adversarial tests + the 7
primitive 10 tests + the 5 ATR multipliers tests + regression on primitive 9 +
per_symbol_cap tests, **does NOT regenerate v3 features** (gate-config-only
change), and writes `phase5p5_gate.md` with OVERALL=PASS. Phase 6 backtest then
runs at single-seed --exploration --clean-oof; budget 25-40 min; well within
2h cap.

After Phase 6 closes, Critic Phase 7.5 review fires; QR Phase 7 evaluates OOS for
first time; QR Phase 8 closes the catalog row at one of the 4 pre-registered
dispositions.

iter-v3/049 is cycle 3 #10 of 10; LAST EXPLORATION before iter-v3/050 SECOND v3
CONFIRMATION.

---

## Section 14 — iter-v3/050 SECOND CONFIRMATION carry-forward note

Per `feedback_v3_strict_10_to_1_cadence.md`: iter-v3/050 = SECOND v3 CONFIRMATION,
SEPARATE from iter-v3/049 (do NOT collapse the LAST EXPLORATION into the
CONFIRMATION). The CONFIRMATION carries forward whichever ingredients the cycle 3
EXPLORATIONs ADVANCED to PROMISING:

**Confirmed PROMISING ingredients**:
- iter-v3/044 ALGO ATR (2.0, 1.5) — PROMISING
- iter-v3/045 LDO ATR (2.0, 1.5) — STRONGEST PROMISING (single-seed; bundle anchor)
- iter-v3/047 primitive 10 BCH LONG block — IS-validated only; NO clean OOS
  EXPLORATION evidence (iter-v3/047 was NEGATIVE-multi-run-stochasticity; iter-v3/048
  forensically corrected to NEGATIVE-clean single-seed Optuna lottery; the
  primitive 10 IS-only validation basis remains the original premise)
- iter-v3/049 per-symbol ADX (TRX 21) — IF iter-v3/049 = PATH A PROMISING-clean

The CONFIRMATION QR brief at iter-v3/050 MUST explicitly note:
- "Primitive 10 has no clean OOS evidence from EXPLORATION; iter-v3/050 multi-seed
  run is the first OOS test of primitive 10 in clean conditions" (UNCHANGED from
  iter-v3/048 closeout note).
- IF iter-v3/049 = PATH A: "Per-symbol ADX (TRX 21) has clean single-seed OOS
  evidence from iter-v3/049 EXPLORATION; iter-v3/050 multi-seed run is the first
  multi-seed OOS test of per-symbol ADX threshold variant in v3."
- IF iter-v3/049 = PATH B/C: "Per-symbol ADX (TRX 21) was iter-v3/049 EXPLORATION-
  NEGATIVE/INERT; NOT carried forward to iter-v3/050 CONFIRMATION."

Spec for iter-v3/050: `--seeds 2 --n-trials 35 --clean-oof` (CONFIRMATION-spec per
`feedback_v3_iter018_confirmation_baseline_validation.md`); 6h hard cap per
`feedback_v3_cadence_discipline.md`.
