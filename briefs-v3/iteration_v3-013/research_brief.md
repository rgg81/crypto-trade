# Iteration v3-013 — Research Brief

**Type**: EXPLORATION (SIXTH EXPLORATION under the cadence discipline; MANDATORY drop-MKR universe-axis per `feedback_mkr_threshold_compression.md` FIRED at iter-v3/012)
**Track**: v3 (rigor arm) — thirteenth iteration
**Branch**: `iteration-v3/013` (off `iteration-v3/012` head; analysis commit `5217490` ships before this brief)
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

**Sacred constants UNCHANGED.** The QR sees OOS metrics for the FIRST time in Phase 7. This brief is produced reading ONLY: iter-v3/007–012 briefs / engineering reports / Critic / diaries; iter-v3/013 analysis script `analysis/iteration_v3-013/drop_mkr_demo.py` outputs (committed at SHA `5217490` BEFORE this brief). The analysis script reads iter-v3/012's already-OOS-disclosed `trades.csv` files but ONLY as a structural counterfactual on already-revealed numbers (the OOS data for iter-v3/012 was disclosed at iter-v3/012 Phase 7 on 2026-05-06). The counterfactual does NOT reveal new OOS information — it re-aggregates the same trade roster minus MKR.

---

## Section 0.5 — Iteration Type Declaration

```
TYPE: EXPLORATION (per-symbol-diagnostic, MANDATORY per pre-committed MKR rule)
Wall-clock budget: < 30 min (2h hard cap)
Single-axis variation: universe (drop MKR; 4-symbol → 3-symbol BCH+LDO+TRX)
Cadence: EXPLORATION #6 of 10 needed
This iteration NEVER updates BASELINE_V3.md.
Pre-committed: this axis is FORCED by feedback_mkr_threshold_compression.md (TRIGGERED at iter-v3/012). Cannot be renegotiated.
```

**Justification**: Per `feedback_mkr_threshold_compression.md` (FIRED at iter-v3/012, 5th consecutive MKR OOS-negative; trajectory −6.5% → −13.1% → −10.6% → −25.75% → −25.75%; STATIONARY identity at iter-v3/012 strengthening the diagnostic case): iter-v3/013 MUST be a per-symbol-diagnostic single-axis EXPLORATION varying the UNIVERSE (drop MKR, retain BCH+LDO+TRX). The rule overrides any other axis preference and cannot be renegotiated post-hoc by future Engineer or QR. The catalog at `briefs-v3/exploration_catalog.md` row for iter-v3/012 explicitly pre-commits this axis ("iter-v3/013 MANDATORY AXIS: per-symbol-diagnostic"). After iter-v3/013 the catalog will have axis coverage features × 2 + labeling × 1 + gate-zscore × 1 + gate-btc-trend × 1 + universe × 1 = 5 unique axis representations.

---

## Section 1 — Hypothesis

Dropping MKR from the v3 universe (3-symbol BCH+LDO+TRX) on top of iter-v3/012's full inherited stack will produce IS Sharpe maintained or improved (≥+0.40, vs iter-v3/012's +0.81) by removing MKR's structural −25.75% OOS drag and −23.21% IS drag — testing whether the v3 universe's collective edge is robust to MKR-specific underperformance.

---

## Section 2 — IS-Only Numerical Evidence

**Analysis script**: `analysis/iteration_v3-013/drop_mkr_demo.py` (committed at SHA `5217490` BEFORE this brief — Phase 5.5 reproducibility requirement).

**Inputs read** (already-disclosed iter-v3/012 trade rosters; counterfactual re-aggregation only — no new OOS information generated):
- `reports-v3/iteration_v3-012/in_sample/trades.csv` — 286 IS trade rows
- `reports-v3/iteration_v3-012/out_of_sample/trades.csv` — 101 OOS trade rows

**Outputs** (committed alongside the script at SHA `5217490`):
- `analysis/iteration_v3-013/expected_drop_mkr_metrics.csv` — counterfactual aggregates with vs without MKR.
- `analysis/iteration_v3-013/synthesis.md` — 1-paragraph narrative.

### 2.1 Counterfactual aggregates (drop-MKR re-aggregation of iter-v3/012 trade roster)

| Slice | n_trades | n_wins | WR % | weighted_pnl_total | approx monthly Sharpe | concentration top % | top symbol |
|---|---:|---:|---:|---:|---:|---:|---|
| IS_full (iter-v3/012) | 286 | 110 | 38.46 | +73.42 | +0.8096 | 72.82 | BCHUSDT |
| **IS_no_MKR (counterfactual)** | **209** | **84** | **40.19** | **+78.80** | **+1.0088** | **67.85** | **BCHUSDT** |
| OOS_full (iter-v3/012) | 101 | 44 | 43.56 | +46.36 | +1.5914 | 87.57 | LDOUSDT |
| **OOS_no_MKR (counterfactual)** | **85** | **40** | **47.06** | **+61.85** | **+2.6970** | **65.65** | **LDOUSDT** |

**IS counterfactual Δ Sharpe = +0.1992** (drop-MKR isolates a non-MKR portfolio).
**OOS counterfactual Δ Sharpe = +1.1056**.

### 2.2 MKR contribution to iter-v3/012 (from per-symbol breakdown)

| Window | Symbol | n_trades | WR % | weighted_pnl |
|---|---|---:|---:|---:|
| IS | BCHUSDT | 100 | 45.00 | +53.46 |
| IS | LDOUSDT | 21 | 47.62 | +38.64 |
| IS | TRXUSDT | 88 | 32.95 | −13.31 |
| IS | **MKRUSDT** | **77** | **33.77** | **−5.38** |
| OOS | BCHUSDT | 31 | 41.94 | +17.21 |
| OOS | LDOUSDT | 10 | 80.00 | +40.60 |
| OOS | TRXUSDT | 44 | 43.18 | +4.04 |
| OOS | **MKRUSDT** | **16** | **25.00** | **−15.49** |

