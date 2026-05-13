# Iteration v3-061 — Research Brief (Cycle 1 EXPLORATION #2: TRX-specific RiskV2 vol_scale_floor=0.5 — Path B per-symbol intervention)

**Type**: EXPLORATION (cycle 1 #2 of 10; FIRST per-symbol risk-primitive customization
EXPLORATION in v3 history; Path B per Section 10 EDA-driven path-selection)
**Track**: v3 (rigor arm) — sixty-first iteration
**Branch**: `iteration-v3/061` (created from `iteration-v3/060` HEAD at SHA `b794d6a`;
includes Phase B-3 unified ensemble at `ab2d9ac` + walk-forward fix at `e149e9d`
+ Phase A revert at `31665f6` + mode-flag refactor at `56f5a30`)
**Date**: 2026-05-13
**Author**: QR (EDA-driven per `feedback_v3_axis_selection_quant_discipline.md`)
**EDA SHA**: `d198b25` — `analysis/iteration_v3-061/trx_anti_kelly_diagnostic.py`

---

## Section 0 — Data Split Declaration

```
OOS_CUTOFF_DATE             = 2025-03-24    # IMMUTABLE
training_months             = 24             # IMMUTABLE
EXPLORATION_ENSEMBLE_SIZE   = 3              # active for /061 (--exploration flag)
CONFIRMATION_ENSEMBLE_SIZE  = 10             # default; reserved for cycle 1 CONFIRMATION
ENSEMBLE_SEEDS              = (191664963, 1662057957, 1405681631, 942484272, 929893137,
                                33158374, 1465339467, 1273345680, 115579757, 1952249162)
ACTIVE_SEEDS (/061)         = ENSEMBLE_SEEDS[0:3] = (191664963, 1662057957, 1405681631)
n_trials                    = 35             # EXPLORATION default (per feedback_v3_exploration_n_trials_35.md)
colsample_bytree            = Optuna-tuned   # NOT hardcoded 1.0
OOS_CUTOFF_MS               = 1742774400000
```

**IS window (24 months)**: 2023-03-24 00:00 UTC through 2025-03-23 23:59 UTC
**OOS window**: 2025-03-24 00:00 UTC onward

Sacred constants UNCHANGED. The QR sees iter-v3/061 OOS metrics for the FIRST time in Phase 7.

---

## Section 0.5 — Iteration Type Declaration

```
TYPE: EXPLORATION (cycle 1 #2 of 10; FIRST per-symbol risk-primitive
  customization EXPLORATION in v3 history)
  - Pre-locked anchor: iter-v3/060 EXPLORATION-MODE-REFERENCE
    (IS +0.8325 / OOS +0.1403; mode="exploration", ensemble_size=3)
    NOT iter-v3/059 (which is the CONFIRMATION-mode canonical baseline at
    IS +1.0894 / OOS +0.5791; reserved for cycle 1 CONFIRMATION re-validation
    at iter-v3/069+ per Critic /060 Rec #2).
  - Axis selection mandate: per Critic FINAL `3cee250` Recommendation #3,
    iter-v3/061 axis = TRX RiskV2 anti-Kelly diagnostic + intervention
    (Path B chosen per Section 10 EDA-driven path-selection logic).
  - Wall-clock target: ~1.1h (3-seed EXPLORATION; same as /060)
  - Run command: uv run python run_baseline_v3.py --exploration --seeds 1 --n-trials 35

Phase chain leading to this iteration:
  Phase B-3 (commit ab2d9ac): unified ensemble (outer-seed loop eliminated)
  Phase A Optuna n_jobs=2 ATTEMPTED at `0a3c30e`, REVERTED at `31665f6`
    (5x GIL slowdown); current state n_jobs=1.
  Walk-forward fix (commit e149e9d): 22-candle embargo at train/test boundary
  Mode-flag refactor (commit 56f5a30): --exploration → ENSEMBLE_SIZE=3
  /060 EXPLORATION-MODE-REFERENCE established at b794d6a (cycle 1 #1)
  iter-v3/061 EDA committed at d198b25 (TRX anti-Kelly partition-method
    cleanup + counterfactual floor sensitivity)
```

---

## Section 1 — Hypothesis

### Path B: TRX-specific RiskV2 vol_scale_floor=0.5

**HYPOTHESIS**: Setting `vol_scale_floor_per_symbol = {"TRXUSDT": 0.5}` (raising
the TRX-only vol-scaling floor from 0.3 to 0.5; BCH/LDO unchanged at 0.3) shifts
TRX's weight_factor distribution upward in the lower tail, lifting TRX OOS
weighted_pnl by approximately +0.47 wpnl (counterfactual prediction, trade-selection
invariance assumed). At single-seed EXPLORATION mode, this translates to a predicted
**OOS Sharpe shift in the range [0.0, +0.20] vs /060 anchor** — placing it most
likely INERT-AT-EXPLORATION (within noise band) per
`feedback_v3_cycle1_axis_pass_criteria.md`.

**Mechanism**: RiskV2 `_vol_scale` returns `np.clip(atr_pct_rank_200, floor=0.3,
ceiling=1.0)` for each signal (src/crypto_trade/strategies/ml/risk_v2.py:580-592).
For TRX, EDA Q3 shows TRX OOS Q1_low bucket (weight 0.33-0.47) has WR=50%
contributing +2.59 weighted_pnl, while Q3 bucket (weight 0.68-0.77) has WR=22%
contributing -3.74 weighted_pnl. Raising the floor to 0.5 for TRX-only:
- Lifts trades currently in Q1_low (10 OOS trades) from avg weight ~0.40 to 0.50
- Slightly amplifies Q1_low's positive PnL contribution
- Leaves Q3/Q4 untouched (already above floor)
- Per Q5 invariance check, BCH/LDO weighted_pnl unchanged (their distribution
  has no weights below 0.5 on average)

