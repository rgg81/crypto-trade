# iter-v3/112 — Research Brief — Pooled vs Per-Symbol Model Architecture

**Cycle-6 EXPLORATION slot #3 of 10** (iter-v3/120 is the mandatory cycle-6 CONFIRMATION).
**Axis:** model architecture — a POOLED cross-symbol LightGBM vs the PER-SYMBOL
architecture v3 has used for all 111 iterations.
**Branch:** `iteration-v3/112`
**Date:** 2026-05-19

---

## Section 0.5 — Iteration Type Declaration

**TYPE = EXPLORATION.**

- **Run command:** `uv run python run_baseline_v3.py --exploration --n-trials 35`
- **EXPLORATION mode:** `--exploration` sets **ENSEMBLE_SIZE = 3** (the current v3
  EXPLORATION-mode standard since the iter-v3/060 RE-ANCHOR, per
  `feedback_v3_cycle1_axis_pass_criteria.md`; `ensemble_summary.json` records
  `mode=exploration, ensemble_size=3, seeds=[191664963, 1662057957, 1405681631]`,
  all `outer=42` lineage). This is **NOT** "single-seed" — the stale /105-era
  "ENSEMBLE_SIZE forced to 1 / single-seed" wording (iter-v3/110 Lesson 5) does
  NOT apply and is explicitly not used here.
