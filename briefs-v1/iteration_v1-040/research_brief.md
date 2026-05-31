# iter-v1/040 — Research Brief

**Iteration**: iter-v1/040
**Date**: 2026-05-31
**TYPE**: EXPLORATION
**Cycle**: 5, EXP 7 of 10
**Branch**: `iteration-v1/040`
**Author**: QR (autopilot)

---

## Section 0.0 — Banner

`iter-v1/040 EXPLORATION cycle-5 #7/10; axis = feature-engineering composed
feature (DROP basis_zscore_30 + ADD regime_momentum_signed_5d); family =
feature-family (4th cycle-5 use after /034 NEG-CLEAN feature-add); LM Master
endorsement = /038 §6 Rec 1 HIGH CONFIDENCE; v3-PROVEN precedent (v3/025
PROMISING + v3/028 CONFIRMATION-MERGE); NORMAL-RISK single-seed=42 at v1
EXPLORATION standard.`

---

## Section 0.5 — Iteration Type, Cadence Position, Wall-Clock

- **TYPE**: EXPLORATION
- **Cadence**: cycle-5 EXPLORATION **7 of 10**. Prior 6 cycle-5 EXPLORATIONs:
  /034 NEG-CLEAN (feature-family basis_zscore_30) → /035 NEG-CAT-bundle bimodal
  (labeling trend-scanning) → /036 PROMISING-CLEAN LINK+DOT trend-scan
  (per-cohort-specialization) → /037 PROMISING-CLEAN Sortino
  (loss-function) → /038 NEG-CATASTROPHIC vol-ceiling (risk-primitive) →
  /039 NEG (drawdown brake, EDA-rejected risk-primitive). Three cycle-5
  EXPLORATIONs remain after /040 (slots #8/9/10) before /044 CONFIRMATION
  bundling.
- **NO kill-switches** (user directive 2026-05-30 + cycle-5 discipline).
- **Wall-clock target**: ~1.0h modal at v1 EXPLORATION standard (n_trials=18,
  ENSEMBLE_SIZE=3, single-seed=42). Cap NOT enforced via kill — overrun
  acceptable per cycle-5 directive.

---

## Section 0.6 — Axis-Family Rotation (v1-only)

- **Axis family**: `feature-family` (4th cycle-5 use; first instance was /034
  basis_zscore_30 NEG-CLEAN — DIFFERENT MECHANISM: /034 added a NEW
  data-source signal from a NEW data feed (perp-spot basis), /040 REPLACES an
  INERT incumbent with a COMPOSED FEATURE algebraically derived from
  in-stack primitives (no new data) per LM Master /038 §6 Rec 1).
- **Prior 5 EXPLORATION families** (from `briefs-v1/exploration_catalog.md`):
  - iter-v1/034: feature-family (NEG-CLEAN — basis_zscore_30 INERT)
  - iter-v1/035: labeling (NEG-CAT-bundle bimodal — trend-scanning)
  - iter-v1/036: per-cohort-specialization (PROMISING-CLEAN — LINK+DOT
    trend-scan substrate)
  - iter-v1/037: loss-function (PROMISING-CLEAN — Sortino)
  - iter-v1/038: risk-primitive (NEG-CATASTROPHIC — per-symbol vol ceiling)
- **Rotation status**: **REPEAT but MECHANISM-JUSTIFIED**. Prior 5 disperse
  across 5 DISTINCT families (feature-family/1 + labeling/1 +
  per-cohort-specialization/1 + loss-function/1 + risk-primitive/1) — v1
  monoculture trigger is NOT armed (Section 0.6 rule fires only when last 5
  are all SAME family). The `feature-family` repeat from /034 is justified
  on MECHANISM grounds: /034 tested an EXOGENOUS new-data-source signal
  (perp-spot basis from a separate data feed); /040 tests an ENDOGENOUS
  COMPOSED-FROM-INCUMBENTS signal (ret_5d × sign(hurst_100 − 0.5),
  algebraically derived from in-stack primitives). These are categorically
  different mechanism classes; LM Master /038 §6 Rec 1 HIGH CONFIDENCE
  endorsed this specific axis on the structural grounds that v1's 43-col
  pruned stack has held identical rank-1-5 importance for 5 iterations —
  feature-space is saturated at the OFF-THE-SHELF primitive level and the
  v3-proven composed-feature category has NEVER been touched in v1.
- **One-sentence rationale**: LM Master /038 §6 Rec 1 binds /040 to a
  feature-engineering composed-feature axis on the explicit grounds that v3's
  /025 PROMISING + /028 CONFIRMATION-MERGE precedent identifies trees at
  depth 3-5 as STRUCTURALLY UNABLE to compose `ret_5d × sign(hurst_100 − 0.5)`
  natively, and v1's saturated OFF-THE-SHELF primitive stack makes composed
  features the highest-prior NEW signal source remaining.

---

## Section 1 — IS-Only Evidence (from EDA + LM Master)

### Section 1.1 — basis_zscore_30 INERT-3-consec confirmation (DROP)

From `eda_findings.md` T1: basis_zscore_30 importance rank across /034, /037,
/038 (15 measurements across 5 cohorts × 3 iters):

| iter | Model_A_pool | Model_C_LINK | Model_D_LTC | Model_E_DOT | portfolio |
|---|---|---|---|---|---|
| /034 | 25 | 29 | 32 | 26 | 27 |
| /037 | 25 | 29 | 31 | 25 | 27 |
| /038 | 25 | 29 | 32 | 26 | 27 |

Mean rank **27.67 / 44**; min rank **25**; max rank **32**. **All 15
observations rank ≥ 25** (bottom half of 44-feature set). Rank stability
across 3 iters is itself diagnostic — STRUCTURALLY low-importance NOT
"lottery-INERT". Per `feedback_v3_inert_features_at_higher_budget.md`
doctrine — INERT-3-consec triggers DROP mandate.

### Section 1.2 — regime_momentum_signed_5d EDA evidence (ADD)

Composed feature: `regime_momentum_signed_5d = ret_5d × sign(hurst_100 − 0.5)`
where `ret_5d = log(close_t) − log(close_{t−15})` at 8h cadence (15 bars =
120h = 5 calendar days) and `hurst_100` is the rolling 100-bar R/S Hurst
exponent (v3-IDENTICAL implementation, BYTE-FOR-BYTE copy from
`src/crypto_trade/features_v3/regime_v3.py:34-75`).

**Stationarity (ADF, IS-only close_time < 2025-03-24):**
| symbol | ADF p-value | stationary @5% |
|---|---|---|
| BTCUSDT | 2.0e-15 | ✓ |
| ETHUSDT | 6.1e-17 | ✓ |
| LINKUSDT | 5.2e-18 | ✓ |
| LTCUSDT | 8.6e-19 | ✓ |
| DOTUSDT | 1.5e-13 | ✓ |

All 5 symbols pass ADF at p << 0.001 → stationary. Satisfies v1 stationarity
discipline.

### Section 1.3 — IMPORTANT FINDING: sign(hurst_100 − 0.5) is +1 ALMOST ALWAYS

| symbol | pct_trending (hurst > 0.5) | pct_meanrev (hurst < 0.5) |
|---|---|---|
| ALL 5 v1 symbols | 100.0% | 0.0% |

The v3 R/S Hurst estimator at 100-bar window on 8h crypto data produces values
centered ~1.00 with std ~0.05. The sign-flip mechanism is therefore **NEVER
engaged in practice** at this window/cadence — `regime_momentum_signed_5d` is
mechanically equivalent to **ret_5d (15-bar log return)** across the full IS
sample. This matches v3's parquet (BCH/LDO/TRX hurst_100 mean 0.998-1.008,
all-positive sign); v3 /025 PROMISING-CLEAN and /028 CONFIRMATION-MERGE
happened DESPITE this — implying v3's lift came from `ret_5d` (15-bar) being
a NEW longer-horizon momentum primitive not from regime conditioning.

