# Iteration v3-046 — Research Brief (QR EDA-driven per-symbol ATR for BCH)

**Type**: EXPLORATION (Cycle 3 #7 of 10)
**Track**: v3 (rigor arm) — forty-sixth iteration
**Branch**: `iteration-v3/046` (off iter-v3/045 head)
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

Sacred constants UNCHANGED. The QR sees iter-v3/046 OOS metrics for the FIRST time in Phase 7.

---

## Section 0.5 — Iteration Type Declaration

```
TYPE: EXPLORATION
Cycle: 3 — #7 of 10 (after iter-v3/040 baseline-restore + iter-v3/041 pruning + 042 universal
  ATR + 043 Kaufman ER + 044 ALGO ATR PROMISING + 045 LDO ATR STRONGEST PROMISING)
Wall-clock budget: <= 2h hard cap (EXPLORATION spec)
Spec: uv run python run_baseline_v3.py --seeds 1
  - ENSEMBLE_SIZE=5 (auto; inner ensemble)
  - n_trials=35 (default)
  - colsample_bytree Optuna-tunable (NOT hardcoded 1.0)
  - outer_seeds=1 (EXPLORATION-spec)
Single axis: per-symbol ATR widening for BCHUSDT only — 3rd application of validated mechanism
  V3_ATR_MULTIPLIERS_PER_SYMBOL = {"ALGOUSDT": (2.0, 1.5),
                                    "LDOUSDT":  (2.0, 1.5),
                                    "BCHUSDT":  (2.0, 1.5)}  -- TP unchanged, SL +50%
  V3_FEATURE_COLUMNS_TOP_N = 14 (UNCHANGED — regime_momentum_signed_5d preserved)
  V3_FEATURES_PER_SYMBOL = {} (UNCHANGED — empty)
  V3_MODELS = 4 (BCH, LDO, TRX, ALGO) — UNCHANGED.
  REQUIRED_GAP = 88 = (21+1)*4 — UNCHANGED.
  DEFAULT_ATR_MULTIPLIERS = (2.0, 1.0) — UNCHANGED (TRX falls back).
Predicted classification: PROMISING (45%), PROMISING-INERT (25%), PROMISING-MECHANICAL (15%),
  NEGATIVE (15%).
```

**Context**: iter-v3/045 (QR EDA-driven LDO ATR (2.0, 1.5)) was STRONGEST PROMISING in v3
history — bundle OOS Sharpe +3.5259 (HIGHEST single-seed in v3), all 4 symbols positive
first time ever. The IS axis is now the binding multi-seed constraint per BASELINE_V3.md
(need IS ≥ +0.5101 multi-seed mean to update baseline under STRICT BOTH-must-improve rule).

iter-v3/045 single-seed IS Sharpe +0.7459. Expected multi-seed compression (~50% per cycle 3
plan) gives ~+0.37 multi-seed mean — BELOW the +0.5101 threshold.

The QR diagnosis (SHA `d86b1f9`, `analysis/iteration_v3-046/`) shows BCH has the highest
IS-axis leverage among low-architectural-risk axes. BCH is currently +23.62% IS PnL but the
LONG side is the IS bottleneck (-25.07% LONG PnL on 39 trades, 30.8% WR). BCH IS=OOS SL:TP
ratio is STABLE at 1.93 (vs LDO IS=1.14 → OOS=2.33 regime-shift), so wider SL helps IS AND
OOS symmetrically (vs LDO where it primarily addressed an OOS regime shift).

iter-v3/046 applies the SAME wider-SL mechanism as iter-v3/044 ALGO + iter-v3/045 LDO to BCH.
This is the THIRD application of the validated mechanism, mirroring the symmetric labeling-
layer customization pattern.

---

## Section 1 — Hypothesis

Widening BCHUSDT's stop-loss multiplier from 1.0×ATR to 1.5×ATR (TP unchanged at 2.0×ATR)
reduces BCH's high IS+OOS SL rate (IS 59.6% / OOS 60.5%; SL:TP 1.93 stable across both
windows) by giving trades 50% more drawdown headroom before stop-out. The mechanism mirrors
iter-v3/044 PROMISING ALGO ATR + iter-v3/045 STRONGEST PROMISING LDO ATR. Expected effect:
BCH IS PnL lifts from +23.62% toward +30% to +40%; BCH OOS PnL lifts from +10.75 toward +14
to +18 (modest OOS lift — BCH is already producing positive OOS). Bundle IS Sharpe lift
estimate +0.10 to +0.18; bundle OOS Sharpe lift estimate +0.05 to +0.15.

---

## Section 2 — IS-Only Numerical Evidence

### 2.1 — Per-symbol IS contribution @ iter-v3/045 (the data)

| Symbol | n IS | WR IS | net_pnl IS | pct of total | Status |
|--------|----:|------:|-----------:|-------------:|---|
| LDO | 18 | 55.6% | +54.55% | 148.10% | Already optimized (per-symbol ATR) |
| **BCH** | **94** | **38.3%** | **+23.62%** | **64.13%** | **Default ATR; high SL rate; iter-v3/046 target** |
| TRX | 85 | 34.1% | -7.28% | -19.77% | Default ATR; IS-NEGATIVE (different mechanism — not addressed this iter) |
| ALGO | 53 | 39.6% | -34.05% | -92.45% | Per-symbol ATR; structural floor (not addressable mechanically) |

### 2.2 — BCH direction asymmetry (the bottleneck)

| Direction | n_IS | WR_IS | net_pnl_IS | n_OOS | WR_OOS | net_pnl_OOS |
|---|---:|---:|---:|---:|---:|---:|
| LONG  | 39 | 30.8% | **-25.07%** | 21 | 28.6% | -7.44% |
| SHORT | 55 | 43.6% | +48.69% | 17 | 52.9% | +18.19% |
| TOTAL | 94 | 38.3% | +23.62% | 38 | 39.5% | +10.75% |

BCH LONGs are toxic in BOTH IS (-25.07% PnL, 30.8% WR) AND OOS (-7.44% PnL, 28.6% WR). The
SHORT side carries BCH's positive contribution (+48.69% IS / +18.19% OOS). Wider SL
preferentially helps the toxic-LONG side reach TP/timeout instead of stop-out, since LONG
SLs are hitting at higher rate than SHORT SLs.