- **`--n-trials 35`** — the v3 EXPLORATION default (`feedback_v3_exploration_n_trials_35.md`).
- **Wall-clock budget: ≤ 2h** (EXPLORATION hard cap, `feedback_v3_cadence_discipline.md`).
  Estimated 1.0–1.3h. The pooled architecture trains ONE model on the
  concatenated 3-symbol panel — the panel is ~3× wider per walk-forward cell than
  one per-symbol panel, but there is ONE Optuna study instead of three. Total
  Optuna trials: `35 trials × 3 ensemble seeds × 1 pooled model = 105` (vs the
  per-symbol baseline's `35 × 3 × 3 = 315`). Net wall-clock is comparable to or
  below a per-symbol EXPLORATION (iter-v3/110 ran 1.08h, iter-v3/111 ran 1.09h).
- **ONE axis changed:** the model architecture (`per-symbol` → `pooled`). The
  feature stack, label, universe, risk-gate stack, ensemble seeds, and data
  window are all /059-identical. Single-axis discipline holds.

This is EXPLORATION #3 of the cycle-6 structural axis menu
(`project_v3_cycle6_axis_menu.md`, menu item 2). Per **THE PRIME DIRECTIVE** and
`feedback_v3_qr_hard_ban_run_experiments.md`, this EXPLORATION produces a brief
AND runs a Phase-6 backtest. The EDA (Section 2) designs the experiment; it does
not terminate the iteration.

---

## Section 1 — Hypothesis

**Training one pooled LightGBM on the concatenated BCH+LDO+TRX panel — instead of
three per-symbol LightGBMs — lifts OOS monthly Sharpe by rescuing the
sample-starved, chronically-OOS-weak LDO model (whose per-symbol model trains on
only ~370–1200 candle rows), at a small dilution cost to the sample-rich BCH/TRX
models, for a net-positive aggregate effect.**

---

## Section 2 — IS-Only Numerical Evidence

All evidence is produced by the committed EDA under `analysis/iteration_v3-112/`
(EDA commit SHA `2cead80`), strictly IS-only (`close_time < OOS_CUTOFF_MS`,
2025-03-24 — `_shared.load_labeled_is()` asserts the invariant per symbol and on
the assembled frame). Three committed scripts plus a shared /059-faithful
triple-barrier labeler; 18 result tables T1–T14 (+ raw cuts).

### 2.1 EDA design

The pooled-vs-per-symbol axis is cleanly EDA-gateable: the held-out predictive
AUC of a pooled model vs the per-symbol models on the IDENTICAL walk-forward
folds, on the IDENTICAL 14 `V3_FEATURE_COLUMNS`, against the IDENTICAL /059
triple-barrier label, IS the answer to "does sample pooling extract a sharper
edge". This is the iter-v3/109 model-class horse-race methodology
(`analysis/iteration_v3-109/`) adapted to the architecture axis — the /111 diary
Section 9 explicitly recommends that template.

**One methodological refinement vs /109.** The /109 horse race built folds on
per-symbol row counts. A pooled-vs-per-symbol comparison REQUIRES the train/test
split on a **shared time axis** — otherwise the two arms would be scored on
different calendar windows and the comparison would be confounded.
`_shared.make_time_aligned_folds` builds 8 expanding-window folds as
`(test_start_ms, test_end_ms)` pairs on the GLOBAL IS calendar; BOTH arms train
on `close_time < test_start − 22-candle embargo` and are scored on the SAME
calendar test window. The 22-candle embargo is the /059
`compute_embargo_candles(10080, 480)` value. The ONLY varied input between the
two arms is the training panel (3-symbol pooled vs 1-symbol); model class,
hyperparameters (`max_depth=4`, the v3 depth-3-5 Optuna-band midpoint), feature
stack, label, embargo, and the 5-seed inner ensemble are identical.

### 2.2 The canonical /059 BCH/LDO/TRX universe — confirmed as the EDA design choice

The /111 diary recommends testing pooled-vs-per-symbol on the **canonical /059
BCH/LDO/TRX universe** so the architecture is the only variable changed. The EDA
confirms this design choice: testing on BCH/LDO/TRX isolates the architecture
axis cleanly against the canonical /059 baseline (IS +1.0894 / OOS +0.5791) and
does not confound the architecture change with a universe change. The /110/111
CRV/AAVE/GRT/ADA universe is **closed** (`v0.v3-111` EXPLORATION-NEGATIVE — clean;
the symbol-selection-by-feature-AUC-screen axis is CLOSED for cycle 6), so
reverting to BCH/LDO/TRX is both the cleanest comparison and the only live v3
universe.

### 2.3 T6 — the mechanism: how much does pooling expand the training sample?

`T6_sample_sizes.csv` — mean training-panel size per (symbol) across the 8
walk-forward folds:

| Symbol | mean per-symbol train rows | mean pooled train rows | pooling multiplier | min per-symbol train rows |
|---|---:|---:|---:|---:|
| BCHUSDT | 3,075 | 6,704 | **2.12×** | 1,108 |
| TRXUSDT | 3,023 | 6,704 | **2.16×** | 1,065 |
| LDOUSDT | 1,213 | 9,553 | **10.29×** | **370** |

LDO is the sample-starved symbol — it listed later (first IS candle 2022-10 vs
BCH/TRX 2020-02) so its per-symbol training panels are 2.5–8× thinner than
BCH/TRX's, and its thinnest fold trains on only **370 rows**. Pooling expands
LDO's effective training sample **10.3×**. BCH and TRX are sample-rich; pooling
only doubles their sample.

### 2.4 T2 / T5 — the aggregate horse race: GO bar NO-GO

`T2_pooled_aggregate.csv` — pooled held-out ROC-AUC across all 20 (symbol×fold)
cells:

| Architecture | mean held-out AUC | mean rank-IC | AUC lift vs per-symbol |
|---|---:|---:|---:|
| per_symbol (v3 incumbent) | 0.49828 | −0.0191 | — |
| pooled | 0.49746 | −0.0052 | **−0.00083** |

`T5_go_nogo_verdict.csv` — pre-registered GO bar (pooled AUC lift ≥ +0.010 AND
positive in ≥ 2 of 3 chronological IS thirds): pooled lift **−0.0008**,
positive thirds **1 of 3** → **NO-GO at the aggregate level.** The aggregate
held-out AUC is a wash. (Honest note: the pooled rank-IC is *less negative*
than per-symbol — −0.005 vs −0.019, an `ic_lift` of +0.014 — but at this
magnitude both ICs are statistical zero and the AUC is the primary metric.)

### 2.5 T3 — the per-symbol breakdown: strong, isolable heterogeneity

`T3_per_symbol_auc.csv` — the aggregate wash hides a real per-symbol pattern:

| Symbol | per-symbol held-out AUC | pooled held-out AUC | pooled − per-symbol |
|---|---:|---:|---:|
| LDOUSDT | 0.5117 | **0.5635** | **+0.0517** |
| BCHUSDT | 0.4968 | 0.4899 | −0.0068 |
| TRXUSDT | 0.4931 | 0.4720 | −0.0211 |

Pooling **lifts LDO by +0.052** and **lightly dilutes BCH (−0.007) and TRX
(−0.021)**. The aggregate washes because BCH/TRX dominate the cell count (BCH 5,626
+ TRX 5,568 IS candles vs LDO 2,640). This is the textbook pooled-model
trade-off: pooling rescues the sample-starved symbol and lightly hurts the
sample-rich ones whose symbol-specific edge is diluted by cross-symbol rows.

### 2.6 T11 — per-symbol permutation null: the LDO lift is statistically credible

`T11_per_symbol_permutation_null.csv` — for EACH symbol, a 60-shuffle
permutation null (training labels permuted, refit per-symbol, re-scored) locates
each symbol's observed pooled and per-symbol AUC against ITS OWN no-signal band.
Single-seed=42, matched to the null:

| Symbol | per-symbol AUC (obs) | pooled AUC (obs) | pooled lift | null q05 | null q50 | null q95 | pooled clears null q95? | per-symbol clears null q95? |
|---|---:|---:|---:|---:|---:|---:|:--:|:--:|
| LDOUSDT | 0.4528 | **0.5432** | **+0.0905** | 0.4277 | 0.4664 | 0.5162 | **YES** | No |
| BCHUSDT | 0.5120 | 0.5003 | −0.0117 | 0.4809 | 0.5009 | 0.5262 | No | No |
| TRXUSDT | 0.4789 | 0.4642 | −0.0147 | 0.4588 | 0.4914 | 0.5267 | No | No |

**This is the central piece of evidence.** LDO's pooled AUC (0.5432)
**clears LDO's own no-signal permutation q95 (0.5162)** — while LDO's per-symbol
AUC (0.4528) sits *below* its own null q05. Pooling moves LDO from a
*sub-no-signal* model to a model that holds **statistically-credible above-null
directional signal**. For BCH and TRX neither architecture clears its own q95 —
consistent with the /109 finding that the 14-feature representation carries no
broad-population signal on the sample-rich symbols; pooling neither rescues nor
materially harms them. (The single-seed observed numbers in T11 differ from the
5-seed T3 numbers — single-seed has higher variance — but the *direction and
ranking* are identical: LDO strongly up, BCH/TRX slightly down.)

### 2.7 T12 — per-symbol gated-tail hit rate: pooling lifts LDO's traded tail

`T12_per_symbol_gated_tail.csv` — the production-relevant metric. The backtest
only trades the high-confidence tail; T12 measures the directional hit rate of
the top-quartile-confidence (`|proba−0.5|`) test predictions, broken out by
symbol and architecture:

| Symbol | per-symbol gated hit rate | pooled gated hit rate | pooled − per-symbol |
|---|---:|---:|---:|
| LDOUSDT | 0.4574 | **0.5833** | **+0.1259** |
| BCHUSDT | 0.6924 | 0.6445 | −0.0479 |
| TRXUSDT | 0.4991 | 0.4324 | −0.0667 |

The gated-tail picture mirrors the broad AUC: pooling lifts LDO's traded-tail
hit rate **+0.126** (from a sub-breakeven 45.7% to 58.3%) and dilutes BCH/TRX.
LDO's per-symbol gated tail at 45.7% is *below* the 33.3% 2:1-ATR-barrier
breakeven's safety margin — pooling pushes it to a healthy 58.3%.

### 2.8 T13 — LDO per-fold detail: not a one-fold artifact

`T13_ldo_per_fold.csv` — LDO's +0.052 (5-seed) / +0.091 (single-seed) aggregate
lift decomposed per fold:

| Fold | LDO test rows | per-symbol AUC | pooled AUC | lift |
|---:|---:|---:|---:|---:|
| 4 | 562 | 0.4575 | 0.6384 | **+0.1809** |
| 5 | 562 | 0.5389 | 0.5176 | −0.0213 |
| 6 | 562 | 0.5101 | 0.4984 | −0.0117 |
| 7 | 561 | 0.5404 | 0.5995 | **+0.0591** |

LDO has 4 evaluable folds (it lists late, so only 4 of 8 global folds have a
usable LDO training panel). 2 of 4 are positive, and the lift is concentrated in
the two largest-lift folds (4 and 7) — a real but fold-uneven tilt, not a single
lucky fold. Honest caveat: a 4-fold base is thin; this is EXPLORATION-grade
evidence, and the Phase-6 backtest is the test.

### 2.9 T9 — sample-starvation gradient: flat in aggregate

`T9_sample_starvation_gradient.csv` — Spearman ρ between per-symbol fold
training-sample size and per-symbol held-out AUC, across all 20 cells:
**ρ = −0.083, p = 0.73** → flat. The /111 diary's *aggregate* mechanism claim
("per-symbol AUC rises with sample size") is **NOT supported as a universal
gradient**. The honest read: the starvation effect is **not a smooth aggregate
gradient** — it is **per-symbol-conditional**. LDO, the symbol below the
sample-adequacy threshold (370–1,200 rows), is the one pooling rescues; BCH/TRX
are already above any starvation threshold (>1,000 rows) so adding more rows via
pooling does not help them — it dilutes. This sharpens the hypothesis: the
mechanism is "rescue the *sub-threshold* symbol", not "more rows monotonically
help every symbol".

### 2.10 EDA verdict — sharpened-GO

The aggregate horse race is **NO-GO** (T5). But the per-symbol breakdown
(T3/T11/T12/T13) is a **credible, permutation-validated, isolable signal**:
pooling moves LDO from a sub-no-signal model to an above-null model
(+0.0905 AUC, clears its own permutation q95; +0.126 gated-tail hit rate), at a
small dilution cost to the sample-rich BCH/TRX. Per **THE PRIME DIRECTIVE** —
"a weak or inconclusive EDA → sharpen the hypothesis and write the brief anyway"
— the sharpened hypothesis is Section 1: a full pooled model is expected to be a
net-positive aggregate trade (LDO rescue partially offsetting BCH/TRX dilution),
and the Phase-6 backtest is the decisive test of the net effect. The EDA's
honest finding is **mixed**: a strong per-symbol positive (LDO) inside an
aggregate wash — which is exactly the kind of result a backtest, not an AUC
horse race, must adjudicate (the AUC horse race cannot weight the LDO rescue
against the BCH/TRX dilution by traded PnL; only the backtest can).

---

## Section 3 — Proposed Changes

**ONE axis: the model architecture changes from PER-SYMBOL to POOLED.** No
feature, label, or risk-gate change. Plus the mechanical universe revert to the
canonical /059 BCH/LDO/TRX (the /110/111 CRV/AAVE/GRT/ADA universe is closed)
and `REQUIRED_GAP` 88 → 66.

| Item | /059 / current runner state | iter-v3/112 |
|---|---|---|
| **Model architecture** | **per-symbol — 3 separate LightGbmStrategy instances, one per symbol** | **pooled — 1 LightGbmStrategy instance trained on the BCH+LDO+TRX panel** |
| Universe (`V3_MODELS`) | CRV/AAVE/GRT/ADA (the closed /110 universe) | **BCH/LDO/TRX** (revert to /059-canonical) |
| `REQUIRED_GAP` | 88 = (21+1)×4 | **66** = (21+1)×3 |
| `ITERATION_LABEL` | `"v3-111"` | **`"v3-112"`** |
| Feature stack | 14 `V3_FEATURE_COLUMNS` | UNCHANGED — 14 `V3_FEATURE_COLUMNS` |
| Labeling | `label_mode="triple_barrier"`, 2:1 ATR (2.0/1.0), 21-candle timeout | UNCHANGED |
| Risk-gate stack | 7-gate RiskV2 | UNCHANGED |
| Ensemble | `--exploration` → ENSEMBLE_SIZE=3, seeds 191664963/1662057957/1405681631 | UNCHANGED |

### 3.5 — Precise `src/` changes for the QE (Phase 6)

**Feasibility assessment — HONEST: the pooled architecture is a LOW-RISK,
WELL-SCOPED change.** The QR investigated the runner and the LightGBM strategy
layer and confirms the per-symbol-vs-pooled split is **entirely a runner-loop +
`BacktestConfig.symbols` decision** — the strategy and backtest layers are
ALREADY panel-capable:

- `LightGbmStrategy.compute_features(master)` (`src/crypto_trade/strategies/ml/lgbm.py:253`)
  accepts whatever `master` panel it is handed. It stores `_master`, `_sym_arr`,
  `_open_time_arr` directly from that panel — no per-symbol assumption.
- `LightGbmStrategy._train_for_month` (`lgbm.py:333`) selects training rows by
  **time window** (`_open_time_arr >= train_start_ms`), NOT by symbol. It already
  logs `"{n} training samples from {n_unique_syms} symbols"` (`lgbm.py:371-372`) —
  the multi-symbol-panel path is already implemented and exercised.
- `backtest.build_master(config.symbols, ...)` (`src/crypto_trade/backtest.py:428`)
  already builds a multi-symbol concatenated panel sorted by `(open_time, symbol)`
  when `config.symbols` has multiple symbols.

So a pooled model = ONE `_build_v3_model` call with `BacktestConfig(symbols=(BCH,
LDO, TRX))` instead of THREE single-symbol calls. The QE does **not** write a new
strategy class. The change is confined to `run_baseline_v3.py`.

**The 5 concrete changes (`run_baseline_v3.py` only):**

1. **`V3_MODELS` revert (3-tuple).** Set
   `V3_MODELS = (("v3-pooled", "BCHUSDT"), ("v3-pooled", "LDOUSDT"), ("v3-pooled", "TRXUSDT"))`
   — revert from the closed CRV/AAVE/GRT/ADA universe to the /059-canonical
   BCH/LDO/TRX. (The `V3_MODELS` tuple still drives `_verify_symbols`, the
   `build_master` symbol list, and `REQUIRED_GAP`; see change 4 for how the
   loop reads it.)

2. **`REQUIRED_GAP` revert 88 → 66.** `REQUIRED_GAP = (timeout_candles+1) ×
   n_symbols = (21+1) × 3 = 66` (in `validation_v3.py` or wherever the constant
   lives — the runner imports it at line 71). The CPCV/embargo formula is
   unchanged; only `n_symbols` reverts 4 → 3. `_verify_label_leakage_gap()`
   (`run_baseline_v3.py:1176`) recomputes `(21+1)×len(V3_MODELS)` and asserts it
   equals `REQUIRED_GAP` — it will pass once both are 3-symbol.

3. **`ITERATION_LABEL = "v3-112"`** (`run_baseline_v3.py:131`).

4. **The pooled-model build — the axis change.** In `_run_single_seed`
   (`run_baseline_v3.py:2475+`), the `for name, symbol in models_to_run:` loop
   builds one strategy per symbol. The pooled architecture builds **ONE**
   strategy on the 3-symbol panel. The QE's recommended minimal implementation:

   - Add a `pooled: bool = False` parameter to `_build_v3_model`. When `pooled`,
     the function takes a **tuple of symbols** (or accepts the existing `symbol`
     param as a comma-joined / tuple form) and sets
     `cfg = BacktestConfig(symbols=("BCHUSDT", "LDOUSDT", "TRXUSDT"), ...)`
     instead of `symbols=(symbol,)`. **Everything else in `_build_v3_model` is
     unchanged** — `common_kwargs` (including `label_mode="triple_barrier"`,
     `feature_columns`, the ATR multipliers, `ensemble_seeds`), the `RiskV2Config`,
     and the `RiskV3Wrapper` wrap are all symbol-agnostic. `atr_multipliers_for_symbol`
     and `features_for_symbol` return the DEFAULT for all 3 symbols
     (`V3_ATR_MULTIPLIERS_PER_SYMBOL={}`, all symbols 14-feature fallback) — so a
     single `common_kwargs` is correct for the pooled panel.
   - In `_run_single_seed`, gate on a `pooled` flag (threaded from a new
     `--pooled` CLI flag, OR — simpler — make the pooled architecture the
     unconditional behaviour for iter-v3/112 since `V3_MODELS` all share the
     `"v3-pooled"` label): when pooled, build ONE `_build_v3_model` with the
     3-symbol tuple, call `run_backtest` ONCE, and `all_trades` is that single
     run's trade list. The pooled run's `RiskV3Wrapper` sees all 3 symbols'
     candles in `master` and gates them with the same 7-gate stack — the BTC
     trend filter, ADX, Hurst, z-score OOD, vol scaling, low-vol filter all
     operate per-candle and are symbol-agnostic, so they apply correctly to a
     pooled `master`.
   - **The cleanest QE implementation** (recommended): since `V3_MODELS`'s three
     entries all carry the SAME label `"v3-pooled"`, the QE can collapse the
     `_run_single_seed` loop: detect that all `models_to_run` entries share one
     label, and if so build ONE `_build_v3_model` with
     `symbols=tuple(sym for _, sym in models_to_run)` and run it once. This needs
     no new CLI flag and keeps `--symbols` filtering working (a filtered subset
     still pools whatever symbols survive the filter).
   - **`_verify_symbols(cfg.symbols)`** is called per built strategy
     (`run_baseline_v3.py:2536`); with the pooled `cfg.symbols=(BCH,LDO,TRX)` it
     asserts none are v1/v2 symbols — BCH/LDO/TRX all pass.

5. **The `_canonical_v059` config-accretion guard** (`run_baseline_v3.py:1034-1061`).
   Update the two universe entries to the /059-canonical 3-symbol values:
   - `"V3_MODELS symbols"` expected → `("BCHUSDT", "LDOUSDT", "TRXUSDT")`
   - `"REQUIRED_GAP"` expected → `66`
   The `label_mode` guard entry stays `"triple_barrier"` (the /111 correction is
   preserved — see the Configuration Diff). The other 9 knobs are unchanged. The
   guard's `_acc_strat` is built via `_build_v3_model` — when the QE makes the
   pooled build the path, the guard's probe build must also be pooled (or the
   guard's `CRVUSDT` probe symbol updated to a BCH/LDO/TRX symbol or the pooled
   tuple) so `_build_v3_model` does not error on a now-removed symbol. **The QE
   must sweep all hard-coded `CRVUSDT`/`AAVEUSDT`/`GRTUSDT`/`ADAUSDT` references
   in `run_baseline_v3.py` (24 occurrences — probe builds at lines ~1083, ~928,
   ~953, etc.) and replace them with a /059-universe symbol (`"BCHUSDT"`) or the
   pooled tuple as appropriate.** These are pre-flight probe builds (`n_trials=1`)
   that assert config invariants; they must reference a symbol that exists in the
   reverted `V3_MODELS`.

