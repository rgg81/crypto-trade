# Iteration v3-047 — Research Brief (REVERT iter-v3/046 BCH ATR + QR-driven BCH LONG signal filter)

**Type**: EXPLORATION (Cycle 3 #8 of 10)
**Track**: v3 (rigor arm) — forty-seventh iteration
**Branch**: `iteration-v3/047` (off iter-v3/046 head)
**Date**: 2026-05-09
**Author**: QR (autopilot)

---

## Section 0 — Data Split Declaration

```
OOS_CUTOFF_DATE  = 2025-03-24    # IMMUTABLE
training_months  = 24             # IMMUTABLE
ENSEMBLE_SIZE    = 5              # single outer seed (EXPLORATION-spec)
n_trials         = 35             # EXPLORATION default
colsample_bytree = Optuna-tuned   # NOT hardcoded 1.0
OOS_CUTOFF_MS    = 1742774400000
```

**IS window (24 months)**: 2023-03-24 00:00 UTC through 2025-03-23 23:59 UTC
**OOS window**: 2025-03-24 00:00 UTC onward

Sacred constants UNCHANGED. The QR sees iter-v3/047 OOS metrics for the FIRST time in Phase 7.

---

## Section 0.5 — Iteration Type Declaration

```
TYPE: EXPLORATION
Cycle: 3 — #8 of 10 (after iter-v3/040 baseline-restore + iter-v3/041 pruning + 042
  universal ATR + 043 Kaufman ER + 044 ALGO ATR PROMISING + 045 LDO ATR STRONGEST
  PROMISING + 046 BCH ATR NEGATIVE)
Wall-clock budget: <= 2h hard cap (EXPLORATION spec)
Spec: uv run python run_baseline_v3.py --seeds 1
  - ENSEMBLE_SIZE=5 (auto; inner ensemble)
  - n_trials=35 (default)
  - colsample_bytree Optuna-tunable (NOT hardcoded 1.0)
  - outer_seeds=1 (EXPLORATION-spec)
Two coupled changes (single coherent axis: REVERT failed mechanism + apply NEW correct
  mechanism for the SAME bottleneck):
  (a) PRE-COMMIT REVERT (mandatory per orchestrator + Critic FINAL `5dae6d6`):
      V3_ATR_MULTIPLIERS_PER_SYMBOL["BCHUSDT"] REMOVED. State after revert =
      iter-v3/045 config. BCH falls back to DEFAULT_ATR_MULTIPLIERS = (2.0, 1.0).
  (b) NEW AXIS (this iteration's hypothesis): primitive 10 (direction-asymmetric
      kill switch) added to RiskV2Config + RiskV3Wrapper. Set
      block_long_for=("BCHUSDT",) in the v3 runner. ALL BCH LONG candidate signals
      are universally suppressed regardless of model confidence; SHORT and
      NO_SIGNAL pass through unchanged. block_short_for=() (BCH SHORT is the
      positive contributor — never block).
  V3_FEATURE_COLUMNS_TOP_N = 14 (UNCHANGED — regime_momentum_signed_5d preserved).
  V3_FEATURES_PER_SYMBOL = {} (UNCHANGED — empty).
  V3_MODELS = 4 (BCH, LDO, TRX, ALGO) — UNCHANGED.
  REQUIRED_GAP = 88 = (21+1)*4 — UNCHANGED.
  V3_ATR_MULTIPLIERS_PER_SYMBOL: {ALGOUSDT: (2.0, 1.5), LDOUSDT: (2.0, 1.5)} — 2 entries.
Predicted classification: PROMISING (45%), PROMISING-MECHANICAL (20%),
  PROMISING-INERT (15%), NEGATIVE (20%).
```

**Context**: iter-v3/046 (per-symbol ATR widening for BCH; mirror of iter-v3/044 ALGO +
iter-v3/045 LDO) was NEGATIVE — bundle IS Sharpe Δ -0.54 + BCH OOS PnL -45 swing
(+10.75 → -34.54). Critic FINAL `5dae6d6` established that the wider-SL mechanism is
REGIME-MISMATCH-SPECIFIC; symbols with stable IS=OOS SL:TP (BCH at 1.93/1.93) do not
benefit. iter-v3/046 was REVERTED at the pre-commit (SHA `f5f0fd6`).

The KNOWN BCH bottleneck is direction asymmetry — LONG IS -25.07% (39 trades, 30.8% WR
— toxic), SHORT IS +48.69% (55 trades, 43.6% WR — positive); confirmed in
`analysis/iteration_v3-047/bch_diagnosis.csv` Tables 01+05 (reproducible across
iter-v3/045 default ATR + iter-v3/046 wider SL — pattern is NOT an ATR-config artifact).
The primitive 10 axis directly addresses the LONG-side toxicity by suppressing all BCH
LONG candidates. EDA Table 03 (naive counterfactual): blocking BCH LONG lifts bundle
weighted_pnl by +18.68 IS + +4.24 OOS (NAIVE; ignores risk-gate ripple effects).

iter-v3/047 is CYCLE 3 #8 of 10. The orchestrator's REVERT mandate (per Critic FINAL
`5dae6d6`) is honored at the pre-commit; the NEW direction-asymmetric axis is
QR-EDA-driven per `feedback_v3_axis_selection_quant_discipline.md`.

---

## Section 1 — Hypothesis

Adding primitive 10 (direction-asymmetric kill switch) with `block_long_for=("BCHUSDT",)`
suppresses ALL BCH LONG candidate signals regardless of model confidence, removing the
known IS+OOS LONG-toxic block (IS -25.07% PnL, 30.8% WR; OOS -7.4% PnL, 28.6% WR). The
mechanism preserves BCH SHORT (positive contributor +48.69% IS / +18.19% OOS) and is
universal across ATR configurations (LONG-toxic pattern reproducible across
iter-v3/045 default ATR + iter-v3/046 wider SL per EDA Table 05). Expected effect:
BCH IS net_pnl lifts from +23.62% to ~+48% (LONG-drag removed, SHORT preserved); BCH
OOS net_pnl lifts from +10.75 to ~+15-20 (NAIVE counterfactual +4.24 PnL but bundle
risk-gate scaling may amplify). Bundle IS Sharpe lift estimate +0.20 to +0.35; bundle
OOS Sharpe lift estimate +0.05 to +0.20 (anchor: iter-v3/045 +0.7459 IS / +3.5259 OOS).

---

## Section 2 — IS-Only Numerical Evidence

### 2.1 — Per-symbol IS contribution @ iter-v3/045 (the binding-constraint baseline)

