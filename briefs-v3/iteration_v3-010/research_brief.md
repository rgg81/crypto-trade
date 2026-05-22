# Iteration v3-010 — Research Brief

**Type**: EXPLORATION (THIRD EXPLORATION under the cadence discipline; SECOND post-iter-v3/008-abort)
**Track**: v3 (rigor arm) — tenth iteration
**Branch**: `iteration-v3/010` (off `iteration-v3/009` head; analysis commit `80332c1` ships before this brief)
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

**Sacred constants UNCHANGED.** The `--exploration` flag (SHA `bce50c8`) does NOT touch `OOS_CUTOFF_DATE` or `training_months`. The QR sees OOS metrics for the FIRST time in Phase 7. This brief is produced reading ONLY: iter-v3/007 + iter-v3/008 + iter-v3/009 briefs / engineering reports / Critic / diaries; iter-v3/009 `in_sample/trades.csv` (IS-only); the iter-v3/010 analysis script `analysis/iteration_v3-010/atr_multiplier_demo.py` outputs (committed at SHA `80332c1` BEFORE this brief).

---

## Section 0.5 — Iteration Type Declaration

```
TYPE: EXPLORATION
Wall-clock budget: < 30 min (well under the 2h hard cap)
Single-axis variation: labeling (ATR multipliers tp=2.9→2.0, sl=1.45→1.0;
                       same 2:1 ratio, tighter absolute values)
Cadence: EXPLORATION #3 of 10 needed before CONFIRMATION can launch
This iteration NEVER updates BASELINE_V3.md.
```

**Justification**: Per cadence discipline (skill SHA `d5c9f21`), CONFIRMATION cannot launch with fewer than 10 EXPLORATION rows since the last CONFIRMATION. The catalog at `briefs-v3/exploration_catalog.md` has 2 rows (iter-v3/007 PROMISING, iter-v3/009 NEGATIVE); iter-v3/010 is the third. Per Critic FINAL Recommendation 1 on iter-v3/009 review (SHA `1bc828f`), iter-v3/010 must vary along a NON-features axis (axis diversity is a quota requirement, not just a count requirement). The LABELING axis is selected because it changes BOTH label distribution AND model targets simultaneously, yielding maximally orthogonal evidence vs the iter-v3/007/009 features-axis runs.

---

## Section 1 — Hypothesis

Tightening triple-barrier ATR multipliers from `(tp=2.9, sl=1.45)` to `(tp=2.0, sl=1.0)` — same 2:1 ratio, tighter absolute values — will produce IS Sharpe ≥ +0.10 (Falsifier 1 threshold) by yielding higher-frequency lower-magnitude trades; tests whether the iter-v3/007 IS=+0.22 baseline was sensitive to the specific multiplier values rather than just the 13-feature subset.

---

## Section 2 — IS-Only Numerical Evidence

**Analysis script**: `analysis/iteration_v3-010/atr_multiplier_demo.py` (committed at SHA `80332c1` BEFORE this brief — Phase 5.5 reproducibility requirement).

**Inputs read** (all IS-only):
- `reports-v3/iteration_v3-009/in_sample/trades.csv` — 267 IS trades from the (tp=2.9, sl=1.45) baseline. NO OOS contact.

**Outputs** (committed alongside the script at SHA `80332c1`):
- `analysis/iteration_v3-010/expected_label_shift.csv` — per-symbol baseline + projected stats.
- `analysis/iteration_v3-010/synthesis.md` — 1-paragraph narrative.

### 2.1 Baseline trade-frequency stats (iter-v3/009 IS, (2.9, 1.45))

| Symbol | n_trades | trades/month | %TP | %SL | %timeout |
|---|---:|---:|---:|---:|---:|
| BCHUSDT | 84 | 2.81 | 20.2% | 53.6% | 26.2% |
| LDOUSDT | 23 | 0.77 | 26.1% | 60.9% | 13.0% |
| MKRUSDT | 71 | 2.37 | 22.5% | 60.6% | 16.9% |
| TRXUSDT | 89 | 2.97 | 21.3% | 59.6% | 19.1% |
| **TOTAL** | **267** | — | — | — | — |

