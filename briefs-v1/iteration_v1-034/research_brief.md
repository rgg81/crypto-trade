# iter-v1/034 — Research Brief

**Iteration**: iter-v1/034
**Date**: 2026-05-30
**TYPE**: EXPLORATION
**Cycle**: 5, EXP 1 of 10
**Branch**: `iteration-v1/034`
**Author**: QR (autopilot)

---

## Section 0 — Hypothesis

**H1 (PRIMARY)**: The **basis z-score** (perp − spot, normalized over a 30-bar rolling window) is an OHLCV-orthogonal signal of intraday futures-positioning stretch that LightGBM can convert into ≥ +0.20 OOS monthly Sharpe lift over `BASELINE_V1` (`+0.6637`). Cycle-5 menu axis #1 was Binance forced-liquidation z-score; that data source is NOT viable (Section 1.0), so /034 PIVOTS to the documented backup axis per `briefs-v1/cycle5_axis_menu.md` line 53–54.

**H1a (mechanism)**: Persistent positive basis = leveraged-long crowding → mean-reversion (or liquidation cascade) prior; persistent negative basis = leveraged-short stress → squeeze prior. The 30-bar z-score normalizes for secular shifts in perp-spot premium so the model sees regime-relative stretch, not absolute level.

**H1b (falsifiable)**: If the IS Sharpe lift is below F1 lower band AND the importance rank for `basis_zscore_30` is 14/14 or lower in ≥4/5 walk-forward months, the axis is INERT and CLOSED at v1 EXPLORATION budget.

---

## Section 0.5 — Iteration Type, Cadence Position, Wall-Clock

- **TYPE**: EXPLORATION
- **Cadence**: cycle-5 EXPLORATION 1 of 10. Cycle-4 closed at /033 BLOCK-FINAL (CONFIRMATION bundle). Cycle-5 mandate: 70% NEW signal sources, 30% architecture (user directive 2026-05-29 + `briefs-v1/cycle5_axis_menu.md`).
- **NO kill-switches** (user directive 2026-05-30).
- **Wall-clock target**: 1.5h modal at v1 EXPLORATION standard (n_trials=18, ENSEMBLE_SIZE=3). Cap NOT enforced via kill — overrun acceptable per cycle-5 discipline.

---

## Section 0.6 — Axis-Family Rotation (v1-only)

- **Axis family**: `feature-family` (NEW NEW signal-source addition: basis z-score)
- **Prior 5 EXPLORATION families** (from `briefs-v1/exploration_catalog.md`):
  - iter-v1/028: per-cohort-specialization-LTC-v2
  - iter-v1/029: per-cohort-specialization-DOT-v2 (TF)
  - iter-v1/030: meta-labeling (CLOSED)
  - iter-v1/031: sample-weighting
  - iter-v1/032: sample-weighting-isolation
- **Rotation status**: **VALID** — `feature-family` family last fired at /025 (>9 EXPLORATIONs ago). Prior 5 disperse across 3 families (per-cohort-specialization, meta-labeling, sample-weighting). /034 PIVOTS the family back to feature-family with a CATEGORICALLY NEW data source (perp-vs-spot basis is NOT cited in /023 funding or /025 OI implementations).
- **One-sentence rationale**: cycle-5 mandates 70% NEW signal sources, and the perp-spot basis is a structurally independent crypto-microstructure primitive (not funding, not OI, not OHLCV) that has never been touched in v1 cycles 1-4.

---

## Section 1 — IS-Only Evidence + Phase 1 Data-Source Decision

### Section 1.0 — Data-source viability for axis (Phase 1)

Cycle-5 axis menu specifies `/034 — Liquidations volume z-score`. Phase 1 verification (`analysis/iteration_v1-034/data_source_check.py`):

| Source | Status | Coverage 2022-01 → 2026-05 |
|---|---|---|
| `data.binance.vision/.../liquidationSnapshot/...` | **404 NOT FOUND** | Endpoint retired by Binance |
| `/fapi/v1/forceOrders` (API) | Account-private OR public ~7-day window | Insufficient for IS-OOS backtest |
| Coinglass / CryptoQuant / Tardis / Amberdata | 3rd-party, paid | Not available in worktree |

**Liquidation axis: NOT VIABLE.** Per cycle-5 menu line 53–54 ("Risk: data availability fallback — if no clean source, replace with **basis (perp − spot) z-score**"), /034 PIVOTS to basis.

### Section 1.0a — Basis data viability (Phase 1)

| Symbol | Perp 8h rows IS | Spot 8h rows IS | Merged | First merged date |
|---|---|---|---|---|
| BTCUSDT | 5,727 | 5,727 | 5,727 | 2020-01-01 |
| ETHUSDT | 5,727 | 5,727 | 5,727 | 2020-01-01 |
| LINKUSDT | 5,678 | 5,727 | 5,678 | 2020-01-17 |
| LTCUSDT | 5,687 | 5,727 | 5,687 | 2020-01-09 |
| DOTUSDT | 5,025 | 5,035 | 5,025 | 2020-08-22 |