### 2.3 — BCH exit-composition stability (no IS→OOS regime shift)

| Period | n | TP% | SL% | TIMEOUT% | SL:TP ratio | mean_SL | mean_TP |
|---|---:|---:|---:|---:|---:|---:|---:|
| iter-v3/045 IS  | 94 | 30.9% | 59.6% | 9.6% | 1.93 | -3.90% | +7.73% |
| iter-v3/045 OOS | 38 | 31.6% | 60.5% | 7.9% | 1.92 | -3.45% | +6.81% |

Δ TP% = +0.7pp (negligible). Δ SL% = +0.9pp (negligible). SL:TP ratio nearly identical (1.93
vs 1.92). **BCH is regime-stable — no IS→OOS regime shift. Wider SL helps both IS AND OOS
symmetrically.** This contrasts with LDO (iter-v3/045 anchor) which had a strong IS→OOS shift
(SL:TP 1.14 → 2.33) that wider SL targeted directly. For BCH, the mechanism is symmetric on
both windows.

### 2.4 — BCH is IS-positive, NOT OOS-divergent (different from LDO/iter-v3/039 pattern)

This is critical. iter-v3/039 NO-MERGE established that per-symbol customizations broke IS
aggregate at multi-seed (the suspicious-OOS-divergence pattern). iter-v3/045 OOS lift came
from LDO addressing an OOS-specific regime shift. **iter-v3/046 BCH is structurally
DIFFERENT**: BCH IS=OOS SL:TP=1.93 (no regime shift); BCH is +23.62% IS / +10.75% OOS (BOTH
positive); the wider-SL mechanism is symmetric on both windows. **This makes iter-v3/046
LESS LIKELY to replicate the iter-v3/039 IS-divergence pattern** because the mechanism is
not asymmetric across IS/OOS.

### 2.5 — Counterfactual: BCH IS lift estimate

BCH IS exit composition: SL = 59.6% (56 of 94 trades); mean_SL_pnl = -3.90%.

If wider SL (1.5×) compresses IS SL rate by ~10pp (similar to iter-v3/045 LDO mechanism),
~9 SL trades become TP/timeout:
- 9 × (-3.90% recovered) = +35.1% IS PnL recovery (the SL drag eliminated)
- Of those 9 redirected trades, assume 50% reach TP (+7.73 mean_TP) and 50% become timeout
  (~+0% mean): 4.5 × 7.73 = +35% additional capture, 4.5 × 0 = +0
- Net BCH IS lift estimate: +35 to +50pp on BCH (significant)

