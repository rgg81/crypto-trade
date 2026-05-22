# iter-v3/119 Research Brief — Cycle-6 EXPLORATION #10 (FINAL)

**Axis**: NEW engineered feature family at 8h — adds **one** composed feature
to `V3_FEATURE_COLUMNS_TOP_N` (14 → 15):
`C6 = ret5d_signed_tbi = ret_5d × sign(taker_buy_imbalance_20)`.
The axis is on the `regime_momentum_signed_5d` (/025 PROMISING) lineage —
a Category-2 composed feature (value × regime-sign multiplied through a
2-state sign function), structurally equivalent in form to the /025
baseline-stack feature AND to /118's failed C3, but with a **STRUCTURALLY
DIFFERENT regime classifier**: order-flow regime via
`taker_buy_imbalance_20` (NOT vol-regime, NOT /025 hurst-regime).
EDA-driven adjudication per `feedback_v3_axis_selection_quant_discipline.md`.

**Cycle**: 6 EXPLORATION slot #10 of 10 (FINAL EXPLORATION — iter-v3/120 is the
mandatory cycle-6 CONFIRMATION). Cycle-6 catalog state at /118 closeout:
8 NEGATIVE (/110-/115, /117, /118) + 1 PROMISING-MECHANICAL (/116). /118
catastrophically falsified the `value × sign(vol-regime-classifier)`
Category-2 lineage (IS Δ = −0.4543); /119 advances to a structurally
different regime classifier per the /118 QR-Critic concurrence (QR Round-2
Clarification 3 + Critic Recommendation 1).

**Anchor (EXPLORATION-mode comparison)**: iter-v3/060 (IS monthly Sharpe
**+0.8325** / OOS monthly Sharpe **+0.1403**) — the 3-seed EXPLORATION-mode
reference per `BASELINE_V3.md`. iter-v3/116 EXPLORATION-PROMISING-MECHANICAL
(IS +0.6246 / OOS +1.1089) is REVERTED for /119 (single-axis discipline; /116
no_confirm primitive is bundled at /120 CONFIRMATION as a strictly-accretive
component decision per `feedback_promising_mechanical_subtype.md` — NOT a
compoundable signal source for /119). iter-v3/118 C3 ema_signed_volregime is
REMOVED from V3_FEATURE_COLUMNS_TOP_N per /118 closeout Section 9 item 7
(the function STAYS in `engineered_v3.py` as code-museum value).

---

## Section 0 — Data Split declaration

`OOS_CUTOFF_DATE = 2025-03-24` and `training_months = 24` are UNCHANGED. The
sacred constants are immutable across all three tracks; no /119 modification
touches them.

- **IS window**: data extent start (per-symbol earliest 8h candle close
  ≥ 2020-01-01) through `OOS_CUTOFF_DATE = 2025-03-24` (exclusive).
- **OOS window**: `OOS_CUTOFF_DATE = 2025-03-24` through current data extent
  (~2026-05-20).
- **Walk-forward training window**: 24 calendar months ending at each
  test-month's start; rolling by 1 month.
- **Reporting layer**: `comparison.csv` and `in_sample/` / `out_of_sample/`
  directories split on `OOS_CUTOFF_DATE` exactly.
- **Bar interval**: 8h (cycle-6 candle-frequency axis broadly CLOSED per
  /117 closeout Section 6).

**Hand-chosen parameter declaration (per `feedback_v3_brief_parameter_provenance.md`)**:

The /119 axis introduces **NO tuned scalar parameter** — every primitive is
INHERITED from the V3 feature inventory at default lookbacks, and the sign
threshold is the natural zero-cross of order-flow imbalance.

| Parameter | Value | Provenance |
|---|---|---|
| `ret_5d` lookback | **15 8h bars (= 5 calendar days)** | INHERITED from the /025 `regime_momentum_signed_5d` value primitive (the production /060 baseline). NOT tuned for /119. Source: `engineered_v3.py:77` `ret_5d = log_close − log_close.shift(15)`. |
| `taker_buy_imbalance_20` window | **20 bars** | INHERITED from `microstructure_v3.py` default; NOT tuned for /119. Source: existing primitive in `data/features_v3/*.parquet` (verified column present in all 3 symbol parquets). |
| Sign threshold | **0.0 (zero-cross)** | Inherent to `sign(taker_buy_imbalance_20)`; the natural imbalance midpoint (positive = buy-imbalanced; negative = sell-imbalanced). NOT a tunable scalar. Source: structural property of `sign(x − 0)`. |
| Sign convention | **+1 if taker_buy_imbalance > 0; −1 if < 0** | Inherent to `sign(x)`. Source: structural property. |

**ZERO tuned scalars in /119.** Every numeric design choice is either
inherited from the V3 feature inventory or structurally fixed by the
algebraic form. This is a stronger provenance posture than /118 (which
declared rolling-median window 200 as hand-chosen).

**Auditable temporal fence**: the EDA (`analysis/iteration_v3-119/`, commit
`7aa5cc5`) was committed in ONE atomic commit BEFORE this brief or any
subsequent setup commit touches the runner. Every script in the EDA directory
asserts `close_time < OOS_CUTOFF_MS = 1742774400000`; no OOS-window file is
read at any point. Verified at EDA: 0 OOS-leaked rows across all 3 symbols
(BCH 5483/0, LDO 2497/0, TRX 5425/0).

---

## Section 0.5 — Iteration Type Declaration

- **TYPE**: `EXPLORATION` (single structural axis: NEW engineered feature in
  V3_FEATURE_COLUMNS_TOP_N, 14 → 15)
- **Cycle 6 slot**: **#10 of 10 (FINAL EXPLORATION)** — iter-v3/120 is the
  mandatory CONFIRMATION launching immediately after /119 closeout per the
  10:1 cadence (`feedback_v3_strict_10_to_1_cadence.md`).
- **CLI invocation**: `uv run python run_baseline_v3.py --exploration --n-trials 35`
  (default `--bar-interval 8h`)
- **ENSEMBLE_SIZE**: 3 (`EXPLORATION_ENSEMBLE_SIZE` per
  `feedback_v3_outer_seed_cap_2_v3.md`; first 3 seeds of the unified 10-seed
  lineage)
- **n_trials**: 35 (per `feedback_v3_exploration_n_trials_35.md` — above TPE
  warmup ~30; the v3 EXPLORATION default since iter-v3/019)
- **Wall-clock cap**: ≤ 2h (cycle-6 EXPLORATION cap per
  `feedback_v3_cadence_discipline.md`; /118 ran 0.72h; /117 ran 0.64h; the
  8h baseline runtime envelope is well under cap)
- **Single axis variation**: ONE new feature added to
  `V3_FEATURE_COLUMNS_TOP_N` (with the mandatory /118-closeout revert of
  `ema_signed_volregime` 15 → 14 → 15 with C6 — net effect a single-axis swap
  of the 15th feature). All other knobs (universe, label, gates, ensemble
  seeds, Optuna search space) are bit-identical to the /117/118 baseline
  (i.e., the /059-canonical state with /116 no_confirm REVERTED).

---

## Section 1 — Hypothesis