Both feeds already on disk under `data/<SYM>/8h.csv` (perp) and `data/spot/<SYM>/8h.csv` (spot). **Fetch cost = 0 min.**

### Section 1.1 — Feature definition (canonical)

```
basis_bps[t]        = (perp_close[t] - spot_close[t]) / spot_close[t] * 10_000
basis_zscore_30[t]  = (basis_bps[t] - mean(basis_bps[t-30..t-1])) /
                       std(basis_bps[t-30..t-1])
```

- Window: 30 bars (~10 days at 8h cadence) — matches `funding_rate_zscore_30` convention.
- Past-only: rolling stats use `.shift(1)` so bar t's own basis does NOT enter bar t's rolling denominator. Numerator uses `basis_bps[t]` which IS knowable at bar close (perp_close and spot_close are bar-close prices).
- Clip: ±10.0 (mirrors `ZSCORE_CLIP` in `funding_v1.py`).
- Burn-in: first 30 rows NaN per symbol.

### Section 1.2 — Distribution per symbol (IS-only)

| Symbol | rows IS | z_mean | z_std | z_skew | z_kurt | z_p01 | z_p99 | %\|z\|>2 | raw bp mean | raw bp std |
|---|---|---|---|---|---|---|---|---|---|---|
| BTCUSDT | 5,727 | +0.006 | 1.257 | +0.756 | 6.143 | -2.81 | +3.52 | 8.43% | -0.69 | 6.36 |
| ETHUSDT | 5,727 | +0.008 | 1.248 | +0.917 | 8.792 | -2.73 | +3.28 | 7.53% | +0.02 | 6.88 |
| LINKUSDT | 5,678 | +0.010 | 1.163 | -0.231 | 3.049 | -2.70 | +2.75 | 7.42% | -0.26 | 9.04 |
| LTCUSDT | 5,687 | +0.020 | 1.174 | +0.015 | 2.125 | -2.84 | +2.91 | 7.53% | +0.35 | 8.18 |
| DOTUSDT | 5,025 | +0.004 | 1.170 | -0.308 | 4.758 | -2.74 | +2.70 | 6.91% | -1.59 | 9.26 |

- **Cross-symbol consistency**: all 5 symbols have z_mean ≈ 0 and z_std ≈ 1.17–1.26 (the z_std > 1 indicates the rolling denominator under-estimates true dispersion ~17–26% on average — typical for fat-tailed series).
- **Fat tails present** but well-clipped: max 8.4% of bars have |z| > 2 (BTC); rest ~7%.
- **Symbol-specific raw level**: DOT has the largest negative bias (-1.59 bps mean basis), LINK has highest dispersion (std 9.04 bps); z-scoring normalizes both.

### Section 1.3 — Cross-correlation with V1_FEATURE_COLUMNS_PRUNED (Pearson IC, IS-only)

Top 5 |Pearson| per symbol:

| Symbol | Feature 1 | r | Feature 2 | r | Feature 3 | r |
|---|---|---|---|---|---|---|
| BTCUSDT | trend_plus_di_14 | +0.359 | trend_minus_di_14 | -0.348 | trend_ema_cross_5_12 | +0.340 |
| ETHUSDT | trend_plus_di_14 | +0.366 | mom_rsi_14 | +0.363 | trend_minus_di_14 | -0.349 |
| LINKUSDT | trend_minus_di_14 | -0.309 | mom_rsi_14 | +0.272 | mr_pct_from_high_20 | +0.257 |
| LTCUSDT | trend_minus_di_14 | -0.371 | mom_rsi_14 | +0.370 | trend_ema_cross_5_12 | +0.349 |
| DOTUSDT | trend_minus_di_14 | -0.340 | mom_rsi_14 | +0.324 | trend_ema_cross_5_12 | +0.299 |

**GLOBAL max |Pearson|** = -0.371 (LTC vs trend_minus_di_14). Within informative band (|IC| < 0.50 per `feedback_v3_engineered_feature_pivot.md` — basis is a NEW family with low/moderate correlation to trend/momentum, NOT redundant).

**Pattern**: positive correlation with bullish-trend features (RSI, +DI, EMA cross) and negative with -DI. Mechanism: positive basis indicates leveraged-long crowding which correlates with prevailing uptrend. The IC is not so large that LightGBM colsample picks would be stolen — basis carries orthogonal information about positioning STRETCH not captured by price-action features alone.

### Section 1.4 — ADF stationarity test