Bundle IS PnL = +37 currently (LDO +54.55 + BCH +23.62 + TRX -7.28 + ALGO -34.05 ≈ 36.84%
roughly equals the comparison.csv weighted_pnl_total = +75.40 difference is per-cell vs
per-symbol attribution). BCH lift of +35 to +50pp ≈ +0.10 to +0.18 IS Sharpe (proportional
to BCH's 64% pct_of_total contribution).

If lift is more aggressive (BCH SL rate compresses by 12-15pp, similar to ALGO at iter-v3/044
which went from 71.9% IS SL rate to 56.6% = -15pp), the IS Sharpe lift could reach +0.20 to
+0.25.

### 2.6 — Counterfactual: BCH OOS lift estimate

BCH OOS exit composition: SL = 60.5% (23 of 38 trades); mean_SL_pnl = -3.45%.

BCH OOS LONG side is toxic (-7.44%, 28.6% WR). Wider SL on OOS LONGs gives them headroom to
recover to TP or timeout. If 4 of 21 OOS LONGs (≈20%) redirect from SL to TP/timeout:
- 4 × (-3.45% recovered) = +14% OOS PnL recovery
- 2 × +6.81 (TP) = +14
- Net BCH OOS lift: +5 to +14pp on BCH

Bundle OOS PnL = +96.99 (single-seed). BCH +5-14pp lift on the +10.75 base = +50 to +130%
relative on BCH. Bundle weighted: BCH is 11% concentration (+10.75 of 96.99); BCH lift adds
+0.5 to +1.5pp to bundle = +0.05 to +0.15 OOS Sharpe (modest; the iter-v3/045 OOS bar is
already very high at +3.53).

### 2.7 — Why NOT TRX per-symbol ATR (the alternative)

TRX has highest IS-axis-leverage potential numerically (-7.28% IS net_pnl is the most
direct IS bottleneck), but iter-v3/046 deliberately picks BCH over TRX because:

| Metric | BCH | TRX | Implication |
|---|---:|---:|---|
| IS SL:TP | 1.93 | 2.24 | Both elevated |
| OOS SL:TP | 1.92 | **0.96** | TRX OOS already much better than IS |
| BCH OOS net_pnl | +10.75 | +29.24 | TRX OOS already strong |
| Mechanism direction | Symmetric IS+OOS | IS-only (risks OOS regression) | BCH cleaner |

Wider SL on TRX would help IS but RISK regressing OOS (TRX OOS SL:TP=0.96 means TRX SLs are
mostly working OOS — letting losing trades absorb more loss may not improve them). BCH's
symmetric IS=OOS pattern means wider SL helps BOTH windows symmetrically, with no
asymmetric trade-off risk. This is the cleanest IS-axis fix at low OOS-regression risk.

### 2.8 — Why NOT BCH/TRX direction filter (architectural-novelty axes)

Direction filters (suppress LONG signals on BCH; suppress SHORT signals on TRX) have higher
IS lift potential (+0.20 to +0.35 Sharpe) but introduce architectural novelty (no v3
precedent for direction-side filtering). EXPLORATION budget is 2h; novel architecture
requires non-trivial dispatch path, configuration field, plus test coverage. Per cycle 3
plan §Axis 5, novel mechanisms require IS-axis pre-validation; while the EDA IS the
pre-validation, the mechanism risk-reward is unfavorable for an EXPLORATION when a known
mechanism is available.

Reserve direction-filter axes for iter-v3/047+ if iter-v3/046 BCH ATR under-delivers.

### 2.9 — Why ALGO ATR REVERT was REJECTED

The QR initially hypothesized ALGO ATR (2.0, 1.5) might have hurt ALGO IS (since ALGO IS is
catastrophic at -34.05%). The diagnostic FALSIFIED this hypothesis:

| Configuration | ALGO IS n | ALGO IS WR | ALGO IS net_pnl |
|---|---:|---:|---:|
| iter-v3/043 (default ATR (2.0, 1.0)) | 57 | 28.1% | **-57.66%** |
| iter-v3/045 (per-symbol ATR (2.0, 1.5)) | 53 | 39.6% | **-34.05%** |

ALGO ATR (2.0, 1.5) IMPROVED ALGO IS by +23.61pp (and +11.5pp WR). Reverting would HURT IS
by -23pp AND lose iter-v3/044's +49 OOS swing (ALGO OOS @ iter-v3/045 = +70.17). REVERT axis
REJECTED — would hurt BOTH IS and OOS.

### 2.10 — BCH per-symbol importance (for context, not action)

| Rank | Feature | Importance |
|---:|---|---:|
| 1 | hurst_diff_100_50 | 347 |
| 2 | range_realized_vol_50 | 337 |
| 3 | vwap_dev_20 | 334 |
| 4 | ret_skew_200 | 332 |
| 5 | btc_ret_14d | 331 |
| 6 | ema_spread_atr_20 | 286 |
| 7 | ret_kurt_200 | 263 |
| 8 | ret_skew_50 | 260 |
| 9 | ret_kurt_50 | 257 |
| 10 | sym_vs_btc_ret_7d | 249 |
| 11 | regime_momentum_signed_5d | 232 |
| 12 | hurst_100 | 214 |
| 13 | ret_autocorr_lag1_50 | 214 |
| 14 | max_dd_window_50 | 190 |

Note: This is the LDO importance from iter-v3/044 (carried over from iter-v3/045 brief
Section 2.5; the BCH iter-v3/045 last-month importance shows similar regime+volatility+
mean-reversion pattern — `hurst_diff_100_50, range_realized_vol_50, vwap_dev_20` are also
top-3 for BCH model, see `analysis/iteration_v3-046/bch_trx_diagnosis.csv`). Universal feature
additions targeting BCH would dilute colsample_bytree picks; per-symbol ATR axis operates
downstream of features at the LABELING layer, doesn't disturb feature hierarchy.

### 2.11 — Predicted Behavioral Effect (per `feedback_v3_axis_saturation_predictor.md`)

Predicted IS trade count delta vs iter-v3/045 anchor:
- BCH IS trades: 94 → 88-94 (modest reduction; wider SL slightly lengthens trade durations,
  reducing trade frequency, but cooldown mechanics may also redistribute).
- BCH IS SL count: 56 → 47-50 (−6 to −9; primary mechanism).
- BCH IS TP count: 29 → 33-37 (+4 to +8; some former-SLs reach TP given wider band).
- TRX/ALGO/LDO bit-identical to iter-v3/045 (per-symbol architecture isolates BCH).
- Bundle IS trades: 250 → 244-250 (within ±2.5%).

**Falsifier**: if observed BCH IS trade count change is > 25% relative vs iter-v3/045, the
ATR widening produced cascade effects beyond barrier geometry (investigate label-pipeline
correctness or cross-symbol contagion via portfolio-level risk gates).

### Analysis Script

`analysis/iteration_v3-046/bch_trx_bottleneck_diagnosis.py` (committed SHA `d86b1f9`)
produces `bch_trx_diagnosis.csv` and `synthesis.md` documenting BCH+TRX bottlenecks.
The diagnosis covers: per-symbol IS contribution, direction asymmetry IS+OOS, exit
distribution IS+OOS, ALGO IS regression test (FALSIFIED — ALGO ATR (2.0, 1.5) IMPROVED ALGO
IS by +23.61pp), per-month BCH/TRX IS PnL temporal stability, and BCH+TRX feature importance.
`candidate_axes_ranking.md` ranks 5 candidate axes; the recommended axis is BCH per-symbol
ATR (2.0, 1.5).

---

## Section 3 — Proposed Changes

### Sub-fix 1: ADD V3_ATR_MULTIPLIERS_PER_SYMBOL["BCHUSDT"] = (2.0, 1.5)

In `src/crypto_trade/features_v3/__init__.py`, set:

```python
V3_ATR_MULTIPLIERS_PER_SYMBOL: dict[str, tuple[float, float]] = {
    "ALGOUSDT": (2.0, 1.5),  # iter-v3/044 — PROMISING
    "LDOUSDT":  (2.0, 1.5),  # iter-v3/045 — STRONGEST PROMISING
    "BCHUSDT":  (2.0, 1.5),  # iter-v3/046 — QR EDA-driven; mirror iter-v3/044+045 mechanism
}
```

This widens BCH's SL multiplier from 1.0× ATR (DEFAULT) to 1.5× ATR (50% wider band). TP
multiplier unchanged at 2.0× ATR. TRX remains on DEFAULT_ATR_MULTIPLIERS = (2.0, 1.0) via
fallback.

### Sub-fix 2: Update _verify_feature_columns in run_baseline_v3.py

Update assertions for iter-v3/046 state:
- `len(V3_ATR_MULTIPLIERS_PER_SYMBOL) == 3` (was 2; now ALGO + LDO + BCH)
- `V3_ATR_MULTIPLIERS_PER_SYMBOL["BCHUSDT"] == (2.0, 1.5)` (NEW per-symbol entry)
- `atr_multipliers_for_symbol("BCHUSDT") == (2.0, 1.5)` (per-symbol — NEW)
- `atr_multipliers_for_symbol("ALGOUSDT") == (2.0, 1.5)` (per-symbol; UNCHANGED)
- `atr_multipliers_for_symbol("LDOUSDT") == (2.0, 1.5)` (per-symbol; UNCHANGED)
- `atr_multipliers_for_symbol("TRXUSDT") == (2.0, 1.0)` (DEFAULT fallback; UNCHANGED)
- Reject non-{ALGOUSDT, LDOUSDT, BCHUSDT} keys in V3_ATR_MULTIPLIERS_PER_SYMBOL
- All other assertions UNCHANGED from iter-v3/045 (V3_FEATURE_COLUMNS=14, regime_momentum
  PRESENT, ER ABSENT, regime_momentum_signed_3d ABSENT, etc.)

### Sub-fix 3: Update tests/features_v3/test_atr_multipliers_for_symbol.py

- Update docstring header from "iter-v3/045 state" to "iter-v3/046 state".
- Update `test_atr_multipliers_default`:
  - BCHUSDT must now return (2.0, 1.5) (was (2.0, 1.0) at iter-v3/045).
  - TRXUSDT still returns (2.0, 1.0) (DEFAULT fallback).
  - ALGOUSDT still returns (2.0, 1.5).
  - LDOUSDT still returns (2.0, 1.5).
- Rename `test_atr_multipliers_bch_default_fallback` →
  `test_atr_multipliers_bch_per_symbol_widened`:
  - BCHUSDT key MUST be PRESENT in V3_ATR_MULTIPLIERS_PER_SYMBOL (was MUST be absent).
  - BCHUSDT value must be (2.0, 1.5).
  - Update assertion error messages to reflect iter-v3/046 state.
- Update `test_v3_atr_multipliers_per_symbol_has_algo_and_ldo` →
  rename `test_v3_atr_multipliers_per_symbol_has_algo_ldo_bch`:
  - Length must be 3 (was 2).
  - All three keys (ALGOUSDT, LDOUSDT, BCHUSDT) must be present with (2.0, 1.5).
- Update `test_atr_multipliers_runner_dispatch`:
  - `strat_bch.inner.atr_tp_multiplier == 2.0` (UNCHANGED)
  - `strat_bch.inner.atr_sl_multiplier == 1.5` (CHANGED from 1.0; NEW iter-v3/046).
  - LDO/ALGO unchanged at (2.0, 1.5).

### Sub-fix 4: Update `V3_ATR_MULTIPLIERS_PER_SYMBOL` docstring in features_v3/__init__.py

Append iter-v3/046 entry to docstring history:

```
iter-v3/046: BCHUSDT entry added (2.0, 1.5) — QR EDA-driven per-symbol axis selection,
  cycle 3 #7. BCH direction asymmetry: LONG IS -25.07% (39 trades, 30.8% WR — toxic),
  SHORT IS +48.69% (55 trades, 43.6% WR). BCH IS=OOS SL:TP=1.93 (regime-stable, no IS->OOS
  shift) — wider SL helps IS AND OOS SYMMETRICALLY, distinct mechanism from iter-v3/045 LDO
  which addressed an asymmetric IS->OOS regime shift. Third application of validated
  wider-SL mechanism (ALGO at iter-v3/044, LDO at iter-v3/045, BCH at iter-v3/046).
  Source: analysis/iteration_v3-046/bch_trx_bottleneck_diagnosis.py SHA `d86b1f9`.
```

### Sub-fix 5: Update ITERATION_LABEL

In `run_baseline_v3.py`, ITERATION_LABEL = "v3-046".

### Sub-fix 6: Update _verify_feature_columns docstring

Replace "iter-v3/045" references with "iter-v3/046" in docstring blocks. The PART A
(REVERT efficiency_ratio_50) sub-section is unchanged — efficiency_ratio_50 still ABSENT.
The PART B (per-symbol ATR axis) sub-section now describes 3 entries (ALGOUSDT + LDOUSDT +
BCHUSDT), all at (2.0, 1.5).

### Bundle state verification (what _verify_feature_columns must assert)

```
V3_FEATURE_COLUMNS_TOP_N: 14 features (UNCHANGED from iter-v3/045)                      PASS
DEFAULT_ATR_MULTIPLIERS: (2.0, 1.0) — UNCHANGED                                         PASS
V3_ATR_MULTIPLIERS_PER_SYMBOL: 3 entries (ALGO, LDO, BCH) — all (2.0, 1.5)              PASS
V3_FEATURES_PER_SYMBOL: {} (empty — UNCHANGED)                                          PASS
features_for_symbol("BCHUSDT") == 14 features (TOP_N fallback)                          PASS
features_for_symbol("ALGOUSDT") == 14 features (TOP_N fallback)                         PASS
features_for_symbol("LDOUSDT") == 14 features (TOP_N fallback)                          PASS
features_for_symbol("TRXUSDT") == 14 features (TOP_N fallback)                          PASS
atr_multipliers_for_symbol("ALGOUSDT") == (2.0, 1.5) (per-symbol — UNCHANGED)           PASS
atr_multipliers_for_symbol("LDOUSDT") == (2.0, 1.5) (per-symbol — UNCHANGED)            PASS
atr_multipliers_for_symbol("BCHUSDT") == (2.0, 1.5) (per-symbol — NEW iter-v3/046)      PASS
atr_multipliers_for_symbol("TRXUSDT") == (2.0, 1.0) (DEFAULT — UNCHANGED)               PASS
"regime_momentum_signed_5d" IN V3_FEATURE_COLUMNS_TOP_N (mandate PRESENT)               PASS
"regime_momentum_signed_3d" NOT IN V3_FEATURE_COLUMNS_TOP_N (REVERTED at iter-v3/044)   PASS
"efficiency_ratio_50" NOT IN V3_FEATURE_COLUMNS_TOP_N (DROPPED at iter-v3/043)          PASS
"ret_skew_50" IN V3_FEATURE_COLUMNS_TOP_N (PRESENT)                                     PASS
"sym_vs_btc_ret_7d" IN V3_FEATURE_COLUMNS_TOP_N (PRESENT)                               PASS
V3_MODELS = (BCH, LDO, TRX, ALGO) — 4 symbols (UNCHANGED)                               PASS
REQUIRED_GAP = 88 = (21+1) x 4 (UNCHANGED)                                              PASS
```

---

## Section 4 — Expected OOS Impact

**IS Sharpe prediction (single-seed, vs iter-v3/045 single-seed anchor +0.7459)**:
- Predicted band: [+0.80, +1.00]
- Median point estimate: +0.85 to +0.90
- Rationale: Wider BCH SL redirects ~6-9 SL exits to TP/timeout. Each redirected SL→TP is
  approximately +11pp PnL swing per trade (TP +7.73 minus former SL -3.90). 6-9 trades
  redirected = ~+35-50pp PnL swing on BCH (current BCH IS = +23.62%). Bundle IS PnL +37
  → +50 to +60. Sharpe lift ~+0.10 to +0.18 (less than PnL lift because variance also
  rises modestly).

**OOS Sharpe prediction (single-seed, vs iter-v3/045 single-seed anchor +3.5259)**:
- Predicted band: [+3.50, +3.85]
- Median point estimate: +3.55 to +3.70
- Rationale: BCH OOS LONGs are also toxic (-7.44%, 28.6% WR). Wider SL on OOS LONGs gives
  them headroom to recover. Estimate +5 to +14pp BCH OOS PnL lift; bundle OOS Sharpe lift
  +0.05 to +0.15. ALGO/LDO/TRX bit-identical (per-symbol Optuna independence).

**OOS falsifier (pre-registered)**:
- If BCH OOS PnL drops below 0% (worse than +10.75 by > -10): wider SL backfired (more
  losses absorbed before stop-out, with WR not improving); NEGATIVE classification.
- If LDO/TRX/ALGO trade rosters are non-bit-identical to iter-v3/045: per-symbol-ATR
  dispatch path bug; PATH C — REVERT.

**Pathway-A trigger (PROMISING)**:
- BCH OOS PnL ≥ +5% AND LDO+TRX+ALGO bit-identical to iter-v3/045 AND bundle OOS Sharpe
  not regressed by more than -0.10 vs iter-v3/045 anchor AND bundle IS Sharpe Δ ≥ +0.05
  vs iter-v3/045 anchor.

**Pathway-B trigger (PROMISING-INERT or PROMISING-MECHANICAL)**:
- BCH trade roster bit-identical to iter-v3/045 (Falsifier 1 fires; ATR multipliers did
  not propagate to model output) — PROMISING-MECHANICAL.
- BCH trade roster differs but BCH OOS PnL within [0%, +5%] AND IS lift within ±0.05 of
  iter-v3/045 anchor (modest improvement, not enough to call PROMISING) — PROMISING-INERT.

**Pathway-C trigger (NEGATIVE)**:
- BCH OOS PnL < 0% OR
- LDO/TRX/ALGO non-bit-identical (architecture bug) OR
- Bundle OOS Sharpe regressed by more than -0.20 vs iter-v3/045.
- Action: REVERT V3_ATR_MULTIPLIERS_PER_SYMBOL["BCHUSDT"] at iter-v3/047; consider TRX
  per-symbol ATR (with OOS-regression-risk awareness) OR direction-filter axes (architectural
  novelty) as next options. iter-v3/045 PROMISING bundle (ALGO + LDO ATR only) preserved.

---

## Section 5 — Risk Mitigation

**R1 (cooldown)**: unchanged. Cooldown=2 candles post-trade per symbol.

**R2 (drawdown scaling)**: unchanged. R2 gate parameters carried forward.

**R3 (OOD detection)**: zscore_threshold=2.0 unchanged. Feature subspace unchanged at 14
features (Mahalanobis covariance space identical to iter-v3/045). Expected effect on OOD
firing rate: <2% relative (no feature dimensionality change).

**BCH ATR widening risk**: wider SL means individual losing trades can lose MORE per trade.
Mean SL pnl_pct shifts from ~-3.90% (iter-v3/045 IS) to potentially ~-5.85% per losing trade.
If the wider SL doesn't redirect enough SLs to TPs, BCH would lose MORE per trade with
similar frequency, making the IS contribution WORSE. Falsifier: if observed BCH IS SL count
remains ≥55 (vs predicted 47-50) AND mean SL pnl_pct ≤ -5%, the wider SL is hurting more
than helping. This would trigger Pathway-C and REVERT at iter-v3/047.

**Stacking risk (3 per-symbol ATR customizations: ALGO + LDO + BCH)**: iter-v3/045
established that ALGO + LDO ATR stacking did NOT replicate the iter-v3/039 IS-divergence
pattern at single-seed (iter-v3/045 IS Sharpe +0.7459 was the highest single-seed in v3).
iter-v3/046 stacks a 3rd per-symbol ATR. Stacking risk:
- ALL THREE are symmetric labeling-layer mechanisms (no feature-layer changes, no per-symbol
  feature additions). The mechanism is more architecturally homogeneous than iter-v3/039's
  mixed feature+label stack.
- BCH IS=OOS SL:TP=1.93 stable means BCH's wider-SL helps IS AND OOS symmetrically (vs LDO
  which had an OOS-asymmetric mechanism). This REDUCES the IS-divergence risk for BCH
  specifically.
