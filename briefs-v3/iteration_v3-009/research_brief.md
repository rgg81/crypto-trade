# Iteration v3-009 — Research Brief

**Type**: EXPLORATION (SECOND EXPLORATION under the cadence discipline; FIRST EXPLORATION post-iter-v3/008-abort)
**Track**: v3 (rigor arm) — ninth iteration
**Branch**: `iteration-v3/009` (off `iteration-v3/008` head; setup commit `56b8f8b` already dropped `vwap_dev_50`; analysis commit `565e0ec` ships before this brief)
**Date**: 2026-05-06
**Author**: QR (autopilot)

---

## Section 0 — Data Split Declaration

```
OOS_CUTOFF_DATE  = 2025-03-24    # IMMUTABLE (shared across v1, v2, v3)
training_months  = 24             # IMMUTABLE
ENSEMBLE_SIZE    = 1              # SET BY --exploration
ensemble_seeds   = _derive_ensemble_seeds(outer_seed, size=1)
n_trials         = 10             # SET BY --exploration default
colsample_bytree = 1.0             # HARDCODED by --exploration
OOS_CUTOFF_MS    = 1742774400000   # millisecond representation
```

**Sacred constants UNCHANGED.** The `--exploration` flag (SHA `bce50c8`) does NOT touch `OOS_CUTOFF_DATE` or `training_months`. The QR sees OOS metrics for the FIRST time in Phase 7. This brief is produced reading ONLY: iter-v3/007 + iter-v3/008 briefs / engineering reports / Critic / diaries; iter-v3/007 `ic_matrix.csv` (IS-only); the iter-v3/009 analysis script `analysis/iteration_v3-009/top_13_validation.py` outputs (committed at SHA `565e0ec` BEFORE this brief).

---

## Section 0.5 — Iteration Type Declaration

```
TYPE: EXPLORATION
Wall-clock budget: < 30 min (well under the 2h hard cap)
Single-axis variation: features (top-13 vs iter-v3/007's top-14; one feature
                       dropped: vwap_dev_50)
Cadence: EXPLORATION #2 of 10 needed before CONFIRMATION can launch
         (catalog: briefs-v3/exploration_catalog.md has iter-v3/007 as #1)
This iteration NEVER updates BASELINE_V3.md.
```

**Justification**: Per cadence discipline (skill SHA `d5c9f21`), CONFIRMATION cannot launch with fewer than 10 EXPLORATION rows since the last CONFIRMATION. iter-v3/008 was aborted at 4h 15min (extrapolated to ~25h, infeasible); the abort triggered the cadence discipline and DID NOT enter the catalog. iter-v3/007 is the only catalog row. iter-v3/009 re-tests the iter-v3/008 hypothesis (top-13) AT EXPLORATION COST (~10-15 min), banking the empirical result as the second catalog row.

---

## Section 1 — Hypothesis

Dropping `vwap_dev_50` (which had IC=0.875 with `ema_spread_atr_20` AND IC=0.794 with `vwap_dev_20` per iter-v3/007's matrix) from `V3_FEATURE_COLUMNS` reducing it from 14 to 13 features will produce IS Sharpe ≥ +0.20 (i.e., maintain iter-v3/007's +0.2241 baseline within ±0.05) under the same `--exploration --seeds 1 --n-trials 10` config on the full v3 universe (BCH+MKR+LDO+TRX), confirming that `vwap_dev_50`'s contribution was indeed redundant with retained features rather than independent signal.

---

## Section 2 — IS-Only Numerical Evidence

**Analysis script**: `analysis/iteration_v3-009/top_13_validation.py` (committed at SHA `565e0ec` BEFORE this brief — Phase 5.5 reproducibility requirement).

**Inputs read** (all IS-only):
- `reports-v3/iteration_v3-007/ic_matrix.csv` — 14×14 IC matrix from iter-v3/007 EXPLORATION (full v3 universe, top-14, single seed=42, computed inside the walk-forward loop with `close_time < OOS_CUTOFF_DATE = 2025-03-24`). NO OOS contact.
- `reports-v3/iteration_v3-007/in_sample/feature_importance.csv` — IS-only iter-v3/007 importance.

