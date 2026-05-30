# iter-v1/035 — Research Brief

**Iteration**: iter-v1/035
**Date**: 2026-05-30
**TYPE**: EXPLORATION
**Cycle**: 5, EXP 2 of 10 (renumbered pivot per /034 NEGATIVE evidence)
**Branch**: `iteration-v1/035`
**Author**: QR (autopilot)

---

## Section 0 — Hypothesis

**H1 (PRIMARY)**: Replacing the v1 baseline's triple-barrier σ_t labeling primitive
with **trend-scanning labels** (López de Prado AFML Ch.5 §5.5; Wald-test horizon
selection on OLS slope across `trend_scan_grid=(5, 8, 13, 21)`) surfaces a
**different signal subspace** than triple-barrier and yields ≥ +0.20 OOS monthly
Sharpe lift over `BASELINE_V1` (+0.6637).

**H1a (mechanism)**: Triple-barrier labels are TP/SL-first-hit signals — they
encode "did price reach +K·σ before −K·σ within 21 bars?" — a *path-dependent*
binary. Trend-scanning labels encode "is there a statistically significant
directional drift across the next 21 bars at the most-significant horizon?" — a
*regression-significance* primitive. The EDA below shows 24-36% of bars get
*opposite* sign labels under the two regimes (sign-agreement 64-76%), which
is direct evidence of a genuinely different supervised target rather than a
proxy of the same one.

**H1b (falsifiable)**: If F1 OOS Δ < +0.20 AND no symbol shows OOS Sharpe lift
≥ +0.10 vs baseline per-symbol attribution, the trend-scanning labeling axis is
classified INERT-or-worse and CLOSED at v1 EXPLORATION budget.

---

## Section 0.5 — Iteration Type, Cadence Position, Wall-Clock

- **TYPE**: EXPLORATION
- **Cadence**: cycle-5 EXPLORATION 2 of 10 (renumbered pivot — /034 basis_zscore_30
  was cycle-5 EXP 1 and closed EXPLORATION-NEGATIVE / LEARNED-NEG; per Critic /034
  Path Forward + user directive 2026-05-30 "freedom to decide", /035 pivots to a
  DIFFERENT MECHANISM CLASS — labeling axis instead of feature-addition axis).
- Pool-A NEW-feature-addition axis structural rejection now n=3 (/023 funding clean,
  /025 OI catastrophic, /034 basis clean). Pivot to labeling axis breaks the
  feature-addition-monoculture failure pattern.
- **NO kill-switches** (user directive 2026-05-30 + `docs/skill: no runtime kill-switches`).
- **Wall-clock target**: 1.8h modal at v1 EXPLORATION standard (n_trials=18,
  ENSEMBLE_SIZE=3). Cap NOT enforced via kill — honest overrun acceptable per
  cycle-5 discipline.

---

## Section 0.6 — Axis-Family Rotation (v1-only)

- **Axis family**: `labeling` (LM Master cycle-5 menu axis #6 — first invocation since
  /014 EWMA σ_t in cycle-2, ~21 EXPLORATIONs ago).
- **Prior 5 EXPLORATION families** (from `briefs-v1/exploration_catalog.md`):
  - iter-v1/030: meta-labeling (NEGATIVE-CATASTROPHIC; axis CLOSED at v1)
  - iter-v1/031: sample-weighting (PROMISING-BASIN-RELOCATION-ARTIFACT)
  - iter-v1/032: sample-weighting-isolation (PROMISING-AXIS-PARTIAL)
  - iter-v1/033: CONFIRMATION bundle (BLOCK-FINAL)
  - iter-v1/034: feature-family (EXPLORATION-NEGATIVE / LEARNED-NEG; basis_zscore_30)
- **Rotation status**: **VALID** — `labeling` is NOT in any of the prior 5
  EXPLORATION slots. Last `labeling` axis at /014 (σ_t EWMA, PROMISING). Five
  prior slots disperse across 3 distinct families (meta-labeling, sample-weighting,
  feature-family) — not monoculture.
- **One-sentence rationale**: per Critic /034 Path Forward, pivoting to a
  fundamentally different MECHANISM CLASS than feature-add breaks the n=3
  Pool-A new-feature-LEARNED-NEG pattern; trend-scanning is the next-priority
  labeling axis per cycle-5 menu and AFML Ch.5 §5.5 canonical primitive.

---

## Section 1 — IS-Only Evidence + Phase 1 Trend-Scanning Code Audit

### Section 1.0 — Code audit: trend-scanning ALREADY IMPLEMENTED in shared `labeling.py`

The trend-scanning primitive is fully implemented:

| Surface | Location | Status |
|---|---|---|
| Core helper | `src/crypto_trade/strategies/ml/labeling.py:132-214` (`_trend_scan_label`) | implemented (iter-v3/105) |
| Dispatcher | `src/crypto_trade/strategies/ml/labeling.py:284-292`, `396-407` (`label_trades` `label_mode="trend_scanning"` branch) | implemented |
| Strategy attribute | `src/crypto_trade/strategies/ml/lgbm.py:176-177, 290-291, 656-657` | implemented |
| Test suite | `tests/strategies/ml/test_trend_scanning_label_mode.py` — 8 tests (causality, monotone, leakage, integration) | PASS at HEAD |

**Implications for iter-v1/035**: NO new feature module needed; NO new labeling module
needed; ONLY plumbing changes — thread `label_mode` + `trend_scan_grid` from
`run_baseline_v1.py` CLI through `run_model()` to `LightGbmStrategy.__init__()`,
plus add a dispatch branch + a dispatch banner + `"v1-035"` to the BASELINE
catch-all exclusion tuple. This is materially less code than /034 (which needed
NEW basis module + features registry add).