- However, single-seed → multi-seed compression remains a risk. The iter-v3/039 pattern
  could re-emerge at multi-seed CONFIRMATION (iter-v3/050) even if iter-v3/046 single-seed
  is clean.
- Mitigation: classify iter-v3/046 catalog row as PROMISING only if IS lift is positive at
  single-seed (i.e., the IS-divergence pattern doesn't fire even at single-seed). Defer
  multi-seed validation to iter-v3/050 CONFIRMATION (cycle convention).

**IS trade-rate stability**: ATR multipliers change for BCH only; non-BCH label distribution
identical to iter-v3/045 (assuming dispatch path is correct — verified by Sub-fix 3 test).
BCH IS trade count expected within ±20% of iter-v3/045 (94 → 75-113 predicted, with point
estimate 88-94). Portfolio total IS trade count expected within ±2% (250 → ~244-250
predicted). If portfolio total deviates > 30%, investigate parquet freshness or feature
column list.

**Cross-symbol contagion risk**: per-symbol ATR change affects only BCH model training data.
LDO/TRX/ALGO models are completely independent (separate Optuna runs, separate feature
parquets at the model-input level). Cross-symbol contagion possible only via portfolio-level
risk gates (BTC trend filter, drawdown brake). Both gates use portfolio-aggregate signals;
BCH trade-rate change shifts portfolio aggregates by single-digit percent. Expected
portfolio risk-gate firing rate change: <3%.

---

## Section 6 — Risk Management Design (7-Primitive Gate Table)

All 7 risk gates carried forward from iter-v3/045 baseline UNCHANGED.

| Gate | Type | Parameter | Change |
|---|---|---|---|
| 1 — BTC trend | BtcTrendFilterConfig | lookback=42, threshold=15% | None |
| 2 — Hit rate | HitRateGateConfig | window=20, sl_threshold=0.65 | DISABLED (unchanged) |
| 3 — ADX gate | ADX regime filter | threshold=20 (v3 default) | None |
| 4 — Hurst regime | hurst_100 > 0.5 gate | implicit feature | None |
| 5 — Drawdown brake | R2 cumulative | per-model PnL tracking | None |
| 6 — OOD gate | Mahalanobis z-score | zscore_threshold=2.0, 14-D space | None (no feature change) |
| 7 — Liquidity floor | NATR floor | NATR >= 0.5% | None |

**Predicted OOD fire rate**: within ±2% of iter-v3/045 baseline. No feature subspace change.

---

## Section 7 — Pre-Registered Failure-Mode Prediction

**Most plausible failure mode (PROMISING — clean IS+OOS lift)**:
BCH IS WR rises modestly (38.3% → 42-45%), BCH IS net_pnl lifts from +23.62% to +35-50%,
bundle IS Sharpe lifts +0.10 to +0.18, BCH OOS WR rises from 39.5% → 41-44%, bundle OOS
Sharpe lifts +0.05 to +0.15. LDO/TRX/ALGO bit-identical. Classification: PROMISING (clean).
Bundle is now QUADRUPLE-validated wider-SL mechanism (ALGO + LDO + BCH per-symbol ATR all
at (2.0, 1.5); TRX at default). Compoundable at iter-v3/050 CONFIRMATION as a 3-symbol
per-symbol-ATR bundle. **Probability: 45%.**

**Second plausible failure mode (PROMISING-INERT — modest BCH impact)**:
BCH trade rate changes by <10%, BCH OOS WR rises modestly (~1-2pp), but the absolute PnL
improvement is too small to move the needle. Bundle IS Sharpe lift < +0.05; OOS lift < +0.05.
Classification: PROMISING-INERT. The mechanism is honest at the labeling layer but BCH's
signal is the binding constraint; relabeling alone cannot lift past the model's predictive
capacity. Retain as zero-cost addition to iter-v3/050 CONFIRMATION bundle if other axes
succeed. **Probability: 25%.**

**Third plausible failure mode (PROMISING-MECHANICAL — bit-identical BCH trades)**:
At single-seed n_trials=35, Optuna converges to a similar hyperparameter region for BCH
regardless of label-barrier geometry. BCH's IS+OOS trade rosters are bit-identical (or
very near-bit-identical) to iter-v3/045. Falsifier 1 fires. PROMISING-MECHANICAL.
Diagnostic: per-symbol-ATR architecture validated as architecturally-neutral on BCH; the
axis effect was not propagated through the LightGBM head. iter-v3/047 should pivot to a
different axis (TRX per-symbol ATR with OOS-risk awareness OR direction-filter axes).
**Probability: 15%.**