**Outputs** (committed alongside the script at SHA `565e0ec`):
- `analysis/iteration_v3-009/top_13_features.csv` — 13 retained features with iter-v3/007 IS importance + rank.
- `analysis/iteration_v3-009/synthesis.md` — 1-paragraph narrative.

### 2.1 Reused evidence — iter-v3/008 already verified the IC redundancy drop

iter-v3/008's analysis script (`analysis/iteration_v3-008/ic_redundancy_drop_demo.py`, SHA `003a21e`) established the following (re-verified at runtime by `top_13_validation.py`):

| Quantity | Value | Source |
|---|---:|---|
| iter-v3/007 IS Sharpe at top-14 | **+0.2241** | reports-v3/iteration_v3-007/comparison.csv |
| Pairs |IC| ≥ 0.7 in 14-feature matrix | **2** | iter-v3/008 SHA `003a21e` |
| Both pairs share | `vwap_dev_50` | iter-v3/008 SHA `003a21e` |
| Pairs |IC| ≥ 0.7 in 13-feature subset | **0** | iter-v3/009 SHA `565e0ec` (re-verified) |
| Max residual |IC| in 13-feature subset | **0.6602** (`max_dd_window_50` × `range_realized_vol_50`, NEGATIVE rho) | iter-v3/009 SHA `565e0ec` |
| Headroom to threshold | **+0.0398** | iter-v3/009 SHA `565e0ec` |

This is reused evidence — no new statistics computed. iter-v3/009 is a VALIDATION rerun, not a discovery iteration.

### 2.2 13 retained features (iter-v3/007 IS rank)

Features as ordered in iter-v3/007's IS importance (rank 1 = highest importance). Rank 2 = `vwap_dev_50` is correctly absent.

| pos | feature | iter-v3/007 imp | iter-v3/007 IS rank |
|---:|---|---:|---:|
| 1 | `ret_skew_200` | 408.0 | 1 |
| 2 | `range_realized_vol_50` | 321.0 | 3 |
| 3 | `ema_spread_atr_20` | 318.0 | 4 |
| 4 | `ret_autocorr_lag1_50` | 292.0 | 5 |
| 5 | `max_dd_window_50` | 242.0 | 6 |
| 6 | `ret_kurt_200` | 237.0 | 7 |
| 7 | `hurst_100` | 236.0 | 8 |
| 8 | `ret_kurt_50` | 219.0 | 9 |
| 9 | `vwap_dev_20` | 201.0 | 10 |
| 10 | `btc_ret_14d` | 195.0 | 11 |
| 11 | `hurst_diff_100_50` | 172.0 | 12 |
| 12 | `ret_skew_50` | 168.0 | 13 |
| 13 | `sym_vs_btc_ret_7d` | 159.0 | 14 |

The dropped feature (`vwap_dev_50`, rank 2 by importance) was the highest-ranked DROP candidate — the test is whether its observed IS importance reflects independent signal or merely redundancy with `ema_spread_atr_20` (rank 4 retained) and `vwap_dev_20` (rank 10 retained).

### 2.3 Setup integrity (verified at SHA `565e0ec`)

```
V3_FEATURE_COLUMNS_len      = 13         PASS
'vwap_dev_50' in V3_FEATURE = False      PASS
pairs_above_threshold       = 0          PASS
max_residual_abs_ic         = 0.6602     PASS (<0.7)
```

---

## Section 3 — Proposed Changes

### 3.1 Symbols — UNCHANGED (full v3 universe)

| Symbol | Status | Rationale |
|---|---|---|
| BCHUSDT | KEEP | Full v3 universe (iter-v3/007 baseline). |
| MKRUSDT | KEEP | Same. |
| LDOUSDT | KEEP | Same. |
| TRXUSDT | KEEP | Same. |

`set({BCH, MKR, LDO, TRX}) ∩ V3_EXCLUDED_SYMBOLS = ∅` ✓

### 3.2 Labeling — UNCHANGED

Inherited from iter-v3/001-008:
- Triple-barrier: `tp = 2.9 × NATR_21`, `sl = 1.45 × NATR_21`
- Timeout: 7 days = 21 candles at 8h
- σ_t: past-only ATR
- Purge gap: `gap = 22 × 4 = 88` (REQUIRED_GAP=88)

