# Phase 6.0 Critic Pre-Flight — iter-v1/076

OVERALL: PASS

## Iteration Context

- **TYPE**: SPECIALIST EXPLORATION — NEW SYMBOL universe-extension (cycle-7 SPECIALIST-MINE 2/N)
- **Symbol**: AAVEUSDT (single-coin cohort `V1_ITER076_UNIVERSE = ("AAVEUSDT",)`)
- **Anchor**: NONE (NEW SYMBOL; verdict frame is BUNDLE-001 member IS Sharpe distribution mean +0.16, std ≈ 0.30)
- **Branch**: `iteration-v1/076`
- **Brief commit anchor**: Section 12 freezes F-AXIS bands at the brief commit SHA (`1436ef8` per `git log`)
- **Methodology constants HELD per user directive 2026-06-06**: 50 inner seeds × 30 Optuna trials × `specialist_mode=True` + 48-col `V1_FEATURE_COLUMNS_PRUNED` (hash `b81176f8…`) + ATR (TP=2.9, SL=1.45) + R1=OFF + R2=OFF + R3=ON-SHARED cutoff=0.70 + R5=ON (vt_target_vol=0.3, vt_lookback_days=45) + max_depth=5 FIXED + num_leaves=31 FIXED + n_estimators ≤ 500 + n_startup_trials=10 + mean-of-signed-weights aggregator + training_months=24
- **Single-bit deviation set vs /075 dispatch**: (a) `SYMBOLS=("AAVEUSDT",)`; (b) `ITERATION_LABEL="v1-076"`. ATR cell and wrapper match /075 byte-identically (both are Model A ETH-class)
- **LM Master verdict**: MEDIUM-LOW confidence; modal IS Sharpe +0.20; aggregate PROMISING-or-better probability 0.39

---

## Pre-Flight Checks

### Mini-Check 1 — Brief Look-Ahead Audit: PASS

Brief Section 0 declares the IS-firewall mechanism: EDA script `analysis/v1-076/eda.py` uses `is_only(df)` filter (`open_time < OOS_CUTOFF_MS = 1742774400000`) and the `_assert_is_only_path` helper which asserts no `out_of_sample` substring on every loaded path. Section 0 also explicitly states that the SOLE OOS read is `table_09_feature_nan_audit` surfacing OOS NaN counts as a Phase 5.5 sanity check — NOT used to derive any signal, threshold, or band edge. F-AXIS bands in Section 4 are anchored to the BUNDLE-001 member IS Sharpe distribution (mean +0.16, std ≈ 0.30) plus LM Master Phase 4.5 modal +0.20 — both purely IS-derived references. Sacred constants (`OOS_CUTOFF_DATE=2025-03-24`, `training_months=24`) restated as IMMUTABLE. The Section 2 evidence tables (TS-mom grid, regime mix, vol regime by year, NaN audit) are all IS-only by construction. No feature description in Section 3 suggests forward data use; no "next-bar funding", "today's range", or "forward window std" patterns. Look-ahead audit clean at the brief layer.

### Mini-Check 13 — Anti-Pattern Static Scan: PASS

Scanned QE's src/ diff (commit `1be3bd1` — `feat(iter-v1/034): basis_zscore_30 feature + dispatch + tests` — and Phase 6 setup additions for /076 universe constant + dispatch branch) against the 13-signature catalog.

