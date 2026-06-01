# iter-v1/038 — Research Brief

**Iteration**: iter-v1/038
**Date**: 2026-05-31
**TYPE**: EXPLORATION
**Cycle**: 5, EXP 5 of 10
**Branch**: `iteration-v1/038`
**Author**: QR (autopilot)

---

## Section 0.0 — Banner

iter-v1/038 EXPLORATION, **cycle-5 #5/10**.
**Axis varied**: per-symbol vol-target ceiling — pre-trade size scaling 1.0× → 0.5× when the symbol's 30d-annualized rolling realized volatility (`rv_30d_ann`, past-only log-return EWMA) exceeds its own 75th-percentile threshold over the symbol's full IS history.
**Axis family**: `risk-primitive` (1st risk-primitive EXPLORATION of cycle-5; family last used at iter-v1/010 R5 vol-floor across cycles 1-5).

---

## Section 0.5 — Iteration Type, Cadence Position, Wall-Clock

- **TYPE**: EXPLORATION (single-axis, single-seed=42, v1 EXPLORATION standard).
- **Cadence**: EXPLORATIONs since last CONFIRMATION (`/033`, BLOCK-FINAL methodology):
  - /034 feature-family (basis_zscore_30 NEG)
  - /035 labeling (trend-scanning, NEG-CAT bundle / PROMISING per-cohort bimodal)
  - /036 per-cohort-specialization (LINK+DOT trend-scan isolation)
  - /037 loss-function (Sortino objective; backtest in flight)
  - **/038 (current) = 5th EXPLORATION since /033** → 5 of 10 toward next CONFIRMATION
  → cadence allowed; 5 EXPLORATIONs remaining before /044 CONFIRMATION trigger per cycle-5 menu.
- **Wall-clock target**: ~50 min modal compute + ~3 min report = **~55 min total**. Conservative band 45-75 min. Anchored to /034 ~50 min at IDENTICAL config (5 cohorts, n_trials=18, ENSEMBLE_SIZE=3, single-seed, 43 features, no feature regen). Ceiling-gate evaluation is a constant-time per-trade arithmetic check at entry-time → negligible compute. Well INSIDE 2h soft cap (60% margin).

---

## Section 0.6 — Axis-Family Rotation (v1-only)

- **Axis family declared**: `risk-primitive`.
- **Prior 5 EXPLORATION families** (from `briefs-v1/exploration_catalog.md` + briefs Section 0.6 reads since catalog last appended at /031):
  - iter-v1/032: `sample-weighting` (frozen-HP isolation of /031 PROMISING)
  - iter-v1/033: `confirmation-bundle` (CONFIRMATION; NOT counted toward 5-EXPLORATION rotation window)
  - iter-v1/034: `feature-family` (basis_zscore_30 NEG)
  - iter-v1/035: `labeling` (trend-scanning)
  - iter-v1/036: `per-cohort-specialization` (LINK+DOT trend-scan)
  - iter-v1/037: `loss-function` (Sortino objective)
- **Prior 5 EXPLORATIONs (excluding CONFIRMATION /033)**: `sample-weighting`, `feature-family`, `labeling`, `per-cohort-specialization`, `loss-function`.
- **Rotation status**: **VALID**. `risk-primitive` does NOT appear in the prior 5 EXPLORATIONs. Last `risk-primitive` axis in v1 was /010 (R5 vol-target floor — PROMISING-then-bundled). No monoculture defiance.
- **One-sentence rationale**: After 4 signal-source / labeling / loss-function axes since /033 produced NEG/NEG-CAT or BLOCK verdicts (/034 NEG, /035 NEG-CAT bundle, /037 TBD), pivoting to a `risk-primitive` axis is a different-family probe that tests whether existing edge can be protected from drawdown-prone high-vol regimes — orthogonal to the signal-discovery cycle that has so far been unproductive.

---

## Section 1 — Hypothesis (3 sentences)