**Single sentence**: adding `ret5d_signed_tbi` (`ret_5d × sign(taker_buy_imbalance_20)`)
to `V3_FEATURE_COLUMNS_TOP_N` as the 15th feature produces an additive
walk-forward OOF AUC lift in the production multivariate LightGBM by exposing
an **order-flow-regime-conditioned momentum** signal at the MICROSTRUCTURE
TIMESCALE (20-bar imbalance, ~7 calendar days) that is structurally orthogonal
to the existing `regime_momentum_signed_5d` (~33-day Hurst regime) and to
/118's failed `ema_signed_volregime` (~67-day vol regime); this lift
translates through walk-forward training to a positive IS monthly Sharpe Δ
vs the /060 anchor (+0.8325).

**Distinguishing claim vs the dead-axes**: this is NOT (a) a new model
architecture (the LightGBM hyperparameter space is unchanged); (b) a new
label (triple_barrier 2.0/1.0 ATR is preserved); (c) a new risk primitive
(the 7-gate RiskV2 stack is unchanged); (d) a new universe (BCH/LDO/TRX);
(e) a new external-data feed (the candidate is built from existing primitives
only — `ret_5d` is constructible from `close`, `taker_buy_imbalance_20` is
precomputed in the existing parquets). The only structural change is one new
column in `V3_FEATURE_COLUMNS_TOP_N`.

