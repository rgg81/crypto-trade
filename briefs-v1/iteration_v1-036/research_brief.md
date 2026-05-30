# iter-v1/036 — Research Brief

**Iteration**: iter-v1/036
**Date**: 2026-05-30
**TYPE**: EXPLORATION
**Cycle**: 5, EXP 3 of 10
**Branch**: `iteration-v1/036`
**Author**: QR (autopilot)

---

## Section 0 — Hypothesis

**H1 (PRIMARY)**: /035's bimodal trend-scanning signal — LINK +75pp OOS lift and
DOT +112pp OOS lift at 5-cohort dispatch — SURVIVES per-cohort isolation. Running
ONLY Model C' (LINK trend-scanning specialist) + Model E (DOT trend-scanning
specialist) — skipping Model A pool, Model D LTC, Model G ETH — yields a
2-cohort bundle whose OOS monthly Sharpe ≥ +1.0 and whose per-symbol OOS Δ vs
baseline ≥ +50pp on BOTH LINK and DOT.

**H1a (mechanism)**: /035's bundle OOS Sharpe was −0.0119 (Δ −0.68 vs baseline
+0.6637) because BTC/ETH/LTC catastrophic regressions (−51 / −46 / +14 pp Δ
respectively, combined ≈ −130pp) offset LINK + DOT gains (+186pp combined). At
per-cohort isolation those large-cap losses are NOT in the portfolio — only
small-cap trend-persistent cohorts trade. The bimodal-signal hypothesis is
testable: if LINK + DOT individual specialists preserve the +75 / +112pp lift,
the 2-cohort bundle OOS Sharpe should land in [+0.8, +1.5] given /035's
per-cohort headline returns.

**H1b (falsifiable)**: If 2-cohort bundle OOS Sharpe Δ vs baseline < +0.20 OR
EITHER LINK or DOT per-symbol OOS lift < +50pp, the per-cohort-isolation +
trend-scanning composite is REFUTED at single-seed EXPLORATION budget and the
mechanism is reclassified as 5-cohort-confound (small-cap edge is contingent on
co-trading large-caps for diversification or threshold-calibration).

---

## Section 0.5 — Iteration Type, Cadence Position, Wall-Clock

- **TYPE**: EXPLORATION
- **Cadence**: cycle-5 EXPLORATION 3 of 10 (after /034 NEGATIVE basis_zscore_30
  + /035 NEGATIVE-CATASTROPHIC trend-scanning bundle WITH bimodal per-cohort
  PROMISING). Two EXPLORATIONs into cycle-5; pivot to /035's bimodal isolation
  per Critic /035 Path Forward §"/036 RECOMMENDATION".
- **NO kill-switches** (user directive 2026-05-30 + `docs/skill: no runtime
  kill-switches`).
- **Wall-clock target**: ~25 min modal compute + 3 min report = ~30 min total.
  Conservative band 20-45 min. Well under 2h skill default.

---

## Section 0.6 — Axis-Family Rotation (v1-only)

- **Axis family**: `per-cohort-specialization` (REPEAT but with trend-scanning
  labels; rotation REPEAT-JUSTIFIED per /035 bimodal isolation mandate).
- **Prior 5 EXPLORATION families** (from `briefs-v1/exploration_catalog.md`):
  - iter-v1/031: sample-weighting (PROMISING-BASIN-RELOCATION-ARTIFACT)
  - iter-v1/032: sample-weighting-isolation (PROMISING-AXIS-PARTIAL)
  - iter-v1/033: CONFIRMATION bundle (BLOCK-FINAL — `methodology`)
  - iter-v1/034: feature-family (EXPLORATION-NEGATIVE / LEARNED-NEG; basis_zscore_30)
  - iter-v1/035: labeling (EXPLORATION-NEGATIVE-CATASTROPHIC bundle + bimodal per-cohort)
- **Rotation status**: **REPEAT but JUSTIFIED**. `per-cohort-specialization` last
  occurred outside the prior-5 window (cycles 3-4, e.g. /018 LINK, /019 ETH,
  /020 BTC, /028/029 LTC/DOT specialists). The prior 5 disperse across 4
  families (sample-weighting/2, methodology/1, feature-family/1, labeling/1),
  so v1 monoculture trigger is NOT armed (Section 0.6 rule fires only when last
  5 are ALL same family). REPEAT JUSTIFIED because /036 is the load-bearing
  follow-up to /035's structural bimodal finding (LINK + DOT trend-scanning
  per-cohort gains exceeded +75 / +112pp respectively, the largest per-cohort
  OOS lifts in v1 cycle-5 history) — isolating the bimodal signal is the only
  way to test whether the per-cohort gains were genuine signal or 5-cohort
  confound.
- **One-sentence rationale**: Critic /035 Path Forward + LM Master /035 finding
  binds /036 to per-cohort isolation of LINK + DOT trend-scanning specialists;
  this is the canonical follow-up axis for a BIMODAL-EXPLORATION verdict and
  cannot be substituted by a different family without losing attribution to
  /035's discovery.

---

## Section 1 — IS-Only Evidence (cites /035 verbatim — no new EDA per prompt)

### Section 1.1 — /035 per-symbol OOS attribution (LOAD-BEARING)

From `briefs-v1/iteration_v1-035/review.md` (Critic FINAL, 2026-05-30):