| Symbol | n | ADF stat | p-value | Stationary @5% |
|---|---|---|---|---|
| BTCUSDT | 5,697 | -15.49 | 0.0 | ✓ |
| ETHUSDT | 5,697 | -20.68 | 0.0 | ✓ |
| LINKUSDT | 5,648 | -20.72 | 0.0 | ✓ |
| LTCUSDT | 5,657 | -18.04 | 0.0 | ✓ |
| DOTUSDT | 4,995 | -17.85 | 0.0 | ✓ |

All 5 symbols: ADF p-value < 1e-30 → strongly stationary. Satisfies the v1 stationarity discipline (`V1_FEATURE_COLUMNS_PRUNED` is curated to ADF α=0.05).

### Section 1.5 — Per-quintile baseline-trade attribution (IS, 621 trades)

| Symbol | Q1_low (z<−1.04) | Q2 | Q3 | Q4 | Q5_high (z>+1.10) |
|---|---|---|---|---|---|
| **BTC** WR / mean PnL | 43.5% / +0.85 | 22.7% / -1.60 | 30.4% / -0.69 | 40.9% / +0.46 | 30.4% / -0.70 |
| **ETH** WR / mean PnL | 24.1% / -1.64 | 37.9% / +0.18 | **58.6% / +1.74** | 27.6% / -2.00 | 44.8% / +1.24 |
| **LINK** WR / mean PnL | 36.7% / -1.47 | **65.5% / +4.02** | **55.2% / +3.03** | 34.5% / -1.48 | 34.5% / -1.57 |
| **LTC** WR / mean PnL | 28.0% / -2.45 | 48.0% / +1.37 | 41.7% / +1.38 | 32.0% / -1.51 | 48.0% / +1.40 |
| **DOT** WR / mean PnL | 36.8% / +0.05 | 44.4% / +0.51 | 42.1% / +0.24 | **55.6% / +1.85** | 31.6% / -1.12 |

**Three signals from this table**:
1. **ETH+LINK middle-quintile sweet spot**: ETH Q3 (z near 0) WR 58.6% / +1.74 mean PnL vs. ETH Q1 WR 24.1% / -1.64. LINK Q2-Q3 WR 55-65% / +3.0 to +4.0 mean PnL vs. LINK Q1/Q4/Q5 WR 34-37% / negative. **Mid-z bars are the productive ones for the M1 model on ETH/LINK.**
2. **LTC tail edge**: Q1 catastrophic (28% WR / -2.45) → LTC longs into negative-basis regime are particularly bad. Tighter atr_sl=1.0 from /028 (load-bearing component) may interact constructively.
3. **DOT inverted**: Q4 best (55.6% / +1.85). DOT may benefit from a sign-flipped relationship — basis at moderately-positive z is a long signal. LightGBM trees can absorb this asymmetry natively.

### Section 1.6 — Per-symbol Pearson with signed_pnl (baseline trade outcomes)

| Symbol | n | Pearson(z, net_pnl_%) | Spearman | Q5 long share | Q1 long share |
|---|---|---|---|---|---|
| BTCUSDT | 113 | -0.042 | -0.012 | 0.435 | 0.565 |
| ETHUSDT | 145 | +0.109 | +0.117 | 0.414 | 0.690 |
| LINKUSDT | 146 | -0.070 | -0.073 | 0.379 | 0.655 |
| LTCUSDT | 124 | +0.107 | +0.125 | 0.440 | 0.720 |
| DOTUSDT | 93 | +0.009 | +0.046 | 0.632 | 0.737 |

- Pearson(z, signed_PnL): ETH +0.11 and LTC +0.11 are the strongest (positive: HIGH basis → BETTER PnL outcome). This is mostly mechanical (long bias when z high; high z marks late-uptrend bullish-bias bars; trees can exploit).
- **q1_long_share vs q5_long_share**: across BTC/ETH/LINK/LTC, baseline takes 65–72% longs in low-z bars (negative basis = leveraged-short-stress → squeeze-long bias) and 38–44% in high-z bars (positive basis = leveraged-long-crowding → reversion-short bias). **Baseline ALREADY trades direction-conditional on what z-basis implies, but uses noisier proxies (RSI, MACD) to infer the regime. Adding z directly should improve LightGBM's ability to gate / size these directional decisions.**

**Combined hypothesis from §1.5+§1.6**: basis z is informationally orthogonal enough (max |IC|≈0.37) AND its mid-quintile bars are where ~50–60% of LINK/ETH's positive-PnL trades live. F1 lift is plausibly ≥+0.20 OOS Sharpe.

---

## Section 2 — Falsifiers

Five F-AXIS falsifiers. Verdict is determined by F1 outcome; F2-F5 are diagnostic on the failure mode.

### F-AXIS #1 — F1 OOS Sharpe Δ vs BASELINE_V1

**Anchor**: BASELINE_V1 = +0.6637 OOS monthly Sharpe (`v0.v1-baseline-corrected`).

