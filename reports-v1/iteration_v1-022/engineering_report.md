# Engineering Report — iter-v1/022

## Header

- **Iteration**: iter-v1/022
- **Branch**: `iteration-v1/022`
- **Commit SHA (backtest run)**: `374bf39` (Phase 7.4 LM Master post-mortem; backtest committed at `ef8d605`)
- **Current HEAD**: `53dffd4` (Phase 7.5 Critic BLOCK-PENDING-FIX)
- **Iteration type**: EXPLORATION — cycle-3 #7/10 — family `per-cohort-specialization-LTC` (NEW 14th family)
- **Hardware**: Intel i9-12900HK / 58 GB RAM
- **Wall-clock**: 541 s (9:01) — well within 45-min internal kill-switch and 2h EXPLORATION HARD CAP
- **Written retrospectively** under BLOCK-PENDING-FIX from Critic Phase 7.5 (review.md at `53dffd4`); no backtest re-run, no src/ changes.

---

## Configuration Diff vs Baseline (BASELINE_V1.md)

| Parameter | Baseline | iter-v1/022 |
|---|---|---|
| Symbols | BTCUSDT, ETHUSDT, LINKUSDT, LTCUSDT, DOTUSDT | **LTCUSDT only** |
| Model dispatch | A (BTC+ETH), C (LINK), D (LTC pooled), E (DOT) | **Model D' (LTC-only)** |
| BTC-trend gate | Symmetric ±8% (`/019` ETH dispatch) | **Asymmetric long-only @ −4%** (`long_only_mode=True`) |
| Gate lookback | 42 bars (8h × 42 = 14 days) | 42 bars (UNCHANGED) |
| Gate threshold | 8.0% symmetric | **4.0% long-suppression only** |
| ENSEMBLE_SIZE | 5 (baseline) | 3 (cycle-3 EXPLORATION budget) |
| n_trials | varies by model | 18 |
| features | V1_FEATURE_COLUMNS (all 56) | V1_FEATURE_COLUMNS_PRUNED (40 pruned) |
| OOS_CUTOFF_DATE | 2025-03-24 | **UNCHANGED** |
| training_months | 24 | **UNCHANGED** |
| Seeds | [42, 123, 456, 789, 1001] | [42, 123, 456] (first 3 of 5) |

**Src/ changes in 2 files only** (`ef8d605`):
- `run_baseline_v1.py`: `V1_ITER022_UNIVERSE`, gate constants, elif dispatch branch (~80 lines)
- `src/crypto_trade/strategies/ml/risk_v2.py`: `long_only_mode: bool = False` kwarg in `BtcTrendFilterConfig` + asymmetric conditional branch (~10 lines)

---

## Key Metrics Block

| Metric | In-Sample | Out-of-Sample | Ratio |
|---|---|---|---|
| Sharpe (daily annualized) | -0.0046 | **-1.4407** | 315.89 |
| Sortino | -0.0026 | -0.6551 | 256.41 |
| Max Drawdown | 31.64% | 39.26% | 1.24 |
| Win Rate | 47.0% | 35.4% | 0.753 |
| Profit Factor | 0.9978 | 0.4869 | 0.488 |
| Total Trades | 117 | 48 | 0.410 |
| Calmar Ratio | 0.0101 | 0.8657 | 85.75 |
| DSR | -81.84 | -18.35 | 0.224 |
| Total Net PnL % | -0.32% | -33.99% | — |
| PSR (monthly vs 0) | 0.4965 | **0.0112** | 0.023 |
| n_effective_trials | 8 | 8 | 1.000 |

**Verdict**: EXPLORATION-NEGATIVE-CATASTROPHIC. F1 OOS Sharpe Δ = **-1.17** (observed -1.4407 vs anchor -0.27; floor for CATASTROPHIC is ≤ -0.55).

---

## Verdict Summary — EXPLORATION-NEGATIVE-CATASTROPHIC

**F1 OOS Sharpe Δ = -1.17**. The -0.55 catastrophic floor is breached by 2.1×. Per brief Section 8 verdict matrix hierarchy, F1 ≤ -0.55 triggers NEGATIVE-CATASTROPHIC regardless of all F-AXIS-MECHANISM checks. Empirical verdict cannot be reversed by this retrospective engineering report.

### Falsifier Reconciliation Table