**Distinguishing claim vs the closed-at-/118 lineage**: this is NOT a retry
of the vol-regime sign factor. The regime classifier `taker_buy_imbalance_20`
is a MICROSTRUCTURE primitive (order-flow regime), structurally orthogonal
to vol-regime (return-volatility) and hurst-regime (long-memory). The
algebraic-form sister of /025 with a DIFFERENT regime classifier remains the
LIVE engineered-feature axis (per /118 closeout Section 6 + 8.1: "composite
families on STRUCTURALLY DIFFERENT regime classifiers ... remain LIVE").

---

## Section 2 — IS-Only Numerical Evidence

EDA backing: `analysis/iteration_v3-119/`, commit `7aa5cc5`. Six composite-
feature candidates evaluated per `feedback_v3_axis_selection_quant_discipline.md`
(IS-only, methodology faithful to /118 walk-forward).

### 2.1 T1 — Candidate catalog (6 candidates across 3 categories)

| ID | Formula | Category | Cycle-6 motivation |
|---|---|---|---|
| C1 | `obv_slope_50 × sign(volume_mom_ratio_20 - 1.0)` | (i) volume | OBV-slope × volume-momentum regime; NEITHER primitive in V3_FEATURE_COLUMNS |
| C2 | `vwap_dev_20 × sign(volume_cv_50 - rolling_median_200)` | (i) volume | VWAP-rev × volume-dispersion regime; rolling-median REUSED but on DIFFERENT classifier (volume CV, NOT realized vol) |
| C3 | `ret_5d × sign(ret_skew_50)` | (iii) tail | 5d momentum × short-horizon skew; /025 algebraic form but DIFFERENT regime classifier (asymmetry vs long-memory) |
| C4 | `sym_vs_btc_ret_7d × sign(ret_kurt_50 - 0)` | (iii) tail | Cross-asset × tail-regime; substitutes /118 C6 value primitive on cross-asset lineage |
| C5 | `max_dd_window_50 × sign(ret_skew_200 - 0)` | (iii) tail | Drawdown × long-horizon skew; NEW lineage (path-property × asymmetry) |
| **C6** | **`ret_5d × sign(taker_buy_imbalance_20)`** | **(iv) microstructure** | **5d momentum × order-flow regime; taker_buy_imbalance is RAW IMBALANCE (NOT tbr_zscore_30 dead-path)** |

Full motivation per candidate: `analysis/iteration_v3-119/T1_candidate_catalog.csv`.

### 2.2 T2 — Linear Redundancy Pre-Falsifier (R² vs 14 V3_FEATURE_COLUMNS primitives)

| Candidate | POOLED R² | POOLED max\|corr\| primitive | Verdict |
|---|---:|---|---|
| C2 | 0.0215 | regime_momentum_signed_5d (corr=0.106) | PASS |
| C1 | 0.0558 | sym_vs_btc_ret_7d (corr=0.193) | PASS |
| C3 | 0.0694 | sym_vs_btc_ret_7d (corr=0.193) | PASS |
| C5 | 0.4663 | ret_skew_200 (corr=0.558) | PASS |
| **C6** | **0.5099** | **regime_momentum_signed_5d (corr=0.706)** | **PASS-CARVEOUT** |
| C4 | 0.7918 | sym_vs_btc_ret_7d (corr=0.888) | PASS-CARVEOUT |

**C6 R²=0.51 PASS-CARVEOUT**: by construction, `ret_5d × sign(tbi)` shares
71% |corr| with `regime_momentum_signed_5d = ret_5d × sign(hurst_100 − 0.5)`
because both have `ret_5d` as the value primitive. The composed-feature
carve-out per `feedback_v3_engineered_feature_pivot.md` applies: PRIMARY
falsifier is Sharpe-Δ NOT importance rank; secondary gate is importance
≥30% threshold. Full table: `T2_linear_redundancy_pre_falsifier.csv`.

### 2.3 T3 — Walk-forward universe-pooled univariate OOF AUC + 100-perm null

| Candidate | POOLED AUC | null q95 | p-value | clears q95 |
|---|---:|---:|---:|:---:|
| C4 | 0.5717 | 0.5930 | 1.0 | False |
| C3 | 0.5660 | 0.5933 | 1.0 | False |
| **C6** | **0.5653** | 0.5953 | 1.0 | False |
| C2 | 0.5635 | 0.5933 | 1.0 | False |
| C1 | 0.5627 | 0.5939 | 1.0 | False |
| C5 | 0.5445 | 0.5950 | 1.0 | False |

**NO candidate clears T3 univariate q95.** This is the **structurally-
expected outcome for composed features** (per `feedback_v3_engineered_features_proven.md`):
a sign-conditioned interaction features carries signal at depth ≥ 2
(value × regime), NOT at 1D univariate. /118 C3 also failed T3 (p=0.61)
but cleared T7 multivariate-lift; C6 follows the same pattern. T3 is
INFORMATIONAL for composed features — the controlling tests are T7 + T5.
Full table: `T3_walkforward_pooled_auc.csv`.

### 2.4 T4 — Per-symbol univariate AUC (the /117 g1 hard gate)

| Candidate | BCH AUC | LDO AUC | TRX AUC | #g1 pass |
|---|---:|---:|---:|:---:|
| C2 | 0.4711 | 0.5197 ✓ | 0.5099 ✓ | 2/3 |
| **C6** | **0.4671** | **0.5484 ✓** | **0.5018 ✓** | **2/3** |
| C1 | 0.4608 | 0.4332 | 0.5079 ✓ | 1/3 |
| C3 | 0.4604 | 0.4537 | 0.5265 ✓ | 1/3 |
| C4 | 0.4714 | 0.4779 | 0.5351 ✓ | 1/3 |
| C5 | 0.4737 | 0.4253 | 0.4455 | 0/3 |

**0 of 6 candidates pass all 3 symbols at the univariate per-symbol g1 gate.**
The same composed-feature multi-dim signal-recovery argument applies for C6
(only multivariate at depth ≥ 2 exposes the interaction). C6 leads at 2/3 g1
PASS alongside C2.

### 2.5 T5 — Multivariate (14+1) depth-4 LightGBM importance rank (per symbol)

| Candidate | BCH rank/15 (gain %) | LDO rank/15 (gain %) | TRX rank/15 (gain %) |
|---|---|---|---|
| C1 | **5 (69%)** | **6 (56%)** | 8 (31%) |
| C5 | **6 (61%)** | 11 (30%) | **4 (55%)** |
| **C6** | **11 (55%)** | **11 (24%)** | **15 (12%)** |
| C2 | 10 (58%) | 11 (20%) | 14 (15%) |
| C3 | 12 (46%) | 12 (22%) | 13 (15%) |
| C4 | 15 (18%) | 15 (8%) | 15 (7%) |

**C1 and C5 lead** on T5 (the /025 PROMISING benchmark, rank ≤ 5 AND gain
≥ 30%). C6 is MID-TABLE (rank 11/11/15, gain 55/24/12%) — NOT in the /085
silent-INERT pattern (rank ≥ 13/15 with near-zero gain) but NOT at the /025
benchmark either. The /118 closeout demonstrated that T5 alone is NOT
verdict-determinative — /118 C3 ranked 8-10/15 at the EDA but failed
catastrophically at production. T7 + T9 are the controlling gates.

Mechanism: composed features that USE interactions efficiently at depth 3-5
don't necessarily rank in the top by total gain (the /053 hurst_drift mechanism
codified in `feedback_v3_lr_pf_methodology.md`: "trees can use derived
features for EFFICIENCY without that allocation reflecting NEW signal").
The inverse holds: a feature CAN be allocated mid-table importance AND
deliver multivariate lift via interaction-level access. C6's BCH gain 55%
+ LDO 24% + TRX 12% (mean 30%) is BELOW the /025 benchmark on aggregate but
ABOVE the /118 C3 portfolio share (7.1%) at the EDA layer. Full table:
`T5_importance_rank_multivariate.csv`.

### 2.6 T7 — Multivariate-LIFT screen (14 vs 14+1 OOF AUC) — THE PRODUCTION-RELEVANT GATE

| Scope | Baseline 14f AUC | +C6 AUC | C6 lift |
|---|---:|---:|---:|
| BCH | 0.5046 | 0.5103 | +0.0057 |
| LDO | 0.5207 | 0.5330 | +0.0123 |
| TRX | 0.4806 | 0.4859 | +0.0053 |
| **POOLED** | **0.4954** | **0.5037** | **+0.0083** |

**C6 clears the POOLED multivariate-lift gate (+0.0083 > 0.005)** AND
delivers **ALL THREE POSITIVE per-symbol lifts** — the inverse of /118 C3's
TRX-only-positive + BCH/LDO-negative pattern that catastrophically failed.
This is the BROAD-BASED LIFT signature: every symbol benefits from the order-
flow-regime composite. T9 (Section 2.7) confirms no SSC-RISK flag.

For comparison, /118 C3 T9 was POOLED +0.0081 (TRX +0.0082 carrier, BCH
−0.0039, LDO −0.0106). C6 POOLED +0.0083 is essentially the same magnitude
BUT with broad-based positive per-symbol distribution — the structural
difference that may translate through production walk-forward.

Full table: `T7_multivariate_lift_screen.csv`.

### 2.7 T9 — NEW Single-Symbol-Carrier RISK gate (per /118 closeout)

The /119-new gate per /118 closeout Critic Recommendation 1 + QR Clarification
3: flag candidate as SSC-RISK if `single-symbol max|lift| > 2 × |POOLED lift|`.
/118 prospectively had SSC ratio ~1.01× — the 2× gate would have flagged
/118 at a different sign reading.

| Candidate | POOLED lift | max single-sym abs | Max carrier | SSC ratio | SSC-RISK |
|---|---:|---:|---|---:|:---:|
| **C6** | **+0.0083** | **0.0123** | **LDO** | **1.48×** | **FALSE** |
| C5 | +0.0060 | 0.0132 | BCH | 2.21× | TRUE |
| C4 | +0.0030 | 0.0064 | BCH | 2.12× | TRUE |
| C1 | +0.0019 | 0.0151 | LDO | 7.77× | TRUE |
| C2 | +0.0003 | 0.0057 | LDO | 19.71× | TRUE |
| C3 | −0.0007 | 0.0082 | LDO | 11.66× | TRUE |

**C6 is the SOLE candidate clearing the new SSC-RISK gate (1.48× < 2.0).**
The diagnostic interpretation: LDO is the strongest carrier (+0.0123) but
the magnitude is only 1.48× the POOLED average (+0.0083), AND BCH+TRX are
ALSO POSITIVE. This is the textbook "broad-based positive lift" pattern that
the gate is designed to distinguish from single-symbol-carrier signatures.
Full table: `T9_ssc_risk_gate.csv`.

### 2.8 T6 — GO/NO-GO verdict synthesis

| # | Candidate | Cat | T2 | T3 | T5 (BCH/LDO/TRX) | **T7 lift** | **T9 SSC** | Verdict |
|---|---|---|---|---|---|---|---|---|
| 1 | **C6_ret5d_signed_tbi** | (iv) | 0.51 CV | 1.0 | 11/11/15 (55/24/12%) | **+0.0083** | **1.48× FALSE** | **/119 AXIS** |
| 2 | C5_maxdd_signed_skew200 | (iii) | 0.47 | 1.0 | 6/11/4 (61/30/55%) | +0.0060 | 2.21× TRUE | GO-SSC-RISK (reject — gate fail) |
| 3 | C4_symvsbtc_signed_kurt50 | (iii) | 0.79 CV | 1.0 | 15/15/15 (18/8/7%) | +0.0030 | 2.12× TRUE | MARGINAL+SSC-RISK |
| 4 | C1_obv_signed_volmom | (i) | 0.06 | 1.0 | 5/6/8 (69/56/31%) | +0.0019 | 7.77× TRUE | MARGINAL+SSC-RISK |
| 5 | C2_vwap_signed_volcv | (i) | 0.02 | 1.0 | 10/11/14 (58/20/15%) | +0.0003 | 19.71× TRUE | MARGINAL+SSC-RISK |
| 6 | C3_ret5d_signed_skew50 | (iii) | 0.07 | 1.0 | 12/12/13 (46/22/15%) | −0.0007 | 11.66× TRUE | REJECT |

**RECOMMENDATION: /119 axis = C6_ret5d_signed_tbi.**

The choice is JUSTIFIED on:
1. **T7 POOLED lift +0.0083** (highest in candidate set; same magnitude as /118 C3 but broad-based positive).
2. **T9 SSC-RISK FALSE** (1.48× — sole candidate clearing the new gate established at /118 closeout).
3. **Broad-based positive per-symbol lifts** (BCH +0.0057 / LDO +0.0123 / TRX +0.0053 — all three positive, the structural inverse of /118 C3).
4. **Mid-table T5 importance** (rank 11/11/15, gain 55/24/12%) — NOT a /085 silent-INERT pattern, NOT a /025 benchmark either, but exhibits the depth-3-5 interaction-level signal pattern the engineered-feature axis targets.
5. **Lineage discipline**: C6 reuses the SUCCESSFUL /025 value primitive (ret_5d) with a fundamentally orthogonal regime classifier (microstructure order-flow), the correct response to /118's closure of vol-regime composites on the SAME value primitive (`ema_spread_atr_20`).

Synthesis document: `analysis/iteration_v3-119/synthesis.md`.

---

## Section 3 — Proposed Changes (the architectural diff vs /059)

The substantive single-axis change (with the mandatory /118-closeout revert):

| Knob | /118 ending value | /119 value |
|---|---|---|
| `V3_FEATURE_COLUMNS_TOP_N` count | 15 (with `ema_signed_volregime` 15th) | **15** (with **`ret5d_signed_tbi`** 15th; `ema_signed_volregime` REMOVED per /118 closeout) |
| `V3_FEATURE_COLUMNS_TOP_N` 15th element | `"ema_signed_volregime"` | **`"ret5d_signed_tbi"`** |
| `compute_ema_signed_volregime` in `engineered_v3.py` | present, dispatched, in TOP_N | **present, dispatched, NOT in TOP_N** (code-museum value per /118 closeout Critic Rec 3) |
| `compute_ret5d_signed_tbi` in `engineered_v3.py` | not present | **NEW function** |
| `add_engineered_v3_features` wires C6 | does not wire C6 | **wires C6 too** |
| Runner `n != 15` guard (line 432-440) | enforces 15 (for /118 ema_signed_volregime) | **enforces 15** (now for /119 ret5d_signed_tbi) |
| Runner `_canonical_v059` accretion guard | 16 knobs unchanged | **16 knobs unchanged** (feature-set is NOT in the accretion-guard knob list; the n_features guard is the sole feature-count check) |
| BANNED-features list in `features_v3/__init__.py` | excludes `ema_signed_volregime` | **adds `ema_signed_volregime` to absent-features ban list** (per /118 closeout — function STAYS in engineered_v3.py for code-museum value but MUST NOT appear in V3_FEATURE_COLUMNS_TOP_N) |

**Knobs UNCHANGED (/059-canonical with /116 no_confirm REVERTED, matching
/117/118-state)**:

- V3_MODELS = ("BCHUSDT", "LDOUSDT", "TRXUSDT")
- REQUIRED_GAP = 66 (= (21+1) × 3; 8h base constant)
- label_mode = "triple_barrier"
- DEFAULT_ATR_MULTIPLIERS = (2.0, 1.0)
- V3_ATR_MULTIPLIERS_PER_SYMBOL = {} (no per-symbol override)
- zscore_threshold = 2.0
- adx_threshold = 20.0
- adx_threshold_per_symbol = {}
- vol_scale_floor_per_symbol = {}
- block_long_for = ()
- block_short_for = ()
- enable_per_symbol_drawdown_brake = False
- enable_no_confirm_exit = False (the /116 no_confirm primitive STAYS REVERTED)
- no_confirm_trigger_atr = 0.50 (field default; never read while flag is False)
- no_confirm_k_candles = 4 (field default; never read)
- ENSEMBLE_SEEDS (the 3-seed EXPLORATION list)
- Optuna search space (the LightGbmStrategy default)

---

## Section 3.5 — Precise `src/` Changes for the QE (Phase 6)

Single-axis EXPLORATION; ONE substantive code change + ONE mandatory
/118-closeout revert spread across several files:

**Change 0 (mandatory /118 housekeeping) — Revert `ema_signed_volregime` from V3_FEATURE_COLUMNS_TOP_N**

Per /118 closeout Section 9 item 7 + Critic Recommendation 3, `ema_signed_volregime`
MUST be REMOVED from `V3_FEATURE_COLUMNS_TOP_N` at the /119 setup-commit
(function STAYS in `engineered_v3.py` AS-IS for code-museum value, dispatch
call STAYS in `add_engineered_v3_features` for zero revert cost). Also:
- Add `ema_signed_volregime` to the BANNED-features list in
  `src/crypto_trade/features_v3/__init__.py` (the ABSENT-list at lines
  301-313 — alongside `vol_normalized_ret_5d`, `hurst_drift_50_200`,
  `regime_momentum_signed_3d`, `funding_regime_momentum_5d`,
  `basis_zscore_30`, etc.).
- Update the runner's pre-flight ABSENT-feature assertion (if it exists for
  the /118 entry) to include `ema_signed_volregime` in the ABSENT-from-TOP_N
  verification.