- **A1 (train_end_ms regression)**: `grep "train_end_ms\s*=\s*test_start_ms[^-]"` returns ZERO matches in active code. `walk_forward.py:113` carries the correct `train_end_ms = test_start_ms - embargo_ms`. `cross_sectional.py:1325, 1345` are documented exception comments + correct math.
- **A2 (labeling σ_t look-ahead)**: `grep "returns\[.*:.*\]\.std\(\)"` in `labeling.py` returns zero forward-window std calls.
- **A3 (scaler fit on combined train+test)**: `grep "scaler\.fit_transform|FractionalDifferentiation.*fit"` returns zero matches across `src/`. LightGBM is scale-invariant; no preprocessing precedes split.
- **A4 (universe survivorship)**: `V1_ITER076_UNIVERSE = ("AAVEUSDT",)` is a static literal in `features_v1/__init__.py:670`. Not computed from current data. The mine-phase selection narrative in the brief (Section 0.5) cites pre-OOS-window metrics only — TS-mom IS Sharpe, IS realized vol, IS regime mix.
- **A5 (master-data-extent dependency)**: covered by `tests/test_lookahead_embargo.py` (present per Glob); 4 tests including `test_labels_are_invariant_to_master_data_extent`.
- **A6 (Optuna trial contamination)**: SPECIALIST-mode runs 50 independent Optuna studies (one per seed `42..91`) per `_train_for_month`. No cross-cell study sharing. Runner at `run_iteration_076.py:312-326` passes `--exploration` + `--ensemble-size 1` + `--seeds 1` — single outer ply, inner specialist loop owns the per-seed studies.
- **A7 (OOF parquet append-without-clearing)**: `optimization.py:597` matches the catalog's documented exception (append-if-file-exists pattern with `--clean-oof` CLI flag at startup per v3 SHA `6a216b5`). Not an unexplained match.
- **A8 (stateful gate deadlock)**: R3 OOD aggregator gate is non-stateful (per-bar Mahalanobis distance). R1=OFF disables consecutive-SL state. R2=OFF disables drawdown peak state. R5 vol-targeting updates per-trade (no deadlock surface).
- **A9 (forming candle)**: standard `fetcher.py` close_time < now_ms guard inherited; no /076-specific change.
- **A10 (confidence threshold on test data)**: brief Section 3.3 confirms Optuna selects `confidence_threshold` per seed within `[0.50, 0.85]` based on validation Sharpe (in-fold), not test fold.
- **A11 (parquets with future data)**: `data/features/AAVEUSDT_8h_features.parquet` is the global features parquet; per-cell training restricts via `train_start_ms`/`train_end_ms` boundaries with embargo subtraction (walk_forward.py:113).
- **A12 (DSR/PSR granularity)**: SPECIALIST EXPLORATION verdict gates on F-AXIS #1 mean IS Sharpe (not DSR/PSR). Section 4 F-AXIS #3 OOS Sharpe is informational only. No granularity-mismatched Sharpe is plugged into psr()/dsr() in this iteration's verdict path.
- **A13 (report read-before-write)**: dispatch block at `run_baseline_v1.py:9059-9087` writes `specialist_dispersion.csv` BEFORE the post-report comparison.csv append; comparison.csv append happens after `generate_iteration_reports()`. Order verified by line-number sequencing.

All 13 anti-pattern signatures return zero unexplained matches.

### Foundation Regression: PASS

`src/crypto_trade/strategies/ml/walk_forward.py:113` carries `train_end_ms = test_start_ms - embargo_ms  # purge labels that would peek into test`. The iter-v3/057 fix (commit `5566a69` on main; cherry-picked to v3 at `e149e9d`) is intact. QE's /076 commits (`1be3bd1` Phase 6 setup) do NOT modify `walk_forward.py`. `tests/test_lookahead_embargo.py` present and contains the 4 mandated regression tests.

### Cadence + Axis Sanity: PASS

- `phase5p5_gate.md` OVERALL: PASS (read at boot).
- Brief Section 0.6 declares **axis family: `universe`** (NEW SYMBOL universe-extension).
- Brief Section 0.6 rotation status: **VALID** under the cycle-7 per-symbol regime-specialist mandate (`feedback_v1_cycle6_per_symbol_regime_specialist_mandate.md` — axis-family rotation SUSPENDED for cycle-6+7; back-to-back `universe` mining /075 → /076 explicitly authorized).
- Prior 5 EXPLORATION families enumerated and documented (/067 universe, /072 risk-primitive, /073 feature-family, /074 risk-primitive, /075 universe).
- Wall-clock budget: 2h EXPLORATION cap declared per `feedback_v1_confirmation_walltime_9h.md`.
- Kill-switch present (>2.5h wall-clock OR nan Sharpe OR FEATURES_BASE_HASH mismatch OR catastrophic NaN coverage break).