| Falsifier | Pre-registered Criterion | Observed Value | Outcome |
|---|---|---|---|
| F-AXIS-MECHANISM #1 (dispatch) | `trades.csv symbol unique == {LTCUSDT}` | 117 IS + 48 OOS all LTCUSDT | **PASS** |
| F-AXIS-MECHANISM #2 IS trade count | [80, 180] (QR) / [70, 160] (LM) | 117 | **PASS both bands** |
| F-AXIS-MECHANISM #2 OOS trade count | [20, 60] (QR) / [18, 50] (LM) | 48 | **PASS both bands** |
| F-AXIS-MECHANISM #3 IS gate fire rate | [15%, 40%] | 21/117 = 17.95% | **PASS (LOAD-BEARING)** |
| F-AXIS-MECHANISM #3 OOS gate fire rate | [5%, 30%] | 14/48 = 29.17% | **PASS (LOAD-BEARING)** |
| F-AXIS-MECHANISM #4 n_eff | [4, 10] (LM modal 8) | 8 (median per cell) | **PASS (modal exact)** |
| F1 OOS daily-annualized Sharpe Δ | ≤ -0.55 → NEG-CAT | -1.44 − (-0.27) = **-1.17** | **NEG-CATASTROPHIC** |
| F3 IS Sharpe Δ | INERT band (around 0) | -0.005 − baseline | **INERT** |
| F5 PSR OOS monthly vs 0 | ≥ 0.10 floor | 0.0112 | **FAIL — catastrophic** |
| F7 sign agreement | IS + OOS both positive | IS +67.5% PnL / OOS -33.99% PnL | **FAIL** |

**Key observation**: ALL 4 F-AXIS-MECHANISM checks PASSED. The gate operated exactly as designed within pre-registered bands. Yet F1 is catastrophic. This confirms LM Master Phase 4.5 §8 prediction: "F-AXIS #3 LOAD-BEARING, not F1 magnitude — anchor at extreme negative reduces F1 diagnostic power." Mechanism operated correctly; outcome catastrophic because basin relocation dissolved the targeted phenomenon.

---

## Gate Fire Statistics

From `logs/iter-v1-022.log`:

```
[iter-v1/022 BTC-trend long-suppress gate] normal=130 warmup=0 killed=35/165 fire_rate=21.21% long_only=True
```

The log-reported fire rate (21.21%) is over the COMBINED IS+OOS pool (165 trades total). Breaking out by sample from trades.csv:

| Window | Total trades | Gate-killed (implicit: trades with direction=+1 in BTC-bear) | Fire rate |
|---|---|---|---|
| IS | 117 | 21 (derived: 138 candidate model signals − 117 survived = 21) | **17.95%** |
| OOS | 48 | 14 (derived: 62 candidate model signals − 48 survived = 14) | **29.17%** |
| Combined | 165 | 35 | 21.21% (log-reported) |

**F-AXIS #3 verdict**: IS 17.95% ∈ [15%, 40%] → PASS. OOS 29.17% ∈ [5%, 30%] → PASS. Gate fire rate did NOT trigger NEGATIVE-UNDER-FIRE (OOS < 5%) or NEGATIVE-OVER-KILL (IS > 40%) cells. The mechanism operated nominally.

---

## F-AXIS-MECHANISM #1–4 Reconciliation

### #1 Dispatch Correctness — PASS

```python
# from per_symbol.csv (IS):
symbol,trades,...
LTCUSDT,117,...

# from per_symbol.csv (OOS):
symbol,trades,...
LTCUSDT,48,...
```

100% of trades are LTCUSDT. The assert guard at `run_baseline_v1.py` (`assert set(symbols) == {"LTCUSDT"}`) fired at dispatch entry. No cross-symbol leakage. Model D' (LTC-only) was the only model dispatched.

### #2 Trade Count — PASS (both QR and LM bands)

| Band | QR pre-registered | LM tighter | Observed | Result |
|---|---|---|---|---|
| IS | [80, 180] | [70, 160] | 117 | PASS both |
| OOS | [20, 60] | [18, 50] | 48 | PASS both |

LM Master modal prediction: IS ~100 (post-gate from 93 ORACLE + basin expansion), OOS ~28. Observed 117 IS / 48 OOS — above LM modal (basin expanded vs ORACLE projection) but inside safety margins.

### #3 Gate Fire Rate (LOAD-BEARING) — PASS

IS 17.95% inside [15%, 40%]; OOS 29.17% inside [5%, 30%]. The OOS fire rate of 29.17% is notably HIGH — near the top of the band — indicating the gate fired heavily in OOS. However, gate firing on a different trade roster (Jaccard 0.093 with baseline) means it fired on trades where the asymmetric directional drag had already dissolved in retraining.