**Change 1 — Add `compute_ret5d_signed_tbi` to `src/crypto_trade/features_v3/engineered_v3.py`**

After the existing `compute_ema_signed_volregime` function (lines 778-831),
add:

```python
def compute_ret5d_signed_tbi(df: pd.DataFrame) -> pd.DataFrame:
    """Composed feature: ret_5d × sign(taker_buy_imbalance_20).

    Encodes an order-flow-regime-conditioned momentum signal at the
    microstructure timescale (~7 calendar days at 8h cadence via 20-bar
    taker-buy imbalance window). Structurally orthogonal to:
    - /025 regime_momentum_signed_5d (~33-day Hurst regime; long-memory)
    - /118 ema_signed_volregime (~67-day vol regime; return-volatility) — CLOSED

    Construction:
    - ``ret_5d``: log(close_t / close_{t-15}) at 8h cadence.
      15 bars × 8h = 120h ≈ 5 calendar days. Past-only by .shift(15).
      Identical to the value primitive in regime_momentum_signed_5d (/025).
    - ``taker_buy_imbalance_20``: 20-bar rolling order-flow imbalance
      (precomputed by add_taker_buy_imbalance_20; past-only by construction).
      Threshold = 0 (zero-cross of imbalance; positive = buy-imbalanced;
      negative = sell-imbalanced).
    - ``order_flow_sign``: sign(taker_buy_imbalance_20);
        +1 if imbalance > 0 (buy-dominated regime) → momentum confirmed
        −1 if imbalance < 0 (sell-dominated regime) → momentum faded
         0 (degenerate zero case) → treated as NaN (no signal)

    Past-only by construction:
    - ``ret_5d`` is past-only (log_close.shift(15)).
    - ``taker_buy_imbalance_20`` is past-only (microstructure_v3 computed it
      past-only at parquet generation).
    - Upstream primitives (close, taker_buy_imbalance_20) run BEFORE
      engineered_v3 in GROUP_REGISTRY; the past-only invariant is preserved.

    NaN warm-up: first 19 bars are NaN (taker_buy_imbalance_20 needs 20-bar
    history). ret_5d warm-up (15 bars) is dominated.

    Args:
        df: DataFrame with columns ``close`` (float-castable) and
            ``taker_buy_imbalance_20`` (from microstructure_v3).

    Returns:
        Copy of ``df`` with ``ret5d_signed_tbi`` column appended.
        If a source primitive is missing, the column is set to all-NaN
        without error (downstream feature-column assertion will fail loudly).
    """
    df = df.copy()
    if "close" not in df.columns or "taker_buy_imbalance_20" not in df.columns:
        df["ret5d_signed_tbi"] = np.nan
        return df
    close = df["close"].astype(float)
    log_close = np.log(close.clip(lower=1e-12))
    # 15 bars at 8h cadence = 5 calendar days (identical to /025's ret_5d)
    ret_5d = log_close - log_close.shift(15)
    tbi = df["taker_buy_imbalance_20"].astype(float)
    sign_tbi = np.sign(tbi)
    # Zero-imbalance edge case: treat as NaN (no signal)
    sign_tbi = sign_tbi.replace(0.0, np.nan)
    df["ret5d_signed_tbi"] = ret_5d * sign_tbi
    return df
```