### Falsifier Presence: PASS

Brief Section 4 contains pre-registered F-AXIS bands frozen at brief commit SHA (Section 12 anchor):
- **PROMISING-CLEAN**: IS Sharpe ≥ +0.50
- **PROMISING-TENTATIVE**: +0.20 ≤ IS Sharpe < +0.50
- **NEGATIVE**: IS Sharpe < +0.20 OR IS trades < 50 (one-attempt-and-eliminate per /066 LINK + /067 LTC precedent)

Additional falsifiers hardwired:
- **F-AXIS-FALSIFIER #1** (per-direction Sharpe): long-bias mirage downgrade (>70% long trades + long Sharpe > short Sharpe + 1.5σ → NEGATIVE-LONG-BIAS-MIRAGE)
- **F-AXIS-FALSIFIER #2** (AAVE/ETH prediction correlation): corr ≥ 0.50 OR eth_* family top-3 importance → SPECIALIST-PROMISING-but-BUNDLE-CONTESTED
- **F-AXIS-FALSIFIER #3** (feature importance signature)
- **F-AXIS-BEHAVIORAL** (trade-count floor 50 IS HARD)
- **F-AXIS #2** σ_pop cross-seed dispersion (≤0.30 LM modal; >0.40 METHODOLOGY-NEGATIVE)

Section 7 enumerates 7 hard anti-tuning conditions including no post-Phase-7 band re-tuning, no methodology constant change, no EDA re-run with different IS-window definition.

---

## Implementation Verification

QE src/ diff audit (commits `1be3bd1` Phase 6 setup + Phase 6.0 setup additions):

| Item | Location | Status |
|---|---|---|
| `V1_ITER076_UNIVERSE = ("AAVEUSDT",)` | `src/crypto_trade/features_v1/__init__.py:670` | PRESENT |
| `V1_ITER076_UNIVERSE` in `__all__` | `src/crypto_trade/features_v1/__init__.py:892` | PRESENT |
| Dispatch branch `elif iteration_label == "v1-076"` | `run_baseline_v1.py:7455` | PRESENT |
| Universe assertion `set(symbols) == {"AAVEUSDT"}` | `run_baseline_v1.py:7500` | PRESENT |
| Feature count assertion `len(active_feature_columns) == 48` | `run_baseline_v1.py:7503` | PRESENT |
| `BacktestConfig(symbols=("AAVEUSDT",))` | `run_baseline_v1.py:7527-7549` | PRESENT |
| ATR cell `atr_tp_multiplier=2.9, atr_sl_multiplier=1.45` | `run_baseline_v1.py:7560-7561` | PRESENT |
| `specialist_mode=True` | `run_baseline_v1.py:7571` | PRESENT |
| `bounds_profile="v1_specialist"` | `run_baseline_v1.py:7570` | PRESENT |
| `specialist_n_startup_trials=10` | `run_baseline_v1.py:7572` | PRESENT |
| `specialist_n_estimators_max=500` | `run_baseline_v1.py:7573` | PRESENT |
| `ood_enabled=True`, `ood_cutoff_pct=0.70` | `run_baseline_v1.py:7566-7568` | PRESENT |
| `feature_columns=active_feature_columns` (48 cols) | `run_baseline_v1.py:7565` | PRESENT |
| Cohort isolation post-assertion | `run_baseline_v1.py:7587-7593` | PRESENT |
| Specialist dispersion CSV persistence | `run_baseline_v1.py:7595-7612` | PRESENT |
| Post-report block (comparison.csv append + OOS dispersion) | `run_baseline_v1.py:9054-9087` | PRESENT |
| Runner pre-flight hash guard | `run_iteration_076.py:141, 157-176` | PRESENT |
| Runner pre-flight seed assertions | `run_iteration_076.py:250-268` | PRESENT |
| `tests/test_iteration_v1_076.py` | tests dir | PRESENT (Phase 5.5 gate notes 18/18 PASS) |