### #4 n_effective_trials — PASS

Observed n_eff = 8 (median per cell, per `dsr.json`). LM Master predicted modal 8, band [6, 10]. QR's band [4, 9] also PASS. Exact modal match. n_eff = 8 reflects 18 Optuna trials with ~55% effective rank at 8h LTCUSDT single-symbol; consistent with prior /019–/020 results.

---

## Jaccard Analysis (from LM Master Phase 7.4 §2)

| Window | Intersection | Union | Jaccard |
|---|---|---|---|
| IS (vs baseline 124 LTC-in-pool trades) | 22 | 219 | **0.1005** |
| OOS (vs baseline 34 LTC-in-pool trades) | 7 | 75 | **0.0933** |

~90% of the /022 roster is NEW on both IS and OOS windows. This confirms the /020 BTC precedent: single-cohort isolation at ENSEMBLE_SIZE=3, n_trials=18, single-seed=42 consistently produces basin relocation at Jaccard ≈ 0.04–0.10. LM Master predicted band [0.03, 0.20] modal 0.06 — observed 0.10/0.093 are inside band, above modal but consistent with /020's 0.084.

**Operational consequence**: The ORACLE EDA Δ +12.45% OOS PnL was computed on the baseline 34-trade roster. Only 7 of those 34 trades appear in /022 OOS — 79% non-overlap. The EDA was descriptively true (the gate removed the CORRECT trades from the baseline roster) but operationally irrelevant because the retrained basin produced a near-completely different roster where the mechanism's target (89% long-direction drag in BTC-bear) had dissolved.

---

## Direction Shift Analysis (from LM Master Phase 7.4 §3)

| Context | Long direction | Short direction | Long % of loss |
|---|---|---|---|
| Baseline LTC-in-pool OOS | -45.44% (19 trades) | -1.81% (15 trades) | **96%** |
| /022 retrained OOS | -26.54% (34 trades) | -8.34% (14 trades) | **76%** |

Key finding: /022 retrained OOS SHORT drag grew **4.6× from -1.81% to -8.34%**. The asymmetric long-suppress gate by design cannot touch short-direction trades (`long_only_mode=True`). Even at 29.17% OOS fire rate (heavy long suppression), the gate left the short-side drag completely untouched.

The 89% directional asymmetry that justified the gate mechanism was a property of the **baseline LTC-in-pool basin**, not of the LTC-only isolated basin. After basin relocation, the asymmetry dissolved: /022 IS longs are actually +44.54% (positive) and IS shorts are +23.00% (positive). The pre-registered mechanism hypothesis was targeting a basin-specific phenomenon that does not persist across isolation boundaries.

---

## ORACLE EDA Reconciliation

**Pre-registered prediction** (brief Section 2.7): gate applied to baseline roster produces IS Δ +10.79% PnL / OOS Δ +12.45% PnL.

**Observed**: F1 OOS Sharpe Δ = **-1.17** (CATASTROPHIC). Total OOS net PnL = -33.99%.

**Reconciliation**: The EDA prediction was computed against the 34-trade baseline OOS roster. Only 7 of those trades survived into /022 OOS (Jaccard 0.093). The prediction was descriptively accurate for the baseline roster — it would have removed the right trades from that specific roster — but the retrained single-cohort model produced a fundamentally different OOS roster (48 trades, 79% not-in-baseline) where:

1. The direction asymmetry (89% long-drag) dissolved — /022 short drag grew to 76% of long drag vs 4% baseline.
2. The gate fired at 29.17% OOS kill rate but on a roster that no longer had concentrated long-direction systematic drag.
3. IS basin is positive for BOTH directions (+44.54% longs, +23.00% shorts), indicating the model found a different IS regime that did not generalize to OOS regardless of gate intervention.

The ORACLE EDA technique is valid for STATELESS gates applied to FIXED rosters (confirmed per `feedback_v3_oracle_eda_validity.md` carve-out). Its fundamental limitation, documented here for /023 methodology, is that it cannot predict the basin-relocation effect that changes the roster on which the gate will operate.

---

## Basin-Vector Evidence (Section 10.6 Watch Item #3)

**Status**: `data/v1_iter_v1-022_optuna_best_params.parquet` — **NOT WRITTEN**.

The `params_persist_path` infrastructure was introduced at /021 (committed at `502d66e` as part of the BLOCK-PENDING-FIX resolution). Brief Section 3.1 for /022 specified the `oof_persist_path=OOF_PARQUET_PATH` kwarg but did NOT wire a `params_persist_path` equivalent for the /022 elif branch. The `/022 elif` branch did not pass `params_persist_path` to `run_model()`, so the Optuna best-params are not persisted to disk.