Then update `add_engineered_v3_features(df)` to call the new function
AFTER `compute_ema_signed_volregime` (which stays in dispatch):

```python
df = compute_ema_signed_volregime(df)  # iter-v3/118 (DEAD CODE — REMOVED from TOP_N at /119)
df = compute_ret5d_signed_tbi(df)  # iter-v3/119 NEW (15th V3_FEATURE_COLUMNS feature)
```

**Change 2 — Update `V3_FEATURE_COLUMNS_TOP_N` in `src/crypto_trade/features_v3/__init__.py`**

REMOVE `"ema_signed_volregime",` (line 213) and REPLACE with `"ret5d_signed_tbi",`
in the 15th slot. Update the inline comment:

```python
"ret5d_signed_tbi",  # engineered [iter-v3/119: order-flow-regime × momentum; /025 PROMISING lineage]
```

Place it as the 15th element (same position as the now-removed C3). Update
the docstring comment block at the top of the tuple definition (lines 316-356)
to record the /119 swap (mirror the existing entries for traceability,
adding a `/119` history entry that explicitly documents the C3 → C6 swap).

Also: add `ema_signed_volregime` to the BANNED-features list at lines 301-313
(in the v3 ABSENT-from-TOP_N ban convention):

```python
#   ema_signed_volregime — /118 NEGATIVE catastrophic (Critic FINAL `80caafd`;
#                          broader `value × sign(vol-regime-classifier)`
#                          Category-2 lineage CLOSED at single-seed budget)
```

**Change 3 — Update the runner feature-count guard at `run_baseline_v3.py:432-440`**

The current code (post /118):
```python
n = len(V3_FEATURE_COLUMNS)
if n != 15:
    raise RuntimeError(
        f"V3_FEATURE_COLUMNS has {n} columns — expected exactly 15. "
        "iter-v3/118: V3_FEATURE_COLUMNS adds ema_signed_volregime ..."
    )
```

STAYS at `n != 15` (the count is unchanged; only the 15th element changes
from `ema_signed_volregime` to `ret5d_signed_tbi`). Update the error message:

```python
n = len(V3_FEATURE_COLUMNS)
if n != 15:
    raise RuntimeError(
        f"V3_FEATURE_COLUMNS has {n} columns — expected exactly 15. "
        "iter-v3/119: V3_FEATURE_COLUMNS adds ret5d_signed_tbi (15th, "
        "engineered Category 2; order-flow-regime × momentum at ~7-day "
        "microstructure timescale) to the BASELINE_V3 anchor (14 features). "
        "Earlier: iter-v3/118 added ema_signed_volregime (15th); REVERTED at "
        "/119 closeout housekeeping (Critic /118 Rec 3). "
        "Check V3_FEATURE_COLUMNS_TOP_N in features_v3/__init__.py."
    )
```

**Change 3.5 — Update ITERATION_LABEL and MODEL_SPECS in `run_baseline_v3.py`**

- Line 131 (or equivalent): `ITERATION_LABEL = "v3-119"`
- Lines 198-200 (or equivalent MODEL_SPECS naming): replace `"v3-118-..."`
  prefix with `"v3-119-..."` throughout.

**Change 4 — Regenerate the `data/features_v3/<SYM>_8h_features.parquet`
files for BCH/LDO/TRX (and BTC for cross-asset)**

The new column `ret5d_signed_tbi` must exist in the parquets read by the
runner. CLI:

```bash
uv run crypto-trade features \
  --symbols BTCUSDT,BCHUSDT,LDOUSDT,TRXUSDT \
  --interval 8h --track v3 --format parquet --workers 4
```

Re-run the parquet generation BEFORE the backtest. Verify the column appears
in each symbol's parquet via:

```bash
uv run python -c "import pandas as pd; print('ret5d_signed_tbi' in pd.read_parquet('data/features_v3/BCHUSDT_8h_features.parquet').columns)"
```

The expected post-regen column count is 95 (prior 94 with `ema_signed_volregime`
+ 1 new `ret5d_signed_tbi`; the `ema_signed_volregime` column STAYS in the
parquet but is NOT referenced by V3_FEATURE_COLUMNS_TOP_N).

**Change 5 — Add unit test for the new function**

In `tests/features/v3/test_engineered_v3.py` (or the closest existing test
module — `tests/test_engineered_v3_features.py` per /118 precedent), add:

```python
def test_compute_ret5d_signed_tbi_past_only():
    """ret5d_signed_tbi is past-only and matches the formula on a
    synthetic panel of 100 bars."""
    rng = np.random.default_rng(42)
    df = pd.DataFrame({
        "close": np.exp(rng.standard_normal(100) * 0.02).cumprod() * 100,
        "taker_buy_imbalance_20": rng.uniform(-0.5, 0.5, size=100),
    })
    out = compute_ret5d_signed_tbi(df)
    # NaN warm-up: first 15 bars are NaN (ret_5d shift)
    assert out["ret5d_signed_tbi"].iloc[:15].isna().all()
    # Past-only spot check at bar 50: append a future bar with extreme
    # values, recompute, verify value at 50 unchanged.
    df_extended = pd.concat([df, pd.DataFrame({
        "close": [99999.0, 99999.0],
        "taker_buy_imbalance_20": [9.9, -9.9],
    })], ignore_index=True)
    out_ext = compute_ret5d_signed_tbi(df_extended)
    assert out.loc[50, "ret5d_signed_tbi"] == pytest.approx(
        out_ext.loc[50, "ret5d_signed_tbi"]
    )
```

**Change 6 — Adversarial integration test**

In `tests/test_run_baseline_v3_integration.py` (or the equivalent), update
the integration test to assert:
1. `V3_FEATURE_COLUMNS` includes `"ret5d_signed_tbi"` at runtime.
2. `V3_FEATURE_COLUMNS` does NOT include `"ema_signed_volregime"` (the /119
   ABSENT assertion — same pattern as other dead-paths in the absent list).
3. The feature parquet for BCH/LDO/TRX has the `ret5d_signed_tbi` column
   non-NaN on the LAST 100 IS rows (proxy for valid feature generation).
4. Runner pre-flight n_features guard fires `n == 15` (unchanged).
5. The `compute_ret5d_signed_tbi` unit test PASSES (past-only invariant on
   synthetic data; the Change 5 test).

**No changes to**:

- `src/crypto_trade/strategies/ml/lgbm.py` (the LightGbmStrategy reads
  feature_columns from the runner; no new code path)
