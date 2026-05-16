# Iteration v3-008 — Research Brief

**Type**: CONFIRMATION (FIRST CONFIRMATION-TYPE iteration in v3 history; forwards iter-v3/007 EXPLORATION-PROMISING per Critic FINAL SHA `a544621`)
**Track**: v3 (rigor arm) — eighth iteration
**Branch**: `iteration-v3/008` (off `iteration-v3/007` head; analysis commit `003a21e` ships before this brief)
**Date**: 2026-05-06
**Author**: QR (autopilot)

---

## Section 0 — Data Split Declaration

```
OOS_CUTOFF_DATE  = 2025-03-24    # IMMUTABLE (shared across v1, v2, v3)
training_months  = 24             # IMMUTABLE
ENSEMBLE_SIZE    = 5              # PRODUCTION (default; --exploration NOT used)
ensemble_seeds   = _derive_ensemble_seeds(outer_seed, size=5)
                                  # 5 inner seeds per outer seed,
                                  # derived from numpy.random.default_rng(outer_seed)
n_trials         = 50             # PRODUCTION (CLI: --n-trials 50)
colsample_bytree = OPTUNA-SAMPLED # production: Optuna search ≈ uniform(0.5, 1.0)
                                  # — REVERTED from iter-v3/007's hardcoded 1.0
OOS_CUTOFF_MS    = 1742774400000  # millisecond representation for IS-only filtering
```

- **Sacred constants UNCHANGED**: `OOS_CUTOFF_DATE`, `training_months`. The CLI invocation (no `--exploration` flag) is what differentiates this CONFIRMATION run from iter-v3/007's EXPLORATION run.
- **IS window**: from each symbol's first usable kline (with the listing-date floor 2022-09-24) through `2025-03-23 23:59:59 UTC` exclusive.
- **OOS window**: from `2025-03-24 00:00:00 UTC` through the data-extent timestamp at backtest time.
- **Walk-forward unit**: monthly retrain, 24-month rolling training window, 1-month OOS prediction window — UNCHANGED.
- The QR sees OOS metrics for the FIRST time in Phase 7. This brief is produced reading ONLY: iter-v3/007 brief / engineering report / Critic preliminary + FINAL / QR response / diary, iter-v3/007 `comparison.csv` and `ic_matrix.csv` (IS-only pieces), and the iter-v3/008 analysis script `analysis/iteration_v3-008/ic_redundancy_drop_demo.py` outputs (committed at SHA `003a21e` BEFORE this brief).

---

## Section 0.5 — Iteration Type Declaration

**TYPE: CONFIRMATION**

**Justification**: Per Critic FINAL review SHA `a544621`, iter-v3/007 emitted **EXPLORATION-PROMISING** with the explicit caveat "iter-v3/008 CONFIRMATION must apply mechanical Section 8 thresholds without further discretion. ... No second discretionary escape hatch." iter-v3/008 forwards the same top-N feature axis (with one redundancy drop, see Section 3.3) at full production config (`--seeds 5 --n-trials 50`, NO `--exploration`) to test whether the +0.22 IS Sharpe floor observed under EXPLORATION's structurally pessimistic config (ENSEMBLE_SIZE=1, n_trials=10, colsample=1.0) lifts to the CONFIRMATION threshold of >+0.5 IS Sharpe AND >+1.0 OOS Sharpe under full ensemble + Optuna budget. **All headline metrics are MECHANICAL gates per Critic FINAL Recommendation 2** — no QR discretion can re-open them. Critic Phase 7.5 enforces Section 8 thresholds exhaustively.

**Mechanical Section 8 thresholds (no discretion permitted)**:

| Metric | Threshold | Rule on failure |
|---|---|---|
| IS monthly Sharpe | > +0.5 | Mechanical NO-MERGE |
| OOS monthly Sharpe | > +1.0 | Mechanical NO-MERGE (CLAUDE.md "Sharpe 1.0 floor") |
| OOS / IS Sharpe ratio | ≥ 0.5 | Mechanical NO-MERGE |
| PBO | < 0.4 | Mechanical BLOCK |
| DSR | > 0.95 | Mechanical FAIL Check 3 (now ENFORCED under TYPE=CONFIRMATION) |
| PSR | > 0.95 | Mechanical FAIL Check 3 (ENFORCED) |
| Per-symbol max concentration | ≤ 30% of OOS PnL | Mechanical NO-MERGE (Critic FINAL Rec 3) |

The discretionary "floor lifts under full config" hypothesis is the falsifiable claim iter-v3/008 tests. If the floor does not lift, iter-v3/008 NO-MERGE is correct and the de-noising axis is dead.

---

## Section 1 — Hypothesis

Dropping `vwap_dev_50` (kills 2 IC redundancies in one move per Critic Recommendation 1) and running the resulting 13-feature subset on the full v3 universe (BCH+MKR+LDO+TRX) at production config (`--seeds 5 --n-trials 50`, no `--exploration`) will produce IS monthly Sharpe > +0.5 AND OOS monthly Sharpe > +1.0 — testing whether the iter-v3/007 +0.22 EXPLORATION floor lifts to >+0.5 under full ensemble + Optuna budget.

---

## Section 2 — IS-Only Numerical Evidence

**Analysis script**: `analysis/iteration_v3-008/ic_redundancy_drop_demo.py` (committed at SHA `003a21e` BEFORE this brief — Phase 5.5 reproducibility requirement).

**Inputs read**:
- `reports-v3/iteration_v3-007/ic_matrix.csv` — 14×14 IC matrix from iter-v3/007 EXPLORATION (full v3 universe, top-14 features, single seed=42, computed inside the walk-forward loop with `close_time < OOS_CUTOFF_DATE = 2025-03-24`).

No OOS contact at any step. Pure pairwise correlation analysis on a previously committed IS-only matrix.

**Outputs** (all committed alongside the script at SHA `003a21e`):
- `analysis/iteration_v3-008/ic_no_redundancy_subset.csv` — 13-row retained feature list
- `analysis/iteration_v3-008/dropped_pairs.csv` — 2 redundant pairs + drop decision
- `analysis/iteration_v3-008/ic_matrix_13.csv` — 13×13 IC sub-matrix after drop
- `analysis/iteration_v3-008/summary.json` — machine-readable summary
- `analysis/iteration_v3-008/synthesis.md` — interpretive narrative

### 2.1 Carry-forward redundancies in iter-v3/007's 14-feature IC matrix

| feature_a | feature_b | abs IC | above 0.70? |
|---|---|---:|:---:|
| `vwap_dev_50` | `ema_spread_atr_20` | 0.8746 | YES |
| `vwap_dev_50` | `vwap_dev_20` | 0.7938 | YES |

Both pairs share `vwap_dev_50`. Per the analysis script's Step 2:

| feature | appearances in redundant pairs |
|---|---:|
| `vwap_dev_50` | 2 |
| `ema_spread_atr_20` | 1 |
| `vwap_dev_20` | 1 |

`vwap_dev_50` appears in BOTH flagged pairs — dropping it kills both redundancies in one move (Critic FINAL Recommendation 1 option (a)).

### 2.2 13-feature retained subset