| Symbol | /035 Trades | /035 WR | /035 Net PnL% | Baseline OOS PnL% | Δ vs baseline |
|---|---|---|---|---|---|
| **DOTUSDT** | 53 | **52.8%** | **+113.63%** | +1.96% | **+111.67pp** ⭐ |
| **LINKUSDT** | 52 | **55.8%** | **+108.91%** | +34.23% | **+74.68pp** ⭐ |
| BTCUSDT | 54 | 31.5% | -17.62% | +33.17% | -50.79pp |
| LTCUSDT | 48 | 31.2% | -32.76% | -47.25% | +14.49pp (slight) |
| ETHUSDT | 54 | 37.0% | -43.73% | +2.75% | -46.48pp |

LINK + DOT combined OOS PnL = +222.54% on 105 trades at 54.3% blended WR. BTC
+ ETH + LTC combined OOS PnL = -94.11% on 156 trades at 33.2% blended WR. The
two cohort groups are MIRRORED: small-cap (LINK/DOT) gain >+100% each at
>52% WR; large-cap (BTC/ETH) lose >40% each at <38% WR. LTC is in between
(slight gain vs baseline but absolute -32.76%).

### Section 1.2 — /035 bundle vs /036 expected bundle

Bundle-level OOS at /035 (5 cohorts):

| Metric | /035 Bundle | Baseline | Δ |
|---|---|---|---|
| OOS Sharpe | -0.0119 | +0.6637 | -0.68 (NEG-CAT) |
| OOS Trades | 261 | 189 | +72 |
| OOS WR | 41.8% | 40.2% | +1.6pp |
| OOS Max DD | 62.34% | 40.94% | +21.4pp worse |

/036 bundle (2 cohorts) projected from /035 per-symbol attribution:

| Metric | /035 LINK+DOT subset | /036 expected (per-cohort isolated) |
|---|---|---|
| OOS Trades | 105 | ~100-150 (each specialist independently re-optimized) |
| Combined OOS PnL | +222.54% | similar OR higher (Optuna no longer averaging across non-target large-caps) |
| Combined OOS WR | 54.3% | maintained or improved |
| OOS Sharpe (est) | n/a (subset) | **+0.8 to +1.5** (modal projection) |

### Section 1.3 — Prior on LINK + DOT cohort specialists

| Symbol | Prior specialist precedent | Outcome |
|---|---|---|
| LINK | iter-v1/018 LINK-only specialist (triple-barrier labels) | PROMISING-INERT-FAV — IS Sharpe +0.40 / OOS Sharpe +0.80 (Δ +0.80 vs baseline at TIME of /018 anchor) |
| DOT | iter-v1/029 DOT-only specialist + BTC-trend gate | TF-NEGATIVE (gate did not engage; cohort isolation alone insufficient at triple-barrier) |

Combining /018 (LINK specialist PROMISING with triple-barrier) + /035 (LINK
trend-scanning in pool +75pp OOS) suggests LINK has BOTH a per-cohort
specialization edge AND a trend-scanning label-mode preference — the /036
combination is a 2-mechanism stack on LINK.

For DOT: /029 specialist alone was negative (gate-dependent), but /035's
+112pp lift at trend-scanning-in-pool is the strongest DOT OOS signal in
v1 cycle-5 history. /036 isolates whether trend-scanning labels alone (no
gate) on DOT specialist produce that lift.

### Section 1.4 — Per-cohort specialist precedent at v1

7 prior per-cohort specialist EXPLORATIONs at v1 (cycles 3-4):
- /018 LINK pure → PROMISING-INERT-FAV (+0.80 OOS Δ at /018 anchor)
- /019 ETH + BTC-trend gate → INERT band
- /020 BTC pure → INERT
- /022 LTC + BTC-trend gate → INERT
- /028 LTC + atr_sl=1.0 → PROMISING (later bundled)
- /029 DOT + BTC-trend gate → TF-NEGATIVE
- /030-/032 (different families, not per-cohort)

Per-cohort specialization is a PRODUCTIVE family at v1 with 2 PROMISING outcomes
in 7 attempts. /036 is the FIRST per-cohort specialist with trend-scanning
labels and the FIRST 2-symbol bundle (vs all prior 1-symbol specialists).

---

## Section 1.5 — Prior Evidence Synthesis (PRIOR)

- /018 LINK PURE-isolation triple-barrier → PROMISING +0.80 OOS Δ (single-cohort)
- /035 trend-scanning labels at 5-cohort dispatch → bimodal: LINK +75pp / DOT
  +112pp lift, BTC/ETH/LTC -50/-46/+14pp drag, bundle OOS Sharpe -0.0119
  (NEG-CAT bundle, PROMISING per-cohort)
- /029 DOT + BTC-trend gate → TF-NEGATIVE (cohort isolation alone insufficient
  at triple-barrier on DOT)

Composite prior: combining /018's specialist mechanism with /035's
trend-scanning bimodal finding on the same 2 cohorts (LINK + DOT) is a
HIGH-RISK 2-mechanism stack — but each mechanism has independent positive
evidence at v1 specifically for these cohorts.

---

## Section 2 — Falsifiers

Five F-AXIS falsifiers. Verdict determined by F1; F2-F5 diagnostic.

### F-AXIS #1 — F1 OOS Sharpe Δ vs BASELINE_V1

**Anchor**: BASELINE_V1 = +0.6637 OOS monthly Sharpe (`v0.v1-baseline-corrected`).