`run_iteration_076.py:312-326` injects argv as `["--exploration", "--iteration", "76", "--n-trials", "30", "--ensemble-size", "1", "--symbols", "AAVEUSDT", "--pruned-features", "--seeds", "1"]`. The `--pruned-features` flag selects the 48-col `V1_FEATURE_COLUMNS_PRUNED` stack; `--seeds 1` is the outer ply (single outer seed=42), specialist_mode internally fans out to 50 inner seeds.

---

## Methodology Constants UNCHANGED Verification

| Constant | Required | Observed | Status |
|---|---|---|---|
| `V1_SPECIALIST_SEED_COUNT` | 50 | `lgbm.py:106` = 50 | PASS |
| `V1_SPECIALIST_OPTUNA_TRIALS` | 30 | `lgbm.py:109` = 30 | PASS |
| `V1_SPECIALIST_SEEDS[0]` | 42 | `lgbm.py:112` = `tuple(range(42, 92))[0]` = 42 | PASS |
| `V1_SPECIALIST_SEEDS[-1]` | 91 | `tuple(range(42, 92))[-1]` = 91 | PASS |
| `specialist_mode` | True | `run_baseline_v1.py:7571` = True | PASS |
| `atr_tp_multiplier` | 2.9 | `run_baseline_v1.py:7560` = 2.9 | PASS |
| `atr_sl_multiplier` | 1.45 | `run_baseline_v1.py:7561` = 1.45 | PASS |
| `n_estimators` upper bound | ≤ 500 | `specialist_n_estimators_max=500` | PASS |
| `n_startup_trials` | 10 | `specialist_n_startup_trials=10` | PASS |
| `max_depth` | 5 FIXED | `bounds_profile="v1_specialist"` enforces | PASS |
| `num_leaves` | 31 FIXED | `bounds_profile="v1_specialist"` enforces | PASS |
| Feature count | 48 | dispatch asserts `len(active_feature_columns) == 48` | PASS |
| Feature hash | `b81176f8…` | runner `_verify_features_hash` guard at entry | PASS |
| R3 cutoff | 0.70 | `ood_cutoff_pct=0.70` | PASS |
| R3 shared OOD features | 16 SI | `ood_features=list(V1_OOD_FEATURE_COLUMNS)` | PASS |
| R5 vt_target_vol | 0.3 (= 4.0 pct) | `r5_vol_target_pct=4.0` default | PASS |
| R5 vt_lookback_days | 45 | inherited from BacktestConfig defaults | PASS |
| training_months | 24 | `LightGbmStrategy(training_months=24)` line 7551 | PASS |
| Walk-forward embargo | `train_end_ms = test_start_ms - embargo_ms` | `walk_forward.py:113` | PASS |
| Aggregator | mean-of-signed-weights | inherited from /063 specialist_mode path | PASS |

All methodology constants byte-identical to /075 dispatch except for the single-bit `SYMBOLS` and `ITERATION_LABEL` changes (ATR cell + wrapper match /075 byte-identically — both Model A ETH-class).

---

## R1 NOT Enabled Verification

`run_baseline_v1.py:7542-7543`:
```
risk_consecutive_sl_limit=0,  # R1=OFF: CATALOG-CLOSED for SPECIALIST_mode
risk_consecutive_sl_cooldown_candles=0,
```

R1 is OFF (CATALOG-CLOSED for SPECIALIST_mode per `f81cafc3`; Model A pattern matching /064 ETH, /065 BTC, /075 ATOM). `risk_consecutive_sl_limit=0` and `risk_consecutive_sl_cooldown_candles=0` are both zero — the wrapper short-circuits the consecutive-SL streak path. R2 also OFF (`risk_drawdown_scale_enabled=False` at line 7544). R3 ON at aggregator level (`ood_enabled=True`, `ood_cutoff_pct=0.70`). R5 ON (vol-targeting at default 4.0% / 45-day lookback).

