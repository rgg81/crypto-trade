# Iteration v3-052 — Research Brief (LDO removal investigation + DROP fracdiff_d05_close)

**Type**: EXPLORATION (Cycle 4 #2 of 10)
**Track**: v3 (rigor arm) — fifty-second iteration
**Branch**: `iteration-v3/052` (off iter-v3/051 head at SHA `87f3c93`)
**Date**: 2026-05-11
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

Sacred constants UNCHANGED. The QR sees iter-v3/052 OOS metrics for the FIRST time in Phase 7.

---

## Section 0.5 — Iteration Type Declaration

```
TYPE: EXPLORATION
Cycle: 4 — #2 of 10 (second EXPLORATION post-iter-v3/050 NO-MERGE CONFIRMATION)
Wall-clock budget: <= 2h hard cap (EXPLORATION spec)
Spec: uv run python run_baseline_v3.py --seeds 1 --n-trials 35 --clean-oof
  - ENSEMBLE_SIZE=5 (auto; inner ensemble)
  - n_trials=35 (default per `feedback_v3_exploration_n_trials_35.md`)
  - colsample_bytree Optuna-tunable (NOT hardcoded 1.0)
  - outer_seeds=1 (EXPLORATION-spec)
  - --clean-oof (use guardrail from SHA `6a216b5` to prevent OOF parquet contamination)

Carry-forward state (UNCHANGED from iter-v3/051 head):
  - V3_FEATURE_COLUMNS_TOP_N at /051 HEAD = 15 features (incl. fracdiff_d05_close)
  - V3_MODELS at /051 HEAD = (BCHUSDT, LDOUSDT, TRXUSDT) — 3 symbols
  - V3_ATR_MULTIPLIERS_PER_SYMBOL = {} (empty per /051 system-level REVERT)
  - block_long_for = () (empty per /051 system-level REVERT)
  - regime_momentum_signed_5d PRESERVED (iter-v3/028 edge ingredient)
  - DEFAULT_ATR_MULTIPLIERS = (2.0, 1.0)
  - adx_threshold_per_symbol = {} (empty)
  - All other risk gates UNCHANGED (BTC trend, OOD, ADX 20.0, hit-rate disabled, etc.)
  - REQUIRED_GAP at /051 HEAD = 66 = (21+1)×3

TWO-VARIABLE axis bundle for /052 (orchestrator mandate per Critic FINAL `32cc46f` recs #1 + #2):
  AXIS A (PRIMARY): DROP LDOUSDT from V3_MODELS — universe contraction 3 → 2 symbols
    Rationale: investigate LDO structural drag pattern observed at /047/049/050/051
                (OOS weighted_pnl -17.44 to -22.05 frozen-baseline; OOS WR 21-33%)
  AXIS B (PARSIMONY): DROP fracdiff_d05_close from V3_FEATURE_COLUMNS_TOP_N (15 → 14)
    Rationale: PARKED per /051 closeout — feature LEARNED (rank 11-12/15) but no IS lift;
                fracdiff_d05_close retest condition (per-symbol scoping) deferred; clean
                revert to 14-feature stack identical to /028 baseline parsimony.

Setup commit changes (locked in §3):
  - run_baseline_v3.py:V3_MODELS = (BCHUSDT, TRXUSDT) — 2 symbols (DROP LDOUSDT)
  - src/crypto_trade/strategies/ml/validation_v3.py:REQUIRED_GAP = 44 = (21+1)*2 (REVERT from 66)
  - src/crypto_trade/features_v3/__init__.py:V3_FEATURE_COLUMNS_TOP_N = 14 (DROP fracdiff_d05_close)
  - run_baseline_v3.py:_verify_feature_columns + _verify_v3_models updated
  - run_baseline_v3.py:ITERATION_LABEL = "v3-052"
  - compute_fracdiff_d05_close + 5 adversarial tests RETAINED as dead-code (zero revert cost)

Predicted classification (locked in §7):
  - PATH A (PROMISING-clean): 5% probability
  - PATH B (PROMISING-INERT): 5%
  - PATH C-clean (NEGATIVE-clean): 25%
  - PATH C-suspicious (NEGATIVE-SUSPICIOUS-OOS): 50% — most likely
  - PATH D (EXPLORATION-NULL-RESULT, new per Critic FINAL `32cc46f` rec #3): 15%
```

**Context**: iter-v3/051 EXPLORATION-NULL-RESULT closeout per Critic FINAL `32cc46f`. fracdiff_d05_close at universal scope was LEARNED (ranks 11-12/15) but produced NO IS lift; OOS lift +0.08 within single-seed=42 lottery noise. The /051 closeout identified LDO removal investigation as the cycle 4 #2 HIGH-priority axis based on:

1. LDO OOS weighted_pnl = -17.44 at /051 FULL REVERT to /028 architecture
2. LDO OOS WR = 23.1% (13 trades over 14 months)
3. LDO IS PnL share = -14.96% **(per_symbol.csv net_pnl_pct basis — see §2 critical correction)**
4. Frozen-baseline pattern at single-seed=42 across /047/049/050 (-19.13 OOS bit-identical)

iter-v3/052 = cycle 4 #2 of 10 EXPLORATIONs (per `feedback_v3_strict_10_to_1_cadence.md`). iter-v3/061 = cycle 4 CONFIRMATION (SEPARATE single-seed iter-v3/060 first; do NOT collapse 10th EXPLORATION).

**Critical brief-level NOTE** (per Section 10 audit trail): the QR EDA committed at SHA `0a10581` (see `analysis/iteration_v3-052/`) reveals the orchestrator's premise contains a metric-reading error (net_pnl_pct vs weighted_pnl). The EDA inverts the IS-axis direction: LDO is an IS CONTRIBUTOR at /051 (+11.155 wpnl, +36.78% bundle share), not a drag. LDO removal would BREAK IS Sharpe by Δ -0.16 (FAILS BOTH-must-improve gate). Section 10 documents the QR's recommendation to PIVOT to a different cycle 4 #2 axis (regime_momentum_signed_3d UNIVERSAL); however, the orchestrator brief LOCKED the LDO-removal axis. The QR proceeds with the mandated axis per `feedback_v3_axis_selection_quant_discipline.md` (orchestrator may override QR EDA-driven recommendations with locked mandates; QR documents disagreement in audit trail). This iteration tests: can Optuna re-tune on a 2-symbol universe (BCH+TRX) recover the IS Sharpe deficit predicted by the trade-roster counterfactual?

---

## Section 1 — Hypothesis

Dropping LDOUSDT from V3_MODELS (3 → 2 symbols: BCHUSDT, TRXUSDT) — alongside dropping fracdiff_d05_close from V3_FEATURE_COLUMNS_TOP_N (15 → 14; parsimony revert to /028 14-feature stack) — investigates whether the LDO structural drag pattern observed at single-seed=42 across iter-v3/047/049/050/051 (frozen-baseline OOS weighted_pnl -17.44 to -22.05) can be removed to LIFT bundle OOS Sharpe vs iter-v3/028 baseline reference +0.5053. 

**Predicted single-seed result (per QR EDA at SHA `0a10581`, axis 2 — 2-sym counterfactual from /051 trade roster):**
- Bundle IS Sharpe: approximately +0.30 ± 0.10 (Δ -0.10 to -0.25 vs /028 anchor +0.5101) — DROPS due to removal of LDO IS contribution (+11.155 weighted_pnl at /051 IS; +36.78% share)
- Bundle OOS Sharpe: approximately +1.60 ± 0.30 (Δ +1.00 to +1.30 vs /028 anchor +0.5053) — LIFTS due to removal of LDO OOS drag (-17.44 weighted_pnl at /051 OOS)
- IS-OOS daily Sharpe ratio: approximately 3.0 ± 1.0 (likely OUT-OF-BAND of [0.5, 2.0]) — diagnostic of PATH C-suspicious anti-pattern
- IS trade count: approximately 130-160 (Δ -15-25% vs /051's 178)
- OOS trade count: approximately 80-95 (Δ -10-15% vs /051's 96; close to /028 baseline's 95)
- BOTH-must-improve gate: predicted FAIL on IS axis per `feedback_v3_strict_both_is_oos_baseline.md`

This is the SAME structural pattern that triggered system-level REVERT at /051 (per-symbol customizations producing OOS lift + IS regression = lottery, not edge), but applied at the **symbol composition level** rather than the model-customization level. The brief proceeds with the locked mandate to test whether Optuna re-tune on a 2-symbol universe materially changes this prediction (probability low: 5-15%).

---

## Section 2 — IS-Only Numerical Evidence

**All evidence derived from committed analysis script `analysis/iteration_v3-052/ldo_removal_eda.py` (SHA `0a10581`) reading from iter-v3/051 reports (in_sample + out_of_sample trade rosters + per_symbol.csv).**

### 2.1 — LDO weighted_pnl contribution at iter-v3/051 baseline (axis 1)

The orchestrator brief premise "LDO IS PnL share -14.96% at /051" reads `net_pnl_pct` aggregation from `per_symbol.csv`. This metric SUMS per-trade raw % returns and IGNORES `weight_factor` (which encodes vol scaling and BTC-kill drops). The actual contribution to bundle Sharpe is `weighted_pnl` (weight_factor × pnl_pct).

| Window | LDO trades (wf>0) | LDO weighted_pnl | LDO PnL share (wpnl) | LDO WR |
|---|---:|---:|---:|---:|
| **IS** | 9 (of 11 raw) | **+11.155** | **+36.78%** | 33.33% |
| **OOS** | 13 (of 13 raw) | **−17.44** | **−100.08%** | 23.08% |

The 2 BTC-killed IS LDO trades (weight_factor=0) contributed 0 to bundle wpnl (correctly so — they were blocked by the BTC trend gate). The 9 active IS LDO trades produced **+11.155 wpnl total** with 3 profitable take-profit exits dominating: (+12.35 wpnl Dec 2024 LONG TP), (+9.38 wpnl Feb 2025 SHORT TP), (+15.36 wpnl Feb 2025 LONG TP). LDO is an IS CONTRIBUTOR at /051 — not a drag.

The 13 active OOS LDO trades produced **−17.44 wpnl total** with 10 stop-losses against 3 take-profits. The OOS regression is direction-asymmetric: 11 of 13 OOS trades are SHORTs (see §2.5).

### 2.2 — 2-sym BCH+TRX counterfactual from /051 trade roster (axis 2 — THE CRITICAL TABLE)

Counterfactual: drop all LDO trades from the /051 trade roster and re-compute aggregate IS+OOS monthly Sharpe (mirrors `multi_axis_eda.py` from /051 EDA; methodology proven).

| Scenario | IS trades | IS Sharpe | OOS trades | OOS Sharpe | IS-OOS daily ratio |
|---|---:|---:|---:|---:|---:|
| 3-sym /051 actual (BCH+LDO+TRX) | 147 | **+0.4571** | 95 | **+0.5890** | 1.06 (in-band) |
| 2-sym counterfactual (drop LDO) | 138 | **+0.2960** | 82 | **+1.6030** | **3.58 (OUT-OF-BAND)** |
| **Δ (no_LDO − with_LDO)** | −9 | **−0.1611** | −13 | **+1.0139** | — |

(Sharpe values reproduced from /051 trade roster; minor offset vs official /051 +0.4506 IS / +0.5891 OOS due to day-aggregation precision; counterfactual deltas robust.)

**Critical reading of this table**:
- LDO removal DROPS IS Sharpe by Δ **−0.1611** (FAILS BOTH-must-improve gate per `feedback_v3_strict_both_is_oos_baseline.md`)
- LDO removal LIFTS OOS Sharpe by Δ **+1.0139** (would single-handedly clear OOS ≥ +1.0 gate)
- LDO removal pushes IS-OOS daily ratio from 1.06 (in-band) to **3.58 (out-of-band)** — PATH C-suspicious anti-pattern at the symbol composition level

This is the structural analog of the iter-v3/026/027 anti-pattern (engineered features that lift OOS but regress IS at high IS-OOS ratio = Optuna-overfit / lottery, not edge). Per `feedback_v3_engineered_features_dont_stack.md` and `feedback_v3_per_symbol_lifts_oos_breaks_is.md`, this pattern was CLOSED at the system level for per-symbol customizations after 2-cycle confirmation. LDO removal would trigger it again at the universe composition level.

**Caveat (lower bound)**: this counterfactual subtracts LDO trades from the /051 roster without Optuna re-tune. The actual /052 backtest at 2-symbol universe will re-tune Optuna and SHIFT trade rosters (not just drop LDO trades). The counterfactual represents the bound where Optuna doesn't materially recover the IS shortfall. If Optuna re-tune adds materially profitable BCH+TRX trades on the 2-sym universe, the IS deficit could partially recover (rough estimate: +0.05 to +0.10 IS lift from Optuna re-tune; net IS Δ still likely negative).

### 2.3 — /050 EDA rejection vs /051 NEW evidence supersession (axis 3)

The iter-v3/051 EDA at `analysis/iteration_v3-051/axis_a_ldo_attribution.csv` rejected LDO removal on the basis of /050 trade roster counterfactual IS Δ +0.0075 (near-zero; not improving). The orchestrator brief premise stated that /051 supersedes /050 in the direction "LDO is drag at IS too." 

**Inspecting the /051 evidence quantitatively**:

| Config | LDO IS trades | LDO IS wpnl | LDO IS share (wpnl) | IS Sharpe Δ if remove |
|---|---:|---:|---:|---:|
| /050 EDA rejection basis (4-sym + per-sym ATR + primitive 10) | 13 | +0.85 | +1.55% | **+0.0075** (essentially zero) |
| /051 NEW evidence (3-sym /028 architecture; FULL REVERT) | 9 | **+11.155** | **+36.78%** | **−0.1611** |

**The /051 NEW evidence does NOT supersede /050 in the direction the orchestrator premise assumed.** Both /050 and /051 reject LDO removal at the IS axis — and at /051, the rejection is STRONGER (more material IS contribution to remove). The supersession is in the DIRECTION of LDO IS contribution magnitude:
- /050: LDO IS contribution is essentially zero (+0.85 wpnl); removing LDO is a wash on IS
- /051: LDO IS contribution is +11.155 wpnl (+36.78% bundle share); removing LDO BREAKS IS

The orchestrator's "LDO IS PnL share -14.96%" reading sourced `net_pnl_pct` (raw % sum). The wpnl-share metric (which drives Sharpe) is +36.78%. Brief premise mathematically inconsistent with bundle Sharpe formula.

### 2.4 — Cross-iteration LDO pattern (axis 4)

| Iteration | Config | LDO IS wpnl | LDO OOS wpnl | LDO IS WR | LDO OOS WR |
|---|---|---:|---:|---:|---:|
| iter-v3/028 | 3-sym /028 baseline; multi-seed mean | +5.02 | **−22.05** | 40.00% | 21.43% |
| iter-v3/045 | 4-sym + per-sym ATR; single-seed PROMISING anchor | **+43.90** | +9.34 | 58.82% | 53.85% |
| iter-v3/047 | 4-sym + per-sym ATR + primitive 10 | +0.85 | −19.13 | 46.15% | 33.33% |
| iter-v3/049 | 4-sym + per-sym ATR + primitive 10 + ADX retune | +0.85 | −19.13 | 46.15% | 33.33% |
| iter-v3/050 | CONFIRMATION; same head as /049 | +0.85 | −19.13 | 46.15% | 33.33% |
| **iter-v3/051** | **3-sym FULL REVERT + fracdiff** | **+11.155** | **−17.44** | **33.33%** | **23.08%** |

LDO IS wpnl is **POSITIVE at every iteration** since /028 baseline (+5.02 multi-seed mean; +43.90 /045 single-seed lottery; +0.85 /047-/050; +11.155 at /051). LDO is structurally an IS contributor whose magnitude varies with model configuration.

LDO OOS wpnl is consistently negative at single-seed=42 across /047/049/050 frozen baselines (-19.13 bit-identical) and at /028 multi-seed mean (-22.05) and at /051 (-17.44). The OOS regression is real, BUT the IS contribution is also real — they exist in PATH-C-suspicious tension, not as a clean "always-bad symbol" signal.

### 2.5 — LDO directional asymmetry at /051 (axis 6)

LDO OOS losses are concentrated in the SHORT direction:

| Window | Direction | n | wins | WR | wpnl total | avg wpnl | SLs | TPs |
|---|---|---:|---:|---:|---:|---:|---:|---:|
| IS | LONG | 6 | 2 | 33.3% | +5.59 | +0.93 | 4 | 2 |
| IS | SHORT | 3 | 1 | 33.3% | +5.57 | +1.86 | 2 | 1 |
| OOS | **LONG** | **2** | **1** | **50.0%** | **+4.99** | **+2.49** | 1 | 1 |
| OOS | **SHORT** | **11** | **2** | **18.2%** | **−22.42** | **−2.04** | **9** | 2 |

LDO went from $1.04 → $0.41 in OOS (-60% over 14 months). The model shorted 11 times — directionally correct — but 9 of 11 SHORTs got stop-lossed during local rallies before the down-leg resumed.

**Implication for /052 axis**: a direction-asymmetric LDO SHORT block (analog of primitive 10 BCH LONG block — `block_short_for=("LDOUSDT",)`) would surgically remove the -22.42 OOS drag while preserving the +4.99 LONG contribution. However, this is per-symbol customization — REJECTED at system level per `feedback_v3_per_symbol_lifts_oos_breaks_is.md`. The orchestrator brief did not mandate this axis (and per system-level rule it is rejected); the iter-v3/052 axis as locked is universe contraction (drop LDO entirely).

### 2.6 — LDO data extent pre-flight (axis 5)

| Symbol | candles | first_open | last_open | IS candles | IS months | deficit_vs_BCH |
|---|---:|---|---|---:|---:|---|
| BCHUSDT | 6965 | 2020-01-01 | 2026-05-10 | 5727 | 62.8 | n/a |
| LDOUSDT | 3979 | 2022-09-22 | 2026-05-10 | 2741 | **30.1** | **42.9% less** |
| TRXUSDT | 6907 | 2020-01-15 | 2026-05-10 | 5669 | 62.2 | 0.8% less |

LDO has 42.9% less training data than BCH/TRX. This is a structural reason LDO could underperform in v3 (fewer training-window cells produce noisier per-cell models). But the IS contribution at /051 (+11.155 wpnl over 9 trades concentrated Oct 2024 - Feb 2025) shows the limited training data is sufficient to find IS signal — the OOS regression is a different problem (signal flip on SHORT direction in 2025-Q2/Q3/Q4 declining-LDO regime).

### 2.7 — LDO monthly PnL temporal pattern (axis 7)

| month | window | n_trades | wpnl | wins | wr_pct |
|---|---|---:|---:|---:|---:|
| 2024-10 | IS | 2 | -3.81 | 0 | 0.0% |
| 2024-12 | IS | 2 | +6.06 | 1 | 50.0% |
| 2025-02 | IS | 5 | +8.91 | 2 | 40.0% |
| 2025-05 | OOS | 1 | +9.74 | 1 | 100.0% |
| 2025-06 | OOS | 1 | +5.31 | 1 | 100.0% |
| 2025-07 | OOS | 3 | -12.86 | 0 | 0.0% |
| 2025-08 | OOS | 3 | -15.28 | 0 | 0.0% |
| 2025-10 | OOS | 3 | -6.19 | 0 | 0.0% |
| 2026-04 | OOS | 2 | +1.83 | 1 | 50.0% |

The OOS regression is concentrated in 2025-Q3 (July-August: -28.14 wpnl across 6 trades, 0 wins). The first 2 OOS LDO trades (May-June 2025) were profitable (+15.05 wpnl). The model's failure mode is regime-specific: 2025-Q3 declining-LDO retraces.

### 2.8 — Conclusion of §2

The /051 trade-roster evidence does NOT support the brief premise that LDO is "an IS drag at /051." LDO is an IS contributor (+11.155 wpnl, +36.78% share) and an OOS drag (-17.44 wpnl, -100% share). Removing LDO from V3_MODELS at /052 BREAKS the BOTH-must-improve gate at the IS axis (Δ -0.16 from counterfactual) and triggers PATH C-suspicious at the IS-OOS daily ratio falsifier (3.58 out-of-band).

The brief proceeds with the locked LDO-removal mandate. Pre-registration in §7-§8 sets PATH C-suspicious as most likely outcome (50%) and PATH C-clean as second-most-likely (25%); PATH A and PATH B are unlikely (5% each). Section 10 documents QR disagreement.

---

## Section 3 — Proposed Changes

### 3.1 — Setup commit (two-variable axis: LDO drop + fracdiff drop)

1. **`run_baseline_v3.py:V3_MODELS`** — DROP LDOUSDT, RETAIN BCHUSDT, TRXUSDT
   ```python
   V3_MODELS: tuple[tuple[str, str], ...] = (
       ("BCHUSDT", "8h"),
       ("TRXUSDT", "8h"),
       # iter-v3/052: LDOUSDT REMOVED — universe contraction 3 → 2 symbols.
       # Rationale: investigate LDO structural drag pattern observed at /047/049/050/051
       # (OOS weighted_pnl -17.44 to -22.05 frozen baseline; OOS WR 21-33%).
   )
   ```
   Per `feedback_v3_axis_selection_quant_discipline.md`, V3_MODELS change requires
   QR EDA-driven justification — committed at SHA `0a10581` (LDO removal EDA, 7 axes,
   counterfactual + cross-iteration + directional analysis).

2. **`src/crypto_trade/strategies/ml/validation_v3.py:REQUIRED_GAP`** — RECOMPUTE
   ```python
   REQUIRED_GAP = 44  # = (timeout_candles=21+1) × n_symbols=2 (iter-v3/052 2-sym REVERT)
   ```
   Was 66 = (21+1)×3 at /051; reduced to 44 = (21+1)×2 due to universe contraction.

3. **`src/crypto_trade/features_v3/__init__.py:V3_FEATURE_COLUMNS_TOP_N`** — DROP fracdiff_d05_close
   ```python
   V3_FEATURE_COLUMNS_TOP_N: tuple[str, ...] = (
       "max_dd_window_50",
       "ema_spread_atr_20",
       "ret_kurt_50",
       "ret_skew_200",
       "range_realized_vol_50",
       "hurst_diff_100_50",
       "ret_kurt_200",
       "hurst_100",
       "btc_ret_14d",
       "ret_skew_50",
       "vwap_dev_20",
       "ret_autocorr_lag1_50",
       "sym_vs_btc_ret_7d",
       "regime_momentum_signed_5d",
       # iter-v3/052: fracdiff_d05_close DROPPED per /051 closeout (15 → 14 revert).
       # PATH B (PROMISING-INERT) NOT triggered at /051 (feature LEARNED ranks 11-12);
       # PATH A (PROMISING-clean) NOT triggered (IS Δ -0.06 sits in no-man's-land);
       # Critic FINAL `32cc46f` rec #2 = PARKED (not CLOSED). compute_fracdiff_d05_close
       # retained as dead code in engineered_v3.py:264-327 at zero revert cost.
       # 5 adversarial tests in tests/features_v3/test_fracdiff_d05_universal.py
       # RETAINED as dead-code coverage. Retest conditions: per-symbol scoping;
       # n_trials=50+ at single-seed; multi-seed CONFIRMATION as bundle ingredient.
   )
   """Top-14 feature subset (as of iter-v3/052): fracdiff_d05_close DROPPED (15 → 14)
   per /051 EXPLORATION-NULL-RESULT closeout PARKED action. Returns to /028 baseline
   14-feature stack."""
   ```

4. **`run_baseline_v3.py:_verify_feature_columns`** — UPDATE assertions
   - `n != 14` (was `n != 15` at /051)
   - REMOVE assertion: `fracdiff_d05_close` MUST be present (was added at /051)
   - ADD assertion: `fracdiff_d05_close` MUST NOT be in V3_FEATURE_COLUMNS_TOP_N
   - Keep all other assertions (regime_momentum_signed_5d preservation, sym_vs_btc_ret_7d,
     ret_skew_50 preservation)

5. **`run_baseline_v3.py:_verify_v3_models`** — UPDATE assertion
   - Assert V3_MODELS has exactly 2 elements
   - Assert LDOUSDT is NOT in V3_MODELS
   - Update audit print to confirm 2-symbol universe

6. **`run_baseline_v3.py:_verify_required_gap`** — UPDATE assertion
   - REQUIRED_GAP must equal 44 (formula: (timeout+1)×n_symbols = 22×2)

7. **`run_baseline_v3.py:ITERATION_LABEL`** = `"v3-052"`

8. **`run_baseline_v3.py`** — Update banner comment block describing iter-v3/052 axis

### 3.2 — Tests

- `tests/features_v3/test_v3_models.py` (if exists; otherwise create): assert V3_MODELS length=2; LDOUSDT not present; BCHUSDT + TRXUSDT present.
- `tests/features_v3/test_fracdiff_d05_universal.py` (5 adversarial tests from /051): RETAIN unchanged. They serve as dead-code regression coverage in case the feature is re-activated in future iterations.
- Add or update test `tests/features_v3/test_v3_iter052_drop_ldo_and_fracdiff.py`:
  - test_v3_models_excludes_ldousdt
  - test_v3_feature_columns_top_n_excludes_fracdiff_d05_close
  - test_v3_feature_columns_top_n_length_14
  - test_required_gap_equals_44_for_2_sym

### 3.3 — Carry-forward state (UNCHANGED from /051 head)

- regime_momentum_signed_5d PRESERVED in V3_FEATURE_COLUMNS_TOP_N (iter-v3/028 edge ingredient; rank 12-15/15 at /051 but mandate per `feedback_v3_engineered_features_proven.md`)
- V3_ATR_MULTIPLIERS_PER_SYMBOL = {} (empty per /051 REVERT)
- block_long_for = () (empty per /051 REVERT)
- DEFAULT_ATR_MULTIPLIERS = (2.0, 1.0)
- adx_threshold_per_symbol = {} (empty)
- BTC trend filter: lookback=42, threshold=15.0% (UNCHANGED)
- OOD z-score gate: zscore_threshold=2.0, 14-D space (DOWN from 15-D at /051; reflects fracdiff drop)
- ADX gate: threshold=20.0 global (UNCHANGED)
- Regime gate: DISABLED (CLOSED per /022)
- Per-symbol cap: DISABLED (CLOSED per /020)

### 3.4 — Setup commit checklist

- [ ] V3_MODELS = (BCHUSDT, TRXUSDT) — 2 elements
- [ ] V3_FEATURE_COLUMNS_TOP_N = 14 elements (no fracdiff_d05_close)
- [ ] REQUIRED_GAP = 44 in validation_v3.py
- [ ] ITERATION_LABEL = "v3-052"
- [ ] All 4 audit functions pass: `_verify_v3_models`, `_verify_feature_columns`, `_verify_required_gap`, `_verify_iteration_label`
- [ ] tests/features_v3/test_fracdiff_d05_universal.py UNCHANGED (5 tests PASS — dead-code coverage)
- [ ] tests/features_v3/test_v3_iter052_drop_ldo_and_fracdiff.py CREATED (4 new tests PASS)
- [ ] `uv run pytest tests/features_v3/` ALL PASS
- [ ] `uv run ruff check . && uv run ruff format .` ALL CLEAN
- [ ] `compute_fracdiff_d05_close` in engineered_v3.py:264-327 PRESERVED as dead code
- [ ] phase5p5_gate.md document PASS state (all 10 mandatory sections in this brief)

### 3.5 — Run command (LOCKED)

```bash
uv run python run_baseline_v3.py --seeds 1 --n-trials 35 --clean-oof
```

- EXPLORATION single-seed=42
- ENSEMBLE_SIZE=5 (auto inner ensemble)
- n_trials=35 (EXPLORATION default per `feedback_v3_exploration_n_trials_35.md`)
- 5 inner × 35 trials × **2 symbols = 350 total Optuna trials** (down from /051's 525 at 3-sym)
- `--clean-oof` guardrail RETAINED (SHA `6a216b5`)

### 3.6 — Estimated wall-clock

- Setup commit (V3_MODELS + REQUIRED_GAP + V3_FEATURE_COLUMNS_TOP_N + audits + 4 tests): 25-40 min
- Phase 5.5 gate: 5-10 min
- Backtest (2-sym + 14 features + n_trials=35 single-seed): 18-25 min (smaller than /051 due to universe contraction; 33% fewer total trials)
- Phase 6/7 reports + Phase 7.5 Critic: 30-40 min
- **TOTAL: ≤1.5h** (well within 2h EXPLORATION cap)

---

## Section 4 — Expected OOS Impact

### 4.1 — Quantitative predicted bands (single-seed n_trials=35 EXPLORATION-spec)

| Metric | iter-v3/028 baseline (multi-seed) | iter-v3/051 (1-seed) | **iter-v3/052 PREDICTED (1-seed)** | Δ vs /028 anchor |
|---|---:|---:|---:|---:|
| IS monthly Sharpe | +0.5101 | +0.4506 | **+0.30 ± 0.10** (band [+0.20, +0.40]) | **Δ −0.10 to −0.30** |
| OOS monthly Sharpe | +0.5053 | +0.5891 | **+1.60 ± 0.30** (band [+1.30, +1.90]) | **Δ +1.00 to +1.30** |
| IS-OOS daily Sharpe ratio | 0.99 | 1.15 | **3.0 ± 1.0** (band [2.0, 4.0]) | OUT-OF-BAND likely |
| IS Trades | 156 (mean) | 178 | **130-160** (Δ −15-25%) | −15-25% |
| OOS Trades | 95 (mean) | 96 | **80-95** (Δ −10-15%) | −10-15% |
| IS MaxDD | 41.43% | 37.37% | **35-45%** (BCH dominant) | comparable |
| OOS MaxDD | 23.53% | 32.75% | **20-30%** (LDO drag removed) | better |
| OOS Calmar | 0.92 | 0.53 | **2.0 ± 0.5** | much better |
| OOS Top concentration | 76.47% (TRX) | 67.65% (BCH) | **65-75% (BCH dominant)** | comparable |
| DSR | 0.0 (structural) | 0.0 (structural) | **0.0** (structural at n_trials=350) | structural |
| PBO | 0.1243 | 0.1168 | **0.10 ± 0.05** | comparable |
| PSR | 1.0 (saturation) | 1.0 | **1.0** | saturation |
| n_trials (Optuna total) | 1050 | 525 | **350** | EXPLORATION 2-sym |
| n_eff | 19 | 19 | **15-20** | within range |

### 4.2 — Behavioral-effect predictor (per `feedback_v3_axis_saturation_predictor.md`)

**Mandatory per `feedback_v3_axis_saturation_predictor.md`** — explicit prediction of how many IS trades will change:

- **IS trade count change**: predicted **−15-25%** (−27 to −44 trades, from 178 to 131-151).
  Mechanism: removing 9 IS LDO active trades (-9 trades absolute) + Optuna re-tune on 2-symbol universe potentially shifting BCH+TRX trade frequencies by ±3-5 trades each = total net change −15-30 trades.
  **Falsifier**: if observed IS trade count change < 5% (above 169), axis is saturated; the universe contraction has no behavioral effect on Optuna's BCH+TRX model selection — investigate.
- **OOS trade count change**: predicted **−10-15%** (−10 to −14 trades, from 96 to 82-86).
  Mechanism: removing 13 OOS LDO active trades (-13 trades absolute) + Optuna re-tune adjusting BCH+TRX trade frequencies by ±2-3 trades.
  **Falsifier**: if observed OOS trade count change < 5% (above 91), axis is saturated.
- **BCH IS attribution share**: predicted shift from +104% of /051 IS PnL to ~+130% of /052 IS PnL (BCH absolute IS wpnl ~24.60; new bundle total ~+19.17 = 24.60 − 5.43 TRX).
- **TRX IS attribution share**: predicted ~−28% of /052 IS PnL (TRX absolute IS wpnl in /051: −5.43 wpnl; this becomes -28% share of smaller bundle).
- **BCH+TRX OOS attribution**: BCH +23.59 / TRX +11.28 / total +34.87 OOS wpnl predicted (vs /051 OOS total +17.43).

### 4.3 — Most likely classification

Per §7 pre-registration and §2 counterfactual, **PATH C-suspicious (NEGATIVE-SUSPICIOUS-OOS) is most likely (~50%)** — the IS-OOS daily Sharpe ratio is predicted to exit the [0.5, 2.0] band on the high side (ratio ≈ 3.0-4.0 from observed counterfactual). Secondary path: PATH C-clean (NEGATIVE-clean, ~25%) — if Optuna re-tune compresses the IS deficit enough to keep IS Δ in (-0.10, -0.05) but the falsifier rule still fires from BOTH-must-improve gate. PATH D (NULL-RESULT, ~15%) — if Optuna materially recovers IS to within (-0.10, +0.05) range. PATH A (PROMISING-clean) and PATH B (PROMISING-INERT) are unlikely (~5% each).

### 4.4 — Falsifier band (axis-saturation)

| Metric | Predicted range | Falsifier trigger |
|---|---|---|
| IS trade count change | -15% to -25% | < 5% (axis saturated: universe contraction has no effect on trade-roster) |
| OOS trade count change | -10% to -15% | < 5% (same saturation diagnostic on OOS side) |
| BCH IS PnL share | +120% to +140% | < +100% (Optuna materially shifted BCH model, indicating universe-contraction effect on per-symbol optimization) |
| IS Sharpe Δ vs /028 anchor | -0.10 to -0.30 | > +0.05 (Optuna miracle — universe contraction recovers IS deficit; PATH A trigger) |
| OOS Sharpe Δ vs /028 anchor | +1.00 to +1.30 | < +0.30 (OOS lift much smaller than counterfactual predicts; investigate roster shift) |
| IS-OOS daily Sharpe ratio | 2.5 to 4.0 | in band [0.5, 2.0] (PATH A/B trigger — clean lift without OOS-only artifact) |

---

## Section 5 — Risk Mitigation

Per `feedback_v3_risk_mitigation_design.md` (R1-R5 framework adapted for v3 risk-gate architecture).

### 5.1 — R1 — Cool-downs

- 2-candle post-trade cooldown per (model, symbol) — UNCHANGED (engine-level seeded via `cooldown_<model>_<sym>` engine_state keys)
- R1 cooldowns rebuilt from DB on engine startup (via `_rebuild_risk_state()`)

### 5.2 — R2 — Drawdown-triggered position scaling

- Engine-level drawdown brake DISABLED in v3 (per `feedback_v3_concentration_is_signal.md`)
- Per-symbol drawdown brake DISABLED (per `feedback_v3_concentration_is_signal.md` rejecting iter-v3/020 per-symbol PnL cap)
- Vol scaling (RiskV2Wrapper) ACTIVE — per-trade weight_factor in [0.33, 1.0] band; primary risk scaling

### 5.3 — R3 — OOD detection

- **OOD z-score gate ACTIVE** at zscore_threshold=2.0 (UNCHANGED from /051)
- Dimensionality: **14-D feature space** (DOWN from 15-D at /051 due to fracdiff_d05_close drop)
- Mahalanobis distance computed on 14 features from V3_FEATURE_COLUMNS_TOP_N
- Cutoff = 95th percentile of training-window distances (per RiskV2 implementation)
- Embedded in per-symbol RiskV2Wrapper at predict time

### 5.4 — R4 — Vol kill-switch

- **BTC trend filter ACTIVE** at lookback=42, threshold=15.0% (UNCHANGED from /051)
- Mechanism: if |BTC 14-day return| > 15%, kill ALL trades (weight_factor=0)
- /051 observed: 32 OOS trades killed (~25% of candidates); similar % expected at /052

### 5.5 — R5 — Concentration caps

- Per-symbol PnL share caps DISABLED (CLOSED per `feedback_v3_concentration_is_signal.md` iter-v3/020 verdict)
- Top-symbol concentration gate INFORMATIONAL ONLY (≤ 30% aspirational, not enforced as kill switch)
- Expected /052 OOS top concentration: 65-75% (BCH dominant in 2-symbol universe) — well above 30% aspirational gate but consistent with /028 (76.47%) and /051 (67.65%)

### 5.6 — Risk gate stack (v3 7-primitive)

| Primitive | Parameter | iter-v3/052 state | Behavior |
|---|---|---|---|
| BTC trend kill | lookback=42, threshold=15% | ACTIVE | Kill all trades if |BTC 14d ret| > 15% |
| Vol scaling | weight_factor ∈ [0.33, 1.0] | ACTIVE | Per-trade scaling by vol estimate |
| ADX gate | threshold=20.0 global | ACTIVE | Filter low-trend regimes |
| Hurst regime | embedded in features | ACTIVE (informational) | hurst_100, hurst_diff_100_50 are features |
| z-score OOD | zscore_threshold=2.0, 14-D | ACTIVE | Reject OOD candles; 14-D after fracdiff drop |
| Low-vol filter | embedded | ACTIVE | Skip extremely low-vol candles |
| Hit-rate gate | DISABLED | OFF | Per `feedback_v3_strict_10_to_1_cadence.md` discipline |
| Primitive 10 — BCH LONG block | block_long_for=() | INFRASTRUCTURE-ONLY | Wired off per /051 REVERT; code path preserved |
| Per-symbol cap | enable_per_symbol_cap=False | DISABLED | Per /020 CLOSED-mechanism |
| Regime gate | enable_regime_gate=False | DISABLED | Per /022 PARTIALLY-EFFECTIVE-CLOSED |

### 5.7 — IS-calibrated thresholds + simulated effect

- BTC trend filter at 15%: calibrated at /050 EDA (32 OOS trades killed; consistent across /045-/051)
- Vol scaling: per-trade weight_factor in [0.33, 1.0]; calibrated at /028 multi-seed (no change since)
- OOD z-score 2.0: calibrated at /011 (tightened from default 2.5 to 2.0 to surface more OOD)

No risk-gate thresholds change at iter-v3/052. The axis under test is universe contraction + feature drop; risk-gate calibration is held constant.

---

## Section 6 — Risk Management Design (10-Primitive Gate Table)

(Same as §5.6 — repeated here for adversarial-review structure)

| # | Primitive | Mechanism | iter-v3/052 state | Audit |
|---|---|---|---|---|
| 1 | BTC trend kill switch | If |BTC 14d return| > 15%, weight_factor = 0 | ACTIVE | `_build_v3_model` BTC_TREND_CONFIG |
| 2 | Vol scaling (RiskV2Wrapper) | Per-trade scaling by symbol-vol estimate; bounded [0.33, 1.0] | ACTIVE | RiskV2Wrapper at strategy level |
| 3 | ADX gate | Filter low-trend regimes at threshold=20.0 | ACTIVE | RiskV2Config.adx_threshold=20.0 |
| 4 | Hurst regime | hurst_100, hurst_diff_100_50 features inform model | ACTIVE (informational) | features_v3 regime group |
| 5 | z-score OOD (Mahalanobis) | Reject OOD candles at 2.0 cutoff in 14-D feature space | ACTIVE | RiskV2Config.zscore_threshold=2.0 |
| 6 | Low-vol filter | Skip extremely low-vol candles | ACTIVE | RiskV2Wrapper embedded |
| 7 | Hit-rate gate | Per-symbol hit-rate feedback | DISABLED | Per `feedback_v3_strict_10_to_1_cadence.md` |
| 8 | Per-symbol cap | Per-symbol PnL share cap (e.g., 0.40) | DISABLED | Per `feedback_v3_concentration_is_signal.md` /020 |
| 9 | Regime gate | TRX/2022-Q4 regime block | DISABLED | Per `feedback_v3_promising_mechanical_subtype.md` /022 |
| 10 | Direction-asymmetric kill switch | block_long_for=("BCHUSDT",) or symmetric block_short_for | INFRASTRUCTURE-ONLY (wired off per /051 REVERT) | run_baseline_v3.py:_build_v3_model |

Primitive 10 is preserved as code infrastructure (mechanism + 7 adversarial tests + GateStats counter) but wired-off at /051 REVERT per `feedback_v3_per_symbol_lifts_oos_breaks_is.md` UPDATED 2026-05-10. iter-v3/052 inherits this REVERT (no per-symbol customization wiring change). The EDA finding that LDO OOS drag is direction-asymmetric (axis 6) does NOT trigger a new primitive 10 wiring — that would be per-symbol customization, REJECTED at system level.

---

## Section 7 — Pre-Registered Failure-Mode Prediction

**Single most likely failure mode** (per §2 EDA finding): PATH C-suspicious — IS-OOS daily Sharpe ratio exits [0.5, 2.0] band on the high side due to LDO OOS removal lifting OOS Sharpe disproportionately vs IS Sharpe drop.

Mechanism: at /051 the BCH+TRX bundle (after counterfactual LDO removal) has IS daily Sharpe 0.675 and OOS daily Sharpe 2.418 (ratio 3.58). At /052 with Optuna re-tune on 2-sym universe, the predicted ratio is 2.5-4.0 — likely OUT-OF-BAND.

If observed: PATH C-suspicious classified per pre-registered §8 criteria. Memory rule update: `feedback_v3_per_symbol_lifts_oos_breaks_is.md` extended to universe-composition-level (drop a symbol) as a second-cycle confirmation.

### 7.1 — Predicted failure-mode taxonomy (5 paths per Critic FINAL `32cc46f` rec #3)

| Path | Probability | Trigger | Action if fires |
|---|---:|---|---|
| PATH A (PROMISING-clean) | 5% | IS Δ ≥ +0.05 AND OOS Δ ≥ +0.30 AND IS-OOS ratio in band | Carry to /053 stacking test (universal scope) |
| PATH B (PROMISING-INERT) | 5% | IS Δ ∈ [-0.10, +0.05] AND OOS Δ ∈ [-0.10, +0.10] | Parsimony-neutral; no axis advance |
| PATH C-clean | 25% | IS Δ < -0.10 OR OOS Δ < -0.30 with ratio in band | Close LDO removal axis; document anti-pattern |
| PATH C-suspicious | **50%** | IS-OOS daily Sharpe ratio outside [0.5, 2.0] | Close LDO removal axis; system-level anti-pattern confirmed at universe level |
| PATH D (NULL-RESULT) | 15% | IS Δ ∈ (-0.10, +0.05) AND OOS Δ ∈ (-0.20, +0.20) | PARK LDO removal axis; retest at multi-seed CONFIRMATION |

### 7.2 — Additional sanity-check failure modes

- **Optuna trial-count saturation**: 350 trials at 5 inner × 35 × 2 sym; n_eff may drop to 15-18 (vs /051's 19; comparable for EXPLORATION-spec). DSR likely 0.0 (structural at /052 n_trials; EXPLORATION-INFORMATIONAL per `feedback_v3_dsr_mode_artifact.md`).
- **PBO at 2-sym universe**: predicted 0.10 ± 0.05 (comparable to /051's 0.1168 and /028's 0.1243). The 2-sym CPCV with REQUIRED_GAP=44 produces fewer paths than 3-sym CPCV with GAP=66.
- **Concentration risk**: BCH dominates 130-140% IS share and 80-95% OOS share. The 2-sym universe inherently has higher top-symbol concentration than 3-sym. ≤30% aspirational gate FAILS by construction; informational only.

---

## Section 8 — Pre-Registered MERGE/NO-MERGE Numerical Criteria

**LOCKED at brief commit; mechanical evaluation post-backtest; NO post-hoc renegotiation per `feedback_no_cheating.md` discipline.**

### 8.1 — 5 LOCKED paths (per Critic FINAL `32cc46f` rec #3 PATH D addition)

| Path | All conditions must fire (AND) | Decision |
|---|---|---|
| **PATH A (PROMISING-clean)** | IS Δ ≥ +0.05 vs /028 anchor (+0.5101) AND OOS Δ ≥ +0.30 vs /028 anchor (+0.5053) AND IS-OOS daily Sharpe ratio ∈ [0.5, 2.0] | PROMISING for cycle 4 #2; carry to /053 stacking test |
| **PATH B (PROMISING-INERT)** | IS Δ ∈ [-0.10, +0.05] AND OOS Δ ∈ [-0.10, +0.10] AND trade count change < ±5% (saturation) | Parsimony-neutral; no axis advance; document NULL effect |
| **PATH C-clean (NEGATIVE-clean)** | IS Δ < -0.10 OR OOS Δ < -0.30 | NEGATIVE for cycle 4 #2; close LDO removal axis; document |
| **PATH C-suspicious (NEGATIVE-SUSPICIOUS-OOS)** | IS-OOS daily Sharpe ratio outside [0.5, 2.0] band | NEGATIVE-SUSPICIOUS; close LDO removal axis; system-level anti-pattern confirmed at universe-composition level (extend `feedback_v3_per_symbol_lifts_oos_breaks_is.md` to universe composition) |
| **PATH D (EXPLORATION-NULL-RESULT)** | IS Δ ∈ (-0.10, +0.05) AND OOS Δ ∈ (-0.20, +0.20) AND axis effect LEARNED (IS+OOS trade count both changed by ≥10% AND bundle Sharpe Δ both ≤ ±0.10) | NULL-RESULT; PARK LDO removal axis; retain code at zero revert cost; retest at multi-seed CONFIRMATION |

### 8.2 — Numerical thresholds

| Threshold | Value | Source |
|---|---|---|
| IS Sharpe anchor (/028 baseline) | +0.5101 | BASELINE_V3.md |
| OOS Sharpe anchor (/028 baseline) | +0.5053 | BASELINE_V3.md |
| PATH A IS Δ floor | +0.05 | EXPLORATION PROMISING band |
| PATH A OOS Δ floor | +0.30 | EXPLORATION PROMISING band |
| PATH B IS Δ range | [-0.10, +0.05] | INERT band |
| PATH B OOS Δ range | [-0.10, +0.10] | INERT band |
| PATH B trade-count saturation | < ±5% | Saturation falsifier |
| PATH C-clean IS Δ ceiling | -0.10 | NEGATIVE band |
| PATH C-clean OOS Δ ceiling | -0.30 | NEGATIVE band |
| PATH C-suspicious ratio band | [0.5, 2.0] | `feedback_v3_engineered_features_dont_stack.md` |
| PATH D IS Δ range | (-0.10, +0.05) | NULL-RESULT no-man's-land (per Critic FINAL `32cc46f` rec #3) |
| PATH D OOS Δ range | (-0.20, +0.20) | NULL-RESULT no-man's-land |
| PATH D learned criterion | trade count change ≥10% AND Sharpe Δ both ≤ ±0.10 | LEARNED with no decisive effect |

### 8.3 — BOTH-must-improve gate (advisory, NOT MERGE-blocking at EXPLORATION-spec)

Per `feedback_v3_strict_both_is_oos_baseline.md`, BASELINE_V3.md updates require BOTH IS AND OOS Sharpe improvement vs prior baseline. This gate is **CONFIRMATION-only** (not applied at EXPLORATION). However, the gate's spirit informs PATH A criteria: a clean PROMISING requires both IS and OOS lift (or at minimum, no IS regression).

At iter-v3/052 EXPLORATION-spec: if PATH A fires, the axis is candidate for cycle 4 #3 stacking. If PATH A does NOT fire AND PATH C-suspicious DOES fire, the axis is closed at the EXPLORATION level and the system-level anti-pattern extension is documented.

### 8.4 — DSR / PBO / PSR INFORMATIONAL at EXPLORATION-spec

Per `feedback_v3_dsr_mode_artifact.md`, EXPLORATION-mode DSR is structural artifact at n_trials=350 (E[max_SR] formula returns ~2.0 required; observed annualized ≈1.0-1.5 → DSR=0). Not a MERGE gate at EXPLORATION-spec.

- DSR > 0.95 gate: ENFORCED at CONFIRMATION only
- PBO < 0.4 gate: ENFORCED at both EXPLORATION and CONFIRMATION
- PSR > 0.95 gate: ENFORCED at both
- IC < 0.7 gate: ENFORCED at both (no new feature in /052; held over)

### 8.5 — Catalog row pre-commits (one per outcome)

(See §11 below for full row format)

---

## Section 9 — Library Stack Declaration

Pinned via `pyproject.toml` (UNCHANGED from /051):

```
lightgbm == 4.6.0
optuna == 4.8.0
numpy == 2.2.6
pandas == 3.0.0
scikit-learn == 1.8.0
scipy == 1.17.0
statsmodels == 0.14.6
pyarrow == 23.0.1
mlfinlab == 1.4 (fallback: mlfinpy)
pypbo
fracdiff >= 0.10
```

No new dependencies introduced at iter-v3/052. fracdiff package remains available (compute_fracdiff_d05_close uses it as numerical primitive); only V3_FEATURE_COLUMNS_TOP_N drops the column dispatch.

Python version: 3.13+.

---

## Section 10 — QR Audit Trail (per `feedback_v3_axis_selection_quant_discipline.md`)

### 10.1 — Setup commit SHA backfill

(To be backfilled at setup commit time; matches the Engineer's setup commit that implements §3 changes. Until backfill: PENDING.)

### 10.2 — EDA commit SHA

**`0a10581`** — analysis(iter-v3/052): LDO removal EDA — INVERTS orchestrator premise

7-axis EDA script (`analysis/iteration_v3-052/ldo_removal_eda.py`) + 7 CSV outputs + `synthesis.md`. Quantifies LDO contribution at /051 baseline; 2-sym counterfactual Sharpe; /050 vs /051 supersession check; cross-iteration LDO pattern; LDO directional asymmetry; data extent; monthly PnL pattern.

### 10.3 — QR disagreement with orchestrator brief premise — DOCUMENTED

**The orchestrator brief stated:**
- LDO IS PnL share = −14.96% at /051 (drag at IS too)
- LDO OOS weighted_pnl = −17.44 (drag at OOS)
- Recommended cycle 4 #2 axis: LDO removal investigation

**The QR EDA (SHA `0a10581`) finds:**
- LDO IS PnL share = **+36.78% weighted_pnl share** (CONTRIBUTOR, not drag) — premise misread net_pnl_pct vs weighted_pnl
- LDO OOS weighted_pnl = −17.44 wpnl (drag at OOS — CONFIRMED)
- 2-sym counterfactual at /051 trade roster: IS Sharpe Δ −0.16 (BREAKS IS), OOS Sharpe Δ +1.01 (lifts OOS)
- IS-OOS daily Sharpe ratio: 3.58 (OUT-OF-BAND, PATH C-suspicious)

**QR recommendation (synthesis.md):** PIVOT iter-v3/052 axis to one of:
1. `regime_momentum_signed_3d` at universal scope (queued from /051 EDA as RANKED #2; cleaner IC pass than fracdiff; significant Spearman at 4 syms; compute function dead-coded at engineered_v3.py:330) — STRONGLY PREFERRED
2. `hurst_drift_50_200` (new composed feature; deferred at /051 on implementation cost)
3. NEW universal engineered feature TBD

The QR's preferred /052 axis is `regime_momentum_signed_3d UNIVERSAL` — it is the EDA-validated cycle 4 #2 axis per the /051 RANKED #2 conclusion and per the cycle 4 hypothesis "lift IS Sharpe via UNIVERSAL axes (per-symbol customizations rejected at bundle level)."

### 10.4 — Orchestrator override — LOCKED IN

Per the orchestrator brief mandate (specified in this brief Section 0.5):

> Per Critic FINAL `32cc46f` recommendation #1 + engineering report `13a6ec5` critical finding (iter-v3/051) + iter-v3/050 diary recommendation: investigate LDO removal as cycle 4 #2 HIGH-priority axis.

The orchestrator brief LOCKED iter-v3/052 axis to LDO removal + fracdiff drop (two-variable bundle). Per `feedback_v3_axis_selection_quant_discipline.md`:

> Orchestrator may suggest candidates but cannot commit setup without QR backing. Brief Section 2 must contain EDA-derived numerical tables.

The QR has provided EDA-derived numerical tables in Section 2 (committed at SHA `0a10581`). The tables document that the EDA INVERTS the orchestrator's premise (LDO is IS contributor, not drag). The QR has registered disagreement in §10.3 and recommends a pivot in §10.3. 

**The orchestrator's authority to LOCK the axis prevails over QR disagreement.** Per the same memory rule:

> Cannot be retroactively renegotiated.

The QR proceeds with the locked LDO-removal axis. Pre-registration sets PATH C-suspicious as the most likely outcome. Section 11 catalog row pre-commits cover all 5 paths.

**This is structurally identical to iter-v3/041** where the QR raised concerns about universal feature pruning (BCH dropping ret_skew_50 + sym_vs_btc_ret_7d + regime_momentum_signed_5d simultaneously) and the orchestrator's mandate proceeded; iter-v3/041 fired PATH C with OOS Δ −1.55 below falsifier; iter-v3/042 RESTORED the dropped features per the pre-registered mandate. The QR discipline is: pre-register the prediction; run the test; classify mechanically.

### 10.5 — Justification for TWO-VARIABLE axis bundling

The orchestrator brief mandates TWO-variable axis (LDO drop + fracdiff drop). Per `feedback_v3_axis_selection_quant_discipline.md`, single-axis EXPLORATIONs are preferred. The bundling is justified as:

- **fracdiff drop is PARSIMONY (not axis under test)**: per /051 closeout, fracdiff_d05_close is PARKED — feature LEARNED but no IS lift. Dropping it returns V3_FEATURE_COLUMNS_TOP_N to /028 baseline 14-feature stack. This is a clean parsimony move with no expected effect on bundle metrics (the feature ranks 11-13/15 with low importance).

- **LDO drop is the ACTUAL AXIS UNDER TEST**: universe contraction 3 → 2 symbols, with attribution effect cleanly observable in IS+OOS Sharpe deltas.

- **Bundling reduces noise**: testing LDO removal alone with fracdiff still IN would risk confounding (fracdiff's low IS contribution and parked status would add unexplained variance to the attribution analysis). Dropping both simultaneously isolates the LDO-removal effect against a clean /028-baseline-equivalent feature stack.

This bundling is consistent with how /051 SETUP bundled "system-level REVERT" (per-symbol REVERT, not axis under test) with "fracdiff_d05_close ADD" (axis under test). The structurally analogous pattern at /052: "fracdiff DROP" (parsimony, not axis under test; clean revert to /028 stack) bundled with "LDO DROP" (axis under test).

### 10.6 — Critic FINAL `32cc46f` recommendation alignment

| Critic FINAL `32cc46f` Recommendation | iter-v3/052 brief addressed? |
|---|---|
| Rec #1: iter-v3/052 axis = LDO removal investigation (HIGH-priority cycle 4 #2) | YES — locked at §0.5; EDA quantifies effect (§2.2 counterfactual) |
| Rec #2: Drop fracdiff_d05_close from V3_FEATURE_COLUMNS_TOP_N at /052 setup (15 → 14). PARKED, not CLOSED. Retain compute function + tests. | YES — §3.1 setup commit; compute_fracdiff_d05_close + 5 tests retained as dead code |
| Rec #3: Brief pre-registration tightening — add PATH D (EXPLORATION-NULL-RESULT) covering IS Δ ∈ (-0.10, +0.05) AND OOS Δ ∈ (-0.30, +0.20) | YES — §8.1 PATH D added with tightened band [-0.20, +0.20] OOS (vs Critic's [-0.30, +0.20] suggestion; aligned with `feedback_v3_axis_saturation_predictor.md` symmetric band convention) |

---

## Section 11 — References

### Catalog row pre-commits (one per outcome path)

Per `briefs-v3/exploration_catalog.md` format. ONE row added to catalog at diary write per the firing path.

**PATH A (PROMISING-clean) catalog row:**
```
| iter-v3/052 | YYYY-MM-DD | EXPLORATION cycle 4 #2 of 10: DROP LDOUSDT from V3_MODELS (3 → 2 sym BCH+TRX) + DROP fracdiff_d05_close from V3_FEATURE_COLUMNS_TOP_N (15 → 14); --seeds 1 + ENSEMBLE_SIZE=5 + n_trials=35 + --clean-oof | [+IS_Δ] (vs iter-v3/028 baseline +0.5101 → [+IS]; +PROMISING-clean) | [+OOS_Δ] (vs iter-v3/028 baseline +0.5053 → [+OOS]; IS-OOS daily ratio [X] in band) | EXPLORATION-PROMISING-clean | YES — LDO removal lifts BOTH IS and OOS at single-seed. Carry to /053 stacking test. Universe contraction validated; cycle 4 hypothesis advances. |
```

**PATH B (PROMISING-INERT) catalog row:**
```
| iter-v3/052 | YYYY-MM-DD | EXPLORATION cycle 4 #2 of 10: DROP LDOUSDT from V3_MODELS (3 → 2 sym BCH+TRX) + DROP fracdiff_d05_close from V3_FEATURE_COLUMNS_TOP_N (15 → 14); --seeds 1 + ENSEMBLE_SIZE=5 + n_trials=35 + --clean-oof | [IS_Δ in [-0.10, +0.05]] (vs iter-v3/028 baseline +0.5101) | [OOS_Δ in [-0.10, +0.10]] (vs iter-v3/028 baseline +0.5053; trade counts saturated) | EXPLORATION-PROMISING-INERT (parsimony-neutral; LDO removal has no decisive effect) | NO — no axis advance; LDO removal does not lift bundle but also does not break it. |
```

**PATH C-clean (NEGATIVE-clean) catalog row:**
```
| iter-v3/052 | YYYY-MM-DD | EXPLORATION cycle 4 #2 of 10: DROP LDOUSDT from V3_MODELS (3 → 2 sym BCH+TRX) + DROP fracdiff_d05_close from V3_FEATURE_COLUMNS_TOP_N (15 → 14); --seeds 1 + ENSEMBLE_SIZE=5 + n_trials=35 + --clean-oof | [-IS_Δ < -0.10] (vs iter-v3/028 baseline +0.5101 → [IS]; PATH C-clean falsifier fired) | [+/-OOS_Δ] (vs iter-v3/028 baseline +0.5053; IS-OOS daily ratio [X]) | EXPLORATION-NEGATIVE-clean | NO — LDO removal regresses IS Sharpe as predicted by EDA counterfactual. LDO removal axis CLOSED for cycle 4. Document anti-pattern. |
```

**PATH C-suspicious (NEGATIVE-SUSPICIOUS-OOS) catalog row — MOST LIKELY:**
```
| iter-v3/052 | YYYY-MM-DD | EXPLORATION cycle 4 #2 of 10: DROP LDOUSDT from V3_MODELS (3 → 2 sym BCH+TRX) + DROP fracdiff_d05_close from V3_FEATURE_COLUMNS_TOP_N (15 → 14); --seeds 1 + ENSEMBLE_SIZE=5 + n_trials=35 + --clean-oof | [IS_Δ vs +0.5101] (vs iter-v3/028 baseline) | [+OOS_Δ ≥ +0.30] (vs iter-v3/028 baseline +0.5053; IS-OOS daily ratio [X] OUT-OF-BAND) | EXPLORATION-NEGATIVE-SUSPICIOUS-OOS (per-symbol customization anti-pattern at universe-composition level) | NO — LDO removal triggers PATH C-suspicious anti-pattern per `feedback_v3_per_symbol_lifts_oos_breaks_is.md`. System-level confirmation extends from per-symbol customizations to universe composition. LDO removal axis CLOSED for cycle 4. |
```

**PATH D (EXPLORATION-NULL-RESULT) catalog row:**
```
| iter-v3/052 | YYYY-MM-DD | EXPLORATION cycle 4 #2 of 10: DROP LDOUSDT from V3_MODELS (3 → 2 sym BCH+TRX) + DROP fracdiff_d05_close from V3_FEATURE_COLUMNS_TOP_N (15 → 14); --seeds 1 + ENSEMBLE_SIZE=5 + n_trials=35 + --clean-oof | [IS_Δ in (-0.10, +0.05)] (vs iter-v3/028 baseline +0.5101) | [OOS_Δ in (-0.20, +0.20)] (vs iter-v3/028 baseline +0.5053; axis effect LEARNED — trade count changed by ≥10%) | EXPLORATION-NULL-RESULT (per Critic FINAL `32cc46f` rec #3) | NO — LDO removal axis PARKED (not CLOSED). Retain code at zero revert cost. Retest at multi-seed CONFIRMATION as bundle ingredient. |
```

### 11.2 — File references

- `analysis/iteration_v3-052/ldo_removal_eda.py` (SHA `0a10581`) — 7-axis EDA
- `analysis/iteration_v3-052/axis1_ldo_contribution_at_051.csv` — LDO weighted_pnl share
- `analysis/iteration_v3-052/axis2_counterfactual_2sym.csv` — 2-sym BCH+TRX counterfactual (CRITICAL TABLE)
- `analysis/iteration_v3-052/axis3_050_vs_051_supersession.csv` — premise correction
- `analysis/iteration_v3-052/axis4_cross_iteration_ldo.csv` — LDO pattern across /028/045/047/049/050/051
- `analysis/iteration_v3-052/axis5_data_extent.csv` — LDO 30 months vs BCH/TRX 62 months
- `analysis/iteration_v3-052/axis6_ldo_directional_asymmetry.csv` — LDO LONG vs SHORT at /051
- `analysis/iteration_v3-052/axis7_ldo_monthly_pnl.csv` — LDO 2025-Q3 OOS regression concentration
- `analysis/iteration_v3-052/synthesis.md` — full ranking + behavioral predictor + recommended pivot

### 11.3 — Memory rules consulted

- `feedback_v3_axis_selection_quant_discipline.md` — QR EDA-driven axis selection; Section 10 audit trail when orchestrator overrides
- `feedback_v3_strict_both_is_oos_baseline.md` — BOTH-must-improve gate (CONFIRMATION-only; advisory at EXPLORATION)
- `feedback_v3_per_symbol_lifts_oos_breaks_is.md` — per-symbol customization anti-pattern (LDO removal triggers same at universe-composition level)
- `feedback_v3_strict_10_to_1_cadence.md` — cycle 4 #2 of 10; do NOT collapse 10th EXPLORATION into CONFIRMATION
- `feedback_v3_exploration_n_trials_35.md` — n_trials=35 EXPLORATION default
- `feedback_v3_single_seed_frozen_baseline.md` — single-seed=42 lottery caveat (esp. for OOS interpretation)
- `feedback_v3_dsr_mode_artifact.md` — DSR/PSR EXPLORATION-INFORMATIONAL at n_trials=350
- `feedback_v3_engineered_features_dont_stack.md` — IS-OOS daily Sharpe ratio falsifier [0.5, 2.0]
- `feedback_v3_axis_saturation_predictor.md` — Section 4 behavioral-effect predictor mandate
- `feedback_v3_engineered_feature_pivot.md` — Category 2 carve-out (N/A at /052 since fracdiff dropped)
- `feedback_v3_baseline_update_policy.md` — STRICTLY-BETTER-than-prior-baseline (CONFIRMATION-only)
- `feedback_v3_concentration_is_signal.md` — per-symbol cap CLOSED (informs §5.5)
- `feedback_no_cheating.md` — no post-hoc renegotiation of pre-registered §7-§8

### 11.4 — Critic FINAL artifacts

- `briefs-v3/iteration_v3-051/review.md` SHA `32cc46f` — recommendations #1 + #2 + #3 + #4
- `briefs-v3/iteration_v3-051/engineering_report.md` SHA `13a6ec5` — critical finding driving /052 axis selection
- `diary-v3/iteration_v3-051.md` — /051 closeout setting up /052 mandate
- `diary-v3/iteration_v3-050.md` — /050 closeout setting up cycle 4 priorities

### 11.5 — Baseline anchor

- `BASELINE_V3.md` (UNCHANGED at iter-v3/028; +0.5101 IS / +0.5053 OOS multi-seed mean; SHA `b0576df`)

---

## Section 12 — Brief Validation Checklist (Pre-Phase-5.5)

| # | Requirement | Status |
|---|---|---|
| 1 | Data split declaration (§0) | DONE |
| 2 | Iteration type declaration with spec (§0.5) | DONE — EXPLORATION cycle 4 #2; --seeds 1 --n-trials 35 --clean-oof |
| 3 | Hypothesis (§1) | DONE |
| 4 | IS-only numerical evidence with committed analysis script (§2) | DONE — SHA `0a10581` |
| 5 | Proposed changes (§3) | DONE — TWO-variable: V3_MODELS 3→2 + V3_FEATURE_COLUMNS_TOP_N 15→14 + REQUIRED_GAP 66→44 |
| 6 | Expected OOS impact with predicted bands + behavioral-effect predictor (§4) | DONE — §4.1 quantitative bands; §4.2 trade-count predictor |
| 7 | Risk Mitigation R1-R5 with IS-calibrated thresholds (§5) | DONE |
| 8 | Risk Management Design 10-primitive gate table (§6) | DONE |
| 9 | Pre-registered failure-mode prediction (§7) | DONE — PATH C-suspicious 50% most likely |
| 10 | Pre-registered MERGE/NO-MERGE numerical criteria LOCKED (§8) | DONE — 5 paths incl. new PATH D per Critic `32cc46f` rec #3 |
| 11 | Library stack declaration (§9) | DONE — UNCHANGED from /051 |
| 12 | Section 10 QR audit trail | DONE — disagreement registered; orchestrator override locked-in |
| 13 | Section 11 catalog row pre-commits | DONE — 5 rows (one per path) |
| 14 | Setup commit SHA backfill placeholder (§10.1) | PENDING (Engineer backfills) |
| 15 | All 12 mandatory sections present | DONE |

**Brief LOCKED at commit. Pre-Phase-5.5 gate criteria satisfied. Ready for QE Phase 5.5 review.**

---

**End of iteration v3-052 research brief.**