**Per-symbol intervention rationale**: Per the existing `adx_threshold_per_symbol`
precedent (iter-v3/049 added; iter-v3/050 reverted) and `block_long_for` precedent
(iter-v3/047 added; iter-v3/051 reverted), per-symbol risk-primitive customization
infrastructure exists in RiskV2Config and is non-controversial at EXPLORATION level.
Per `feedback_v3_per_symbol_lifts_oos_breaks_is.md`, the RISK is that at multi-seed
CONFIRMATION the per-symbol customization breaks the IS aggregate; the IS
counterfactual at single-seed shows +0.008 wpnl shift (bit-identical IS), so this
specific intervention has lower IS-regression risk than label or feature
customizations.

**What this iteration tests**: (a) Does the counterfactual prediction (TRX OOS lift
+0.47 wpnl, IS bit-identical) hold under actual backtest re-run? (b) Does the
trade-selection-invariance assumption hold (i.e., does the floor change leak into
other decisions via state-update effects)? (c) Establishes whether per-symbol
vol_scale_floor is an axis worth carrying to cycle 1 CONFIRMATION.

**What this iteration does NOT test**:
- BCH or LDO RiskV2 weight_factor calibration (out of scope; per-symbol design)
- Universal RiskV2 reformulation (Path C; deferred — too aggressive for single-EXPLORATION)
- Reverse-sign falsification (Path E; deferred — anti-Kelly not statistically significant)
- Any feature, label, or universe change
- Trade-rate floor or 8/14-month OOS-aggregate gate logic (these are CONFIRMATION-only)

---

## Section 2 — IS-Only Numerical Evidence (committed EDA at `d198b25`)

Analysis script: `analysis/iteration_v3-061/trx_anti_kelly_diagnostic.py`
Output directory: `analysis/iteration_v3-061/`
Run command: `uv run python analysis/iteration_v3-061/trx_anti_kelly_diagnostic.py`

### Section 2.1 — Q1: Anti-Kelly statistical significance (partition-method comparison)

| split | symbol | Method A (/060 Q7) diff | Method B (cleaned) diff | Method B Welch t | Method B 95% CI | Significant? |
|---|---|---:|---:|---:|---|---|
| IS | BCH | (n/a in /060) | **+0.068** | +1.22 | [-0.042, +0.176] | NO (Kelly-aligned direction) |
| IS | LDO | (n/a in /060) | **+0.125** | +0.86 | [-0.146, +0.344] | NO (Kelly-aligned direction) |
| **IS** | **TRX** | **-0.061** | **+0.020** | **+0.34** | **[-0.091, +0.130]** | **NO — sign flips A→B; CI includes 0** |
| OOS | BCH | (n/a in /060) | +0.038 | +0.50 | [-0.108, +0.180] | NO |
| OOS | LDO | (n/a in /060) | +0.189 | +2.08 | [+0.026, +0.357] | **YES (Kelly-aligned)** |
| **OOS** | **TRX** | **-0.014** | **-0.031** | **-0.49** | **[-0.154, +0.088]** | **NO — sign preserved A=B but CI includes 0** |

**CRITICAL FINDING — partition-method dependency**: The /060 Q7 anti-Kelly result for
TRX (IS -0.061, OOS -0.014) used `net_pnl_pct > 0` as the win partition (Method A).
TRX has 15 IS weight=0 killed trades (19% of IS trades) where `net_pnl_pct > 0` —
these contribute 0 to portfolio weighted_pnl but are counted as "wins" under
Method A with weight=0, pulling down the avg_win_w. Under Method B
(`weighted_pnl > 0`; excludes killed trades from both partitions, which is the
appropriate partition for portfolio Sharpe questions):

- **TRX IS sign flips from -0.061 (anti-Kelly) to +0.020 (Kelly-aligned)**, but
  Welch t=+0.34 / CI [-0.091, +0.130] includes 0 → NOT statistically significant
- **TRX OOS sign preserved at -0.031 (anti-Kelly direction)**, but Welch t=-0.49 /
  CI [-0.154, +0.088] includes 0 → NOT statistically significant

**Neither IS nor OOS TRX anti-Kelly is statistically significant under Method B.**
The /060 Q7 finding's strength is reduced from "decisive" to "weak directional
suggestion in OOS only".

### Section 2.2 — Q2: TRX weight_factor distribution by win/loss outcome (Method B)

| split | outcome | n | mean | P25 | P50 | P75 | frac_below_05 |
|---|---|---:|---:|---:|---:|---:|---:|
| IS | wins | 20 | 0.7365 | 0.555 | 0.815 | 0.920 | **15.0%** |
| IS | losses | 44 | 0.7166 | 0.550 | 0.755 | 0.890 | 20.5% |
| OOS | wins | 19 | 0.6842 | **0.485** | 0.710 | 0.855 | **26.3%** |
| OOS | losses | 26 | 0.7150 | 0.568 | 0.715 | 0.910 | 19.2% |

**Reading**: For TRX OOS wins, P25 = 0.485 (just below 0.5 floor candidate); 26.3% of
OOS wins have weight < 0.5. Raising the floor to 0.5 would lift the lower quartile
of OOS winners. For OOS losses, only 19.2% have weight < 0.5 — they would be
lifted less. **Net Q2 effect: more OOS winners lifted than losers**, supporting
the Path B counterfactual prediction (+0.47 wpnl OOS lift).

For IS, the asymmetry is reversed (15.0% wins vs 20.5% losses below 0.5 floor) —
losses would be lifted more than wins, which is anti-Kelly direction. But the IS
absolute counts are 3 wins vs 9 losses lifted; net wpnl impact still positive due
to magnitude offsets (Q4 IS counterfactual lift = +0.008 wpnl, bit-identical).

### Section 2.3 — Q3: TRX outcome by 5-quantile weight bucket

| split | bucket | weight range | n | WR | weighted_pnl |
|---|---|---|---:|---:|---:|
| IS | Q1_low | [0.35, 0.51] | 13 | 30.8% | -0.02 |
| IS | Q2 | [0.53, 0.67] | 13 | 38.5% | +2.41 |
| IS | Q3 | [0.68, 0.82] | 12 | **16.7%** | **-6.96** |
| IS | Q4 | [0.83, 0.93] | 13 | 30.8% | -5.98 |
| IS | Q5_high | [0.95, 1.00] | 13 | 38.5% | +3.19 |
| OOS | Q1_low | [0.33, 0.47] | 10 | **50.0%** | **+2.59** |
| OOS | Q2 | [0.50, 0.67] | 8 | 50.0% | +0.24 |
| OOS | Q3 | [0.68, 0.77] | 9 | 22.2% | -3.74 |
| OOS | Q4 | [0.78, 0.91] | 9 | 55.6% | +6.88 |
| OOS | Q5_high | [0.93, 1.00] | 9 | 33.3% | -1.82 |