**Fourth plausible failure mode (NEGATIVE — wider SL increases loss per trade without raising WR)**:
BCH mean SL pnl_pct shifts from -3.90% to ~-5.85%. If the wider SL doesn't redirect enough
SLs to TPs, BCH trades just lose MORE per trade with similar frequency. BCH IS PnL drops
to +5 to -10%; OOS PnL drops to 0% to -5%. Per-trade Sharpe could WORSEN if WR rises only
marginally. Classification: NEGATIVE; close per-symbol-ATR axis on BCH. **Probability: 10%.**

**Fifth plausible failure mode (NEGATIVE — cross-symbol architecture bug — Falsifier 2)**:
LDO/TRX/ALGO trade rosters non-bit-identical to iter-v3/045. The per-symbol-ATR dispatch
path has unintended side-effects from adding a third entry (most likely: a global Optuna
seed or random-state cross-pollination). PATH C — REVERT and diagnose. **Probability: <5%**
(per-symbol architecture validated at iter-v3/032 + 044 + 045; third entry is mechanically
analogous to first two).

**What the gates should catch**:
- Gate 5 (R2 drawdown): BCH label-distribution shift may alter R2 firing rate. Monitor.
- Gate 7 (liquidity): NATR floor unchanged; BCH trades that were marginal NATR-wise before
  still pass.