**H1 (PRIMARY)**: For at least 2 of 5 baseline cohorts (BTC + LTC per EDA §4 asymmetry table), high-vol regime entries (above each symbol's own 75th-percentile rolling 30d RV) exhibit negative-skewed PnL — mean net PnL deteriorates from -0.247% (below ceiling) to -0.768% (above) for BTC and from +0.100% to -0.662% for LTC — so applying a 0.5× pre-trade size scaling above the per-symbol p75 threshold reduces tail downside on those symbols without sacrificing positive-expectancy mid-vol regime trades.

**H1a (mechanism, model-retrained)**: Under retraining-with-sizing (Optuna sees the post-ceiling weighted PnL during HP search), the model relocates the loss-surface basin to a configuration that internalizes the ceiling — high-vol BTC/LTC entries shrink in importance, mid-vol regime captures expand, and per-cohort Optuna may compensate the IS-roster-linear -26% portfolio PnL prediction by re-weighting threshold semantics toward lower-vol regimes that the linear EDA approximation cannot capture.

**H1b (FALSIFIABLE)**: If the F1 OOS Sharpe Δ vs BASELINE_V1 (+0.6637) lands inside the EDA-predicted **modal band [-0.45, -0.15] (NEG-CLEAN)** with LINK and DOT showing the predicted per-symbol PnL DROP > 25pp each (matching EDA §3's -32.94pp LINK and -6.24pp DOT linear predictions), the symmetric per-symbol vol-ceiling mechanism is REFUTED at v1 cycle-5 — model retraining did NOT compensate the asymmetry inversion for LINK/DOT, and the axis is CLOSED for /044 bundling (no symmetric ceiling will appear in future bundles).

---

## Section 2 — F-AXIS #1 Falsifier: OOS Sharpe Δ vs BASELINE_V1

**Anchor**: BASELINE_V1 = +0.6637 OOS monthly Sharpe (`v0.v1-baseline-corrected`).

**EDA-derived modal prior**: linear IS-roster approximation predicts -25.63pp portfolio weighted PnL Δ (EDA §3). With 5 cohorts and ~189 OOS trades, treating this as proportional to Sharpe pressure (PnL Δ → Sharpe Δ ≈ ~-0.30 to -0.40 under unchanged trade count + ratio), the EDA points strongly toward NEG-CLEAN modal. Model retraining can move the result UP (Optuna compensates) or DOWN (Optuna overfits to ceiling-clipped IS basin and worsens OOS), so the modal band is asymmetric.

| Band | OOS Δ vs +0.6637 | Verdict | Modal prior |
|---|---|---|---|
| Δ ≥ +0.50 | OOS Sharpe ≥ +1.16 | EXPLORATION-PROMISING-CLEAN (CAT) | **5%** |
| +0.20 ≤ Δ < +0.50 | OOS Sharpe +0.86 to +1.16 | EXPLORATION-PROMISING-CLEAN | **10%** |
| -0.15 ≤ Δ < +0.20 | OOS Sharpe +0.51 to +0.86 | EXPLORATION-INERT (axis no-op) | **20%** |
| **-0.45 ≤ Δ < -0.15** | **OOS Sharpe +0.21 to +0.51** | **EXPLORATION-NEGATIVE-CLEAN** | **40% (MODAL)** |
| Δ < -0.45 | OOS Sharpe < +0.21 | EXPLORATION-NEGATIVE-CATASTROPHIC | **25%** |

**Modal verdict prior: NEG-CLEAN 40% + NEG-CAT 25% = combined NEG 65%** vs combined PROMISING 15%. This is the FIRST v1 cycle-5 EXPLORATION where the EDA prior is NEG-DOMINANT; the experiment is run anyway under THE PRIME DIRECTIVE because the EDA is the IS-roster-linear approximation — it CANNOT predict whether model retraining at Optuna step 0 will compensate the ceiling clip via mid-vol regime over-weighting. The experiment resolves whether the EDA's linear prediction generalizes to retrained-model OOS. Either outcome is informative: a NEG result CLOSES symmetric ceilings; an INERT/PROMISING result reveals model-retraining compensation as a load-bearing mechanism unmodelled by IS-roster linear extrapolation.

---

## Section 2.5 — HIGH-RISK Axis Declaration

- **Declaration**: **NORMAL-RISK**.
- **Reason**: The per-symbol vol-target ceiling is a **stateless pre-trade sizing gate** evaluated DOWNSTREAM of model prediction. It does NOT alter Optuna's training-objective domain — Optuna still optimizes the Sharpe (or Sortino, depending on /037's threading) on the IS PnL distribution. The mechanism multiplies position_size by 0.5× when entry-time `rv_30d_ann > per_symbol_threshold`, but the Optuna search space, the LightGBM training labels, the feature columns, and the loss surface are bit-identical to baseline. This is structurally analogous to /010 R5 (vol-target floor) and the existing R1 cool-down — both `risk-primitive` family members that did NOT trigger HIGH-RISK declarations in their respective EXPLORATIONs.
- **Mitigation**: **SINGLE-SEED OK**. Per cycle-5 EXPLORATION standard (n_trials=18, ENSEMBLE_SIZE=3, single outer seed=42). No multi-seed validation required at EXPLORATION budget. If F1 fires PROMISING (modal prior 15%) → /044 CONFIRMATION will multi-seed validate. If F1 fires NEG (modal prior 65%) → axis CLOSED; no further compute.
- **HIGH-RISK SINGLE-SEED COUNTER**: /034 NORMAL / /035 HIGH-RISK single-seed (NEG-CAT bundle) / /036 HIGH-RISK single-seed / /037 NORMAL → /038 NORMAL. Counter at 2 of 3 HIGH-RISK single-seed; /038 does NOT increment. Not at auto-upgrade threshold.

---

## Section 3 — Implementation Design + CLI Invocation

### Section 3.1 — LM Master recommendations

**LM Master `lgbm_advisor.md` was NOT authored at Phase 4.5 for /038** (file absent on disk at brief-authoring time). Per v1 skill, when LM Master output is unavailable, the brief proceeds with the QR's own design and documents the absence. If LM Master input arrives after brief commit, Phase 5.5 gate reviews any deltas before Phase 6 dispatch.

Implicit LM Master adjudications the QR has anticipated and addressed:

1. **Threshold percentile selection** (anticipated: "why 75th not 80th or 85th?") — **ADOPT** EDA §2 finding: p85 gives 1-8% above-ceiling shares (sample collapse on DOT/LTC); p75 gives 3-19% shares (enough to move the needle). p75 IS the natural operating point.
2. **Sizing fraction selection** (anticipated: "why 0.5× not 0.25× or full-kill?") — **ADOPT** EDA §3 linear prediction at 0.5× to keep the mechanism continuous (not a binary kill). 0.5× preserves a non-zero contribution from high-vol trades while halving the position notional, which matches the "tail clip" semantics of the hypothesis better than a binary kill (which would also eliminate LINK D8 and DOT D8 entirely — see EDA §5).
3. **Per-symbol vs portfolio-level ceiling** (anticipated: "why per-symbol not portfolio?") — **ADOPT** EDA §1 finding that BTC sits 40% lower than LINK/DOT on absolute RV scale — a single global ceiling is structurally mis-calibrated. Per-symbol p75 is the correct unit of analysis.
4. **Threshold computation source** (anticipated: "IS-only p75 or rolling p75?") — **MODIFY**: use FULL-IS-history p75 (the symbol's p75 of `rv_30d_ann` over all bars with close_time < OOS_CUTOFF=2025-03-24) computed ONCE at run start. NOT a rolling window. Rationale: rolling p75 introduces concept-drift coupling between the threshold and the regime; full-IS p75 is a STATIC threshold per symbol, which makes the OOS test a clean falsification (does the IS-derived p75 generalize?). Look-ahead-safe: IS-only history is by definition closed at OOS_CUTOFF.
5. **Lookback for `rv_30d_ann`** (anticipated: "30d or 14d or 90d?") — **ADOPT** EDA's 30d (90 bars at 8h). 14d is too noisy (sub-funding-cycle); 90d washes out regime transitions. 30d sits at the funding-period × ~30 boundary and matches the EDA design.

### Section 3.2 — Code changes (atomic edits + tests)

NEW code path is a single dispatch branch + a single sizing-gate primitive:

1. **NEW MODULE** `src/crypto_trade/risk/vol_ceiling.py` (~80 LOC):
   - `compute_per_symbol_rv_threshold(klines_panel, symbol, lookback_bars=90, percentile=75, oos_cutoff_ms=...) -> float`: returns the p75 of `rv_30d_ann` over IS-only bars. Past-only, log-return-based, computed ONCE per symbol per backtest run.
   - `apply_vol_ceiling(symbol, entry_time_ms, current_rv, threshold, scale_factor=0.5) -> float`: returns 0.5 if `current_rv > threshold`, else 1.0. STATELESS.
   - `compute_rv_30d_ann_at_bar(closes_arr, idx) -> float`: 30d annualized log-return std computed strictly from `closes_arr[:idx+1]` (past-only).

2. **EDIT** `run_baseline_v1.py`:
   - Add CLI flags:
     - `--vol-ceiling-mode {none, per_symbol, portfolio}` (default `none` → BIT-IDENTICAL baseline path).
     - `--vol-ceiling-pct INT` (default 75, range [50, 95]).
     - `--vol-ceiling-scale FLOAT` (default 0.5, range [0.1, 1.0]).
   - Add `iteration_label == "v1-038"` dispatch branch (~70 LOC, mirroring /037 dispatch pattern at lines 3720+):
     - Pre-flight asserts:
       - `assert vol_ceiling_mode_arg == "per_symbol"`
       - `assert vol_ceiling_pct_arg == 75`
       - `assert vol_ceiling_scale_arg == 0.5`
       - `assert set(symbols) == set(V1_BASELINE_UNIVERSE)` (5-cohort baseline universe)
     - Dispatch banner:
       `[iter-v1/038] VOL-CEILING ACTIVE: mode=per_symbol, pct=75, scale=0.5, symbols=BTC+ETH+LINK+LTC+DOT, lookback_bars=90, ENSEMBLE_SIZE={ensemble_size}, n_trials={n_trials}, seeds=1, features={len(active_feature_columns)} cols`
     - Computes per-symbol thresholds at run start (5 thresholds, logged).
     - Threads `vol_ceiling_config` into each `run_model()` call as a sizing-side hook evaluated at trade entry.
   - **Add `"v1-038"` to BASELINE catch-all exclusion tuple** at line ~3605 (per /030 LESSON `feedback_v1_dispatch_baseline_catchall_exclusion.md`).

3. **EDIT** `src/crypto_trade/backtest.py` (or `backtest_models.py`):
   - Thread `vol_ceiling_config` through `BacktestConfig`. At entry-time within the order-creation loop, evaluate `apply_vol_ceiling(...)`; multiply `position_size` (or equivalently `weight_factor` in the trade row) by the returned scale.
   - Persistence: write the applied scale + threshold + current_rv to `trades.csv` for forensic auditing (new optional columns `vol_ceiling_scale_applied`, `entry_rv_30d_ann`, `vol_ceiling_threshold`).

4. **TESTS** `tests/test_iteration_v1_038.py` (10 tests):
   1. `test_v1_038_compute_per_symbol_rv_threshold_btc_p75` — BTC p75 ≈ 0.6758 ± 0.01 (matches EDA §2 table).
   2. `test_v1_038_compute_per_symbol_rv_threshold_link_p75` — LINK p75 ≈ 1.2058 ± 0.01.
   3. `test_v1_038_apply_vol_ceiling_returns_half_above_threshold` — above-threshold scenario returns 0.5.
   4. `test_v1_038_apply_vol_ceiling_returns_one_below_threshold` — below-threshold scenario returns 1.0.
   5. `test_v1_038_rv_30d_ann_past_only` — uses only `closes[:idx+1]`; passing forward closes does not change output (look-ahead audit).
   6. `test_v1_038_dispatch_branch_pre_flight_mode_assert` — runner with `iteration_label="v1-038"` AND `--vol-ceiling-mode none` raises AssertionError BEFORE compute.
   7. `test_v1_038_dispatch_branch_pre_flight_pct_assert` — runner with `--vol-ceiling-pct 50` raises AssertionError.
   8. `test_v1_038_in_baseline_catchall_exclusion` — line ~3605 tuple contains `"v1-038"`.
   9. `test_v1_038_dispatch_banner_emitted` — banner with all required fields prints to stdout.
   10. `test_v1_038_per_symbol_threshold_logged_at_run_start` — 5 threshold log lines (one per cohort).

### Section 3.3 — CLI invocation (Phase 6 backtest)

```bash
PYTHONUNBUFFERED=1 uv run python run_baseline_v1.py \
  --pruned-features \
  --iteration 38 \
  --exploration \
  --n-trials 18 \
  --ensemble-size 3 \
  --seeds 1 \
  --vol-ceiling-mode per_symbol \
  --vol-ceiling-pct 75 \
  --vol-ceiling-scale 0.5 \
  > logs/iter_v1_038_backtest.log 2>&1
```

### Section 3.4 — File changes (anticipated diff sizes)

| File | Change | Approx LOC |
|---|---|---|
| `src/crypto_trade/risk/vol_ceiling.py` | NEW module | ~80 |
| `run_baseline_v1.py` | CLI flags + dispatch branch + exclusion-tuple add | +90 -2 |
| `src/crypto_trade/backtest.py` | thread `vol_ceiling_config` into entry-time sizing | +30 -1 |
| `tests/test_iteration_v1_038.py` | NEW (10 tests) | ~220 |

Total: 4 files, ~420 LOC net.

---

## Section 4 — F-AXIS Mechanism Falsifiers (#2-#5)

### F-AXIS #2 — Importance/wiring check

**Diagnostic** (not a binary pass/fail): the dispatch banner prints `vol-ceiling-fire-rate-IS` and `vol-ceiling-fire-rate-OOS` (% of IS / OOS trades where the ceiling fired at 0.5×) per symbol AND portfolio.

- **Predicted IS fire-rate (matching EDA §2)**:
  - BTC 15.9% / ETH 19.3% / LINK 10.3% / LTC 8.9% / DOT 3.2% → portfolio ~12.1%
- **Predicted OOS fire-rate**: similar order of magnitude (5-25% per symbol), modal portfolio ~10-15%.
- **WIRING-FAILURE-SILENT-FALLBACK trigger**: portfolio IS fire-rate < 1% (gate did not engage; silent baseline path) OR portfolio IS fire-rate > 50% (gate engaged on majority — threshold mis-applied; possible look-ahead in `compute_per_symbol_rv_threshold` evaluating future data) → BLOCK-PENDING-FIX.

### F-AXIS #3 — Per-symbol PnL Δ LOAD-BEARING

**PRIMARY mechanism falsifier**. EDA §3 predicts per-symbol PnL Δ (% portfolio weighted PnL) at IS-roster-linear approximation. Model retraining can MOVE these; the falsifier brackets:

| Symbol | EDA prediction (PnL Δ pct, linear) | Falsifier range (model-retrained) | Trigger |
|---|---|---|---|
| BTC  | **+6.16** (favorable) | [+0, +15] retrained | Outside → unmodelled retrain dynamic |
| ETH  | **+4.81** (favorable) | [-5, +15] retrained | n/a (ETH is mildly inverted but small share) |
| LTC  | **+3.58** (favorable) | [-5, +15] retrained | n/a |
| LINK | **-32.94** (HOSTILE — inverse asymmetry) | [-40, +5] retrained | If LINK PnL Δ > +10 (model fully compensates) → INERT-MODEL-COMPENSATION verdict subtype |
| DOT  | **-6.24** (HOSTILE — sample collapse + D8) | [-15, +5] retrained | If DOT PnL Δ > +10 → INERT-MODEL-COMPENSATION |

**LOAD-BEARING**: if BOTH LINK and DOT per-symbol PnL Δ land WORSE than the EDA's linear prediction (i.e. LINK < -32.94pp and DOT < -6.24pp), the symmetric per-symbol ceiling is REFUTED with diagnostic clarity — model retraining made the inversion WORSE not better — and the axis is CLOSED for /044 bundling regardless of F1 numeric.

### F-AXIS #4 — Bundle OOS trade-count hard floor

**Anchor**: BASELINE_V1 OOS 189 trades.

- **Expected OOS trades**: 170-210 (ceiling-gate is sizing-only, does NOT change trade-count semantics — model retraining at Optuna step 0 may shift entry-thresholds slightly; expect ±10% from baseline).
- **HARD FLOOR**: OOS < 130 total trades → TECHNICAL-FAILURE-SILENT-FALLBACK (sizing gate broke entry selection — possible bug; BLOCK-PENDING-FIX).
- **HARD FLOOR**: per-symbol OOS trades < 10 on any symbol → trade-rate sub-floor failure per `feedback_trade_rate_floor.md` (≥10/month OOS) — BLOCK-PENDING-FIX at /038 EXPLORATION; would also block any /044 CONFIRMATION inclusion.

### F-AXIS #5 — Wall-clock plausibility

- **Modal estimate**: ~50 min compute + ~3 min report = **~53 min total**.
- **Conservative band**: 45-75 min.
- **Anchor**: /034 ran 50 min at IDENTICAL config (5 cohorts, 43 features, n_trials=18, ENSEMBLE_SIZE=3, single-seed). Ceiling evaluation is constant-time per trade entry (~ns); negligible vs LightGBM training (~minutes per cell).
- **WIRING-FAILURE-WALL-CLOCK trigger**: total wall-clock > 90 min → silent recompute defect (possible `compute_per_symbol_rv_threshold` recomputing per-bar instead of once-per-run) → halt + investigate; BLOCK-PENDING-FIX after kill.

---

## Section 5 — Configuration Summary

| Item | Spec |
|---|---|
| Universe | V1_BASELINE_UNIVERSE = (BTCUSDT, ETHUSDT, LINKUSDT, LTCUSDT, DOTUSDT) — 5 cohorts |
| Models | Baseline 4-model topology UNCHANGED: A (BTC+ETH pool), C (LINK), D (LTC), E (DOT) |
| Labels | Triple-barrier σ_t EWMA 14d, atr_tp/atr_sl per-model baseline UNCHANGED |
| Features | V1_FEATURE_COLUMNS_PRUNED 43 cols UNCHANGED |
| Sample weight | `abs_pnl` baseline default |
| Optuna bounds | `v1_pruned` baseline |
| Optuna objective | `sharpe` baseline (NOT sortino; /037's axis is orthogonal) |
| n_trials | 18 |
| Inner ensemble | 3 seeds (V1_EXPLORATION_ENSEMBLE_SIZE) |
| Outer seed | 42 (single) |
| Walk-forward | training_months=24 (sacred), monthly retrain, embargo `walk_forward.py:113` fix |
| OOS_CUTOFF | 2025-03-24 (sacred) |
| Risk gates baseline | R1 ON per-model, R2 ON for E only, R3 ON all (Mahalanobis 0.70, 16 features) |
| **NEW: vol-ceiling-mode** | **`per_symbol`** |
| **NEW: vol-ceiling-pct** | **75** |
| **NEW: vol-ceiling-scale** | **0.5** |
| **NEW: vol-ceiling-lookback-bars** | **90 (= 30d at 8h)** |
| **NEW: vol-ceiling-threshold-window** | **IS-only full history (close_time < OOS_CUTOFF)** |

CLI:
```
--exploration --iteration 38 --n-trials 18 --ensemble-size 3 --seeds 1 \
  --pruned-features --vol-ceiling-mode per_symbol --vol-ceiling-pct 75 --vol-ceiling-scale 0.5
```

---

## Section 6 — Wall-Clock Estimate

**Step 1 — Anchor**: /034 ran 50 min compute at v1 EXPLORATION standard (5 cohorts, n_trials=18, ENSEMBLE_SIZE=3, single-seed=42, 43 features, no feature regen).

**Step 2 — Scaling factors**:
- Cohort count: 5/5 = 1.0×
- ENSEMBLE_SIZE: 3/3 = 1.0×
- n_trials: 18/18 = 1.0×
- Outer seeds: 1/1 = 1.0×
- Feature count: 43/43 = 1.0×
- Feature regen: 0 min (no new features)
- Per-symbol threshold compute: 5 symbols × O(panel_size) once = ~5 sec total (negligible)
- Per-trade ceiling evaluation: O(1) per entry = ~ns per trade (negligible)
- **Composite scaling factor: 1.0×**

**Step 3 — Projection**: 50 min × 1.0 = **50 min modal compute**.

**Total wall-clock**:
- Data fetch: 0 min (klines on disk)
- Feature regen: 0 min
- Backtest compute: ~50 min modal
- Report layer (DSR/PSR/comparison.csv): ~3 min

**Modal total: ~53 min (~0.9h).**
**Conservative band: 45-75 min — well INSIDE 2h soft cap (60% margin).**

No kill-switch armed (per cycle-5 directive — honest overrun acceptable).

---

## Section 7 — Expected Report Shape

`reports-v1/iteration_v1-038/` should contain:

1. **`comparison.csv`** — IS/OOS Sharpe, Sortino, MaxDD, trade count, win rate, net PnL per model (A/C/D/E) and portfolio total.
2. **`per_symbol.csv`** — IS/OOS breakdown per cohort (BTC/ETH/LINK/LTC/DOT) including:
   - Per-cohort OOS net PnL, trade count, WR
   - **NEW**: per-cohort `vol_ceiling_fire_rate_IS`, `vol_ceiling_fire_rate_OOS` (% trades where 0.5× applied)
   - **NEW**: per-cohort `vol_ceiling_threshold_p75` (the computed p75 from EDA §2)
3. **`trades.csv`** — full IS+OOS trade roster with NEW columns `vol_ceiling_scale_applied`, `entry_rv_30d_ann`, `vol_ceiling_threshold`.
4. **`dsr.json`** — DSR/PSR/PBO at single-seed EXPLORATION granularity (INFORMATIONAL per `feedback_v3_dsr_mode_artifact.md`).
5. **Dispatch banner in log**: 1 banner line + 5 per-symbol threshold log lines.

**Headline numbers Critic + QR Phase 7 inspect first**:
- Portfolio IS Sharpe (anchored to BASELINE_V1 IS +0.2829)
- Portfolio OOS Sharpe (anchored to BASELINE_V1 OOS +0.6637)
- Per-symbol OOS PnL Δ for LINK and DOT (F-AXIS #3 LOAD-BEARING)
- Portfolio fire-rate (F-AXIS #2 wiring)

---

## Section 8 — Path Forward Predictions

### If PROMISING (Δ ≥ +0.20 OOS Sharpe; modal 15%):
**Unexpected** — would mean model retraining absorbed the ceiling and reallocated trades to lower-vol regimes that captured more edge than the IS-roster-linear prediction modeled. /044 CONFIRMATION bundles per-symbol vol-ceiling as a strictly-accretive risk-primitive component (multi-seed validation mandatory for risk-primitive bundle gates). Per `feedback_v3_promising_mechanical_subtype.md`, sub-classify as PROMISING-MECHANICAL if trade-roster overlap with baseline > 60% (axis acts as drag-removal at retraining rather than novel signal).

### If INERT (-0.15 ≤ Δ < +0.20; modal 20%):
Axis NO-OP or near-no-op. Model retraining largely cancelled the sizing gate. Document under axis-NULL category; do NOT bundle in /044. Next cycle-5 EXPLORATION = menu axis #9 (Cross-symbol correlation gate) OR menu axis #10 (Per-trade Kelly sizing).

### If NEG-CLEAN (-0.45 ≤ Δ < -0.15; modal 40%):
Axis CLOSED for symmetric per-symbol ceilings. Reason: EDA's linear prediction generalized to OOS (LINK/DOT inversion confirmed empirically). Next axis from cycle-5 menu in order:
- **/039**: cycle-5 menu axis #6 — trend-scanning labels (HIGH-RISK; already attempted at /035 NEG-CAT bundle but per-cohort isolated at /036 — if /036 PROMISES, /039 may be skipped in favor of /044 bundling; if /036 NEG, /039 is the next axis-family pivot)
- **/040**: cycle-5 menu axis #7 — Sortino objective (already attempted at /037)
- **/041**: re-route to drawdown-conditional ceiling per EDA §7 Option 3 (cap applied only if symbol is BOTH high-RV AND in 3-trade losing streak) — orthogonal to symmetric ceiling
- **/042**: cycle-5 menu axis #9 — Cross-symbol correlation gate

### If NEG-CAT (Δ < -0.45; modal 25%):
Axis CLOSED definitively. Risk-primitive family bypassed for /044 bundling. Cycle-5 routing audit: 4 of 5 cycle-5 EXPLORATIONs have produced NEG/NEG-CAT (/034 NEG, /035 NEG-CAT, /037 TBD, /038 NEG-CAT) — if /037 also NEG, declare cycle-5 saturation and pivot to STRUCTURAL break-scope axis for /039 per `feedback_v3_structural_over_knob_exploration.md` (e.g. new bar interval, new universe, new data class — NOT another knob within current scope).

---

## Section 9 — Behavioral-Effect Predictor (per feedback_v3_axis_saturation_predictor)

**Predicted IS trades AFFECTED by the ceiling** (i.e. trades where 0.5× scaling applies at entry):

| Symbol | Above-ceiling IS trades (EDA §2) | Predicted IS Δ trade-count (vs baseline) |
|---|---:|---:|
| BTC  | **18** of 113 (15.9%) | 0 trades dropped (sizing only); 18 trades shrunk |
| ETH  | **28** of 145 (19.3%) | 0 dropped; 28 shrunk |
| LTC  | **11** of 123 (8.9%)  | 0 dropped; 11 shrunk |
| LINK | **15** of 146 (10.3%) | 0 dropped; 15 shrunk |
| DOT  | **3** of 93  (3.2%)   | 0 dropped; 3 shrunk |
| **TOTAL** | **75** of 620 (12.1%) | **0 dropped; 75 IS trades shrunk to 0.5×** |

**Predicted OOS trades affected**: scaling 12.1% to OOS 189 trades = **~23 OOS trades shrunk to 0.5×** (range 15-35 depending on regime mix in OOS window).

**Falsifier coupled to this prediction (F-AXIS #2 WIRING)**:
- IS fire-rate count < 50 trades → silent fallback (gate did not engage at expected rate; possible threshold mis-applied OR `--vol-ceiling-mode` defaulted to `none` silently).
- IS fire-rate count > 200 trades → threshold leak (per-symbol thresholds computed too low; possible look-ahead into OOS data via thresholds containing OOS samples).
- **Modal**: IS 60-90 trades fired (target 75); OOS 15-35 trades fired (target 23).

**Direct mechanical PnL prediction (EDA §3, linear)**: portfolio IS weighted PnL Δ = **-25.63pp** (-26% destruction). Model retraining can compensate this UP or worsen it DOWN. The OOS test resolves which.

**Saturation check**: if portfolio fire-rate is materially lower than predicted (< 5% portfolio) AND F1 outcome is INERT, the axis is BOTH inert AND saturated — declare cycle-5 menu axis #8 EXHAUSTED at v1 EXPLORATION single-seed budget and prefer drawdown-conditional ceiling (EDA §7 Option 3) for any future risk-primitive exploration.

---

**END OF BRIEF**