| Band | OOS Δ | Verdict |
|---|---|---|
| Δ ≥ +0.50 | exceeds modal (e.g. bundle OOS Sharpe ≥ +1.16) | EXPLORATION-PROMISING-CLEAN |
| +0.20 ≤ Δ < +0.50 | PROMISING band (bundle OOS Sharpe +0.86 to +1.16) | EXPLORATION-PROMISING |
| -0.15 ≤ Δ < +0.20 | within noise band (per-cohort isolation halves trade pool so noise band wider than feature-add cycle-5 ±0.10) | EXPLORATION-INERT |
| -0.40 ≤ Δ < -0.15 | NEG no-effect | EXPLORATION-NEGATIVE |
| Δ < -0.40 | NEG catastrophic | EXPLORATION-NEGATIVE-CATASTROPHIC |

**Modal prior**: PROMISING-CLEAN 25% / PROMISING 35% / PROMISING-INERT 15% /
INERT 15% / NEG 7% / NEG-CAT 3%. Combined PROMISING 75% vs NEG 10%. This is
the highest PROMISING-modal prior of any v1 cycle-5 EXPLORATION — justified
by /035's direct attribution evidence (+74pp and +112pp per-cohort lifts).

### F-AXIS #2 — Trade-count band (2-cohort scaling adjusted)

**Anchor**: BASELINE_V1 IS 621 / OOS 189 (5 cohorts).
**/035 LINK+DOT subset**: 105 OOS trades (~52/cohort).

/036 bundle scales to 2/5 = 0.4× cohort coverage at the trade-frequency level,
but per-cohort Optuna re-optimization may shift entry thresholds:

- **IS band**: [200, 400] (modal ~280, scaling baseline IS 621 × 2/5 × [0.8, 1.6]
  to account for per-cohort threshold relocation)
- **OOS band**: [80, 160] (modal ~110, scaling baseline OOS 189 × 2/5 × [1.0, 2.1]
  account for /035 per-cohort 105 trades + Optuna re-optimization variance)
- **TECHNICAL-FAILURE-SILENT-FALLBACK trigger**: IS < 150 OR OOS < 60
  → BLOCK-PENDING-FIX (silent BASELINE catch-all dispatch OR feature parquet
  schema mismatch OR universe-set mismatch).

### F-AXIS #3 — Per-symbol OOS lift preservation (LOAD-BEARING)

PRIMARY falsifier. /035 measured LINK +74.68pp / DOT +111.67pp at 5-cohort
dispatch. /036 per-cohort isolation should PRESERVE or IMPROVE these lifts.

| Symbol | /035 OOS Δ | /036 Predicted OOS Δ | Falsifier |
|---|---|---|---|
| **LINK** | +74.68pp | ≥ +50pp (preserved) to +90pp (improved) | < +50pp → mechanism REFUTED |
| **DOT** | +111.67pp | ≥ +50pp (preserved) to +130pp (improved) | < +50pp → mechanism REFUTED |

If EITHER LINK or DOT per-symbol OOS lift < +50pp → axis REFUTED regardless
of F1 outcome. The mechanism prediction is that per-cohort isolation removes
pool-driven label/threshold confounds, so the predicted direction is
improvement (>+74/+112pp), not preservation only.

### F-AXIS #4 — Bundle OOS Sharpe target

Conditional on F-AXIS #3 PASS:

| Bundle OOS Sharpe | Verdict subtype |
|---|---|
| ≥ +1.30 | PROMISING-CLEAN-EXCEPTIONAL (better than projection top end) |
| +0.86 to +1.30 | PROMISING-CLEAN |
| +0.40 to +0.86 | PROMISING (within projection low half) |
| +0.30 to +0.40 | INERT-FAV (below projection but bundle PnL still positive) |
| < +0.30 | mechanism REFUTED (LINK + DOT lift did not translate to bundle Sharpe — bundle volatility/trade-spacing dominates) |

### F-AXIS #5 — Trade-roster overlap with /035 LINK + DOT subset

**Diagnostic** (informational at EXPLORATION budget):
- For each of LINK + DOT, compute Jaccard overlap between /036 OOS trade
  open_times and /035 LINK/DOT-only OOS subset.
- Expected overlap range [40%, 80%] (per-cohort Optuna re-optimization shifts
  some entries but signal-source remains TS).
- < 25% overlap → per-cohort isolation fundamentally relocated the loss
  surface (basin-relocation artifact); F1 outcome conditioned on basin lottery.
- > 90% overlap on BOTH → /036 produces bit-identical LINK+DOT subset of /035
  (no axis-specific re-optimization happened — TECHNICAL-FAILURE-SILENT-NO-OP).

### F-AXIS #6 — Dispatch banner verification

Runtime verification at Phase 6 closeout:
- `[iter-v1/036] PER-COHORT-TREND-SCANNING ACTIVE` banner emitted
- Banner specifies: `models=Model_C_LINK + Model_E_DOT`, `label_mode=trend_scanning`,
  `trend_scan_grid=(5, 8, 13, 21)`, `ENSEMBLE_SIZE=3`, `n_trials=18`, `seeds=1`,
  `features=43 V1_FEATURE_COLUMNS_PRUNED`.
- trades.csv contains ONLY LINKUSDT + DOTUSDT rows (per-cohort isolation
  enforced via universe filter + dispatch branch).

---

## Section 2.5 — HIGH-RISK Axis Declaration