### Section 1.1 — Labeling primitive specification (canonical)

For each candidate bar t in `_train_for_month`'s training window:

```
For h in (5, 8, 13, 21):
  y[0]   = close[t]
  y[k+1] = close[t+k+1]   for k in [0, h-1]   (h+1 prices)
  x       = [0, 1, ..., h]
  slope  = sum((x-x̄)(y-ȳ)) / sum((x-x̄)²)
  se     = sqrt( residual_ss / (h-1) / sum((x-x̄)²) )
  t_stat = slope / se
  abs_t  = |t_stat|

h*       = argmax_h abs_t
label    = +1 if slope(h*) >= 0 else -1
fwd_pct  = (close[t+h*] - close[t]) / close[t] * 100
long_pnl  = fwd_pct - fee_pct
short_pnl = -fwd_pct - fee_pct
weight   = abs(labeled_pnl)
```

- **Past-only**: only forward closes `close[t+1 .. t+h]` are read; `close[t-k]`
  for any k > 0 is never accessed. Hard-causality test at
  `tests/strategies/ml/test_trend_scanning_label_mode.py::test_trend_scanning_hard_causality`
  proves removing bars > `max(grid)=21` does not change earlier-bar labels.
- **No look-ahead via embargo**: `max(grid)=21` candles = `timeout_minutes/interval_minutes`
  = `10080 / 480 = 21` at 8h. The walk-forward gap remains identical to the
  baseline triple-barrier label horizon. No CV-embargo recomputation required.
- **Zero labels**: with the default grid, `_trend_scan_label` always returns
  ±1 (never 0); proven empirically below.

### Section 1.2 — Label distribution per symbol (IS-only)

Output of `analysis/iteration_v1-035/trend_scanning_eda.py` →
`trend_scanning_label_distribution.csv`. Columns: TS = trend-scanning label;
TB = triple-barrier label (with `tp_pct=4.0, sl_pct=2.0` for comparison only —
runtime uses ATR-scaled barriers, but the relative distribution shape is
preserved).

| Symbol | n_cand | TS +1 / -1 | TB +1 / -1 | TS w̄ | TB w̄ | h=5 / h=8 / h=13 / h=21 share | TS↔TB sign-agreement |
|---|---|---|---|---|---|---|---|
| BTCUSDT | 5,705 | 55.3% / 44.7% | 52.1% / 47.9% | 2.56% | 8.42% | 14.0% / 14.6% / 22.6% / 48.7% | 76.2% |
| ETHUSDT | 5,705 | 55.3% / 44.7% | 51.9% / 48.1% | 2.16% | 8.48% | 13.1% / 15.2% / 22.2% / 49.5% | 71.8% |
| LINKUSDT | 5,656 | 52.3% / 47.7% | 49.9% / 50.1% | 2.32% | 8.47% | 12.4% / 16.5% / 24.1% / 47.0% | 64.4% |
| LTCUSDT | 5,665 | 52.9% / 47.1% | 51.9% / 48.1% | 2.55% | 8.45% | 13.9% / 14.9% / 24.3% / 46.9% | 68.5% |
| DOTUSDT | 5,003 | 49.2% / 50.8% | 47.1% / 52.9% | 1.84% | 8.47% | 13.6% / 15.4% / 22.6% / 48.4% | 66.3% |

**Three observations from §1.2**:

1. **Class balance is well-behaved** — TS labels are 49–55% +1 across all 5
   symbols, mildly more bullish than TB but well within usable LightGBM class-balance
   bounds. **No re-balancing or `scale_pos_weight` retune required.**

2. **TS↔TB sign-agreement = 64–76%** — meaning **24–36% of training bars receive
   the OPPOSITE direction label** under trend-scanning vs triple-barrier.
   **LINKUSDT shows the largest divergence (64.4% agreement)** which makes LINK
   the highest-prior axis-target — basis 1.1's strongest baseline cohort
   (PROMISING-INERT-FAV at /018, +0.80 OOS specialist). This is genuine
   supervised-target divergence, not proxy-of-same.

3. **Horizon selection skewed long: ~47-49% of bars pick h*=21** (the maximum).
   This is because OLS |t-stat| scales as `√(n-2)` so longer windows have more
   statistical power. h=13 captures ~22-24%; h=5/8 split the remaining ~28%.
   Trees see a TIME-VARYING decision horizon — the LightGBM model can implicitly
   learn that long-horizon bars (high abs_t at h=21) are "high-conviction trend"
   bars and short-horizon bars (h=5/8 picked) are "short-burst" bars.

### Section 1.3 — Weight-scale shift (LOAD-BEARING for HIGH-RISK declaration)

**Critical**: TS weight mean ≈ 1.8-2.6% across symbols vs TB weight mean ≈ 8.4-8.5%.
TS weights are **3.3-4.6× smaller** than TB weights on average.

Mechanism: TB weight = `abs(long_pnl)` where `long_pnl` = `tp_pct − fee` or
`-sl_pct − fee` or `fwd_return − fee` — typically clamped at the ±4%/±2% TP/SL
bands, so the modal weight is large. TS weight = `abs(fwd_return at h*) − fee`
— typically a single-digit-percent realized return at the selected horizon.

**Implications for LightGBM**:
- `sample_weight_mode="abs_pnl"` baseline default — the absolute scale of
  `sample_weight` is irrelevant for LightGBM's gradient (it only matters
  relatively across rows); BUT the *distribution shape* matters because
  LightGBM regularization terms (reg_alpha, reg_lambda) interact with the
  weighted loss surface.