| rank | feature | iter-v3/007 mean rank | group |
|---:|---|---:|---|
| 1 | `max_dd_window_50` | 2.5 | tail_risk |
| 2 | `ema_spread_atr_20` | 3.0 | momentum_accel |
| 3 | `ret_kurt_50` | 5.0 | tail_risk |
| 4 | `ret_skew_200` | 5.0 | tail_risk |
| 5 | `range_realized_vol_50` | 6.5 | tail_risk |
| 6 | `hurst_diff_100_50` | 11.5 | regime |
| 7 | `ret_kurt_200` | 11.5 | tail_risk |
| 8 | `hurst_100` | 11.5 | regime |
| 9 | `btc_ret_14d` | 12.5 | cross_btc |
| 10 | `ret_skew_50` | 12.5 | tail_risk |
| 11 | `vwap_dev_20` | 13.0 | volume_micro |
| 12 | `ret_autocorr_lag1_50` | 13.5 | momentum_accel |
| 13 | `sym_vs_btc_ret_7d` | 14.5 | cross_btc |

Group coverage of the 13-feature subset:
- tail_risk: 6 (`max_dd_window_50`, `ret_kurt_50`, `ret_skew_200`, `range_realized_vol_50`, `ret_kurt_200`, `ret_skew_50`)
- regime: 2 (`hurst_diff_100_50`, `hurst_100`)
- momentum_accel: 2 (`ema_spread_atr_20`, `ret_autocorr_lag1_50`)
- cross_btc: 2 (`btc_ret_14d`, `sym_vs_btc_ret_7d`)
- volume_micro: 1 (`vwap_dev_20`)

The drop preserves both VWAP-deviation family signal (`vwap_dev_20` retained) AND EMA-spread family signal (`ema_spread_atr_20` retained); the model is not stripped of either source. Group coverage drops from 5/8 (iter-v3/007) to 5/8 (iter-v3/008) — the volume_micro group goes from 2 to 1 features, all other groups unchanged.

### 2.3 Verification: 13-feature subset has NO pair above 0.70

Maximum off-diagonal |IC| in the 13-feature subset: **0.6602** (`max_dd_window_50` × `range_realized_vol_50`). Headroom to threshold: **+0.0398**.

No pair above 0.70 remains. The drop achieves the Critic Recommendation 1 goal completely.

### 2.4 Why option (a) over option (b)

The Critic offered two compliance options:
- **Option (a)**: drop one feature from each redundant pair (recommended)
- **Option (b)**: provide paired-bootstrap CV proof both belong

Option (a) is preferred because:
1. **Single code edit** vs option (b)'s 50-bootstrap × 5-fold paired-CV pipeline (~1–2h wall-clock investment).
2. **Both pairs share `vwap_dev_50`** — one drop kills both redundancies, no compromise needed.
3. **Lower joint sample-dependence risk** — option (b)'s "joint necessity" verdict is itself a single 14-feature IS run; if iter-v3/007's IS Sharpe = +0.22 floor doesn't lift in iter-v3/008, the bootstrap proof is moot.
4. **Pre-empts Recommendation 1's escape hatch** — Critic explicitly stated "Do NOT carry the redundancy forward silently — this Critic will flag it as FAIL on iter-v3/008 ... without explicit mitigation." Option (a) ships the cleanest mitigation possible.

### 2.5 Implication for Phase 6

Replacing `V3_FEATURE_COLUMNS_TOP_N` (14 features) with the 13-feature subset above is a single, atomic, value-aligned change. Combined with the production `--seeds 5 --n-trials 50` invocation (no `--exploration`), this is the cheapest possible CONFIRMATION test of "does the iter-v3/007 +0.22 EXPLORATION floor lift to >+0.5 under full ensemble + Optuna budget?". A negative result (IS Sharpe ≤ +0.5) is informative — it means the de-noising hypothesis fails under production config and iter-v3/009 should pivot to a different axis (labeling, risk gates). A positive result (IS Sharpe > +0.5 AND OOS Sharpe > +1.0) is the path to v3's first MERGE.

---

## Section 3 — Proposed Changes

### 3.1 Symbols — UNCHANGED (full v3 universe)

| Symbol | Status (iter-v3/008) | Rationale |
|---|---|---|
| BCHUSDT | KEEP | Full v3 universe per iter-v3/007 Critic Rec 3 (CONFIRMATION on same axis). |
| MKRUSDT | KEEP | Same — but per Critic Rec 3, see Section 5.4 for ex-ante story. |
| LDOUSDT | KEEP | Same. |
| TRXUSDT | KEEP | Same. |

`set({BCH, MKR, LDO, TRX}) ∩ V3_EXCLUDED_SYMBOLS = ∅` ✓

### 3.2 Labeling — UNCHANGED

Inherited from iter-v3/001-007:
- Triple-barrier with ATR-scaled barriers: `tp = 2.9 × NATR_21`, `sl = 1.45 × NATR_21`
- Timeout: 7 days = 21 candles at 8h
- σ_t for triple-barrier: past-only ATR (no leak)
- Label-horizon-derived purge gap: `gap = (timeout_candles + 1) × n_symbols = 22 × 4 = 88`. With full universe (`n_symbols=4`), `REQUIRED_GAP=88` is the existing constant — UNCHANGED.

### 3.3 Features — REDUCED from 14 to 13 (drop `vwap_dev_50`)

The feature set used by Phase 6 backtest:

```python
V3_FEATURE_COLUMNS_TOP_N = (
    # iter-v3/008: dropped vwap_dev_50 (Critic Rec 1 SHA a544621)
    # —— removes IC 0.875 with ema_spread_atr_20 AND IC 0.794 with vwap_dev_20
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
)  # length = 13
```

Engineer modifies `src/crypto_trade/features_v3/__init__.py` to:
- Remove `"vwap_dev_50"` from `V3_FEATURE_COLUMNS_TOP_N` (line 126 currently — keep the rest of the tuple).
- Update the header comment block above the tuple (lines 118-124) to reflect "Top 13 by mean importance rank ... iter-v3/008 dropped vwap_dev_50 per Critic Rec 1 SHA a544621."
- Update the docstring on line 140-147 from "Top-14 feature subset for iter-v3/007 EXPLORATION run" to "Top-13 feature subset for iter-v3/008 CONFIRMATION run, with vwap_dev_50 dropped per Critic FINAL SHA a544621".

The runner must continue to pass `feature_columns=list(V3_FEATURE_COLUMNS)` to `LightGbmStrategy` unchanged at `run_baseline_v3.py:863` — only the LIST CONTENTS change. (`V3_FEATURE_COLUMNS = V3_FEATURE_COLUMNS_TOP_N` reassignment from iter-v3/007 stays in place at line 151.)