LDO has the lowest baseline frequency (listed 2022-09-22 → fewer IS months), TRX the highest. SL-rate is 53–61% across symbols; TP-rate is 20–26%; timeout 13–26%. The exit-mix is **SL-dominant** at the (2.9, 1.45) baseline — this is the iter-v3/009 IS distribution against which iter-v3/010 will be measured.

### 2.2 Expected label-distribution shift under (2.0, 1.0)

Both TP and SL distances shrink by the same factor `2.9/2.0 = 1.45×`. Under inverse-ratio scaling (a Brownian-like price process hits a barrier at distance `d_new` ~ `d_old/d_new` times faster on average), the expected per-symbol trade count multiplier is **1.45×**.

| Symbol | baseline_n | expected_n (1.45×) | expected trades/month |
|---|---:|---:|---:|
| BCHUSDT | 84 | 122 | 4.07 |
| LDOUSDT | 23 | 33 | 1.11 |
| MKRUSDT | 71 | 103 | 3.44 |
| TRXUSDT | 89 | 129 | 4.31 |
| **TOTAL** | **267** | **387** | — |

Total expected IS trades: ~387 (vs 267 baseline). This is a **rough estimate** — actual frequency depends on the joint distribution of forward returns and time-to-barrier-touch, which only the Phase 6 backtest can measure. The estimate serves as the Falsifier-2 reference.

### 2.3 Setup integrity (verified at SHA `80332c1`)

```
trades.csv path                   = reports-v3/iteration_v3-009/in_sample/trades.csv  PASS
total IS trades read              = 267                                               PASS
expected frequency multiplier     = 1.45                                              PASS
expected_label_shift.csv produced = analysis/iteration_v3-010/                        PASS
```

---

## Section 3 — Proposed Changes

### 3.1 Symbols — UNCHANGED (full v3 universe)

| Symbol | Status | Rationale |
|---|---|---|
| BCHUSDT | KEEP | Full v3 universe (iter-v3/007/009 baseline). |
| MKRUSDT | KEEP | Same. |
| LDOUSDT | KEEP | Same. |
| TRXUSDT | KEEP | Same. |

`set({BCH, MKR, LDO, TRX}) ∩ V3_EXCLUDED_SYMBOLS = ∅` ✓

### 3.2 Labeling — **CHANGED** (single-axis variation)

| Parameter | iter-v3/009 (current) | iter-v3/010 (this iteration) |
|---|---:|---:|
| `atr_tp_multiplier` | **2.9** | **2.0** |
| `atr_sl_multiplier` | **1.45** | **1.0** |
| Ratio TP:SL | 2:1 | **2:1 (same)** |
| Timeout | 21 candles (7d, 10080 min) | UNCHANGED |
| σ_t source | past-only `natr_21_raw` | UNCHANGED |
| `use_atr_labeling` | True | UNCHANGED |
| Purge gap | 88 (= (21+1)×4) | UNCHANGED |

The only change is the absolute ATR multiplier values. The 2:1 TP:SL ratio is preserved — this is a single-axis (labeling-magnitude) variation, NOT a ratio change. The change is made in `run_baseline_v3.py:_build_v3_model` lines 863–864.