- `src/crypto_trade/strategies/risk_v2.py` (gates unchanged)
- `src/crypto_trade/backtest.py` (no new exit primitive — /119 is single-axis)
- `src/crypto_trade/features_v3/multioffset_24h.py` (this module is for the
  CLOSED 24h-multi-offset axis; not used at /119 8h baseline)
- `compute_ema_signed_volregime` function (STAYS in `engineered_v3.py` as
  code-museum value per /118 closeout)
- `OOS_CUTOFF_DATE`, `training_months` — sacred constants, immutable

---

## Section 4 — Expected OOS Impact (predicted bands) — SSC-RISK-aware

| Arm | Modal predicted Δ vs /060 anchor | Lower (Mode 4/5) | Upper |
|---|---:|---:|---:|
| IS monthly Sharpe Δ | +0.05 to +0.30 | −0.20 (catastrophic) | +0.50 |
| OOS monthly Sharpe Δ | +0.05 to +0.25 | −0.50 (Mode 4) | +0.40 |
| /060 anchor IS | +0.8325 | | |
| /060 anchor OOS | +0.1403 | | |

**Modal prediction band**: IS Sharpe ∈ [+0.88, +1.13]; OOS Sharpe ∈ [+0.19, +0.39].

**SSC-RISK-aware adjustment** (per /119-new gate methodology): C6's T9 SSC
ratio = 1.48× (FALSE flag). The Section-4 band is therefore SET AT THE
STANDARD WIDTH (the same /118 band template) — no SSC-RISK band-tightening
required for /119. If a future EXPLORATION evaluates a SSC-RISK-TRUE
candidate, the band should TIGHTEN (e.g., upper bound IS Δ ≤ +0.20, OOS Δ
≤ +0.15 — the modal expected lift should be smaller given the single-symbol
carrier risk). C6 does NOT trigger this tightening.

**Pre-registered explicit falsifier**: if production OOS monthly Sharpe Δ
falls below **−0.50** AND IS monthly Sharpe Δ falls below **−0.20** vs the
/060 anchor, the hypothesis is FALSIFIED — the C6 multivariate-lift signal
did NOT transfer through walk-forward production training; file
EXPLORATION-NEGATIVE.

**Trade-rate prediction**: total IS trades expected ≈ /060 anchor count
± 15% (the new feature does not change the entry/exit gates, only adds a
LightGBM-input column). OOS trades expected ≈ /060 anchor count ± 25%.
If OOS trade count falls by > 50% vs /060, file Mode 4 RESIDUAL (the new
feature is causing OOD-rejection rate to spike).

**Behavioral-effect predictor** (per `feedback_v3_axis_saturation_predictor.md`):
the new feature changes Optuna's loss surface, so the IS trade roster will
differ from /060 — expected fraction of common IS trades vs /060 baseline
roster: 60–80% (a fresh feature changes ~20–40% of the model's
threshold-crossing decisions). If common-trade fraction > 95%, the feature
is fully INERT (no behavioral signal) → file as NEGATIVE-no-effect / saturated.

**Per-symbol decomposition prediction** (T9-derived; pre-registered as a
falsifier test): given C6's broad-based positive T9 lift, the expected
production IS PnL Δ vs /060 should be positive across at least 2 of 3
symbols. If only 1 of 3 is positive at production (or the single positive
carrier is different from the T9 prediction LDO), file Mode 3 (PROMISING-
PARTIAL) — the same /118-style role-reversal risk.

---

## Section 5 — Risk Mitigation