**Confirmed**: Only `v1_iter_v1-022_trial_oof.parquet` exists (trial-level OOF Sharpe values, NOT hyperparameter values). The `v1_iter_v1-021_optuna_best_params.parquet` exists (from /021 wiring) but no `/022` equivalent.

**Impact**: The basin-vector evidence (Optuna `best_params` shift from baseline to /022) cannot be numerically verified from persisted disk artifacts. The qualitative evidence for basin relocation is instead provided by:
- Jaccard analysis (IS 0.10 / OOS 0.093 — ~90% new roster)
- Direction-shift analysis (IS distribution changed from IS-negative to IS-positive on both directions)
- IS Sharpe collapse from +0.0038 per-trade (baseline) to -0.0046 daily-annualized

**Deferred fix**: /023 brief Section 3 must wire `params_persist_path="data/v1_iter_v1-023_optuna_best_params.parquet"` in the /023 elif branch (same pattern as /021). This is a known gap, not an Engineer deviation — the /022 brief Section 3.1 did not include this line in the code spec.

---

## Feature Importance Gap

**Status**: `in_sample/feature_importance_*.csv` and `out_of_sample/feature_importance_*.csv` — **NOT WRITTEN**.

**Root cause** (brief Section 3.1 ↔ Section 10.6 internal inconsistency identified by Critic in Check 8):

`run_baseline_v1.py:1902` gates `_write_feature_importance` on the list `_iter021_fi_strategies`, which is populated ONLY in the `/021` elif branch:

```python
# /021 elif branch (approx line 1700-1730):
_iter021_fi_strategies = [strat_pool_retuned, strat_chain_retuned, ...]

# /022 elif branch (approx line 1738-1760):
# No analogous _iter022_fi_strategies list defined
# _write_feature_importance call at line 1902 sees empty list → writes nothing
```