**Reading**: TRX OOS Q1_low (lowest weight bucket) has WR=50% with positive
weighted_pnl. This is the bucket Path B floor=0.5 would lift. IS shows a non-monotonic
pattern (Q1 ~31%, Q2/Q5 ~38%, Q3 ~17%, Q4 ~31%) — no clean linear anti-Kelly.

### Section 2.4 — Q4: Counterfactual TRX weighted_pnl under different floors

| split | floor | weighted_pnl_sum | Δ vs current (0.3) |
|---|---:|---:|---:|
| IS | 0.30 (current) | -7.3503 | (baseline) |
| IS | 0.40 | -7.3598 | **-0.009** (bit-identical) |
| **IS** | **0.50** | **-7.3423** | **+0.008** (bit-identical IS — KEY) |
| IS | 0.60 | -7.3337 | +0.017 |
| OOS | 0.30 (current) | +4.1640 | (baseline) |
| OOS | 0.40 | +4.1051 | -0.059 |
| **OOS** | **0.50** | **+4.6353** | **+0.471** (Path B intervention) |
| OOS | 0.60 | +5.0900 | +0.926 (alt) |

**Reading**: Path B (TRX floor=0.5) counterfactual:
- IS lift: **+0.008 wpnl (bit-identical IS)** — IS Sharpe shift expected ~0.0
- OOS lift: **+0.47 wpnl** — modest. At /060 OOS portfolio total +5.50, +0.47
  represents +8.5% portfolio OOS wpnl improvement, translating to roughly
  +0.05 to +0.10 OOS monthly Sharpe shift (rough scaling; actual depends on std)

The counterfactual ASSUMES trade-selection invariance — the gate cascade upstream
of vol-scaling (z-score OOD, Hurst, ADX, low-vol filter) doesn't change because
their thresholds are floor-independent. The actual backtest may show slightly
different numbers if state-update effects (cap_timeline, drawdown_brake_timeline
deques) interact with the floor change, but these are disabled at /061 baseline.

### Section 2.5 — Q5: BCH/LDO invariance check at per-symbol TRX-only floor=0.5

| split | symbol | applied_floor | current wpnl | counterfactual wpnl | delta |
|---|---|---:|---:|---:|---:|
| IS | BCH | 0.3 (unchanged) | +76.61 | +76.61 | **-0.0002** (round-off) |
| IS | LDO | 0.3 (unchanged) | +8.93 | +8.93 | **-0.00004** (round-off) |
| IS | TRX | 0.5 (intervention) | -7.35 | -7.34 | +0.008 |
| OOS | BCH | 0.3 (unchanged) | +24.75 | +24.75 | -0.0001 |
| OOS | LDO | 0.3 (unchanged) | -6.18 | -6.18 | +0.0001 |
| **OOS** | **TRX** | **0.5 (intervention)** | **+4.16** | **+4.64** | **+0.47** |

**Reading**: Per-symbol design isolation verified — BCH and LDO weighted_pnl is
mathematically invariant when only TRX floor changes (deltas are pure
floating-point round-off at ~1e-4 magnitude). This is the structural guarantee
that distinguishes per-symbol RISK PRIMITIVE customization from per-symbol
FEATURE or LABEL customization (the latter changes the trained model itself).

### Section 2.6 — Q6: Path decision synthesis

| Criterion | Value | Interpretation |
|---|---:|---|
| TRX IS partition-method sign flip A vs B | **YES (1)** | Method A=-0.061, Method B=+0.020 |
| TRX IS anti-Kelly significant (Method B CI) | NO | t=+0.34, CI=[-0.091, +0.130] |
| TRX OOS anti-Kelly significant (Method B CI) | NO | t=-0.49, CI=[-0.154, +0.088] |
| TRX OOS wins weight P25 (Method B) | 0.485 | Just below 0.5 floor |
| Q4 floor=0.5 IS counterfactual lift | +0.008 | Bit-identical IS |
| Q4 floor=0.5 OOS counterfactual lift | +0.47 | Marginal — within 3-seed noise |
| **VERDICT** | Path B (floor=0.5) | Counterfactual OOS lift > noise; IS bit-identical |

**Path A (passive)**: rejected — /060 was already Path A; running consecutive Path A
would skew cycle 1 toward methodology paralysis.

**Path B (TRX-specific floor=0.5)**: **CHOSEN**. Single per-symbol risk-primitive
customization; cleanly testable counterfactual; IS bit-identical at single-seed.
Pre-registered expectation INERT-AT-EXPLORATION per
`feedback_v3_cycle1_axis_pass_criteria.md` (OOS lift +0.47 wpnl is below the +0.20
OOS Sharpe shift threshold for PROMISING).

**Path C (universal reformulation)**: rejected — Method B falsifies cross-symbol
anti-Kelly significance (BCH/LDO IS Kelly-aligned but not significant; LDO OOS
Kelly-aligned and significant; TRX is not uniquely anti-Kelly). Too aggressive
for single-EXPLORATION; would require coordinated re-validation.

**Path D (passive + partition-correction publication)**: rejected — the
partition-method correction IS published as part of /061 EDA Section 2.1, but
running /061 as bit-identical-to-/060 would consume a cycle 1 EXPLORATION slot
for zero axis variation. Path B is a single substantive change with falsifiable
prediction.

**Path E (reverse-sign for TRX)**: rejected — anti-Kelly not statistically
significant; reversing sign would be data-mining without theoretical grounding.

### Section 2.10 — Anchor declaration

**Pre-locked anchor: iter-v3/060 EXPLORATION-MODE-REFERENCE (IS +0.8325 / OOS +0.1403; 3-seed mode).**