- The TS weight DISTRIBUTION is tighter (std 1.0-1.3 vs 2.0-2.2) — LESS
  variation in row weights → the model treats most TS rows similarly, in
  contrast to TB where TP-hits get 4× the weight of timeout-exits.
- **This is a TRAINING-OBJECTIVE DOMAIN CHANGE.** Hence HIGH-RISK declared
  (Section 2.5).

### Section 1.4 — Per-cohort priors from §1.2

| Symbol | TS divergence (1 − agreement) | Baseline class | Cycle-5 prior |
|---|---|---|---|
| LINK | 35.6% | POSITIVE_EVERYWHERE (/018 PROMISING-INERT-FAV) | HIGHEST — different labels on a strong-baseline cohort = highest expected lift |
| ETH (in Pool A) | 28.2% | /019 PROMISING with gate | MEDIUM-HIGH |
| LTC | 31.5% | /028 PROMISING (atr_sl=1.0) | MEDIUM |
| DOT | 33.7% | mixed (/029 TF) | MEDIUM |
| BTC (in Pool A) | 23.8% | mixed | LOWEST |

LINK is the prime target — 35.6% of training-bar labels flip under trend-scanning
on a cohort that the v1 baseline already treats favorably. If trend-scanning
captures a structurally different signal (regime-significance vs path-dependent
TP-first-hit), the model's ability to discriminate on LINK should improve.

### Section 1.5 — Comparison to /014 EWMA σ_t (prior labeling axis)

/014 swapped triple-barrier's σ_t source (NATR_21 → past-only EWMA 14d) →
PROMISING outcome (later integrated into baseline). That was a *parametric* change
within the triple-barrier framework — same path-dependent TP/SL primitive,
different σ_t scaling. iter-v1/035 is a *structural* change — replace
path-dependent TP-first-hit with regression-significance labels at the
selected horizon.

Reference point: /014's PROMISING outcome lends credibility that the labeling
axis is a productive class at v1; trend-scanning is the canonical next step
per LdP AFML Ch.5 §5.5.

### Section 1.6 — Prior on v3/017 trend-scanning attempt

v3/017 was a meta-labeling axis (NOT trend-scanning). The closest v3 attempt
is v3/072 (LightGbmStrategy label_mode plumbing), which established the API.
The v3 trend-scanning EDA at v3/105 produced PROMISING-FEATURE-MECHANICAL
verdict. At v3 (3-symbol universe BCH/LDO/TRX, different architecture, smaller
budget), the trend-scanning axis has not been catastrophic — it has been
positive-mechanical. No prior NEGATIVE evidence at v3 for trend-scanning labels
specifically. **No dead-paths-catalog entry for trend-scanning at v1.**

---

## Section 2 — Falsifiers

Five F-AXIS falsifiers. Verdict determined by F1 outcome; F2-F5 diagnostic.

### F-AXIS #1 — F1 OOS Sharpe Δ vs BASELINE_V1

**Anchor**: BASELINE_V1 = +0.6637 OOS monthly Sharpe (`v0.v1-baseline-corrected`).

| Band | OOS Δ | Verdict |
|---|---|---|
| Δ ≥ +0.50 | exceeds modal estimate | EXPLORATION-PROMISING-CLEAN |
| +0.20 ≤ Δ < +0.50 | PROMISING band | EXPLORATION-PROMISING |
| -0.15 ≤ Δ < +0.20 | within noise band (cycle-5 F1 cap ±0.15 — wider than feature-add cycle-5 ±0.10 because labeling change has larger basin variance) | EXPLORATION-INERT |
| -0.40 ≤ Δ < -0.15 | NEGATIVE no-effect | EXPLORATION-NEGATIVE |
| Δ < -0.40 | NEGATIVE catastrophic | EXPLORATION-NEGATIVE-CATASTROPHIC |

**Modal prior**: post-EDA QR estimate = PROMISING 30% / PROMISING-INERT 25% /
**INERT 25% MODAL** / NEG 15% / NEG-CAT 5%. Combined PROMISING 55% vs combined
NEG 20%. Mechanism: §1.4 LINK strong-cohort 35.6% divergence creates upside
optionality; HIGH-RISK basin-relocation creates downside variance.

### F-AXIS #2 — Trade-count band (HIGH-RISK adjusted)

Per `feedback_v3_axis_saturation_predictor.md` — must predict behavioral effect:

**Anchor**: BASELINE_V1 IS 621 / OOS 189.

HIGH-RISK label-mode change → expected trade-count band wider than feature-add
±15% because TS labels change the M1 decision boundary, which feeds into the
prediction threshold:

- **IS band**: [430, 800] (±30% from 621). Modal ~600 IS trades.
- **OOS band**: [120, 260] (±35% from 189). Modal ~190 OOS trades.
- **TECHNICAL-FAILURE-SILENT-FALLBACK trigger**: IS < 350 OR OOS < 100
  → BLOCK-PENDING-FIX (silent BASELINE catch-all dispatch OR feature parquet
  schema mismatch).

### F-AXIS #3 — Sign-agreement signal preservation (LOAD-BEARING)

EDA §1.2 measured TS↔TB sign-agreement = 64–76% across symbols at training-bar
level. If the runtime label generation diverges materially from EDA (e.g., due
to walk-forward window slicing, σ_t-induced bar dropout, or different candidate
selection), the axis isolation premise is violated.

**Verification (run at Phase 6 closeout)**:
For 1 OOS month per symbol, recompute trend-scanning labels and compare to
triple-barrier labels at the same candidate bars. Expected sign-agreement
~65-76% (±5pp tolerance band [60%, 81%]).