- **Declaration**: **HIGH-RISK**
- **Reason**: Composes 2 mechanisms simultaneously — (1) per-cohort isolation
  (universe substitution from 5-cohort to 2-cohort, removing large-cap
  Optuna averaging) AND (2) trend-scanning label-mode (already HIGH-RISK at
  /035 per training-objective domain change). Per
  `feedback_axis_saturation_predictor.md` HIGH-RISK is binding when an axis
  "changes Optuna's training-objective domain" — both component mechanisms
  trigger this individually; composing them stacks the risk.
- **Mitigation (v1 OPT-IN per cycle-5 standard)**:
  - F-AXIS #3 LOAD-BEARING per-symbol OOS lift falsifier directly addresses
    the bimodal-isolation hypothesis at single-seed EXPLORATION budget.
  - F-AXIS #5 trade-roster overlap with /035 LINK+DOT subset catches
    basin-relocation lotteries.
  - Pre-flight asserts at dispatch branch:
    `assert set(symbols) == {"LINKUSDT", "DOTUSDT"}` and
    `assert label_mode_arg == "trend_scanning"`.
- **HIGH-RISK budget choice**: SINGLE-SEED at v1 EXPLORATION
  (ENSEMBLE_SIZE=3, n_trials=18, outer seed=42) — opt-OUT of multi-seed per
  cycle-5 standard. /035 was already HIGH-RISK single-seed; /036 maintains
  that footing to keep wall-clock under 30 min and produce a fast verdict
  on the bimodal-isolation hypothesis. If F1 PROMISING fires, /037+
  CONFIRMATION will validate multi-seed per HIGH-RISK rule.
- **HIGH-RISK SINGLE-SEED COUNTER**: /034 was NORMAL-RISK so counter reset.
  /035 = HIGH-RISK single-seed NEG-CAT bundle (bimodal subtype, not >1σ
  negative on the per-cohort prediction). /036 = HIGH-RISK single-seed.
  Counter at 1 of 3 → not yet at auto-upgrade threshold.

---

## Section 3 — Implementation Design + CLI Invocation

### Section 3.1 — Code changes (1 atomic edit + tests)

NO new feature module, NO new labeling module, NO new universe constant
needed. Trend-scanning is already implemented (per /035) and threaded through
`run_model()` → `LightGbmStrategy(label_mode=...)`. The new code path is a
single dispatch branch:

1. **EDIT** `run_baseline_v1.py`:
   - **Define** `V1_ITER036_UNIVERSE: tuple[str, ...] = ("LINKUSDT", "DOTUSDT")`
     near other `V1_ITERnnn_UNIVERSE` constants (alphabetical neighborhood of
     `V1_ITER029_UNIVERSE` and `V1_ITER035`-related items).
   - **Add `iteration_label == "v1-036"` dispatch branch** (~75 lines mirroring
     /035 dispatch at lines 3505-3592, but dispatching ONLY Model C' + Model E):
     - Pre-flight assert: `assert label_mode_arg == "trend_scanning"`
     - Pre-flight assert: `assert set(symbols) == set(V1_ITER036_UNIVERSE)`
     - Dispatch banner:
       `[iter-v1/036] PER-COHORT-TREND-SCANNING ACTIVE: models=Model_C_LINK + Model_E_DOT, label_mode={label_mode}, trend_scan_grid=(5,8,13,21), ENSEMBLE_SIZE={ensemble_size}, n_trials={n_trials}, seeds=1, features={len(active_feature_columns)} cols`
     - Dispatch Model C' (LINK only): `run_model("C' (LINK + R1)",
       ("LINKUSDT",), atr_tp=3.5, atr_sl=1.75, apply_r1=True, ...)`
     - Dispatch Model E (DOT only): `run_model("E (DOT + R1 + R2)",
       ("DOTUSDT",), atr_tp=3.5, atr_sl=1.75, apply_r1=True, apply_r2=True, ...)`
     - Threads `label_mode=label_mode_arg` to BOTH `run_model()` calls.
     - Combines results: `all_results = results_c036 + results_e036`,
       `_r5_model_results = [results_c036, results_e036]`,
       `_post_dispatch_fi_strategies = [("Model_C_LINK_trend_scan_specialist", _strat_c036), ("Model_E_DOT_trend_scan_specialist", _strat_e036)]`.
   - **Add `"v1-036"`** to BASELINE catch-all exclusion tuple at line ~3605
     (per `/030 LESSON` `feedback_v1_dispatch_baseline_catchall_exclusion.md`).

2. **CONFIRM** Trend-scanning + `label_mode` plumbing already in place per /035.
   No further edits to `lgbm.py` or `labeling.py`.

### Section 3.2 — Feature regeneration

**NONE.** V1_FEATURE_COLUMNS_PRUNED (43 cols) UNCHANGED. Trend-scanning uses
only `close` from kline frames. Existing feature parquets at
`data/features/<SYM>_8h_features.parquet` for LINK + DOT are reused as-is.
Feature regen cost = 0 min.

### Section 3.3 — CLI invocation (Phase 6 backtest)

```bash
PYTHONUNBUFFERED=1 uv run python run_baseline_v1.py \
  --pruned-features \
  --iteration 36 \
  --exploration \
  --n-trials 18 \
  --ensemble-size 3 \
  --seeds 1 \
  --label-mode trend_scanning \
  --symbols LINKUSDT,DOTUSDT \
  > logs/iter_v1_036_backtest.log 2>&1