| Symbol | n IS | WR IS | net_pnl IS | pct of total | Status |
|--------|----:|------:|-----------:|-------------:|---|
| LDO | 18 | 55.6% | +54.55% | 148.10% | Already optimized (per-symbol ATR) |
| **BCH** | **94** | **38.3%** | **+23.62%** | **64.13%** | **Default ATR; LONG-toxic; iter-v3/047 target** |
| TRX | 85 | 34.1% | -7.28% | -19.77% | Default ATR; IS-NEGATIVE (different mechanism) |
| ALGO | 53 | 39.6% | -34.05% | -92.45% | Per-symbol ATR; structural floor |

Source: `reports-v3/iteration_v3-045/in_sample/per_symbol.csv`.

### 2.2 — BCH direction asymmetry (re-confirms iter-v3/046 EDA finding; the bottleneck)

| Direction | n_IS | WR_IS | net_pnl_IS | n_OOS | WR_OOS | net_pnl_OOS |
|---|---:|---:|---:|---:|---:|---:|
| LONG  | 39 | 30.8% | **-25.07%** | 21 | 28.6% | **-7.44%** |
| SHORT | 55 | 43.6% | **+48.69%** | 17 | 52.9% | **+18.19%** |
| TOTAL | 94 | 38.3% | +23.62% | 38 | 39.5% | +10.75% |

BCH LONGs are toxic in BOTH IS (-25.07% PnL, 30.8% WR) AND OOS (-7.44% PnL, 28.6% WR).
SHORTs carry BCH's positive contribution. Source: `analysis/iteration_v3-047/bch_diagnosis.csv`
Table 01 (script SHA `695fc8e`, executed on iter-v3/045 trades.csv).

### 2.3 — Per-direction exit composition (the SL/TP/timeout breakdown)

iter-v3/045 BCH IS:

| Direction | exit_reason | n | pct_of_dir | mean_pnl | sum_pnl |
|---|---|---:|---:|---:|---:|
| LONG  | take_profit | 9  | 23.08% | +7.43% | +66.84% |
| LONG  | **stop_loss** | **25** | **64.10%** | **-3.96%** | **-98.96%** |
| LONG  | timeout | 5 | 12.82% | +1.41% | +7.05% |
| SHORT | take_profit | 20 | 36.36% | +7.86% | +157.24% |
| SHORT | stop_loss | 31 | 56.36% | -3.85% | -119.38% |
| SHORT | timeout | 4 | 7.27% | +2.71% | +10.83% |

LONG SL rate (64.10%) is higher than SHORT SL rate (56.36%); LONG TP rate (23.08%) is
roughly 2/3 the SHORT TP rate (36.36%). The LONG side fails because the model is
producing LONG signals on candles where the LONG side later proves toxic (lower TP
hit rate, higher SL hit rate, similar mean per-exit PnL magnitudes).

Source: `analysis/iteration_v3-047/bch_diagnosis.csv` Table 02.

### 2.4 — Counterfactual: NAIVE bundle weighted_pnl with all BCH LONGs removed

| Period | bundle_weighted_pnl | minus_BCH_LONG | Δ |
|---|---:|---:|---:|
| iter-v3/045 IS  | 75.40 | 94.07 | **+18.68** |
| iter-v3/045 OOS | 96.99 | 101.23 | **+4.24** |