| Band | OOS Δ | Verdict |
|---|---|---|
| Δ ≥ +0.50 | exceeds modal estimate | EXPLORATION-PROMISING-CLEAN |
| +0.20 ≤ Δ < +0.50 | PROMISING band | EXPLORATION-PROMISING |
| -0.10 ≤ Δ < +0.20 | within noise band (cycle-3+ F1 cap at ±0.10) | EXPLORATION-INERT |
| -0.30 ≤ Δ < -0.10 | NEGATIVE no-effect | EXPLORATION-NEGATIVE |
| Δ < -0.30 | NEGATIVE catastrophic | EXPLORATION-NEGATIVE-CATASTROPHIC |

LM Master priors for /034 (post-EDA): PROMISING-CLEAN 18% / PROMISING-INERT-FAV 27% / **INERT 30% MODAL** / NEG no-effect 17% / NEG-CAT 8% (combined PROMISING 45% vs combined NEG 25%; expected E[Δ] ≈ +0.07).

### F-AXIS #2 — Trade-count band (realistic per /033 LESSON)

Per `feedback_v1_axis_selection_data_fetch_budget.md` + /033 lesson: F2 must reflect MODAL behavior, not aspirational.

**Realistic baseline**: BASELINE_V1 IS 621 / OOS 189 (BIT-IDENTICAL anchor reproduction).
- Single-axis NEW feature additions at n_trials=18 + ES=3 typically perturb trade counts by ±15% (loss-surface relocates basin slightly).

**Bands**:
- IS [560, 690] / OOS [170, 215] — modal MEDIAN ~190 OOS.
- IS < 470 OR OOS < 145 → TECHNICAL-FAILURE-SILENT-FALLBACK (or BASELINE catch-all exclusion missing — /030 lesson) → BLOCK-PENDING-FIX.

### F-AXIS #3 — basis_zscore_30 feature importance

Importance rank (split-count) of `basis_zscore_30` across the 4 walk-forward models × test months:

- **Median rank across (Model, OOS month) pairs**: rank ≤ 22/44 in ≥50% of cells → LEARNED.
- **Worst-case**: rank 14/14 in ≥4/5 OOS months for ANY model → INERT-by-importance → confirmation that the feature is signal-empty.

If basis IC ~0.37 vs trend features but rank 14/14 → LightGBM finds trend features more split-efficient at depth-5 trees; basis is redundant despite stat measure.

### F-AXIS #4 — Per-symbol Δ direction band

Per `feedback_v3_axis_saturation_predictor.md` — must predict behavioral effect:

| Symbol | Predicted IS Δ direction | Predicted OOS Δ direction | Mechanism rationale |
|---|---|---|---|
| BTC (in Pool A) | flat to slight + | flat to slight + | weak trade outcome IC, but baseline already sees direction-conditional patterns via RSI/MACD |
| ETH (in Pool A) | + | + | EDA §1.5: Q3 WR 58.6% productivity peak; +0.11 signed Pearson; expected ≥+0.10 OOS Sharpe lift |
| LINK | + | + | EDA §1.5: Q2-Q3 WR 55-65% mean PnL +3.0 / +4.0; strongest quintile signal |
| LTC | + (mild) | + (mild) | EDA §1.5: Q1 catastrophe avoidance prior; tighter SL interaction |
| DOT | - (mild) to + | - (mild) to + | EDA §1.5: inverted Q4 peak; sign-asymmetry may dilute signal |

**Falsifier**: if 4/5 symbols turn NEGATIVE OOS Δ, mechanism prediction REFUTED → reclassify INERT → cycle-5 #5/038 axis prior weight shifts toward gate-architecture wins.

### F-AXIS #5 — Loss-surface relocation magnitude (Cross-seed best-`learning_rate` Spearman)

Per `feedback_v1_iter032_axis_attribution_methodology.md` — measure basin-relocation risk:

- Cross-seed best-`learning_rate` Spearman correlation vs BASELINE_V1 baseline median **> 0.80** → axis is feature-add-clean, not loss-surface-disruptive (PROMISING attributable to signal, not basin-lottery).
- < 0.50 → basin-lottery artifact concern → reclassify candidate to PROMISING-BASIN-RELOCATION-ARTIFACT (mirror /031 → /032 isolation step). At v1 EXPLORATION budget single-seed, this is informational only; CONFIRMATION would re-validate via frozen-HP.

---

## Section 2.5 — HIGH-RISK Axis Declaration

- **Declaration**: **NORMAL-RISK**
- **Reason**: Pure feature-add. Does NOT change Optuna's training-objective domain, labels, universe, model arch, label-mode, bar-interval, or risk-primitive constraints. Mirror of /023 (funding NEW feature) and /025 (OI NEW feature), both NORMAL-RISK declared.
- **Mitigation**: F-AXIS #5 cross-seed Spearman diagnostic catches basin-relocation if signal is conflated with loss-surface disruption (defensive only — not expected at single-feature-add).

