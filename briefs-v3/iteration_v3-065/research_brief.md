# iter-v3/065 — Research Brief

**Branch**: `iteration-v3/065`
**EDA SHA**: `662659c`
**Setup commit SHA**: (LOCKED at setup commit — Section 10 backfilled post-LOCK)
**Iteration type**: EXPLORATION (cycle 1 #6 of 10; NON-FEATURE PIVOT; UNIVERSAL LABELING AXIS)
**Axis**: UNIVERSAL TRIPLE-BARRIER SL WIDENING — DEFAULT_ATR_MULTIPLIERS (2.0, 1.0) → (2.0, 1.5)

---

## Section 0 — Data Split Declaration

**UNCHANGED.** OOS_CUTOFF_DATE = `2025-03-24` (IMMUTABLE; sacred constant per `feedback_no_cheating.md`). Training window = 24 months walk-forward (IMMUTABLE per `feedback_training_window.md`). Symbol universe = BCHUSDT, LDOUSDT, TRXUSDT (3 symbols, UNCHANGED from /051 SYSTEM-LEVEL REVERT). Feature universe = 14 BASELINE_V3 features (UNCHANGED post-/064 revert at commit `04080c4`; V3_FEATURE_COLUMNS_TOP_N == /060 anchor).

## Section 0.5 — Iteration Type Declaration

**TYPE**: EXPLORATION.

- **Cycle 1 EXPLORATION slot**: #6 of 10 (post /058 RE-ANCHOR + /059 RE-ANCHOR #2; cycle counting per BASELINE_V3.md /059).
- **Sub-type**: **NON-FEATURE PIVOT — UNIVERSAL LABELING AXIS**. Per Critic /064 Rec #4 NON-FEATURE pivot mandate after /060 14-feature anchor was empirically classified as a LOCAL OPTIMUM at single-seed n_trials=35 (Rule 5 of `feedback_v3_iter064_process_lessons.md`).
- **Run mode**: `--exploration` (ENSEMBLE_SIZE=3, seeds from outer=42 lineage subset [191664963, 1662057957, 1405681631]).
- **Optuna budget**: `--n-trials 35` per (symbol × walk-forward month × seed). Total trials = 35 × 3 × 3 = 315 (matches /060-/064 EXPLORATION-mode budget).
- **Wall-clock target**: ~1.1h (within 2h EXPLORATION HARD CAP per `feedback_v3_cadence_discipline.md`).

**Cycle 1 catalog status before /065**:

| Slot | Iter | Axis | Verdict |
|---|---|---|---|
| #1 | /060 | EXPLORATION-MODE-REFERENCE (anchor) | PROMISING-EXPLORATION |
| #2 | /061 | TRX RiskV2 anti-Kelly (Path B vol_scale_floor) | INERT-AT-EXPLORATION (closed) |
| #3 | /062 | DSR_relative recalibration (Path C passive) | PASSIVE-DIAGNOSTIC (Path B4 deferred to /069) |
| #4 | /063 | MASS FEATURE EXPANSION (Path B 46 features) | SUSPICIOUS-OOS-DOMINANT + IS-COLLAPSE (closed) |
| #5 | /064 | Phased mass-expansion #1 (+adx_14) | NEGATIVE (closed) |
| **#6** | **/065** | **NON-FEATURE PIVOT: UNIVERSAL SL widen 1.0 → 1.5 (Path D)** | TBD |
| #7-9 | /066-068 | TBD | TBD |
| CONFIRMATION | /069 | Bundle + Path B4 implementation | TBD |

**Why NON-FEATURE pivot now**:

1. **Critic /064 Rec #4 directive (binding)**: "iter-v3/065 should be a NON-FEATURE axis (labeling, ensemble parameters, risk primitive, universe expansion) selected by QR with EDA backing per `feedback_v3_axis_selection_quant_discipline.md`. Defer phased-mass-expansion to CONFIRMATION-mode multi-seed runs."

2. **Structural inference per `feedback_v3_iter064_process_lessons.md` Rule 5**: /060 14-feature anchor is a LOCAL OPTIMUM at single-seed n_trials=35. Two consecutive feature-axis EXPLORATIONs (/063 mass, /064 single-feature) both produced BCH-concentration + LDO-collapse failure pattern. Adding/removing features around /060 at single-seed cannot productively escape.

3. **Per `feedback_v3_per_symbol_lifts_oos_breaks_is.md`** (system-level confirmed across 2 CONFIRMATIONs): per-symbol customizations break IS aggregate at multi-seed. UNIVERSAL labeling is the structurally safe path — all 3 symbols see the same logic.

4. **Labels are ground truth**: if LDO labels are noisy at default (2.0, 1.0), no feature engineering can fix it. The label distribution analysis in Section 2 confirms LDO has structural label noise at the default.

## Section 1 — Testable Hypothesis (ONE sentence)

> Universal SL widening from `DEFAULT_ATR_MULTIPLIERS=(2.0, 1.0)` to `(2.0, 1.5)` produces ≥+0.10 IS Sharpe AND ≥+0.20 OOS Sharpe vs /060 baseline (IS +0.8325 / OOS +0.1403) primarily via reduced premature-SL hits on LDO (LDO long_tp_hit_rate +8.6pp lift from 30.8% to 39.4% in IS labeling counterfactual per EDA T2/T3) while preserving BCH/TRX label balance (universal change, no per-symbol asymmetry).

## Section 2 — Numerical EDA Tables (EDA SHA `662659c`)

EDA committed at SHA `662659c` (`analysis/iteration_v3-065/labeling_parameter_eda.py`). Produces 6 tables. Anchor = iter-v3/060 EXPLORATION-MODE-REFERENCE (IS +0.8325 / OOS +0.1403; 3-seed lineage subset of /059's unified 10-seed mass). **NOT iter-v3/064** (axis CLOSED per Critic FINAL `452fcf2`).

### Section 2.1 — T0 Anchor-value declaration (per Critic /064 Rec #1)

| metric | value | source (file:line) |
|---|---:|---|
| monthly_sharpe_in_sample | **+0.8325** | `reports-v3/iteration_v3-060/comparison.csv:2` |
| monthly_sharpe_out_of_sample | **+0.1403** | `reports-v3/iteration_v3-060/comparison.csv:2` |
| BCH_OOS_weighted_pnl | **+1.9078** | `reports-v3/iteration_v3-060/comparison.csv:18` |
| LDO_OOS_weighted_pnl | **-19.7208** | `reports-v3/iteration_v3-060/comparison.csv:19` |
| TRX_OOS_weighted_pnl | **+23.3119** | `reports-v3/iteration_v3-060/comparison.csv:20` |
| n_trades_out_of_sample | **102** | `reports-v3/iteration_v3-060/comparison.csv:7` |

These are the BIT-EXACT /060 anchor values per Phase 5.5 anchor-value correctness gate (Rule 1 of `feedback_v3_iter064_process_lessons.md`). Brief Section 4 falsifier bands reference these.

### Section 2.2 — T1 Label distribution at default (TP=2.0, SL=1.0, 21 bars) per symbol

| symbol | n_obs | long_tp_hit_rate | long_sl_hit_rate | long_timeout_rate | label_balance_ratio | mean_close_usd | mean_natr_pct | effective_tp_pct |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| BCHUSDT | 1888 | **0.3686** | **0.6255** | 0.0058 | **0.9697** | 331.52 | 4.21% | 8.42% |
| LDOUSDT | 893  | **0.3080** | **0.6865** | 0.0056 | **0.7648** | 1.91 | 5.36% | 10.72% |
| TRXUSDT | 1869 | **0.4227** | **0.5693** | 0.0080 | **0.6673** | 0.086 | 3.28% | 6.55% |

**Reading**:
- LDO has the **LOWEST long_tp_hit_rate** (30.8%) AND the **HIGHEST long_sl_hit_rate** (68.7%) of all 3 symbols.
- LDO `tp_sl_hit_ratio = 0.4486` (T3) — by far the worst (BCH 0.5893, TRX 0.7425).
- LDO's effective TP threshold (5.36% × 2.0 = 10.72%) is actually wider than BCH (8.42%) in percentage terms (LDO is more volatile). The structural noise is NOT under-sized TP — it is **over-cut SL** relative to LDO's mean-reversion noise.
- Label balance ratios reveal LDO is **most skewed** (0.7648 vs BCH 0.9697 vs TRX 0.6673), indicating disproportionate -1 labels (i.e., short-favorable outcomes / SL-hits-before-TP).
- Average bars-to-long-TP is ~3.2 bars across all 3 symbols at default — well within the 21-bar timeout. The 21-bar timeout is NOT the binding constraint.

### Section 2.3 — T2 Counterfactual label distributions (6 alternatives)

| path_label | symbol | n_label_pos | n_label_neg | label_balance_ratio | long_tp_hit_rate | long_sl_hit_rate |
|---|---|---:|---:|---:|---:|---:|
| default_2.0_1.0_21bars | BCHUSDT | 929 | 958 | 0.9697 | 0.3686 | 0.6255 |
| default_2.0_1.0_21bars | LDOUSDT | 387 | 506 | **0.7648** | **0.3080** | **0.6865** |
| default_2.0_1.0_21bars | TRXUSDT | 1121 | 748 | 0.6673 | 0.4227 | 0.5693 |
| PathA_tp1.5_sl1.0_21bars | LDOUSDT | 391 | 502 | 0.7789 | 0.3617 | 0.6361 |
| PathA_tp2.5_sl1.0_21bars | LDOUSDT | 402 | 491 | 0.8187 | 0.2665 | 0.7245 |
| PathB_tp2.0_sl0.75_21bars | LDOUSDT | 381 | 512 | 0.7441 | 0.2721 | 0.7245 |
| **PathD_tp2.0_sl1.5_21bars** | **LDOUSDT** | **407** | **486** | **0.8374** | **0.3942** | **0.5901** |
| PathC_tp2.0_sl1.0_7bars | LDOUSDT | 427 | 480 | 0.8896 | 0.2867 | 0.6472 |
| PathC_tp2.0_sl1.0_42bars | LDOUSDT | 401 | 471 | 0.8514 | 0.3131 | 0.6869 |

**LDO-row reading**:
- **Path D (TP=2.0, SL=1.5)** is the BEST among options at LDO `long_tp_hit_rate` (39.4% — +8.6pp from default 30.8%).
- Path D LDO `long_sl_hit_rate` falls from 68.7% → 59.0% (-9.6pp).
- Path D LDO `label_balance_ratio` lifts 0.7648 → 0.8374 (+0.073).
- Path A (TP=1.5) lifts LDO TP hit rate to 36.2% (lower than D's 39.4%) and IS shorter-cycle.
- Path C (timeout=7 bars) lifts LDO balance more (0.8896) but COMPRESSES the trend cycle — LDO TP hit rate FALLS to 28.7%. The "more balanced" labels come from MORE timeout-no-TP outcomes, not real signal.
- Path B (SL=0.75) WORSENS LDO TP hit rate to 27.2% — tightening SL makes the problem worse.

### Section 2.4 — T3 LDO-specific label-noise analysis

| symbol | long_tp_hit_rate | long_sl_hit_rate | label_balance_ratio | avg_bars_to_long_tp | avg_bars_to_long_sl | tp_sl_hit_ratio |
|---|---:|---:|---:|---:|---:|---:|
| BCHUSDT | 0.3686 | 0.6255 | 0.9697 | 3.90 | 3.26 | **0.5893** |
| LDOUSDT | 0.3080 | 0.6865 | 0.7648 | 3.19 | 2.90 | **0.4486** |
| TRXUSDT | 0.4227 | 0.5693 | 0.6673 | 4.32 | 2.85 | **0.7425** |

**Reading**: LDO's `tp_sl_hit_ratio = 0.4486` is structurally the worst of the 3 symbols by a wide margin (24% relative worse than BCH; 40% worse than TRX). LDO's avg-bars-to-long-SL = 2.90 (faster than BCH's 3.26) and slower-than-LDO-TP (LDO TP comes at 3.19 — barely later than SL). The structural pattern: **LDO's SL barrier is being hit ~0.3 bars BEFORE the would-be TP barrier on average for those cases where price is moving favorably but with intra-bar noise**. Widening SL from 1.0×ATR → 1.5×ATR gives LDO trades 50% more room to absorb adverse noise before being cut.

### Section 2.5 — T4 Predicted impact bands per Path

| path_label | tp | sl | timeout | avg_balance | Δ_balance_vs_default | avg_tp_hit_rate | ldo_balance | ldo_tp_hit_rate | ldo_sl_hit_rate |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| default | 2.0 | 1.00 | 21 | 0.8006 | 0.0000 | 0.3664 | 0.7648 | 0.3080 | 0.6865 |
| PathA_tp1.5 | 1.5 | 1.00 | 21 | 0.8324 | +0.0318 | 0.4212 | 0.7789 | 0.3617 | 0.6361 |
| PathA_tp2.5 | 2.5 | 1.00 | 21 | 0.8040 | +0.0034 | 0.3216 | 0.8187 | 0.2665 | 0.7245 |
| PathB_tp2.0_sl0.75 | 2.0 | 0.75 | 21 | 0.7903 | -0.0104 | 0.3174 | 0.7441 | 0.2721 | 0.7245 |
| **PathD_tp2.0_sl1.5** | **2.0** | **1.50** | **21** | **0.8240** | **+0.0234** | **0.4440** | **0.8374** | **0.3942** | **0.5901** |
| PathC_tp2.0_sl1.0_7b | 2.0 | 1.00 | 7 | 0.8764 | +0.0758 | 0.3225 | 0.8896 | 0.2867 | 0.6472 |
| PathC_tp2.0_sl1.0_42b | 2.0 | 1.00 | 42 | 0.8255 | +0.0249 | 0.3722 | 0.8514 | 0.3131 | 0.6869 |

**Path D is the optimal pick**:
- **Highest avg long_tp_hit_rate (0.4440)** — beats Path A (0.4212), Path C (~0.32), and default (0.3664) by clear margins. TP hits are the signal source; raising TP-hit rate raises label quality.
- **Highest LDO long_tp_hit_rate (0.3942)** — the largest LDO TP improvement of any Path (+8.6pp from default 30.8%; +3.2pp better than runner-up Path A).
- **LDO sl_hit_rate FALLS to 0.5901** — the LARGEST LDO SL reduction (-9.6pp from default 68.7%; -4.6pp better than runner-up Path A's 0.6361).
- BCH balance: 0.9524 (preserved within 1.8pp of default 0.9697).
- TRX balance: 0.6823 (modest +0.015 lift vs default 0.6673).
- This is a TRUE universal change: all 3 symbols see the same labeling logic, no per-symbol asymmetry per `feedback_v3_per_symbol_lifts_oos_breaks_is.md`.

### Section 2.6 — T5 Path selection summary

| path_label | tp | sl | timeout | ldo_balance | bch_balance | trx_balance | avg_balance | ldo_tp_hit_rate | ldo_sl_hit_rate |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| **PathD_tp2.0_sl1.5** | **2.0** | **1.50** | **21** | **0.8374** | **0.9524** | **0.6823** | **0.8240** | **0.3942** | **0.5901** |
| PathC_tp2.0_sl1.0_7b | 2.0 | 1.00 | 7 | 0.8896 | 0.9885 | 0.7512 | 0.8764 | 0.2867 | 0.6472 |
| PathA_tp1.5 | 1.5 | 1.00 | 21 | 0.7789 | 0.9780 | 0.7402 | 0.8324 | 0.3617 | 0.6361 |

**Why Path D over Path C**: Path C (7-bar timeout) produces higher LDO `label_balance_ratio` (0.8896 vs Path D 0.8374), but its mechanism is wrong — Path C COMPRESSES the cycle so fewer trades reach TP within window (LDO TP rate falls to 28.7%). The balance improvement is artifactual (more timeout-no-TP labels → neutral, balanced via fwd-return-sign default). Path C **lowers** TP hit rate — it does not solve the structural noise problem. Path D directly addresses the mechanism: widening SL gives LDO room to absorb adverse noise before being cut prematurely.

### Section 2.7 — Anchor declaration

**Anchor**: iter-v3/060 EXPLORATION-MODE-REFERENCE (IS +0.8325 / OOS +0.1403). **NOT iter-v3/064** (axis CLOSED per Critic FINAL `452fcf2`).

iter-v3/060 is the legitimate cycle 1 EXPLORATION-mode baseline (3-seed lineage subset of /059 10-seed CONFIRMATION). Per `feedback_v3_cycle1_axis_pass_criteria.md` Rec #1: cycle 1 EXPLORATIONs use /060 as the EXPLORATION-mode anchor; CONFIRMATION-mode delta vs /059 is evaluated only at /069 CONFIRMATION.

### Section 2.8 — Summary

- LDO has structural label noise at default (TP_hit_rate=30.8%, SL_hit_rate=68.7%, balance=0.7648).
- LDO's avg-bars-to-SL (2.90) is faster than avg-bars-to-TP (3.19) — SL is being hit BEFORE the would-be TP, by ~0.3 bars (intra-bar noise).
- Path D (TP=2.0, SL=1.5) widens SL by 50% — universally — directly addressing LDO's premature-SL mechanism.
- Path D lifts LDO long_tp_hit_rate from 30.8% → 39.4% (+8.6pp); lifts overall avg_tp_hit_rate (0.3664 → 0.4440, +7.8pp).
- BCH and TRX label balance/TP rate preserved within reasonable bounds (no per-symbol asymmetry per universal change).
- Predicted impact: small expected shift IS (non-feature axis), single-seed lottery range OOS.

## Section 3 — Proposed Changes (enumerated)

### Sub-fix 1 — DEFAULT_ATR_MULTIPLIERS edit (2.0, 1.0) → (2.0, 1.5)

**ONE substantive change**. Universal SL multiplier raised from 1.0× to 1.5× ATR. TP multiplier preserved at 2.0× ATR. Timeout preserved at 21 bars (10080 minutes).

File: `src/crypto_trade/features_v3/__init__.py` line 222
```python
# Before (iter-v3/043 revert state, locked since)
DEFAULT_ATR_MULTIPLIERS: tuple[float, float] = (2.0, 1.0)

# After (iter-v3/065 Path D — universal SL widening)
DEFAULT_ATR_MULTIPLIERS: tuple[float, float] = (2.0, 1.5)
```

**Why this is the ONE change**: per `feedback_v3_engineered_features_dont_stack.md` single-axis EXPLORATION discipline. The SL multiplier change is a TRUE universal change — all 3 symbols receive the same labeling logic. V3_ATR_MULTIPLIERS_PER_SYMBOL remains empty `{}`, so all 3 symbols use the new DEFAULT.

**Why not change TP or timeout**: per EDA T4/T5, Path D (SL widening alone) has the best LDO TP-hit-rate lift (+8.6pp) AND highest avg-balance preservation. Path A (TP=1.5) is runner-up. Path B (SL=0.75) WORSENS LDO. Path C (timeout=7) compresses the trend cycle artificially. Combining TP and SL would be 2-axis variation forbidden under `feedback_v3_engineered_features_dont_stack.md`.

**Anti-snooping note**: PathD's (2.0, 1.5) was previously deployed per-symbol on LDO at iter-v3/032+ (1.5, 0.75 era) and removed at iter-v3/051 SYSTEM-LEVEL REVERT per `feedback_v3_per_symbol_lifts_oos_breaks_is.md`. The /051 revert was specifically a PER-SYMBOL revert. UNIVERSAL (2.0, 1.5) has NEVER been tested. /065 is the first test of universal SL widening at single-seed EXPLORATION mode.

### Sub-fix 2 — ITERATION_LABEL bump

File: `run_baseline_v3.py` line 128
```python
# Before
ITERATION_LABEL = "v3-064"

# After
ITERATION_LABEL = "v3-065"
```

### Sub-fix 3 — Test updates

Two test files reference DEFAULT_ATR_MULTIPLIERS hardcoded to (2.0, 1.0):

| File | Current assertion | New assertion |
|---|---|---|
| `tests/features_v3/test_features_for_symbol.py:285` | `DEFAULT_ATR_MULTIPLIERS == (2.0, 1.0)` | `DEFAULT_ATR_MULTIPLIERS == (2.0, 1.5)` |
| `tests/features_v3/test_atr_multipliers_for_symbol.py:31,38` | `DEFAULT_ATR_MULTIPLIERS == (2.0, 1.0)` | `DEFAULT_ATR_MULTIPLIERS == (2.0, 1.5)` |

Update docstrings + assertion messages to reference iter-v3/065 Path D rationale.

### Sub-fix 4 — Runner consistency assertion

File: `run_baseline_v3.py` lines 413-420 (`_verify_feature_columns`)
```python
# Before
if DEFAULT_ATR_MULTIPLIERS != (2.0, 1.0):
    raise RuntimeError(
        f"DEFAULT_ATR_MULTIPLIERS = {DEFAULT_ATR_MULTIPLIERS} — expected (2.0, 1.0). "
        "iter-v3/047: DEFAULT_ATR_MULTIPLIERS must be (2.0, 1.0) ..."
    )

# After
if DEFAULT_ATR_MULTIPLIERS != (2.0, 1.5):
    raise RuntimeError(
        f"DEFAULT_ATR_MULTIPLIERS = {DEFAULT_ATR_MULTIPLIERS} — expected (2.0, 1.5). "
        "iter-v3/065 Path D: universal SL widening from 1.0x to 1.5x ATR. "
        "V3_ATR_MULTIPLIERS_PER_SYMBOL remains empty — all 3 symbols use DEFAULT. "
        "Verify DEFAULT_ATR_MULTIPLIERS = (2.0, 1.5) in features_v3/__init__.py."
    )
```

### Sub-fix 5 — Parquet regeneration

**NOT required.** ATR computation (`natr_21_raw` column) is unchanged. The MULTIPLIER change is consumed inside `label_trades()` via `atr_tp_multiplier` and `atr_sl_multiplier` kwargs (per `run_baseline_v3.py:1349-1350`). No new feature columns needed; no parquet regen.

### Sub-fix 6 — ENSEMBLE_SIZE assertion

**UNCHANGED**. EXPLORATION_ENSEMBLE_SIZE=3, CONFIRMATION_ENSEMBLE_SIZE=10 (per Phase B-3 unified architecture). /065 runs with `--exploration` (ENSEMBLE_SIZE=3).

### Sub-fix 7 — V3_FEATURE_COLUMNS_TOP_N

**UNCHANGED**. Stays at 14 features post-/064 revert (commit `04080c4`). NON-FEATURE axis means feature universe is held constant.

## Section 4 — Predicted Bands + Falsifiers

### Section 4.1 — Headline Sharpe prediction (single-seed EXPLORATION mode)

| Metric | /060 anchor | Predicted /065 | Predicted Δ band |
|---|---:|---:|---|
| IS monthly Sharpe | +0.8325 | +0.70 to +0.95 | Δ ∈ [-0.13, +0.13] |
| OOS monthly Sharpe | +0.1403 | -0.05 to +0.40 | Δ ∈ [-0.20, +0.26] |
| OOS/IS daily ratio | 0.21 | 0.10 to 0.50 | within [0.10, 0.50] |
| IS trades | ~159 | 140 to 200 | Δ ∈ [-20, +40] |
| OOS trades | ~94 | 80 to 110 | Δ ∈ [-15, +20] |
| frac_positive_paths | 0.6444 | 0.50 to 0.75 | architecture-invariant ≥0.50 |
| BCH IS share | ~95% | 70%-150% | one-sided ≥ 80% per Critic /060 Rec #1 |

**Rationale for band widths**: this is a UNIVERSAL LABELING CHANGE (non-feature axis). Historical precedents at universal labeling changes single-seed n_trials=35:
- iter-v3/042 universal ATR (1.5, 0.75) — Path C IS collapse NEGATIVE: IS Sharpe -0.5941, TRX OOS -33 swing. **But** that was TIGHTENING SL (smaller multiplier, fewer trades survive); iter-v3/065 is WIDENING SL (larger multiplier, more trades survive to TP).
- iter-v3/039 PER-SYMBOL LDO ATR (2.0, 1.5) — multi-seed CONFIRMATION: IS -0.08 / OOS +1.47 (NO-MERGE; IS regression dominated by per-symbol asymmetry; universal change should not have this asymmetry).
- iter-v3/045 BCH BLOCK + LDO ATR — single-seed PROMISING: IS +0.75 / OOS +3.53 (later compressed at multi-seed).
- Universal SL widening is structurally novel — has NOT been tested at single-seed (only per-symbol LDO at /032+).

**Predicted bands are TIGHTER than /064's** because:
1. Non-feature axis → no Optuna feature-subsample lottery
2. Labels are pre-computed before training → directly observable mechanism
3. EDA T4 shows mean TP-hit-rate +7.8pp universally → expected modest behavioral shift

### Section 4.2 — BCH IS sensitivity prediction (per /059 Critic Rec #3 carry-forward)

BCH IS share at /060 was 176.68% (3-seed averaging structurally amplified BCH's IS dominance vs LDO+TRX). The one-sided ≥80% gate applies per `feedback_v3_cycle1_axis_pass_criteria.md` Rec #1.

Wider SL (1.0× → 1.5×) is expected to:
- INCREASE BCH trade survival rate (BCH long_sl_hit_rate falls 0.6255 → 0.5524 per EDA T2)
- Lift BCH long_tp_hit_rate from 36.9% to 42.8% (+5.9pp)
- Likely PRESERVE BCH IS dominance (BCH is the strongest symbol; its edge compounds with wider SL)

**Predicted BCH IS share at /065**: 70% to 150% (one-sided ≥ 80% gate cleared in expectation; band wider than baseline because universal labeling change affects BCH's trade roster).

### Section 4.3 — Behavioral effect predictor (per `feedback_v3_axis_saturation_predictor.md`)

**Predicted trade-count change** (IS + OOS):

| Symbol | IS trades /060 | IS trades /065 predicted | OOS trades /060 | OOS trades /065 predicted |
|---|---:|---:|---:|---:|
| BCH | ~80 | 75-100 (modest lift; more trades survive to TP) | ~37 | 35-50 |
| LDO | ~13 | 13-25 (lift expected; fewer premature SL cuts) | ~13 | 12-25 (lift expected) |
| TRX | ~78 | 70-90 (modest preservation) | ~44 | 40-50 |
| **Total** | **~171** | **[160, 215]** | **~94** | **[87, 125]** |

**Behavioral-effect rationale**: Path D widens SL by 50%, leading to:
1. MORE long-TP outcomes (avg TP rate +7.8pp per EDA T4)
2. FEWER long-SL outcomes (LDO -9.6pp; BCH -7.3pp; TRX -9.7pp)
3. Slightly MORE bars-per-trade (no compression effect)
4. Slightly fewer total trades initially (LightGBM may filter more aggressively when label quality is higher; or fewer entry signals when broader SL widens "uncertainty zone")

**Saturation falsifier**: if trade-count Δ < |5| total OOS, the axis is INERT (per `feedback_v3_axis_saturation_predictor.md`) — the labeling change had no effective downstream behavioral impact.

### Section 4.4 — Pre-registered FALSIFIER bands (BINDING GATES)

| Gate ID | Gate | Threshold | Action if FAIL |
|---|---|---|---|
| **A.1** | IS Sharpe shift | ≥ -0.20 vs /060 (i.e., IS ≥ +0.6325) | FAIL → NEGATIVE / IS-COLLAPSE |
| **A.2** | OOS Sharpe shift | ≥ -0.30 vs /060 (i.e., OOS ≥ -0.1597) | FAIL → NEGATIVE / OOS-NEGATIVE |
| **A.3** | frac_positive_paths | ≥ 0.50 | FAIL → methodology FAIL (CPCV degenerate) |
| **A.4** | No methodology FAIL | Critic 13 checks + §11 anti-pattern scan | FAIL → BLOCK |
| **B.5** | BCH IS share | one-sided ≥ 80% | FAIL → BCH collapse warning |
| **C.6** | IS trade count | ∈ [100, 250] | FAIL → trade-rate floor violation |
| **C.7** | OOS trade count | ∈ [60, 130] | FAIL → trade-rate floor violation |
| **D.8** | BCH IS wpnl Δ | within [-10, +10] vs /060 | FAIL → BCH IS regression |
| **D.9** | BCH OOS wpnl Δ | within [-10, +10] vs /060 (+1.9078 anchor) | FAIL → BCH OOS regression |
| **D.10** | LDO IS wpnl Δ | within [-5, +20] vs /060 (target lift) | FAIL → LDO IS regression |
| **D.11** | LDO OOS wpnl Δ | within [-5, +20] vs /060 (-19.7208 anchor; target lift) | FAIL → LDO OOS collapse |
| **D.12** | TRX IS wpnl Δ | within [-10, +10] vs /060 | FAIL → TRX IS regression |
| **D.13** | TRX OOS wpnl Δ | within [-10, +10] vs /060 (+23.3119 anchor) | FAIL → TRX OOS regression |
| **E.14** | Tests passing | All v3 feature + ATR tests PASS | FAIL → BLOCK |
| **E.15** | ensemble_summary | mode=exploration, size=3 | FAIL → mode-flag wiring bug |
| **E.16** | EDA-implementation parity | DEFAULT_ATR_MULTIPLIERS == (2.0, 1.5) at runtime | FAIL → process violation |

**Notes on falsifier bands**:
- Gates A.1 (IS ≥ -0.20) and A.2 (OOS ≥ -0.30) are the LOCKED Section 8.4 disjunctive-OR NEGATIVE thresholds per `feedback_v3_cycle1_axis_pass_criteria.md`. Either single-gate FAIL → NEGATIVE classification.
- Gates D.10 & D.11 target LDO LIFT (asymmetric upper band) — the hypothesis predicts LDO improvement; gates allow modest LDO regression while requiring no catastrophic LDO collapse.
- Gates D.8-D.13 are per-symbol falsifier bands per `feedback_v3_per_symbol_target_axis_falsifier.md` (target-symbol axis discipline).

### Section 4.5 — Anti-stacking check

Per `feedback_v3_engineered_features_dont_stack.md`: /065 changes ONE axis (universal SL multiplier). No engineered features added. No same-family features stacked. Single-axis EXPLORATION at single-seed mode is LEGITIMATE.

## Section 5 — Risk Mitigation

**UNCHANGED stack** (carry-forward from /060 anchor):

| Primitive | Status | Source |
|---|---|---|
| Vol scaling (RiskV2) | ENABLED | `feedback_v3_baseline_update_policy.md` carry-forward |
| ADX threshold (global 20.0) | ENABLED | iter-v3/050 closeout (per-symbol cleared) |
| Hurst regime gate | DISABLED | iter-v3/022 (closed) |
| Feature z-score OOD (\|z\|>2.0) | ENABLED | iter-v3/011 |
| Low-vol filter | ENABLED | carry-forward |
| Hit-rate gate | DISABLED | OOS-only; not active |
| BTC trend kill (±15%, 14d) | ENABLED | iter-v3/051 reverted to no-block; threshold=15% |
| Primitive 10 (direction-asymmetric kill switch) | DISABLED (block_long_for=(), block_short_for=()) | iter-v3/051 SYSTEM-LEVEL REVERT |
| Primitive 11 (per-symbol drawdown brake) | DISABLED | iter-v3/054 closeout |

**Labeling axis is orthogonal to risk gates**. No risk-primitive changes at /065 (single-axis discipline).

## Section 6 — Risk Management

**CHANGED (single substantive change)**: DEFAULT_ATR_MULTIPLIERS (2.0, 1.0) → (2.0, 1.5). V3_ATR_MULTIPLIERS_PER_SYMBOL remains empty `{}` per `feedback_v3_per_symbol_lifts_oos_breaks_is.md` UPDATED 2026-05-10 SYSTEM-LEVEL REVERT. All 3 symbols (BCH/LDO/TRX) consume DEFAULT.

Triple-barrier labeling timeout UNCHANGED: 21 candles (10080 minutes). Cooldown UNCHANGED: 4 candles post-trade. Fee UNCHANGED: 0.1% per leg.

**Translated to live trading**: live engine's actual stop-loss order distance per trade widens from 1.0×ATR_at_entry to 1.5×ATR_at_entry. TP stays at 2.0×ATR_at_entry. Per-trade risk-reward ratio shifts from 2:1 to 1.33:1 (less attractive per trade) but expected win rate lifts (~+7.8pp avg) which dominates Kelly fraction algebra under empirically observed conditions.

## Section 7 — Pre-registered Failure-Mode Prediction

Per Rule 3 of `feedback_v3_iter064_process_lessons.md`: single-feature additions at single-seed n_trials=35 weight NEGATIVE ≥25%. Non-feature axes at single-seed have similar local-optimum risk per Rule 5. The 30% NEGATIVE weighting reflects this.

| Mode | Description | Probability | Expected metrics |
|---|---|---:|---|
| **INERT** | Universal SL widening produces shifts within ±band; LightGBM compensates Optuna search around new labels | ~40% | IS Δ ∈ [-0.10, +0.10], OOS Δ ∈ [-0.20, +0.20] |
| **PROMISING** | Wider SL on LDO produces meaningful LDO lift; BCH/TRX preserved | ~15% | IS Δ ≥ +0.10 AND OOS Δ ≥ +0.20 |
| **SUSPICIOUS-OOS-DOMINANT** | Single-seed lottery: OOS spikes (especially LDO) while IS doesn't track | ~10% | IS Δ < +0.10, OOS Δ ≥ +0.20 |
| **NEGATIVE** | Wider SL accepts more bad trades (label noise from low-edge candidates); IS Sharpe shifts down; possible OOS regression on TRX | ~30% | IS Δ < -0.20 OR OOS Δ < -0.30 |
| **Methodology FAIL** | Test breakage, ATR-multiplier wiring inconsistency, CPCV degenerate | ~5% | Critic 13-check BLOCK |

**Why INERT is most likely (40%)**: LightGBM at depth-3-5 with n_trials=35 may converge to similar Sharpe via different hyperparameter regions in response to label-distribution shift. Mean reverter to /060 anchor in expectation.

**Why NEGATIVE is 30% (calibrated UP per Rule 3)**: Universal labeling changes at single-seed are sensitive — iter-v3/042 universal (1.5, 0.75) produced IS Sharpe -0.59. The OPPOSITE direction (widening) may also fail if wider SL admits more low-edge entries that bleed Sharpe. iter-v3/039 per-symbol LDO (2.0, 1.5) at multi-seed produced IS -0.08 (regression) — same multipliers we now apply universally have HISTORICAL EVIDENCE of IS regression at multi-seed; the EXPLORATION-single-seed evidence is the test of whether this regression is per-symbol-asymmetry artifact or genuine.

**Why PROMISING is only 15% (constrained UP-bound per Rule 3)**: per `feedback_v3_iter064_process_lessons.md` Rule 3 — PROMISING probability max 25% for feature-axis EXPLORATIONs; non-feature axes are similarly cautious. Wider SL is structurally non-edge-generating (it changes the label distribution, not the underlying signal); PROMISING outcome requires the ML model to discover a Sharpe pathway from cleaner LDO labels.

## Section 8 — LOCKED Acceptance / Path Criteria

Per `feedback_v3_cycle1_axis_pass_criteria.md`:

### Section 8.1 — PROMISING-AT-EXPLORATION (advances to /069 CONFIRMATION as candidate)

ALL of:
- **A.1** IS Sharpe shift ≥ +0.10 vs /060 (IS ≥ +0.9325)
- **A.2** OOS Sharpe shift ≥ +0.20 vs /060 (OOS ≥ +0.3403)
- **A.3** frac_positive_paths ≥ 0.50
- **A.4** No methodology FAIL (Critic 13 checks + §11 anti-pattern scan)
- **B.5** BCH IS share ≥ 80% (one-sided per Critic /060 Rec #1)
- **C.6** IS trade count ∈ [100, 250]
- **C.7** OOS trade count ∈ [60, 130]
- **D.8-D.13** Per-symbol wpnl Δ bands all within range
- **E.14** All v3 feature + ATR tests pass
- **E.15** ensemble_summary.json shows mode=exploration, size=3
- **E.16** EDA-implementation parity gate PASS (DEFAULT_ATR_MULTIPLIERS == (2.0, 1.5))

### Section 8.2 — INERT-AT-EXPLORATION

- IS Δ within [-0.10, +0.10] OR OOS Δ within [-0.20, +0.20] (noise-band)
- AND no methodology FAIL
- Axis CLOSED for current cycle; not re-evaluated.

### Section 8.3 — SUSPICIOUS-OOS-DOMINANT

- IS Δ < +0.10 (i.e., INSIDE noise band or NEGATIVE)
- AND OOS Δ ≥ +0.20
- Axis CLOSED-PENDING-CONFIRMATION; does NOT advance to /069 as PROMISING.

### Section 8.4 — NEGATIVE (disjunctive OR per `feedback_v3_iter064_process_lessons.md` Rule 4)

- IS Δ < -0.20 **OR** OOS Δ < -0.30 (either gate FAIL)
- AND no methodology FAIL
- Axis CLOSED. Universal SL=1.5 placed on PARKED list with rationale.

### Section 8.5 — NEGATIVE-SUSPICIOUS-OOS-NEGATIVE (rare)

- IS Δ < -0.20 AND OOS Δ < -0.20
- Axis CLOSED. Strong evidence against universal SL widening.

### Section 8.6 — Methodology FAIL

- Any Critic 13-check BLOCK fires
- Iteration is INVALID; not classifiable as PROMISING/INERT/NEGATIVE.

## Section 9 — Library Stack + Reproducibility

**UNCHANGED**:
- Python 3.13, uv environment, LightGBM (`lightgbm` package), pandas, pyarrow, statsmodels.
- ATR computation at `src/crypto_trade/features_v3/regime_v3.py:135` (`natr_21_raw` column; past-only Wilder 21-period; no change to formula).
- Label code path: `src/crypto_trade/strategies/ml/labeling.py::label_trades()` consumes `tp_pct` and `sl_pct` kwargs (forwarded from `LightGbmStrategy.atr_tp_multiplier` and `atr_sl_multiplier` per `lgbm.py:357`).
- `run_baseline_v3.py:1338` calls `atr_multipliers_for_symbol(symbol)` which returns `DEFAULT_ATR_MULTIPLIERS` for all 3 symbols (empty per-symbol dict).
- ENSEMBLE_SEEDS[0:3] = (191664963, 1662057957, 1405681631) — outer=42 lineage subset for EXPLORATION mode.

**Reproducibility stamp**:
- EDA SHA: `662659c` (`analysis/iteration_v3-065/labeling_parameter_eda.py`)
- Setup commit SHA: (LOCKED at setup commit — backfilled into Section 10 post-LOCK)
- ITERATION_LABEL: `"v3-065"`
- DEFAULT_ATR_MULTIPLIERS at runtime: (2.0, 1.5)
- V3_ATR_MULTIPLIERS_PER_SYMBOL: {} (empty — universal change applies to all)
- Parquet data: `data/features_v3/{BCHUSDT,LDOUSDT,TRXUSDT}_8h_features.parquet` (no regen needed)

### Integration test (per `feedback_v3_methodology_axis_integration_test.md`)

The DEFAULT_ATR_MULTIPLIERS edit is consumed by:
1. `tests/features_v3/test_atr_multipliers_for_symbol.py::test_default_value` — assertion `(2.0, 1.5)`
2. `tests/features_v3/test_features_for_symbol.py::test_default_atr_multipliers` — assertion `(2.0, 1.5)`
3. `run_baseline_v3.py::_verify_feature_columns()` runtime assertion `(2.0, 1.5)`
4. `_build_v3_model()` per-symbol call returns `(2.0, 1.5)` for all 3 symbols → propagates to LightGbmStrategy constructor → label_trades() forward scan

A smoke test consists of running `uv run pytest tests/features_v3/ -k atr -v` and confirming all atr-multiplier tests PASS with the new (2.0, 1.5) values.

## Section 10 — QR Audit Trail

**Why this axis (universal SL widening, Path D)**:

1. **Critic /064 Rec #4 binding directive**: NON-FEATURE axis pivot mandated after /060 14-feature anchor classified as LOCAL OPTIMUM at single-seed n_trials=35 (per Rule 5 of `feedback_v3_iter064_process_lessons.md`). Feature-axis EXPLORATIONs at this budget cannot productively escape.

2. **QR (orchestrator) selection of UNIVERSAL LABELING per `feedback_v3_per_symbol_lifts_oos_breaks_is.md`**: SYSTEM-LEVEL CONFIRMED across 2 CONFIRMATIONs (iter-v3/039 + iter-v3/050) that per-symbol customizations break IS aggregate at multi-seed. Universal changes preserve IS aggregate by construction.

3. **QR EDA SHA `662659c`** produced 6 tables that quantitatively support Path D over Paths A/B/C/E:
   - **T0**: anchor-value declaration (per Critic /064 Rec #1 anchor correctness gate).
   - **T1**: LDO has structural label noise at default (30.8% TP hit, 68.7% SL hit, 0.7648 balance, 0.4486 TP/SL ratio).
   - **T2**: Path D LDO TP hit rate 39.4% (+8.6pp from default) — largest LDO TP lift of any Path.
   - **T3**: LDO's avg-bars-to-SL (2.90) is 0.3 bars FASTER than avg-bars-to-TP (3.19) — intra-bar noise hits SL premature.
   - **T4**: Path D avg long_tp_hit_rate (0.4440) is the HIGHEST of any Path; avg balance (0.8240) is preserved.
   - **T5**: Path D directly addresses LDO's premature-SL mechanism via universal 50% SL widening.

4. **Path D selection rationale (quantitative)**:
   - Highest LDO TP-hit-rate (39.4%) and lowest LDO SL-hit-rate (59.0%) of any Path
   - Universal — no per-symbol asymmetry per `feedback_v3_per_symbol_lifts_oos_breaks_is.md`
   - Preserves BCH balance (0.9524 vs default 0.9697) and lifts TRX balance modestly (0.6823 vs default 0.6673)
   - Direct mechanism: 50% wider SL absorbs LDO intra-bar noise that hits SL before TP
   - Anti-snooping note: universal (2.0, 1.5) has NEVER been tested; iter-v3/045's per-symbol LDO (2.0, 1.5) at single-seed was PROMISING and at multi-seed iter-v3/050 was NO-MERGE (IS regression dominated by per-symbol asymmetry which universal does not have)

5. **Methodology compliance**:
   - `feedback_v3_axis_selection_quant_discipline.md`: EDA committed BEFORE brief (SHA `662659c` precedes setup commit).
   - `feedback_v3_axis_saturation_predictor.md`: Section 4.3 behavioral-effect predictor present with quantitative trade-count band.
   - `feedback_v3_per_symbol_target_axis_falsifier.md`: Per-symbol wpnl Δ bands pre-registered for all 3 symbols (Gates D.8-D.13).
   - `feedback_v3_per_symbol_lifts_oos_breaks_is.md`: Universal change (V3_ATR_MULTIPLIERS_PER_SYMBOL remains empty). No per-symbol asymmetry.
   - `feedback_v3_cycle1_axis_pass_criteria.md`: PASS thresholds (IS Δ ≥ +0.10 AND OOS Δ ≥ +0.20 vs /060) explicit.
   - `feedback_v3_engineered_features_dont_stack.md`: single-axis EXPLORATION (ONE substantive change — universal SL multiplier).
   - `feedback_v3_dsr_mode_artifact.md`: DSR_relative INFORMATIONAL ONLY at /065 EXPLORATION mode.
   - `feedback_v3_iter064_process_lessons.md` Rule 1 (anchor-value correctness gate): T0 references /060 anchor values with bit-exact `comparison.csv:LINE` refs.
   - `feedback_v3_iter064_process_lessons.md` Rule 3 (probability calibration): Section 7 NEGATIVE=30% (≥25% required for non-feature axes at single-seed).
   - `feedback_v3_iter064_process_lessons.md` Rule 4 (Section 8 disjunctive OR): Section 8.4 NEGATIVE LOCKED as disjunctive OR.

6. **EDA-implementation parity (per Critic /063 Rec #2)**: V3_FEATURE_COLUMNS_TOP_N UNCHANGED (14 features). DEFAULT_ATR_MULTIPLIERS edit is the ONE change. Phase 5.5 gate asserts DEFAULT_ATR_MULTIPLIERS == (2.0, 1.5) at runtime.

7. **Cannot be retroactively renegotiated**. Established at brief LOCK (setup commit).

---

**Setup commit SHA**: (backfilled at Phase 5.5 by orchestrator)

**Reading order for Engineer (Phase 6)**:
1. Verify branch `iteration-v3/065`; pull SHA `662659c` (EDA).
2. Apply Sub-fixes 1-4: `DEFAULT_ATR_MULTIPLIERS = (2.0, 1.5)`, `ITERATION_LABEL = "v3-065"`, test assertion updates, runner runtime assertion update.
3. Run `uv run pytest tests/features_v3/ -k atr -v` to confirm test PASS.
4. Run `uv run python run_baseline_v3.py --clean-oof --exploration --n-trials 35` (Phase 6 backtest).
5. Wall-clock target ~1.1h; HARD CAP 2h per `feedback_v3_cadence_discipline.md`.
6. Engineering report covers Section 8 LOCKED criteria evaluation (PASS/FAIL on each gate A.1–E.16) for Critic Phase 7.5.