- < 50% sign-agreement: trend-scanning is producing nearly-inverse labels →
  TECHNICAL-FAILURE-LABEL-INVERSION (some code defect at the dispatch site).
- ∈ [60%, 81%]: PASS.
- > 90% sign-agreement: trend-scanning produces nearly-identical labels to TB
  → INERT-AT-LABEL-LEVEL → axis structural verdict regardless of F1 outcome.

### F-AXIS #4 — Per-symbol OOS Δ prediction

| Symbol | Predicted OOS Δ direction | Mechanism rationale |
|---|---|---|
| LINK | + (HIGHEST) | §1.4: 35.6% divergence on POSITIVE_EVERYWHERE cohort; expected ≥ +0.15 Sharpe |
| ETH (Pool A) | + | §1.4: 28.2% divergence; /019 gate baseline already favorable |
| LTC | + (mild) | §1.4: 31.5% divergence; /028 atr_sl=1.0 interaction TBD |
| DOT | mixed (sign uncertain) | §1.4: 33.7% divergence; mixed baseline; HIGH-RISK basin lottery |
| BTC (Pool A) | flat | §1.4: lowest divergence; least informative label change |

**Falsifier**: if 4/5 symbols turn NEGATIVE OOS Δ AND LINK NEGATIVE → mechanism
prediction REFUTED → reclassify regardless of F1.

### F-AXIS #5 — Loss-surface relocation magnitude (Cross-seed best-`learning_rate` Spearman)

Per `feedback_v1_iter032_axis_attribution_methodology.md` — HIGH-RISK label change
has high basin-relocation likelihood.

- Cross-seed best-`learning_rate` Spearman across 3 inner seeds vs BASELINE_V1
  median **> 0.50** → axis is label-clean-additive, basin-stable.
- **< 0.30** → loss-surface fundamentally relocated; F1 signal may be a basin
  lottery — at single-seed EXPLORATION, INFORMATIONAL ONLY. Multi-seed
  CONFIRMATION required to attribute F1 to labels vs basin.

### F-AXIS #6 — Selected-horizon distribution sanity (NEW for /035)

Pre-registered expectation from EDA §1.2: ~47-50% of training bars pick h*=21
(maximum), ~22-24% pick h=13, ~28% split h=5/8.

**Runtime verification** (at Phase 6 closeout): the dispatch banner emits the
observed horizon distribution. If the distribution materially deviates from
EDA (e.g., > 70% h=21 OR > 20% h=5), there is a degenerate basin selecting
extreme horizons unexpectedly → INFORMATIONAL ONLY at EXPLORATION budget.

---

## Section 2.5 — HIGH-RISK Axis Declaration

- **Declaration**: **HIGH-RISK**
- **Reason**: Label-mode change. Per `feedback_axis_saturation_predictor.md`
  HIGH-RISK is binding when an axis "changes Optuna's training-objective domain"
  — trend-scanning replaces the path-dependent triple-barrier label with a
  regression-significance label, changes per-row sample weights from TP/SL-magnitude
  (~8% modal) to forward-return magnitude (~2% modal), and shifts the LightGBM
  loss-surface basin. This is the canonical HIGH-RISK case.
- **Mitigation (v1 OPT-IN per cycle-5 standard)**:
  - F-AXIS #5 cross-seed Spearman diagnostic catches basin-relocation
    (informational at single-seed EXPLORATION; HARD GATE only at CONFIRMATION).
  - F-AXIS #3 sign-agreement runtime verification catches label-dispatch defects.
  - Pre-flight assert at the dispatch branch asserts `label_mode="trend_scanning"`
    is in fact propagated to every LightGbmStrategy instance.
- **HIGH-RISK budget choice**: SINGLE-SEED at v1 EXPLORATION (ENSEMBLE_SIZE=3,
  n_trials=18, outer seed=42). Per `feedback_axis_saturation_predictor.md` v1
  HIGH-RISK MAY OPT IN to multi-seed; iter-v1/035 OPTS OUT — single-seed
  acceptable, basin-lottery risk acknowledged. If F1 PROMISING fires, /036 OR
  /044 CONFIRMATION will validate multi-seed (per Critic /034 + LM Master
  default mandate for HIGH-RISK PROMISING outcomes). **If 3+ HIGH-RISK
  single-seed EXPLORATIONs produce >1σ negative deltas in a row going forward,
  the rule auto-upgrades per `feedback_axis_saturation_predictor.md`** — /034
  was NORMAL-RISK so this counter starts fresh; /035 is the FIRST cycle-5
  HIGH-RISK.

---

## Section 3 — Implementation Design + CLI Invocation

### Section 3.1 — Code changes (2 atomic edits + tests)

NO new feature module needed; NO new labeling module needed. Trend-scanning is
ALREADY implemented in `src/crypto_trade/strategies/ml/labeling.py:132-407` and
plumbed into `LightGbmStrategy` at `lgbm.py:176-177, 290-291, 656-657`. ONLY
plumbing additions in `run_baseline_v1.py`:

1. **EDIT** `run_baseline_v1.py`:
   - **Add CLI flag** `--label-mode` with choices `["triple_barrier", "fixed_horizon", "trend_scanning"]`
     and default `"triple_barrier"` near the existing `--sample-weight-mode` flag (after line 1811).
   - **Thread `label_mode` into `run_model()` signature** as kwarg
     `label_mode: str = "triple_barrier"` (and into the analogous `run_meta_model`
     for completeness, though /035 does NOT use meta-labeling).
   - **Pass `label_mode` to LightGbmStrategy()** at the existing strategy
     construction site (lgbm.py kwarg `label_mode=label_mode`; `trend_scan_grid`
     stays at default `(5, 8, 13, 21)`).
   - **Add `iteration_label == "v1-035"` dispatch branch** (~95 lines mirroring
     /034 basis branch at lines 3399-3480) that:
     - Asserts pre-flight: `assert label_mode_arg == "trend_scanning"`
     - Prints dispatch banner: `[iter-v1/035] TREND-SCANNING-LABEL ACTIVE: label_mode={label_mode}, trend_scan_grid={trend_scan_grid}, ENSEMBLE_SIZE={ensemble_size}, n_trials={n_trials}, seeds=1`
     - Dispatches 4 models (A/C/D/E) with IDENTICAL atr_tp/atr_sl/R-gate config to baseline
     - Threads `label_mode=label_mode_arg` to every `run_model()` call
   - **Add `"v1-035"`** to BASELINE catch-all exclusion tuple at line 3492
     (per `/030 LESSON` `feedback_v1_dispatch_baseline_catchall_exclusion.md`).

2. **CONFIRM** `src/crypto_trade/strategies/ml/lgbm.py` already supports the kwarg
   plumbing. No edit needed; verified at audit §1.0.

### Section 3.2 — Feature regeneration

**NONE.** Trend-scanning uses ONLY `close` from the master kline frame —
no new feature columns required. `V1_FEATURE_COLUMNS_PRUNED` (43 cols)
UNCHANGED. Existing feature parquets at `data/features/<SYM>_8h_features.parquet`
are reused as-is. **Feature regen cost = 0 min.**

### Section 3.3 — CLI invocation (Phase 6 backtest)

```bash
PYTHONUNBUFFERED=1 uv run python run_baseline_v1.py \
  --pruned-features \
  --iteration 35 \
  --exploration \
  --n-trials 18 \
  --ensemble-size 3 \
  --seeds 1 \
  --label-mode trend_scanning \
  > logs/iter_v1_035_backtest.log 2>&1
```

Flags:
- `--pruned-features` activates `V1_FEATURE_COLUMNS_PRUNED` (43 cols UNCHANGED).
- `--iteration 35` formats `iteration_label="v1-035"`, triggers dispatch branch.
- `--exploration` sets EXPLORATION default sizes (`V1_EXPLORATION_ENSEMBLE_SIZE=3`).
- `--n-trials 18` standardized v1 EXPLORATION trial budget.
- `--seeds 1` single outer seed=42 (canonical EXPLORATION).
- **`--label-mode trend_scanning`** triggers the trend-scanning labeling path
  in `LightGbmStrategy._train_for_month` → `label_trades(label_mode="trend_scanning")`.

### Section 3.4 — Symbols + universe + model config

| Item | Spec |
|---|---|
| Universe | V1_BASELINE_UNIVERSE (BTC/ETH/LINK/LTC/DOT) UNCHANGED |
| Models | A (BTC+ETH pool, atr_tp=2.9, atr_sl=1.45, R1=OFF, R3=ON), C (LINK, atr_tp=3.5, atr_sl=1.75, R1=ON, R3=ON), D (LTC, atr_tp=3.5, atr_sl=1.75, R1=ON, R3=ON), E (DOT, atr_tp=3.5, atr_sl=1.75, R1=ON, R2=ON, R3=ON) — IDENTICAL to baseline |
| Labels | **`trend_scanning` with grid (5, 8, 13, 21)** — CHANGED |
| `atr_tp` / `atr_sl` | UNCHANGED for execution-side TP/SL (different mechanism from labeling — execution barriers still ATR-driven; trend-scanning only changes M1 supervised target) |
| `sigma_source` | `natr` baseline default — `sigma_values` are inert in the trend-scanning labeling path (verified at `labeling.py:398-407` — `use_trend_scanning` short-circuits BEFORE sigma/atr branches) |
| Features | V1_FEATURE_COLUMNS_PRUNED 43 cols UNCHANGED |
| Sample weight | `abs_pnl` (baseline default; under TS this is `abs(fwd_return − fee)` per row) |
| Optuna bounds | `v1_pruned` (NOT axis016 — /035 is labeling-axis, NOT weight-mode change) |
| n_trials | 18 |
| Inner ensemble | 3 seeds (V1_EXPLORATION_ENSEMBLE_SIZE) |
| Outer seed | 42 (single) |
| Walk-forward | training_months=24, monthly retrain, embargo via walk_forward.py:113 fix |
| OOS_CUTOFF | 2025-03-24 (sacred) |
| Risk gates | R1/R2/R3 per-model baseline UNCHANGED |

### Section 3.5 — File changes (anticipated diff sizes)

| File | Change | Approx LOC |
|---|---|---|
| `run_baseline_v1.py` | CLI flag + 3 function kwargs + dispatch branch + exclusion-tuple add | +120 −2 |
| `tests/test_iteration_v1_035.py` | NEW | ~180 |

**Total change footprint**: 2 files, ~300 lines net.

### Section 3.6 — Wall-clock estimate (5-step scaling per `feedback_v1_label_rate_wall_clock_scaling.md`)

**Step 1 — Anchor precedent**: iter-v1/014 (EWMA σ_t labeling axis; closest
labeling-axis precedent at v1 standard EXPLORATION config).

- /014 was the σ_t-source labeling axis; /034 (most recent EXPLORATION) at
  comparable spec (n_trials=18, ENSEMBLE_SIZE=3, 5 syms, 43 cols) took
  ~50-65 min compute.

**Step 2 — Anchor label count**: BASELINE_V1 = 621 IS / 189 OOS trades over
53 walk-forward months × 5 syms. /034 produced trade counts very close to
baseline.