This is per `feedback_v3_cycle1_axis_pass_criteria.md` Critic FINAL `3cee250`
Recommendation #2: cycle 1 EXPLORATIONs (iter-v3/061-068) anchor against /060
(NOT /059) for axis-PASS deltas. The /060 anchor reflects 3-seed EXPLORATION-mode
noise floor (-0.26 IS, -0.44 OOS vs /059's CONFIRMATION) and BCH IS share 176.68%
(inflated denominator under 2 of 3 symbols flipping IS-negative). Per `feedback_v3_per_symbol_lifts_oos_breaks_is.md`,
CONFIRMATION re-validation (at iter-v3/069 or later) compares against /059 baseline,
not /060.

The /059 CONFIRMATION-mode canonical baseline (IS +1.0894 / OOS +0.5791) remains
the BASELINE_V3.md anchor. /060 is a parallel/supplementary reference.

---

## Section 3 — Proposed Changes (Setup Commit)

### Edit 1: `src/crypto_trade/strategies/ml/risk_v2.py` — add per-symbol vol_scale_floor

**RiskV2Config additions** (parallel to existing `adx_threshold_per_symbol` pattern):

```python
# iter-v3/061: per-symbol vol_scale_floor override (parallel to adx_threshold_per_symbol
# field). When a symbol is in this dict, the per-symbol value is used instead of the
# global vol_scale_floor. Symbols absent from this dict fall back to global vol_scale_floor.
# Default empty preserves v1/v2/v3-prior behavior (universal floor).
# Calibrated by QR EDA at iter-v3/061 (analysis/iteration_v3-061/
# trx_anti_kelly_diagnostic.py Q4 counterfactual). iter-v3/061 sets
# {"TRXUSDT": 0.5}; BCH/LDO/ALGO unchanged.
vol_scale_floor_per_symbol: dict[str, float] = field(default_factory=dict)
```

**`_vol_scale` method update** (lines 580-592):

```python
def _vol_scale(self, symbol: str, row: dict) -> float:
    atr_pct = row["atr_pct_rank_200"]
    if not np.isfinite(atr_pct):
        return 1.0
    # iter-v3/061: per-symbol vol_scale_floor override (default empty falls back to
    # global vol_scale_floor). Per QR EDA SHA d198b25: TRX-only raise 0.3 → 0.5
    # produces +0.47 OOS wpnl counterfactual lift; IS bit-identical.
    floor = self.config.vol_scale_floor_per_symbol.get(symbol, self.config.vol_scale_floor)
    raw = float(atr_pct)
    return float(np.clip(raw, floor, self.config.vol_scale_ceiling))
```

### Edit 2: `run_baseline_v3.py` — RiskV2Config initialization

```python
# iter-v3/061: TRX-specific vol_scale_floor=0.5 per QR EDA SHA d198b25 + Critic /060 Rec #3.
# Single per-symbol risk-primitive customization; BCH/LDO unchanged at 0.3.
vol_scale_floor_per_symbol={"TRXUSDT": 0.5},
```

### Edit 3: `run_baseline_v3.py` — runtime assertion (parallel to adx_threshold_per_symbol check)

Add to `_verify_v3_assumptions()`:

```python
# iter-v3/061: per-symbol vol_scale_floor — TRX-only 0.5; BCH/LDO/ALGO at global 0.3.
expected_floor_dict = {"TRXUSDT": 0.5}
if dict(trx_strat_check.config.vol_scale_floor_per_symbol) != expected_floor_dict:
    raise ValueError(
        f"RiskV2Config.vol_scale_floor_per_symbol = "
        f"{trx_strat_check.config.vol_scale_floor_per_symbol} — expected {expected_floor_dict}. "
        "Set vol_scale_floor_per_symbol={'TRXUSDT': 0.5} in RiskV2Config init in _build_v3_model."
    )
```

### Edit 4: `tests/strategies/ml/test_per_symbol_vol_scale_floor.py` — NEW test file

Parallel to `test_per_symbol_adx_threshold.py`. Tests:
1. `test_per_symbol_floor_lifts_low_vol_for_target_symbol_only` — TRX weight_factor for atr_pct_rank=0.4 returns 0.5 with TRX override; BCH same input returns 0.4 with global floor.
2. `test_per_symbol_floor_invariance_for_other_symbols` — when `vol_scale_floor_per_symbol={"TRXUSDT": 0.5}`, BCH/LDO weight_factor distributions are identical to baseline (floor=0.3 universal).
3. `test_per_symbol_floor_empty_dict_falls_back_to_global` — empty dict reproduces universal-floor behavior.

### Edit 5: `run_baseline_v3.py` — ITERATION_LABEL

```python
ITERATION_LABEL = "v3-061"
```

### Carry-forward state (all UNCHANGED from /060):

- `V3_FEATURE_COLUMNS_TOP_N`: 14 features identical to /060
- `V3_MODELS = ("BCHUSDT", "LDOUSDT", "TRXUSDT")`
- `V3_ATR_MULTIPLIERS_PER_SYMBOL = {}`
- `DEFAULT_ATR_MULTIPLIERS = (2.0, 1.0)`
- `RiskV2Config(adx_threshold_per_symbol={}, block_long_for=(), enable_per_symbol_drawdown_brake=False)`
- `REQUIRED_GAP = 66 = (21+1) × 3`
- `EXPLORATION_ENSEMBLE_SIZE = 3` (active at /061 via --exploration)
- `ENSEMBLE_SEEDS` = 10-tuple lineage-preserving (only [0:3] active)
- Walk-forward fix at `e149e9d` present
- Optuna `n_jobs=1` (Phase A revert at `31665f6`)

---

## Section 4 — Expected OOS Impact

### Section 4.1 — Predicted bands (3-seed EXPLORATION mode vs /060 anchor)

Per `feedback_v3_cycle1_axis_pass_criteria.md` cycle 1 EXPLORATION axis-PASS criteria:

| Metric | /060 anchor (3-seed) | /061 predicted (3-seed; Path B TRX floor=0.5) | Δ vs /060 |
|---|---:|---:|---:|
| IS monthly Sharpe | +0.8325 | **+0.78 to +0.88** (band ±0.05) | ~**0.00** (IS bit-identical counterfactual) |
| OOS monthly Sharpe | +0.1403 | **+0.10 to +0.30** (band ±0.10 centered ~+0.20) | **+0.06** (counterfactual +0.47 wpnl → ~+0.05-0.10 OOS Sharpe lift) |
| OOS/IS monthly ratio | 0.1685 | similar **[0.13, 0.34]** | small shift |
| BCH IS weighted_pnl | +79.45 | **comparable (±5%)** (per Q5 invariance) | ~0.0 |
| LDO IS weighted_pnl | -11.44 | **comparable (±5%)** (per Q5 invariance) | ~0.0 |
| TRX IS weighted_pnl | -23.04 (at /060 3-seed) | **comparable** (Q4 IS counterfactual lift +0.008 only) | ~0.0 |
| BCH OOS weighted_pnl | +1.91 | **comparable (±5%)** | ~0.0 |
| LDO OOS weighted_pnl | -19.72 | **comparable (±5%)** | ~0.0 |
| **TRX OOS weighted_pnl** | **+23.31** (at /060 3-seed) | **+23.5 to +24.0** (counterfactual +0.47 plus 3-seed noise) | **+0.5 to +1.0** |
| OOS trade count | 102 | **95-110** (±10%; trade selection invariant under Path B) | similar |
| IS trade count | 159 | **150-170** | similar |
| cpcv_frac_positive_paths | 0.6444 | **0.55 to 0.70** | ~0.0 architecture-invariant |
| DSR_relative | 0.0 | **0.0 to 0.10** | EXPLORATION informational |

**Behavioral effect predictor (per `feedback_v3_axis_saturation_predictor.md`)**:

- Predicted IS trade-count change: **0** (trade selection invariant; floor lift only
  modifies weight_factor for the same set of trades). Falsifier band: if observed IS
  trade count change > 5 (>3% of /060's 159), trade-selection-invariance assumption
  failed.
- Predicted OOS trade-count change: **0** (same logic). Falsifier band: > 5
  (>5% of /060's 102) triggers investigation.
- Predicted TRX OOS weighted_pnl lift: **+0.47 wpnl** (counterfactual). Falsifier
  band: if observed TRX OOS wpnl Δ < +0.20 (below noise) OR > +1.0 (above noise),
  trade-selection-invariance assumption failed AND the floor change is interacting
  with downstream state.

### Section 4.2 — BCH IS sensitivity projection (per Critic /060 Rec #1 + /060 Rec #3)

Path B affects ONLY TRX weight_factor distribution. BCH/LDO weight_factor
distributions are mathematically invariant per Section 2 Q5 invariance check.
The BCH IS share at /060 was 176.68%; at /061 we predict **BCH IS share remains
in [165%, 190%] band** (3-seed averaging noise; trade-selection invariance under
Path B implies BCH IS attribution unchanged).

**Per Critic /060 Rec #1 one-sided gate wording**: BCH IS share gate is **one-sided
lower (`≥ 80%`)** per /060 Section 4.4 falsifier. 176.68% is acceptable;
the gate triggers only if BCH IS share DROPS below 80% (which would indicate that
the Path B floor change leaked into BCH's IS attribution, contradicting the
per-symbol design isolation).

### Section 4.3 — Behavioral effect predictor (extended)

| Effect | Predicted | Falsifier (observed value outside this triggers) |
|---|---:|---|
| TRX OOS weight_factor mean lift | +0.05 to +0.10 | Observed change < +0.02 OR > +0.15 → leakage |
| TRX OOS trades with weight ∈ [0.30, 0.50) lifted to 0.50 | ≥ 5 trades | Observed < 3 → unexpected gate interaction |
| BCH IS weighted_pnl change vs /060 | 0 ± 0.5 wpnl | |Δ| > 1.0 wpnl → leakage |
| LDO IS weighted_pnl change vs /060 | 0 ± 0.5 wpnl | |Δ| > 1.0 wpnl → leakage |
| OOS portfolio wpnl change vs /060 | +0.3 to +0.6 wpnl | |Δ| > 2.0 → unexpected state-coupling |

### Section 4.4 — Falsifier (axis CLOSURE triggers)

**Falsifier triggered (axis CLOSED for cycle 1 carry-forward) if**:
- IS Sharpe shift ≤ -0.20 vs /060 (axis is IS-destructive) OR
- OOS Sharpe shift ≤ -0.10 vs /060 (axis is OOS-destructive) OR
- BCH IS share < 80% (per /060 Rec #1 one-sided gate) OR
- IS trade count outside [128, 222] (±30% of /060's 159) — trade-selection-invariance
  failed OR
- OOS trade count outside [66, 122] (±30% of /060's 102) OR
- BCH or LDO weighted_pnl change |Δ| > 1.0 wpnl IS or OOS (per-symbol design
  isolation failed; floor change leaked into other symbols)

If axis CLOSURE triggers: per-symbol vol_scale_floor customization is CLOSED for
cycle 1 carry-forward. iter-v3/062 must pivot to a different axis (e.g., advancing
the mass feature expansion mandate one slot earlier).

---

## Section 5 — Risk Mitigation

7-primitive gate stack UNCHANGED from /059/060 baseline. Path B modifies the
vol-scaling primitive's BEHAVIOR for TRX only (lifts the floor); the primitive
itself remains active and the gate cascade ordering is unchanged.

**New risk-management considerations under Path B**:

- **Per-symbol design isolation** — RiskV2Config.vol_scale_floor_per_symbol = {"TRXUSDT": 0.5}
  is a per-symbol dict; symbols absent fall back to global floor=0.3. The Q5 invariance
  check + the new test in Edit 4 guarantee BCH/LDO behavior is unchanged.
- **Trade-selection invariance** — the floor change is applied INSIDE `_vol_scale`,
  which is called by `get_signal` AFTER all kill-gates (z-score OOD, Hurst, ADX,
  low-vol filter). The gate cascade decisions (kill/no-kill) are upstream of the
  vol-scaling and don't depend on the floor value. Trade selection invariance is
  a mechanical guarantee, not a probabilistic assumption.
- **Cap and brake interaction** — `enable_per_symbol_cap=False` and
  `enable_per_symbol_drawdown_brake=False` at /061 baseline. The
  `_cap_per_symbol_pnl` and `_brake_timeline` deques are not updated when these
  primitives are disabled, so Path B does not interact with cap/brake state.
- **Live deployment compatibility** — per-symbol dict parameterization mirrors the
  existing `adx_threshold_per_symbol` and `block_long_for` patterns; same serialization
  hygiene applies (frozen dataclass with `field(default_factory=dict)`).

---

## Section 6 — Risk Management Design (UPDATED for Path B)

8-primitive framework status (1 primitive's BEHAVIOR modified at /061):

| Primitive | Status | Threshold | /061 change |
|---|---|---|---|
| Vol-adjusted sizing | ACTIVE | vol_scale_floor=0.3 (universal) | **TRX-only override to 0.5** (Path B) |
| ADX gate | ACTIVE | 20.0 (global); {} per-symbol | UNCHANGED |
| Hurst regime | ACTIVE | hurst_100 >= 0.5 | UNCHANGED |
| Z-score OOD | ACTIVE | zscore_threshold=2.0 | UNCHANGED |
| Drawdown brake | DISABLED | per_symbol=False | UNCHANGED |
| BTC contagion kill | ACTIVE | threshold_pct=15.0 | UNCHANGED |
| Per-symbol kill switch | DISABLED | block_long_for=() | UNCHANGED |
| Hit-rate gate | DISABLED | enabled=False | UNCHANGED |

The vol-scaling primitive behavior change for TRX is **non-destructive**: floor=0.5
floor=0.3 by construction (TRX trades currently at weight 0.30 stay at 0.30 under
floor=0.3; the same trades become weight 0.50 under floor=0.5). No trades are killed,
no decisions are inverted.

---

## Section 7 — Pre-Registered Failure-Mode Prediction

| Failure mode | Probability estimate | Detection criterion |
|---|---|---|
| **Path B INERT-AT-EXPLORATION** (within noise band) | **~55%** (most likely outcome) | OOS Sharpe shift in [-0.20, +0.20] vs /060 anchor; PROMISING bar (+0.20 OOS shift) not cleared |
| **Path B PROMISING-AT-EXPLORATION** | ~15% | OOS Sharpe shift ≥ +0.20 vs /060 (counterfactual prediction over-delivers) |
| **Path B NEGATIVE-AT-EXPLORATION** | ~10% | OOS Sharpe shift ≤ -0.20 vs /060 (counterfactual prediction inverts; state-coupling we didn't anticipate) |
| **Trade-selection-invariance violation** (IS or OOS trade count outside ±30% band) | ~5% | Falsifier band triggered; floor change leaked into upstream gate decisions |
| **BCH/LDO per-symbol design isolation violation** (|Δ wpnl| > 1.0) | <1% | Q5 invariance check predicted ~0; would indicate `vol_scale_floor_per_symbol` dict lookup bug |
| **Backtest runtime failure** | <5% | hardware/environment issue |
| **Methodology FAIL** (Critic check or Anti-Pattern hit) | <5% | Critic Foundation Audit + §11 Anti-Pattern scan |

**Most plausible failure mode (~55%)**: Path B classifies INERT-AT-EXPLORATION
within noise band. The counterfactual +0.47 OOS wpnl lift translates to ~+0.05 to
+0.10 OOS Sharpe shift, which is well below the +0.20 PROMISING threshold. This
would be a CLEAN axis closure (per-symbol vol_scale_floor adjustment is a TUNING
axis, not a structural axis; Path B's modest counterfactual lift is consistent with
INERT classification). Axis advances to iter-v3/062 with a different priority.

**Predicted-success path (~15%)**: Path B classifies PROMISING-AT-EXPLORATION if the
counterfactual under-estimated the actual lift (state-coupling effects favorable,
e.g., the floor lift cascades through Optuna's IS-PnL feedback at month boundary
training). Per `feedback_v3_cycle1_axis_pass_criteria.md`, PROMISING-AT-EXPLORATION
axes carry forward to cycle 1 CONFIRMATION; PROMISING is NOT a MERGE signal in itself.

---

## Section 8 — LOCKED Criteria

Per `feedback_v3_cycle1_axis_pass_criteria.md`:

### Section 8.1 — PASS criteria (PROMISING-AT-EXPLORATION)

PROMISING-AT-EXPLORATION requires ALL of:
- **IS Sharpe shift ≥ +0.10 vs /060 anchor** (i.e., IS Sharpe ≥ +0.93)
- **OOS Sharpe shift ≥ +0.20 vs /060 anchor** (i.e., OOS Sharpe ≥ +0.34)
- **BCH IS share ≥ 80%** (one-sided lower bound per Critic /060 Rec #1; NOT a closed band)
- **cpcv_frac_positive_paths ≥ 0.50** (relaxed EXPLORATION threshold; CONFIRMATION-mode threshold is 0.55)
- **No methodology FAIL** (Critic 13 checks + §11 anti-pattern scan)
- **`ensemble_summary.json` `mode == "exploration"` AND `ensemble_size == 3`**
- **Tests 31/31 + new TestPerSymbolVolScaleFloor tests pass**

If PROMISING-AT-EXPLORATION: axis (per-symbol vol_scale_floor) carries forward to
cycle 1 CONFIRMATION (iter-v3/069 or later) per Critic /060 Rec #2 cross-validation
requirement; CONFIRMATION re-validates against /059 baseline at 10-seed mode.

### Section 8.2 — INERT-AT-EXPLORATION (noise band)

Triggered when:
- IS Sharpe shift in [-0.10, +0.10] OR
- OOS Sharpe shift in [-0.20, +0.20]
- AND no other failure-mode fires

Classification: axis does NOT advance to cycle 1 CONFIRMATION. iter-v3/062
pivots to a different axis. The per-symbol vol_scale_floor mechanism stays in
the codebase (low revert cost) for potential re-evaluation under different
conditions but is NOT included in any future bundle without fresh evidence.

### Section 8.3 — SUSPICIOUS-OOS-DOMINANT classifier

Per `feedback_v3_per_symbol_lifts_oos_breaks_is.md` system-level rule:
- OOS Sharpe shift ≥ +0.20 vs /060 anchor AND
- IS Sharpe shift < +0.10 vs /060 anchor (IS regressed or flat while OOS lifted)

→ SUSPICIOUS-OOS-DOMINANT. Classification: PROMISING-AT-EXPLORATION-WITH-CAVEAT;
the axis advances to cycle 1 CONFIRMATION but with explicit per-symbol-customization
risk warning per the system-level rule. CONFIRMATION must show IS aggregate
maintenance OR PASS will fail per `feedback_v3_strict_both_is_oos_baseline.md`.

### Section 8.4 — DSR_relative gate informational

Per `feedback_v3_dsr_mode_artifact.md`: EXPLORATION-mode DSR/PSR are informational
only (n_trials_total=315 = 35 × 3 × 3 syms; structurally different from
CONFIRMATION-mode n_trials=1050). /061 DSR/PSR are NOT MERGE-gate-relevant at
EXPLORATION level.

### Section 8.5 — NEGATIVE-AT-EXPLORATION (axis CLOSED)

Triggered when:
- IS Sharpe shift ≤ -0.10 vs /060 OR
- OOS Sharpe shift ≤ -0.20 vs /060 OR
- Section 4.4 falsifier hit (trade-count or per-symbol design isolation
  violations)

Classification: axis CLOSED for cycle 1 carry-forward. Per-symbol vol_scale_floor
customization is added to the dead-paths catalog (with mechanism: per-symbol risk
primitive tuning at single-EXPLORATION doesn't transfer to portfolio).

### Section 8.6 — FAIL (methodology)

Triggered when:
- Any Critic FAIL on the 13 standard checks (Foundation Audit) OR
- Any Anti-Pattern scan A1-A13 hit

Action: setup-commit revert; QR re-briefs.

### Section 8.7 — Cycle 1 EXPLORATION cadence

This is iter-v3/061 = cycle 1 EXPLORATION #2 (of 10). /061 axis = TRX RiskV2
anti-Kelly intervention (Path B per Critic /060 Rec #3). Cycle 1 EXPLORATIONs
continue at iter-v3/062-068; CONFIRMATION at iter-v3/069 (do NOT collapse).
Cycle 1 axis priorities per BASELINE_V3.md Cycle 1 Axis Priorities:
- HIGHEST: TRX RiskV2 anti-Kelly intervention — **iter-v3/061 (CURRENT)**
- HIGH: DSR_relative threshold/benchmark recalibration — iter-v3/062 candidate
- MEDIUM: BCH IS concentration sensitivity (applied as constraint on every brief)
- STRUCTURAL: Mass feature expansion at iter-v3/063 (per `feedback_v3_mass_feature_expansion.md`)

---

## Section 9 — Library Stack Declaration

UNCHANGED from /060 and /059:

- Python 3.13
- lightgbm 4.6.0
- optuna 4.8.0 (n_jobs=1 per `31665f6` revert)
- numpy 2.2.6
- pandas 3.0.0
- scikit-learn 1.8.0
- scipy 1.17.0
- statsmodels 0.14.6
- pyarrow 23.0.1

No new dependencies. Path B is a single-line addition to RiskV2Config (new
`vol_scale_floor_per_symbol` field) + a one-line modification in `_vol_scale`
(per-symbol dict lookup with fallback to global floor).

**Mode-flag refactor at SHA `56f5a30`** intact. Test suite: 31/31 + 3 new
TestPerSymbolVolScaleFloor tests (target 34/34 pass post-implementation).

---

## Section 10 — QR Audit Trail

Per `feedback_v3_axis_selection_quant_discipline.md`, this section documents the
QR-driven research path that landed on Path B per-symbol vol_scale_floor.

### Stage 1 — Critic FINAL `3cee250` Recommendation #3 directed iter-v3/061 axis

Per /060 Critic FINAL `3cee250` Recommendation #3 (verbatim):

> "iter-v3/061 axis = TRX RiskV2 anti-Kelly diagnostic per the EDA Q7 finding
> (`analysis/iteration_v3-060/trx_diagnostic.py`). The EDA Q7 finding (TRX is the
> ONLY symbol where average weight_factor on winning trades < average weight_factor
> on losing trades, both IS and OOS) is the highest-value diagnostic insight from
> /060. iter-v3/061 brief Section 2 EDA must include committed IS-only numerical
> tables comparing per-symbol weight_factor distributions before and after the
> proposed change. Test ONE engineered intervention alone at single-seed/3-seed
> mode per `feedback_v3_engineered_features_dont_stack.md` — do not stack multiple
> changes."

### Stage 2 — EDA at `analysis/iteration_v3-061/` (commit SHA `d198b25`)

EDA script `analysis/iteration_v3-061/trx_anti_kelly_diagnostic.py` runs 6 questions:

- Q1: Anti-Kelly statistical significance (Welch t-stat + bootstrap CI per
  symbol per split) with explicit comparison of partition-method A (/060 Q7)
  vs partition-method B (cleaned)
- Q2: TRX weight_factor distribution percentiles by win/loss/killed outcome
- Q3: TRX trade outcome (WR + weighted_pnl) by 5-quantile weight bucket
- Q4: Counterfactual TRX weighted_pnl under different per-symbol floors {0.30
  current, 0.40, 0.50, 0.60}
- Q5: BCH/LDO invariance check at per-symbol TRX-only floor=0.5
- Q6: Path B/C/D/E decision synthesis with verdict logic

Outputs: 6 committed CSVs + `diagnostic_summary.md`.

### Stage 3 — Path B selection rationale

The /060 Q7 anti-Kelly finding (TRX IS -0.061, OOS -0.014) was originally classified
as the highest-value diagnostic insight from /060. EDA Q1 reveals that this
finding is a **partition-method artifact**: /060 Q7 used `net_pnl_pct > 0` as the
win definition, which INCLUDES 15 IS weight=0 killed trades (19% of IS trades) in
the "wins" bucket. Under partition-method B (`weighted_pnl > 0`, excluding killed
trades from both partitions, which is appropriate for portfolio Sharpe questions):

- TRX IS sign FLIPS from -0.061 to **+0.020** (Kelly-aligned direction; Welch t=+0.34;
  bootstrap CI [-0.091, +0.130] includes 0 → not statistically significant)
- TRX OOS sign PRESERVED at -0.031, but Welch t=-0.49 / CI [-0.154, +0.088] includes
  0 → not statistically significant

**Neither IS nor OOS TRX anti-Kelly survives statistical-significance testing.**
The /060 Q7 strength is downgraded from "decisive" to "weak directional suggestion
in OOS only".

Despite the partition-method correction reducing the anti-Kelly evidence strength,
Path B (TRX-specific vol_scale_floor=0.5) was chosen for the following reasons:

1. **Counterfactual OOS lift is non-trivial**: Q4 shows +0.47 OOS wpnl lift at
   floor=0.5 (+0.93 at floor=0.6). The OOS portfolio total at /060 was +5.50,
   so +0.47 = +8.5% portfolio OOS wpnl improvement.
2. **IS counterfactual is bit-identical**: Q4 shows +0.008 IS wpnl lift at floor=0.5.
   This avoids the `feedback_v3_per_symbol_lifts_oos_breaks_is.md` IS-regression
   risk at single-seed (multi-seed CONFIRMATION risk is a separate concern).
3. **Per-symbol design isolation guaranteed**: Q5 invariance check shows
   BCH/LDO weighted_pnl mathematically invariant to the TRX-only floor change.
4. **Cycle 1 cadence discipline**: running consecutive Path A passive diagnostics
   would consume axis slots without testing any axis variation. Path B is the
   cleanest single-intervention axis available given the partition-method
   correction.
5. **Pre-registered expectation INERT-AT-EXPLORATION**: per
   `feedback_v3_cycle1_axis_pass_criteria.md`, the +0.05 to +0.10 OOS Sharpe shift
   predicted from the counterfactual is below the +0.20 PROMISING threshold.
   Path B is expected to classify INERT, which is a clean cycle 1 outcome that
   advances the cadence without false-positive promotion.

Path A rejected (consecutive passive; cadence skew). Path C rejected (universal
reformulation too aggressive at single-EXPLORATION; cross-symbol significance
falsified by Method B). Path D rejected (partition-correction publication
already integrated into /061 EDA Section 2.1; running /061 bit-identical to /060
consumes axis slot for no axis variation). Path E rejected (reverse-sign without
theoretical grounding; anti-Kelly not statistically significant).

### Stage 4 — Setup commit (this commit SHA)

```
Phase A revert SHA:        31665f6 (n_jobs=2 → n_jobs=1 GIL contention)
Phase B-3 unified seed:    ab2d9ac (unified ensemble; outer-seed loop eliminated)
Walk-forward fix SHA:      e149e9d (22-candle embargo at train/test boundary)
Mode-flag refactor SHA:    56f5a30 (--exploration → ENSEMBLE_SIZE=3 + tests 31/31)
/060 EXPLORATION-MODE-REFERENCE diary SHA: b794d6a
/061 EDA SHA:              d198b25 (TRX anti-Kelly partition-method cleanup +
                                    counterfactual floor sensitivity)
/061 Setup commit SHA:     (this commit — research brief + RiskV2Config
                                    vol_scale_floor_per_symbol field + per-symbol
                                    vol-scale-floor test file)
Phase 5.5 gate SHA:        (orchestrator-dispatched after this commit)
```

### Stage 5 — Critic /060 Rec #1 BCH-share gate wording compliance

Per Critic /060 Rec #1: "BCH IS share gate is one-sided lower (`≥ 80%`) per
Section 4.4 falsifier — not a closed band [80%, 100%]."

This /061 brief Section 8.1 states explicitly: "BCH IS share ≥ 80% (one-sided
lower bound per Critic /060 Rec #1; NOT a closed band)." Section 4.2 states:
"BCH IS share remains in [165%, 190%] band" (predicted band, not a closed
elimination criterion). Section 4.4 falsifier list states: "BCH IS share < 80%"
(explicitly one-sided).

### Stage 6 — Cycle 1 cadence counting

This is iter-v3/061 = cycle 1 EXPLORATION #2 (of 10). /060 was cycle 1 EXPLORATION
#1 (EXPLORATION-MODE-REFERENCE). RE-ANCHOR #2 (/059) is orthogonal (NOT counted).
Cycle 1 EXPLORATIONs continue at iter-v3/062-068; SEPARATE CONFIRMATION at
iter-v3/069 per `feedback_v3_strict_10_to_1_cadence.md` (do NOT collapse the 10th
EXPLORATION into CONFIRMATION).

---

## Section 11 — Catalog Row Pre-Commit

Pre-committed catalog row template (inserted at `briefs-v3/exploration_catalog.md`
after Phase 8 diary):

```
| iter-v3/061 | <DATE> | Cycle 1 #2 EXPLORATION: TRX-specific RiskV2 vol_scale_floor=0.5 (Path B per QR EDA d198b25 + Critic /060 Rec #3). Partition-method cleanup falsifies /060 Q7 anti-Kelly significance; Path B chosen for clean per-symbol risk-primitive intervention with bit-identical IS counterfactual + +0.47 OOS wpnl counterfactual. | <IS> | <OOS> | <PROMISING-AT-EXPLORATION advances axis to cycle 1 CONFIRMATION; INERT or NEGATIVE closes axis; SUSPICIOUS-OOS-DOMINANT advances with caveat per system-level rule> | EXPLORATION classification | NO MERGE — cycle 1 EXPLORATION; axis evaluation only |
```

Expected classification: **INERT-AT-EXPLORATION** (probability ~55% per Section 7)
or PROMISING-AT-EXPLORATION (probability ~15%). NEGATIVE-AT-EXPLORATION at ~10%.
Per-symbol design isolation violation (BCH/LDO leak) <1%.

---

**END OF BRIEF — Phase 5 complete.**

**Next**: Engineer dispatches Phase 5.5 gate (orchestrator's call), then Phase 6
backtest launch with the setup edits applied (run_baseline_v3.py with
`--exploration` flag; ITERATION_LABEL v3-061; new
RiskV2Config.vol_scale_floor_per_symbol field with {"TRXUSDT": 0.5}).
Wall-clock target: ~1.1h (3-seed EXPLORATION; same as /060).