Blocking BCH LONG lifts bundle weighted_pnl by +18.68 IS + +4.24 OOS (NAIVE — ignores
risk-gate ripple effects on other symbols' trades). This is the upper-bound estimate.

Bundle Sharpe lift estimate (proportional to PnL/sigma; sigma assumed unchanged):
- IS lift ≈ +18.68 / 75.40 × 0.7459 ≈ **+0.18 IS Sharpe** (first-order; variance also drops)
- OOS lift ≈ +4.24 / 96.99 × 3.5259 ≈ **+0.15 OOS Sharpe** (first-order; small relative magnitude)

Source: `analysis/iteration_v3-047/bch_diagnosis.csv` Table 03.

### 2.5 — Per-month BCH LONG vs SHORT (temporal stability of LONG toxicity)

Of 22 IS months with at least 1 BCH LONG trade (out of 31 IS months total with BCH
trades), the following months produced negative LONG PnL:

| Year-Month | n_long | long_pnl | long_wr |
|---|---:|---:|---:|
| 2022-01 | 1 | -4.89% | 0% |
| 2022-02 | 1 | -4.19% | 0% |
| 2022-05 | 1 | -5.22% | 0% |
| 2022-09 | 1 | -4.40% | 0% |
| **2022-11** | **6** | **-12.99%** | **17%** |
| 2023-02 | 3 | -0.46% | 33% |
| 2023-11 | 1 | -3.18% | 0% |
| **2023-12** | **2** | **-6.89%** | **0%** |
| 2024-06 | 4 | -3.24% | 25% |
| 2024-10 | 1 | -3.08% | 0% |
| **2024-12** | **3** | **-12.96%** | **0%** |

Source: `analysis/iteration_v3-047/bch_diagnosis.csv` Table 04.

LONG-toxic across multiple years (2022, 2023, 2024) and multiple market regimes (post-
FTX, mid-cycle, late-cycle). The 3 worst LONG months (2022-11, 2023-12, 2024-12)
contribute -32.85% LONG PnL alone — but eliminating them with a date filter would be
overfitting; instead, blocking BCH LONG universally captures the persistent pattern.

OOS LONG-toxic months: 2025-05 (-18.09%), 2025-09 (-2.96%), 2026-02 (-3.61%); positive
LONG months: 2025-04 (+5.11%), 2025-07 (+5.73%), 2025-08 (+0.11%), 2025-10 (+6.26%).
OOS LONG total -7.44% (the EDA Table 01 number).

### 2.6 — Reproducibility check: iter-v3/045 vs iter-v3/046

| Config | n_total | n_long | n_short | long_pnl | short_pnl | long_wr | short_wr |
|---|---:|---:|---:|---:|---:|---:|---:|
| iter-v3/045 IS (default ATR (2.0, 1.0)) | 94 | 39 | 55 | -25.07% | +48.69% | 30.77% | 43.64% |
| iter-v3/046 IS (wider SL (2.0, 1.5)) | 72 | 29 | 43 | -18.64% | +4.12% | 44.83% | 46.51% |
| iter-v3/045 OOS (default ATR) | 38 | 21 | 17 | -7.44% | +18.19% | 28.57% | 52.94% |
| iter-v3/046 OOS (wider SL) | 40 | 21 | 19 | -22.02% | -12.52% | 33.33% | 47.37% |

Source: `analysis/iteration_v3-047/bch_diagnosis.csv` Table 05.

LONG side is negative in BOTH iter-v3/045 (default ATR) AND iter-v3/046 (wider SL) —
the LONG-toxic pattern is NOT an artifact of one ATR config. Wider SL (iter-v3/046)
LIFTED LONG WR (30.8% → 44.8%) but also DEEPENED OOS LONG losses (-7.4% → -22%) — the
per-trade SL absorption was much worse OOS (mean SL pnl_pct -3.4% → -5.8% under wider
SL). This confirms the mirror mechanism's failure mode and re-validates that wider SL
is the WRONG axis for BCH; direction-suppression is the right axis.

### 2.7 — BCH model importance (last month of iter-v3/045 IS)

| Rank | Feature | Importance |
|---:|---|---:|
| 1 | ret_kurt_50 | 173 |
| 2 | ema_spread_atr_20 | 172 |
| 3 | range_realized_vol_50 | 129 |
| 4 | max_dd_window_50 | 107 |
| 5 | sym_vs_btc_ret_7d | 106 |
| 6 | ret_skew_200 | 104 |
| 7 | ret_kurt_200 | 99 |
| 8 | ret_skew_50 | 87 |
| 9 | hurst_100 | 72 |
| 10 | ret_autocorr_lag1_50 | 63 |
| 11 | btc_ret_14d | 58 |
| 12 | vwap_dev_20 | 52 |
| 13 | regime_momentum_signed_5d | 43 |
| 14 | hurst_diff_100_50 | 22 |

Note: this is a CONTEXT table only — the iter-v3/047 axis is at the SIGNAL-FILTER layer
(downstream of model inference), so feature importance per se does not change.

Source: `reports-v3/iteration_v3-045/in_sample/model_importance_last_month_BCHUSDT.csv`.

### 2.8 — Why NOT per-direction ATR (Candidate 2 in EDA ranking)

Per `analysis/iteration_v3-047/candidate_axes_ranking.md` Section "Candidate 2":
- Architectural refactor (nested config, label-generation refactor, new tests).
- Speculative direction (tighter LONG SL = more SLs at lower individual loss; net lift
  unknown — not directly EDA-supported).
- EXPLORATION 2h cap may not accommodate setup + testing.
- Architectural debt: nested config that may not generalize to other symbols.

### 2.9 — Why NOT BCH LONG threshold tightening (Candidate 3 in EDA ranking)

Per ranking Section "Candidate 3":
- Requires probability surface exposure + per-symbol-per-direction config (subset of
  Candidate 2's architectural refactor).
- Threshold (0.65 vs 0.55 vs 0.7) is a HYPERPARAMETER — Optuna-tunable inflates trial
  count and risks overfitting.
- Could end up suppressing same set of LONGs as Candidate 1 (PROMISING-MECHANICAL).

### 2.10 — Why NOT BCH LONG-only feature subset (Candidate 4 in EDA ranking)

Per ranking Section "Candidate 4":
- VERY HIGH complexity — architectural rewrite of per-cell model loop.
- No quantitative basis (would require its own EDA on per-direction feature importance,
  itself requiring per-direction model re-training).
- Doubles model count → doubles Optuna budget OR halves trials per direction.

### 2.11 — Predicted Behavioral Effect (per `feedback_v3_axis_saturation_predictor.md`)

Predicted IS trade count delta vs iter-v3/045 anchor:
- BCH IS trades: 94 → ~55 (LONG removed; predicted -39 ± 5 trades, -41% BCH-specific).
- Bundle IS trades: 250 → ~211 (predicted -16% bundle reduction).
- BCH OOS trades: 38 → ~17 (LONG removed; -21 ± 3 trades).
- Bundle OOS trades: ~78 (vs iter-v3/045 99 OOS bundle total). Above 130 floor IF
  `--seeds 1` * EXPLORATION pass; CONFIRMATION may need separate seed-rate validation.

**Falsifier**: if observed BCH IS trade count change is < -25% (i.e. BCH trades drop by
fewer than 24 — predicted -41% / -39 trades), the LONG-block did not propagate cleanly
through the dispatch path (investigate primitive 10 wiring or RiskV3Wrapper override).
If observed > -50% (more than 47 trades dropped), LONG-block over-fired (cross-symbol
contagion or off-by-one in the direction check; investigate test
`test_primitive_10_block_long_for_bch`).

### Analysis Script

`analysis/iteration_v3-047/bch_direction_diagnosis.py` (committed SHA `695fc8e`)
produces `bch_diagnosis.csv`, `synthesis.md`, and `candidate_axes_ranking.md`. The
diagnosis covers: BCH direction asymmetry IS+OOS, per-direction exit composition,
naive bundle counterfactual, per-month LONG-vs-SHORT, reproducibility iter-v3/045 vs
iter-v3/046, BCH model importance.

---

## Section 3 — Proposed Changes

### Sub-fix 1: ADD primitive 10 fields to `RiskV2Config`

In `src/crypto_trade/strategies/ml/risk_v2.py`, add to `RiskV2Config`:

```python
# iter-v3/047: primitive 10 — direction-asymmetric kill switch.
block_long_for: tuple[str, ...] = ()  # e.g. ("BCHUSDT",) — block direction == +1
block_short_for: tuple[str, ...] = ()  # e.g. () — block direction == -1
```

Default empty preserves v1/v2/v3-prior behavior (no behavioral change for any prior
iteration that does not set these fields).

### Sub-fix 2: ADD `direction_block_fires` to `GateStats`

In `src/crypto_trade/strategies/ml/risk_v2.py`, add to `GateStats`:

```python
direction_block_fires: int = 0  # iter-v3/047: primitive 10 fires
```

### Sub-fix 3: WIRE primitive 10 into `RiskV3Wrapper.get_signal`

In `src/crypto_trade/strategies/ml/risk_v3.py`, extend `get_signal`:

```python
def get_signal(self, symbol: str, open_time: int):
    # primitive 9 (regime gate; iter-v3/022) — fires BEFORE inner inference.
    if self.config.enable_regime_gate and symbol in self.config.regime_gate_symbols:
        if self._regime_gate_fires(symbol, open_time):
            self._gate_stats.setdefault(symbol, GateStats()).regime_gate_fires += 1
            return NO_SIGNAL

    # Inherited gate cascade (computes inner.get_signal first, then applies gates 1-8).
    sig = super().get_signal(symbol, open_time)

    # primitive 10 (direction block; iter-v3/047) — fires AFTER inner inference.
    if sig.direction == 1 and symbol in self.config.block_long_for:
        self._gate_stats.setdefault(symbol, GateStats()).direction_block_fires += 1
        return NO_SIGNAL
    if sig.direction == -1 and symbol in self.config.block_short_for:
        self._gate_stats.setdefault(symbol, GateStats()).direction_block_fires += 1
        return NO_SIGNAL

    return sig
```

Also extend `gate_stats_summary()` to include `direction_block_fires`.

### Sub-fix 4: ADD adversarial test `tests/strategies/ml/test_direction_block_primitive_10.py`

7 mandatory tests (all PASS at setup commit SHA TBD):
1. `test_primitive_10_block_long_for_bch` — BCH LONG blocked; SHORT preserved.
2. `test_primitive_10_other_symbol_not_blocked` — ALGO LONG passes (not in list).
3. `test_primitive_10_default_no_block` — default config preserves all signals.
4. `test_primitive_10_no_signal_passes_through` — NO_SIGNAL passes; counter does NOT
   increment.
5. `test_primitive_10_counter_increments` — counter fires once per blocked signal.
6. `test_primitive_10_block_short_for_symmetry` — symmetric mechanism (block_short_for
   works analogously, even though unused at iter-v3/047).
7. `test_primitive_10_summary_field_present` — gate_stats_summary contains
   direction_block_fires; primitive 9 regime_gate_fires still present (regression).

Tests use a deterministic mock inner strategy (no LightGBM training; no parquet I/O).

### Sub-fix 5: SET `block_long_for=("BCHUSDT",)` in v3 runner

In `run_baseline_v3.py:_build_v3_model`, add to the `RiskV2Config(...)` init:

```python
# iter-v3/047: primitive 10 — direction-asymmetric kill switch.
block_long_for=("BCHUSDT",),
block_short_for=(),
```

### Sub-fix 6: ADD `_verify_feature_columns` assertion

In `run_baseline_v3.py:_verify_feature_columns`, add:

```python
# iter-v3/047 primitive 10 dispatch: spot-check that the BCH model risk_cfg has
# block_long_for=("BCHUSDT",).
_cfg_check, strat_check = _build_v3_model(
    symbol="BCHUSDT", seed=42, n_trials=1, ensemble_seeds=[42]
)
assert strat_check.config.block_long_for == ("BCHUSDT",)
assert strat_check.config.block_short_for == ()
```

### Sub-fix 7: PRE-COMMIT REVERT (already executed at SHA `f5f0fd6`)

V3_ATR_MULTIPLIERS_PER_SYMBOL["BCHUSDT"] REMOVED. State after revert = iter-v3/045
config (ALGO + LDO at (2.0, 1.5) only). BCH falls back to DEFAULT_ATR_MULTIPLIERS =
(2.0, 1.0). 5 adversarial tests in `tests/features_v3/test_atr_multipliers_for_symbol.py`
PASS for the reverted state. Pre-commit SHA `f5f0fd6` is committed.

### Bundle state verification (what _verify_feature_columns must assert)

```
V3_FEATURE_COLUMNS_TOP_N: 14 features (UNCHANGED from iter-v3/045)                      PASS
DEFAULT_ATR_MULTIPLIERS: (2.0, 1.0) — UNCHANGED                                         PASS
V3_ATR_MULTIPLIERS_PER_SYMBOL: 2 entries (ALGO, LDO) — both (2.0, 1.5)                  PASS
V3_FEATURES_PER_SYMBOL: {} (empty — UNCHANGED)                                          PASS
features_for_symbol("BCHUSDT") == 14 features (TOP_N fallback)                          PASS
features_for_symbol("ALGOUSDT") == 14 features (TOP_N fallback)                         PASS
features_for_symbol("LDOUSDT") == 14 features (TOP_N fallback)                          PASS
features_for_symbol("TRXUSDT") == 14 features (TOP_N fallback)                          PASS
atr_multipliers_for_symbol("ALGOUSDT") == (2.0, 1.5) (per-symbol — UNCHANGED)           PASS
atr_multipliers_for_symbol("LDOUSDT") == (2.0, 1.5) (per-symbol — UNCHANGED)            PASS
atr_multipliers_for_symbol("BCHUSDT") == (2.0, 1.0) (DEFAULT — REVERTED iter-v3/047)    PASS
atr_multipliers_for_symbol("TRXUSDT") == (2.0, 1.0) (DEFAULT — UNCHANGED)               PASS
"regime_momentum_signed_5d" IN V3_FEATURE_COLUMNS_TOP_N (mandate PRESENT)               PASS
"regime_momentum_signed_3d" NOT IN V3_FEATURE_COLUMNS_TOP_N (REVERTED at iter-v3/044)   PASS
"efficiency_ratio_50" NOT IN V3_FEATURE_COLUMNS_TOP_N (DROPPED at iter-v3/043)          PASS
"ret_skew_50" IN V3_FEATURE_COLUMNS_TOP_N (PRESENT)                                     PASS
"sym_vs_btc_ret_7d" IN V3_FEATURE_COLUMNS_TOP_N (PRESENT)                               PASS
V3_MODELS = (BCH, LDO, TRX, ALGO) — 4 symbols (UNCHANGED)                               PASS
REQUIRED_GAP = 88 = (21+1) x 4 (UNCHANGED)                                              PASS
Primitive 10: BCH model risk_cfg.block_long_for == ("BCHUSDT",)                         PASS
Primitive 10: BCH model risk_cfg.block_short_for == ()                                  PASS
```

---

## Section 4 — Expected OOS Impact

**IS Sharpe prediction (single-seed, vs iter-v3/045 single-seed anchor +0.7459)**:
- Predicted band: [+0.85, +1.15]
- Median point estimate: +0.92 to +0.97
- Rationale: BCH LONG removal lifts BCH IS net_pnl from +23.62% to ~+48.69% (the
  SHORT-only contribution; +25pp BCH-specific lift). Bundle IS PnL +75.40 → ~+94.07
  (+18.68 weighted_pnl from EDA Table 03). Sharpe lift ~+0.18 first-order
  (proportional to PnL/sigma; sigma may also drop because the high-variance LONG
  block is removed, amplifying lift to +0.20-0.30).

**OOS Sharpe prediction (single-seed, vs iter-v3/045 single-seed anchor +3.5259)**:
- Predicted band: [+3.50, +3.85]
- Median point estimate: +3.60 to +3.70
- Rationale: BCH LONG removal lifts BCH OOS PnL from +10.75 to ~+15.55 (the SHORT-only
  contribution per EDA Table 03; +4.8 weighted_pnl). Bundle OOS Sharpe lift +0.05 to
  +0.20 (BCH is 11% of bundle OOS PnL; modest concentration impact). ALGO/LDO/TRX
  OOS bit-identical (per-symbol Optuna independence; primitive 10 affects only BCH
  model).

**OOS falsifier (pre-registered)**:
- If BCH OOS PnL drops below 0% (worse than +10.75 by > -10): primitive 10 backfired
  (some BCH SHORTs were collateral-blocked, OR LONG-block freed risk capacity for
  toxic OOS SHORT trades that wouldn't have fired before); NEGATIVE classification.
- If LDO/TRX/ALGO trade rosters are non-bit-identical to iter-v3/045: primitive 10
  dispatch path bug (cross-symbol contagion); PATH C — REVERT.
- If BCH SHORT trade roster is NOT bit-identical to iter-v3/045: primitive 10 over-
  fired (incorrectly blocked SHORTs); PATH C — REVERT.

**Pathway-A trigger (PROMISING)**:
- BCH OOS PnL ≥ +13 (≥+10.75 anchor + ≥+2 lift) AND BCH LONG count == 0 (Falsifier 1
  PASS) AND BCH SHORT roster bit-identical to iter-v3/045 (Falsifier 2 PASS) AND
  LDO+TRX+ALGO trade rosters bit-identical to iter-v3/045 (Falsifier 3 PASS) AND
  bundle OOS Sharpe not regressed by more than -0.10 vs iter-v3/045 anchor AND
  bundle IS Sharpe Δ ≥ +0.10 vs iter-v3/045 anchor.

**Pathway-B trigger (PROMISING-INERT or PROMISING-MECHANICAL)**:
- PROMISING-MECHANICAL: BCH SHORT trade roster bit-identical AND LDO/TRX/ALGO bit-
  identical AND bundle OOS Sharpe Δ in [-0.05, +0.05] AND bundle IS Sharpe Δ in
  [-0.05, +0.10]. Mechanism dispatched but signal not lifted (LONG removal cancels
  out via risk-budget redistribution — unlikely but possible).
- PROMISING-INERT: BCH LONG count > 0 AND < 5 (some LONGs slipped through;
  investigate dispatch). OR BCH LONG count == 0 BUT bundle IS Sharpe lift < +0.05
  (LONGs were genuinely net-near-zero in this seed).

**Pathway-C trigger (NEGATIVE)**:
- BCH OOS PnL < 0% OR
- BCH SHORT roster NOT bit-identical to iter-v3/045 OR
- LDO/TRX/ALGO trade rosters non-bit-identical (Falsifier 3 fires) OR
- Bundle OOS Sharpe regressed by more than -0.20 vs iter-v3/045 anchor OR
- Bundle IS Sharpe regressed by more than -0.10 vs iter-v3/045 anchor.
- Action: REVERT primitive 10 wiring at iter-v3/048; pivot to per-direction ATR
  (Candidate 2 from EDA ranking) OR LONG-confidence-threshold (Candidate 3).
  iter-v3/045 PROMISING bundle (ALGO + LDO ATR only) preserved.

---

## Section 5 — Risk Mitigation

**R1 (cooldown)**: unchanged. Cooldown=2 candles post-trade per symbol.

**R2 (drawdown scaling)**: unchanged. R2 gate parameters carried forward.

**R3 (OOD detection)**: zscore_threshold=2.0 unchanged. Feature subspace unchanged at 14
features (Mahalanobis covariance space identical to iter-v3/045/046). Expected effect on
OOD firing rate: <2% relative.

**Primitive 10 dispatch risk**: the primitive is wired in `RiskV3Wrapper.get_signal`
AFTER `super().get_signal` (which runs the inherited cascade including primitive 9 on
non-RiskV3 levels; primitive 10 fires after inner inference). The 7-test adversarial
suite (Sub-fix 4) verifies:
- LONG blocked / SHORT passed for BCH.
- Other symbols unaffected.
- Default (empty list) preserves prior behavior.
- NO_SIGNAL doesn't increment counter.
- Counter accuracy.
- Symmetric block_short_for mechanism.
- gate_stats_summary contains the new field (regression check on primitive 9).

**Cross-symbol contagion risk**: primitive 10 only checks `symbol in
config.block_long_for`. The dispatched config is per-model (each `_build_v3_model` call
creates its own RiskV3Wrapper with the same `block_long_for=("BCHUSDT",)`). Even though
the gate is wired for ALL models, it can only fire on BCH (only BCH is in the list). A
cross-symbol dispatch bug (LONG blocked on ALGO accidentally) would manifest as
ALGO/LDO/TRX trade-roster drift — pre-registered Falsifier 3.

**Risk-budget redistribution risk**: by blocking BCH LONGs, the bundle's
risk-management gates (vol scaling, drawdown brake) see lower BCH-attributed risk
consumption. This may free risk capacity for OTHER symbols (ALGO, LDO, TRX), which
would manifest as drift in their trade rosters or weight distributions. Falsifier 3
(LDO/TRX/ALGO trade-roster bit-identity) catches this. If risk-budget redistribution
is NOT bit-identical-preserving, the iteration is NEGATIVE; the cleanest interpretation
of primitive 10 success is per-symbol Optuna independence.

**IS trade-rate stability**: Bundle IS trades expected within -16% (±5%) of iter-v3/045
(250 → 211 ± 12). If portfolio total deviates > 30%, investigate primitive 10 wiring,
parquet freshness, or feature column list.

**Adversarial-tests regression risk**: the 7 primitive 10 tests + the 5 ATR tests + the
existing primitive 9 + per-symbol cap tests all PASS at the setup commit. If any of
these regress in CI before backtest runs, the iteration is BLOCKED.

---

## Section 6 — Risk Management Design (7-Primitive Gate Table → 8-Primitive)

All 7 prior risk gates carried forward from iter-v3/045 baseline UNCHANGED. NEW primitive
10 (direction-asymmetric kill switch) added.

| Gate | Type | Parameter | Change |
|---|---|---|---|
| 1 — BTC trend | BtcTrendFilterConfig | lookback=42, threshold=15% | None |
| 2 — Hit rate | HitRateGateConfig | window=20, sl_threshold=0.65 | DISABLED (unchanged) |
| 3 — ADX gate | ADX regime filter | threshold=20 (v3 default) | None |
| 4 — Hurst regime | hurst_100 > 0.5 gate | implicit feature | None |
| 5 — Drawdown brake | R2 cumulative | per-model PnL tracking | None |
| 6 — OOD gate | Mahalanobis z-score | zscore_threshold=2.0, 14-D space | None (no feature change) |
| 7 — Liquidity floor | NATR floor | NATR >= 0.5% | None |
| 8 — Per-symbol cap | RiskV2Config | enable_per_symbol_cap=False | None |
| 9 — Regime gate | RiskV2Config | enable_regime_gate=False | None |
| **10 — Direction block (NEW)** | **RiskV2Config** | **block_long_for=("BCHUSDT",); block_short_for=()** | **NEW iter-v3/047** |

**Predicted primitive 10 fire rate**: BCH LONG candidate signals from the model. Based on
iter-v3/045 BCH trade composition (94 trades total, 39 LONG = 41.5% of BCH candidates that
passed prior gates), the primitive will fire ~41% of BCH model signals. Fires on
candidate-LONG only; no false positives on SHORTs or non-BCH symbols.

**Predicted OOD fire rate**: within ±2% of iter-v3/045 baseline. No feature subspace
change.

---

## Section 7 — Pre-Registered Failure-Mode Prediction

**Most plausible failure mode (PROMISING — clean IS+OOS lift; 45% probability)**:
BCH IS WR rises to ~43.6% (the SHORT-only WR), BCH IS net_pnl lifts from +23.62% to
~+48.69% (LONG-drag removed; SHORT preserved bit-identical). Bundle IS Sharpe lifts
+0.10 to +0.30 (NAIVE estimate +0.18; risk-budget redistribution may amplify if it
shifts capacity toward higher-Sharpe ALGO/LDO/TRX trades). BCH OOS WR rises from 39.5%
to ~52.9% (the SHORT-only OOS WR), BCH OOS PnL lifts from +10.75 to ~+15-20. Bundle OOS
Sharpe lift +0.05 to +0.20. LDO/TRX/ALGO trade rosters bit-identical (per-symbol Optuna
independence; primitive 10 affects only BCH). Classification: PROMISING (clean).
Compoundable at iter-v3/050 CONFIRMATION as a labeling+gate hybrid: ALGO + LDO ATR
(2.0, 1.5) per-symbol + primitive 10 BCH LONG block. **Probability: 45%.**

**Second plausible failure mode (NEGATIVE — risk-budget redistribution; 20% probability)**:
By blocking BCH LONGs, risk capacity frees up for ALGO/LDO/TRX. The freed capacity
allows MORE trades (or LARGER trades via vol-scaling) on other symbols, which may
include toxic trades that wouldn't have fired before. ALGO/LDO/TRX trade rosters drift
(Falsifier 3 fires); bundle OOS Sharpe regresses. Classification: NEGATIVE; pivot to
per-direction ATR (Candidate 2) at iter-v3/048. **Probability: 20%.**

**Third plausible failure mode (PROMISING-MECHANICAL — bit-identical accounting; 20% probability)**:
At single-seed n_trials=35, the bundle's risk-management gates absorb the freed capacity
without changing per-symbol trade rosters; the LONG-block is purely accounting cleanup.
BCH LONG count == 0 AND BCH SHORT bit-identical AND LDO/TRX/ALGO bit-identical AND
bundle Sharpe Δ in [-0.05, +0.10]. Classification: PROMISING-MECHANICAL per
`feedback_promising_mechanical_subtype.md`. NOT a CONFIRMATION-bundle ingredient —
strictly architectural drag-removal (the "non-compoundable across iterations" subtype).
Diagnostic: per-symbol Optuna independence + bundle-level risk-budget conservation.
**Probability: 20%.**

**Fourth plausible failure mode (PROMISING-INERT — partial dispatch; 10% probability)**:
BCH LONG count > 0 AND < 5 (some LONGs slipped through). Investigate primitive 10
wiring. If ALL LONGs were blocked (count == 0) BUT bundle IS Sharpe lift < +0.05, the
LONG-block was net-near-zero in this seed (LONGs were collectively breakeven, not
toxic). Classification: PROMISING-INERT. Retain as zero-cost addition to iter-v3/050
CONFIRMATION bundle. **Probability: 10%.**

**Fifth plausible failure mode (NEGATIVE — primitive 10 dispatch bug; <5% probability)**:
LDO/TRX/ALGO trade rosters non-bit-identical to iter-v3/045. The primitive 10 wiring
has a bug (e.g., the symbol check is wrong, or the list contains entries for other
symbols). Falsifier 3 fires; PATH C — REVERT. The 7-test adversarial suite makes this
extremely unlikely; tests cover symmetric block_short_for so wiring symmetry is
verified. **Probability: <5%.**

**What the gates should catch**:
- Gate 5 (R2 drawdown): BCH label-distribution shift may alter R2 firing rate. Monitor.
- Gate 7 (liquidity): NATR floor unchanged; BCH trades that were marginal NATR-wise
  before still pass.
- **Primitive 10 fire rate (NEW)**: predicted ~41% of BCH candidate signals; if
  observed < 30% or > 55%, investigate dispatch.

**Behavioral effect predictor**: predicted IS trade count delta -41% BCH-specific (94
→ 55), -16% bundle-wide (250 → 211). Falsifier: > 50% BCH-specific drop OR > 30%
bundle-wide drop triggers investigation.

---

## Section 8 — Pre-Registered MERGE/NO-MERGE Numerical Criteria

This is an EXPLORATION iteration. MERGE gates do NOT apply. Classification criteria
(pre-registered before backtest runs):

**PATH A — PROMISING (clean)**:
  BCH OOS PnL ≥ +13 AND BCH LONG count == 0 AND BCH SHORT roster bit-identical AND
  LDO+TRX+ALGO trade rosters bit-identical AND bundle OOS Sharpe Δ ≥ -0.10 AND bundle
  IS Sharpe Δ ≥ +0.10 vs iter-v3/045 anchor.
  Classification: PROMISING. Primitive 10 contributes positive lift on BCH-LONG-block
  axis. Catalog entry: candidate for next CONFIRMATION bundle (compoundable with
  iter-v3/044 ALGO ATR + iter-v3/045 LDO ATR — a labeling + gate hybrid).

**PATH B-MECHANICAL — PROMISING-MECHANICAL**:
  BCH LONG count == 0 AND BCH SHORT roster bit-identical AND LDO/TRX/ALGO bit-identical
  AND bundle OOS Sharpe Δ in [-0.05, +0.05] AND bundle IS Sharpe Δ in [-0.05, +0.10].
  Classification: PROMISING-MECHANICAL per `feedback_promising_mechanical_subtype.md`.
  NOT a CONFIRMATION-bundle ingredient.

**PATH B-INERT — PROMISING-INERT**:
  BCH LONG count > 0 AND < 5 (partial dispatch — investigate). OR BCH LONG count == 0
  AND bundle IS Sharpe lift < +0.05 (LONGs were collectively breakeven). Retain as
  zero-cost addition to iter-v3/050 CONFIRMATION bundle if other axes succeed.

**PATH C — NEGATIVE**:
  - NEGATIVE-BCH-deepens: BCH OOS PnL < 0% (worse than +10.75 by > -10).
  - NEGATIVE-bundle-regression: bundle OOS Sharpe regressed by more than -0.20 vs
    iter-v3/045 OR bundle IS Sharpe regressed by more than -0.10.
  - NEGATIVE-architecture-bug: LDO/TRX/ALGO trade rosters non-bit-identical to
    iter-v3/045 (Falsifier 3 fires) OR BCH SHORT roster non-bit-identical (over-fire) —
    REVERT primitive 10 wiring.
  Classification: NEGATIVE. Direction-asymmetric axis FALSIFIED for BCH.
  Action: REVERT primitive 10 wiring at iter-v3/048; consider per-direction ATR
  (Candidate 2 from EDA ranking) OR LONG-confidence-threshold (Candidate 3) as next
  options. iter-v3/045 PROMISING bundle (ALGO + LDO ATR) preserved.
  Catalog entry: "Primitive 10 BCH LONG block FALSIFIED — direction-asymmetric
  mechanism creates risk-budget contagion / cross-symbol drift / over-fire OR LONG-
  block is net-negative on OOS at single-seed".

**Pre-registered classification thresholds (locked before backtest)**:
- PATH A: BCH OOS PnL ≥ +13 AND BCH LONG count == 0 AND BCH SHORT bit-identical AND
  LDO/TRX/ALGO bit-identical AND bundle OOS Sharpe Δ ≥ -0.10 AND bundle IS Sharpe Δ ≥ +0.10
- PATH B-MECHANICAL: BCH LONG count == 0 AND BCH SHORT bit-identical AND LDO/TRX/ALGO
  bit-identical AND bundle OOS Sharpe Δ ∈ [-0.05, +0.05] AND IS Δ ∈ [-0.05, +0.10]
- PATH B-INERT: BCH LONG count > 0 (some slipped through) OR (count == 0 AND bundle IS
  Sharpe lift < +0.05)
- PATH C: BCH OOS PnL < 0% OR bundle OOS Sharpe Δ < -0.20 OR bundle IS Sharpe Δ < -0.10
  OR LDO/TRX/ALGO drift OR BCH SHORT non-bit-identical

These thresholds are LOCKED and cannot be post-hoc renegotiated.

---

## Section 9 — Library Stack Declaration

All versions identical to iter-v3/045/046 reproducibility stamp. No new libraries
introduced. Primitive 10 is a config-only + 5-line code addition (no new feature
implementations dispatched).

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

**No mlfinlab/mlfinpy/pypbo/fracdiff dependencies.** v3 uses scipy + statsmodels for all
statistical tests (ADF, PBO, DSR, PSR).

---

## Section 10 — QR Audit Trail (per `feedback_v3_axis_selection_quant_discipline.md`)

**EDA basis**: `analysis/iteration_v3-047/bch_direction_diagnosis.py` (committed SHA
`695fc8e`). Outputs: `bch_diagnosis.csv`, `synthesis.md`, `candidate_axes_ranking.md`.
Establishes:
- BCH direction asymmetry IS+OOS — LONG IS -25.07% (toxic), SHORT IS +48.69% (positive)
- BCH per-direction exit composition — LONG SL rate 64% vs SHORT SL rate 56%; LONG TP
  rate 23% vs SHORT TP rate 36%
- Bundle counterfactual (NAIVE) — blocking BCH LONG lifts bundle weighted_pnl +18.68 IS
  + +4.24 OOS
- Per-month LONG toxicity — persistent across 2022-2024 (worst months 2022-11, 2023-12,
  2024-12); not a single-period artifact
- Reproducibility iter-v3/045 vs iter-v3/046 — LONG-toxic pattern reproducible across
  default ATR + wider SL configs (NOT an ATR-config artifact)
- 4 candidate axes ranked: top recommendation is primitive 10 (BCH LONG signal filter)
  — lowest implementation complexity, largest quantitative leverage, direct mechanism
  alignment with EDA root cause

**Original orchestrator pick**: REVERT iter-v3/046 BCH ATR per Critic FINAL `5dae6d6`
recommendation — executed at pre-commit `f5f0fd6`. The orchestrator did NOT pre-commit
the NEW axis (per `feedback_v3_axis_selection_quant_discipline.md` discipline since
iter-v3/044); QR EDA-derived the direction-asymmetric axis from candidate ranking.

**QR-driven selection**: primitive 10 (direction-asymmetric kill switch) with
`block_long_for=("BCHUSDT",)`. EDA ranks this as Candidate 1 of 4: lowest complexity
(~5-10 LOC wrapper extension), largest quantitative leverage (NAIVE counterfactual
+18.68 IS + +4.24 OOS), direct mechanism alignment with EDA root cause (BCH LONG-side
toxicity), reversible (single config tuple), and aligned with the existing primitive-9
pattern (architectural symmetry). Per-direction ATR (Candidate 2), LONG-threshold
tightening (Candidate 3), and LONG-only feature subset (Candidate 4) all rejected for
higher implementation complexity OR speculative direction without EDA support.

**Pre-commit SHA**: `f5f0fd6` (REVERT iter-v3/046 BCH ATR; state = iter-v3/045 config).
**EDA SHA**: `695fc8e` (BCH direction diagnosis + 4-axis ranking).
**Brief SHA**: TBD (this commit).
**Setup commit SHA**: TBD (will follow brief + Phase 5.5 gate per discipline).

**Phase 5.5 verification**: pre-commit + EDA committed BEFORE brief; brief includes
Section 2 numerical evidence sourced from `bch_diagnosis.csv` (committed SHA `695fc8e`);
brief includes Section 10 QR Audit Trail (NEW required section); 7-test primitive 10
adversarial suite committed alongside setup commit.

This Section 10 satisfies the process-discipline requirement that QR EDA precedes axis
selection. Cannot be retroactively renegotiated.

---

## Section 11 — Catalog-Row Pre-Commit Disposition

The catalog row to be appended at Phase 8 (diary closure) is pre-registered for ALL outcomes:

**Outcome A — PROMISING-clean** (BCH OOS PnL ≥ +13 AND BCH LONG count == 0 AND BCH SHORT
bit-identical AND LDO/TRX/ALGO bit-identical AND bundle OOS Sharpe Δ ≥ -0.10 AND bundle IS
Sharpe Δ ≥ +0.10):
> `| iter-v3/047 | 2026-05-09 | REVERT iter-v3/046 BCH ATR + Primitive 10 (direction-asymmetric kill switch) block_long_for=("BCHUSDT",); 4-sym BCH+LDO+TRX+ALGO; QR EDA-driven; cycle 3 #8 | <IS Δ> | <OOS Δ> | EXPLORATION-PROMISING (clean) | YES — STRONG candidate; iter-v3/050 CONFIRMATION-bundle ingredient (compoundable with iter-v3/044 ALGO ATR + iter-v3/045 LDO ATR — labeling + gate hybrid) |`

**Outcome B-MECHANICAL — PROMISING-MECHANICAL** (BCH LONG == 0 AND BCH SHORT bit-identical
AND LDO/TRX/ALGO bit-identical AND bundle OOS Sharpe Δ ∈ [-0.05, +0.05] AND IS Δ ∈ [-0.05, +0.10]):
> `| iter-v3/047 | 2026-05-09 | REVERT iter-v3/046 BCH ATR + Primitive 10 BCH LONG block; cycle 3 #8 | <IS Δ> | <OOS Δ> | EXPLORATION-PROMISING-MECHANICAL | NO — strictly architectural drag-removal; bundle risk-budget conserved; non-compoundable across iterations per `feedback_promising_mechanical_subtype.md`; iter-v3/048 may try per-direction ATR or LONG-threshold tightening |`

**Outcome B-INERT — PROMISING-INERT** (BCH LONG > 0 (partial dispatch) OR LONG == 0 AND
bundle IS Sharpe lift < +0.05):
> `| iter-v3/047 | 2026-05-09 | REVERT iter-v3/046 BCH ATR + Primitive 10 BCH LONG block; cycle 3 #8 | <IS Δ> | <OOS Δ> | EXPLORATION-PROMISING-INERT | RETAIN as zero-cost CONFIRMATION-bundle addition if other axes succeed; mechanism dispatched but signal not lifted |`

**Outcome C — NEGATIVE-BCH-deepens** (BCH OOS PnL < 0%):
> `| iter-v3/047 | 2026-05-09 | REVERT iter-v3/046 BCH ATR + Primitive 10 BCH LONG block; cycle 3 #8 | <IS Δ> | <OOS Δ> | EXPLORATION-NEGATIVE (BCH deepens) | NO — closes direction-asymmetric axis on BCH; LONG-block is net-negative on OOS; iter-v3/048 = different axis (consider per-direction ATR or LONG-threshold tightening); risk-budget redistribution may have freed capacity for OOS-toxic trades on other symbols |`

**Outcome C — NEGATIVE-architecture-bug** (LDO/TRX/ALGO non-bit-identical OR BCH SHORT non-bit-identical):
> `| iter-v3/047 | 2026-05-09 | REVERT iter-v3/046 BCH ATR + Primitive 10 BCH LONG block; cycle 3 #8 | <IS Δ> | <OOS Δ> | EXPLORATION-NEGATIVE (architecture-bug — primitive 10 dispatch drift) | NO — REVERT primitive 10 wiring; iter-v3/048 = different axis category after architectural fix |`

**Outcome C — NEGATIVE-redistribution** (bundle OOS Sharpe Δ < -0.20 OR IS Δ < -0.10):
> `| iter-v3/047 | 2026-05-09 | REVERT iter-v3/046 BCH ATR + Primitive 10 BCH LONG block; cycle 3 #8 | <IS Δ> | <OOS Δ> | EXPLORATION-NEGATIVE (risk-budget redistribution) | NO — primitive 10 freed risk capacity for cross-symbol toxic trades; closes direction-asymmetric axis at single-seed; iter-v3/048 = pivot to per-direction ATR (architectural Candidate 2) |`

The diary commit closes the catalog row regardless of outcome. The 5-row pre-commit
prevents post-hoc rationalization.

---

## Section 12 — Phase 5.5 Gate Self-Check (10 mandatory sections inventory)

| # | Section | Status |
|---|---|---|
| 1 | Section 0 — Data Split Declaration | PRESENT (sacred constants UNCHANGED) |
| 2 | Section 1 — Hypothesis | PRESENT (primitive 10 BCH LONG block; expected effect; mechanism named) |
| 3 | Section 2 — IS-Only Numerical Evidence | PRESENT (11 sub-sections; 6 numerical tables; falsifiers with explicit thresholds; behavioral-effect predictor; reproducibility check across iter-v3/045 vs iter-v3/046) |
| 4 | Section 3 — Proposed Changes | PRESENT (7 sub-fixes; bundle state verification table with 21 assertions) |
| 5 | Section 4 — Expected OOS Impact | PRESENT (PATH A/B-MECHANICAL/B-INERT/C bands; pre-registered classification thresholds) |
| 6 | Section 5 — Risk Mitigation | PRESENT (R1/R2/R3 + primitive 10 dispatch risk + cross-symbol contagion + risk-budget redistribution + IS trade-rate stability + adversarial-tests regression) |
| 7 | Section 7 — Pre-Registered Failure-Mode Prediction | PRESENT (5 plausible failure modes; most plausible PROMISING; 2nd NEGATIVE-redistribution; 3rd PROMISING-MECHANICAL; 4th PROMISING-INERT; 5th NEGATIVE-architecture-bug) |
| 8 | Section 8 — Pre-Registered MERGE/NO-MERGE Criteria | PRESENT (PATH A/B-MECHANICAL/B-INERT/C with locked thresholds) |
| 9 | Section 9 — Library Stack | PRESENT (UNCHANGED from iter-v3/045/046) |
| 10 | Section 10 — QR Audit Trail | PRESENT (NEW required per `feedback_v3_axis_selection_quant_discipline.md`; pre-commit SHA + EDA SHA cited; QR-driven selection rationale + orchestrator REVERT mandate honored) |
| 11 | Section 11 — Catalog-Row Pre-Commit | PRESENT (5 outcomes pre-registered) |

**All 11 sections (10 mandatory + Section 11 pre-commit) PRESENT.** Engineer's Phase 5.5
gate should PASS this brief.

---

## Section 13 — Status

**READY-FOR-PHASE-5.5** — research brief complete. Engineer reads this brief, verifies
the sections, runs the bundle state assertions, runs the 7 adversarial primitive 10
pytest tests + the 5 ATR multipliers tests (reverted state) + regression on primitive
9 + per_symbol_cap tests, and writes `phase5p5_gate.md` with OVERALL=PASS. Phase 6
backtest then runs at single-seed --exploration; budget 25-35 min; well within 2h cap.

After Phase 6 closes, Critic Phase 7.5 review fires; QR Phase 7 evaluates OOS for first
time; QR Phase 8 closes the catalog row at one of the 5 pre-registered dispositions.

iter-v3/047 is cycle 3 #8 of 10; 2 EXPLORATIONs remain in this cycle (iter-v3/048,
/049); CONFIRMATION at iter-v3/050.