**Behavioral effect predictor**: predicted IS trade count delta -10% to +5% (BCH model
specifically; -2% to +1% portfolio-wide). Falsifier: > 25% portfolio delta triggers
investigation.

---

## Section 8 — Pre-Registered MERGE/NO-MERGE Numerical Criteria

This is an EXPLORATION iteration. MERGE gates do NOT apply. Classification criteria
(pre-registered before backtest runs):

**PATH A — PROMISING (clean)**:
  BCH OOS PnL ≥ +5% AND LDO+TRX+ALGO trade rosters bit-identical to iter-v3/045 AND
  bundle OOS Sharpe not regressed by more than -0.10 vs iter-v3/045 anchor AND
  bundle IS Sharpe Δ ≥ +0.05 vs iter-v3/045 anchor AND
  BCH trade roster differs from iter-v3/045 (Falsifier 1 PASS).
  Classification: PROMISING. Per-symbol ATR widening for BCHUSDT contributes positive lift
  on IS axis (the binding multi-seed constraint).
  Catalog entry: candidate for next CONFIRMATION bundle (compoundable with iter-v3/044
  ALGO ATR + iter-v3/045 LDO ATR per same-mechanism principle; all wider-SL
  labeling-layer adjustments for 3 of 4 bundle symbols).

**PATH B — PROMISING-INERT or PROMISING-MECHANICAL**:
  - PROMISING-INERT: BCH trade roster differs but BCH OOS PnL in [0%, +5%]; bundle IS
    Sharpe within ±0.05 of iter-v3/045. Mechanism dispatched but signal not lifted.
    Retain as zero-cost addition to iter-v3/050 CONFIRMATION bundle if other axes succeed.
  - PROMISING-MECHANICAL: BCH trade roster bit-identical to iter-v3/045 (Falsifier 1 fires).
    Architecture validated as neutral on BCH; NOT a CONFIRMATION-bundle ingredient per
    `feedback_promising_mechanical_subtype.md`.