Verified consistent with brief Section 5.2 Model A risk wrapper table.

---

## Forensic Observations

1. **NEW SYMBOL — engine.py parity is N/A at EXPLORATION**. Brief Section 11 pre-commits to the parity surface at BUNDLE-002 assembly time only. `engine.py:_initial_setup` does not yet include AAVEUSDT in its kline-fetch list. This is **acceptable for /076 EXPLORATION** because /076 runs only the backtest validation surface; no `engine.py:_tick` change is required. The Critic Check 15 = `BUNDLE-PARITY-VIOLATION` becomes a HARD BLOCK at BUNDLE-002 assembly if AAVE is included AND engine wiring not present. Pre-registered for future Critic reviews at BUNDLE-002 setup.

2. **Two SYMBOL-conditional ALL-NaN-IS features retained**. `dot_vs_btc_ret_ratio_30` and `eth_vs_btc_ret_ratio_30` are ALL-NaN for AAVE by construction (these features are populated only for SYMBOL=DOT and SYMBOL=ETH respectively in V1 feature-generation code). LightGBM handles NaN natively (`use_missing=True` default). Cost: 4.2% of `colsample_bytree` slots = wasted slots. Brief Section 2.9 accepts this as a logged future-refactor item; NOT a /076 blocker.

3. **Partial-NaN features**: `long_short_zscore_30` (~43% IS NaN) and `oi_delta_30_z90` (~34% IS NaN) reflect mid-window data-source start for AAVE (~mid-2024). LightGBM NaN-handles; adjustment ≈ −0.02 IS Sharpe per Section 2.9 NaN-tax.

4. **ETH return correlation 0.75 IS / 0.80 OOS** is the LOAD-BEARING risk flagged in the user prompt and hardwired as F-AXIS-FALSIFIER #2. AAVE's specialist signal will be partially ETH-leakage; the residual signal is what matters for BUNDLE-002 inclusion. Phase 7.4 must produce rolling-90day corr(AAVE_pred, ETH_pred) and eth_* family importance rank. **This is a verdict-modifier at Phase 7.5, not a /076 EXPLORATION blocker at Phase 6.0.**

5. **Bull-IS / bear-OOS regime inversion** (Section 2.8 — IS 2023+2024+2025-Q1 cumulative return ≈ +13× compounded; OOS structurally bear) is the modal FAILURE-mode prediction per LM Master Risk Flag 2. Long-bias memorization fingerprint must be reported in Phase 7.4. **This is a verdict-modifier at Phase 7.5, not a /076 EXPLORATION blocker at Phase 6.0.**

6. **NEW SYMBOL strike rule (one-attempt-and-eliminate)** is pre-registered per /066 LINK + /067 LTC precedent. If /076 verdicts NEGATIVE, AAVE is dropped from the BUNDLE-002 candidate roster after this single EXPLORATION; mining axis pivots to rank-3 candidate (non-DeFi narrative cluster per LM Saturation Risk 1).

7. **`V1_ITER077_UNIVERSE` already declared** in `features_v1/__init__.py:893` — this is QE's forward-prep for the next mining candidate and does NOT affect /076 dispatch (the /076 branch fires on `iteration_label == "v1-076"` only). Acceptable forward-staging.

8. **Single-bit discipline preserved**: ATR cell shifted /063's (3.5, 1.75) → /064's (2.9, 1.45) per Section 1 H1b's vol-class match rationale. This is structurally a 2-bit change vs /063 (`SYMBOLS` + ATR cell), but per Section 3.1 it is a single-bit change vs the /075 dispatch (which also used ATR (2.9, 1.45)). The brief explicitly anchors to /075 as the dispatch precedent, NOT /063. This is methodology-compliant: the ATR cell choice is the Model A vol-class match (ETH ~70%, ATOM ~80%, AAVE ~95%, DOT ~110%), and AAVE sits in the Model A band consistent with /064/065/075. No second-knob confound.

---

## Path Forward

OVERALL=PASS — no Path Forward required. Backtest launch authorized.