---

## Section 3 — Implementation Design + CLI Invocation

### Section 3.1 — Code changes (4 atomic edits)

1. **NEW** `src/crypto_trade/features_v1/basis_v1.py` (~150 lines, mirrors `funding_v1.py` structure):
   - `compute_basis_zscore(perp_df, spot_df, window=30, clip=10.0, output_col="basis_zscore_30")`
   - `add_basis_v1_features(df, data_dir=Path("data"), window=30, clip=10.0)`
   - Spot data loaded from `data_dir / "spot" / <SYMBOL> / "8h.csv"` (already on disk)
   - Past-only via `.shift(1)` on rolling stats
   - Clip ±10.0 on z-score

2. **EDIT** `src/crypto_trade/features/__init__.py`:
   - Add `from crypto_trade.features_v1.basis_v1 import add_basis_v1_features as _add_basis_v1_features`
   - Add `_register("basis_v1", _add_basis_v1_features)  # iter-v1/034`

3. **EDIT** `src/crypto_trade/features_v1/__init__.py`:
   - Insert `"basis_zscore_30",  # iter-v1/034: NEW — basis (perp-spot) z-score 30-bar` into `V1_FEATURE_COLUMNS_PRUNED` (alphabetical position, between `"vol_volume_rel_20"` end-of-list — actually alphabetically `basis_zscore_30` sorts BEFORE `cal_dow_norm` at the front)
   - Update assertion: `assert len(V1_FEATURE_COLUMNS_PRUNED) == 44`

4. **EDIT** `run_baseline_v1.py`:
   - **Add `iteration_label == "v1-034"` dispatch branch** (~85 lines mirroring /023 funding branch at lines 2188-2280)
   - Add **dispatch banner**: `[iter-v1/034] BASIS-Z30 ACTIVE: basis_zscore_30@<pos> / <total> features`
   - Add **pre-flight assert**: `assert "basis_zscore_30" in active_feature_columns`
   - **Add `"v1-034"`** to BASELINE catch-all exclusion tuple at line 3408 (`/030 LESSON enforcement`)
   - 4 model dispatch (Model A pool / C / D / E) — identical to /023 spec, NO atr or R changes

### Section 3.2 — Feature regeneration (Phase 6 step 0)

Pre-backtest, regenerate v1 features so basis_zscore_30 is present in `data/features/<SYM>_8h_features.parquet`:

```bash
uv run crypto-trade features \
  --symbols BTCUSDT,ETHUSDT,LINKUSDT,LTCUSDT,DOTUSDT \
  --interval 8h \
  --track v1 \
  --groups basis_v1 \
  --format parquet \
  --workers 4
```

This invokes `add_basis_v1_features` only — no other group recomputation needed. Existing 219 columns + new `basis_zscore_30` = 220 columns total per parquet.

### Section 3.3 — CLI invocation (Phase 6 backtest)

```bash
PYTHONUNBUFFERED=1 uv run python run_baseline_v1.py \
  --pruned-features \
  --iteration-label v1-034 \
  --exploration \
  --n-trials 18 \
  --ensemble-size 3 \
  --seeds 42 \
  > logs/iter_v1_034_backtest.log 2>&1
```