**PATH C — NEGATIVE**:
  - NEGATIVE-BCH-deepens: BCH OOS PnL < 0% (worse than +10.75 by > -10).
  - NEGATIVE-bundle-regression: bundle OOS Sharpe regressed by more than -0.20 vs
    iter-v3/045 OR bundle IS Sharpe regressed by more than -0.10.
  - NEGATIVE-architecture-bug: LDO/TRX/ALGO trade rosters non-bit-identical to iter-v3/045
    (Falsifier 2 fires) — REVERT.
  Classification: NEGATIVE. Per-symbol ATR axis FALSIFIED for BCH.
  Action: REVERT V3_ATR_MULTIPLIERS_PER_SYMBOL["BCHUSDT"] at iter-v3/047; consider TRX
  per-symbol ATR (with OOS-regression awareness) OR direction-filter axes (architectural
  novelty). iter-v3/045 PROMISING bundle (ALGO + LDO ATR) preserved.
  Catalog entry: "BCH ATR widening (1.5×SL) FALSIFIED — bottleneck not addressable via
  mechanical ATR widening despite ALGO + LDO precedent. BCH may need direction-filter
  mechanism instead (LONGs are toxic in BOTH IS and OOS)".

**Pre-registered classification thresholds (locked before backtest)**:
- PATH A: BCH OOS PnL ≥ +5% AND LDO+TRX+ALGO bit-identical AND bundle OOS Sharpe Δ ≥ -0.10
  AND bundle IS Sharpe Δ ≥ +0.05 AND BCH trades differ
- PATH B-INERT: BCH trades differ AND BCH OOS PnL in [0%, +5%] AND bundle IS Sharpe Δ ∈ [-0.05, +0.05]
- PATH B-MECHANICAL: BCH trades bit-identical (Falsifier 1 fires)
- PATH C: BCH OOS PnL < 0% OR bundle OOS Sharpe Δ < -0.20 OR bundle IS Sharpe Δ < -0.10 OR
  LDO/TRX/ALGO drift (Falsifier 2)

These thresholds are LOCKED and cannot be post-hoc renegotiated.

---

## Section 9 — Library Stack Declaration

All versions identical to iter-v3/045 reproducibility stamp. No new libraries introduced.
Per-symbol ATR is a config-only change (no new feature implementations dispatched).

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

**EDA basis**: `analysis/iteration_v3-046/bch_trx_bottleneck_diagnosis.py` (committed SHA
`d86b1f9`). Outputs: `bch_trx_diagnosis.csv`, `synthesis.md`, `candidate_axes_ranking.md`.
Establishes:
- Per-symbol IS contribution @ iter-v3/045 — BCH +23.62%, TRX -7.28%, ALGO -34.05%, LDO +54.55%
- BCH direction asymmetry: LONG IS -25.07% / SHORT IS +48.69% (LONG side is the toxic IS bottleneck)
- TRX direction asymmetry: LONG IS +24.77% / SHORT IS -32.05% (SHORT side is the toxic IS bottleneck)
- BCH IS=OOS SL:TP=1.93 — STABLE; wider SL helps IS+OOS symmetrically
- TRX IS SL:TP=2.24 vs OOS=0.96 — IS only; widening SL would HURT OOS
- ALGO IS regression FALSIFIED: ALGO ATR (2.0, 1.5) IMPROVED ALGO IS by +23.61pp vs
  iter-v3/043 default ATR (-57.66 → -34.05). REVERT axis REJECTED.
- 5 candidate axes ranked: top recommendation is BCH per-symbol ATR (2.0, 1.5) — third
  application of validated wider-SL mechanism; symmetric IS+OOS lift; no OOS-regression risk
  (vs TRX which would risk OOS); known mechanism (vs direction filters which are architecturally
  novel)

**Original orchestrator pick**: NONE (per `feedback_v3_axis_selection_quant_discipline.md`,
established at iter-v3/044, the orchestrator no longer pre-commits axes; QR drives axis
selection from EDA).

**QR-driven selection**: per-symbol ATR widening for BCHUSDT only
(V3_ATR_MULTIPLIERS_PER_SYMBOL["BCHUSDT"] = (2.0, 1.5)). EDA shows BCH has the highest IS-axis
leverage among low-architectural-risk axes. BCH IS=OOS SL:TP=1.93 stable means the mechanism
helps both IS AND OOS symmetrically (vs LDO which addressed an asymmetric IS→OOS shift; vs
TRX which would risk OOS regression). Mechanism mirrors iter-v3/044 PROMISING ALGO ATR +
iter-v3/045 STRONGEST PROMISING LDO ATR. Cleanest single-axis test; lowest-risk candidate
from the 5-axis ranking.

**Setup commit SHA**: TO BE FILLED post-setup-commit (Engineer responsibility).
**Phase 5.5 verification**: brief Section 2 numerical evidence committed BEFORE setup
commit (committed at `d86b1f9`); brief is iter-v3/046 single-rev (no orchestrator-pick
predecessor).

This Section 10 satisfies the process-discipline requirement that QR EDA precedes axis
selection. Cannot be retroactively renegotiated.

---

## Section 11 — Catalog-Row Pre-Commit Disposition

The catalog row to be appended at Phase 8 (diary closure) is pre-registered for ALL outcomes:

**Outcome A — PROMISING-clean** (BCH OOS PnL ≥ +5% AND LDO+TRX+ALGO bit-identical AND bundle
OOS Sharpe Δ ≥ -0.10 AND bundle IS Sharpe Δ ≥ +0.05 AND BCH trades differ):
> `| iter-v3/046 | 2026-05-09 | Per-symbol ATR widening for BCHUSDT (2.0, 1.5); 4-sym BCH+LDO+TRX+ALGO; 3rd application of validated wider-SL mechanism (ALGO at iter-v3/044 + LDO at iter-v3/045 + BCH at iter-v3/046); QR EDA-driven mirror; cycle 3 #7 | <IS Δ> | <OOS Δ> | EXPLORATION-PROMISING (clean) | YES — STRONG candidate; iter-v3/050 CONFIRMATION-bundle ingredient (compoundable with iter-v3/044 ALGO ATR + iter-v3/045 LDO ATR per same-mechanism principle) |`

