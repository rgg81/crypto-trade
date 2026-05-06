# Iteration v3-011 — Research Brief

**Type**: EXPLORATION (FOURTH EXPLORATION under the cadence discipline)
**Track**: v3 (rigor arm) — eleventh iteration
**Branch**: `iteration-v3/011` (off `iteration-v3/010` head; analysis commit `17d01ab` ships before this brief)
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

**Sacred constants UNCHANGED.** The `--exploration` flag (SHA `bce50c8`) does NOT touch `OOS_CUTOFF_DATE` or `training_months`. The QR sees OOS metrics for the FIRST time in Phase 7. This brief is produced reading ONLY: iter-v3/007/009/010 briefs / engineering reports / Critic / diaries; iter-v3/010 `in_sample/trades.csv` (IS-only, 357 trades); the iter-v3/011 analysis script `analysis/iteration_v3-011/zscore_threshold_demo.py` outputs (committed at SHA `17d01ab` BEFORE this brief).

---

## Section 0.5 — Iteration Type Declaration

```
TYPE: EXPLORATION
Wall-clock budget: < 30 min (2h hard cap)
Single-axis variation: risk-gate (z-score OOD threshold 2.5 → 2.0; tighter)
Cadence: EXPLORATION #4 of 10 (3 prior, last PROMISING was iter-v3/010 labeling)
This iteration NEVER updates BASELINE_V3.md.
```

**Justification**: Per cadence discipline (skill SHA `d5c9f21`), CONFIRMATION cannot launch with fewer than 10 EXPLORATION rows since the last CONFIRMATION. The catalog at `briefs-v3/exploration_catalog.md` has 3 rows (iter-v3/007 PROMISING, iter-v3/009 NEGATIVE, iter-v3/010 PROMISING); iter-v3/011 is the fourth. Per Critic FINAL Recommendation 1 on iter-v3/010 review (SHA `f6f4ef7`), iter-v3/011 must vary along the RISK-GATE axis to maximize catalog axis diversity (currently features×2, labeling×1, gate×0). After iter-v3/011: features×2, labeling×1, gate×1 — meaningful diversity for the eventual CONFIRMATION bundle.

**Direction (tighter not looser)**: 2.0 is selected over 3.0 because iter-v3/010's OOS trade-rate is 8.07/month (below the 10/month floor `feedback_trade_rate_floor`); tightening might further reduce trade rate, which stress-tests whether the floor is recoverable at CONFIRMATION's 5-seed × ensemble multiplication. iter-v3/012 may test 3.0 if needed.

---

## Section 1 — Hypothesis

Tightening the z-score OOD threshold from 2.5 to 2.0 (kills any trade where any feature in V2_FEATURE_COLUMNS exceeds 2σ from the IS-window training distribution) on top of iter-v3/010's labeling baseline (ATR 2.0/1.0) will produce IS Sharpe maintained or improved (≥ +0.40, vs iter-v3/010's +0.5683) by filtering more aggressively against feature-distribution drift, testing whether iter-v3/010's IS lift was robust to stricter gating or signal-density-dependent.

---

## Section 2 — IS-Only Numerical Evidence

**Analysis script**: `analysis/iteration_v3-011/zscore_threshold_demo.py` (committed at SHA `17d01ab` BEFORE this brief — Phase 5.5 reproducibility requirement).

**Inputs read** (all IS-only):
- `reports-v3/iteration_v3-010/in_sample/trades.csv` — 357 IS trades from the (z=2.5, ATR(2.0/1.0)) baseline. NO OOS contact.

**Outputs** (committed alongside the script at SHA `17d01ab`):
- `analysis/iteration_v3-011/expected_trade_reduction.csv` — per-symbol baseline + projected stats under two priors.
- `analysis/iteration_v3-011/synthesis.md` — 1-paragraph narrative.

### 2.1 Baseline trade-frequency stats (iter-v3/010 IS, z=2.5)

| Symbol | n_trades | trades/month | %TP | %SL | %timeout |
|---|---:|---:|---:|---:|---:|
| BCHUSDT | 124 | 4.14 | 33.1% | 59.7% | 7.3% |
| LDOUSDT | 25 | 0.84 | 40.0% | 52.0% | 8.0% |
| MKRUSDT | 101 | 3.37 | 29.7% | **66.3%** | 4.0% |
| TRXUSDT | 107 | 3.57 | 33.6% | 60.7% | 5.6% |
| **TOTAL** | **357** | — | — | — | — |