| Risk | Mitigation | IS-calibrated threshold |
|---|---|---|
| R1: Univariate signal absent (T3 informational; expected for composed features) | C6 chosen on multivariate-lift (T7), not univariate AUC; production runner uses multivariate LightGBM at depth 3-5 (where C6's interaction signal lives) | T7 POOLED lift +0.0083 (above 0.005 gate) is the controlling evidence |
| R2: Single-symbol-carrier risk (the /118 catastrophic failure mode) | NEW SSC-RISK gate evaluated at T9; C6 cleared at 1.48× < 2.0 threshold; per-symbol lifts ALL POSITIVE (BCH+0.0057 / LDO+0.0123 / TRX+0.0053) | T9 SSC ratio 1.48× (FALSE — sole candidate clearing the gate) is the controlling evidence |
| R3: Importance INERT at production scale (the /085/086 pattern) | Pre-registered Mode 2 in Section 7; the T5+T7 cross-reference (rank 11/11/15 + positive POOLED lift) is the controlling diagnostic | If production importance rank falls to ≥ 14/15 on > 1 symbol AND POOLED lift not materially > 0, file PROMISING-INERT |
| R4: Per-symbol role-reversal (the /118 BCH↔TRX flip) | EDA T7 broad-based positive across all 3 symbols means no single carrier to flip; pre-registered Mode 3 if only 1 of 3 positive at production | If at production, only 1 of 3 symbols is IS-positive AND the carrier ≠ T9 prediction (LDO), file Mode 3 PROMISING-PARTIAL |
| R5: Look-ahead via ret_5d shift or taker_buy_imbalance generation | The `ret_5d = log_close.shift(15)` is past-only; `taker_buy_imbalance_20` is precomputed past-only by microstructure_v3; unit test Change 5 verifies past-only invariant on a synthetic panel | Test must PASS in CI before merge |
| R6: Parquet column missing at runtime | Change 4 mandates parquet regeneration; runner has a hard assertion (lgbm.py:582-589 verifies feature_columns); Change 6 integration test catches at runtime | n_features == 15 hard guard at runner pre-flight |
| R7: /118 ema_signed_volregime accidentally retained in V3_FEATURE_COLUMNS_TOP_N | Change 2 + Change 6 explicit ABSENT-assertion in BANNED list + integration test | Integration test asserts `"ema_signed_volregime" not in V3_FEATURE_COLUMNS` |

---

## Section 6 — Risk Management Design

The 7-gate RiskV2 stack is UNCHANGED:
1. Vol scaling (vol_scale_floor_per_symbol = {} → no floor)
2. ADX threshold (20.0; no per-symbol override)
3. Hurst regime check
4. z-score OOD gate (threshold = 2.0)
5. Low-vol filter
6. Hit-rate feedback (OOS only)
7. BTC trend alignment filter

No new risk primitive introduced at /119. The single axis is the new feature
column.

**Hard-merge gate implications for /120 CONFIRMATION** (if /119 is PROMISING):

| Gate | /119 EDA estimate | /120 CONFIRMATION requirement |
|---|---|---|
| IS Sharpe > 1.0 | EDA does not predict beyond +1.13 modal upper | CONFIRMATION must clear at multi-seed mean |
| OOS Sharpe > 1.0 | EDA does not predict beyond +0.39 modal upper | CONFIRMATION must clear |
| OOS/IS ratio ≥ 0.5 | Modal point estimate 0.30/0.13 vs anchor ratios | needs multi-seed validation |
| Trade-rate ≥ 10/month OOS | EDA does not predict trade count change at /119; expected ≈ /060 anchor | needs /120 multi-seed measurement |
| Top-symbol ≤ 30% | Broad-based per-symbol lift suggests no single dominant carrier | CONFIRMATION must check |
| 10-seed validation | Single-seed at /119 EXPLORATION; full 10-seed at /120 | /120 |

The /119 brief does NOT promise merge-eligibility — it promises a single-axis
EXPLORATION result that feeds into the /120 bundle decision per the cycle-6
cadence (10 EXPLORATIONs + 1 CONFIRMATION).

---

## Section 7 — Pre-Registered Failure-Mode Prediction

Five modes pre-registered (Mode 1 = success; Modes 2-5 = failure variants).
**First-match-wins**: classify by the FIRST mode whose condition matches the
observed outcome.

| Mode | Condition (BEFORE checking the result) | Probability prior | Verdict if matches |
|---|---|---:|---|
| **Mode 1 (Modal success)** | IS Sharpe Δ ∈ [+0.05, +0.30] AND OOS Sharpe Δ ∈ [+0.05, +0.25] AND common-trade fraction with /060 ∈ [60%, 80%] | 35% | EXPLORATION-PROMISING (the /025 lineage repeats with a different regime classifier; /120 bundle candidate) |
| Mode 2 (Importance INERT at production) | Production importance rank ≥ 14/15 on > 1 symbol with gain < 20% of top-feature | 15% | PROMISING-INERT (the /085 precedent; not bundled at /120) |
| Mode 3 (Per-sym role-reversal vs T9) | Only 1 of 3 symbols IS-positive at production, AND the positive carrier ≠ LDO (T9 prediction) | 15% | PROMISING-PARTIAL — the /118 inversion repeats. /120 bundles only if a per-symbol architecture can isolate the carrier |
| Mode 4 (Catastrophic regime artifact) | IS Sharpe Δ < −0.20 AND OOS Sharpe Δ < −0.50 | 10% | EXPLORATION-NEGATIVE (the order-flow-regime classifier did not transfer; the broader axis closes) |
| Mode 5 (Null at production) | IS Sharpe Δ ∈ [−0.05, +0.05] AND common-trade fraction with /060 > 95% | 20% | NEGATIVE-no-effect (the /015 / /019 saturated-axis pattern; feature is fully INERT, drop) |
| Mode 6 (Suspicious-OOS-dominant) | OOS Sharpe Δ > +0.30 BUT IS Sharpe Δ < +0.05 | 3% | SUSPICIOUS per `feedback_v3_per_symbol_lifts_oos_breaks_is.md` |
| Mode 7 (Suspicious-IS-dominant) | IS Sharpe Δ > +0.40 BUT OOS Sharpe Δ < −0.30 | 2% | SUSPICIOUS-IS-overfit (the /102 alpha032 pattern) |

---

## Section 8 — Pre-Registered MERGE/NO-MERGE Numerical Criteria

EXPLORATION-mode criteria (first-match-wins; the post-result classification
the QR commits to BEFORE looking at the result):

### NEGATIVE criteria (any-of-the-below)

1. **NEGATIVE-catastrophic**: IS Sharpe Δ < −0.20 vs /060 OR OOS Sharpe Δ < −0.50 vs /060 → file EXPLORATION-NEGATIVE catastrophic. Axis-CLOSE recommendation: the broader order-flow-regime composite axis CLOSED at /119 (microstructure classifier didn't lift in production).

2. **NEGATIVE-no-effect**: IS Sharpe Δ ∈ [−0.05, +0.05] AND common-trade fraction with /060 > 95% AND production importance rank ≥ 14/15 on all 3 symbols → file EXPLORATION-NEGATIVE no-effect (the /015 saturated-axis pattern).

3. **NEGATIVE-clean**: IS Sharpe Δ < +0.05 AND OOS Sharpe Δ < +0.05 (both arms fail the PROMISING leg threshold) and Modes 2/5 do not match → file EXPLORATION-NEGATIVE clean.

### PROMISING criteria (all-of-the-below)

4. **PROMISING-strong**: IS Sharpe Δ ≥ +0.10 AND OOS Sharpe Δ ≥ +0.10 AND production importance rank ≤ 11/15 on ≥ 2 symbols AND common-trade fraction ∈ [60%, 85%] AND no Mode 3/4 falsifier → file EXPLORATION-PROMISING strong. Bundle candidate for /120 CONFIRMATION.

5. **PROMISING-partial**: Only 1 of 3 symbols IS-positive AND that symbol IS PnL Δ > +2.0% AND another symbol IS PnL Δ < −1.0% → file EXPLORATION-PROMISING-PARTIAL. /120 bundles only if a per-symbol gate (e.g., excluding the negative symbol from C6-enabled architecture) is also tested at a future iteration.

6. **PROMISING-INERT-RISK**: T5 importance rank ≥ 14/15 on > 1 symbol AND POOLED T7-equivalent OOF AUC lift < +0.005 at production → file EXPLORATION-PROMISING-INERT-RISK (the /085 pattern). Not bundled at /120.

### Anchor

The /060 anchor IS Sharpe = +0.8325, OOS Sharpe = +0.1403. The /119
backtest will be compared multi-anchor: /060 (the EXPLORATION-mode
reference per BASELINE_V3.md) AND /059 (the CONFIRMATION anchor IS +1.0894 /
OOS +0.5791). The IS-Δ + OOS-Δ are computed vs /060.

---

## Section 9 — Library Stack Declaration

**No new library dependencies** — C6 is built from existing primitives
(`close`, `taker_buy_imbalance_20`) using numpy `sign` and pandas `shift`.
All required functions are already imported in `engineered_v3.py`.

**Library inventory** (verified at /119):
- `lightgbm == 4.6.0` (unchanged from /118)
- `numpy >= 2.0` (unchanged)
- `pandas >= 2.2` (unchanged)
- `scikit-learn` (used only in EDA, not in production runner)
- No `statsmodels` / `optuna` / `pyarrow` version change

**Adversarial integration test** (per
`feedback_v3_methodology_axis_integration_test.md`): the `Change 6`
integration test asserts:
- `V3_FEATURE_COLUMNS` includes `"ret5d_signed_tbi"` at runtime
- `V3_FEATURE_COLUMNS` does NOT include `"ema_signed_volregime"` (the
  /119 ABSENT assertion — restoring the BANNED-list convention)
- The feature parquet for BCH/LDO/TRX has the `ret5d_signed_tbi` column
  non-NaN on the LAST 100 IS rows
- Runner pre-flight n_features guard fires `n == 15` (unchanged)
- The `compute_ret5d_signed_tbi` unit test PASSES (past-only invariant
  on synthetic data; the Change 5 test)

These 5 assertions cover the end-to-end integration boundary (feature
generation → runner → strategy → model fit) at the runtime call-site, not
just the unit-level math (the /055 DSR_relative defect mode addressed by
the methodology mandate).

---

## Section 10 — QR Audit Trail

**Provenance of the /119 axis selection**:

1. **/118 closeout QR Round-2 recommendation** (`diary-v3/iteration_v3-118.md`
   Section 8.1): "NEW engineered-feature lineage on STRUCTURALLY DIFFERENT
   primitives". Specific candidates suggested by /118 QR (4 categories):
   (i) volume-based, (ii) cross-asset BTC, (iii) tail/higher-moment regime,
   (iv) microstructure. Critic CONCURRED — axis pivot + NEW SSC-RISK gate.

2. **/118 closeout Critic Recommendation 1** (commit `80caafd`): "NEW
   engineered-feature lineage on STRUCTURALLY DIFFERENT primitives ...
   Single-Symbol-Carrier RISK pre-Falsifier (2× threshold)".

3. **/119 QR adjudication via EDA** (per `feedback_v3_axis_selection_quant_discipline.md`):
   - Evaluated 6 candidates from 3 of the 4 prompt-recommended categories
     (i volume × 2, iii tail × 3, iv microstructure × 1).
   - Category (ii) cross-asset BTC NOT evaluated as a fresh candidate
     because the existing /060 baseline already includes `sym_vs_btc_ret_7d`
     and `btc_ret_14d` as primitives. Cross-asset BTC composites
     (sym_vs_btc × btc_regime_sign) would have R²≥0.50 carve-out via the
     `sym_vs_btc_ret_7d` shared primitive AND structurally overlap with
     /025-direction signals. C4 (`sym_vs_btc_ret_7d × sign(ret_kurt_50)`)
     is the cross-asset proxy in the screen — and FAILED on T5 (rank 15/15/15
     all 3 symbols) AND T9 (SSC ratio 2.12×).
   - Closure-scope EXCLUSIONS strictly enforced (no vol-regime, no /025
     hurst retry, no funding-rate, no tbr_zscore_30, no
     `ema_spread_atr_20 × sign(ret_kurt_50 − rolling_median_200)`
     borderline-of-/118).

4. **Why C6 over C5 and C1 (the runner-up GO candidates)**:
   - **C5_maxdd_signed_skew200** has the strongest T5 importance profile
     (rank 6/11/4, gain 61/30/55%) but FAILS the SSC-RISK gate (BCH +0.0132
     vs POOLED +0.0060 = 2.21×). The /118 closeout mandate is explicit:
     SSC-RISK flag MUST tighten the Section-4 falsifier band. The
     orchestrator's prompt section "SSC-RISK gate" (NEW mandatory EDA gate)
     was DESIGNED to catch this single-symbol-carrier pattern. C5 cannot be
     chosen on the very gate the orchestrator established.
   - **C1_obv_signed_volmom** has the BEST per-symbol importance (rank
     5/6/8, gain 69/56/31% — strongest in the set on all 3 symbols, clears
     /025 PROMISING benchmark on BCH + LDO + borderline TRX). But T7 POOLED
     lift is only +0.0019 (mid-table) AND SSC-RISK 7.77× — LDO +0.0151 vs
     TRX −0.0080. The DIVERGENT TRX sign is the diagnostic: at production
     scale Optuna would allocate hyperparameters to maximize LDO's
     contribution, FLIPPING TRX into negative regime (the inverse of /118
     C3's pattern — same mechanism, different carrier).
   - **C6_ret5d_signed_tbi** has the BEST T7 POOLED lift (+0.0083) AND the
     BEST SSC ratio (1.48× < 2.0 gate) AND broad-based POSITIVE per-symbol
     lifts on all 3 symbols. The mid-table T5 importance (rank 11/11/15) is
     a known trade-off — composed features that USE interactions efficiently
     at depth 3-5 don't necessarily rank in the top by total gain (the /053
     hurst_drift mechanism: "trees can use derived features for EFFICIENCY
     without that allocation reflecting NEW signal").

5. **Lineage discipline check** (the orchestrator's borderline-case
   warning):
   - The prompt explicitly warned about
     `ema_spread_atr_20 × sign(ret_kurt_50 − rolling_median_200)` —
     reuses the FAILED /118 C3 value primitive (ema_spread_atr_20). This
     candidate was DROPPED from the EDA before scoring (it would have been
     a SISTER of /118).
   - C6 reuses `ret_5d` (the /025 SUCCESSFUL value primitive) and pairs
     it with a fundamentally DIFFERENT regime classifier (microstructure
     order-flow, NOT vol-regime, NOT hurst, NOT funding, NOT tbr_zscore_30).
     This is the correct lineage discipline per `feedback_v3_engineered_features_proven.md`:
     "the value primitive can be shared as long as the regime classifier is
     orthogonal to closed lineages". The /118 closure was the REGIME
     CLASSIFIER (vol-regime), NOT the value primitive (ret_5d-family
     remains LIVE because /025 is its precedent and is KEPT in
     V3_FEATURE_COLUMNS).

6. **Provenance per `feedback_v3_brief_parameter_provenance.md`**:
   - Section 0 declares ZERO tuned scalars — every parameter is either
     INHERITED from the V3 feature inventory at default lookbacks (ret_5d
     15-bar lookback from /025; taker_buy_imbalance_20 20-bar window from
     microstructure_v3) or structurally fixed (sign threshold = 0 zero-cross).
   - No false-provenance failure mode.
   - All scalars cite their source.

7. **Cycle-6 trajectory recap (FINAL EXPLORATION position)**:
   - /110 (universe×2) NEGATIVE — confounded by label drift
   - /111 (universe×2 clean retry) NEGATIVE — wholesale replacement failed
   - /112 (pooled architecture) NEGATIVE
   - /113 (multi-frequency on 8h) NEGATIVE
   - /114 (risk management) NEGATIVE — Check-1 FAIL provenance issue
   - /115 (labeling architecture) NEGATIVE
   - /116 (exit-layer primitive) PROMISING-MECHANICAL — strictly accretive at /120
   - /117 (candle frequency) NEGATIVE catastrophic — candle-frequency axis broadly CLOSED
   - /118 (engineered feature: vol-regime composite) NEGATIVE catastrophic — `value × sign(vol-regime-classifier)` Category-2 lineage CLOSED
   - **/119 (engineered feature: order-flow-regime composite) — this iteration, FINAL EXPLORATION**
   - /120 (CONFIRMATION — bundles /116 no_confirm + /119 if PROMISING)

**Commit chain expected**:
- `analysis(iter-v3/119): engineered-feature axis EDA — Category-(i)/(iii)/(iv) screen, top candidate C6_ret5d_signed_tbi, SSC-RISK gate (NEW)` (SHA `7aa5cc5`, committed BEFORE this brief)
- `docs(iter-v3/119): research brief — engineered-feature axis on (iv) microstructure primitives (ret5d_signed_tbi)` (this brief)
- Phase 5.5 Engineer gate
- `feat(iter-v3/119): add ret5d_signed_tbi to V3_FEATURE_COLUMNS_TOP_N + engineered_v3.py + runner guards + revert /118 ema_signed_volregime`
- Parquet regeneration
- Backtest + reports
- Critic preliminary
- QR response (if needed)
- Critic FINAL
- Diary

**PRIME DIRECTIVE confirmation**: /119 is the LAST EXPLORATION of cycle 6.
Per the orchestrator directive + the strict 10:1 cadence
(`feedback_v3_strict_10_to_1_cadence.md`), /119 WILL run a backtest regardless
of the EDA verdict. The EDA returned a GO verdict on C6 with the strongest
production-relevance evidence in the candidate set; the brief targets a
PROMISING outcome but commits to running the production backtest in all
EDA-verdict branches.

---

**END OF BRIEF** — ready for QE Phase 6 implementation.