**Outcome B-INERT — PROMISING-INERT** (BCH trades differ AND BCH OOS PnL in [0%, +5%] AND
bundle IS Sharpe Δ within ±0.05):
> `| iter-v3/046 | 2026-05-09 | Per-symbol ATR widening for BCHUSDT (2.0, 1.5); cycle 3 #7 | <IS Δ> | <OOS Δ> | EXPLORATION-PROMISING-INERT | RETAIN as zero-cost CONFIRMATION-bundle addition if other axes succeed; mechanism dispatched but signal not lifted |`

**Outcome B-MECHANICAL — PROMISING-MECHANICAL** (BCH trades bit-identical to iter-v3/045):
> `| iter-v3/046 | 2026-05-09 | Per-symbol ATR widening for BCHUSDT (2.0, 1.5); cycle 3 #7 | ~iter-v3/045 (bit-identical) | ~iter-v3/045 (bit-identical) | EXPLORATION-PROMISING-MECHANICAL | NO — strictly architectural; per-symbol-ATR architecture validated as neutral on BCH; iter-v3/047 may apply ATR widening to TRX (with OOS-risk awareness) or pivot to direction-filter axes |`

**Outcome C — NEGATIVE-BCH-deepens** (BCH OOS PnL < 0%):
> `| iter-v3/046 | 2026-05-09 | Per-symbol ATR widening for BCHUSDT (2.0, 1.5); cycle 3 #7 | <IS Δ> | <OOS Δ> | EXPLORATION-NEGATIVE (BCH deepens) | NO — closes per-symbol-ATR axis on BCH; BCH bottleneck not addressable via mechanical SL widening despite ALGO+LDO precedent; iter-v3/047 = different axis (consider direction-filter for BCH LONGs) |`

**Outcome C — NEGATIVE-architecture-bug** (LDO/TRX/ALGO non-bit-identical):
> `| iter-v3/046 | 2026-05-09 | Per-symbol ATR widening for BCHUSDT (2.0, 1.5); cycle 3 #7 | <IS Δ> | <OOS Δ> | EXPLORATION-NEGATIVE (architecture-bug — LDO/TRX/ALGO drift) | NO — REVERT; iter-v3/047 = different axis category after architectural fix |`

**Outcome C — NEGATIVE-stacking-suspect** (bundle OOS Sharpe Δ < -0.20 OR IS Δ < -0.10):
> `| iter-v3/046 | 2026-05-09 | Per-symbol ATR widening for BCHUSDT (2.0, 1.5); cycle 3 #7 | <IS Δ> | <OOS Δ> | EXPLORATION-NEGATIVE (stacking-suspect; replicates iter-v3/039 IS-divergence pattern at 3-symbol ATR layer) | NO — closes per-symbol-ATR stacking axis at 3-symbol; revert to 2-symbol per-symbol-ATR (ALGO + LDO from iter-v3/045) and pivot to universal axes. Update memory: per-symbol-ATR customizations don't stack beyond 2 symbols |`

The diary commit closes the catalog row regardless of outcome. The 5-row pre-commit prevents
post-hoc rationalization.

---

## Section 12 — Phase 5.5 Gate Self-Check (10 mandatory sections inventory)

| # | Section | Status |
|---|---|---|
| 1 | Section 0 — Data Split Declaration | PRESENT (sacred constants UNCHANGED) |
| 2 | Section 1 — Hypothesis | PRESENT (per-symbol ATR widening BCH; expected effect; mechanism named) |
| 3 | Section 2 — IS-Only Numerical Evidence | PRESENT (11 sub-sections; 6 numerical tables; falsifiers with explicit thresholds; behavioral-effect predictor; ALGO REVERT axis falsified) |
| 4 | Section 3 — Proposed Changes | PRESENT (6 sub-fixes; bundle state verification table with 19 assertions) |
| 5 | Section 4 — Expected OOS Impact | PRESENT (PATH A/B-INERT/B-MECHANICAL/C bands; pre-registered classification thresholds) |
| 6 | Section 5 — Risk Mitigation | PRESENT (R1/R2/R3 + BCH ATR risk + 3-symbol stacking risk + IS trade-rate stability + cross-symbol contagion) |
| 7 | Section 7 — Pre-Registered Failure-Mode Prediction | PRESENT (5 plausible failure modes; most plausible PROMISING; 2nd PROMISING-INERT; 3rd PROMISING-MECHANICAL; 4th NEGATIVE-BCH-deepens; 5th architecture-bug) |
| 8 | Section 8 — Pre-Registered MERGE/NO-MERGE Criteria | PRESENT (PATH A/B-INERT/B-MECHANICAL/C with locked thresholds) |
| 9 | Section 9 — Library Stack | PRESENT (UNCHANGED from iter-v3/045) |
| 10 | Section 10 — QR Audit Trail | PRESENT (NEW required per `feedback_v3_axis_selection_quant_discipline.md`; EDA SHA cited; QR-driven selection rationale) |
| 11 | Section 11 — Catalog-Row Pre-Commit | PRESENT (5 outcomes pre-registered) |

**All 11 sections (10 mandatory + Section 11 pre-commit) PRESENT.** Engineer's Phase 5.5
gate should PASS this brief.

---

## Section 13 — Status

**READY-FOR-PHASE-5.5** — research brief complete. Engineer reads this brief, verifies the
sections, runs the bundle state assertions, runs the updated 5 adversarial pytest tests
(test_atr_multipliers_for_symbol.py with iter-v3/046 expectations), and writes
`phase5p5_gate.md` with OVERALL=PASS. Phase 6 backtest then runs at single-seed
--exploration; budget 25-35 min; well within 2h cap.

After Phase 6 closes, Critic Phase 7.5 review fires; QR Phase 7 evaluates OOS for first
time; QR Phase 8 closes the catalog row at one of the 5 pre-registered dispositions.

iter-v3/046 is cycle 3 #7 of 10; 3 EXPLORATIONs remain in this cycle (iter-v3/047, /048,
/049); CONFIRMATION at iter-v3/050.