DROPPED features in iter-v3/008 (vs iter-v3/007's top-14):

```
vwap_dev_50    (highest-importance dropped — IC 0.875 with ema_spread_atr_20, IC 0.794 with vwap_dev_20)
```

Plus the 20 features dropped in iter-v3/007 from `V3_FEATURE_COLUMNS_FULL` remain dropped (see iter-v3/007 brief Section 3.3).

### 3.4 Risk gates — UNCHANGED (v2's 5 active gates + BTC trend filter)

| Gate | Status |
|---|---|
| Vol scaling (atr_pct_rank_200) | ON |
| ADX threshold (20) | ON |
| Hurst regime check | ON |
| Z-score OOD (|z| > 2.5) | ON |
| Low-vol filter (atr_pct_rank_200 ≥ 0.33) | ON |
| BTC trend filter (±20%, 14d) | ON |
| Hit-rate feedback gate | OFF |
| R1 / R2 / R3 | OFF |

**Note**: As in iter-v3/007, the vol scaling, low-vol filter, and z-score OOD gates compute on FEATURES that may or may not appear in `V3_FEATURE_COLUMNS_TOP_N`. Specifically:
- `atr_pct_rank_200` is DROPPED from `V3_FEATURE_COLUMNS_TOP_N` (it has been since iter-v3/007), but it is still computed by the feature pipeline (it's in the parquet) and the gate logic reads it directly via the iter-v3/007 fix at SHA `849c4a6` (`risk_v3.py:_build_lookups()` adds `"atr_pct_rank_200"` explicitly to the `needed` list). Engineer should re-verify in pre-flight that `risk_v3.py` still loads `atr_pct_rank_200` independently of `V3_FEATURE_COLUMNS`.
- The ONE feature now dropped in iter-v3/008 (`vwap_dev_50`) is NOT a gate input — the gates use `atr_pct_rank_200`, `hurst_100`, ADX-from-OHLC, and the z-score OOD set. None reference `vwap_dev_50`. The drop has zero risk-gate side effects.

### 3.5 Sub-fix decomposition

iter-v3/008 has THREE atomic deliverables. Each is a Phase-6 commit that the QE owns.

| # | Sub-fix | Spec | Status / verifier |
|---|---|---|---|
| 1 | **Drop `vwap_dev_50` from `V3_FEATURE_COLUMNS_TOP_N`** | `src/crypto_trade/features_v3/__init__.py`: remove line 126 (`"vwap_dev_50",`) from the tuple; update header comment + docstring per §3.3. The reassignment `V3_FEATURE_COLUMNS = V3_FEATURE_COLUMNS_TOP_N` (line 151) stays put. | Verifier: `python -c "from crypto_trade.features_v3 import V3_FEATURE_COLUMNS; assert len(V3_FEATURE_COLUMNS) == 13, f'len={len(V3_FEATURE_COLUMNS)}'; assert 'vwap_dev_50' not in V3_FEATURE_COLUMNS, 'vwap_dev_50 should be dropped'"`. |
| 2 | **Update `_verify_feature_columns()` AND parametrize the stale runtime banner** | `run_baseline_v3.py`: change `if n != 14:` (line 191) to `if n != 13:`. Update the line 198 print to show 13. **AND parametrize the stale banner at line 1315** from `"feature-cols=34 PASS"` to `f"feature-cols={len(V3_FEATURE_COLUMNS)} PASS"` (Critic Clarification 4 disposition). Update the stale comment at line 1305 similarly. | Verifier: pre-flight prints `V3_FEATURE_COLUMNS: 13 columns  PASS`; `grep "feature-cols=" run_baseline_v3.py` returns the parametrized form, NOT a hardcoded number. |
| 3 | **Run `--seeds 5 --n-trials 50`** (NO `--exploration`) on full 4-symbol universe at full IS+OOS window | Phase-6 invocation: `uv run python run_baseline_v3.py --seeds 5 --n-trials 50` (no `--symbols` flag → all 4 V3_MODELS, no `--exploration` → production ENSEMBLE_SIZE=5 + Optuna-sampled colsample). Wall-clock target: 5–9h, hard cap 12h (Critic Rec 2 budget). | Verifier: `test -f reports-v3/iteration_v3-008/comparison.csv` AND `python -c "import pandas as pd; df=pd.read_csv('reports-v3/iteration_v3-008/comparison.csv'); print(df.iloc[0])"`. |

### 3.6 Brief-vs-Code reconciliation table (Phase 5.5 input)

Each row maps to a FILE ARTIFACT with an executable verifier command. Empty cells = Phase 5.5 BLOCK. Verifier commands MUST execute and exit 0 post-Phase 6.

| # | Sub-fix | Code path | File artifact + verifier |
|---|---|---|---|
| 1 | Sub-fix #1 (V3_FEATURE_COLUMNS reduced to 13) | `src/crypto_trade/features_v3/__init__.py` | `python -c "from crypto_trade.features_v3 import V3_FEATURE_COLUMNS; assert len(V3_FEATURE_COLUMNS) == 13, f'len={len(V3_FEATURE_COLUMNS)}'"` exits 0 |
| 2 | Sub-fix #1 (vwap_dev_50 dropped) | `src/crypto_trade/features_v3/__init__.py` | `python -c "from crypto_trade.features_v3 import V3_FEATURE_COLUMNS; assert 'vwap_dev_50' not in V3_FEATURE_COLUMNS, 'vwap_dev_50 must not be in V3_FEATURE_COLUMNS'"` exits 0 |
| 3 | Sub-fix #2 (_verify_feature_columns updated) | `run_baseline_v3.py:~191` | grep `n != 13` matches in `_verify_feature_columns`; pre-flight log line shows `V3_FEATURE_COLUMNS: 13 columns  PASS` |
| 4 | Sub-fix #2 (runtime banner parametrized) | `run_baseline_v3.py:~1315` | `grep "feature-cols=" run_baseline_v3.py` returns `f"feature-cols={...}"` form, NOT hardcoded `34` or `13` or `14` |
| 5 | Sub-fix #3 produces comparison.csv | runner | `test -f reports-v3/iteration_v3-008/comparison.csv` |
| 6 | Sub-fix #3 produces non-zero monthly_sharpe in IS | runner | `python -c "import pandas as pd; df=pd.read_csv('reports-v3/iteration_v3-008/comparison.csv'); ms = df.loc[df['metric']=='monthly_sharpe','in_sample'].iloc[0]; assert float(ms) != 0, f'IS sharpe is zero: {ms}'"` exits 0 |
| 7 | **CONFIRMATION mechanical Section 8.1**: IS monthly Sharpe > 0.5 | runner | `python -c "import pandas as pd; df=pd.read_csv('reports-v3/iteration_v3-008/comparison.csv'); ms = df.loc[df['metric']=='monthly_sharpe','in_sample'].iloc[0]; assert float(ms) > 0.5, f'IS sharpe = {ms} ≤ 0.5 (mechanical NO-MERGE)'"` exits 0 |
| 8 | **CONFIRMATION mechanical Section 8.2**: OOS monthly Sharpe > 1.0 | runner | `python -c "import pandas as pd; df=pd.read_csv('reports-v3/iteration_v3-008/comparison.csv'); ms = df.loc[df['metric']=='monthly_sharpe','out_of_sample'].iloc[0]; assert float(ms) > 1.0, f'OOS sharpe = {ms} ≤ 1.0 (mechanical NO-MERGE)'"` exits 0 |
| 9 | **CONFIRMATION mechanical Section 8.3**: PBO < 0.4 | runner | `python -c "import json; d=json.load(open('reports-v3/iteration_v3-008/dsr.json')); assert d['pbo'] < 0.4, f'PBO = {d[\"pbo\"]} ≥ 0.4 (mechanical BLOCK)'"` exits 0 |
| 10 | **CONFIRMATION mechanical Section 8.4**: per-symbol max concentration ≤ 30% | runner | `python -c "import pandas as pd; df=pd.read_csv('reports-v3/iteration_v3-008/comparison.csv', skiprows=lambda i: i<16); df['concentration_pct']=df['concentration_pct'].abs(); assert float(df['concentration_pct'].max()) <= 30, f'max conc = {df[\"concentration_pct\"].max()} > 30%'"` exits 0 |
| 11 | `pareto_front.csv` has 5 rows (5-seed CONFIRMATION) | runner | `python -c "import pandas as pd; df=pd.read_csv('reports-v3/iteration_v3-008/pareto_front.csv'); assert len(df) == 5, f'rows={len(df)}'"` exits 0 |
| 12 | All 35 adversarial tests pass | tests | `uv run pytest tests/strategies/ml/ -v` exits 0 |
| 13 | Wall-clock ceiling: total Phase 6 runtime < 12h | engineering report | `python -c "import json; d=json.load(open('briefs-v3/iteration_v3-008/engineering_report_summary.json')); assert d['wall_clock_minutes'] < 720, f'minutes={d[\"wall_clock_minutes\"]}'"` exits 0 |
| 14 | Full v3 universe used (4 symbols, no --symbols filter) | runner invocation log | `grep -E "Active models: 4/4" reports-v3/iteration_v3-008/run.log` exits 0 |
| 15 | `--exploration` flag was NOT used in the run | runner invocation log | `grep -E "Seeds: 5, Optuna trials/model: 50" reports-v3/iteration_v3-008/run.log` exits 0 AND `! grep -E "exploration" reports-v3/iteration_v3-008/run.log` |

### 3.7 NO new features added, NO meta-labeling, NO universe change beyond what's specified

iter-v3/008 is purely a CONFIRMATION iteration testing whether the iter-v3/007 EXPLORATION-PROMISING signal survives full production config. The model architecture, label scheme, risk gates, CPCV parameters, walk-forward window, and inner ensemble seed derivation are byte-for-byte unchanged from iter-v3/007. The ONLY structural changes:

1. `V3_FEATURE_COLUMNS_TOP_N` shrinks from 14 to 13 (drop `vwap_dev_50` per Critic Rec 1).
2. `_verify_feature_columns()` asserts `n != 13` instead of `n != 14`.
3. The stale "feature-cols=34" banner at runtime is parametrized against `len(V3_FEATURE_COLUMNS)` (Critic Rec 4 cleanup).
4. The runner is invoked with `--seeds 5 --n-trials 50` (production) instead of `--exploration --seeds 1`.

NO meta-labeling. NO universe change. NO new risk gates. NO new features.

### 3.8 Inheritance plan from iter-v3/007

The `iteration-v3/008` branch was branched from `iteration-v3/007` head. One analysis commit already shipped:

- `003a21e feat(iter-v3/008): IC redundancy drop analysis (14 → 13 features)` — this brief's Section 2 evidence

iter-v3/007's risk_v3 fix at SHA `849c4a6` (gate-feature decoupling for `atr_pct_rank_200`) is carried over via the branching. The `_derive_ensemble_seeds(outer_seed, size=5)` call is what the production-config invocation uses (size=5 for 5-seed inner ensemble).

Critical inheritance verifiers (run before any code edits in Phase 6):
- `git log --oneline iteration-v3/008 -- run_baseline_v3.py | wc -l` ≥ 3 (iter-v3/006 SHA `9314db4` + iter-v3/007 SHA `bce50c8` + iter-v3/007 SHA `849c4a6` + any iter-v3/008 banner edit)
- `test -f tests/strategies/ml/test_outer_seed_propagation.py` (iter-v3/006 inherited)
- `test -f tests/strategies/ml/test_per_cell_pbo_synthetic.py` (iter-v3/004 inherited)
- `test -f tests/strategies/ml/test_ensemble_seed_propagation.py` (iter-v3/005 inherited)
- `uv run pytest tests/strategies/ml/ -v` exits 0 with 35/35 PASS

### 3.9 Engineer's Phase 6 work plan (informative, not mandatory)

1. Verify §3.8 inheritance preconditions (35/35 tests PASS at HEAD).
2. Implement sub-fix #1: edit `src/crypto_trade/features_v3/__init__.py` — remove `"vwap_dev_50",` from `V3_FEATURE_COLUMNS_TOP_N`, update the header comment + docstring per §3.3.
3. Implement sub-fix #2 part A: edit `run_baseline_v3.py` `_verify_feature_columns()` from `if n != 14:` to `if n != 13:`. Update the corresponding error message and pre-flight print.
4. Implement sub-fix #2 part B: parametrize the stale runtime banner at `run_baseline_v3.py:1315` (and the stale comment at `:1305`) against `len(V3_FEATURE_COLUMNS)`.
5. Pre-flight: `python -c "from crypto_trade.features_v3 import V3_FEATURE_COLUMNS; assert len(V3_FEATURE_COLUMNS) == 13 and 'vwap_dev_50' not in V3_FEATURE_COLUMNS"` returns 0.
6. Pre-flight: `uv run pytest tests/strategies/ml/ -v` returns 35/35 PASS.
7. **Pre-flight wall-clock estimator (P2 mitigation)**: launch a 2-seed pre-flight run for ~30 min to estimate full-run wall-clock. If extrapolated full-run wall-clock > 12h, abort and document the cause; iter-v3/009 EXPLORATION re-scopes (e.g., 2 symbols).
8. Run sub-fix #3: `time uv run python run_baseline_v3.py --seeds 5 --n-trials 50`. Wall-clock estimate: 5–9h, hard cap 12h.
9. Persist outputs to `reports-v3/iteration_v3-008/`. Note the `run.log` should include `[features] V3_FEATURE_COLUMNS: 13 columns  PASS` and the parametrized `feature-cols=13 PASS` banner.
10. Verify §3.6 reconciliation table — every verifier exits 0. **Mechanical Section 8 verifiers (rows 7, 8, 9, 10) are NO-MERGE triggers** — Engineer documents PASS/FAIL in engineering report Section 3.6.
11. Write `engineering_report.md` + `engineering_report_summary.json` including: (a) wall-clock minutes, (b) trade counts (IS / OOS), (c) per-symbol monthly_sharpe / weighted_pnl / concentration_pct, (d) git SHAs (`003a21e` for analysis, plus the new sub-fix #1+#2 SHA), (e) hardware, (f) library versions, (g) the 13 feature names actually used (sanity check against §3.3), (h) the EXPLICIT mechanical-verifier outcomes for §3.6 rows 7-10.

Estimated total wall-clock: 5–9h on full universe at production config (ENSEMBLE_SIZE=5, n_trials=50).

---

## Section 4 — Expected OOS Impact

### 4.1 Per TYPE=CONFIRMATION, headline metrics ARE GATES (mechanical, no discretion)

iter-v3/008 is a CONFIRMATION iteration per Section 0.5. Per Critic FINAL Recommendation 2, headline metrics (DSR, PSR, IS Sharpe > 0.5, OOS Sharpe > 1.0, PBO < 0.4) are MECHANICAL gates. The Critic emits `CONFIRMATION-MERGE`, `CONFIRMATION-NO-MERGE`, or `BLOCK` based on these criteria — no discretion is permitted. The discretionary "+0.22 floor lifts under full config" hypothesis is what iter-v3/008 tests; the test outcome is mechanical, the test design is the prediction.

### 4.2 Predicted IS Sharpe range

| Metric | iter-v3/007 EXPLORATION (top-14, ENSEMBLE_SIZE=1, n_trials=10) | iter-v3/008 prediction (top-13, ENSEMBLE_SIZE=5, n_trials=50) |
|---|---:|---:|
| IS monthly Sharpe | +0.2241 | **predicted [+0.4, +0.9] with median +0.6** |
| OOS monthly Sharpe | +0.0622 | **predicted [+0.5, +1.5] with median +0.9** |
| Phase 6 wall-clock | 8 min | predicted 5–9h, hard cap 12h |

The IS Sharpe prediction band [+0.4, +0.9] reflects:
- **Upward shift from EXPLORATION**: ENSEMBLE_SIZE=5 (5x averaging) reduces per-seed variance roughly by √5 ≈ 2.2x; n_trials=50 (5x search budget) gives Optuna 5x more samples to find better hyperparameters; Optuna-sampled colsample (vs hardcoded 1.0) lets the ensemble exploit feature subsampling. Empirically, full-config runs typically lift EXPLORATION's IS Sharpe by 0.2–0.4.
- **Mild lift from drop**: removing the most-redundant feature reduces Optuna's effective hyperparameter-feature space by ~1/14 ≈ 7%, which can either help (less noise) or hurt slightly (less feature diversity); historically a single-feature drop of a redundant pair has a small, slightly-positive expected effect.
- **Dispersion**: the 5-seed std of monthly Sharpe in iter-v3/003-006 was ~0.2-0.4 across runs. A [+0.4, +0.9] prediction band of width 0.5 covers ~2σ above and below the median.

The OOS Sharpe prediction band [+0.5, +1.5] is wider because:
- Per-seed OOS variance is structurally larger than IS variance (smaller sample).
- iter-v3/007's single-seed OOS Sharpe = +0.0622 is one realization of a wide distribution; under 5-seed averaging the OOS Sharpe should anchor closer to its IS-extrapolated mean rather than to one extreme draw.
- The OOS/IS ratio prediction is roughly 1.0–1.5 (CONFIRMATION typically shows OOS ≥ IS for genuine signals; the iter-v3/003 anomaly of OOS Sharpe 1.10 vs IS -0.07 was a single-seed artifact).

### 4.3 Falsifiers (locked before backtest, mechanical)

**Falsifier 1 (mechanical, Section 8 row 1)**: IS monthly Sharpe ≤ +0.5 → top-13 feature subset failed to lift the EXPLORATION floor; the de-noising hypothesis is rejected under production config; **mechanical NO-MERGE**. iter-v3/009 pivots to a different axis (labeling, risk gates, model architecture).

**Falsifier 2 (mechanical, Section 8 row 2)**: OOS monthly Sharpe ≤ +1.0 → no edge survives at production config; **mechanical NO-MERGE per CLAUDE.md "Sharpe 1.0 floor"**. iter-v3/009 pivots.

**Falsifier 3 (mechanical, Section 8 row 3)**: PBO ≥ 0.4 → strategy is overfit; the IS-best seed underperforms OOS median; **mechanical BLOCK**.

**Falsifier 4 (mechanical, Section 8 row 4)**: per-symbol max concentration > 30% (per Critic FINAL Rec 3) → portfolio fragility on a single symbol; **mechanical NO-MERGE** unless brief Section 5.4 ex-ante story is accepted (option (a) gate is the default — see Section 5.4).

**Falsifier 5 (process)**: Phase 6 wall-clock > 12h → infrastructure budget exceeded; engineer aborts and iter-v3/009 re-scopes.

**Falsifier 6 (process)**: pre-flight `len(V3_FEATURE_COLUMNS) == 13 AND 'vwap_dev_50' not in V3_FEATURE_COLUMNS` returns False → sub-fix #1 not implemented; Phase 6 must not start.

### 4.4 Expected CONFIRMATION outcome

iter-v3/008 PASSES CONFIRMATION (Critic emits `CONFIRMATION-MERGE`) if and only if:

1. All 15 reconciliation table verifiers exit 0
2. Critic OVERALL = `CONFIRMATION-MERGE` (NOT BLOCK)
3. Mechanical Section 8 thresholds ALL pass (IS Sharpe > 0.5, OOS Sharpe > 1.0, OOS/IS ratio ≥ 0.5, PBO < 0.4, DSR > 0.95, PSR > 0.95, max conc ≤ 30%)
4. 5-seed Pareto: mean monthly Sharpe > 0, ≥3/5 profitable seeds (5-seed CONFIRMATION minimum; 10-seed validation deferred to iter-v3/009)

If iter-v3/008 MERGES, it becomes the FIRST v3 baseline (`v0.v3-008`) and iter-v3/009 runs the 10-seed validation.

If iter-v3/008 NO-MERGES on falsifier 1 or 2, the de-noising-axis hypothesis is dead and iter-v3/009 pivots to a model axis (different labels, risk gates, or architecture).

---

## Section 5 — Risk Mitigation

### 5.1 NEW structural safeguards (per Critic FINAL Recommendations 1, 2, 3)

iter-v3/008 introduces THREE structural safeguards directly addressing the three Critic FINAL pre-conditions:

1. **Drop `vwap_dev_50` PRE-EMPTIVELY (Critic Rec 1).** The Phase-1 analysis script `analysis/iteration_v3-008/ic_redundancy_drop_demo.py` (SHA `003a21e`) verifies the 13-feature subset has NO pair above the IC threshold (max residual |IC| = 0.6602, headroom +0.0398). The Critic explicitly stated "this Critic will flag it as FAIL on iter-v3/008 if it appears in a CONFIRMATION-TYPE iteration without explicit mitigation." The drop pre-empts that FAIL.

2. **Mechanical Section 8 thresholds — no discretionary escape hatch (Critic Rec 2).** Section 0.5 declares the mechanical thresholds explicitly. Section 8 enforces them as PASS/FAIL conditions. Section 3.6 reconciliation table rows 7, 8, 9 are EXECUTABLE verifiers that exit non-zero on threshold failure. The Phase 7.5 Critic verifies all reconciliation rows; any failure on rows 7-10 is a mechanical NO-MERGE — no QR response or discretionary call can re-open it. The "+0.22 floor lifts under full config" claim is the falsifiable hypothesis being tested, not a license to relax thresholds.

3. **Per-symbol concentration ≤ 30% mechanical gate (Critic Rec 3 option (a)).** Per the recommendation, iter-v3/008 pre-registers max-symbol weighted_pnl-fraction ≤ 30% as a mechanical merge gate (Section 3.6 reconciliation row 10). This is the cleaner of the two compliance options (vs option (b) MKR ex-ante story) because:
   - The gate is uniformly enforceable across all 4 symbols (not just MKR).
   - It removes the need for an ex-ante diversification narrative whose validity itself depends on the OOS outcome.
   - It protects against single-symbol fragility regardless of which symbol dominates.
   - Note: iter-v3/007 OOS showed BCH 84.44% concentration. If iter-v3/008's 5-seed CONFIRMATION shows similar concentration, NO-MERGE is mechanical.

### 5.2 Methodology-pipeline safety

Three additional safeguards (inherited from iter-v3/006-007):

1. **35 adversarial unit tests** (29 inherited + 6 new at SHA `9314db4`) must PASS before backtest. Engineer's pre-flight verifies.
2. **File-artifact reconciliation table** (§3.6). 15 verifier commands map to specific file artifacts. Empty cells = Phase 5.5 BLOCK. **Rows 7-10 are mechanical Section 8 enforcers** — the Critic uses them to certify CONFIRMATION-MERGE.
3. **Pre-flight len-check + name-check on V3_FEATURE_COLUMNS**: catches the case where sub-fix #1 silently regresses (e.g., reassignment lost during a merge or rebase). Engineer prints both `len(V3_FEATURE_COLUMNS)` and the `vwap_dev_50` membership test before backtest.

### 5.3 NO new model-level risks introduced

The iter-v3/008 changes:
- Drop ONE feature (`vwap_dev_50`) — fewer features = less risk of look-ahead from any one feature; the dropped feature was already in iter-v3/007's audited `V3_FEATURE_COLUMNS_TOP_N` and has passed iter-v3/007's Critic Check 1.
- Use `ENSEMBLE_SIZE=5` (production) — REDUCES per-seed variance vs iter-v3/007's `ENSEMBLE_SIZE=1`; the Critic Check 8 (hypothesis alignment) explicitly anticipates this.
- Use `n_trials=50` (production) — Optuna explores the standard search space; same risk as iter-v3/001-005's full-config runs.
- Use Optuna-sampled `colsample_bytree` — REVERTS from iter-v3/007's hardcoded 1.0 to the standard production sampling; this reduces per-seed variance and makes the redundancy-drop more impactful (because under colsample<1.0, redundant pairs steal sampling probability more aggressively).

The only NEW risk is the `vwap_dev_50` drop, which is mitigated by the IC verification in Section 2.3 (no residual pair above 0.70).

### 5.4 Per-symbol concentration mechanical gate (Critic Rec 3 detail)

The mechanical gate at Section 3.6 reconciliation row 10 enforces:

```
max(|concentration_pct|) ≤ 30 across all 4 symbols
```

where `concentration_pct = weighted_pnl_symbol / weighted_pnl_total × 100`.

iter-v3/007 OOS reference values (NOT the gate target — the gate operates on iter-v3/008's OOS):
- BCH: 83.95% — would FAIL the 30% gate
- LDO: 455.55% — would FAIL (denominator is small total, this is an artifact)
- TRX: -51.15% — would FAIL
- MKR: -388.34% — would FAIL

In iter-v3/007, the small total OOS PnL (+3.61%) inflated all concentrations. **Under iter-v3/008's 5-seed averaging the total OOS PnL should be larger and more stable**, so the concentration ratios should be in the 10-50% range rather than the [-388%, +455%] range. If they are NOT (e.g., total OOS PnL stays small and concentrations remain >100%), the mechanical gate triggers NO-MERGE — which is the correct outcome under the gate's "single-symbol fragility" rationale.

**Pre-registered tightening rule (Section 7 P3 mitigation)**: if the concentration gate at 30% triggers NO-MERGE on iter-v3/008 BUT the absolute OOS Sharpe is > +1.5 AND ≥3/5 seeds are profitable, the QR's iter-v3/008 diary documents the concentration as "structural" (BCH leadership), and iter-v3/009 EXPLORATION explicitly tests a 35% concentration cap as the mechanical gate. This is NOT a discretionary escape hatch for iter-v3/008 — iter-v3/008 NO-MERGES per the 30% gate; iter-v3/009 EXPLORATION re-validates the 35% boundary on a fresh run.

---

## Section 6 — Risk Management Design

### 6.1 7-primitive table — IDENTICAL TO iter-v3/006 / iter-v3/007

| # | Primitive | Spec | Fire-rate prediction (IS) | Regime coverage |
|---|---|---|---|---|
| 1 | Vol scaling | `scale = clip(atr_pct_rank_200, 0.3, 1.0)` | Always on; mean scale ≈ 0.6 | High-vol → scale down |
| 2 | ADX gate | trade only when ADX > 20 | ≈ 60% of bars pass | Trending only |
| 3 | Hurst regime check | trade only when 0.05 < hurst_100 < 0.95 | ≈ 90% of bars pass | Filters bond-like regimes |
| 4 | Feature z-score OOD | kill if any |z| > 2.5 | ≈ 5–8% killed | Distributional drift |
| 5 | Low-vol filter | trade only when atr_pct_rank_200 ≥ 0.33 | ≈ 67% of bars pass | Filters dead chop |
| 6 | Hit-rate feedback | DISABLED | 0% | Reserved for future tuning |
| 7 | BTC trend alignment | kill alt trade fighting BTC 14d ±20% | ≈ 7–8% killed | Macro flips |

Combined kill rate target: 69–78%. SAME as iter-v3/006-007.

**Important**: Primitives 1, 4, 5 reference features (`atr_pct_rank_200`, the z-score-OOD-feature-set, and `atr_pct_rank_200` again) that are DROPPED from `V3_FEATURE_COLUMNS_TOP_N`. This does NOT affect the gates because:
- Gates read from the parquet feature DataFrame (where all 34 features remain computed by the feature pipeline) — NOT from the model's `feature_columns` argument.
- The risk_v3 fix at SHA `849c4a6` (iter-v3/007) explicitly adds `"atr_pct_rank_200"` to the `risk_v3.py:_build_lookups()` `needed` list independently of `V3_FEATURE_COLUMNS`.
- The single new drop in iter-v3/008 (`vwap_dev_50`) is NOT a gate input — Engineer must re-verify in Phase 6 step 5 pre-flight.

### 6.2 Regime coverage — UNCHANGED

The full v3 universe IS data spans 2022-09-24 → 2025-03-23. Regime coverage includes 2022 LUNA/FTX, 2023 banking, 2024 halving + Trump rally, 2025 January correction. OOS data extends through the data-extent timestamp at backtest time (currently ~2026-04-30 per recent baseline reruns).

### 6.3 Concentration — multi-symbol full universe with mechanical gate

Per Critic Rec 3 / Section 5.4, the per-symbol concentration cap (≤30% of OOS PnL per symbol) is now a MECHANICAL merge gate, not a soft warning. Section 8 row 10 enforces.

---

## Section 7 — Pre-Registered Failure-Mode Prediction

iter-v3/004's 5/5 calibration win, iter-v3/006's 5/5 calibration win, and iter-v3/007's 2/5 calibration partial-win establish the discipline. iter-v3/008's Section 7 inherits and refines based on iter-v3/007 lesson #5 ("calibrated, not aspirational" prior-setting).

**Prediction P1 (process-level, P=15%): the `vwap_dev_50` drop introduces a new feature ordering issue (column index references in existing code, e.g., test fixtures that hardcode 14 OR a slice index in `feature_importance.csv` consumer code).** The reassignment of `V3_FEATURE_COLUMNS_TOP_N` from 14 to 13 may trip downstream code that hardcodes 14 (e.g., the `_verify_feature_columns()` itself, OR any test fixture that asserts 14, OR a slice operation `feature_importance.iloc[:14]` somewhere). **Detection signal**: pre-flight `python -c "from crypto_trade.features_v3 import V3_FEATURE_COLUMNS; assert len(V3_FEATURE_COLUMNS) == 13 and 'vwap_dev_50' not in V3_FEATURE_COLUMNS"` raises OR `_verify_feature_columns()` raises OR a test in `tests/strategies/ml/` fails. **Mitigation**: Phase 6 work plan step 5 explicitly checks both. Step 6 runs the full test suite. If anything fails, sub-fix #1 or #2 is incomplete; Phase 6 must abort and the QR is re-engaged for a Phase 5.5 re-gate.

**Prediction P2 (process-level, P=10%): wall-clock overshoots 12h cap.** Production config (ENSEMBLE_SIZE=5, n_trials=50) on full v3 universe at ~1 month per training cell × ~28 cells × 4 symbols × 5 seeds × 50 trials. iter-v3/003 at the same config took ~3.6h (BUT with 34 features, parquet I/O slightly faster). At 13 features the per-trial training is faster but the per-cell PBO computation is unchanged, so wall-clock should be 3-9h. Worst case (lots of Optuna pruning failures, slow Optuna trial scheduling) could hit 12h. **Detection signal**: total Phase 6 wall-clock > 12h. **Mitigation**: Engineer launches a 2-seed pre-flight run for ~30 min to extrapolate the full-run wall-clock (Phase 6 work plan step 7). If extrapolated > 12h, abort and document the cause; iter-v3/009 EXPLORATION re-scopes (e.g., 2 symbols).

**Prediction P3 (process-level, P=15%): per-symbol concentration mechanical gate at 30% blocks even good iterations because BCH dominance is structural.** iter-v3/007's OOS showed BCH at 84.44% concentration (single-seed; the figure is inflated by small total OOS PnL but BCH being top-symbol is a real pattern). Under 5-seed averaging the absolute concentration may stabilize around 40-60% rather than 84%, but it could still exceed 30%. If it does AND Sharpe metrics are otherwise good, iter-v3/008 NO-MERGES correctly per the gate, but the lesson is that 30% is too tight for a 4-symbol universe with a structural leader. **Detection signal**: Section 3.6 row 10 verifier fails BUT rows 7-9 (Sharpe + PBO) all PASS. **Mitigation**: iter-v3/008 NO-MERGES (mechanical, no discretion); iter-v3/009 EXPLORATION explicitly pre-registers a 35% gate as a MECHANICAL re-test with the BCH-dominance "structural not overfit" rationale documented in iter-v3/008 diary. This is NOT a retroactive escape hatch for iter-v3/008.

**Prediction P4 (model-level, P=35%): IS Sharpe stays in [+0.2, +0.4] range — the de-noising hypothesis fails to lift the floor under production config.** The iter-v3/007 +0.22 floor reflects the fundamental limit of the top-N axis under the v3 stack (data, features, labels, risk gates). Even with 5-seed averaging + Optuna budget + Optuna-sampled colsample, the IS Sharpe may only lift to +0.3-0.4, falling short of the mechanical +0.5 threshold. **Pre-registered**: this is INFORMATIVE. iter-v3/008 NO-MERGES on falsifier 1 (mechanical, no discretion); iter-v3/009 EXPLORATION pivots to a different axis (labels, risk gates, model architecture).

**Prediction P5 (model-level, P=50%): IS Sharpe lifts to [+0.5, +0.8] range BUT OOS Sharpe ≤ +1.0 — CONFIRMATION fails on edge axis.** The hypothesized full-config lift materializes for IS Sharpe (production reduces variance, expands hyperparameter search), bringing the median IS Sharpe near +0.6 as predicted. BUT the OOS Sharpe lifts only modestly (e.g., +0.3-0.8 range), failing the +1.0 floor. This indicates the de-noising axis lifts the IS edge but not the OOS edge — a sign that the underlying model has insufficient generalization capacity, not that the features are wrong. **Pre-registered**: this is INFORMATIVE. iter-v3/008 NO-MERGES on falsifier 2 (mechanical); iter-v3/009 EXPLORATION pivots to a model axis (labels, risk gates) rather than re-running the same de-noising axis.

The predictions are intentionally Bayesian-calibrated:
- 3 process-level (P1, P2, P3) per iter-v3/003 lesson #3 discipline (validated 5/5 in iter-v3/004, iter-v3/006; partial-validated 2/5 in iter-v3/007)
- 2 model-level (P4, P5) per the historical class
- The model-level priors (P4 = 35%, P5 = 50%, residual ~15% for "MERGE pathway" P=15%) reflect iter-v3/007 lesson #5: the QR's prior on EXPLORATION at 70% was miscalibrated; iter-v3/008 explicitly weights the failure-mode classes higher than the success class.

Summary: **MERGE pathway probability ≈ 15%**. CONFIRMATION on a single axis (de-noising) is a low-base-rate event historically — 0/7 v3 iterations have produced a MERGE. iter-v3/008 is testing whether the EXPLORATION-PROMISING signal is strong enough to clear mechanical thresholds; the prior should reflect that most CONFIRMATION runs after first-EXPLORATION-PROMISING fail at one of the mechanical gates.

---

## Section 8 — Pre-Registered MERGE/NO-MERGE Numerical Criteria

**These thresholds are LOCKED before backtest. Phase 7 evaluation applies them mechanically. NO discretion permitted (per Critic FINAL Rec 2).**

iter-v3/008 is a **CONFIRMATION iteration** per Section 0.5. All headline-metric thresholds are mechanical PASS/FAIL conditions. Critic emits `CONFIRMATION-MERGE`, `CONFIRMATION-NO-MERGE`, or `BLOCK` based on the 12 criteria below.

### CONFIRMATION-MERGE iff ALL 12 of the following are true:

| # | Criterion | Threshold | Source |
|---|---|---:|---|
| 1 | TYPE=CONFIRMATION declared in Section 0.5 | TRUE (verified at brief-time) | §0.5 |
| 2 | `--seeds 5 --n-trials 50` used in runner invocation; `--exploration` NOT used | TRUE | §3.5 #3, §3.6 row 15 |
| 3 | IS monthly Sharpe > 0.5 | float > 0.5 | §3.6 row 7 (mechanical) |
| 4 | OOS monthly Sharpe > 1.0 | float > 1.0 | §3.6 row 8 (mechanical, CLAUDE.md "Sharpe 1.0 floor") |
| 5 | OOS / IS Sharpe ratio ≥ 0.5 | ratio ≥ 0.5 | derived from §3.6 rows 7+8 |
| 6 | PBO < 0.4 | float < 0.4 | §3.6 row 9 (mechanical BLOCK if FAIL) |
| 7 | DSR > 0.95 | float > 0.95 | dsr.json field (mechanical FAIL Check 3 if ≤ 0.95) |
| 8 | PSR > 0.95 | float > 0.95 | dsr.json field (mechanical FAIL Check 3 if ≤ 0.95) |
| 9 | n_trades ≥ 10/month OOS AND ≥ 130 total OOS | counts | comparison.csv |
| 10 | Per-symbol max concentration ≤ 30% (Critic Rec 3) | abs(max) ≤ 30 | §3.6 row 10 (mechanical) |
| 11 | 5-seed Pareto: mean monthly Sharpe > 0, ≥3/5 profitable | derived | pareto_front.csv (5 rows expected) |
| 12 | Critic OVERALL = `CONFIRMATION-MERGE` (NOT BLOCK or NO-MERGE) | enum | Phase 7.5 review.md |

### CONFIRMATION-NO-MERGE iff:

- Any of criteria 3, 4, 5, 7, 8, 9, 10, 11 fails (mechanical, no discretion)
- Critic OVERALL = `CONFIRMATION-NO-MERGE` (criterion 12 fails because at least one mechanical threshold above failed)

### NO-MERGE-PROCESS iff ANY of:

- Criteria 1, 2 fail (process-level: wrong type declaration, wrong invocation)
- Criterion 6 fails (PBO ≥ 0.4 → mechanical BLOCK on overfitting axis)
- Engineer's Phase 6 wall-clock exceeds 12h cap (process)
- Phase 5.5 gate emits BLOCK (process)
- Phase 7.5 Critic emits explicit BLOCK (process-level methodology failure beyond the CONFIRMATION axes)

### CONFIRMATION outcome interpretation

| Critic verdict | Meaning | Next iteration |
|---|---|---|
| `CONFIRMATION-MERGE` | All 12 criteria PASS; this is the FIRST v3 baseline. iter-v3/008 becomes `v0.v3-008` and `BASELINE_V3.md` is updated. | iter-v3/009 — 10-seed Pareto validation on the merged stack |
| `CONFIRMATION-NO-MERGE` (falsifier 1) | IS Sharpe ≤ +0.5 — de-noising hypothesis fails to lift floor under production | iter-v3/009 EXPLORATION on a DIFFERENT axis (labeling, risk gates, model architecture) |
| `CONFIRMATION-NO-MERGE` (falsifier 2) | IS Sharpe > +0.5 BUT OOS Sharpe ≤ +1.0 — IS edge does not generalize | iter-v3/009 EXPLORATION on a MODEL axis (different labels, hit-rate gate, simpler architecture) |
| `CONFIRMATION-NO-MERGE` (falsifier 4) | All Sharpe + PBO criteria PASS BUT max concentration > 30% — single-symbol fragility | iter-v3/009 EXPLORATION pre-registers a 35% gate with BCH-dominance "structural" rationale |
| `BLOCK` (process-level) | A methodology check FAILED unexpectedly (e.g., look-ahead, IC redundancy reintroduced, embargo violation) | Diary documents, iter-v3/009 fixes the methodology gap and retries on the SAME axis |

### NO discretionary judgment permitted

Per Critic FINAL Recommendation 2: "iter-v3/008 CONFIRMATION must apply mechanical Section 8 thresholds without further discretion. ... No second discretionary escape hatch." All criteria 3-11 are PASS/FAIL float comparisons with verifiable thresholds; criterion 12 is the Critic's mechanical mapping of those PASS/FAIL outcomes. The QR has NO authority to re-interpret threshold failures as PROMISING / DISCRETIONARY / WAIVED in Phase 7.

If Section 7 P3 materializes (concentration gate triggers NO-MERGE on otherwise-good metrics), **iter-v3/008 NO-MERGES per the 30% gate**. iter-v3/009 EXPLORATION may re-test at a 35% gate, but iter-v3/008's verdict stands.

---

## Section 9 — Library Stack Declaration

| Package | Version pinned | License | Usage | Fallback if install fails |
|---|---|---|---|---|
| `numpy` | (already installed) | BSD-3 | `np.random.default_rng` for `_derive_ensemble_seeds`; column-array math | n/a |
| `scipy` | (already installed) | BSD-3 | (no use this iteration) | n/a |
| `statsmodels` | (already installed) | BSD-3 | `tsa.stattools.adfuller` for per-(sym, feat, month) ADF (unchanged) | n/a |
| `scikit-learn` | (already installed) | BSD-3 | `TimeSeriesSplit` in `_objective` (unchanged) | n/a |
| `lightgbm` | (already installed) | MIT | M1 only — no M2 | n/a |
| `pytest` | (already installed) | MIT | Adversarial unit tests (29 inherited + 6 new = 35) | n/a |
| `pandas` | (already installed) | BSD-3 | Parquet I/O (unchanged) + analysis script IC matrix loading | n/a |
| `pyarrow` | (already installed via pandas) | Apache-2 | Parquet engine (unchanged) | If missing, pandas auto-falls back to fastparquet |

**No new external deps.** The iteration's NEW code is:
- 1 analysis script + 5 output artifacts (already committed at SHA `003a21e`)
- 1 sub-fix #1 edit to `src/crypto_trade/features_v3/__init__.py` (Engineer ships in Phase 6, drops `vwap_dev_50` from `V3_FEATURE_COLUMNS_TOP_N`)
- 1 sub-fix #2 edit to `run_baseline_v3.py` (Engineer ships in Phase 6, updates `_verify_feature_columns()` to `n != 13` AND parametrizes the stale runtime banner)
- 0 new pytest test files (all test plumbing inherited)
- 0 modifications to per-cell PBO / DSR / PSR / ADF code paths

### Aggregator strategy — UNCHANGED from iter-v3/006-007

Per-cell PBO with cross-cell mean aggregation. Per-cell n_eff with cross-cell median aggregation. The aggregator choices are fixed; iter-v3/008 only validates that the EXPLORATION-floor signal lifts under production config + IC-redundancy drop.

### Reproducibility stamp

The Engineer's Phase 6 writes `briefs-v3/iteration_v3-008/engineering_report.md` with:
- The git commit SHAs at backtest time (expected: `003a21e` analysis + the new sub-fix #1+#2 SHA + any banner cleanup SHA)
- Output of `uv pip list | grep -E "(numpy|scipy|statsmodels|scikit-learn|lightgbm|pytest|pandas|pyarrow)"`
- The full 13-feature list as actually trained on (sanity check against §3.3)
- The `comparison.csv` IS / OOS monthly Sharpe values
- The wall-clock minutes total (must be < 720)
- The `tests/strategies/ml/test_outer_seed_propagation.py` and `test_per_cell_pbo_synthetic.py` and `test_ensemble_seed_propagation.py` test outcomes (all PASS expected)
- The `comparison.csv` per-symbol concentration values + an EXPLICIT statement of whether row 10 (max conc ≤ 30%) PASSes
- The per-row mechanical Section 8 PASS/FAIL grid (rows 7-10)
- The Pareto front for the 5 seeds (5 rows expected)
- The runner invocation literal (proof `--exploration` was NOT used, `--seeds 5 --n-trials 50` WAS used)

---

## Appendix — Phase 5.5 Gate Self-Check

The QR has self-verified all 11 mandatory sections plus the Phase 5.5 inputs:

| Section | Status |
|---|---|
| 0 — Data Split | PASS — sacred constants UNCHANGED; ENSEMBLE_SIZE=5 / colsample=Optuna-sampled / n_trials=50 are PRODUCTION (no `--exploration` flag); documented |
| 0.5 — Iteration Type Declaration | PASS — TYPE: CONFIRMATION declared; mechanical threshold table inline; references Critic FINAL SHA `a544621` |
| 1 — Hypothesis | PASS — one sentence; specific testable target (IS Sharpe > +0.5 AND OOS Sharpe > +1.0); falsifiers in §4.3 |
| 2 — IS-Only Numerical Evidence | PASS — `analysis/iteration_v3-008/ic_redundancy_drop_demo.py` committed at SHA `003a21e` BEFORE this brief; 5 outputs committed; redundancy → drop → 13-feature retained subset table inline in §2.1-2.4 |
| 3 — Proposed Changes | PASS — symbols UNCHANGED; labeling UNCHANGED; features REDUCED 14 → 13 with explicit dropped feature `vwap_dev_50` and rationale; risk gates UNCHANGED; decomposed into 3 sub-fixes in §3.5; brief-vs-code reconciliation table in §3.6 with 15 file-artifact verifiers (including 4 mechanical Section 8 enforcers); inheritance plan in §3.8 |
| 4 — Expected OOS Impact | PASS — predicted IS Sharpe range [+0.4, +0.9], OOS [+0.5, +1.5]; 6 falsifiers in §4.3 (4 mechanical, 2 process); CONFIRMATION pathway in §4.4 |
| 5 — Risk Mitigation | PASS — 3 NEW structural safeguards in §5.1 explicitly addressing Critic FINAL Recs 1, 2, 3 + 3 methodology-pipeline safeguards in §5.2 + concentration gate detail in §5.4 |
| 6 — Risk Management Design | PASS — 7-primitive table identical to iter-v3/006-007; gate-vs-feature-column independence verified §6.1; new gate input verification step added (P6 step 5) |
| 7 — Pre-Registered Failure-Mode | PASS — 5 predictions with **3 process-level (P1, P2, P3)** per iter-v3/003 lesson #3; calibrated MERGE prior at ~15% (iter-v3/007 lesson #5) |
| 8 — Pre-Registered MERGE/NO-MERGE | PASS — 12 mechanical CONFIRMATION criteria; CONFIRMATION-MERGE / CONFIRMATION-NO-MERGE / BLOCK pathways; explicit "no discretionary judgment permitted" clause |
| 9 — Library Stack | PASS — no new deps; aggregator strategy unchanged from iter-v3/006-007 |

Engineer: please run Phase 5.5 gate verification against the brief-vs-code reconciliation table in Section 3.6. Empty cells in the right column = BLOCK. Verifier commands that do NOT execute and exit 0 post-Phase 6 = NO-MERGE per Section 8.