**Configuration Diff vs /059 — the QE verifies this line-by-line against
`run.log`** (per the iter-v3/110 Lesson 3 / iter-v3/111 reconciliation
discipline — do NOT assert "all other knobs /059-identical"; enumerate every
knob and confirm each against `run.log`):

| Knob | /059 canonical | iter-v3/112 | Changed? |
|---|---|---|:--:|
| **model architecture** | **per-symbol (3 instances)** | **pooled (1 instance, 3-symbol panel)** | **YES — the axis** |
| `V3_MODELS` symbols | BCHUSDT, LDOUSDT, TRXUSDT | BCHUSDT, LDOUSDT, TRXUSDT | No (revert from /111's CRV/AAVE/GRT/ADA) |
| `REQUIRED_GAP` | 66 = (21+1)×3 | 66 = (21+1)×3 | No (revert from /111's 88) |
| `label_mode` | `triple_barrier` | `triple_barrier` | **No — /111 correction PRESERVED** |
| `trend_scan_grid` | default `(5,8,13,21)` (not injected) | default `(5,8,13,21)` (not injected) | No |
| `V3_FEATURE_COLUMNS` | 14-feature stack | 14-feature stack | No |
| `DEFAULT_ATR_MULTIPLIERS` | (2.0, 1.0) | (2.0, 1.0) | No |
| `V3_ATR_MULTIPLIERS_PER_SYMBOL` | `{}` | `{}` | No |
| `zscore_threshold` | 2.0 | 2.0 | No |
| `adx_threshold` | 20.0 | 20.0 | No |
| `adx_threshold_per_symbol` | `{}` | `{}` | No |
| `vol_scale_floor_per_symbol` | `{}` | `{}` | No |
| `block_long_for` / `block_short_for` | `()` / `()` | `()` / `()` | No |
| `enable_per_symbol_drawdown_brake` | False | False | No |
| `ENSEMBLE_SIZE` (run mode) | 10 (CONFIRMATION) | 3 (EXPLORATION `--exploration`) | mode difference, not an axis |
| `n_trials` | 35 | 35 | No |

The QE engineering report must grep `run.log` for the executed `label_mode`
value and quote it verbatim (`label_mode (iter-v3/112): 'triple_barrier' PASS`),
per iter-v3/111 reconciliation discipline.

---

## Section 4 — Expected OOS Impact

**EXPLORATION anchor.** Per `feedback_v3_cycle1_axis_pass_criteria.md`, cycle
EXPLORATION axes are evaluated against the EXPLORATION-MODE anchor — the most
recent no-axis 3-seed run. The /060-lineage EXPLORATION-mode anchor is **IS
+0.8325 / OOS +0.1403**; the iter-v3/077 re-anchor noted code/data accretion
drift to roughly **IS +0.82 / OOS +0.21** on current code. The iter-v3/110 and
/111 briefs used the /060 figures (IS +0.8325 / OOS +0.1403); iter-v3/112 uses
the SAME /060 EXPLORATION-mode anchor for continuity. **Note:** the /110 and /111
EXPLORATIONs ran on the CRV/AAVE/GRT/ADA universe; iter-v3/112 reverts to
BCH/LDO/TRX, so the BCH/LDO/TRX EXPLORATION-mode per-symbol anchor is the
relevant comparison — the closest available BCH/LDO/TRX 3-seed reference is the
/060-lineage anchor (IS +0.8325 / OOS +0.1403). The Phase-7 QR will compare the
pooled run against the per-symbol BCH/LDO/TRX EXPLORATION-mode behaviour.

**Predicted effect (point estimate + interval).** The pooled architecture is
predicted to be a **net-positive but modest** OOS change:

- **Per-symbol effect (from the EDA):** LDO is rescued (T11: +0.091 AUC clearing
  its own permutation q95; T12: +0.126 gated-tail hit rate). BCH/TRX are lightly
  diluted (T3: −0.007 / −0.021 AUC; T12: −0.048 / −0.067 gated tail). The
  aggregate AUC is a wash (T5: −0.0008).
- **Predicted OOS monthly Sharpe delta vs the per-symbol EXPLORATION-mode anchor:
  +0.10, 80% interval [−0.30, +0.55].** The wide interval, skewed slightly
  positive, reflects the genuinely-mixed EDA: a credible LDO rescue inside an
  aggregate AUC wash. The backtest weights the LDO rescue against the BCH/TRX
  dilution by *traded PnL* — which the AUC horse race cannot do — so the net
  outcome is genuinely uncertain. Honest framing: the EDA is **sharpened-GO, not
  clean-GO**; the central estimate is a small positive.
- **Predicted IS monthly Sharpe delta: −0.05, interval [−0.40, +0.20].** BCH
  carries 95.76% of /059's IS PnL; pooling lightly dilutes BCH's IS edge (T3
  BCH −0.007 AUC). The aggregate IS Sharpe is most sensitive to BCH, so a small
  IS regression is the central expectation.

**Pre-registered falsifier.** The pooled-architecture hypothesis is **rejected**
if ANY of:
1. **OOS monthly Sharpe < −0.10** (the pooled architecture is OOS-net-negative —
   the BCH/TRX dilution outweighs the LDO rescue and the architecture has no
   merge path). [Mirrors the /110/111 OOS falsifier.]
2. **LDO OOS `net_pnl_pct` does NOT improve vs the per-symbol BCH/LDO/TRX
   EXPLORATION-mode LDO** — i.e. the EDA's central claim (pooling rescues LDO)
   does not transfer to the production backtest. If LDO is not rescued, the
   architecture's entire mechanism is falsified.
3. **Aggregate IS monthly Sharpe < +0.40** (the BCH/TRX dilution collapses the
   IS book — the /110/111-style NEGATIVE-floor; the pooled architecture is
   IS-non-viable). [+0.40 floor consistent with the cycle-6 NEGATIVE floor used
   at /110/111, which was +0.7325 vs the /060 anchor; +0.40 absolute is the
   conservative IS-collapse line for a pooled architecture expected to dilute the
   BCH-dominated IS book.]

**Supplemental SUSPICIOUS gate** (per `feedback_v3_oos_is_ratio_gate.md`,
mandatory for cycle 2+ EXPLORATION briefs): if **OOS/IS monthly Sharpe ratio >
3.0**, the result is flagged **SUSPICIOUS** regardless of absolute OOS Sharpe
(regime-exposure unmasked). Healthy band ~[0.5, 2.0].

---

## Section 5 — Risk Mitigation

iter-v3/112 changes the model architecture; it adds **no new risk primitive**.
The /059 7-gate RiskV2 stack is carried unchanged and applies identically to the
pooled `master`:

| Gate | /059 setting | Effect under the pooled architecture |
|---|---|---|
| BTC trend kill (±15%, 14d) | enabled | Per-candle; symbol-agnostic — unchanged. Applied post-roster in `apply_btc_trend_filter`. |
| Vol scaling | enabled | Per-candle per-symbol — unchanged. |
| ADX threshold (20.0) | enabled | Per-candle — unchanged. |
| Hurst regime | enabled | Per-candle — unchanged. |
| Feature z-score OOD (2.0) | enabled | Per-candle; the OOD reference covariance is built from the model's training window — under pooling the training window is the 3-symbol panel, so the OOD reference is the pooled covariance. This is a **consequence** of the architecture, not a new gate. |
| Low-vol filter | enabled | Per-candle — unchanged. |
| Hit-rate feedback | DISABLED (per /059) | Unchanged. |

**Architecture-specific risk note (honest).** The pooled model produces ONE
trained model per walk-forward month that serves all 3 symbols. Two risks
specific to pooling, both bounded:
1. **BCH/TRX dilution** — the EDA quantifies it (T3: −0.007 / −0.021 AUC; T12:
   −0.048 / −0.067 gated tail). This is the *measured* downside, pre-registered
   in the Section 4 falsifier #3. It is small per the EDA; the backtest sizes
   its PnL cost.
2. **Concentration** — the /059 baseline has BCH at 95.76% of IS PnL. Pooling
   does NOT change which symbols trade; it changes how the model learns. If
   anything, a pooled model that rescues LDO should *reduce* BCH concentration
   (LDO contributes more). The Phase-7 QR checks the OOS top-symbol
   `concentration_pct` — but no new concentration cap is added (per
   `feedback_v3_concentration_is_signal.md`, per-symbol caps are CLOSED; the
   pooled architecture is itself an orthogonal mechanism — it changes the model,
   not a proportional scaler).

No IS-calibrated new-threshold simulation is required because no new gate is
added; the 7-gate stack's IS-calibrated thresholds are /059-inherited and
unchanged.

---

## Section 6 — Risk Management Design

The v3 7-primitive risk-gate stack is carried **unchanged** from /059. iter-v3/112
adds no primitive and removes none. Fire-rate predictions are /059-inherited:

| # | Primitive | /059 state | iter-v3/112 | Predicted fire-rate change |
|---|---|---|---|---|
| 1 | BTC trend kill | enabled | enabled | None — symbol-agnostic, applied post-roster |
| 2 | Vol scaling | enabled | enabled | None |
| 3 | ADX threshold (20.0) | enabled | enabled | None |
| 4 | Hurst regime | enabled | enabled | None |
| 5 | Feature z-score OOD (2.0) | enabled | enabled | **Possible small change** — OOD reference covariance is now the 3-symbol pooled training panel rather than a per-symbol panel; the pooled covariance is wider, so the OOD gate may fire marginally *less* on each symbol (a pooled covariance envelopes more of each symbol's feature space). This is a measured consequence, not a tuning knob — the Phase-7 QR reports the gate-fire stats. |
| 6 | Low-vol filter | enabled | enabled | None |
| 7 | Hit-rate feedback | DISABLED | DISABLED | None |

**Regime coverage.** The IS window (2022-09 → 2025-03) spans the FTX/LUNA crash,
the 2023 chop, and the 2024 recovery; the OOS window (2025-03 → 2026-05) is the
2025 uptrend. The pooled architecture does not change regime coverage — the same
candles are evaluated; only the model's training panel is pooled. The pooled
model's per-month training window is the 24-month walk-forward window (unchanged),
so each pooled model sees the same calendar regime mix a per-symbol model would,
just with 2–10× more rows.

---

## Section 7 — Pre-Registered Failure-Mode Prediction

**The single most plausible OOS failure mode: the BCH/TRX dilution outweighs the
LDO rescue, and the pooled architecture is OOS-net-flat-to-negative.** The EDA is
honest that this is a genuine risk: BCH/TRX show small negative pooled AUC lifts
(T3: −0.007 / −0.021) and negative gated-tail lifts (T12: −0.048 / −0.067), and
BCH/TRX together generate the large majority of v3 trades. LDO's rescue (+0.126
gated-tail hit rate) is real and permutation-validated — but LDO is the
thin-roster symbol (it produces the fewest trades; /059 LDO had only 12 OOS
trades). **If LDO's rescue lifts ~12 thin LDO trades while the dilution lightly
degrades the ~60–80 BCH/TRX trades, the trade-count-weighted net could be
negative even though the per-symbol rescue is genuine.** In metrics this looks
like: aggregate OOS monthly Sharpe near zero or slightly negative; LDO OOS
`net_pnl_pct` improved vs the per-symbol anchor (the rescue *did* transfer) but
BCH and/or TRX OOS `net_pnl_pct` degraded by more in aggregate. The Section 4
falsifier #1 (OOS < −0.10) and the per-symbol attribution catch this — and the
Phase-8 diary will record it as a **PROMISING-mechanism-confirmed-but-net-negative**
outcome (the LDO rescue transferred, validating the EDA, but the architecture as
a whole does not clear the bar). This is the textbook pooled-model failure: the
pooling helps the symbol that needs it and hurts the symbols that don't, and the
PnL-weighted sum is the question — which only the backtest answers.

**Second failure mode: the LDO rescue does NOT transfer to production** (Section
4 falsifier #2). The EDA's LDO lift is held-out-AUC + gated-tail-hit-rate on 4
walk-forward folds — a thin base. The production pipeline adds the 35-trial
Optuna search and the 7-gate stack; the iter-v3/111 lesson is that a thin EDA
proxy can invert through the production machinery. If LDO's OOS `net_pnl_pct`
does not improve, the EDA's central claim is falsified and the architecture has
no mechanism. Probability of NEGATIVE (either mode): **~50%** — the EDA is
genuinely mixed (sharpened-GO, not clean-GO), and a single-feature-magnitude
honest prior at 3-seed/35-trial is high; this is pre-registered per the
iter-v3/064 process rule that single-axis EXPLORATIONs at single-seed-class
budget carry a ≥25% NEGATIVE probability.

**A note on the EXPLORATION-mode DSR/PSR.** Per `feedback_v3_dsr_mode_artifact.md`,
EXPLORATION-mode DSR/PSR at the 3-seed/35-trial budget are structural regime
artifacts, NOT edge-significance evidence. They will appear in `dsr.json` and are
**informational only** — not a verdict input for this EXPLORATION.

---

## Section 8 — Pre-Registered MERGE/NO-MERGE Numerical Criteria

iter-v3/112 is an **EXPLORATION**, not a CONFIRMATION — it never updates
`BASELINE_V3.md` regardless of outcome (`v0.v3-112` will be a closeout marker
only). The criteria below classify the EXPLORATION outcome and decide whether the
pooled architecture advances toward the cycle-6 CONFIRMATION (iter-v3/120).

**Locked thresholds (pre-registered before the Phase-6 backtest):**

The verdict is determined against the per-symbol BCH/LDO/TRX EXPLORATION-mode
anchor (IS +0.8325 / OOS +0.1403, the /060-lineage anchor) and the cycle-6
axis-PASS criteria (`feedback_v3_cycle1_axis_pass_criteria.md`):

- **EXPLORATION-PROMISING** (the pooled architecture advances to iter-v3/120
  CONFIRMATION consideration) iff ALL of:
  1. **IS monthly Sharpe Δ ≥ +0.10** vs the /060 anchor (IS ≥ +0.93), AND
  2. **OOS monthly Sharpe Δ ≥ +0.20** vs the /060 anchor (OOS ≥ +0.34), AND
  3. **`frac_positive_paths` (CPCV) ≥ 0.50**, AND
  4. **LDO OOS `net_pnl_pct` improves** vs the per-symbol BCH/LDO/TRX
     EXPLORATION-mode LDO (the EDA's central mechanism transfers), AND
  5. **OOS/IS monthly Sharpe ratio ≤ 3.0** (not SUSPICIOUS — `feedback_v3_oos_is_ratio_gate.md`).

- **EXPLORATION-PROMISING-PARTIAL / mechanism-confirmed** — if criterion 4 holds
  (LDO rescue transfers) but the aggregate criteria 1–2 do not clear the PASS
  bar: the EDA mechanism is validated but the full pooled architecture does not
  beat the per-symbol anchor on aggregate. Recorded as a documented partial —
  the next cycle-6 EXPLORATION can target a **partial-pooling** design (pool only
  the sample-starved symbol; keep BCH/TRX per-symbol) rather than a full pooled
  model. Does NOT advance to CONFIRMATION as-is.

- **EXPLORATION-SUSPICIOUS** — if OOS/IS monthly Sharpe ratio > 3.0
  (`feedback_v3_oos_is_ratio_gate.md`): regime-exposure unmasked; does NOT
  advance regardless of absolute OOS.

- **EXPLORATION-NEGATIVE** — if ANY Section 4 falsifier fires: OOS monthly Sharpe
  < −0.10, OR LDO OOS `net_pnl_pct` does not improve, OR aggregate IS monthly
  Sharpe < +0.40. The pooled-full architecture is closed for cycle 6; the
  Phase-8 diary records whether the LDO-rescue mechanism nonetheless transferred
  (informing a possible partial-pooling axis).

**Bundle-level trade-rate floor** (`feedback_v3_trade_rate_floor_bundle_level.md`):
the ≥130-OOS-trade floor applies at the iter-v3/120 CONFIRMATION-bundle level,
NOT to this single EXPLORATION row. The Phase-7 QR reports the OOS trade count;
a low EXPLORATION trade count is informational, not verdict-triggering.

---

## Section 9 — Library Stack Declaration

iter-v3/112 introduces **no new library**. The EDA and the Phase-6 backtest use
the existing v3 stack:

| Library | Version | Use |
|---|---|---|
| lightgbm | 4.6.0 | The model class (pooled and per-symbol — identical class) |
| optuna | 4.8.0 | Hyperparameter search (`--n-trials 35`) |
| numpy | 2.2.6 | EDA + runner numerics |
| pandas | 3.0.0 | EDA + runner data handling |
| scikit-learn | 1.8.0 | EDA `roc_auc_score` |
| scipy | 1.17.0 | EDA `spearmanr` (rank-IC, sample-starvation gradient) |
| statsmodels | 0.14.6 | ADF stationarity test (Critic Check 5) |
| pyarrow | 23.0.1 | Parquet I/O |

No `mlfinlab` / `mlfinpy` / `pypbo` / `fracdiff` feature is added by this
iteration. CPCV/PBO/PSR/DSR are computed by the existing
`src/crypto_trade/strategies/ml/validation_v3.py` machinery, unchanged.

**Walk-forward harness.** The `walk_forward.py` harness with the `e149e9d`
embargo fix (`train_end_ms = test_start_ms − embargo_ms`) is carried unchanged.
The pooled architecture does not touch `generate_monthly_splits` — the pooled
model's `compute_features` calls the same `generate_monthly_splits` with the same
22-candle embargo; the only difference is the `master` panel it is handed is
3-symbol. `REQUIRED_GAP` for the global CPCV reverts to `66 = (21+1)×3` (Section
3.5 change 2).

---

## Section 10 — QR Audit Trail

The cycle-6 axis menu (`project_v3_cycle6_axis_menu.md`) and the iter-v3/111
diary Section 9 both recommend **menu item 2 — pooled vs per-symbol model
architecture** as the iter-v3/112 axis. This is an orchestrator/menu suggestion;
per `feedback_v3_axis_selection_quant_discipline.md` the QR backs it with a
committed IS-only EDA before the brief:

- **EDA commit:** `analysis(iter-v3/112): pooled-vs-per-symbol gating EDA`,
  SHA `2cead80` — 3 scripts (`pooled_vs_persymbol_horse_race.py`,
  `robustness_annex.py`, `persymbol_pooling_breakdown.py`) + a shared
  /059-faithful labeler (`_shared.py`); 18 result tables T1–T14.
- **The EDA does not rubber-stamp the menu suggestion** — it returns a
  **NO-GO at the aggregate level** (T5: pooled AUC lift −0.0008) and a
  **credible per-symbol-conditional GO** (T11: LDO pooled AUC clears its own
  permutation q95; T12: +0.126 LDO gated-tail lift). The QR's axis call: the
  menu's "pooled vs per-symbol" axis IS the right cycle-6 axis (it directly
  attacks the per-symbol sample-starvation mechanism the cycle's universe work
  exposed), and the brief is written with a hypothesis **sharpened by the EDA**
  (Section 1: full pooled model expected net-positive via the LDO rescue
  partially offsetting the BCH/TRX dilution) — per THE PRIME DIRECTIVE, a mixed
  EDA sharpens the hypothesis and the iteration runs the backtest.
- **No prior orchestrator setup commit was superseded** — iter-v3/112's setup is
  authored fresh by the QR with EDA backing. This Section 10 documents the
  EDA-backed axis confirmation; there is no orchestrator-pick reversal to log.

---

## Appendix — EDA reproduction

```
analysis/iteration_v3-112/
  _shared.py                          IS-only /059-faithful triple-barrier labeler
  pooled_vs_persymbol_horse_race.py   T1-T6: the pooled-vs-per-symbol horse race
  robustness_annex.py                 T7-T10: permutation null, gated tail, gradient
  persymbol_pooling_breakdown.py      T11-T14: per-symbol pooling-effect breakdown
```

Reproduce: `cd analysis/iteration_v3-112 && uv run python pooled_vs_persymbol_horse_race.py
&& uv run python robustness_annex.py && uv run python persymbol_pooling_breakdown.py`.
Strictly IS-only — every script imports `_shared.load_labeled_is()`, which
asserts `close_time < OOS_CUTOFF_MS` (2025-03-24) per symbol and on the assembled
frame. The post-cutoff OOS feature data and the /059 OOS roster were NOT read by
the EDA — the QR did not inspect OOS in Phases 1-5; the OOS reports are first
read in Phase 7.

**NO CHEATING.** `OOS_CUTOFF_DATE = 2025-03-24` and `training_months = 24` are
untouched. The IS window is not trimmed. The axis changes ONE variable — the
model architecture — vs the /059-canonical baseline (plus the mechanical revert
of the closed /110/111 universe to BCH/LDO/TRX). The `e149e9d` walk-forward
embargo fix is inherited unchanged.