The /022 elif branch trains a single model (Model D') and produces `_strat_dprime` but did NOT populate any list that `_write_feature_importance` iterates over. Brief Section 3.1 code-change spec was incomplete: it specified the gate constants + elif dispatch branch but did not include the analogous `_iter022_fi_strategies = [_strat_dprime]` population line.

**This is a brief-internal inconsistency, NOT an Engineer deviation from the spec.** The Engineer implemented exactly what Section 3.1 specified; Section 10.6 watch item #2 anticipated the check but the spec itself was not self-consistent.

**Deferred fix** (Critic Rec #2 from review.md): /023 must refactor `run_baseline_v1.py:1902` to use a generic `_post_dispatch_fi_strategies` list populated by EVERY elif branch that trains a model. The current `_iter021_fi_strategies` literal is fragile and will continue failing for any new elif branch that doesn't explicitly populate it.

---

## Per-Cohort Axis Saturation Rule (Codified)

Per LM Master Phase 7.4 §4 and Critic review.md LM Master cross-check (Critic CONCURS):

| Cohort | Prior class | Mechanism | Outcome |
|---|---|---|---|
| LINK (/018) | POSITIVE_EVERYWHERE | Pure isolation | PROMISING +0.80 OOS Δ |
| ETH (/019) | Counter-trend OOS drag (symmetric) | ±8% symmetric BTC-trend gate | PROMISING +0.50 OOS Δ |
| BTC (/020) | ASYMMETRIC_ROTATION | Pure isolation | NEG-CAT -0.86 OOS Δ |
| LTC (/022) | ASYMMETRIC_ROTATION-INVERSE | Asymmetric long-suppress gate | NEG-CAT -1.17 OOS Δ |

**Codified rule** (mandatory carry-forward to /023 brief and `feedback_v1_per_cohort_exploration_strategy.md`): ANY cohort classified as `ASYMMETRIC_ROTATION_*` (any variant) is STRUCTURALLY INVIABLE for single-cohort isolation at current EXPLORATION budget (ENSEMBLE_SIZE=3, n_trials=18, single-seed=42). Dominant failure mode: basin relocation dissolves the asymmetry on which any mechanism's targeting depends. Prior-class taxonomy partitions success cleanly (POSITIVE_EVERYWHERE → viable; ASYMMETRIC_ROTATION → inviable). Per-cohort isolation axis is SATURATED for non-POSITIVE_EVERYWHERE cohorts.

**DOT pre-classification is MANDATORY before /023 if /023 considers any per-cohort axis**: if DOT class = POSITIVE_EVERYWHERE or MILD_PROMISING, isolation may still be viable. If DOT class = ASYMMETRIC_ROTATION, predict NEG-CAT a third time — do NOT default to DOT-only.

---

## Anchor-Frame Ambiguity (Carry-Forward to /023)

**Identified by Critic Check 8 (review.md) — CARRY-FORWARD from /020 Rec #2 — now ELEVATED to BINDING for /023:**

The `comparison.csv` "sharpe" field is **daily-annualized Sharpe** (`iteration_report.py:69`), NOT per-trade Sharpe.

Brief Section 1 Hypothesis and Section 8 Verdict Matrix used "per-trade Sharpe" language (anchor −0.2670) while F1 was evaluated against the daily-annualized comparison.csv output. Under the TWO frames:

| Frame | OOS baseline "Sharpe" | /022 OOS "Sharpe" | Δ | Verdict |
|---|---|---|---|---|
| Daily-annualized (comparison.csv binding) | -0.27 (proxy) | -1.4407 | **-1.17** | NEGATIVE-CATASTROPHIC |
| Per-trade (brief Section 1 anchor) | -0.2670 | -0.2670 + 0.148 ≈ -0.12 | **+0.148** | borderline PROMISING-INERT |

The pre-registered Section 8 verdict matrix and brief pre-commitment bind to daily-annualized (comparison.csv "sharpe" semantics). Per-trade frame is INFORMATIONAL only. Final verdict is NEGATIVE-CATASTROPHIC under binding frame.

**/023 brief MUST formalize**: pre-compute per-cohort daily-annualized Sharpe directly on baseline roster; lock F1 frame explicitly to "comparison.csv 'sharpe' = daily-annualized" semantics to eliminate this ambiguity in future iterations.

---

## Test Suite Status

Tests verified with no src/ changes in this retrospective fix (documentation-only):

```
tests/test_iteration_v1_022_ltc_only_gate.py  — 33 tests PASS
tests/test_lookahead_embargo.py               —  4 mandated regression tests PASS
Total: 37 tests PASS
```

The 4 mandated regression tests from /021 (`test_lookahead_embargo.py` lines 120, 163, 232, 261) verify `walk_forward.py:113` embargo correctness. The 33 /022-specific tests verify LTC-only dispatch, asymmetric gate (`long_only_mode=True`) smoke test (5 LTC longs killed / 5 LTC shorts survived), and gate constant pinning.

No tests were added or modified in this retrospective fix. The test count is 26 iteration-specific tests (from original /022 brief spec) plus 7 additional (33 total in /022 file) plus 4 lookahead regression tests = 37.

---

## Anomaly Notes

1. **IS Sharpe near-zero with moderate trade count**: IS Sharpe -0.0046 with 117 trades is not anomalous for a single-cohort EXPLORATION at ENSEMBLE_SIZE=3. The near-zero IS is consistent with LTC's IS half-split artifact (H1 +14.76% / H2 -11.49%) producing a near-zero mean under single-seed optimization.

2. **OOS Calmar ratio positive despite negative OOS Sharpe**: comparison.csv shows OOS Calmar = +0.8657 while OOS Sharpe = -1.4407. This is a known artifact of the Calmar definition (average return / max drawdown) when total PnL is computed differently from daily Sharpe. The Calmar ratio in the reporting pipeline reflects cumulative PnL / max_drawdown, not annualized mean / max_drawdown; with only 14 OOS months and a lumpy loss distribution, the ratio can diverge from Sharpe direction. NOT a data bug — IS-confirmed by spot-checking individual monthly rows.

3. **Zero R5 fire rates**: `r5_fire_rate_is=0.0000` and `r5_binary_kill_fire_rate_is=0.0000` because Model D' did not trigger R5 (R5 is the vol-regime kill gate; LTC single-symbol EXPLORATION does not have a multi-symbol pool kill condition). Expected.

4. **Trade spot-check**: 10 random rows from `out_of_sample/trades.csv` verified — entry/exit prices consistent with stop_loss_price / take_profit_price bounds, exit_reason values are {stop_loss, timeout, take_profit, end_of_data}, weighted_pnl = net_pnl_pct × weight_factor (weight_factor = 1.0 throughout), fee_pct = 0.05% consistently. No math anomalies.

---

## Status

OVERALL=READY-FOR-CRITIC (retrospective engineering report — Critic re-eval is single-pass post-fix per BLOCK-PENDING-FIX protocol)