### 3.3 Features — 13 (already set in V3_FEATURE_COLUMNS via iter-v3/008 SHA `56b8f8b`)

Imports at runtime:

```python
V3_FEATURE_COLUMNS = (
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
)  # length = 13, vwap_dev_50 dropped
```

**No new code changes required**. iter-v3/008's setup commit (`56b8f8b`) already shipped:
- Drop `vwap_dev_50` from `V3_FEATURE_COLUMNS_TOP_N` in `src/crypto_trade/features_v3/__init__.py`
- Update `_verify_feature_columns()` to assert `n != 13` in `run_baseline_v3.py`
- Parametrize the runtime banner against `len(V3_FEATURE_COLUMNS)`

The iteration-v3/009 branch was branched from iteration-v3/008 head, inheriting all of these.

### 3.4 Risk gates — UNCHANGED

Same 7-primitive table as iter-v3/006-008 (see Section 6). The dropped `vwap_dev_50` is NOT a gate input — gates use `atr_pct_rank_200`, `hurst_100`, ADX-from-OHLC, and the z-score OOD set.

### 3.5 Sub-fix — engineer's only job is updating ITERATION_LABEL + committing

| # | Sub-fix | Spec | Verifier |
|---|---|---|---|
| 1 | **Update `ITERATION_LABEL` to `"v3-009"`** in `run_baseline_v3.py` | One-line change. iter-v3/008 commit `56b8f8b` set it to `"v3-008"`; iter-v3/009 must change to `"v3-009"`. | `grep -E 'ITERATION_LABEL.*=.*"v3-009"' run_baseline_v3.py` exits 0 |
| 2 | **Commit the runner with that change** | `feat(iter-v3/009): ITERATION_LABEL=v3-009` | `git log --oneline iteration-v3/009 -- run_baseline_v3.py | head -1` shows the iter-v3/009 SHA |
| 3 | **Run `--exploration --seeds 1 --n-trials 10`** on full 4-symbol universe | Phase 6 invocation: `uv run python run_baseline_v3.py --exploration --seeds 1 --n-trials 10` (no `--symbols` flag → all 4 V3_MODELS). Wall-clock target: < 30 min (hard cap 2h per cadence rule). | `test -f reports-v3/iteration_v3-009/comparison.csv` |

NO new src/ code changes beyond `ITERATION_LABEL`. NO test additions.

### 3.6 Brief-vs-Code reconciliation table (Phase 5.5 input)

Each row maps to a FILE ARTIFACT with an executable verifier command. Empty cells = Phase 5.5 BLOCK.

| # | Sub-fix | Code path | File artifact + verifier |
|---|---|---|---|
| 1 | V3_FEATURE_COLUMNS at 13 features (inherited setup) | `src/crypto_trade/features_v3/__init__.py` | `python -c "from crypto_trade.features_v3 import V3_FEATURE_COLUMNS; assert len(V3_FEATURE_COLUMNS) == 13, f'len={len(V3_FEATURE_COLUMNS)}'"` exits 0 |
| 2 | `vwap_dev_50` dropped (inherited setup) | `src/crypto_trade/features_v3/__init__.py` | `python -c "from crypto_trade.features_v3 import V3_FEATURE_COLUMNS; assert 'vwap_dev_50' not in V3_FEATURE_COLUMNS"` exits 0 |
| 3 | `ITERATION_LABEL` updated to `"v3-009"` | `run_baseline_v3.py` | `grep -E 'ITERATION_LABEL.*=.*"v3-009"' run_baseline_v3.py` exits 0 |
| 4 | Sub-fix #3 produces comparison.csv | runner | `test -f reports-v3/iteration_v3-009/comparison.csv` |
| 5 | **EXPLORATION central test**: IS monthly Sharpe > 0 (signal direction maintained) | runner | `python -c "import pandas as pd; df=pd.read_csv('reports-v3/iteration_v3-009/comparison.csv'); ms = df.loc[df['metric']=='monthly_sharpe','in_sample'].iloc[0]; assert float(ms) > 0, f'IS sharpe non-positive: {ms}'"` exits 0 |
| 6 | All 35 adversarial tests pass | tests | `uv run pytest tests/strategies/ml/ -v` exits 0 |
| 7 | Wall-clock ceiling: total Phase 6 runtime < 30 min target / 2h hard cap | engineering report | `python -c "import json; d=json.load(open('briefs-v3/iteration_v3-009/engineering_report_summary.json')); assert d['wall_clock_minutes'] < 120, f'minutes={d[\"wall_clock_minutes\"]}'"` exits 0 |
| 8 | Full v3 universe used (4 symbols, no --symbols filter) | runner invocation log | `grep -E "Active models: 4/4" reports-v3/iteration_v3-009/run.log` exits 0 |
| 9 | `--exploration` flag was active | runner invocation log | `grep -E "exploration|colsample.*1\.0|ENSEMBLE_SIZE.*1" reports-v3/iteration_v3-009/run.log` exits 0 |
| 10 | `pareto_front.csv` has ≥1 row | runner | `python -c "import pandas as pd; df=pd.read_csv('reports-v3/iteration_v3-009/pareto_front.csv'); assert len(df) >= 1, f'rows={len(df)}'"` exits 0 |