### 3.3 Features — UNCHANGED (13 features inherited from iter-v3/009)

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
)  # length = 13, vwap_dev_50 dropped (inherited from iter-v3/008/009)
```

NO feature changes. `_verify_feature_columns()` will continue to assert `len == 13` and `'vwap_dev_50' not in V3_FEATURE_COLUMNS`.

### 3.4 Risk gates — UNCHANGED

Same 7-primitive table as iter-v3/006-009 (see Section 6). Gates are computed against parquet feature DataFrames (where all 34 features remain computed), independently of `V3_FEATURE_COLUMNS`. The label change does NOT affect gate logic.

### 3.5 Sub-fix decomposition (single-axis: labeling)

| # | Sub-fix | Spec | Verifier |
|---|---|---|---|
| 1 | **Update `atr_tp_multiplier` 2.9 → 2.0** in `run_baseline_v3.py:_build_v3_model` (line 863) | `atr_tp_multiplier=2.0` | `grep -E 'atr_tp_multiplier=2\.0' run_baseline_v3.py` exits 0 |
| 2 | **Update `atr_sl_multiplier` 1.45 → 1.0** in `run_baseline_v3.py:_build_v3_model` (line 864) | `atr_sl_multiplier=1.0` | `grep -E 'atr_sl_multiplier=1\.0' run_baseline_v3.py` exits 0 |
| 3 | **Update `ITERATION_LABEL` to `"v3-010"`** in `run_baseline_v3.py` (line 99) | One-line change | `grep -E 'ITERATION_LABEL.*=.*"v3-010"' run_baseline_v3.py` exits 0 |
| 4 | **Fix stale `_verify_feature_columns()` docstring** (Critic FINAL Rec 3, iter-v3/009 review SHA `1bc828f`) | Replace hardcoded `"iter-v3/008 brief Section 3.3"` and `"iter-v3/008 CONFIRMATION"` references with parametrized `f"{ITERATION_LABEL}"` references. Cosmetic but compounding — third iteration with stale banner. | After fix: `grep -E 'iter-v3/008' run_baseline_v3.py` returns no matches inside `_verify_feature_columns()` (lines 181-203) |
| 5 | **Commit the runner with these changes** | `feat(iter-v3/010): ATR multipliers (2.9,1.45)→(2.0,1.0) + ITERATION_LABEL + docstring fix` | `git log --oneline iteration-v3/010 -- run_baseline_v3.py | head -1` shows the iter-v3/010 SHA |
| 6 | **Run `--exploration --seeds 1 --n-trials 10`** on full 4-symbol universe | Phase 6 invocation: `uv run python run_baseline_v3.py --exploration --seeds 1 --n-trials 10` (no `--symbols` flag → all 4 V3_MODELS). Wall-clock target: < 30 min (hard cap 2h per cadence rule). | `test -f reports-v3/iteration_v3-010/comparison.csv` |

NO new src/ code changes (only `run_baseline_v3.py` line edits + docstring). NO test additions.

### 3.6 Brief-vs-Code reconciliation table (Phase 5.5 input)

Each row maps to a FILE ARTIFACT with an executable verifier command. Empty cells = Phase 5.5 BLOCK.

| # | Sub-fix | Code path | File artifact + verifier |
|---|---|---|---|
| 1 | V3_FEATURE_COLUMNS unchanged at 13 features (inherited) | `src/crypto_trade/features_v3/__init__.py` | `python -c "from crypto_trade.features_v3 import V3_FEATURE_COLUMNS; assert len(V3_FEATURE_COLUMNS) == 13, f'len={len(V3_FEATURE_COLUMNS)}'"` exits 0 |
| 2 | `atr_tp_multiplier=2.0` (CHANGED from 2.9) | `run_baseline_v3.py` line 863 | `grep -E 'atr_tp_multiplier=2\.0' run_baseline_v3.py` exits 0 |
| 3 | `atr_sl_multiplier=1.0` (CHANGED from 1.45) | `run_baseline_v3.py` line 864 | `grep -E 'atr_sl_multiplier=1\.0' run_baseline_v3.py` exits 0 |
| 4 | `ITERATION_LABEL` updated to `"v3-010"` | `run_baseline_v3.py` line 99 | `grep -E 'ITERATION_LABEL.*=.*"v3-010"' run_baseline_v3.py` exits 0 |
| 5 | `_verify_feature_columns()` docstring de-stale (no `iter-v3/008` references) | `run_baseline_v3.py` lines 181-203 | `python -c "import re; src=open('run_baseline_v3.py').read(); m=re.search(r'def _verify_feature_columns.*?(?=\ndef )', src, re.S); assert m and 'iter-v3/008' not in m.group(0), 'iter-v3/008 still referenced in _verify_feature_columns body/docstring'"` exits 0 |
| 6 | Sub-fix #6 produces comparison.csv | runner | `test -f reports-v3/iteration_v3-010/comparison.csv` |
| 7 | **EXPLORATION sanity test**: IS monthly Sharpe != 0 (label change took effect; non-zero Sharpe means the new labels actually drive predictions) | runner | `python -c "import pandas as pd; df=pd.read_csv('reports-v3/iteration_v3-010/comparison.csv'); ms = df.loc[df['metric']=='monthly_sharpe','in_sample'].iloc[0]; assert abs(float(ms)) > 1e-6, f'IS sharpe ~0 — labels likely not taking effect: {ms}'"` exits 0 |
| 8 | All 35 adversarial tests pass | tests | `uv run pytest tests/strategies/ml/ -v` exits 0 |
| 9 | Wall-clock ceiling: total Phase 6 runtime < 30 min target / 2h hard cap | engineering report | `python -c "import json; d=json.load(open('briefs-v3/iteration_v3-010/engineering_report_summary.json')); assert d['wall_clock_minutes'] < 120, f'minutes={d[\"wall_clock_minutes\"]}'"` exits 0 |
| 10 | Full v3 universe used (4 symbols, no --symbols filter) | runner invocation log | `grep -E "Active models: 4/4" reports-v3/iteration_v3-010/run.log` exits 0 |

### 3.7 NO new feature additions, NO universe change

iter-v3/010 is a single-axis (labeling) EXPLORATION. The feature set, model architecture, risk gates, CPCV parameters, and walk-forward window are byte-for-byte unchanged from iter-v3/009. The only differences vs iter-v3/009: ATR multipliers (single-axis) + ITERATION_LABEL (cosmetic) + docstring fix (cosmetic).

### 3.8 Inheritance from iter-v3/009

The `iteration-v3/010` branch was branched from `iteration-v3/009` head. Inherited commits include:

- `bce50c8 feat(iter-v3/007): --exploration mode` (CLI flag plumbing)
- `92218ef feat(iter-v3/007): top-14 V3_FEATURE_COLUMNS subset`
- `849c4a6 fix(iter-v3/007): risk_v3 always loads atr_pct_rank_200 from parquet`
- `56b8f8b feat(iter-v3/008): drop vwap_dev_50 (14→13 features)`
- `43b3ed8 feat(iter-v3/009): ITERATION_LABEL=v3-009`
- `80332c1 feat(iter-v3/010): ATR multiplier perturbation analysis` (this brief's evidence)

Critical inheritance verifiers (run before any code edits in Phase 6):
- `python -c "from crypto_trade.features_v3 import V3_FEATURE_COLUMNS; assert len(V3_FEATURE_COLUMNS) == 13 and 'vwap_dev_50' not in V3_FEATURE_COLUMNS"` exits 0
- `uv run pytest tests/strategies/ml/ -v` exits 0 with 35/35 PASS

---

## Section 4 — Expected OOS Impact

### 4.1 EXPLORATION → headline metrics are GUIDANCE not GATES

Per Section 0.5 + skill spec at SHA `f0f8b84`, headline metrics are NOT BLOCK-triggering for the Critic on EXPLORATION iterations. The Critic emits `EXPLORATION-PROMISING`, `EXPLORATION-NEGATIVE`, or `BLOCK` (process). iter-v3/010 NEVER updates BASELINE_V3.md regardless of verdict.

### 4.2 Predicted IS Sharpe range

| Metric | iter-v3/009 (top-13, 2.9/1.45) | iter-v3/010 prediction (top-13, 2.0/1.0) |
|---|---:|---:|
| IS monthly Sharpe | +0.0802 | **predicted [-0.20, +0.40] with median +0.10** |
| IS trades | 267 | **predicted ~387 (1.45× scaling)** |
| Phase 6 wall-clock | 11 min | predicted 12-18 min (more trades = marginally slower), hard cap 2h |

The prediction band [-0.20, +0.40] is intentionally **wide** — labeling perturbations are high-variance changes (every label re-defines what the model is trying to predict, not just which features it sees). The median +0.10 reflects the iter-v3/009 calibration miss lesson: features-axis variation under colsample=1.0 is not free; labeling-axis variation is structurally different (changes the target distribution rather than the feature subset), so prior-setting reflects the catalog's empirical data (only 2 rows; one PROMISING, one NEGATIVE; insufficient for tight calibration on a new axis).

### 4.3 Falsifiers (locked before backtest)

**Falsifier 1**: IS Sharpe < +0.10 → labeling change is NEGATIVE on this axis. The (2.0, 1.0) ratio yields decisions that are too noisy / too frequent to capture edge. Verdict: EXPLORATION-NEGATIVE on labeling-magnitude axis. Catalog this finding; iter-v3/011 tries a DIFFERENT axis (e.g., risk gate threshold, BTC trend filter band, OOD threshold).

**Falsifier 2**: total IS trades < iter-v3/009's count (267) → labeling change reduced trade frequency unexpectedly. Suggests SL is too tight, killing trades early before TP can fire (i.e., the TP hit-rate drops while SL hit-rate increases without offsetting frequency gain). Verdict: EXPLORATION-NEGATIVE with structural diagnosis (the (2.0, 1.0) ratio is dominated by SL hits, not faster TP hits).

**Falsifier 3** (process): Phase 6 wall-clock > 30 min on full v3 universe at exploration config → labeling-perturbation slowdown reproduces; engineer documents the cause; future EXPLORATION iterations re-scope.

**Process falsifier**: pre-flight `len(V3_FEATURE_COLUMNS) == 13` returns False OR grep for ATR multiplier values returns empty → setup drift; Phase 6 must not start.

### 4.4 EXPLORATION outcome interpretation

| Critic verdict | Meaning | Next iteration |
|---|---|---|
| `EXPLORATION-PROMISING` | IS Sharpe ≥ +0.10 — tighter labels are NEUTRAL or HELP | iter-v3/011 EXPLORATION on a DIFFERENT axis (risk gates, BTC trend filter, OOD threshold) |
| `EXPLORATION-NEGATIVE` | IS Sharpe < +0.10 — tighter labels HURT (Falsifier 1) | iter-v3/011 EXPLORATION on a DIFFERENT axis OR re-test labeling at a different multiplier (e.g., (3.5, 1.75) — wider) |
| `BLOCK` (process) | Methodology check FAILED unexpectedly | Diary documents, iter-v3/011 fixes the methodology gap |

---

## Section 5 — Risk Mitigation

### 5.1 Cadence-discipline structural safeguards

iter-v3/010 inherits THREE structural safeguards from the cadence skill:

1. **2h wall-clock hard cap** (skill SHA `d5c9f21`): Engineer kills Phase 6 if elapsed > 2h, regardless of progress. Prevents the iter-v3/008 abort pattern from recurring.
2. **Single-axis variation rule** honored (only labeling changed; features/symbols/risk gates byte-for-byte identical to iter-v3/009).
3. **EXPLORATION never updates BASELINE_V3.md** — outcome (PROMISING / NEGATIVE / BLOCK) records only in `briefs-v3/exploration_catalog.md` and `diary-v3/iteration_v3-010.md`.

### 5.2 Methodology-pipeline safety (inherited from iter-v3/006-009)

1. **35 adversarial unit tests** must PASS before backtest.
2. **File-artifact reconciliation table** (§3.6). 10 verifier commands; empty cells = Phase 5.5 BLOCK.
3. **Pre-flight len + name check** on `V3_FEATURE_COLUMNS`: catches the case where inherited setup was silently lost during a rebase.
4. **Two-round Critic flow**: any methodology issue surfaces before Phase 6 launches.

### 5.3 NO new model-level risks introduced

The iter-v3/010 changes:
- ZERO new code (only `_build_v3_model` arg edits + ITERATION_LABEL + docstring fix).
- ZERO new features.
- ZERO new dropped features.
- ZERO risk gate changes.
- ZERO CPCV / walk-forward window changes.

The only model-level effect is the new label distribution. Mitigated by:
- Per-symbol IS-only frequency baseline (§2.1) provides a Falsifier-2 reference.
- Critic two-round flow surfaces any unexpected interaction.

---

## Section 6 — Risk Management Design

### 6.1 7-primitive table — IDENTICAL TO iter-v3/006-009

| # | Primitive | Spec | Fire-rate prediction (IS) | Regime coverage |
|---|---|---|---|---|
| 1 | Vol scaling | `scale = clip(atr_pct_rank_200, 0.3, 1.0)` | Always on; mean scale ≈ 0.6 | High-vol → scale down |
| 2 | ADX gate | trade only when ADX > 20 | ≈ 60% of bars pass | Trending only |
| 3 | Hurst regime check | trade only when 0.05 < hurst_100 < 0.95 | ≈ 90% of bars pass | Filters bond-like regimes |
| 4 | Feature z-score OOD | kill if any \|z\| > 2.5 | ≈ 5–8% killed | Distributional drift |
| 5 | Low-vol filter | trade only when atr_pct_rank_200 ≥ 0.33 | ≈ 67% of bars pass | Filters dead chop |
| 6 | Hit-rate feedback | DISABLED | 0% | Reserved for future tuning |
| 7 | BTC trend alignment | kill alt trade fighting BTC 14d ±20% | ≈ 7–8% killed | Macro flips |

Combined kill rate target: 69–78%. SAME as iter-v3/006-009.

**Gate-vs-label independence**: gates fire at trade-entry time on the candle's feature vector. The label change (ATR multipliers) only affects WHICH candles are positively/negatively labeled during training and the per-trade TP/SL price. It does NOT affect gate logic. Verifier command: gates use `atr_pct_rank_200`, `hurst_100`, ADX-from-OHLC, and z-score OOD set, none of which depend on `atr_tp_multiplier` or `atr_sl_multiplier`.

### 6.2 Regime coverage — UNCHANGED

Full v3 universe IS data spans 2022-09-24 → 2025-03-23. Regime coverage includes 2022 LUNA/FTX, 2023 banking, 2024 halving + Trump rally, 2025 January correction.

### 6.3 Concentration — informational only under EXPLORATION

iter-v3/009 OOS showed 98.61% LDO concentration (single-seed, lottery). Concentration is NOT a gate for iter-v3/010 per TYPE=EXPLORATION; it is informational only. The label change may shift concentration in either direction (faster TP frequency on liquid symbols vs slower on illiquid ones); diary captures.

---

## Section 7 — Pre-Registered Failure-Mode Prediction

iter-v3/004's 5/5 calibration win, iter-v3/006's 5/5 win, iter-v3/007's 2/5 partial-win, and iter-v3/009's 0/3 model-prediction miss establish the discipline. iter-v3/010 inherits and refines.

**Prediction P1 (process, P=5%)**: the ATR multiplier change in `_build_v3_model` doesn't propagate to the actual labeling code (e.g., a downstream cache stamps the old labels, or the LightGBM strategy fixture uses hardcoded multipliers). **Detection signal**: pre-flight check via grep + runtime banner showing the multipliers; comparison.csv produces IS Sharpe identical to iter-v3/009's +0.0802 (impossible if labels actually changed). **Mitigation**: pre-flight grep verifies `atr_tp_multiplier=2.0` AND `atr_sl_multiplier=1.0`; runtime banner from LightGbmStrategy reports the multipliers it sees (sub-fix #6 verifier).

**Prediction P2 (process, P=10%)**: wall-clock overshoots 30 min on full v3 universe at exploration config. iter-v3/009 ran in 11 min on the same config + same 4 symbols; the labeling change is expected to produce ~1.45× more trades (267 → 387) which marginally increases run time. **Detection signal**: total Phase 6 wall-clock > 30 min on full universe. **Mitigation**: 2h hard cap (cadence rule). Engineer kills if exceeded; iter-v3/011 EXPLORATION re-scopes.

**Prediction P3 (process, P=5%)**: docstring fix accidentally breaks `_verify_feature_columns()` runtime check (e.g., a syntax error in the f-string substitution, or the runtime check no longer asserts `len == 13`). **Detection signal**: pre-flight pytest fails OR runtime banner shows wrong feature count. **Mitigation**: pre-flight test pass requirement (sub-fix #5 verifier); the docstring fix is an inert-by-default cosmetic change with one regex replacement; reviewing the diff before commit catches any syntax issue.

**Prediction P4 (model, P=50%)**: IS Sharpe lands in [+0.10, +0.30] (predicted band; tighter labels work). EXPLORATION-PROMISING. The (2.0, 1.0) labels yield more frequent decisions per regime, and at colsample=1.0 the model has more data points to fit, which may compensate for the smaller per-trade signal magnitude.

**Prediction P5 (model, P=30%)**: IS Sharpe drops below +0.10 (Falsifier 1 activates). Tighter labels hurt — the model's edge lives in slower, larger moves and the (2.0, 1.0) ratio over-decides. EXPLORATION-NEGATIVE on this axis. Catalog third row; iter-v3/011 pivots to a DIFFERENT non-features axis (risk gate threshold, BTC trend filter band, OOD threshold).

**Prediction P6 (model, P=15%)**: trade frequency rises to 2× or more iter-v3/009's count (i.e., > 534 IS trades), suggesting the (2.0, 1.0) ratio is structurally noisy — the SL is firing too often. EXPLORATION-NEGATIVE on Falsifier 1 likely (more decisions = more noise unless edge per-trade is strong, which the IS Sharpe will show). The Falsifier-2 floor (≥ iter-v3/009's count) is satisfied trivially in this branch, but Falsifier-1 likely triggers.

The predictions are intentionally Bayesian-calibrated:
- 3 process-level (P1, P2, P3) per iter-v3/003 lesson #3 discipline
- 3 model-level (P4, P5, P6) covering predicted-band, undershoot, overshoot
- Per iter-v3/009 calibration miss: features-axis priors were 60/15/25 (PROMISING / drop-helps / drop-hurts) and reality was below-floor; labeling-axis priors here reflect the wider variance of labeling perturbations as 50/30/15 (PROMISING / hurts / overshoot-also-hurts).

Summary: **EXPLORATION-PROMISING pathway probability ≈ 50%** (P4); EXPLORATION-NEGATIVE ≈ 45% (P5+P6); process abort ≈ 5% (P1+P2+P3 ≈ 20% but each individually triggers a remediation, not a verdict change).

If any prediction fails to materialize, the iter-v3/010 diary documents the calibration miss.

---

## Section 8 — Pre-Registered EXPLORATION Criteria

**These thresholds are LOCKED before backtest. Phase 7 evaluation applies them mechanically.**

iter-v3/010 is an **EXPLORATION iteration** per Section 0.5. Headline-metric criteria from CONFIRMATION iterations (DSR > 0.95, PSR > 0.95, OOS Sharpe > 1.0) are NOT in scope. Critic emits `EXPLORATION-PROMISING`, `EXPLORATION-NEGATIVE`, or `BLOCK`.

### EXPLORATION-PROMISING iff ALL 10 of the following are true:

| # | Criterion | Threshold | Source |
|---|---|---:|---|
| 1 | TYPE=EXPLORATION declared in Section 0.5 | TRUE | §0.5 |
| 2 | Single-axis variation only (labeling) | TRUE | §3.7 |
| 3 | Wall-clock < 2h (target < 30 min) | TRUE | §3.6 row 9 |
| 4 | `--exploration --seeds 1 --n-trials 10` used | TRUE | §3.5 sub-fix #6 |
| 5 | 35/35 adversarial tests pass | TRUE | §3.6 row 8 |
| 6 | `atr_tp_multiplier=2.0` AND `atr_sl_multiplier=1.0` confirmed at runtime | TRUE | §3.6 rows 2,3 |
| 7 | `comparison.csv` produced (basic headline metrics) | TRUE | §3.6 row 6 |
| 8 | Critic OVERALL = `EXPLORATION-PROMISING` or `EXPLORATION-NEGATIVE` (NOT BLOCK) | enum | Phase 7.5 |
| 9 | NO 5-seed or CONFIRMATION-style runs | TRUE (vacuous; --seeds 1) | §3.7 |
| 10 | Catalog updated post-Phase-8 with iter-v3/010 row | TRUE | post-iteration mechanic |

### EXPLORATION-NEGATIVE iff:

- Criteria 1-7, 9, 10 PASS BUT Critic OVERALL = `EXPLORATION-NEGATIVE` (because IS Sharpe < +0.10, falsifier 1, OR IS trades < iter-v3/009's 267, falsifier 2)

### BLOCK (process) iff ANY of:

- Criteria 1-7, 9 fail (process-level)
- Phase 5.5 gate emits BLOCK
- Phase 7.5 Critic emits explicit BLOCK
- Wall-clock exceeds 2h hard cap

### Discretionary judgment — EXPLORATION pathway

iter-v3/010 has NO MERGE pathway because the iteration TYPE is EXPLORATION. The "MERGE pathway" is `EXPLORATION-PROMISING`, which is a forward-pointer: it adds one row to the catalog and counts toward the 10 EXPLORATION quota. **iter-v3/010 NEVER updates BASELINE_V3.md.**

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

**No new external deps.** Same stack as iter-v3/007-009. The iteration's NEW code is:
- 1 analysis script + 2 outputs (committed at SHA `80332c1`)
- 3 cosmetic `run_baseline_v3.py` line edits (Engineer ships in Phase 6): `atr_tp_multiplier`, `atr_sl_multiplier`, `ITERATION_LABEL`
- 1 docstring fix in `_verify_feature_columns()` (per Critic Rec 3)
- 0 new pytest test files
- 0 modifications to per-cell PBO / DSR / PSR / ADF code paths

### Aggregator strategy — UNCHANGED

Per-cell PBO with cross-cell mean aggregation. Per-cell n_eff with cross-cell median aggregation.

### Reproducibility stamp

The Engineer's Phase 6 writes `briefs-v3/iteration_v3-010/engineering_report.md` with:
- The git commit SHAs at backtest time (expected: `80332c1` analysis + the new sub-fix SHA)
- Output of `uv pip list | grep -E "(numpy|scipy|statsmodels|scikit-learn|lightgbm|pytest|pandas|pyarrow)"`
- The full 13-feature list as actually trained on (sanity check against §3.3)
- The runtime ATR multipliers (sanity check against §3.5 sub-fixes #1, #2)
- The `comparison.csv` IS / OOS monthly Sharpe values
- The total IS trade count (Falsifier 2 reference)
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
| 0.5 — Iteration Type Declaration | PASS — TYPE: EXPLORATION declared; cadence catalog reference; explicit "NEVER updates BASELINE_V3.md"; non-features axis chosen per Critic FINAL Rec 1 |
| 1 — Hypothesis | PASS — one sentence; testable target IS Sharpe ≥ +0.10 (Falsifier 1); falsifiers in §4.3 |
| 2 — IS-Only Numerical Evidence | PASS — `analysis/iteration_v3-010/atr_multiplier_demo.py` committed at SHA `80332c1` BEFORE this brief; per-symbol baseline + projected shift tables |
| 3 — Proposed Changes | PASS — symbols UNCHANGED; labeling CHANGED (single-axis); features UNCHANGED; risk gates UNCHANGED; sub-fix decomposition with reconciliation table 10 verifiers; inheritance plan §3.8 |
| 4 — Expected OOS Impact | PASS — predicted IS Sharpe range [-0.20, +0.40]; 4 falsifiers in §4.3; EXPLORATION pathway in §4.4 |
| 5 — Risk Mitigation | PASS — 3 cadence-discipline structural safeguards in §5.1 + 4 methodology-pipeline safeguards in §5.2 |
| 6 — Risk Management Design | PASS — 7-primitive table identical to iter-v3/006-009; gate-vs-label independence verified |
| 7 — Pre-Registered Failure-Mode | PASS — 6 predictions with **3 process-level (P1, P2, P3)**; calibrated PROMISING prior at ~50% (reflecting iter-v3/009 calibration miss + labeling-axis variance) |
| 8 — Pre-Registered EXPLORATION Criteria | PASS — 10 EXPLORATION criteria; EXPLORATION-PROMISING / EXPLORATION-NEGATIVE / BLOCK pathways; explicit "NEVER updates BASELINE_V3.md" |
| 9 — Library Stack | PASS — no new deps; aggregator strategy unchanged from iter-v3/006-009 |

Engineer: please run Phase 5.5 gate verification against the brief-vs-code reconciliation table in Section 3.6. Empty cells in the right column = BLOCK. Verifier commands that do NOT execute and exit 0 post-Phase 6 = NO-MERGE per Section 8.