```

Flags:
- `--pruned-features` activates `V1_FEATURE_COLUMNS_PRUNED` (43 cols UNCHANGED).
- `--iteration 36` formats `iteration_label="v1-036"`, triggers dispatch branch.
- `--exploration` sets EXPLORATION defaults (`V1_EXPLORATION_ENSEMBLE_SIZE=3`).
- `--n-trials 18` standardized v1 EXPLORATION trial budget.
- `--seeds 1` single outer seed=42.
- **`--label-mode trend_scanning`** triggers the trend-scanning labeling path.
- **`--symbols LINKUSDT,DOTUSDT`** restricts universe to V1_ITER036_UNIVERSE
  (2 cohorts); set-equality check in dispatch branch routes to /036 path.

### Section 3.4 — Symbols + models + config

| Item | Spec |
|---|---|
| Universe | V1_ITER036_UNIVERSE = (LINKUSDT, DOTUSDT) — NEW 2-symbol constant |
| Models | Model C' (LINK, atr_tp=3.5, atr_sl=1.75, R1=ON, R3=ON) + Model E (DOT, atr_tp=3.5, atr_sl=1.75, R1=ON, R2=ON, R3=ON). IDENTICAL to baseline Model C and Model E semantics. Model A pool, Model D LTC, Model G ETH SKIPPED. |
| Labels | `trend_scanning` with grid (5, 8, 13, 21) — SAME as /035 |
| `atr_tp` / `atr_sl` | baseline per-model values UNCHANGED (execution-side exits) |
| `sigma_source` | inert under trend-scanning (verified at `labeling.py:398-407`) |
| Features | V1_FEATURE_COLUMNS_PRUNED 43 cols UNCHANGED |
| Sample weight | `abs_pnl` (baseline default; under TS this is `abs(fwd_return − fee)` per row) |
| Optuna bounds | `v1_pruned` (NOT axis016) |
| n_trials | 18 |
| Inner ensemble | 3 seeds (V1_EXPLORATION_ENSEMBLE_SIZE) |
| Outer seed | 42 (single) |
| Walk-forward | training_months=24 (sacred), monthly retrain, embargo via walk_forward.py:113 fix |
| OOS_CUTOFF | 2025-03-24 (sacred) |
| Risk gates | R1 ON for C' + E; R2 ON for E only (baseline); R3 ON both (Mahalanobis cutoff 0.70, 16 features) |

### Section 3.5 — File changes (anticipated diff sizes)

| File | Change | Approx LOC |
|---|---|---|
| `run_baseline_v1.py` | V1_ITER036_UNIVERSE constant + dispatch branch + exclusion-tuple add | +85 −2 |
| `tests/test_iteration_v1_036.py` | NEW | ~210 |

Total: 2 files, ~290 lines net.

### Section 3.6 — Wall-clock estimate (5-step scaling)

**Step 1 — Anchor precedent**: /034 ~50 min compute at 5-cohort baseline standard
EXPLORATION (n_trials=18, ENSEMBLE_SIZE=3, 5 syms, 43 cols).

**Step 2 — Anchor label count**: BASELINE_V1 = 621 IS / 189 OOS trades, 53
walk-forward months × 5 syms.

**Step 3 — /036 expected label count**: 2/5 = 40% of cohort coverage. Per-cohort
Optuna re-optimization (single-cohort training per cell instead of
2-symbol-pool for Model A) does NOT change per-symbol candidate generation
rate. Expected IS ~250-350, OOS ~100-150.

**Step 4 — Scaling factors**:
- Cohort count: 2 / 5 = 0.4× compute (per-symbol Optuna is the dominant cost)
- ENSEMBLE_SIZE: 3 / 3 = 1.0×
- n_trials: 18 / 18 = 1.0×
- Outer seed: 1 / 1 = 1.0×
- Feature count: 43 / 43 = 1.0×
- Label generation cost: 1.0× (trend-scanning same constant-time per bar as /035)
- **Composite scaling factor: 0.4×**

**Step 5 — Projection**: 50 min × 0.4 = **20 min modal compute**.

**Total wall-clock**:
- Data fetch: 0 min (LINK + DOT klines on disk)
- Feature regen: 0 min (no new features)
- Backtest compute: ~20 min modal
- Report layer (DSR/PSR/etc): ~3 min

**Modal total: ~25 min (~0.4h).**
**Conservative band: 20-45 min — well under 2h skill default.**

No kill-switch (per cycle-5 directive). Honest overrun acceptable.

### Section 3.7 — Phase 6 step-sequence

1. Define `V1_ITER036_UNIVERSE: tuple[str, ...] = ("LINKUSDT", "DOTUSDT")`.
2. Add `iteration_label == "v1-036"` dispatch branch dispatching Model C' + E
   only, with `label_mode=label_mode_arg` threaded into both `run_model()` calls.
3. Add `"v1-036"` to BASELINE catch-all exclusion tuple.
4. Add `tests/test_iteration_v1_036.py` (10 tests; spec in §10.3).
5. Run `uv run pytest tests/test_iteration_v1_036.py
   tests/strategies/ml/test_trend_scanning_label_mode.py -v` — ALL must pass.
6. Launch backtest with CLI in §3.3.
7. After backtest: verify `[iter-v1/036] PER-COHORT-TREND-SCANNING ACTIVE`
   banner; verify trades.csv contains ONLY LINKUSDT + DOTUSDT rows; verify
   `iteration_label="v1-036"` lines in log present.
8. Read `reports-v1/iteration_v1-036/comparison.csv` for F1 verdict.

---

## Section 4 — Verdict Matrix

| F1 (Bundle OOS Δ) | F-AXIS #3 LINK lift | F-AXIS #3 DOT lift | F-AXIS #5 overlap | Verdict | Cycle-5 routing |
|---|---|---|---|---|---|
| ≥ +0.50 | ≥ +50pp | ≥ +50pp | [40%, 80%] | PROMISING-CLEAN | /037+ CONFIRMATION bundle: 2-specialist (LINK+DOT trend-scan) + baseline /A/D/G (BTC/ETH/LTC remain triple-barrier) — UNIFIED 5-cohort with MIXED labels |
| +0.20 to +0.50 | ≥ +50pp | ≥ +50pp | [40%, 80%] | PROMISING | bundle component for /037+ CONFIRMATION |
| +0.20 to +0.50 | ≥ +50pp | < +50pp | varies | PROMISING-LINK-ONLY | /037 = LINK trend-scan specialist ALONE; DOT axis CLOSED |
| +0.20 to +0.50 | < +50pp | ≥ +50pp | varies | PROMISING-DOT-ONLY | /037 = DOT trend-scan specialist ALONE; LINK axis CLOSED |
| -0.15 to +0.20 | < +50pp | < +50pp | varies | INERT (mechanism REFUTED — /035 lift was 5-cohort confound) | /037 NEW axis: cycle-5 menu axis #7 Sortino objective OR universe expansion |
| -0.40 to -0.15 | mixed | mixed | varies | NEGATIVE-no-effect | per-cohort + trend-scan composite CLOSED at v1 EXPLORATION |
| < -0.40 | < +20pp | < +20pp | varies | NEGATIVE-CATASTROPHIC | composite CLOSED; cycle-5 routing audit |
| any | n/a | n/a | < 25% overlap | PROMISING-BASIN-RELOCATION-ARTIFACT | F1 conditioned on basin lottery; /037 multi-seed isolation |
| any | n/a | n/a | > 90% on BOTH | TECHNICAL-FAILURE-SILENT-NO-OP | BLOCK-PENDING-FIX (no Optuna re-optimization happened) |
| IS < 150 OR OOS < 60 | n/a | n/a | n/a | TECHNICAL-FAILURE-SILENT-FALLBACK | BLOCK-PENDING-FIX |

---

## Section 5 — Risk Mitigation

| Risk Layer | Status | Rationale |
|---|---|---|
| **R1 Consecutive-SL cool-down** | ON for Model C' + Model E (baseline) | Independent of label-mode + universe |
| **R2 Drawdown brake** | ON for Model E only (baseline) | Independent of label-mode |
| **R3 OOD Mahalanobis** | ON for both (cutoff 0.70, 16 features) | Feature set unchanged — same OOD subspace |
| **Bundle-level concentration** | 2 cohorts → top-symbol PnL share by construction will exceed 30% (split between LINK and DOT) | EXPLORATION-LEVEL declaration — concentration cap is a MERGE-gate concern at /037 CONFIRMATION; /036 EXPLORATION acknowledges but does not enforce |
| **HIGH-RISK 2-mechanism stack** | acknowledged §2.5 | F-AXIS #3 per-symbol falsifier + F-AXIS #5 overlap diagnostic |

If /036 graduates to /037+ CONFIRMATION bundle, concentration risk must be
addressed by either (a) re-introducing the 3 large-cap cohorts under baseline
labels (mixed-label bundle), (b) opting for a 2-cohort merge with explicit
exception, or (c) /038+ universe expansion to 3-4 cohorts at per-cohort
specialization.

---

## Section 6 — Risk Management Table

| Risk | Likelihood | Severity | Mitigation |
|---|---|---|---|
| Dispatch branch routes to BASELINE catch-all instead of /036 path | LOW (audited at /035; same pattern + new exclusion add) | HIGH (silent baseline numbers in comparison.csv) | Explicit exclusion add at line ~3605 + test `test_v1_036_in_baseline_catchall_exclusion`. |
| `--symbols LINKUSDT,DOTUSDT` set-equality check fails (typo / case / extra symbols) | LOW | HIGH (dispatch fall-through) | Pre-flight assert `set(symbols) == {"LINKUSDT", "DOTUSDT"}` + test `test_v1_036_universe_set_equality`. |
| `--label-mode trend_scanning` not threaded to both `run_model()` calls | LOW (audited /035 plumbing) | HIGH (silent triple-barrier labels) | Pre-flight assert in dispatch branch + test `test_v1_036_label_mode_threaded_both_models` (real instance access per /027 lesson). |
| Single-seed basin lottery for HIGH-RISK 2-mechanism stack | MEDIUM (acknowledged §2.5) | MEDIUM (F1 may be basin artifact at single-seed) | F-AXIS #5 trade-roster overlap diagnostic; PROMISING outcome triggers multi-seed CONFIRMATION at /037. |
| /035 LINK+DOT lift was 5-cohort confound (mechanism falsifier prediction) | MEDIUM (no prior 2-cohort precedent at trend-scanning) | LOW-MED (would convert to INERT verdict, not catastrophic) | F-AXIS #3 LOAD-BEARING per-symbol lift falsifier catches confound-attribution. |
| Concentration cap pre-failure (2-cohort bundle will violate top-symbol ≤ 30%) | HIGH (by construction) | LOW at EXPLORATION (not a hard gate); HIGH at /037 CONFIRMATION | Documented §5; explicit deferral to /037 routing decision. |
| Forming-candle leak in trend-scanning forward window | LOW | HIGH | Same guards as /035: `_trend_scan_label` reads strictly-forward bars; `fetcher.py` drops forming candles at ingest. |

---

## Section 7 — Failure-mode Prediction

Per `feedback_v3_axis_saturation_predictor.md` — must predict behavioral effects.

**Predicted IS trade count**: range [200, 400], modal ~280 (baseline 5-cohort
IS 621 × 0.4 cohort-coverage × ~[0.8, 1.6] re-optimization factor).

**Predicted OOS trade count**: range [80, 160], modal ~110 (baseline 5-cohort
OOS 189 × 0.4 × ~[1.0, 2.1]; reference point /035 LINK+DOT subset 105 trades).

**Predicted per-symbol OOS Δ**: LINK ≥ +50pp (modal +75pp matching /035, with
upside +90pp from per-cohort re-optimization); DOT ≥ +50pp (modal +110pp
matching /035, with upside +130pp).

**Predicted bundle OOS Sharpe**: range [+0.5, +1.5], modal +1.0 (Δ +0.34
vs baseline +0.6637). Δ band drives F1 verdict.

**Predicted F-AXIS #5 overlap (LINK)**: 50-75% (per-cohort Optuna shifts ~25-50%
of /035's LINK trade roster).

**Predicted F-AXIS #5 overlap (DOT)**: 50-75% (same mechanism).

**FALSIFIER triggers**:
1. EITHER LINK or DOT per-symbol OOS lift < +50pp → mechanism REFUTED →
   reclassify regardless of F1 band.
2. IS < 150 OR OOS < 60 → TECHNICAL-FAILURE-SILENT-FALLBACK.
3. Overlap > 90% on BOTH cohorts → TECHNICAL-FAILURE-SILENT-NO-OP (no
   re-optimization happened — silent code defect).
4. Overlap < 25% on BOTH cohorts → PROMISING-BASIN-RELOCATION-ARTIFACT
   (informational at EXPLORATION; multi-seed needed for attribution).

**Mechanism failure scenario (PREDICTED FAILURE MODE):**
The most plausible failure mode is that /035's LINK+DOT lift was partly a
5-COHORT-CONFOUND artifact — i.e. in the 5-cohort setting, Optuna's
threshold-prediction calibration was BIASED by the noisy large-cap labels
(BTC+ETH+LTC under trend-scanning produced 24-36% sign-flips from triple-barrier
per /035 §1.2). That noise may have INADVERTENTLY produced more conservative
LINK/DOT thresholds that captured the trend-scanning edge cleanly. At
per-cohort isolation, Optuna re-calibrates on LINK alone (or DOT alone) and
may converge to AGGRESSIVE thresholds that over-trade and erode the edge.
This is the H1b falsifier: if per-symbol lift collapses to < +50pp on both,
the bimodal-signal was a 5-cohort confound, not a stand-alone per-cohort signal.

---

## Section 8 — Verdict Cell Determination

```
IF overlap > 90% on BOTH cohorts:
    → TECHNICAL-FAILURE-SILENT-NO-OP
    → BLOCK-PENDING-FIX