Flags:
- `--pruned-features` activates `V1_FEATURE_COLUMNS_PRUNED` (now 44 cols with basis_zscore_30 in alphabetical position #1).
- `--iteration-label v1-034` triggers the `iteration_label == "v1-034"` dispatch branch.
- `--exploration` sets EXPLORATION default sizes (n_trials=18, ENSEMBLE_SIZE=3 per `V1_EXPLORATION_ENSEMBLE_SIZE`).
- `--seeds 42` outer seed single-pass.

### Section 3.4 — Symbols + universe + model config

| Item | Spec |
|---|---|
| Universe | V1_BASELINE_UNIVERSE (BTC/ETH/LINK/LTC/DOT) UNCHANGED |
| Models | A (BTC+ETH pool, atr_tp=2.9, atr_sl=1.45, R1=OFF, R3=ON), C (LINK, atr_tp=3.5, atr_sl=1.75, R1=ON, R3=ON), D (LTC, atr_tp=3.5, atr_sl=1.75, R1=ON, R3=ON), E (DOT, atr_tp=3.5, atr_sl=1.75, R1=ON, R2=ON, R3=ON) — IDENTICAL to baseline |
| Labels | triple-barrier σ_t EWMA 14d UNCHANGED |
| Features | V1_FEATURE_COLUMNS_PRUNED 44 cols (43 + basis_zscore_30) |
| Sample weight | `abs_pnl` (baseline default) — NO composite_inv_concurrency (cycle-5 isolated axis) |
| Optuna bounds | `v1_pruned` (NOT axis016 — basis is feature-add, not weight-mode change) |
| n_trials | 18 |
| Inner ensemble | 3 seeds (V1_EXPLORATION_ENSEMBLE_SIZE) |
| Outer seed | 42 (single) |
| Walk-forward | training_months=24, monthly retrain, embargo via walk_forward.py:113 fix |
| OOS_CUTOFF | 2025-03-24 (sacred) |

### Section 3.5 — File changes (anticipated diff sizes)

| File | Change | Approx LOC |
|---|---|---|
| `src/crypto_trade/features_v1/basis_v1.py` | NEW | ~150 |
| `src/crypto_trade/features_v1/__init__.py` | INSERT 1 line + update assert | +2 −1 |
| `src/crypto_trade/features/__init__.py` | INSERT 4 lines (import + register) | +4 |
| `run_baseline_v1.py` | INSERT dispatch + exclusion-tuple add | +90 |
| `tests/features_v1/test_basis_v1.py` | NEW | ~120 |
| `tests/test_iteration_v1_034.py` | NEW | ~140 |

### Section 3.6 — Wall-clock estimate (5-step scaling per `feedback_v1_label_rate_wall_clock_scaling.md`)

**Step 1 — Anchor precedent**: iter-v1/016 (sample-weighting EXPLORATION; same v1 standard `--exploration --n-trials 18 --ensemble-size 3 --seeds 42 --pruned-features`).
- /016 wall-clock observed: ~50 min compute (5 models × ~10 min/model × ~1.0× pruned-features cost factor).

**Step 2 — Anchor label count**: ~810 IS + OOS trades over 53 months × 5 syms.

**Step 3 — /034 expected label count**: feature-add does NOT alter triple-barrier labels or universe → expected label count BIT-NEAR-IDENTICAL to BASELINE_V1 (621 IS / 189 OOS); label-rate factor ≈ 1.0.

**Step 4 — Scaling factors**:
- ENSEMBLE_SIZE = 3 inner / 3 inner anchor = 1.0
- n_trials = 18 / 18 anchor = 1.0
- Outer seed = 1 / 1 anchor = 1.0
- Feature count = 44 / 43 anchor = 1.02 (negligible cost)
- Label-rate = 1.0
- **Composite scaling factor = 1.02×**

**Step 5 — Projection**: 50 min × 1.02 = **~51 min modal compute**.

**Total wall-clock**:
- Data fetch: **0 min** (perp + spot 8h CSV already on disk; verified Phase 1).
- Feature regen for basis_v1 group: ~5 min (`uv run crypto-trade features ... --groups basis_v1` is single-group; 5 symbols × <1 min/symbol since it's just a CSV read + rolling math).
- Backtest compute: ~51 min.
- Report layer (DSR/PSR/etc): ~3 min.

**Modal total: ~60 min (1.0h).**
**Conservative band: 50-80 min (under 1.5h target).**

No kill-switch (per cycle-5 directive); honest overrun acceptable.

### Section 3.7 — Phase 6 step-sequence

1. Implement `basis_v1.py` + features registry + V1_FEATURE_COLUMNS_PRUNED + dispatch + exclusion-tuple ADD + tests
2. Run tests `uv run pytest tests/features_v1/test_basis_v1.py tests/test_iteration_v1_034.py -v` — ALL must pass
3. Regenerate features parquet for basis_v1 group (5 syms)
4. Verify parquet contains `basis_zscore_30` column with non-null fraction > 95%
5. Launch backtest with the CLI in §3.3
6. After backtest: verify dispatch banner printed; verify `[iter-v1/034]` log lines present (catch-all exclusion working)
7. Read `comparison.csv` for verdict on F1

---

## Section 4 — Verdict Matrix

| F1 (OOS Δ) | F-AXIS #3 importance | F-AXIS #4 per-sym | F-AXIS #5 Spearman | Verdict | Cycle-5 routing |
|---|---|---|---|---|---|
| ≥ +0.50 | rank ≤ 22 median | ≥3/5 syms +OOS | > 0.80 | PROMISING-CLEAN | bundle component candidate for /044 |
| +0.20 to +0.50 | rank ≤ 22 median | ≥3/5 syms +OOS | > 0.80 | PROMISING | bundle candidate; cycle-5 advances /035 |
| +0.20 to +0.50 | rank 30-44 | mixed | < 0.50 | PROMISING-BASIN-RELOCATION-ARTIFACT | /036 isolation step (frozen-HP) |
| -0.10 to +0.20 | rank 30-44 | mixed | > 0.50 | INERT | /035 NEW family next |
| -0.30 to -0.10 | rank 14/14 some cells | <3/5 syms +OOS | varies | NEGATIVE-no-effect | basis CLOSED at v1 EXPLORATION; /035 OI velocity proceeds |
| < -0.30 | varies | <2/5 +OOS | varies | NEGATIVE-CATASTROPHIC | basis CLOSED; cycle-5 routing audit |

---

## Section 5 — Risk Mitigation

Per `feedback_risk_mitigation_design.md`: every merge-candidate iteration must include a Risk Mitigation section. /034 is EXPLORATION not merge-candidate, but discipline applies — Section 5 documents what risk semantics will look like IF /034 graduates to bundle-inclusion at /044 CONFIRMATION.

| Risk Layer | Status | Rationale |
|---|---|---|
| **R1 Consecutive-SL cool-down** | UNCHANGED (active C/D/E, off A) | Independent of feature-add |
| **R2 Drawdown brake** (Model E) | UNCHANGED | Independent of feature-add |
| **R3 OOD Mahalanobis** | UNCHANGED (active all 4 models, cutoff 0.70, 16 features) | V1_OOD_FEATURE_COLUMNS is decoupled per features_v1/__init__.py — basis is NOT added to OOD set (basis dispersion is regime-dependent; including in OOD would compress effective cutoff) |
| **NEW basis-extreme guard** (DESIGN-ONLY; not in /034) | DEFERRED to /044 | If /034 PROMISING, consider gate: "if |basis_zscore_30| > 4 at entry, scale position by 0.5x" to avoid catastrophic squeeze entries during basis-tail regimes. NOT implemented in /034 — single-axis isolation. |

---

## Section 6 — Risk Management Table

| Risk | Likelihood | Severity | Mitigation |
|---|---|---|---|
| `basis_zscore_30` not in parquet at training time | LOW (regeneration runs in §3.7 step 3) | HIGH (silent NaN-fill could pass tests) | Pre-flight assert in dispatch branch: `assert "basis_zscore_30" in active_feature_columns`; KeyError if column missing from parquet via LightGbmStrategy. |
| BASELINE catch-all silent-fallback (no `v1-034` exclusion) | MEDIUM (recurring /030 + /033 defect) | HIGH (entire backtest runs but reports BASELINE numbers) | Explicit exclusion add at line 3408 + test `test_baseline_catchall_excludes_v1_034`. |
| Spot data extends to 2026-05-18 but perp goes to 2026-05-27 | LOW (well outside training_months=24 window) | LOW (OOS window ends 2026-05; merge is inner join → uses min extent) | Inner join in `compute_basis_zscore`; merge will gracefully drop ~9 bars of post-spot-end perp data. |
| Look-ahead bias via basis_bps[t] using bar-close perp + bar-close spot | NONE | NONE | Both bar-close prices ARE knowable at bar close by definition; same convention as funding_v1 (where rate[t] settled at bar open is past-only); the rolling denominator is `.shift(1)` so bar-t's own basis_bps is excluded from its own z-score denominator. Unit-tested in `test_basis_v1.py`. |
| Burn-in NaN propagation into trade decisions | LOW (LightGBM handles NaN natively; first 30 bars per symbol) | LOW | The first 30 bars (10 days) are NaN; baseline already has burn-in for 14-day EWMA σ_t. No bars in IS train start before 2020-01-31 due to 30-bar warm-up. |
| Spot CSV missing/corrupt for any symbol | LOW (verified in Phase 1) | MEDIUM | Code raises FileNotFoundError; pre-flight script will print clear error before backtest start. |

---

## Section 7 — Failure-mode Prediction

Per `feedback_v3_axis_saturation_predictor.md` — must predict behavioral effects, with falsifier if observed deviates.

**Predicted IS trade count change**: ±5% from baseline 621 IS trades (range [560, 690] = F2 band). NEW feature add slightly perturbs Optuna's basin selection but does not change label generation.

**Predicted OOS trade count change**: ±10% from baseline 189 OOS trades (range [170, 215]). NEW feature can introduce small directional gating depending on what LightGBM learns; the threshold-effect through R3 OOD gate may be slightly amplified.

**Predicted basis_zscore_30 importance rank**: median rank 8-15/44 across (Model, OOS month) cells. Mechanism: basis_zscore_30 captures positioning regime independently of OHLCV-derived features; LightGBM should select it within the top 1/3 of splits in most cells. NOT expected to dominate (rank 1) given correlated existing features (trend_plus_di_14, mom_rsi_14).

**Predicted per-symbol OOS Δ direction**: ETH/LTC positive (signed Pearson +0.11); LINK mild (Q2-Q3 productive but not signed-PnL-correlated); BTC flat; DOT possibly negative (inverted Q5 effect).

**FALSIFIER**: if observed importance rank for `basis_zscore_30` is 30-44 (bottom third) in ≥4/5 walk-forward OOS months → reclassify INERT and feature does NOT carry forward to /044 CONFIRMATION bundle. If rank 14/14 in ≥4/5 months → basis axis CLOSED at v1.

---

## Section 8 — Verdict Cell Determination

Verdict is determined by F-AXIS #1 (binary primary), with F2-F5 as diagnostic on mechanism:

```
IF OOS Δ ≥ +0.20 AND IS Δ ≥ +0.20 AND OOS trades ∈ [145, 215] AND
   importance rank median ≤ 22/44 AND ≥3/5 syms +OOS Δ:
    → EXPLORATION-PROMISING
    → /034 axis added to /044 CONFIRMATION bundle substrate

ELSE IF OOS Δ ∈ [-0.10, +0.20]:
    → EXPLORATION-INERT
    → cycle-5 advances to /035 OI velocity (next priority axis)

ELSE IF OOS Δ < -0.10:
    → EXPLORATION-NEGATIVE (band per F1 table)
    → basis CLOSED for v1 cycle-5

ELSE IF OOS trades < 145 OR importance rank confirms silent-fallback:
    → BLOCK-PENDING-FIX (technical defect — pre-Phase-7.5 reroute)
```

---

## Section 9 — Library Stack

- `pandas` (already in deps): CSV read + rolling stats
- `numpy` (already in deps): clip + arithmetic
- `pyarrow` (already in deps): parquet round-trip
- `scipy.stats` (already in deps): pearsonr + spearmanr (EDA only, not runtime)
- `statsmodels.tsa.stattools.adfuller` (already in deps): ADF test (EDA only, not runtime)
- NO new deps required.

---

## Section 10 — Symbol Exclusion + Reproducibility + Test Mandate

### Section 10.1 — Symbol exclusion

V1_BASELINE_UNIVERSE unchanged (BTC/ETH/LINK/LTC/DOT). No symbols added or removed. V1_EXCLUDED_SYMBOLS unchanged.

### Section 10.2 — Reproducibility

- Single outer seed = 42 (matches baseline canonical seed)
- ENSEMBLE_SIZE = 3 inner seeds (selected from BASELINE_V1 5-seed roster: 42, 123, 456 — first 3 per `V1_EXPLORATION_ENSEMBLE_SIZE` ordering convention)
- Optuna sampler: TPE with random_state=outer_seed (deterministic per (cell, seed))
- Walk-forward: monthly retrain on training_months=24 window, embargo via `walk_forward.py:113` fix

Two re-runs from a clean checkout must produce bit-identical `trades.csv` per `feedback_deterministic_trade_match.md`. Smoke-tested at Phase 6 step 1.

### Section 10.3 — Test mandate (8+ tests per `/030 LESSON`)

**Mandatory** (8+ tests; 9 planned):

`tests/features_v1/test_basis_v1.py`:
1. `test_compute_basis_zscore_past_only` — bar t's own basis_bps does NOT enter its own rolling denominator (lookahead guard).
2. `test_compute_basis_zscore_known_values` — sample-instance assertion: hand-computed z-score on a 32-row synthetic series matches `compute_basis_zscore` output to <1e-9.
3. `test_compute_basis_zscore_clip` — outlier basis_bps (>10000 bps) gets clipped to ±10.0 in z output.
4. `test_compute_basis_zscore_burn_in_nan` — first `window-1` bars are NaN (rolling warm-up).
5. `test_add_basis_v1_features_missing_spot_raises` — FileNotFoundError raised when spot CSV missing.
6. `test_add_basis_v1_features_btc_smoke` — runs on real BTC data; output has `basis_zscore_30` column; non-null fraction > 95% after burn-in.

`tests/test_iteration_v1_034.py`:
7. `test_v1_034_dispatch_banner` — runner with `iteration_label="v1-034"` prints `[iter-v1/034] BASIS-Z30 ACTIVE` line.
8. `test_v1_034_in_baseline_catchall_exclusion` — line-3408 tuple contains `"v1-034"` (catch-all guard per `/030 LESSON` `feedback_v1_dispatch_baseline_catchall_exclusion.md`).
9. `test_v1_034_dispatch_branch_exists` — runner code path `iteration_label == "v1-034"` is reachable (existence check via `inspect.getsource(run_baseline_v1)`).

ALL 9 tests must pass at Phase 6 before backtest launch.

### Section 10.4 — Anti-cheating self-check

- IS-only window for ALL EDA + Phase 1-5 work. Confirmed via `IS_START_MS = 1577836800000` and `OOS_CUTOFF_MS = 1742774400000` in `analysis/iteration_v1-034/*.py`.
- OOS data NOT inspected during Phases 1-5.
- IS window NOT trimmed; full 2020-01 → 2025-03-23 used for EDA.

### Section 10.5 — Phase 5.5 dispatch readiness

- Brief committed at HEAD.
- EDA scripts committed at `analysis/iteration_v1-034/`.
- BASELINE catch-all exclusion tuple ADD planned (Phase 6 first commit).
- Test suite mandate documented.
- Wall-clock target 1.5h modal (modal estimate 1.0h compute) — well INSIDE skill default 2h cap.

Ready for Phase 6 dispatch.

---

**END OF BRIEF**