MKR has the highest SL% (66.3%) — proxy for heaviest feature-distribution tails (more volatile underlying drives both labeling outcomes and feature-distribution width). Expectation: MKR most affected by tighter gate.

### 2.2 Expected kill-rate shift at z=2.5 → z=2.0

The z-score gate fires when `max(|z_i|) > threshold` over the 34 V2_FEATURE_COLUMNS (`risk_v2.py:286`). Per-feature normal-tail probabilities:

| Threshold | P(\|z\| > t) per feature |
|---|---:|
| z=2.5 | 0.01242 |
| z=2.0 | 0.04550 |

Two priors for compound kill rate (gate fires on at least one feature exceeding):

| Prior | N_eff | kill_rate(2.5) | kill_rate(2.0) | survivor_ratio |
|---|---:|---:|---:|---:|
| **A — iid Gaussian, all 34 features** | 34 | 34.6% | 79.5% | **0.314** |
| **B — N_eff=8 realistic correlation** | 8 | 9.5% | 31.1% | **0.761** |

Prior A is the stress-test ceiling (assumes feature independence which is FALSE — V2_FEATURE_COLUMNS contains correlated families: regime hurst_100/200, atr_pct_rank_200/500, ret_skew_{50,100,200}, ret_kurt_{50,200}, parkinson_vol_20 & parkinson_gk_ratio_20, etc.). Prior B reflects realistic dimensionality after PCA-style collapse (estimated N_eff ~ 8 across regime, tail-risk, momentum, microstructure, fracdiff, BTC-cross families).

### 2.3 Expected trade-count reduction

| Symbol | baseline_n | expected_n (Prior A iid) | expected_n (Prior B realistic) |
|---|---:|---:|---:|
| BCHUSDT | 124 | 39 | 94 |
| LDOUSDT | 25 | 8 | 19 |
| MKRUSDT | 101 | 32 | 77 |
| TRXUSDT | 107 | 34 | 81 |
| **TOTAL** | **357** | **113** | **271** |

Prior B (realistic, ~76% survivor ratio) is the calibration anchor for Section 4 prediction. Actual outcome depends on ACTUAL feature-distribution shape (heavy tails compress threshold percentiles; correlated firings reduce compound kill rate).

### 2.4 Setup integrity (verified at SHA `17d01ab`)

```
trades.csv path                       = reports-v3/iteration_v3-010/in_sample/trades.csv  PASS
total IS trades read                  = 357                                                PASS
N V2_FEATURE_COLUMNS                  = 34                                                 PASS
expected_trade_reduction.csv produced = analysis/iteration_v3-011/                         PASS
synthesis.md produced                 = analysis/iteration_v3-011/                         PASS
```

---

## Section 3 — Proposed Changes

### 3.1 Symbols — UNCHANGED (full v3 universe)

| Symbol | Status | Rationale |
|---|---|---|
| BCHUSDT | KEEP | Full v3 universe (iter-v3/007/009/010 baseline). |
| MKRUSDT | KEEP | Same. |
| LDOUSDT | KEEP | Same. |
| TRXUSDT | KEEP | Same. |

`set({BCH, MKR, LDO, TRX}) ∩ V3_EXCLUDED_SYMBOLS = ∅` ✓

### 3.2 Labeling — UNCHANGED (inherits iter-v3/010 ATR(2.0/1.0))

| Parameter | iter-v3/010 (current) | iter-v3/011 (this iteration) |
|---|---:|---:|
| `atr_tp_multiplier` | 2.0 | **2.0 (UNCHANGED)** |
| `atr_sl_multiplier` | 1.0 | **1.0 (UNCHANGED)** |
| Timeout | 21 candles (7d, 10080 min) | UNCHANGED |
| `use_atr_labeling` | True | UNCHANGED |
| Purge gap | 88 (= (21+1)×4) | UNCHANGED |