ELSE IF OOS trades < 60 OR IS trades < 150:
    → TECHNICAL-FAILURE-SILENT-FALLBACK
    → BLOCK-PENDING-FIX

ELSE IF overlap < 25% on BOTH cohorts:
    → PROMISING-BASIN-RELOCATION-ARTIFACT
    → /037 multi-seed isolation
    (F1 numbers reported INFORMATIONAL)

ELSE IF LINK OOS Δ ≥ +50pp AND DOT OOS Δ ≥ +50pp:
    IF F1 OOS Δ ≥ +0.50:
        → EXPLORATION-PROMISING-CLEAN
    ELIF F1 OOS Δ ≥ +0.20:
        → EXPLORATION-PROMISING
    ELSE:
        → EXPLORATION-INERT-FAV (per-symbol lift preserved but bundle Sharpe diluted)
    → /037 CONFIRMATION bundle substrate

ELSE IF LINK OOS Δ ≥ +50pp AND DOT OOS Δ < +50pp:
    → PROMISING-LINK-ONLY (DOT axis CLOSED for /037 routing)

ELSE IF DOT OOS Δ ≥ +50pp AND LINK OOS Δ < +50pp:
    → PROMISING-DOT-ONLY (LINK axis CLOSED for /037 routing)

ELSE:
    IF F1 OOS Δ ≥ -0.15:
        → EXPLORATION-INERT (5-cohort confound mechanism CONFIRMED)
    ELIF F1 OOS Δ ≥ -0.40:
        → EXPLORATION-NEGATIVE
    ELSE:
        → EXPLORATION-NEGATIVE-CATASTROPHIC
    → per-cohort + trend-scan composite CLOSED at v1 EXPLORATION budget
    → /037 routing: NEW family