### 3.7 NO new feature additions, NO labeling changes, NO universe change

iter-v3/009 is a single-axis (features) VALIDATION EXPLORATION. The model architecture, label scheme, risk gates, CPCV parameters, and walk-forward window are byte-for-byte unchanged from iter-v3/007. The only difference vs iter-v3/007: `vwap_dev_50` dropped (single-feature variation along the features axis).

### 3.8 Inheritance from iter-v3/008

The `iteration-v3/009` branch was branched from `iteration-v3/008` head. Inherited commits:

- `bce50c8 feat(iter-v3/007): --exploration mode` (CLI flag plumbing)
- `92218ef feat(iter-v3/007): top-14 V3_FEATURE_COLUMNS subset + ITERATION_LABEL=v3-007`
- `849c4a6 fix(iter-v3/007): risk_v3 always loads atr_pct_rank_200 from parquet`
- `56b8f8b feat(iter-v3/008): drop vwap_dev_50 (14→13 features) + ITERATION_LABEL + banner fix`
- `565e0ec feat(iter-v3/009): top-13 validation analysis` (this brief's evidence)

Critical inheritance verifiers (run before any code edits in Phase 6):
- `python -c "from crypto_trade.features_v3 import V3_FEATURE_COLUMNS; assert len(V3_FEATURE_COLUMNS) == 13 and 'vwap_dev_50' not in V3_FEATURE_COLUMNS"` exits 0
- `uv run pytest tests/strategies/ml/ -v` exits 0 with 35/35 PASS

---

## Section 4 — Expected OOS Impact

### 4.1 EXPLORATION → headline metrics are GUIDANCE not GATES

Per Section 0.5 + skill spec at SHA `f0f8b84`, headline metrics are NOT BLOCK-triggering for the Critic on EXPLORATION iterations. The Critic emits `EXPLORATION-PROMISING`, `EXPLORATION-NEGATIVE`, or `BLOCK` (process). iter-v3/009 NEVER updates BASELINE_V3.md regardless of verdict.

### 4.2 Predicted IS Sharpe range

| Metric | iter-v3/007 (top-14, exploration) | iter-v3/009 prediction (top-13, exploration) |
|---|---:|---:|
| IS monthly Sharpe | +0.2241 | **predicted [+0.18, +0.28] with median +0.22** |
| Phase 6 wall-clock | 8 min | predicted 10-15 min, hard cap 2h |

The prediction band is essentially iter-v3/007's +0.22 ± 0.05 — a tight band reflecting the hypothesis that the dropped feature was redundant rather than independent signal.

### 4.3 Falsifiers (locked before backtest)

**Falsifier 1**: IS Sharpe < +0.10 → `vwap_dev_50` was actually contributing independent signal (not redundant with `ema_spread_atr_20` / `vwap_dev_20`). Verdict: EXPLORATION-NEGATIVE on this axis. Catalog this finding; iter-v3/010 tests a DIFFERENT axis (e.g., labeling timeout, risk gate threshold).

**Falsifier 2**: IS Sharpe > +0.40 → dropping the redundancy materially improved the model unexpectedly. Verdict: EXPLORATION-PROMISING with surprise; iter-v3/010 might re-investigate why colsample=1.0 + smaller redundant feature set helps so much.

**Falsifier 3** (process): Phase 6 wall-clock > 30 min on full v3 universe at exploration config → `--exploration` slowdown reproduces; engineer documents the cause; future EXPLORATION iterations re-scope.

**Process falsifier**: pre-flight `len(V3_FEATURE_COLUMNS) == 13 AND 'vwap_dev_50' not in V3_FEATURE_COLUMNS` returns False → setup drift; Phase 6 must not start.

### 4.4 EXPLORATION outcome interpretation

| Critic verdict | Meaning | Next iteration |
|---|---|---|
| `EXPLORATION-PROMISING` | IS Sharpe inside [+0.18, +0.28] band — redundancy hypothesis confirmed at exploration cost | iter-v3/010 EXPLORATION on a DIFFERENT axis (labeling, risk gates, BTC trend filter threshold, etc.) |
| `EXPLORATION-NEGATIVE` | IS Sharpe < +0.10 — `vwap_dev_50` had real signal | iter-v3/010 EXPLORATION on a DIFFERENT axis OR re-test top-14 with different EXPLORATION config (e.g., colsample<1.0) |
| `BLOCK` (process) | Methodology check FAILED unexpectedly | Diary documents, iter-v3/010 fixes the methodology gap |

---

## Section 5 — Risk Mitigation

### 5.1 Cadence-discipline structural safeguards

iter-v3/009 inherits THREE structural safeguards from the cadence skill:

1. **2h wall-clock hard cap** (skill SHA `d5c9f21`): Engineer kills Phase 6 if elapsed > 2h, regardless of progress. This automatically prevents the iter-v3/008 abort pattern from recurring.
2. **Single-axis variation rule** honored (only features changed; iter-v3/008's setup commit `56b8f8b` already made the code change; iter-v3/009 only updates `ITERATION_LABEL`).
3. **EXPLORATION never updates BASELINE_V3.md** — outcome (PROMISING / NEGATIVE / BLOCK) records only in `briefs-v3/exploration_catalog.md` and `diary-v3/iteration_v3-009.md`.

### 5.2 Methodology-pipeline safety (inherited from iter-v3/006-008)

1. **35 adversarial unit tests** must PASS before backtest.
2. **File-artifact reconciliation table** (§3.6). 10 verifier commands; empty cells = Phase 5.5 BLOCK.
3. **Pre-flight len + name check** on `V3_FEATURE_COLUMNS`: catches the case where `56b8f8b` was silently lost during a rebase or merge.

### 5.3 NO new model-level risks introduced

The iter-v3/009 changes:
- ZERO new code (only `ITERATION_LABEL` cosmetic update).
- ZERO new features.
- ZERO new dropped features (the drop was made in iter-v3/008's setup commit `56b8f8b`).
- ZERO label / risk gate / CPCV changes.

The only risk is process drift — the inheritance from iter-v3/008 not propagating cleanly. Mitigated by the pre-flight check above.

---

## Section 6 — Risk Management Design

### 6.1 7-primitive table — IDENTICAL TO iter-v3/006-008

| # | Primitive | Spec | Fire-rate prediction (IS) | Regime coverage |
|---|---|---|---|---|
| 1 | Vol scaling | `scale = clip(atr_pct_rank_200, 0.3, 1.0)` | Always on; mean scale ≈ 0.6 | High-vol → scale down |
| 2 | ADX gate | trade only when ADX > 20 | ≈ 60% of bars pass | Trending only |
| 3 | Hurst regime check | trade only when 0.05 < hurst_100 < 0.95 | ≈ 90% of bars pass | Filters bond-like regimes |
| 4 | Feature z-score OOD | kill if any \|z\| > 2.5 | ≈ 5–8% killed | Distributional drift |
| 5 | Low-vol filter | trade only when atr_pct_rank_200 ≥ 0.33 | ≈ 67% of bars pass | Filters dead chop |
| 6 | Hit-rate feedback | DISABLED | 0% | Reserved for future tuning |
| 7 | BTC trend alignment | kill alt trade fighting BTC 14d ±20% | ≈ 7–8% killed | Macro flips |

Combined kill rate target: 69–78%. SAME as iter-v3/006-008.

**Gate-vs-feature-column independence**: gates read from the parquet feature DataFrame (where all 34 features remain computed), not from `V3_FEATURE_COLUMNS`. The risk_v3 fix at SHA `849c4a6` (iter-v3/007) explicitly adds `"atr_pct_rank_200"` to `risk_v3.py:_build_lookups()` `needed` list independently of `V3_FEATURE_COLUMNS`. The dropped `vwap_dev_50` is NOT a gate input.

### 6.2 Regime coverage — UNCHANGED

Full v3 universe IS data spans 2022-09-24 → 2025-03-23. Regime coverage includes 2022 LUNA/FTX, 2023 banking, 2024 halving + Trump rally, 2025 January correction.

### 6.3 Concentration — informational only under EXPLORATION

iter-v3/007 OOS showed BCH 84.44% concentration (single-seed, small total OOS PnL). Concentration is NOT a gate for iter-v3/009 per TYPE=EXPLORATION; it is informational only.

---

## Section 7 — Pre-Registered Failure-Mode Prediction

iter-v3/004's 5/5 calibration win, iter-v3/006's 5/5 win, and iter-v3/007's 2/5 partial-win establish the discipline. iter-v3/009 inherits and refines.

**Prediction P1 (process, P=5%)**: the iter-v3/008 setup commit (`56b8f8b`) didn't propagate cleanly to the iteration-v3/009 branch (e.g., a rebase silently reverted the drop, or a downstream test fixture asserts 14). **Detection signal**: pre-flight `python -c "from crypto_trade.features_v3 import V3_FEATURE_COLUMNS; assert len(V3_FEATURE_COLUMNS) == 13"` raises OR `_verify_feature_columns()` raises OR the test suite fails. **Mitigation**: pre-flight len check + grep for `'vwap_dev_50'` not in cols. Phase 6 must abort if either fails.

**Prediction P2 (process, P=5%)**: wall-clock overshoots 30 min on full v3 universe at exploration config. iter-v3/007 ran in 8 min on the same config + same 4 symbols + 14 features; the 13-feature variation should be at most marginally faster (1 fewer LightGBM column + 1 fewer feature_importance row). **Detection signal**: total Phase 6 wall-clock > 30 min on full universe. **Mitigation**: 2h hard cap (cadence rule). Engineer kills if exceeded; iter-v3/010 EXPLORATION re-scopes.

**Prediction P3 (process, P=10%)**: iter-v3/007's `--exploration` config produced a `feature_importance.csv` ordering that may not generalize to iter-v3/009's slightly different feature set; the importance signal could be different but that is SECONDARY to the IS Sharpe outcome. **Detection signal**: iter-v3/009 importance ranks for the 13 retained features differ materially from iter-v3/007's (e.g., `range_realized_vol_50` shifts from rank 3 to rank 11). **Mitigation**: Section 8's central test is IS Sharpe direction maintained, not importance stability. Documented in diary.

**Prediction P4 (model, P=60%)**: IS Sharpe lands in [+0.18, +0.28] (predicted band). EXPLORATION-PROMISING. Confirms iter-v3/008's hypothesis at exploration cost. The redundancy-drop maintains the signal because `vwap_dev_50`'s contribution was indeed correlated with `ema_spread_atr_20` (IC 0.875) and `vwap_dev_20` (IC 0.794) rather than independent.

**Prediction P5 (model, P=15%)**: IS Sharpe drops to [+0.10, +0.18] — `vwap_dev_50` had a small but real contribution that was being absorbed into the high-IC pairs but contributed marginal independent gain to the model. EXPLORATION-NEGATIVE on this axis; iter-v3/010 tries a different feature variation (e.g., re-introduce `vwap_dev_50`, drop a different feature) OR pivots to a non-features axis.

**Prediction P6 (model, P=10%)**: IS Sharpe rises to >+0.30 — dropping redundancy unexpectedly helped under colsample=1.0 (every tree split sees ALL features; redundant pairs steal effective gain estimation). EXPLORATION-PROMISING with surprise; iter-v3/010 might investigate the redundancy-amplification effect under exploration config.

The predictions are intentionally Bayesian-calibrated:
- 3 process-level (P1, P2, P3) per iter-v3/003 lesson #3 discipline
- 3 model-level (P4, P5, P6) covering predicted-band, undershoot, overshoot

Summary: **EXPLORATION-PROMISING pathway probability ≈ 70%** (P4 + P6); EXPLORATION-NEGATIVE ≈ 15% (P5); process abort ≈ 15% (P1+P2+P3).

If any prediction fails to materialize, the iter-v3/009 diary documents the calibration miss.

---

## Section 8 — Pre-Registered EXPLORATION Criteria

**These thresholds are LOCKED before backtest. Phase 7 evaluation applies them mechanically.**

iter-v3/009 is an **EXPLORATION iteration** per Section 0.5. Headline-metric criteria from CONFIRMATION iterations (DSR > 0.95, PSR > 0.95, OOS Sharpe > 1.0) are NOT in scope. Critic emits `EXPLORATION-PROMISING`, `EXPLORATION-NEGATIVE`, or `BLOCK`.

### EXPLORATION-PROMISING iff ALL 10 of the following are true:

| # | Criterion | Threshold | Source |
|---|---|---:|---|
| 1 | TYPE=EXPLORATION declared in Section 0.5 | TRUE | §0.5 |
| 2 | Single-axis variation only (features) | TRUE | §3.7 |
| 3 | Wall-clock < 2h (target < 30 min) | TRUE | §3.6 row 7 |
| 4 | `--exploration --seeds 1 --n-trials 10` used | TRUE | §3.6 row 9 |
| 5 | 35/35 adversarial tests pass | TRUE | §3.6 row 6 |
| 6 | `len(V3_FEATURE_COLUMNS) == 13` confirmed at runtime | TRUE | §3.6 row 1 |
| 7 | `comparison.csv` produced (basic headline metrics) | TRUE | §3.6 row 4 |
| 8 | Critic OVERALL = `EXPLORATION-PROMISING` or `EXPLORATION-NEGATIVE` (NOT BLOCK) | enum | Phase 7.5 |
| 9 | NO 5-seed or CONFIRMATION-style runs | TRUE (vacuous; --seeds 1) | §3.7 |
| 10 | Catalog updated post-Phase-8 with iter-v3/009 row | TRUE | post-iteration mechanic |

### EXPLORATION-NEGATIVE iff:

- Criteria 1-7, 9, 10 PASS BUT Critic OVERALL = `EXPLORATION-NEGATIVE` (because IS Sharpe < +0.10, falsifier 1)

### BLOCK (process) iff ANY of:

- Criteria 1-7, 9 fail (process-level)
- Phase 5.5 gate emits BLOCK
- Phase 7.5 Critic emits explicit BLOCK
- Wall-clock exceeds 2h hard cap

### Discretionary judgment — EXPLORATION pathway

iter-v3/009 has NO MERGE pathway because the iteration TYPE is EXPLORATION. The "MERGE pathway" is `EXPLORATION-PROMISING`, which is a forward-pointer: it adds one row to the catalog and counts toward the 10 EXPLORATION quota. **iter-v3/009 NEVER updates BASELINE_V3.md.**

---

## Section 9 — Library Stack Declaration

| Package | Version pinned | License | Usage | Fallback |
|---|---|---|---|---|
| `numpy` | (already installed) | BSD-3 | `np.random.default_rng` for `_derive_ensemble_seeds`; column-array math | n/a |
| `scipy` | (already installed) | BSD-3 | (no use this iteration) | n/a |
| `statsmodels` | (already installed) | BSD-3 | `tsa.stattools.adfuller` (unchanged) | n/a |
| `scikit-learn` | (already installed) | BSD-3 | `TimeSeriesSplit` in `_objective` (unchanged) | n/a |
| `lightgbm` | (already installed) | MIT | M1 only — no M2 | n/a |
| `pytest` | (already installed) | MIT | 35 adversarial tests | n/a |
| `pandas` | (already installed) | BSD-3 | Parquet I/O + analysis script CSV/IC matrix loading | n/a |
| `pyarrow` | (already installed via pandas) | Apache-2 | Parquet engine (unchanged) | If missing, fastparquet |

**No new external deps.** Same stack as iter-v3/007-008. The iteration's NEW code is:
- 1 analysis script + 2 outputs (committed at SHA `565e0ec`)
- 1 cosmetic `ITERATION_LABEL` edit to `run_baseline_v3.py` (Engineer ships in Phase 6)
- 0 new pytest test files
- 0 modifications to per-cell PBO / DSR / PSR / ADF code paths

### Aggregator strategy — UNCHANGED

Per-cell PBO with cross-cell mean aggregation. Per-cell n_eff with cross-cell median aggregation.

### Reproducibility stamp

The Engineer's Phase 6 writes `briefs-v3/iteration_v3-009/engineering_report.md` with:
- The git commit SHAs at backtest time (expected: `565e0ec` analysis + the new `ITERATION_LABEL` SHA)
- Output of `uv pip list | grep -E "(numpy|scipy|statsmodels|scikit-learn|lightgbm|pytest|pandas|pyarrow)"`
- The full 13-feature list as actually trained on (sanity check against §3.3)
- The `comparison.csv` IS / OOS monthly Sharpe values
- The wall-clock minutes total (must be < 120; target < 30)
- The 35-test outcome (PASS expected)
- The `--exploration` activation banner from `run.log`
- The runner invocation literal (proof of `--exploration --seeds 1 --n-trials 10`)

---

## Appendix — Phase 5.5 Gate Self-Check

The QR has self-verified all 11 mandatory sections plus the Phase 5.5 inputs:

| Section | Status |
|---|---|
| 0 — Data Split | PASS — sacred constants UNCHANGED; ENSEMBLE_SIZE=1 / colsample=1.0 / n_trials=10 SET BY --exploration |
| 0.5 — Iteration Type Declaration | PASS — TYPE: EXPLORATION declared; cadence catalog reference; explicit "NEVER updates BASELINE_V3.md" |
| 1 — Hypothesis | PASS — one sentence; testable target IS Sharpe ≥ +0.20 (within ±0.05 of iter-v3/007 +0.2241); falsifiers in §4.3 |
| 2 — IS-Only Numerical Evidence | PASS — `analysis/iteration_v3-009/top_13_validation.py` committed at SHA `565e0ec` BEFORE this brief; reuses iter-v3/008 SHA `003a21e` IC analysis; setup integrity verified at runtime |
| 3 — Proposed Changes | PASS — symbols UNCHANGED; labeling UNCHANGED; features 13 (already set via inherited `56b8f8b`); risk gates UNCHANGED; sub-fix is single ITERATION_LABEL update; reconciliation table 10 verifiers; inheritance plan §3.8 |
| 4 — Expected OOS Impact | PASS — predicted IS Sharpe range [+0.18, +0.28]; 4 falsifiers in §4.3; EXPLORATION pathway in §4.4 |
| 5 — Risk Mitigation | PASS — 3 cadence-discipline structural safeguards in §5.1 + 3 methodology-pipeline safeguards in §5.2 |
| 6 — Risk Management Design | PASS — 7-primitive table identical to iter-v3/006-008; gate-vs-feature-column independence verified |
| 7 — Pre-Registered Failure-Mode | PASS — 6 predictions with **3 process-level (P1, P2, P3)**; calibrated PROMISING prior at ~70% |
| 8 — Pre-Registered EXPLORATION Criteria | PASS — 10 EXPLORATION criteria; EXPLORATION-PROMISING / EXPLORATION-NEGATIVE / BLOCK pathways; explicit "NEVER updates BASELINE_V3.md" |
| 9 — Library Stack | PASS — no new deps; aggregator strategy unchanged from iter-v3/006-008 |

Engineer: please run Phase 5.5 gate verification against the brief-vs-code reconciliation table in Section 3.6. Empty cells in the right column = BLOCK. Verifier commands that do NOT execute and exit 0 post-Phase 6 = NO-MERGE per Section 8.