**Hypothesis re-framing**: /040 is NOT adding regime-aware feature; it is
adding a **5-DAY (15-bar) log return primitive** that v1 currently lacks
(v1's longest momentum primitive is `stat_log_return_5` at 5-bar = 40h).

### Section 1.4 — IC matrix (composed feature vs incumbents)

|symbol  | ic_stat_log_return_5 | ic_mom_rsi_14 | ic_trend_aroon_osc_50 | ic_ret_5d_15bar_PRIMITIVE | ic_hurst_100_PRIMITIVE |
|---|---|---|---|---|---|
|BTCUSDT |0.588 | 0.815 |0.396 |1.000 |0.026|
|ETHUSDT |0.596 | 0.813 |0.427 |1.000 |−0.012|
|LINKUSDT|0.577 | 0.820 |0.397 |1.000 |0.005|
|LTCUSDT |0.567 | 0.814 |0.374 |1.000 |0.004|
|DOTUSDT |0.582 | 0.798 |0.402 |1.000 |0.063|

- |IC| vs ret_5d_15bar primitive = **1.000 EXACT** (mechanical: sign is +1
  everywhere; composed feature ≡ ret_5d).
- |IC| vs hurst_100 primitive = **≤ 0.063** (regime primitive contributes
  ~zero variance).
- |IC| vs `mom_rsi_14`: **0.80-0.82** (HIGH — momentum-family overlap).
- |IC| vs `stat_log_return_5` (5-bar log return; ALREADY IN V1 PRUNED SET):
  **0.57-0.60** (moderate; horizon mismatch 40h vs 120h).

**Composed-feature IC carve-out applies** per
`feedback_v3_engineered_feature_pivot.md`: strict |IC| < 0.50 against
incumbents FAILS (RSI overlap 0.80; stat_log_return_5 overlap 0.58); binding
falsifier is **importance ≥ 30 in ≥ 2 of 5 cohorts**.

### Section 1.5 — Predicted per-cohort importance rank

v3 precedent: regime_momentum_signed_5d ranked 51% top-importance (Model A
in v3) at /025 vs 22-25% off-the-shelf NEW features. v1 prediction (5
cohorts):

| cohort | predicted rank | rationale |
|---|---|---|
| Model_A_pool (BTC+ETH) | 5-12 | strong competition (RSI rank 1-3 + ADX + MACD + multi-horizon stat_returns); distinctive 120h horizon |
| Model_C_LINK | 8-15 | LINK rewards momentum (RSI rank 2, MACD rank 4 at /037-/038) |
| Model_D_LTC | 10-18 | LTC weaker momentum response (RSI rank 5 at /038); riskier |
| Model_E_DOT | 8-15 | DOT trades momentum strongly in 2022 IS bear regime |
| portfolio | 6-10 | averaged |

**Expected: importance ≥ 30 in 3-4 of 5 cohorts** → passes composed-feature
gate. **Risk**: |IC|=0.80 with RSI may steal colsample picks; v1's
momentum-rich stack is harder competition than v3's 14-feature TOP_N.

---

## Section 2 — Falsifiers

Five F-AXIS falsifiers. F1 primary; F2 LOAD-BEARING importance rank gate;
F3-F5 diagnostic.

### F-AXIS #1 — F1 OOS Sharpe Δ vs BASELINE_V1

**Anchor**: BASELINE_V1 = +0.6637 OOS monthly Sharpe (`v0.v1-baseline-corrected`).

| Band | OOS Δ | Verdict |
|---|---|---|
| Δ ≥ +0.50 | exceeds modal | EXPLORATION-PROMISING-CLEAN-EXCEPTIONAL |
| +0.20 ≤ Δ < +0.50 | PROMISING band | EXPLORATION-PROMISING-CLEAN |
| +0.05 ≤ Δ < +0.20 | PROMISING-INERT-FAV | EXPLORATION-PROMISING-INERT-FAV |
| -0.10 ≤ Δ < +0.05 | within noise band | EXPLORATION-INERT |
| -0.30 ≤ Δ < -0.10 | NEG no-effect | EXPLORATION-NEGATIVE |
| Δ < -0.30 | NEG catastrophic | EXPLORATION-NEGATIVE-CATASTROPHIC |

**Modal prior (QR-adjusted from LM Master HIGH-confidence priors per EDA T5)**:
- PROMISING-CLEAN: 30% (slight down from LM 35% — v1 feature set richer in
  momentum than v3's 14-feature TOP_N; competition harder)
- PROMISING-INERT-FAV: **35% MODAL** (up from LM 30% — high |IC|=0.80 with
  RSI suggests learned-but-redundant is modal outcome)
- INERT: 20% (unchanged)
- NEGATIVE: 15% (unchanged — same regime-decay risk)

**Modal band**: PROMISING-INERT-FAV (35%) > PROMISING-CLEAN (30%) > INERT
(20%) > NEGATIVE (15%). Combined PROMISING 65% > combined NEG 15%; net
expected E[Δ] ≈ +0.12.

### F-AXIS #2 — Composed-feature importance rank (LOAD-BEARING)

PRIMARY mechanism falsifier per `feedback_v3_engineered_feature_pivot.md` IC
carve-out: composed features mechanically correlate with primitives (|IC|=1.0
vs ret_5d) so |IC| gate is INAPPROPRIATE; binding gate is split-count
importance.

**LOAD-BEARING falsifier wording**:
- **PASS**: regime_momentum_signed_5d ranks **1-5** in ≥ 3 of 5 cohorts
  (matches v3 /025 precedent's top-importance pattern). Trees structurally
  unable to compose; verifies the v3 mechanism transfers to v1's richer
  primitive stack.
- **PASS-CONDITIONAL** (PROMISING-INERT-FAV consistent): importance ≥ 30 (top
  third) in ≥ 2 of 5 cohorts. Feature LEARNED but signal-redundant with
  incumbents — Critic Check 4 IC carve-out gate cleared.
- **FAIL**: importance ≥ 30 in 0 of 5 cohorts (i.e. rank ≥ 31 in ALL 5
  cohorts) → axis INERT-by-importance → composed-feature mechanism does NOT
  transfer to v1 → reclassify as EXPLORATION-INERT-LEARNED-NEG regardless of
  F1 band. RSI colsample-theft hypothesis CONFIRMED.

### F-AXIS #3 — Trade-count band

**Anchor**: BASELINE_V1 IS 621 / OOS 189.

- **IS band**: [560, 690] (±15% feature-add basin perturbation per /034
  precedent).
- **OOS band**: [165, 215] modal ~190.
- **TECHNICAL-FAILURE-SILENT-FALLBACK trigger**: IS < 470 OR OOS < 145 →
  BLOCK-PENDING-FIX (silent BASELINE catch-all dispatch OR parquet schema
  mismatch).

### F-AXIS #4 — Per-symbol OOS Δ direction

| symbol | predicted OOS Δ direction | mechanism rationale |
|---|---|---|
| BTC (in Pool A) | flat to slight + | RSI-overlapping signal; modest lift if model picks up longer horizon |
| ETH (in Pool A) | + | richer momentum response; horizon-diversification benefit |
| LINK | + | LINK historically rewards momentum-family additions (RSI rank 2) |
| LTC | flat to mild + | LTC weaker momentum response; modest |
| DOT | flat to + | DOT 2022 bear regime + post-launch drift; uncertain |

**Falsifier**: if 4/5 symbols turn NEGATIVE OOS Δ, mechanism REFUTED →
reclassify INERT. Per-cohort attribution dissolves at multi-seed
(`feedback_v3_single_seed_frozen_baseline.md`) — single-seed per-symbol
directions are diagnostic, not statistical, at EXPLORATION budget.

### F-AXIS #5 — Loss-surface relocation (basin-stability)

Cross-seed best-`learning_rate` Spearman correlation vs baseline median **>
0.80** → axis is feature-add-clean (PROMISING attributable to signal, not
basin lottery). < 0.50 → reclassify PROMISING-BASIN-RELOCATION-ARTIFACT.
Informational at single-seed EXPLORATION budget; CONFIRMATION re-validates
multi-seed.

---

## Section 2.5 — HIGH-RISK Axis Declaration (v1-only)

- **Declaration**: **NORMAL-RISK**
- **Reason**: Pure feature swap (DROP 1 + ADD 1 → V1_FEATURE_COLUMNS_PRUNED
  stays at 44 cols). Does **NOT** change Optuna training-objective domain,
  labels, universe, model arch, label-mode, bar-interval, loss function,
  risk gates, sample weighting, or n_features dimension. Mirror of /034
  (feature-family, NORMAL-RISK declared); the DROP+ADD pattern is more
  conservative than /034's pure ADD because n_features dimension is held
  constant.
- **Mitigation (optional)**: F-AXIS #2 LOAD-BEARING importance rank gate
  catches RSI colsample-theft; F-AXIS #5 cross-seed Spearman diagnostic
  catches basin-relocation (defensive only at NORMAL-RISK).
- **Budget choice**: SINGLE-SEED=42 at v1 EXPLORATION standard
  (ENSEMBLE_SIZE=3, n_trials=18, outer seed=42). No multi-seed opt-in.

---

## Section 3 — Implementation Design + CLI Invocation

### Section 3.1 — Code changes (5 atomic edits)

1. **NEW** `src/crypto_trade/features_v1/composed_v1.py` (~120 lines, mirrors
   v3's `engineered_v3.py:36-91`):
   - `_hurst_rs(window)` and `_rolling_hurst(series, window=100)` — BYTE-FOR-BYTE
     copies from `src/crypto_trade/features_v3/regime_v3.py:34-75`.
   - `compute_regime_momentum_signed_5d(df, ret_window_bars=15, hurst_window=100)`
     — returns `ret_5d × sign(hurst_100 − 0.5)` per row.
   - `add_composed_v1_features(df, ret_window_bars=15, hurst_window=100)` —
     wrapper for registry dispatch.

2. **EDIT** `src/crypto_trade/features/__init__.py`:
   - `from crypto_trade.features_v1.composed_v1 import add_composed_v1_features as _add_composed_v1_features`
   - `_register("composed_v1", _add_composed_v1_features)  # iter-v1/040`

3. **EDIT** `src/crypto_trade/features_v1/__init__.py`:
   - **REMOVE** `"basis_zscore_30",` from `V1_FEATURE_COLUMNS_PRUNED` tuple.
   - **ADD** `"regime_momentum_signed_5d",` to `V1_FEATURE_COLUMNS_PRUNED`
     tuple (alphabetical insertion).
   - **ADD** `"regime_momentum_signed_5d"` to `V1_NON_FEATURE_COLUMNS` exclusion
     check (defensive) — actually V1_NON_FEATURE_COLUMNS lists columns NOT to
     treat as features; the new col IS a feature so it does NOT belong in
     V1_NON_FEATURE_COLUMNS. Instead: ADD `"basis_zscore_30"` to
     V1_NON_FEATURE_COLUMNS so any residual basis_zscore_30 column in legacy
     parquets is explicitly NOT picked up as a feature.
   - Assertion: `assert len(V1_FEATURE_COLUMNS_PRUNED) == 44` (UNCHANGED count).

4. **EDIT** `run_baseline_v1.py`:
   - Add `iteration_label == "v1-040"` dispatch branch (~85 lines mirroring
     /034 dispatch).
   - Dispatch banner:
     `[iter-v1/040] COMPOSED-FEATURE ACTIVE: regime_momentum_signed_5d@<pos> / 44 features; basis_zscore_30 DROPPED`.
   - Pre-flight assert: `assert "regime_momentum_signed_5d" in active_feature_columns`.
   - Pre-flight assert: `assert "basis_zscore_30" not in active_feature_columns`.
   - 4 model dispatch (Model A pool / C / D / E) — identical to /034 spec.
   - **ADD `"v1-040"`** to BASELINE catch-all exclusion tuple (per /030
     LESSON `feedback_v1_dispatch_baseline_catchall_exclusion.md`).

5. **NEW** `tests/features_v1/test_composed_v1.py` + `tests/test_iteration_v1_040.py`
   (≥12 tests total per Section 10.3).

### Section 3.2 — Feature regeneration

Pre-backtest, regenerate v1 features so `regime_momentum_signed_5d` is present:

```bash
uv run crypto-trade features \
  --symbols BTCUSDT,ETHUSDT,LINKUSDT,LTCUSDT,DOTUSDT \
  --interval 8h \
  --track v1 \
  --groups composed_v1 \
  --format parquet \
  --workers 4
```

Single-group regeneration: ~3-5 min total (5 symbols × <1 min/symbol since
Hurst is the dominant cost via vectorized R/S over 100-bar windows).

### Section 3.3 — CLI invocation (Phase 6 backtest)

```bash
PYTHONUNBUFFERED=1 uv run python run_baseline_v1.py \
  --pruned-features \
  --iteration-label v1-040 \
  --exploration \
  --n-trials 18 \
  --ensemble-size 3 \
  --seeds 42 \
  > logs/iter_v1_040_backtest.log 2>&1
```

### Section 3.4 — Symbols + universe + model config

| Item | Spec |
|---|---|
| Universe | V1_BASELINE_UNIVERSE (BTC/ETH/LINK/LTC/DOT) UNCHANGED |
| Models | A (BTC+ETH, atr_tp=2.9/sl=1.45, R1=OFF, R3=ON), C (LINK, atr_tp=3.5/sl=1.75, R1=ON, R3=ON), D (LTC, atr_tp=3.5/sl=1.75, R1=ON, R3=ON), E (DOT, atr_tp=3.5/sl=1.75, R1=ON, R2=ON, R3=ON) — IDENTICAL to baseline |
| Labels | triple-barrier σ_t EWMA 14d UNCHANGED |
| Features | V1_FEATURE_COLUMNS_PRUNED 44 cols (DROP basis_zscore_30; ADD regime_momentum_signed_5d) |
| Sample weight | `abs_pnl` (baseline) |
| Optuna bounds | `v1_pruned` |
| n_trials | 18 |
| Inner ensemble | 3 seeds (V1_EXPLORATION_ENSEMBLE_SIZE) |
| Outer seed | 42 (single) |
| Walk-forward | training_months=24 (sacred), monthly retrain, embargo via walk_forward.py:113 fix |
| OOS_CUTOFF | 2025-03-24 (sacred) |

### Section 3.5 — File changes

| File | Change | Approx LOC |
|---|---|---|
| `src/crypto_trade/features_v1/composed_v1.py` | NEW | ~120 |
| `src/crypto_trade/features_v1/__init__.py` | swap tuple member + V1_NON_FEATURE_COLUMNS ADD | +3 −1 |
| `src/crypto_trade/features/__init__.py` | INSERT import + register | +4 |
| `run_baseline_v1.py` | INSERT dispatch + exclusion-tuple add | +90 |
| `tests/features_v1/test_composed_v1.py` | NEW | ~140 |
| `tests/test_iteration_v1_040.py` | NEW | ~120 |

Total 6 files, ~480 LOC net.

---

## Section 4 — F-AXIS #2-#5 + Verdict Matrix

| F1 (OOS Δ) | F2 importance | F4 per-sym | F5 Spearman | Verdict | Cycle-5 routing |
|---|---|---|---|---|---|
| ≥ +0.50 | rank 1-5 ≥3/5 | ≥3/5 syms +OOS | > 0.80 | PROMISING-CLEAN-EXCEPTIONAL | /044 CONFIRMATION substrate (alongside /036 + /037) |
| +0.20 to +0.50 | rank ≤ 30 ≥2/5 | ≥3/5 syms +OOS | > 0.80 | PROMISING-CLEAN | /044 substrate candidate |
| +0.05 to +0.20 | rank ≤ 30 ≥2/5 | mixed | > 0.50 | PROMISING-INERT-FAV (LEARNED-redundant) | /041 stacking experiment OR /044 substrate at low confidence |
| -0.10 to +0.05 | rank ≥31 all 5 | mixed | > 0.50 | INERT-LEARNED-NEG (RSI colsample-theft confirmed) | composed-feature axis CLOSED at v1 EXPLORATION; /041 NEW axis |
| -0.30 to -0.10 | rank ≥31 all 5 | <3/5 +OOS | varies | NEGATIVE-no-effect | composed-feature axis CLOSED |
| < -0.30 | varies | <2/5 +OOS | varies | NEGATIVE-CATASTROPHIC | composed-feature axis CLOSED; counter-example to v3 /025 PROMISING precedent appended to `feedback_v3_engineered_features_proven.md` |

---

## Section 5 — Configuration (canonical) + Risk Mitigation

### Section 5.1 — Configuration locks

- ENSEMBLE_SIZE = 3 inner (V1_EXPLORATION_ENSEMBLE_SIZE; 42, 123, 456 first 3)
- n_trials = 18 (v1 EXPLORATION standard)
- single outer seed = 42
- training_months = 24 (sacred)
- OOS_CUTOFF = 2025-03-24 (sacred)
- bounds_profile = `v1_pruned`
- Sample weight = `abs_pnl` baseline
- Optuna objective = Sharpe baseline (NOT Sortino — orthogonal to /037)

### Section 5.2 — Risk Mitigation

| Risk Layer | Status | Rationale |
|---|---|---|
| **R1 Consecutive-SL cool-down** | UNCHANGED (active C/D/E, off A) | Independent of feature swap |
| **R2 Drawdown brake** (Model E) | UNCHANGED | Independent |
| **R3 OOD Mahalanobis** | UNCHANGED (active all 4 models, cutoff 0.70, 16 features) | V1_OOD_FEATURE_COLUMNS decoupled — composed feature NOT added to OOD set (regime-conditional features destabilize OOD subspace) |
| **NEW concentration / sizing gate** | NONE | EXPLORATION single-axis; no new risk primitive |

---

## Section 6 — Wall-clock estimate

**5-step scaling per `feedback_v1_label_rate_wall_clock_scaling.md`**:

- **Anchor**: /034 ~50 min compute at v1 EXPLORATION standard (n_trials=18,
  ENSEMBLE_SIZE=3, 5 syms, 43→44 cols, single-seed=42).
- **/040 expected**: feature SWAP (drop 1 + add 1; n_features unchanged at 44).
  Label generation unchanged. Optuna search-space dimensionality unchanged.
- **Composite scaling factor**: 1.00× (identical to /034).
- **Projection**: 50 min compute.

**Total wall-clock**:
- Data fetch: 0 min (perp 8h klines on disk; no new data source).
- Feature regen: 3-5 min (composed_v1 single-group; Hurst R/S 100-bar is the
  cost driver via vectorized rolling).
- Backtest compute: ~50 min.
- Report layer: ~3 min.

**Modal total: ~60 min (1.0h).** Conservative band: 50-80 min. No
kill-switch.

---

## Section 7 — Expected report shape

After Phase 6 backtest, expected artifacts at `reports-v1/iteration_v1-040/`:

- `comparison.csv` — 4 model rows (Pool A / C / D / E) IS + OOS + per-symbol;
  portfolio aggregate row with IS Sharpe + OOS Sharpe + IS/OOS trade counts.
- `in_sample/trades.csv` — IS trades (expected 560-690).
- `out_of_sample/trades.csv` — OOS trades (expected 165-215).
- `feature_importance.csv` — per-cohort split-count rankings for all 44
  features × 4 models × ~12 walk-forward months (≥ 2,000 rows). Required for
  F-AXIS #2 evaluation.
- `dsr.json` — DSR + PSR + n_eff (informational at EXPLORATION mode per
  `feedback_v3_dsr_mode_artifact.md`).
- Dispatch banner in `logs/iter_v1_040_backtest.log`:
  `[iter-v1/040] COMPOSED-FEATURE ACTIVE: regime_momentum_signed_5d@<pos> / 44 features; basis_zscore_30 DROPPED`.

---

## Section 8 — Path Forward (per /038 Critic + LM Master)

**Conditional routing on F1 verdict**:

- **PROMISING-CLEAN (Δ ≥ +0.20)**: /040 substrate candidate for /044
  CONFIRMATION bundle alongside /036 (LINK+DOT trend-scan) + /037 (Sortino).
  Multi-seed CONFIRMATION at /044-C target band [+0.05, +0.20]. Bundling
  decision deferred to /044 brief composition (non-compoundability flag per
  cycle-5 ingredient orthogonality).
- **PROMISING-INERT-FAV (Δ ∈ [+0.05, +0.20] AND importance ≥ 30 in ≥ 2
  cohorts)**: /041 stacking experiment — add a SECOND composed feature
  (candidate: `vol_adj_autocorr_5_signed`) at single-seed to test whether
  v1 supports composed-feature ACCUMULATION (caveat: v3
  `feedback_v3_engineered_features_dont_stack.md` says NO at single-seed;
  v1 may differ).
- **INERT (Δ ∈ [-0.10, +0.05])**: composed-feature axis CLOSED at v1
  EXPLORATION budget; /041 NEW axis from cycle-5 menu (axis #8 = volume
  imbalance z-score OR cross-symbol correlation gate). LM Master /038 §6 Rec
  2 (LABELING width asymmetry) becomes next-priority axis.
- **NEGATIVE (Δ < -0.10)**: composed-feature axis CLOSED; counter-example to
  v3 /025 PROMISING precedent appended to
  `feedback_v3_engineered_features_proven.md` documenting that v3-proven
  composed features do NOT generalize to v1's 5-cohort 44-feature stack at
  single-seed EXPLORATION. /041 = LM Master /038 §6 Rec 2 labeling width
  asymmetry (TP=1.5/SL=0.75) — MEDIUM CONFIDENCE LM endorsement.

**Alternative axes from non-feature-family for cycle-5 #8/9/10** (per
constructive-Critic Path Forward discipline):

1. **LABELING** (untouched outside /035 trend-scan + /015 σ_t magnitude):
   triple-barrier WIDTH asymmetry per LM /038 §6 Rec 2 — TP=1.5/SL=0.75
   narrower bands → more trades + Optuna basin re-search.
2. **MODEL-ARCH** (untouched in v1 cycle-5): XGBoost head-to-head on v1's
   44-col stack per LM /038 §6 Rec 3 — MEDIUM-LOW CONFIDENCE; v3 /016
   tested at 13-feature stack and got NEG-CLEAN, but v1's richer stack +
   5-cohort universe is a different regime.
3. **SAMPLE-WEIGHTING isolation refresh**: revisit /031 `composite_inv_concurrency`
   PROMISING-BASIN-RELOCATION-ARTIFACT at multi-seed pre-CONFIRMATION (NOT
   currently scheduled; would require user authorization).

---

## Section 9 — Behavioral Predictor (per `feedback_v3_axis_saturation_predictor.md`)

**Predicted IS trade count change**: ±5% from baseline 621 IS trades (range
[560, 690] per F-AXIS #3 band). Feature SWAP (drop 1 + add 1, n_features
unchanged) perturbs Optuna basin similarly to feature ADD (/034 anchor); does
NOT change label generation.

**Predicted OOS trade count change**: ±10% from baseline 189 OOS trades (range
[165, 215]). NEW composed feature may introduce small directional gating;
threshold effects through R3 OOD gate possible.

**Predicted importance rank for regime_momentum_signed_5d**: median rank
**5-12 / 44** across (cohort, OOS month) cells per Section 1.5. Modal target
**rank ≤ 30 in ≥ 2 of 5 cohorts** (Critic Check 4 IC carve-out gate). Top-5
rank in ≥3 cohorts (matching v3 /025) would be a strong signal that v3
mechanism transfers cleanly.

**Predicted per-symbol OOS Δ direction**: ETH + LINK positive; BTC + LTC
flat to mild positive; DOT uncertain (may benefit from 120h horizon in 2022
bear regime, or may underperform if RSI overlap dominates).

**Predicted F1 OOS Sharpe Δ**: range [-0.10, +0.50], modal **+0.12**
(PROMISING-INERT-FAV centered) per QR-adjusted priors in F-AXIS #1.

**FALSIFIERS**:
1. If `regime_momentum_signed_5d` importance rank ≥ 31 in ALL 5 cohorts at
   ≥ 4/5 walk-forward OOS months → axis INERT-by-importance regardless of
   F1 outcome → composed-feature mechanism does NOT transfer to v1 →
   reclassify as EXPLORATION-INERT-LEARNED-NEG; RSI colsample-theft
   hypothesis CONFIRMED.
2. If IS < 470 OR OOS < 145 → TECHNICAL-FAILURE-SILENT-FALLBACK (BASELINE
   catch-all dispatch OR parquet schema mismatch) → BLOCK-PENDING-FIX.
3. If F1 Δ ≤ -0.30 (NEG-CATASTROPHIC) → composed-feature axis CLOSED at v1;
   append v1-counter-example to `feedback_v3_engineered_features_proven.md`
   documenting v3-proven mechanism non-transfer.

**Mechanism failure scenario (PREDICTED MOST PLAUSIBLE FAILURE MODE)**:
RSI colsample-theft. Composed feature has |IC|=0.80 with `mom_rsi_14`; v1's
`mom_rsi_14` ranks 1-3 across all 5 cohorts at /037-/038. At n_trials=18 +
LightGBM colsample_bytree, the composed feature may displace RSI in
split-budget without net signal gain → PROMISING-INERT-FAV (rank ≥ 30 but
F1 Δ in [+0.05, +0.20] band) or INERT-LEARNED-NEG (rank < 31 but F1 Δ
< +0.05) depending on whether RSI's role was efficiency-only or signal-only.

---

## Section 10 — Symbol Exclusion + Reproducibility + Test Mandate

### Section 10.1 — Symbol exclusion

V1_BASELINE_UNIVERSE UNCHANGED (BTC/ETH/LINK/LTC/DOT). No symbols added or
removed. V1_EXCLUDED_SYMBOLS unchanged.

### Section 10.2 — Reproducibility

- Single outer seed = 42 (baseline canonical)
- ENSEMBLE_SIZE = 3 inner seeds (42, 123, 456 first 3 per V1_EXPLORATION_ENSEMBLE_SIZE)
- Optuna sampler: TPE with random_state=outer_seed (deterministic per cell, seed)
- Walk-forward: monthly retrain, training_months=24 (sacred), embargo via walk_forward.py:113 fix
- Hurst R/S computation is deterministic (pure rolling vectorized math; no
  random sampling).

Two re-runs from clean checkout must produce bit-identical trades.csv per
`feedback_deterministic_trade_match.md`.

### Section 10.3 — Test mandate (≥12 tests)

`tests/features_v1/test_composed_v1.py`:
1. `test_hurst_rs_byte_identical_to_v3` — synthetic 100-bar series produces
   bit-identical Hurst as v3's `_hurst_rs`.
2. `test_rolling_hurst_burn_in_nan` — first 99 bars are NaN (rolling warm-up).
3. `test_compute_regime_momentum_signed_5d_known_values` — sample-instance
   assertion on 32-row synthetic series matches hand-computed `ret_5d ×
   sign(hurst − 0.5)` to <1e-9.
4. `test_compute_regime_momentum_signed_5d_past_only` — bar t's value uses
   ONLY close[t-15..t] for ret_5d AND close[t-100..t] for hurst (no
   forward-leak; lookahead guard).
5. `test_compute_regime_momentum_signed_5d_burn_in` — first max(15, 100)
   bars NaN per symbol.
6. `test_add_composed_v1_features_btc_smoke` — runs on real BTC data; output
   has `regime_momentum_signed_5d` column; non-null fraction > 95% after
   burn-in.
7. `test_add_composed_v1_features_stationarity` — ADF p-value < 0.01 on BTC
   IS slice (sanity check; replicates Section 1.2 EDA).

`tests/test_iteration_v1_040.py`:
8. `test_v1_040_pruned_features_contains_regime_momentum_signed_5d` —
   V1_FEATURE_COLUMNS_PRUNED tuple contains `"regime_momentum_signed_5d"`.
9. `test_v1_040_pruned_features_excludes_basis_zscore_30` —
   V1_FEATURE_COLUMNS_PRUNED tuple does NOT contain `"basis_zscore_30"`.
10. `test_v1_040_pruned_features_count_44` — len(V1_FEATURE_COLUMNS_PRUNED)
    == 44 (UNCHANGED count post-swap).
11. `test_v1_040_basis_zscore_30_in_non_feature_columns` — V1_NON_FEATURE_COLUMNS
    contains `"basis_zscore_30"` (defensive — legacy parquet residual
    rejection).
12. `test_v1_040_dispatch_branch_exists` — runner code path
    `iteration_label == "v1-040"` is reachable (existence check via
    `inspect.getsource(run_baseline_v1)`).
13. `test_v1_040_in_baseline_catchall_exclusion` — runner BASELINE catch-all
    tuple contains `"v1-040"` per /030 LESSON.
14. `test_v1_040_dispatch_banner_emitted` — runner with
    `iteration_label="v1-040"` prints `[iter-v1/040] COMPOSED-FEATURE ACTIVE:
    regime_momentum_signed_5d@<pos> / 44 features; basis_zscore_30 DROPPED`.

**ALL 14 tests must pass at Phase 6 before backtest launch.**

### Section 10.4 — Anti-cheating self-check

- IS-only window for ALL Phase 1-5 EDA work (close_time < 2025-03-24 per
  `analysis/iteration_v1-040/eda.py`).
- OOS data NOT inspected during Phases 1-5.
- IS window NOT trimmed; full 2020-01 → 2025-03-23 used for EDA.
- training_months = 24 sacred; OOS_CUTOFF_MS sacred.
- `_hurst_rs` reads only `close[t-100..t]`; `ret_5d` reads only
  `close[t-15..t]` — strictly past-only.

### Section 10.5 — Phase 5.5 dispatch readiness

- Brief committed at HEAD.
- EDA scripts committed at `analysis/iteration_v1-040/`.
- LM Master /038 §6 Rec 1 (HIGH CONFIDENCE) ADOPTED VERBATIM — DROP
  basis_zscore_30 + ADD regime_momentum_signed_5d.
- LM Master /038 §6 Rec 2 (LABELING width asymmetry, MEDIUM CONFIDENCE)
  DEFERRED to /041 conditional on /040 INERT/NEG outcome (per Path Forward §8).
- LM Master /038 §6 Rec 3 (MODEL-ARCH XGBoost head-to-head, MEDIUM-LOW
  CONFIDENCE) DEFERRED to cycle-5 #9/10 or cycle-6 substrate.
- BASELINE catch-all exclusion tuple ADD planned (Phase 6 first commit).
- Test suite mandate documented (14 tests).
- Wall-clock target 1.0h modal — well INSIDE 2h cap.
- NORMAL-RISK declared; single-seed=42 at v1 EXPLORATION standard.

Ready for Phase 6 dispatch.

---

**END OF BRIEF**