```

---

## Section 9 — Library Stack

- `numpy` (already in deps): OLS / t-stat math at `_trend_scan_label` (reused)
- `pandas` (already in deps): master DataFrame ops
- `lightgbm` (already in deps): training UNCHANGED
- `optuna` (already in deps): hyperparameter search UNCHANGED
- `pyarrow` (already in deps): parquet round-trip UNCHANGED
- **NO new deps required.**

---

## Section 10 — Symbol Exclusion + Reproducibility + Test Mandate

### Section 10.1 — Symbol exclusion

V1_ITER036_UNIVERSE = (LINKUSDT, DOTUSDT). Subset of V1_BASELINE_UNIVERSE.
`assert_v1_universe()` accepts {LINKUSDT, DOTUSDT} because neither is in
V1_EXCLUDED_SYMBOLS.

### Section 10.2 — Reproducibility

- Single outer seed = 42 (baseline canonical)
- ENSEMBLE_SIZE = 3 inner seeds (42, 123, 456)
- Optuna sampler: TPE with random_state=outer_seed
- Walk-forward: monthly retrain, training_months=24 (sacred), embargo via
  walk_forward.py:113 fix
- Trend-scanning is deterministic transformation of forward closes (identical
  input → identical labels; no random sampling in `_trend_scan_label`).

Two re-runs from clean checkout must produce bit-identical `trades.csv`
per `feedback_deterministic_trade_match.md`. Smoke-tested at Phase 6 step 5.

### Section 10.3 — Test mandate (8+ tests per `/030 LESSON`)

10 mandatory tests at `tests/test_iteration_v1_036.py`:

1. `test_v1_036_universe_constant_exists` — `V1_ITER036_UNIVERSE` is defined as
   tuple containing exactly `("LINKUSDT", "DOTUSDT")`.
2. `test_v1_036_universe_subset_of_baseline` — V1_ITER036_UNIVERSE ⊂
   V1_BASELINE_UNIVERSE (both symbols are in V1_BASELINE_UNIVERSE).
3. `test_v1_036_dispatch_branch_exists` — runner code path
   `iteration_label == "v1-036"` is reachable (existence check via
   `inspect.getsource(run_baseline_v1)`).
4. `test_v1_036_dispatch_branch_pre_flight_label_mode_assert` — runner with
   `iteration_label="v1-036"` AND `--label-mode triple_barrier` raises
   AssertionError BEFORE compute. Sample-instance test per /030 LESSON.
5. `test_v1_036_dispatch_branch_pre_flight_universe_assert` — runner with
   `iteration_label="v1-036"` AND a different symbols set (e.g. {LINKUSDT
   only}) raises AssertionError BEFORE compute.
6. `test_v1_036_in_baseline_catchall_exclusion` — line-~3605 tuple contains
   `"v1-036"` (catch-all guard per /030 LESSON).
7. `test_v1_036_dispatch_banner_emitted` — runner with `iteration_label="v1-036"`,
   `--label-mode trend_scanning`, `--symbols LINKUSDT,DOTUSDT` prints
   `[iter-v1/036] PER-COHORT-TREND-SCANNING ACTIVE` banner with all required
   fields: models, label_mode, trend_scan_grid, ENSEMBLE_SIZE, n_trials, seeds=1,
   feature count.
8. `test_v1_036_label_mode_threaded_to_link_model` —
   `run_model(label_mode="trend_scanning", ..., symbols=("LINKUSDT",))`
   constructs a `LightGbmStrategy` whose `.label_mode == "trend_scanning"`
   (real-instance attr access per /027 LESSON).
9. `test_v1_036_label_mode_threaded_to_dot_model` — same for DOT specialist.
10. `test_v1_036_dispatches_only_link_and_dot_models` — runner with
    `iteration_label="v1-036"` produces exactly 2 model results
    (`Model_C_LINK_trend_scan_specialist` + `Model_E_DOT_trend_scan_specialist`);
    NO Model A pool, NO Model D LTC, NO Model G ETH dispatched.

ALL 10 tests must pass at Phase 6 before backtest launch.

Existing `tests/strategies/ml/test_trend_scanning_label_mode.py` (8 tests)
MUST continue to pass.

### Section 10.4 — Anti-cheating self-check

- No new EDA scripts per prompt directive (reuse /035 evidence).
- All numerical citations from /035 evidence are from
  `briefs-v1/iteration_v1-035/review.md` (Critic FINAL).
- OOS data NOT inspected during Phases 1-5 — /036 cites /035 OOS numbers
  which were measured at /035 Phase 7 evaluation.
- OOS_CUTOFF_MS = 1742774400000 SACRED — unchanged.
- training_months = 24 SACRED — unchanged.
- IS window NOT trimmed; full 2020-01 → 2025-03-23 used at backtest time.
- `_trend_scan_label` reads only `close_arr[sym_idx[pos+1 .. pos+max_h]]` —
  strictly forward bars (audited /035).

### Section 10.5 — Phase 5.5 dispatch readiness

- Brief committed at HEAD.
- NO new EDA scripts (per prompt directive — /035 evidence reused).
- V1_ITER036_UNIVERSE + dispatch branch + exclusion-tuple add planned
  (Phase 6 first commit).
- Test suite mandate documented (10 new tests + 8 existing trend-scanning
  tests must pass).
- Wall-clock target ~25 min modal (band 20-45 min) — well INSIDE skill
  default 2h cap.
- HIGH-RISK declared with single-seed OPT-OUT per cycle-5 EXPLORATION standard;
  mitigation via F-AXIS #3 LOAD-BEARING per-symbol lift falsifier + F-AXIS #5
  overlap diagnostic.

Ready for Phase 6 dispatch.

---

**END OF BRIEF**