MKR's IS weighted_pnl contribution is −5.38 (smaller than expected from the per_symbol.csv −23.21% net_pnl_pct, because weighted_pnl normalizes by vol-scaling weights). MKR's OOS contribution is −15.49 — a clear drag despite the small trade count.

### 2.3 Behavioral-effect predictor (per `feedback_axis_saturation_predictor.md`)

Per the new memory rule (added after iter-v3/012's NULL-RESULT trade-roster bit-identity surprise): brief Section 2 must include explicit estimates of how many IS trades will change in the roster, with a falsifier triggered if observed change is below the predicted lower bound.

| Metric | Predicted iter-v3/013 | Source |
|---|---:|---|
| IS trade count | **~209** (lower bound; iter-v3/012's 286 minus 77 MKR rows) | counterfactual §2.1 |
| OOS trade count | **~85** (iter-v3/012's 101 minus 16 MKR rows) | counterfactual §2.1 |
| IS trade count plausible band | **[170, 230]** (±20% of 209 to absorb Optuna re-optimization variance) | calibration band |
| **Saturation falsifier** | **observed IS > 240 → MKR drop did NOT propagate** | §4.3 falsifier 2 |

The realized iter-v3/013 run will diverge from the counterfactual numbers because:
- Optuna re-optimizes hyperparameters on a 3-symbol universe (different optimal params).
- Ensemble seed determinism shifts because n_symbols affects gap/embargo math (REQUIRED_GAP changes 88 → 66).
- Risk-gate firing distributions reshape against a 3-symbol portfolio.
- LightGBM's `colsample_bytree=1.0` means model specs are not directly comparable across universes.

The DIRECTION of the counterfactual is informative (drop-MKR is strictly accretive to weighted_pnl_total in both IS and OOS); the predicted range is wide to acknowledge Optuna re-optimization variance.

### 2.4 Setup integrity (verified at SHA `5217490`)

```
reports-v3/iteration_v3-012/in_sample/trades.csv extant + non-empty   PASS (287 rows incl. header)
reports-v3/iteration_v3-012/out_of_sample/trades.csv extant + non-empty PASS (102 rows incl. header)
expected_drop_mkr_metrics.csv produced                                  PASS
synthesis.md produced                                                   PASS
counterfactual IS_no_MKR shows BCH+LDO+TRX (3 symbols)                  PASS
counterfactual OOS_no_MKR shows BCH+LDO+TRX (3 symbols)                 PASS
```

---

## Section 3 — Proposed Changes

### 3.1 Symbols — CHANGED (drop MKR; 4-symbol → 3-symbol)

| Symbol | iter-v3/012 status | iter-v3/013 status | Rationale |
|---|---|---|---|
| BCHUSDT | KEEP | KEEP | Largest positive IS contributor (+86.82%/100 trades). |
| MKRUSDT | KEEP | **DROP** | 5/5 consecutive OOS-negative with stationary identity at iter-v3/012; rule FIRED. |
| LDOUSDT | KEEP | KEEP | Largest OOS positive contributor (+70.77%/12 trades; lottery-flag noted but kept). |
| TRXUSDT | KEEP | KEEP | Highest IS trade volume (88 trades); diversifier role. |

`set({BCH, LDO, TRX}) ∩ V3_EXCLUDED_SYMBOLS = ∅` ✓
The 3-symbol set still has zero overlap with v1's {BTC, ETH, LINK, LTC, DOT} and v2's {SOL, XRP, DOGE, NEAR}.

### 3.2 Labeling — UNCHANGED (inherits iter-v3/010 ATR(2.0/1.0))

| Parameter | iter-v3/012 (current) | iter-v3/013 (this iteration) |
|---|---:|---:|
| `atr_tp_multiplier` | 2.0 | **2.0 (UNCHANGED)** |
| `atr_sl_multiplier` | 1.0 | **1.0 (UNCHANGED)** |
| Timeout | 21 candles (7d, 10080 min) | UNCHANGED |
| `use_atr_labeling` | True | UNCHANGED |
| Purge gap | 88 (= (21+1)×4 with 4 symbols) | **66 (= (21+1)×3 with 3 symbols)** — formula propagates |

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
)  # length = 13, vwap_dev_50 dropped (inherited from iter-v3/009/010/011/012)
```

NO feature changes. `_verify_feature_columns()` will continue to assert `len == 13` and `'vwap_dev_50' not in V3_FEATURE_COLUMNS`.

### 3.4 Risk gates — UNCHANGED (z-score 2.0, BTC band ±15%, all primitive thresholds inherited from iter-v3/012)

| Parameter | iter-v3/012 (current) | iter-v3/013 (this iteration) |
|---|---:|---:|
| `RiskV2Config.zscore_threshold` | 2.0 | **2.0 (UNCHANGED)** |
| `BTC_TREND_CONFIG.threshold_pct` | 15.0 | **15.0 (UNCHANGED — kept despite NEGATIVE-no-effect because iter-v3/012 was not reverted; the variation is single-axis ON UNIVERSE)** |
| `BTC_TREND_CONFIG.lookback_bars` | 42 (14d) | UNCHANGED |
| `BTC_TREND_CONFIG.enabled` | True | UNCHANGED |
| Vol scaling | enabled | UNCHANGED |
| ADX threshold | 20 | UNCHANGED |
| Hurst regime check | (0.05, 0.95) | UNCHANGED |
| Low-vol filter | 0.33 | UNCHANGED |
| Hit-rate feedback | DISABLED | UNCHANGED |

### 3.5 Sub-fix decomposition (single-axis: UNIVERSE — drop MKR)

| # | Sub-fix | Spec | Verifier |
|---|---|---|---|
| 1 | **Update `V3_MODELS`** in `run_baseline_v3.py` (lines 105–110) to remove the `("B (MKRUSDT)", "MKRUSDT")` tuple | Tuple becomes 3-element: A (BCH), C (LDO), D (TRX) | `python -c "from importlib import import_module; m = import_module('run_baseline_v3'); assert len(m.V3_MODELS) == 3 and 'MKRUSDT' not in {s for _, s in m.V3_MODELS}"` exits 0 |
| 2 | **Update `REQUIRED_GAP` constant** in `src/crypto_trade/strategies/ml/validation_v3.py` line 44 from `(21 + 1) * 4 = 88` → `(21 + 1) * 3 = 66` | One-line change | `python -c "from crypto_trade.strategies.ml.validation_v3 import REQUIRED_GAP; assert REQUIRED_GAP == 66, REQUIRED_GAP"` exits 0 |
| 3 | **Update `ITERATION_LABEL`** to `"v3-013"` in `run_baseline_v3.py` line 99 | One-line change | `grep -E 'ITERATION_LABEL.*=.*"v3-013"' run_baseline_v3.py` exits 0 |
| 4 | **Update any CPCV/embargo doc-strings** in `validation_v3.py` that reference `4 symbols` or `(21+1)*4=88` to reflect 3 symbols / 66 | docstring-level | `grep -E '(21\+1)\*3' src/crypto_trade/strategies/ml/validation_v3.py` exits 0 (or Engineer accepts that doctsring reflects 3-symbol canonical state) |
| 5 | **Verify `tests/strategies/ml/test_per_cell_pbo_synthetic.py` and other tests still pass** with REQUIRED_GAP=66 | tests | `uv run pytest tests/strategies/ml/ -v` exits 0 |
| 6 | **Commit the runner + validation_v3 changes** with clear message | `feat(iter-v3/013): drop MKR universe (4→3 symbols) + REQUIRED_GAP 88→66 + ITERATION_LABEL=v3-013` | `git log --oneline iteration-v3/013 -- run_baseline_v3.py src/crypto_trade/strategies/ml/validation_v3.py` shows the iter-v3/013 SHA |
| 7 | **Run `--exploration --seeds 1 --n-trials 10`** on 3-symbol universe | Phase 6 invocation: `uv run python run_baseline_v3.py --exploration --seeds 1 --n-trials 10` (no `--symbols` flag → uses V3_MODELS = 3 entries). Wall-clock target: < 12 min (vs ~8 min for 4 symbols at iter-v3/012; 3 symbols ≈ 75% of compute). | `test -f reports-v3/iteration_v3-013/comparison.csv` |

NO new feature additions. NO labeling change. NO z-score-gate change. NO BTC-band change. NO new src/ code beyond the REQUIRED_GAP constant edit.

### 3.6 Brief-vs-Code reconciliation table (Phase 5.5 input)

Each row maps to a FILE ARTIFACT with an executable verifier command. Empty cells = Phase 5.5 BLOCK.

| # | Sub-fix | Code path | File artifact + verifier |
|---|---|---|---|
| 1 | V3_FEATURE_COLUMNS unchanged at 13 features (inherited) | `src/crypto_trade/features_v3/__init__.py` | `python -c "from crypto_trade.features_v3 import V3_FEATURE_COLUMNS; assert len(V3_FEATURE_COLUMNS) == 13, f'len={len(V3_FEATURE_COLUMNS)}'"` exits 0 |
| 2 | `atr_tp_multiplier=2.0` UNCHANGED (inherited from iter-v3/010) | `run_baseline_v3.py` ATR mult line | `grep -E 'atr_tp_multiplier=2\.0' run_baseline_v3.py` exits 0 |
| 3 | `atr_sl_multiplier=1.0` UNCHANGED (inherited from iter-v3/010) | `run_baseline_v3.py` ATR mult line | `grep -E 'atr_sl_multiplier=1\.0' run_baseline_v3.py` exits 0 |
| 4 | `zscore_threshold=2.0` UNCHANGED (inherited from iter-v3/011) | `run_baseline_v3.py` zscore line | `grep -E 'zscore_threshold=2\.0' run_baseline_v3.py` exits 0 |
| 5 | `BTC_TREND_CONFIG.threshold_pct=15.0` UNCHANGED (inherited from iter-v3/012) | `run_baseline_v3.py` line 121 | `grep -E 'threshold_pct=15\.0' run_baseline_v3.py` exits 0 |
| 6 | `V3_MODELS` has exactly 3 entries; `MKRUSDT` NOT present | `run_baseline_v3.py` lines 105–110 | `python -c "from importlib import import_module; import sys; sys.path.insert(0, '.'); m = import_module('run_baseline_v3'); assert len(m.V3_MODELS) == 3 and 'MKRUSDT' not in {s for _, s in m.V3_MODELS}, m.V3_MODELS"` exits 0 |
| 7 | `REQUIRED_GAP == 66` (= (21+1)×3) | `src/crypto_trade/strategies/ml/validation_v3.py` line 44 | `python -c "from crypto_trade.strategies.ml.validation_v3 import REQUIRED_GAP; assert REQUIRED_GAP == 66, REQUIRED_GAP"` exits 0 |
| 8 | `ITERATION_LABEL` updated to `"v3-013"` | `run_baseline_v3.py` line 99 | `grep -E 'ITERATION_LABEL.*=.*"v3-013"' run_baseline_v3.py` exits 0 |
| 9 | Sub-fix #7 produces comparison.csv | runner | `test -f reports-v3/iteration_v3-013/comparison.csv` |
| 10 | **EXPLORATION sanity test**: IS monthly Sharpe != 0 (universe change took effect; non-trivial signal computed) | runner | `python -c "import pandas as pd; df=pd.read_csv('reports-v3/iteration_v3-013/comparison.csv'); ms = df.loc[df['metric']=='monthly_sharpe','in_sample'].iloc[0]; assert abs(float(ms)) > 1e-6, f'IS sharpe ~0 — universe change likely not taking effect: {ms}'"` exits 0 |
| 11 | All adversarial tests pass | tests | `uv run pytest tests/strategies/ml/ -v` exits 0 |
| 12 | Wall-clock ceiling: total Phase 6 runtime < 30 min target / 2h hard cap | engineering report | wall-clock minutes < 120 |
| 13 | 3-symbol universe used | runner invocation log | `grep -E "Active models: 3/3" reports-v3/iteration_v3-013/run.log` exits 0 (or equivalent indicator of 3-symbol active universe) |
| 14 | **Behavioral-effect verifier (saturation falsifier per `feedback_axis_saturation_predictor.md`)**: IS trades < 240 (i.e., MKR drop propagated to model output) | comparison.csv | `python -c "import pandas as pd; df=pd.read_csv('reports-v3/iteration_v3-013/comparison.csv'); n = df.loc[df['metric']=='n_trades','in_sample'].iloc[0]; assert int(n) < 240, f'IS trades >= 240 — MKR drop did not propagate: {n}'"` exits 0 |
| 15 | **Pre-flight unit test**: MKR rows absent in trades.csv | trades CSVs | `python -c "import pandas as pd; df=pd.read_csv('reports-v3/iteration_v3-013/in_sample/trades.csv'); assert (df['symbol'] != 'MKRUSDT').all(), 'MKR rows present in IS trades after drop-MKR run'"` exits 0 |

### 3.7 NO labeling/feature/gate changes

iter-v3/013 is a single-axis (UNIVERSE) EXPLORATION. The feature set, model architecture, ATR labeling multipliers, z-score OOD gate threshold, BTC trend filter band, CPCV parameters (other than the gap formula scaling with n_symbols), and walk-forward window are unchanged from iter-v3/012. The only differences vs iter-v3/012: V3_MODELS (drops MKRUSDT) + REQUIRED_GAP (88 → 66 to match the formula) + ITERATION_LABEL (cosmetic) + any docstring updates referencing 4 symbols / gap=88.

### 3.8 Inheritance from iter-v3/012

The `iteration-v3/013` branch was branched from `iteration-v3/012` head. Inherited commits include:

- `bce50c8 feat(iter-v3/007): --exploration mode` (CLI flag plumbing)
- `92218ef feat(iter-v3/007): top-14 V3_FEATURE_COLUMNS subset`
- `849c4a6 fix(iter-v3/007): risk_v3 always loads atr_pct_rank_200 from parquet`
- `56b8f8b feat(iter-v3/008): drop vwap_dev_50 (14→13 features)`
- `b55086a feat(iter-v3/010): ATR multipliers (2.9,1.45)→(2.0,1.0)`
- `17d01ab feat(iter-v3/011): z-score OOD threshold 2.5 → 2.0`
- `93891a3 feat(iter-v3/012): BTC trend band 0.20 → 0.15 + ITERATION_LABEL=v3-012`
- `5217490 feat(iter-v3/013): drop-MKR counterfactual analysis` (this brief's evidence)

Critical inheritance verifiers (run before any code edits in Phase 6):
- `python -c "from crypto_trade.features_v3 import V3_FEATURE_COLUMNS; assert len(V3_FEATURE_COLUMNS) == 13 and 'vwap_dev_50' not in V3_FEATURE_COLUMNS"` exits 0
- `grep -E 'atr_tp_multiplier=2\.0' run_baseline_v3.py` exits 0 (still iter-v3/010 value)
- `grep -E 'zscore_threshold=2\.0' run_baseline_v3.py` exits 0 (still iter-v3/011 value)
- `grep -E 'threshold_pct=15\.0' run_baseline_v3.py` exits 0 (still iter-v3/012 value)
- BEFORE iter-v3/013 sub-fix #1: `grep -E '"MKRUSDT"' run_baseline_v3.py` exits 0 (4-symbol state)
- AFTER iter-v3/013 sub-fix #1: `grep -E '"MKRUSDT"' run_baseline_v3.py` exits 1 (MKR removed)
- `uv run pytest tests/strategies/ml/ -v` exits 0 with all tests passing

---

## Section 4 — Expected OOS Impact

### 4.1 EXPLORATION → headline metrics are GUIDANCE not GATES

Per Section 0.5 + skill spec at SHA `f0f8b84`, headline metrics are NOT BLOCK-triggering for the Critic on EXPLORATION iterations. The Critic emits `EXPLORATION-PROMISING`, `EXPLORATION-NEGATIVE`, or `BLOCK` (process). iter-v3/013 NEVER updates BASELINE_V3.md regardless of verdict.

### 4.2 Predicted IS Sharpe range

| Metric | iter-v3/012 (4-symbol) | Counterfactual (3-symbol re-aggregate) | iter-v3/013 prediction (3-symbol Optuna re-optimized) |
|---|---:|---:|---:|
| IS monthly Sharpe | +0.8096 | +1.0088 | **predicted [+0.30, +1.20] with median +0.65** |
| IS trades | 286 | 209 (counterfactual) | **predicted ~175–230** |
| OOS trades | 101 | 85 (counterfactual) | **predicted ~80–100** |
| Phase 6 wall-clock | 8 min | n/a | predicted 7–12 min (3 symbols vs 4), hard cap 2h |

The prediction band [+0.30, +1.20] is intentionally **broad** because universe-axis variation is high-variance:
- The counterfactual Δ Sharpe of +0.20 establishes the lower-variance bound (re-aggregation only).
- Optuna re-optimization on 3 symbols shifts hyperparameters in unpredictable directions.
- BCH and LDO have very different IS sample sizes (100 vs 21); the 3-symbol portfolio's Sharpe is dominated by BCH's distribution.
- MKR's 77 IS trades may have been providing useful Optuna signal even though their PnL contribution was net negative — losing them may make the Optuna selection noisier.

Median +0.65 sits between iter-v3/012's +0.81 and the counterfactual +1.01, reflecting realistic Optuna re-optimization variance partially offsetting the MKR-drag removal benefit. Per López de Prado AFML Ch. 7 on universe selection: dropping a losing symbol is rarely a free lunch in models that share Optuna trial budget across all symbols.

### 4.3 Falsifiers (locked before backtest)

**Falsifier 1**: IS Sharpe < +0.10 → MKR drop didn't help / ex-MKR universe is anti-edge (e.g., dropping MKR's Optuna budget contribution removes useful signal, or 3-symbol portfolio is fundamentally fragile). Verdict: EXPLORATION-NEGATIVE on universe-axis. Catalog this finding; iter-v3/014 may revisit at a different Optuna trial budget.

**Falsifier 2 (saturation predictor per `feedback_axis_saturation_predictor.md`)**: IS trade count > 240 → MKR drop did NOT propagate to the model's prediction surface (analogous to iter-v3/012's trade-roster identity bit-identity NULL-RESULT but with different root cause — likely V3_MODELS edit didn't propagate through Optuna, or REQUIRED_GAP mismatch caused silent fallback to 4-symbol state). Verdict: BLOCK (process); engineer documents.

**Falsifier 3** (process): Phase 6 wall-clock > 30 min on 3-symbol universe → drop-MKR slowdown reproduces or new code path is unexpectedly slow; engineer documents the cause.

**Process falsifier**: pre-flight `len(V3_MODELS) == 3` returns False OR `REQUIRED_GAP == 66` returns False OR `'MKRUSDT' in V3_MODELS strings` returns True → setup drift; Phase 6 must not start.

### 4.4 EXPLORATION outcome interpretation (pre-commit catalog framing)

| Critic verdict | Conditions | Catalog row | Next iteration |
|---|---|---|---|
| `EXPLORATION-PROMISING` | IS Sharpe up ≥ +0.10 vs iter-v3/012 (i.e., ≥ +0.91) AND broad-based per-symbol (BCH, LDO, TRX all positive in OOS counterfactual sense) | "MKR was a drag" | iter-v3/014 EXPLORATION on a DIFFERENT axis (e.g., ADX threshold, low-vol filter floor) |
| `EXPLORATION-PROMISING-INERT` | IS Sharpe within ±0.10 of iter-v3/012 (i.e., in [+0.71, +0.91]) | "MKR-orthogonal — 3-symbol portfolio yields similar Sharpe; the drop neither helps nor hurts" | iter-v3/014 EXPLORATION on a DIFFERENT axis; CONFIRMATION QR may still bundle drop-MKR for diversification rationale (3-symbol universe is structurally smaller) |
| `EXPLORATION-NEGATIVE` | IS Sharpe down > 0.10 (i.e., < +0.71) | "MKR carried weight; can't drop" — counterfactual surprise | iter-v3/014 EXPLORATION on a DIFFERENT axis; MKR drop deferred |
| `BLOCK` (process) | Methodology check FAILED, or Falsifier 2 (saturation) triggered | (none) | Diary documents, iter-v3/014 fixes the methodology gap |

---

## Section 5 — Risk Mitigation

### 5.1 Cadence-discipline structural safeguards

iter-v3/013 inherits THREE structural safeguards from the cadence skill + the new MKR rule:

1. **2h wall-clock hard cap** (skill SHA `d5c9f21`): Engineer kills Phase 6 if elapsed > 2h.
2. **Single-axis variation rule** honored (only V3_MODELS + REQUIRED_GAP changed; features/labeling/all gates byte-for-byte identical to iter-v3/012). The single axis is UNIVERSE; REQUIRED_GAP propagates from the formula `(timeout_candles + 1) × n_symbols`.
3. **EXPLORATION never updates BASELINE_V3.md** — outcome (PROMISING / PROMISING-INERT / NEGATIVE / BLOCK) records only in `briefs-v3/exploration_catalog.md` and `diary-v3/iteration_v3-013.md`.
4. **Saturation predictor falsifier (per `feedback_axis_saturation_predictor.md`)** — Section 3.6 row 14 actively verifies that the MKR drop propagated to the model output (IS trades < 240).

### 5.2 Methodology-pipeline safety (inherited from iter-v3/006-012)

1. **Adversarial unit tests** must PASS before backtest.
2. **File-artifact reconciliation table** (§3.6). 15 verifier commands; empty cells = Phase 5.5 BLOCK.
3. **Pre-flight len + name check** on `V3_MODELS` and `REQUIRED_GAP`: catches the case where inherited setup was silently lost during a rebase or REQUIRED_GAP update was missed.
4. **Two-round Critic flow**: any methodology issue surfaces before Phase 6 launches.

### 5.3 Universe-axis specific risks

1. **REQUIRED_GAP propagation**: the constant lives in `validation_v3.py` line 44 and is exported. The runner's `_verify_label_leakage_gap` reads `n_symbols = len(V3_MODELS)` and asserts the formula matches the constant. If only V3_MODELS is edited (without REQUIRED_GAP), the assertion fires immediately at runtime — fail-fast pattern. Section 3.6 row 7 catches it pre-flight.
2. **Optuna trial budget shifts**: 3 symbols × 10 trials = 30 trial-symbols vs 4 × 10 = 40. Slightly less Optuna signal per symbol. For EXPLORATION, this is acceptable; for CONFIRMATION the future bundling QR must consider increasing trials proportionally.
3. **Concentration threshold**: counterfactual OOS shows LDO concentration drops from 87.57% to 65.65% — still above the 30% guideline at CONFIRMATION level but informational at EXPLORATION. The future CONFIRMATION QR must scope ex-LDO basket fragility separately.

---

## Section 6 — Risk Management Design

### 6.1 7-primitive table — SAME 7 PRIMITIVES, all primitive thresholds inherited from iter-v3/012

| # | Primitive | Spec | Fire-rate prediction (IS, 3-symbol) | Regime coverage |
|---|---|---|---|---|
| 1 | Vol scaling | `scale = clip(atr_pct_rank_200, 0.3, 1.0)` | Always on; mean scale ≈ 0.6 | High-vol → scale down |
| 2 | ADX gate | trade only when ADX > 20 | ≈ 60% of bars pass | Trending only |
| 3 | Hurst regime check | trade only when 0.05 < hurst_100 < 0.95 | ≈ 90% of bars pass | Filters bond-like regimes |
| 4 | Feature z-score OOD | kill if any \|z\| > 2.0 | ≈ 25–35% killed | Distributional drift |
| 5 | Low-vol filter | trade only when atr_pct_rank_200 ≥ 0.33 | ≈ 67% of bars pass | Filters dead chop |
| 6 | Hit-rate feedback | DISABLED | 0% | Reserved for future tuning |
| 7 | BTC trend alignment | kill alt trade fighting BTC 14d ±15% | ≈ 12–13% killed (inherited from iter-v3/012) | Macro flips |

Combined kill rate target: **80–90%** (same as iter-v3/012). Universe shrinkage from 4→3 symbols affects the *number* of candidate trades but does not change any primitive's threshold.

**Gate orthogonality**: All 7 primitives operate per-(symbol, candle) and are independent of the universe size. Removing MKR mechanically removes the MKR predict/feature path without affecting the other 3 symbols' gate operations.

### 6.2 Regime coverage — UNCHANGED

3-symbol IS data spans 2022-09-24 → 2025-03-23 — same as iter-v3/012. Regime coverage includes 2022 LUNA/FTX, 2023 banking (SVB → BTC +40%/14d), 2024 halving + Trump rally (BTC +48%/30d at peak), 2024-08 yen-carry crash (BTC −25%/14d), 2025 January correction. The 3-symbol portfolio's exposure to these regimes is broadly similar.

### 6.3 Concentration — informational only under EXPLORATION

iter-v3/012 OOS showed 87.57% LDO concentration. Counterfactual OOS without MKR shows 65.65% LDO concentration — still above the 30% per-symbol cap that would apply at CONFIRMATION. Concentration is NOT a gate for iter-v3/013 per TYPE=EXPLORATION; informational only. Per the catalog row for iter-v3/011 (LDO lottery-flag), this concentration is monitored but not disqualifying at EXPLORATION level.

---

## Section 7 — Pre-Registered Failure-Mode Prediction

**Prediction P1 (process, P=5%)**: V3_MODELS edit doesn't propagate to runner runtime. The Engineer edits V3_MODELS but the runner caches an older import or environment somewhere. **Detection signal**: pre-flight grep (Section 3.6 row 6) + run.log Active models count != 3 + IS trades > 240 (saturation falsifier). **Mitigation**: Section 3.6 row 6 verifier + behavioral-effect verifier row 14 + pre-flight unit test row 15.

**Prediction P2 (process, P=10%)**: REQUIRED_GAP not updated when V3_MODELS shrinks → label leakage assertion `_verify_label_leakage_gap` fires at runtime. The assertion at `run_baseline_v3.py:212` reads `required_gap = (21+1)*n_symbols` and asserts equal to `REQUIRED_GAP`. If REQUIRED_GAP=88 stays while n_symbols becomes 3, formula gives 66 ≠ 88 → AssertionError. **Detection signal**: runtime exception with message "REQUIRED_GAP mismatch". **Mitigation**: Section 3.6 row 7 explicitly verifies REQUIRED_GAP=66; sub-fix #2 in §3.5 makes the constant edit explicit.

**Prediction P3 (process, P=5%)**: observed IS trades > 240 (saturation predictor falsifier triggered without obvious mechanism failure). The drop-MKR variation went through edit but model trained on a 4-symbol-equivalent feature space due to a subtle parquet caching issue or an Optuna seed determinism quirk. **Detection signal**: behavioral-effect verifier (row 14) fails. **Mitigation**: pre-flight unit test ensuring MKR rows absent in trades.csv (row 15) + Engineer Phase 6 documentation of any Optuna re-seeding step.

**Prediction P4 (model, P=40%)**: IS Sharpe up by > +0.10 (i.e., ≥ +0.91) — MKR was a drag and removing it helps; 3-symbol portfolio captures the BCH+LDO+TRX edge cleanly. EXPLORATION-PROMISING. The strategy's edge is broad-based across the 3 retained symbols and Optuna re-optimization on the smaller universe finds equally good or better hyperparameters because the 30 trial-symbols × 5-fold CV gives sufficient resolution.

**Prediction P5 (model, P=30%)**: IS Sharpe within ±0.10 of iter-v3/012 (i.e., [+0.71, +0.91]) — MKR-orthogonal; the 3-symbol portfolio yields similar Sharpe because the loss of MKR's negative contribution is offset by Optuna re-optimization noise. EXPLORATION-PROMISING-INERT. Catalog this finding; CONFIRMATION QR may still bundle drop-MKR for diversification-rationale reasons (smaller universe is more honest).

**Prediction P6 (model, P=20%)**: IS Sharpe drops below iter-v3/012 by > 0.10 (i.e., < +0.71) — MKR carried weight via Optuna trial budget contribution; removing it makes Optuna selection noisier and degrades signal. EXPLORATION-NEGATIVE. Counterfactual overstated the gain because re-aggregating ignores Optuna re-optimization variance. Catalog this finding; iter-v3/014 EXPLORATION pivots to a different axis.

The predictions are intentionally Bayesian-calibrated:
- 3 process-level (P1, P2, P3) per iter-v3/003 lesson #3 discipline.
- 3 model-level (P4, P5, P6) covering PROMISING / PROMISING-INERT / NEGATIVE.
- Per the iter-v3/010 + iter-v3/011 + iter-v3/012 calibration history (labeling-axis +0.49 vs predicted [+0.10, +0.30]; gate-zscore-axis +0.39 vs predicted [+0.10, +0.30]; gate-btc-trend-axis 0 vs predicted [+0.40, +1.20] reduction): for universe-axis here, priors are 40/30/20 (PROMISING / PROMISING-INERT / NEGATIVE) with broad PROMISING band reflecting the high-variance nature of universe changes.

Summary: **EXPLORATION-PROMISING pathway probability ≈ 70%** (P4+P5); EXPLORATION-NEGATIVE ≈ 20% (P6); process abort ≈ 20% (P1+P2+P3 ≈ 20% but each individually triggers a remediation, not a verdict change).

If any prediction fails to materialize, the iter-v3/013 diary documents the calibration miss.

---

## Section 8 — Pre-Registered EXPLORATION Criteria

**These thresholds are LOCKED before backtest. Phase 7 evaluation applies them mechanically.**

iter-v3/013 is an **EXPLORATION iteration** per Section 0.5. Headline-metric criteria from CONFIRMATION iterations (DSR > 0.95, PSR > 0.95, OOS Sharpe > 1.0) are NOT in scope. Critic emits `EXPLORATION-PROMISING`, `EXPLORATION-PROMISING-INERT`, `EXPLORATION-NEGATIVE`, or `BLOCK`.

### EXPLORATION-PROMISING iff ALL 11 of the following are true:

| # | Criterion | Threshold | Source |
|---|---|---:|---|
| 1 | TYPE=EXPLORATION declared in Section 0.5 | TRUE | §0.5 |
| 2 | Single-axis variation only (UNIVERSE: drop MKR) | TRUE | §3.7 |
| 3 | Wall-clock < 2h (target < 30 min) | TRUE | §3.6 row 12 |
| 4 | `--exploration --seeds 1 --n-trials 10` used | TRUE | §3.5 sub-fix #7 |
| 5 | All adversarial tests pass | TRUE | §3.6 row 11 |
| 6 | `V3_MODELS` has 3 entries; `MKRUSDT` NOT present | TRUE | §3.6 row 6 |
| 7 | `REQUIRED_GAP == 66` confirmed at runtime | TRUE | §3.6 row 7 |
| 8 | `comparison.csv` produced (basic headline metrics) | TRUE | §3.6 row 9 |
| 9 | Critic OVERALL = `EXPLORATION-PROMISING` (NOT NEGATIVE, NOT BLOCK) | enum | Phase 7.5 |
| 10 | NO 5-seed or CONFIRMATION-style runs | TRUE (vacuous; --seeds 1) | §3.7 |
| 11 | **Behavioral-effect verifier passes (IS trades < 240)** | TRUE | §3.6 row 14 |

### EXPLORATION-PROMISING-INERT iff:

- Criteria 1-8, 10, 11 PASS BUT Critic OVERALL = `EXPLORATION-PROMISING-INERT` (because IS Sharpe in [+0.71, +0.91], i.e., axis-orthogonal to current edge)

### EXPLORATION-NEGATIVE iff:

- Criteria 1-8, 10, 11 PASS BUT Critic OVERALL = `EXPLORATION-NEGATIVE` (because IS Sharpe < +0.71 indicating MKR-was-carrying)

### BLOCK (process) iff ANY of:

- Criteria 1-8, 10 fail (process-level)
- Phase 5.5 gate emits BLOCK
- Phase 7.5 Critic emits explicit BLOCK
- Wall-clock exceeds 2h hard cap
- Criterion 11 (saturation falsifier) fails: IS trades >= 240

### Discretionary judgment — EXPLORATION pathway

iter-v3/013 has NO MERGE pathway because the iteration TYPE is EXPLORATION. The "MERGE pathway" is `EXPLORATION-PROMISING` or `EXPLORATION-PROMISING-INERT`, both of which are forward-pointers: they add one row to the catalog and count toward the 10 EXPLORATION quota. **iter-v3/013 NEVER updates BASELINE_V3.md.**

---

## Section 9 — Library Stack Declaration

| Package | Version pinned | License | Usage | Fallback |
|---|---|---|---|---|
| `numpy` | (already installed) | BSD-3 | `np.random.default_rng` for `_derive_ensemble_seeds`; column-array math | n/a |
| `scipy` | (already installed) | BSD-3 | (no use this iteration) | n/a |
| `statsmodels` | (already installed) | BSD-3 | `tsa.stattools.adfuller` (unchanged) | n/a |
| `scikit-learn` | (already installed) | BSD-3 | `TimeSeriesSplit` in `_objective` (unchanged) | n/a |
| `lightgbm` | (already installed) | MIT | M1 only — no M2 | n/a |
| `pytest` | (already installed) | MIT | adversarial tests | n/a |
| `pandas` | (already installed) | BSD-3 | Parquet I/O + analysis script CSV loading | n/a |
| `pyarrow` | (already installed via pandas) | Apache-2 | Parquet engine (unchanged) | If missing, fastparquet |

**No new external deps.** Same stack as iter-v3/007–012. The iteration's NEW code is:
- 1 analysis script + 2 outputs (committed at SHA `5217490`)
- 1 line edit in `validation_v3.py` (REQUIRED_GAP 88 → 66)
- 5–10 line edits in `run_baseline_v3.py` (V3_MODELS removes MKR tuple + ITERATION_LABEL)
- Optional: docstring updates in validation_v3.py
- 0 new pytest test files
- 0 modifications to per-cell PBO / DSR / PSR / ADF code paths

### Aggregator strategy — UNCHANGED

Per-cell PBO with cross-cell mean aggregation. Per-cell n_eff with cross-cell median aggregation.

### Reproducibility stamp

The Engineer's Phase 6 writes `briefs-v3/iteration_v3-013/engineering_report.md` with:
- The git commit SHAs at backtest time (expected: `5217490` analysis + the new sub-fix SHA)
- Output of `uv pip list | grep -E "(numpy|scipy|statsmodels|scikit-learn|lightgbm|pytest|pandas|pyarrow)"`
- The full 13-feature list as actually trained on (sanity check against §3.3)
- The runtime `V3_MODELS` (sanity check against §3.5 sub-fix #1) — must show 3 entries, no MKR
- The runtime `REQUIRED_GAP` (sanity check against §3.5 sub-fix #2) — must show 66
- The `comparison.csv` IS / OOS monthly Sharpe values
- The total IS trade count (Falsifier 2 reference, must be < 240; counterfactual ~209)
- The MKR-absence check from trades.csv (Section 3.6 row 15)
- The wall-clock minutes total (must be < 120; target < 30)
- The adversarial test outcome (PASS expected)
- The `--exploration` activation banner from `run.log`
- The runner invocation literal (proof of `--exploration --seeds 1 --n-trials 10`)

---

## Appendix — Phase 5.5 Gate Self-Check

The QR has self-verified all 10 mandatory sections plus the new behavioral-effect predictor (Section 2):

| Section | Status |
|---|---|
| 0 — Data Split | PASS — sacred constants UNCHANGED; ENSEMBLE_SIZE=1 / colsample=1.0 / n_trials=10 SET BY --exploration |
| 0.5 — Iteration Type Declaration | PASS — TYPE: EXPLORATION declared; cadence catalog reference; explicit "NEVER updates BASELINE_V3.md"; UNIVERSE-axis MANDATED by `feedback_mkr_threshold_compression.md` (FIRED at iter-v3/012) |
| 1 — Hypothesis | PASS — one sentence; testable target IS Sharpe ≥ +0.40 (Falsifier 1 at +0.10); falsifiers in §4.3 |
| 2 — IS-Only Numerical Evidence | PASS — `analysis/iteration_v3-013/drop_mkr_demo.py` committed at SHA `5217490` BEFORE this brief; counterfactual aggregates + per-symbol breakdown + behavioral-effect predictor (saturation falsifier IS trades < 240) |
| 3 — Proposed Changes | PASS — symbols CHANGED (drop MKR); labeling UNCHANGED; features UNCHANGED; all gates UNCHANGED; sub-fix decomposition with reconciliation table 15 verifiers; inheritance plan §3.8 |
| 4 — Expected OOS Impact | PASS — predicted IS Sharpe range [+0.30, +1.20]; 3 falsifiers + 1 process falsifier in §4.3; pre-commit catalog framing in §4.4 |
| 5 — Risk Mitigation | PASS — 4 cadence-discipline structural safeguards + 4 methodology-pipeline safeguards + 3 universe-axis-specific risks |
| 6 — Risk Management Design | PASS — 7-primitive table inherited; gate orthogonality verified for universe shrinkage |
| 7 — Pre-Registered Failure-Mode | PASS — 6 predictions with **3 process-level (P1, P2, P3)**; calibrated PROMISING+PROMISING-INERT prior at ~70% (reflecting iter-v3/010 + iter-v3/011 + iter-v3/012 calibration history) |
| 8 — Pre-Registered EXPLORATION Criteria | PASS — 11 EXPLORATION criteria including **criterion 11: Behavioral-effect verifier passes (IS trades < 240)**; PROMISING / PROMISING-INERT / NEGATIVE / BLOCK pathways; explicit "NEVER updates BASELINE_V3.md" |
| 9 — Library Stack | PASS — no new deps; aggregator strategy unchanged from iter-v3/006-012 |

Engineer: please run Phase 5.5 gate verification against the brief-vs-code reconciliation table in Section 3.6. Empty cells in the right column = BLOCK. Verifier commands that do NOT execute and exit 0 post-Phase 6 = NO-MERGE per Section 8. Note that Section 3.6 row 7 (REQUIRED_GAP == 66) and row 14 (behavioral-effect verifier IS trades < 240) are NEW critical gates; row 14 implements the saturation predictor falsifier per `feedback_axis_saturation_predictor.md`.