**Step 3 — /035 expected label count**:
- Trend-scanning produces ±1 labels for nearly every bar (no neutral floor
  → no zero labels — EDA §1.2 confirmed). LightGBM's positive-rate input is
  comparable to TB.
- BUT: weight distribution shift (TS 2.5% mean vs TB 8.5% mean) — the
  threshold-prediction → entry-decision boundary may relocate; expected
  trade-count band IS [430, 800] / OOS [120, 260] (±30-35%).
- Modal estimate: ~600 IS / ~190 OOS (close to baseline; trend-scanning is
  a label-replacement not a regime-filter).
- Label-rate factor for wall-clock estimation ≈ 1.0 (similar per-bar generation
  cost — OLS slope and t-stat math is constant-time per horizon, all 4 horizons
  evaluated each candidate; ~ 4×(matrix ops on h+1 prices); marginally cheaper
  than triple-barrier's barrier-scan loop with TP/SL detection at each forward
  bar.

**Step 4 — Scaling factors**:
- ENSEMBLE_SIZE = 3 inner / 3 inner anchor = 1.0
- n_trials = 18 / 18 anchor = 1.0
- Outer seed = 1 / 1 anchor = 1.0
- Feature count = 43 / 43 anchor = 1.0
- Label generation cost: ~1.0 (constant-time per bar, see Step 3)
- **Composite scaling factor ≈ 1.0×**

**Step 5 — Projection**: anchor ~55 min compute × 1.0 = **~55 min modal compute**.

**Total wall-clock**:
- Data fetch: **0 min** (kline already on disk).
- Feature regen: **0 min** (no new features).
- Backtest compute: ~55 min (modal).
- Report layer (DSR/PSR/etc): ~3 min.

**Modal total: ~60 min (1.0h).**
**Conservative band: 50-100 min (well under 1.8h target / 2h skill default cap).**

No kill-switch (per cycle-5 directive). Honest overrun acceptable.

### Section 3.7 — Phase 6 step-sequence

1. Wire `--label-mode` CLI flag + `run_model()` kwarg + LightGbmStrategy passthrough
2. Add `iteration_label == "v1-035"` dispatch branch + dispatch banner +
   pre-flight assert + exclusion-tuple ADD at line 3492
3. Run tests `uv run pytest tests/strategies/ml/test_trend_scanning_label_mode.py
   tests/test_iteration_v1_035.py -v` — ALL must pass
4. Launch backtest with the CLI in §3.3
5. After backtest: verify `[iter-v1/035] TREND-SCANNING-LABEL ACTIVE` banner
   printed; verify `iteration_label="v1-035"` lines in log present
6. Read `reports-v1/iteration_v1-035/comparison.csv` for F1 verdict

---

## Section 4 — Verdict Matrix

| F1 (OOS Δ) | F-AXIS #3 sign-agreement | F-AXIS #4 per-sym | F-AXIS #5 Spearman | F-AXIS #6 horizon | Verdict | Cycle-5 routing |
|---|---|---|---|---|---|---|
| ≥ +0.50 | ∈ [60%, 81%] | ≥3/5 syms +OOS (LINK +) | > 0.50 | h21 ∈ [40%, 60%] | PROMISING-CLEAN | bundle component for /044 CONFIRMATION |
| +0.20 to +0.50 | ∈ [60%, 81%] | ≥3/5 syms +OOS | > 0.30 | h21 ∈ [40%, 60%] | PROMISING | bundle component; cycle-5 advances /036 |
| +0.20 to +0.50 | ∈ [60%, 81%] | mixed | < 0.30 | varies | PROMISING-BASIN-RELOCATION-ARTIFACT | /036 multi-seed isolation OR /044 multi-seed CONFIRMATION |
| -0.15 to +0.20 | ∈ [60%, 81%] | mixed | varies | h21 ∈ [40%, 60%] | INERT | /036 NEW axis: cycle-5 menu axis #7 Sortino objective |
| -0.40 to -0.15 | varies | <3/5 +OOS | varies | varies | NEGATIVE-no-effect | trend-scanning CLOSED at v1 EXPLORATION; /036 NEW axis |
| < -0.40 | varies | <2/5 +OOS | varies | varies | NEGATIVE-CATASTROPHIC | trend-scanning CLOSED; cycle-5 routing audit |
| any | < 50% OR > 90% | n/a | n/a | n/a | TECHNICAL-FAILURE-LABEL-DISPATCH | BLOCK-PENDING-FIX |
| IS < 350 OR OOS < 100 | n/a | n/a | n/a | n/a | TECHNICAL-FAILURE-SILENT-FALLBACK | BLOCK-PENDING-FIX |

---

## Section 5 — Risk Mitigation

Per `feedback_risk_mitigation_design.md`: every merge-candidate iteration must
include a Risk Mitigation section. /035 is EXPLORATION not merge-candidate, but
discipline applies — Section 5 documents what risk semantics will look like IF
/035 graduates to bundle-inclusion at /044 CONFIRMATION.

| Risk Layer | Status | Rationale |
|---|---|---|
| **R1 Consecutive-SL cool-down** | UNCHANGED (active C/D/E, off A) | Independent of label-mode |
| **R2 Drawdown brake** (Model E) | UNCHANGED | Independent of label-mode |
| **R3 OOD Mahalanobis** | UNCHANGED (active all 4 models, cutoff 0.70, 16 features) | Feature set unchanged — same OOD subspace |
| **Trend-scanning HORIZON guard** (DESIGN-ONLY; not in /035) | DEFERRED to /044 | If /035 PROMISING with h21 dominance ≥ 60% (regime-significance heavy), consider per-trade horizon-conditional sizing at /044. NOT implemented in /035 — single-axis isolation. |

---

## Section 6 — Risk Management Table

| Risk | Likelihood | Severity | Mitigation |
|---|---|---|---|
| `--label-mode` flag not threaded through `run_model()` to LightGbmStrategy | LOW (audited §1.0; explicit thread) | HIGH (silent baseline labels would pass tests but produce baseline numbers) | Pre-flight assert in dispatch branch: `assert label_mode_arg == "trend_scanning"`; test `test_v1_035_label_mode_threaded` verifies kwarg reaches LightGbmStrategy instance. |
| BASELINE catch-all silent-fallback (no `v1-035` exclusion) | MEDIUM (recurring /030 + /033 + /034 defect class) | HIGH (entire backtest runs but reports BASELINE numbers) | Explicit exclusion add at line 3492 + test `test_baseline_catchall_excludes_v1_035`. |
| Look-ahead in trend-scanning forward window | NONE | NONE | Hard-causality test at `tests/strategies/ml/test_trend_scanning_label_mode.py::test_trend_scanning_hard_causality` proves forward-only access; embargo (`walk_forward.py:113`) unchanged since `max(grid)=21` matches existing 21-bar label horizon. |
| Single-seed basin lottery for HIGH-RISK label change | MEDIUM (acknowledged §2.5) | MEDIUM (F1 may be basin artifact at single-seed) | F-AXIS #5 cross-seed Spearman informational diagnostic; PROMISING outcome at /035 triggers multi-seed CONFIRMATION at /044 per HIGH-RISK rule. |
| `sample_weight_mode=abs_pnl` weight scale mismatch with TS PnL (~3-4× smaller) | LOW | LOW | LightGBM gradient is scale-invariant; only relative weight distribution matters. EDA §1.3 documented — informational. |
| Selected-horizon degenerate (>70% h=21 OR >20% h=5) | LOW (EDA §1.2 confirmed ~47-49% h=21 baseline) | LOW (informational only at single-seed) | F-AXIS #6 runtime check via dispatch banner; informational at EXPLORATION budget. |
| Forming-candle leak in trend-scanning forward window | LOW | HIGH | `_trend_scan_label` reads `close_arr[sym_idx[pos+1 .. pos+max_h]]` — bar `pos` is the entry and pos+1..pos+max_h are strictly-forward bars. fetcher.py filters forming candles at ingest time (`k.close_time < now_ms`). No additional guard needed. |

---

## Section 7 — Failure-mode Prediction

Per `feedback_v3_axis_saturation_predictor.md` — must predict behavioral effects.

**Predicted IS trade count change**: −5 to +20% from baseline 621 IS trades
(range [560, 740]). Trend-scanning is a label-replacement axis — Optuna's basin
selection may shift trade frequencies through threshold-prediction relocation,
but TS labels are bar-by-bar (every bar gets ±1), so the LightGBM regressor's
output distribution should remain stable.

**Predicted OOS trade count change**: ±25% from baseline 189 OOS trades (range
[140, 240]). Modal ~190.

**Predicted basin-shift (F-AXIS #5)**: cross-seed Spearman > 0.50 modal —
trend-scanning is a CLEAN label-swap (no feature change, no architecture change),
so the Optuna search-space remains identical. Some basin shift expected due to
weight-distribution change (§1.3), but not catastrophic.

**Predicted per-symbol OOS Δ direction**: LINK + (highest divergence, +
baseline class); ETH + (gate baseline favorable); LTC + mild (atr_sl=1.0
interaction TBD); DOT mixed; BTC flat. Per §1.4.

**Predicted sign-agreement at runtime (F-AXIS #3)**: 64-76% per EDA §1.2,
±5pp tolerance band [60%, 81%].

**FALSIFIER triggers**:
1. If observed sign-agreement is < 50% OR > 90% → TECHNICAL-FAILURE-LABEL-DISPATCH.
2. If IS trade count < 350 OR OOS < 100 → TECHNICAL-FAILURE-SILENT-FALLBACK.
3. If LINK OOS Sharpe Δ < +0.10 AND F1 OOS Δ ≤ 0 → mechanism REFUTED, reclassify
   regardless of F1 band (LINK was the prime cohort target).

---

## Section 8 — Verdict Cell Determination

Verdict determined by F-AXIS #1 (binary primary), with F2-F6 as diagnostic on mechanism:

```
IF sign-agreement F-AXIS #3 ∉ [50%, 90%]:
    → TECHNICAL-FAILURE-LABEL-DISPATCH
    → BLOCK-PENDING-FIX

ELSE IF OOS trades < 100 OR IS trades < 350:
    → TECHNICAL-FAILURE-SILENT-FALLBACK
    → BLOCK-PENDING-FIX

ELSE IF OOS Δ ≥ +0.20 AND IS Δ ≥ +0.10 AND OOS trades ∈ [120, 260] AND
        ≥3/5 syms +OOS Δ (LINK MUST BE +):
    → EXPLORATION-PROMISING (or PROMISING-CLEAN if Δ ≥ +0.50)
    → trend-scanning axis added to /044 CONFIRMATION bundle substrate
    → HIGH-RISK F-AXIS #5 Spearman < 0.30 → reclassify PROMISING-BASIN-RELOCATION-ARTIFACT

ELSE IF OOS Δ ∈ [-0.15, +0.20]:
    → EXPLORATION-INERT
    → cycle-5 advances to /036 NEW axis (Sortino objective)

ELSE IF OOS Δ < -0.15:
    → EXPLORATION-NEGATIVE (band per F1 table)
    → trend-scanning CLOSED for v1 cycle-5
```

---

## Section 9 — Library Stack

- `numpy` (already in deps): OLS / t-stat math at `_trend_scan_label`
- `pandas` (already in deps): master DataFrame ops
- `lightgbm` (already in deps): training (UNCHANGED)
- `optuna` (already in deps): hyperparameter search (UNCHANGED)
- `pyarrow` (already in deps): parquet round-trip (UNCHANGED)
- `scipy.stats` (already in deps): only for EDA (analysis script); NOT runtime
- **NO new deps required.**

---

## Section 10 — Symbol Exclusion + Reproducibility + Test Mandate

### Section 10.1 — Symbol exclusion

V1_BASELINE_UNIVERSE unchanged (BTC/ETH/LINK/LTC/DOT). No symbols added or removed.
V1_EXCLUDED_SYMBOLS unchanged.

### Section 10.2 — Reproducibility

- Single outer seed = 42 (matches baseline canonical seed)
- ENSEMBLE_SIZE = 3 inner seeds (42, 123, 456 — first 3 per
  `V1_EXPLORATION_ENSEMBLE_SIZE` ordering convention)
- Optuna sampler: TPE with random_state=outer_seed (deterministic per (cell, seed))
- Walk-forward: monthly retrain on training_months=24 window, embargo via
  `walk_forward.py:113` fix
- Trend-scanning is a deterministic transformation of forward close prices —
  identical input → identical labels (no random sampling in `_trend_scan_label`).

Two re-runs from a clean checkout must produce bit-identical `trades.csv` per
`feedback_deterministic_trade_match.md`. Smoke-tested at Phase 6 step 1.

### Section 10.3 — Test mandate (8+ tests per `/030 LESSON`)

**Mandatory** (8+ tests; 9 planned at `tests/test_iteration_v1_035.py`):

1. `test_v1_035_label_mode_cli_flag_parses` — `--label-mode trend_scanning` parses
   via argparse with allowed choices.
2. `test_v1_035_label_mode_default_unchanged` — `--label-mode` default is
   `"triple_barrier"`; runs WITHOUT `--label-mode` produce BIT-IDENTICAL master
   labels to historic runs (backward-compat).
3. `test_v1_035_run_model_threads_label_mode` — `run_model(label_mode="trend_scanning")`
   constructs a `LightGbmStrategy` instance whose `.label_mode == "trend_scanning"`
   (introspection via real strategy instance — per `/027 LESSON` real-attr access).
4. `test_v1_035_dispatch_banner_emitted` — runner with `iteration_label="v1-035"`
   and `--label-mode trend_scanning` prints `[iter-v1/035] TREND-SCANNING-LABEL ACTIVE`
   banner with label_mode, trend_scan_grid, ENSEMBLE_SIZE, n_trials, seeds=1.
5. `test_v1_035_dispatch_branch_pre_flight_assert` — runner with
   `iteration_label="v1-035"` AND `--label-mode triple_barrier` (mismatch)
   raises AssertionError BEFORE any backtest compute starts. Sample-instance
   test mandate per `/030 LESSON`.
6. `test_v1_035_in_baseline_catchall_exclusion` — line-3492 tuple contains
   `"v1-035"` (catch-all guard per `feedback_v1_dispatch_baseline_catchall_exclusion.md`).
7. `test_v1_035_dispatch_branch_exists` — runner code path `iteration_label == "v1-035"`
   is reachable (existence check via `inspect.getsource(run_baseline_v1)`).
8. `test_v1_035_trend_scan_grid_default` — when only `--label-mode trend_scanning`
   is passed, the LightGbmStrategy receives `trend_scan_grid=(5, 8, 13, 21)` default.
9. `test_v1_035_label_mode_does_not_leak_outside_dispatch` — confirms
   `--label-mode trend_scanning` propagates ONLY in the iter-v1/035 dispatch
   branch and the BASELINE catch-all branch does NOT pass the label_mode kwarg
   (defensive: BASELINE-mode runs should use baseline labels regardless of CLI flag).

ALL 9 tests must pass at Phase 6 before backtest launch.

Existing tests at `tests/strategies/ml/test_trend_scanning_label_mode.py`
(8 tests) MUST also continue to pass — covers the underlying labeling primitive
correctness (hard-causality, monotone, leakage, integration).

### Section 10.4 — Anti-cheating self-check

- IS-only window for ALL EDA + Phase 1-5 work. Confirmed via
  `OOS_CUTOFF_MS = 1742774400000` and `master[master["open_time"] < OOS_CUTOFF_MS]`
  in `analysis/iteration_v1-035/trend_scanning_eda.py:64`.
- OOS data NOT inspected during Phases 1-5.
- IS window NOT trimmed; full 2020-01 → 2025-03-23 used for EDA.
- `_trend_scan_label` reads only `close_arr[sym_idx[pos+1 .. pos+max_h]]` —
  strictly forward bars; no past-bar access in label computation.

### Section 10.5 — Phase 5.5 dispatch readiness

- Brief committed at HEAD.
- EDA script committed at `analysis/iteration_v1-035/trend_scanning_eda.py` +
  output CSV `trend_scanning_label_distribution.csv`.
- BASELINE catch-all exclusion tuple ADD planned (Phase 6 first commit).
- Test suite mandate documented (9 new + 8 existing trend-scanning tests).
- Wall-clock target ~1.0h modal (band 50-100 min) — well INSIDE skill default
  2h cap.
- HIGH-RISK declared with single-seed OPT-OUT per cycle-5 EXPLORATION standard;
  mitigation via F-AXIS #5 cross-seed Spearman informational diagnostic.

Ready for Phase 6 dispatch.

---

**END OF BRIEF**