### 3.3 Features — UNCHANGED (13 features, inherited from iter-v3/009)

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
)  # length = 13, vwap_dev_50 dropped (inherited from iter-v3/008/009/010)
```

NO feature changes. `_verify_feature_columns()` will continue to assert `len == 13` and `'vwap_dev_50' not in V3_FEATURE_COLUMNS`. Note: the z-score gate uses `V2_FEATURE_COLUMNS` (34 features) for OOD detection independently of the model's `V3_FEATURE_COLUMNS` (13 features) — see `risk_v2.py:215-226`.

### 3.4 Risk gates — **CHANGED** (single-axis: z-score OOD threshold)

| Parameter | iter-v3/010 (current) | iter-v3/011 (this iteration) |
|---|---:|---:|
| `RiskV2Config.zscore_threshold` | **2.5** | **2.0 (CHANGED)** |
| Vol scaling | enabled | UNCHANGED |
| ADX threshold | 20 | UNCHANGED |
| Hurst regime check | (0.05, 0.95) | UNCHANGED |
| Low-vol filter | 0.33 | UNCHANGED |
| BTC trend alignment | ±20% 14d | UNCHANGED |
| Hit-rate feedback | DISABLED | UNCHANGED |

The only change is `zscore_threshold` 2.5 → 2.0 in `run_baseline_v3.py:_build_v3_model`. The 7-primitive risk table structure preserved; only one knob tuned.

### 3.5 Sub-fix decomposition (single-axis: risk gate)

| # | Sub-fix | Spec | Verifier |
|---|---|---|---|
| 1 | **Update `zscore_threshold` 2.5 → 2.0** in `run_baseline_v3.py:_build_v3_model` (line 873) | `zscore_threshold=2.0` | `grep -E 'zscore_threshold=2\.0' run_baseline_v3.py` exits 0 |
| 2 | **Update `ITERATION_LABEL` to `"v3-011"`** in `run_baseline_v3.py` (line 99) | One-line change | `grep -E 'ITERATION_LABEL.*=.*"v3-011"' run_baseline_v3.py` exits 0 |
| 3 | **Commit the runner with these changes** | `feat(iter-v3/011): z-score OOD threshold 2.5→2.0 + ITERATION_LABEL=v3-011` | `git log --oneline iteration-v3/011 -- run_baseline_v3.py | head -1` shows the iter-v3/011 SHA |
| 4 | **Run `--exploration --seeds 1 --n-trials 10`** on full 4-symbol universe | Phase 6 invocation: `uv run python run_baseline_v3.py --exploration --seeds 1 --n-trials 10` (no `--symbols` flag → all 4 V3_MODELS). Wall-clock target: < 30 min (hard cap 2h per cadence rule). | `test -f reports-v3/iteration_v3-011/comparison.csv` |

NO new src/ code changes (only `run_baseline_v3.py` line edits). NO test additions. NO labeling/universe/features change.

### 3.6 Brief-vs-Code reconciliation table (Phase 5.5 input)

Each row maps to a FILE ARTIFACT with an executable verifier command. Empty cells = Phase 5.5 BLOCK.

| # | Sub-fix | Code path | File artifact + verifier |
|---|---|---|---|
| 1 | V3_FEATURE_COLUMNS unchanged at 13 features (inherited) | `src/crypto_trade/features_v3/__init__.py` | `python -c "from crypto_trade.features_v3 import V3_FEATURE_COLUMNS; assert len(V3_FEATURE_COLUMNS) == 13, f'len={len(V3_FEATURE_COLUMNS)}'"` exits 0 |
| 2 | `atr_tp_multiplier=2.0` UNCHANGED (inherited from iter-v3/010) | `run_baseline_v3.py` line 862 | `grep -E 'atr_tp_multiplier=2\.0' run_baseline_v3.py` exits 0 |
| 3 | `atr_sl_multiplier=1.0` UNCHANGED (inherited from iter-v3/010) | `run_baseline_v3.py` line 863 | `grep -E 'atr_sl_multiplier=1\.0' run_baseline_v3.py` exits 0 |
| 4 | `zscore_threshold=2.0` CHANGED (was 2.5 in iter-v3/010) | `run_baseline_v3.py` line 873 | `grep -E 'zscore_threshold=2\.0' run_baseline_v3.py` exits 0 |
| 5 | `ITERATION_LABEL` updated to `"v3-011"` | `run_baseline_v3.py` line 99 | `grep -E 'ITERATION_LABEL.*=.*"v3-011"' run_baseline_v3.py` exits 0 |
| 6 | Sub-fix #4 produces comparison.csv | runner | `test -f reports-v3/iteration_v3-011/comparison.csv` |
| 7 | **EXPLORATION sanity test**: IS monthly Sharpe != 0 (gate change took effect; non-zero Sharpe means the new gate threshold actually drives kill counts) | runner | `python -c "import pandas as pd; df=pd.read_csv('reports-v3/iteration_v3-011/comparison.csv'); ms = df.loc[df['metric']=='monthly_sharpe','in_sample'].iloc[0]; assert abs(float(ms)) > 1e-6, f'IS sharpe ~0 — gate likely not taking effect: {ms}'"` exits 0 |
| 8 | All 35 adversarial tests pass | tests | `uv run pytest tests/strategies/ml/ -v` exits 0 |
| 9 | Wall-clock ceiling: total Phase 6 runtime < 30 min target / 2h hard cap | engineering report | `python -c "import json; d=json.load(open('briefs-v3/iteration_v3-011/engineering_report_summary.json')); assert d['wall_clock_minutes'] < 120, f'minutes={d[\"wall_clock_minutes\"]}'"` exits 0 |
| 10 | Full v3 universe used (4 symbols, no --symbols filter) | runner invocation log | `grep -E "Active models: 4/4" reports-v3/iteration_v3-011/run.log` exits 0 |

### 3.7 NO new feature additions, NO universe change, NO labeling change

iter-v3/011 is a single-axis (risk-gate) EXPLORATION. The feature set, model architecture, ATR labeling multipliers, CPCV parameters, and walk-forward window are byte-for-byte unchanged from iter-v3/010. The only differences vs iter-v3/010: `zscore_threshold` (single-axis) + `ITERATION_LABEL` (cosmetic).

### 3.8 Inheritance from iter-v3/010

The `iteration-v3/011` branch was branched from `iteration-v3/010` head. Inherited commits include:

- `bce50c8 feat(iter-v3/007): --exploration mode` (CLI flag plumbing)
- `92218ef feat(iter-v3/007): top-14 V3_FEATURE_COLUMNS subset`
- `849c4a6 fix(iter-v3/007): risk_v3 always loads atr_pct_rank_200 from parquet`
- `56b8f8b feat(iter-v3/008): drop vwap_dev_50 (14→13 features)`
- `b55086a feat(iter-v3/010): ATR multipliers (2.9,1.45)→(2.0,1.0) + ITERATION_LABEL=v3-010 + docstring parametrization`
- `17d01ab feat(iter-v3/011): z-score OOD threshold perturbation analysis` (this brief's evidence)

Critical inheritance verifiers (run before any code edits in Phase 6):
- `python -c "from crypto_trade.features_v3 import V3_FEATURE_COLUMNS; assert len(V3_FEATURE_COLUMNS) == 13 and 'vwap_dev_50' not in V3_FEATURE_COLUMNS"` exits 0
- `grep -E 'atr_tp_multiplier=2\.0' run_baseline_v3.py` exits 0 (still iter-v3/010 value)
- `grep -E 'atr_sl_multiplier=1\.0' run_baseline_v3.py` exits 0 (still iter-v3/010 value)
- `uv run pytest tests/strategies/ml/ -v` exits 0 with 35/35 PASS

---

## Section 4 — Expected OOS Impact

### 4.1 EXPLORATION → headline metrics are GUIDANCE not GATES

Per Section 0.5 + skill spec at SHA `f0f8b84`, headline metrics are NOT BLOCK-triggering for the Critic on EXPLORATION iterations. The Critic emits `EXPLORATION-PROMISING`, `EXPLORATION-NEGATIVE`, or `BLOCK` (process). iter-v3/011 NEVER updates BASELINE_V3.md regardless of verdict.

### 4.2 Predicted IS Sharpe range

| Metric | iter-v3/010 (z=2.5, ATR(2.0/1.0)) | iter-v3/011 prediction (z=2.0, ATR(2.0/1.0)) |
|---|---:|---:|
| IS monthly Sharpe | +0.5683 | **predicted [+0.30, +0.70] with median +0.45** |
| IS trades | 357 | **predicted ~270 (Prior B), stress-test floor ~113 (Prior A iid)** |
| Phase 6 wall-clock | 7 min | predicted 6-12 min (fewer trades = marginally faster), hard cap 2h |

The prediction band [+0.30, +0.70] is intentionally **broad** — gate sensitivity is high-variance (every kill-rate change shifts the trade-mix and effectively changes which regimes the model gets to act on, not just sample size). The median +0.45 reflects the realistic Prior B's 76% survivor ratio: a moderate trade reduction that should preserve most of iter-v3/010's IS edge IF the strategy's edge is broad-based (consistent with iter-v3/010's diary "broad-based across 3 of 4 OOS symbols"). Median is BELOW iter-v3/010's +0.5683 because tighter gating is uniformly likely to lose at least some marginal-but-positive trades; not above, despite the framing "maintained or improved", because the typical effect of stricter filtering on a working strategy is to compress edge (per López de Prado AFML Ch. 2 on signal/noise tradeoffs in filter selection).

### 4.3 Falsifiers (locked before backtest)

**Falsifier 1**: IS Sharpe < +0.10 → tighter gate killed signal beyond noise reduction. The (z=2.0) threshold over-filters; tightening over-corrects. Verdict: EXPLORATION-NEGATIVE on gate-axis-tight direction. Catalog this finding; iter-v3/012 may try z=3.0 (looser direction) to verify the relationship is monotonic in the OPPOSITE direction.

**Falsifier 2**: IS trade count > 357 (i.e., MORE trades despite tighter gate) → bug. The gate logic should be monotonic-decreasing in threshold (lower threshold = more kills = fewer trades). If trade count rises, something is wrong in the runtime wiring. Verdict: BLOCK (process); engineer documents.

**Falsifier 3** (process): Phase 6 wall-clock > 30 min on full v3 universe at exploration config → gate-perturbation slowdown reproduces; engineer documents the cause; future EXPLORATION iterations re-scope.

**Process falsifier**: pre-flight `len(V3_FEATURE_COLUMNS) == 13` returns False OR grep for `zscore_threshold=2.0` returns empty → setup drift; Phase 6 must not start.

### 4.4 EXPLORATION outcome interpretation

| Critic verdict | Meaning | Next iteration |
|---|---|---|
| `EXPLORATION-PROMISING` | IS Sharpe ≥ +0.40 — tighter gate validates iter-v3/010 robustness | iter-v3/012 EXPLORATION on a DIFFERENT axis (e.g., feature reduction further, BTC trend filter band, ADX threshold) |
| `EXPLORATION-NEGATIVE-soft` | IS Sharpe in [+0.10, +0.40) — tighter gate filters useful information; signal dilutes but stays positive | iter-v3/012 may test z=3.0 (looser direction) to confirm gate-axis sensitivity |
| `EXPLORATION-NEGATIVE` | IS Sharpe < +0.10 (Falsifier 1) — tighter gate over-filters | iter-v3/012 EXPLORATION on a DIFFERENT axis OR test z=3.0 (looser) |
| `BLOCK` (process) | Methodology check FAILED unexpectedly | Diary documents, iter-v3/012 fixes the methodology gap |

---

## Section 5 — Risk Mitigation

### 5.1 Cadence-discipline structural safeguards

iter-v3/011 inherits THREE structural safeguards from the cadence skill:

1. **2h wall-clock hard cap** (skill SHA `d5c9f21`): Engineer kills Phase 6 if elapsed > 2h, regardless of progress. Prevents the iter-v3/008 abort pattern from recurring.
2. **Single-axis variation rule** honored (only `zscore_threshold` changed; features/symbols/labeling/other gates byte-for-byte identical to iter-v3/010).
3. **EXPLORATION never updates BASELINE_V3.md** — outcome (PROMISING / NEGATIVE / BLOCK) records only in `briefs-v3/exploration_catalog.md` and `diary-v3/iteration_v3-011.md`.

### 5.2 Methodology-pipeline safety (inherited from iter-v3/006-010)

1. **35 adversarial unit tests** must PASS before backtest.
2. **File-artifact reconciliation table** (§3.6). 10 verifier commands; empty cells = Phase 5.5 BLOCK.
3. **Pre-flight len + name check** on `V3_FEATURE_COLUMNS`: catches the case where inherited setup was silently lost during a rebase.
4. **Two-round Critic flow**: any methodology issue surfaces before Phase 6 launches.

### 5.3 NO new model-level risks introduced

The iter-v3/011 changes:
- ZERO new code (only `_build_v3_model` arg edit + ITERATION_LABEL).
- ZERO new features.
- ZERO new dropped features.
- ZERO labeling changes.
- ZERO CPCV / walk-forward window changes.
- ZERO test changes.

The only model-level effect is the new gate kill-rate distribution. Mitigated by:
- Per-symbol IS-only frequency baseline + projected reduction (§2.3) provides Falsifier-2 reference.
- Critic two-round flow surfaces any unexpected interaction.

---

## Section 6 — Risk Management Design

### 6.1 7-primitive table — SAME 7 PRIMITIVES as iter-v3/006-010, only #4 threshold tuned

| # | Primitive | Spec | Fire-rate prediction (IS) | Regime coverage |
|---|---|---|---|---|
| 1 | Vol scaling | `scale = clip(atr_pct_rank_200, 0.3, 1.0)` | Always on; mean scale ≈ 0.6 | High-vol → scale down |
| 2 | ADX gate | trade only when ADX > 20 | ≈ 60% of bars pass | Trending only |
| 3 | Hurst regime check | trade only when 0.05 < hurst_100 < 0.95 | ≈ 90% of bars pass | Filters bond-like regimes |
| 4 | Feature z-score OOD | kill if any \|z\| > **2.0 (tightened from 2.5)** | **≈ 25–35% killed (Prior B realistic)** vs ≈ 5–15% baseline | Distributional drift — TIGHTER |
| 5 | Low-vol filter | trade only when atr_pct_rank_200 ≥ 0.33 | ≈ 67% of bars pass | Filters dead chop |
| 6 | Hit-rate feedback | DISABLED | 0% | Reserved for future tuning |
| 7 | BTC trend alignment | kill alt trade fighting BTC 14d ±20% | ≈ 7–8% killed | Macro flips |

Combined kill rate target: **75–88%** (vs 69–78% at z=2.5) — the tightening adds ~15-25pp to the combined kill rate via primitive #4.

**Gate-vs-feature-set independence**: gates fire at trade-entry time on the candle's `V2_FEATURE_COLUMNS` (34 features) computed in `risk_v2.py:_build_lookups`, INDEPENDENT of the LightGBM model's `V3_FEATURE_COLUMNS` (13 features). Verifier: the gate threshold change at `RiskV2Config.zscore_threshold` propagates to `_zscore_ood` (risk_v2.py:286) but does NOT affect the model's feature ingestion or labeling logic.

### 6.2 Regime coverage — UNCHANGED

Full v3 universe IS data spans 2022-09-24 → 2025-03-23. Regime coverage includes 2022 LUNA/FTX, 2023 banking, 2024 halving + Trump rally, 2025 January correction. Tighter gate may differentially affect tail regimes (e.g., LUNA/FTX feature outliers more likely killed at z=2.0), which is intentional per the OOD-detection design.

### 6.3 Concentration — informational only under EXPLORATION

iter-v3/010 OOS showed 57.17% BCH concentration. Concentration is NOT a gate for iter-v3/011 per TYPE=EXPLORATION; informational only. The gate change may shift concentration in either direction (different per-symbol kill rates, since each symbol has its own IS-window mean/std snapshot per `risk_v2.py:225-226`); diary captures the actual shift.

---

## Section 7 — Pre-Registered Failure-Mode Prediction

**Prediction P1 (process, P=5%)**: the `zscore_threshold` change in `_build_v3_model` doesn't propagate to `RiskV2Wrapper._zscore_ood` at runtime (e.g., a stale config object is cached, or the Engineer accidentally edits a different `zscore_threshold` reference). **Detection signal**: pre-flight check via grep + Phase 6 run.log gate-stats showing IS kill rates identical to iter-v3/010 (impossible if threshold actually changed). **Mitigation**: pre-flight grep verifies `zscore_threshold=2.0` (sub-fix #4 verifier); engineer reports observed IS gate kill counts in engineering report.

**Prediction P2 (process, P=5%)**: wall-clock overshoots 30 min on full v3 universe at exploration config. iter-v3/010 ran in 7 min on the same config + same 4 symbols; tightening is expected to produce FEWER trades (1.32x baseline at Prior B realistic), which marginally DECREASES run time. **Detection signal**: total Phase 6 wall-clock > 30 min on full universe. **Mitigation**: 2h hard cap (cadence rule). Engineer kills if exceeded; iter-v3/012 EXPLORATION re-scopes.

**Prediction P3 (process, P=5%)**: the 0.5-pp drift in z-threshold reveals a hidden floating-point comparison bug in `_zscore_ood` (e.g., the comparison uses `>=` instead of `>` and the change is silently no-op at the interior of the 2.5-z to 2.0-z mass). **Detection signal**: pre-flight unit test fails OR comparison.csv IS Sharpe identical to iter-v3/010's +0.5683 to 4 decimal places (impossible if gate actually fires more). **Mitigation**: pre-flight pytest pass requirement (sub-fix #8 verifier); the gate logic at `risk_v2.py:286` uses strict `>` per existing code review.

**Prediction P4 (model, P=50%)**: IS Sharpe lands in [+0.40, +0.70] band (predicted band; tighter gate validates iter-v3/010 signal robustness). EXPLORATION-PROMISING. The strategy's edge survives the stricter filter because the underlying signal is broad-based rather than driven by marginal high-z outlier trades. The realistic Prior B's 76% survivor ratio compresses sample size moderately while preserving most directional edge.

**Prediction P5 (model, P=30%)**: IS Sharpe lands in [+0.10, +0.40) band — tighter gate filters useful information; signal dilutes but stays positive. EXPLORATION-NEGATIVE-soft. The (z=2.0) threshold over-filters by removing trades where z-score outliers were directional signal (not noise) — iter-v3/010's edge was partly carried by feature-outlier candles. Catalog this finding; iter-v3/012 may test looser direction (z=3.0).

**Prediction P6 (model, P=15%)**: IS Sharpe drops below +0.10 (Falsifier 1 activates). Tighter gate over-filters severely — the strategy's edge sat substantially on z>2.0 trades (e.g., volatility-shock signals where high-z is the entire informational content). EXPLORATION-NEGATIVE. Catalog third NEGATIVE row; iter-v3/012 pivots back to features-axis or labeling-axis variation.

The predictions are intentionally Bayesian-calibrated:
- 3 process-level (P1, P2, P3) per iter-v3/003 lesson #3 discipline
- 3 model-level (P4, P5, P6) covering predicted-band, soft-undershoot, hard-undershoot
- Per the iter-v3/010 calibration overshoot (predicted [+0.10, +0.30], reality +0.5683): labeling-axis priors had been too narrow. For gate-axis here, priors are widened to reflect higher gate-sensitivity variance: 50/30/15 (PROMISING / soft-NEGATIVE / hard-NEGATIVE) with wider PROMISING band ([+0.40, +0.70] vs iter-v3/010's [+0.10, +0.30]).

Summary: **EXPLORATION-PROMISING pathway probability ≈ 50%** (P4); EXPLORATION-NEGATIVE ≈ 45% (P5+P6); process abort ≈ 5% (P1+P2+P3 ≈ 15% but each individually triggers a remediation, not a verdict change).

If any prediction fails to materialize, the iter-v3/011 diary documents the calibration miss.

---

## Section 8 — Pre-Registered EXPLORATION Criteria

**These thresholds are LOCKED before backtest. Phase 7 evaluation applies them mechanically.**

iter-v3/011 is an **EXPLORATION iteration** per Section 0.5. Headline-metric criteria from CONFIRMATION iterations (DSR > 0.95, PSR > 0.95, OOS Sharpe > 1.0) are NOT in scope. Critic emits `EXPLORATION-PROMISING`, `EXPLORATION-NEGATIVE`, or `BLOCK`.

### EXPLORATION-PROMISING iff ALL 10 of the following are true:

| # | Criterion | Threshold | Source |
|---|---|---:|---|
| 1 | TYPE=EXPLORATION declared in Section 0.5 | TRUE | §0.5 |
| 2 | Single-axis variation only (risk-gate `zscore_threshold`) | TRUE | §3.7 |
| 3 | Wall-clock < 2h (target < 30 min) | TRUE | §3.6 row 9 |
| 4 | `--exploration --seeds 1 --n-trials 10` used | TRUE | §3.5 sub-fix #4 |
| 5 | 35/35 adversarial tests pass | TRUE | §3.6 row 8 |
| 6 | `zscore_threshold=2.0` confirmed at runtime | TRUE | §3.6 row 4 |
| 7 | `comparison.csv` produced (basic headline metrics) | TRUE | §3.6 row 6 |
| 8 | Critic OVERALL = `EXPLORATION-PROMISING` (NOT NEGATIVE, NOT BLOCK) | enum | Phase 7.5 |
| 9 | NO 5-seed or CONFIRMATION-style runs | TRUE (vacuous; --seeds 1) | §3.7 |
| 10 | Catalog updated post-Phase-8 with iter-v3/011 row | TRUE | post-iteration mechanic |

### EXPLORATION-NEGATIVE iff:

- Criteria 1-7, 9, 10 PASS BUT Critic OVERALL = `EXPLORATION-NEGATIVE` (because IS Sharpe < +0.40, falsifier 1 region, OR IS trades > 357 unexpectedly indicating monotonicity bug)

### BLOCK (process) iff ANY of:

- Criteria 1-7, 9 fail (process-level)
- Phase 5.5 gate emits BLOCK
- Phase 7.5 Critic emits explicit BLOCK
- Wall-clock exceeds 2h hard cap
- IS trade count > 357 (Falsifier 2: monotonicity violation)

### Discretionary judgment — EXPLORATION pathway

iter-v3/011 has NO MERGE pathway because the iteration TYPE is EXPLORATION. The "MERGE pathway" is `EXPLORATION-PROMISING`, which is a forward-pointer: it adds one row to the catalog and counts toward the 10 EXPLORATION quota. **iter-v3/011 NEVER updates BASELINE_V3.md.**

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
| `pandas` | (already installed) | BSD-3 | Parquet I/O + analysis script CSV/trades.csv loading | n/a |
| `pyarrow` | (already installed via pandas) | Apache-2 | Parquet engine (unchanged) | If missing, fastparquet |

**No new external deps.** Same stack as iter-v3/007-010. The iteration's NEW code is:
- 1 analysis script + 2 outputs (committed at SHA `17d01ab`)
- 2 cosmetic `run_baseline_v3.py` line edits (Engineer ships in Phase 6): `zscore_threshold`, `ITERATION_LABEL`
- 0 new pytest test files
- 0 modifications to per-cell PBO / DSR / PSR / ADF code paths

### Aggregator strategy — UNCHANGED

Per-cell PBO with cross-cell mean aggregation. Per-cell n_eff with cross-cell median aggregation.

### Reproducibility stamp

The Engineer's Phase 6 writes `briefs-v3/iteration_v3-011/engineering_report.md` with:
- The git commit SHAs at backtest time (expected: `17d01ab` analysis + the new sub-fix SHA)
- Output of `uv pip list | grep -E "(numpy|scipy|statsmodels|scikit-learn|lightgbm|pytest|pandas|pyarrow)"`
- The full 13-feature list as actually trained on (sanity check against §3.3)
- The runtime `zscore_threshold` (sanity check against §3.5 sub-fix #1)
- Observed IS gate kill counts (P1 detection signal): `killed_by_zscore` per symbol from `risk_v2.py:333-345` log output
- The `comparison.csv` IS / OOS monthly Sharpe values
- The total IS trade count (Falsifier 2 reference, must be ≤ 357)
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
| 0.5 — Iteration Type Declaration | PASS — TYPE: EXPLORATION declared; cadence catalog reference; explicit "NEVER updates BASELINE_V3.md"; risk-gate axis chosen per Critic FINAL Rec 1 of iter-v3/010 |
| 1 — Hypothesis | PASS — one sentence; testable target IS Sharpe ≥ +0.40 (Falsifier 1 at +0.10); falsifiers in §4.3 |
| 2 — IS-Only Numerical Evidence | PASS — `analysis/iteration_v3-011/zscore_threshold_demo.py` committed at SHA `17d01ab` BEFORE this brief; per-symbol baseline + projected reduction tables (Prior A iid / Prior B realistic) |
| 3 — Proposed Changes | PASS — symbols UNCHANGED; labeling UNCHANGED; features UNCHANGED; risk gate threshold CHANGED (single-axis); sub-fix decomposition with reconciliation table 10 verifiers; inheritance plan §3.8 |
| 4 — Expected OOS Impact | PASS — predicted IS Sharpe range [+0.30, +0.70]; 4 falsifiers in §4.3; EXPLORATION pathway in §4.4 |
| 5 — Risk Mitigation | PASS — 3 cadence-discipline structural safeguards in §5.1 + 4 methodology-pipeline safeguards in §5.2 |
| 6 — Risk Management Design | PASS — 7-primitive table with primitive #4 threshold tightened; gate-vs-feature-set independence verified |
| 7 — Pre-Registered Failure-Mode | PASS — 6 predictions with **3 process-level (P1, P2, P3)**; calibrated PROMISING prior at ~50% (reflecting iter-v3/010 overshoot lesson + gate-axis variance) |
| 8 — Pre-Registered EXPLORATION Criteria | PASS — 10 EXPLORATION criteria; EXPLORATION-PROMISING / EXPLORATION-NEGATIVE / BLOCK pathways; explicit "NEVER updates BASELINE_V3.md" |
| 9 — Library Stack | PASS — no new deps; aggregator strategy unchanged from iter-v3/006-010 |

Engineer: please run Phase 5.5 gate verification against the brief-vs-code reconciliation table in Section 3.6. Empty cells in the right column = BLOCK. Verifier commands that do NOT execute and exit 0 post-Phase 6 = NO-MERGE per Section 8.
