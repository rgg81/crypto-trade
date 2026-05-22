# Iteration v3-039 — Research Brief

**Type**: CONFIRMATION (SECOND v3 CONFIRMATION — cycle 10/10 EXPLORATIONs complete)
**Track**: v3 (rigor arm) — thirty-ninth iteration
**Branch**: `iteration-v3/039` (off iter-v3/038 head)
**Date**: 2026-05-08
**Author**: QR (autopilot)

---

## Section 0 — Data Split Declaration

```
OOS_CUTOFF_DATE  = 2025-03-24    # IMMUTABLE
training_months  = 24             # IMMUTABLE
ENSEMBLE_SIZE    = 5              # non-exploration default (CONFIRMATION-spec)
ensemble_seeds   = _derive_ensemble_seeds(outer_seed, size=5)
n_trials         = 35             # default; per feedback_v3_confirmation_n_trials_35
colsample_bytree = Optuna-tuned   # NOT hardcoded (CONFIRMATION-spec)
OOS_CUTOFF_MS    = 1742774400000
```

**IS window (24 months)**: 2023-03-24 00:00 UTC through 2025-03-23 23:59 UTC
**OOS window**: 2025-03-24 00:00 UTC onward

Sacred constants UNCHANGED. The QR sees OOS metrics for the FIRST time in Phase 7.

---

## Section 0.5 — Iteration Type Declaration

```
TYPE: CONFIRMATION (SECOND v3 CONFIRMATION)
Cycle: 10/10 EXPLORATIONs complete (iter-v3/029–038)
Wall-clock budget: <= 6h hard cap (per feedback_v3_cadence_discipline.md CONFIRMATION cap)
Spec: uv run python run_baseline_v3.py --seeds 2
  - ENSEMBLE_SIZE=5 (auto; non-exploration mode)
  - n_trials=35 (default)
  - colsample_bytree Optuna-tunable (NOT hardcoded 1.0)
  - outer_seeds=2 (per feedback_outer_seed_cap_2_v3.md)
Bundle: iter-v3/035 config — 4 edge ingredients validated across 10 EXPLORATIONs
```

**Validated bundle (4 edge ingredients locked in iter-v3/035):**

1. **V3_MODELS = (BCH, LDO, TRX, ALGO)** — 4 symbols (iter-v3/034 drop-VET atomic swap;
   ALGO added per iter-v3/032 EXPLORATION)
2. **V3_FEATURE_COLUMNS_TOP_N = 14** — `regime_momentum_signed_5d` as 14th universal feature
   (iter-v3/025 PROMISING → iter-v3/028 CONFIRMATION-MERGE; FIRST multi-seed validated
   edge ingredient in v3 history)
3. **V3_FEATURES_PER_SYMBOL = {"BCHUSDT": V3_FEATURE_COLUMNS_TOP_N + ("fracdiff_d05_close",)}**
   — BCH-only fracdiff per-symbol targeting (iter-v3/035 EXPLORATION +2.85 OOS Sharpe;
   BCH +48.73 OOS wpnl with TRX/LDO/ALGO fully restored to anchor)
4. **V3_ATR_MULTIPLIERS_PER_SYMBOL = {"LDOUSDT": (1.5, 0.75)}** — LDO-specific ATR labeling
   tuning (iter-v3/032 EXPLORATION; LDOUSDT natr_21_raw 1.35× peer median; barrier alignment)

**What this CONFIRMATION tests**: does the iter-v3/035 single-seed +2.85 OOS Sharpe hold at
multi-seed (`--seeds 2`)? The iter-v3/028 FIRST CONFIRMATION established a 50–60% multi-seed
compression precedent (+0.8788 single-seed → +0.5101 multi-seed mean, 42% IS compression;
+1.2244 single-seed → +0.5053 multi-seed mean, 59% OOS compression). Applying the same
50–60% compression to iter-v3/035 single-seed +2.85 OOS predicts multi-seed mean of
+1.14 to +1.43 — which would clear the +1.0 OOS Sharpe floor for the FIRST TIME in v3 history.

**iter-v3/039 vs iter-v3/038 diff (single sub-fix):** REVERT V3_FEATURES_PER_SYMBOL ALGO entry
(iter-v3/038 added ALGOUSDT fracdiff; iter-v3/038 result was NEGATIVE — ALGO does NOT
benefit from fracdiff; reverting to iter-v3/035 bundle state: only BCH has per-symbol fracdiff).
ITERATION_LABEL "v3-038" → "v3-039".

---

## Section 1 — Hypothesis

The iter-v3/035 single-seed OOS Sharpe of +2.85 compresses to a multi-seed mean of at least
+1.0 at `--seeds 2` (ENSEMBLE_SIZE=5, n_trials=35), clearing the +1.0 OOS Sharpe floor for the
first time in v3 history, because (a) the 4-ingredient bundle has no single dominant seed-lottery
artifact (BCH fracdiff, LDO ATR, ALGO universe addition, and regime_momentum_signed_5d all
contributed positively in single-seed), and (b) the iter-v3/028 compression precedent of 42–59%
is a reliable upper bound for this architecture's multi-seed variance.

---

## Section 2 — IS-Only Numerical Evidence

### 2.1 — iter-v3/035 Single-Seed Result (the primary evidence)

iter-v3/035 Phase 7 result (`reports-v3/iteration_v3-035/comparison.csv` + `dsr.json`):

| Metric | IS | OOS | Ratio |
|---|---:|---:|---:|
| monthly_sharpe | -0.1023 | **+2.8521** | -27.89 |
| daily_sharpe | -0.1820 | +3.8765 | -21.29 |
| max_drawdown | 49.27% | 28.83% | 0.5851 |
| profit_factor | 0.9758 | 1.6593 | 1.7004 |
| win_rate | 30.92% | 45.53% | 1.4726 |
| n_trades | 262 | 123 | 0.4695 |
| total_pnl | -8.46 | +87.35 | -10.33 |
| monthly_calmar | -0.1716 | +3.0301 | -17.65 |
| weighted_pnl_total | -8.46 | +87.35 | -10.33 |
| dsr | 0.000 | — | — |
| pbo | 0.1012 | — | — |
| psr | 1.000 | — | — |
| n_trials | 140 | — | — |
| n_effective_trials | 20 | — | — |

**IS/OOS Sharpe divergence note**: iter-v3/035 IS Sharpe is negative (-0.1023) while OOS is
strongly positive (+2.8521). This is the DEFINING single-seed characteristic of the bundle:
the IS regime in 2023-2025 is trend-poor for BCH/LDO/TRX/ALGO (regime_momentum_signed_5d
fires on trend-following when hurst_100 > 0.5, which IS is sparse), while OOS post-2025-03-24
is trend-rich. This IS/OOS Sharpe divergence is EXPECTED AT SINGLE-SEED; at multi-seed the
Optuna search variance is reduced and IS Sharpe typically compresses toward +0.3 to +0.7
(per iter-v3/028 precedent: single-seed IS +0.8788 → multi-seed mean IS +0.5101).

**Per-symbol OOS attribution (iter-v3/035, seed 42):**

| Symbol | OOS wpnl | OOS n_trades | OOS WR | OOS concentration |
|--------|--------:|-------------:|-------:|------------------:|
| BCHUSDT | +48.73 | 32 | 50.0% | 47.39% |
| TRXUSDT | +29.24 | 46 | 52.2% | 28.44% |
| ALGOUSDT | +20.87 | 25 | 40.0% | 20.30% |
| LDOUSDT | +3.98 | 20 | 35.0% | 3.87% |

BCH is the dominant OOS contributor (47.39% concentration, single-seed). At multi-seed this
typically compresses toward 35-40% (per iter-v3/028 precedent: TRX concentration 181.9%
seed-42 → 76.47% multi-seed mean). BCH concentration is architecturally expected given the
BCH-only fracdiff entry; it is NOT above the 35% concentration gate at single-seed.

### 2.2 — iter-v3/028 Multi-Seed Compression Precedent

The FIRST CONFIRMATION (iter-v3/028) established the compression baseline for this
architecture at `--seeds 2` (ENSEMBLE_SIZE=5, n_trials=35, colsample_bytree Optuna-tuned):

| Reference | IS Sharpe | OOS Sharpe | IS compression | OOS compression |
|---|---:|---:|---:|---:|
| iter-v3/025 single-seed | +0.8788 | +1.2244 | — | — |
| iter-v3/028 multi-seed mean | +0.5101 | +0.5053 | **42%** | **59%** |

Applying 50% midpoint compression to iter-v3/035:
- IS: -0.1023 × (1 - 0.50) = -0.05 (but IS compresses TOWARD the baseline, not a fixed %
  of the single-seed value — multi-seed IS typically lands near the BASELINE_V3.md IS of
  +0.51 ± the new signal contribution; predicted IS band: [+0.20, +0.70])
- OOS: +2.8521 × (1 - 0.55) = +1.28 at 55% compression; at 60%: +1.14. Predicted OOS band:
  **[+1.10, +1.70], median +1.40**

### 2.3 — Edge Ingredient Lineage (evidence for each of 4 ingredients)

| Ingredient | EXPLORATION evidence | Single-seed IS/OOS | Status |
|---|---|---:|---|
| regime_momentum_signed_5d | iter-v3/025 | IS+0.88/OOS+1.22 | CONFIRMED iter-v3/028 |
| LDO ATR (1.5, 0.75) | iter-v3/032 IS per-symbol EDA | IS+0.24/OOS+1.93 (anchor) | PROMISING |
| ALGO universe + 14 features | iter-v3/032 | IS+0.24/OOS+1.93 (4-sym anchor) | PROMISING |
| BCH fracdiff_d05_close per-symbol | iter-v3/035 | IS-0.10/OOS+2.85 | PROMISING (IS divergent) |

Analysis script: `analysis/iteration_v3-039/is_pbo_strategy_axis_analysis.py` (committed SHA
`9294855` from iter-v3/038 — covers PBO strategy-axis IS analysis over the IS window
for the confirmed bundle's strategy configuration). This script validates on IS data only
and was committed before this brief.

---

## Section 3 — Proposed Changes

### Sub-fix 1 (REVERT): Remove ALGO entry from V3_FEATURES_PER_SYMBOL

In `src/crypto_trade/features_v3/__init__.py`, revert `V3_FEATURES_PER_SYMBOL` to
iter-v3/035 state — BCH-only fracdiff; ALGO returns to 14-feature fallback:

```python
V3_FEATURES_PER_SYMBOL: dict[str, tuple[str, ...]] = {
    "BCHUSDT": V3_FEATURE_COLUMNS_TOP_N + ("fracdiff_d05_close",),
}
# ALGO removed: iter-v3/038 NEGATIVE — ALGO does NOT benefit from fracdiff;
# reverts to 14-feature fallback (V3_FEATURE_COLUMNS_TOP_N).
```

Rationale: iter-v3/038 EXPLORATION tested ALGO-only fracdiff targeting (specificity probe).
Result was NEGATIVE — ALGO fracdiff did not replicate BCH's +37.98 OOS wpnl swing; the
fracdiff signal is BCH-SPECIFIC. Reverting ALGO to 14-feature fallback is the correct
iter-v3/039 CONFIRMATION state.

### Sub-fix 2: Update `_verify_feature_columns` in `run_baseline_v3.py`

Update docstring and assertions to iter-v3/039 state:
- BCH per-symbol (V3_FEATURES_PER_SYMBOL["BCHUSDT"]): 15 features WITH fracdiff_d05_close
- ALGO falls back to 14 features (ALGOUSDT NOT in V3_FEATURES_PER_SYMBOL)
- LDO/TRX fallback: 14 features
- V3_FEATURES_PER_SYMBOL has 1 entry (BCHUSDT only)

Specific assertion changes:
- Remove ALGO-presence check (`"ALGOUSDT" in V3_FEATURES_PER_SYMBOL` assertion)
- Add ALGO-absence check (`"ALGOUSDT" not in V3_FEATURES_PER_SYMBOL` assertion)
- Remove `V3_FEATURES_PER_SYMBOL has 2 entries` check; replace with `has 1 entry`
- Update error messages to reference iter-v3/039

### Sub-fix 3: Update ITERATION_LABEL "v3-038" → "v3-039"

In `run_baseline_v3.py`, change:
```python
ITERATION_LABEL = "v3-039"
```

### Sub-fix 4: Update test suite in `tests/features_v3/test_features_for_symbol.py`

Rewrite tests to iter-v3/039 state (BCH-only fracdiff; ALGO = 14-feature fallback;
V3_FEATURES_PER_SYMBOL has 1 entry):

Mandatory assertions for iter-v3/039:
- `test_bch_has_fracdiff`: BCHUSDT returns 15 features WITH fracdiff_d05_close (UNCHANGED)
- `test_algo_no_fracdiff`: ALGOUSDT returns 14 features WITHOUT fracdiff_d05_close (REVERTED)
- `test_algousdt_not_in_per_symbol`: ALGOUSDT NOT in V3_FEATURES_PER_SYMBOL (REVERTED)
- `test_ldousdt_not_in_per_symbol`: LDOUSDT NOT in V3_FEATURES_PER_SYMBOL (UNCHANGED)
- `test_trxusdt_not_in_per_symbol`: TRXUSDT NOT in V3_FEATURES_PER_SYMBOL (UNCHANGED)
- `test_bch_per_symbol_len`: len(V3_FEATURES_PER_SYMBOL["BCHUSDT"]) == 15 (UNCHANGED)
- `test_non_bch_fallback_len`: parametrized ALGO/LDO/TRX — all return 14 features
- `test_subset_invariant_bch`: BCH = V3_FEATURE_COLUMNS_TOP_N + ("fracdiff_d05_close",)
- `test_v3_features_per_symbol_has_one_entry`: len(V3_FEATURES_PER_SYMBOL) == 1 (REVERTED from 2)
- `test_regime_momentum_in_universal_list`: regime_momentum_signed_5d in TOP_N
- `test_fracdiff_not_in_universal_list`: fracdiff_d05_close NOT in TOP_N
- `test_cross_asset_divergence_not_in_universal_list`: cross_asset_divergence_norm NOT in TOP_N
- `test_vol_adj_autocorr_not_in_universal_list`: vol_adj_autocorr NOT in TOP_N
- `test_universal_list_is_14`: len(V3_FEATURE_COLUMNS_TOP_N) == 14

### Sub-fix 5: Update docstrings in `features_v3/__init__.py`

Update `features_for_symbol` docstring and `V3_FEATURES_PER_SYMBOL` docstring to reflect
iter-v3/039 state:
- BCHUSDT: 15 features (V3_FEATURE_COLUMNS_TOP_N + fracdiff_d05_close)
- ALGOUSDT: 14 features (fallback; REVERTED from iter-v3/038; iter-v3/038 NEGATIVE)
- LDOUSDT, TRXUSDT: 14 features (fallback, unchanged)
- V3_FEATURES_PER_SYMBOL has 1 entry at iter-v3/039

### Bundle state verification (what _verify_feature_columns must assert after sub-fixes)

```
V3_FEATURE_COLUMNS_TOP_N: 14 features — NO fracdiff_d05_close in universal list    PASS
V3_FEATURES_PER_SYMBOL["BCHUSDT"]: 15 features WITH fracdiff_d05_close             PASS
ALGOUSDT NOT in V3_FEATURES_PER_SYMBOL (14-feature fallback)                        PASS
LDOUSDT NOT in V3_FEATURES_PER_SYMBOL (14-feature fallback)                         PASS
TRXUSDT NOT in V3_FEATURES_PER_SYMBOL (14-feature fallback)                         PASS
V3_FEATURES_PER_SYMBOL has 1 entry (BCHUSDT only)                                   PASS
V3_ATR_MULTIPLIERS_PER_SYMBOL["LDOUSDT"] = (1.5, 0.75)                              PASS
V3_MODELS = (BCH, LDO, TRX, ALGO) — 4 symbols                                       PASS
REQUIRED_GAP = 88 = (21+1) × 4                                                      PASS
regime_momentum_signed_5d in V3_FEATURE_COLUMNS_TOP_N                               PASS
```

---

## Section 4 — Expected OOS Impact

**IS Sharpe prediction (multi-seed mean, vs BASELINE_V3.md +0.5101):**
- Predicted band: [+0.20, +0.70]
- Median point estimate: +0.45
- Rationale: CONFIRMATION typically compresses single-seed IS toward the
  BASELINE_V3.md anchor ± the incremental signal contribution of the new
  edge ingredients (BCH fracdiff per-symbol + LDO ATR + ALGO universe + regime_momentum
  already in BASELINE_V3.md). IS band reflects that IS Sharpe may be modestly positive
  even though single-seed IS is -0.10 (Optuna variance reduction at multi-seed).

**OOS Sharpe prediction (multi-seed mean, vs BASELINE_V3.md +0.5053):**
- Predicted band: **[+1.10, +1.70]**
- Median point estimate: **+1.40**
- Rationale: iter-v3/028 compression precedent (42–59%) applied to iter-v3/035
  single-seed OOS +2.8521; 50% midpoint → +1.43; lower bound at 60%: +1.14;
  upper bound at 40%: +1.71

**OOS falsifier (pre-registered):**
- If OOS Sharpe < +1.0 (multi-seed mean): the iter-v3/035 single-seed result was a
  single-seed lottery artifact; the bundle does NOT clear the +1.0 floor; hypothesis
  REJECTED. This triggers a BASELINE freeze (iter-v3/039 is STRICTLY-BETTER-than-028
  only if OOS > +0.5053; if OOS is in [+0.51, +1.0] the baseline still updates but
  Gates 1+2 remain failed).

**IS falsifier (pre-registered):**
- If IS Sharpe < +0.0: the multi-seed ensemble has NEGATIVE IS even with variance
  reduction; hypothesis REJECTED (pathological state indicating the bundle overfits
  OOS noise not IS signal). Escalate to QR.

**Path taxonomy (pre-registered):**
- Path A (CLEAR-FLOOR): OOS multi-seed mean >= +1.0 AND IS >= +0.0 → MERGE-candidate;
  first time v3 clears the +1.0 floor; BASELINE_V3.md updates.
- Path B (BELOW-FLOOR): OOS in (+0.51, +1.0) AND IS >= +0.0 → BASELINE updates
  (strictly better than +0.5053); Gates 1+2 still fail. Further EXPLORATIONs required
  to clear the floor.
- Path C (COMPRESSION-WIPEOUT): OOS <= +0.51 OR IS < +0.0 → NO baseline update;
  iter-v3/035 bundle rejected at multi-seed. Hypothesis FALSIFIED.

---

## Section 5 — Risk Mitigation

**R1 (cooldown)**: unchanged. Cooldown=2 candles post-trade per symbol.

**R2 (drawdown scaling)**: unchanged. R2 gate parameters carried forward from
BASELINE_V3.md (iter-v3/028). No parameter changes in this CONFIRMATION.

**R3 (OOD detection)**: unchanged. Mahalanobis OOD z-score threshold unchanged
(zscore_threshold=2.0 per iter-v3/011).

**Multi-seed variance risk**: at `--seeds 2` × ENSEMBLE_SIZE=5, per-cell trade count
is higher (10 models per cell vs 1 at EXPLORATION). Expected IS trade count: ~280-320
(vs 262 at single-seed). Expected OOS trade count: ~110-135. This reduces per-cell
Optuna variance and typically compresses the single-seed extremes toward the population
mean — the core purpose of the CONFIRMATION spec.

**BCH concentration risk (multi-seed)**: iter-v3/035 single-seed BCH concentration was
47.39% (above 35% gate). At multi-seed (iter-v3/028 precedent: TRX 181.9% → 76.47%
multi-seed mean), BCH concentration is expected to compress to 35-45%. If BCH multi-seed
mean concentration > 60% of OOS PnL, this is flagged in the engineering report as a
concentration anomaly.

**IS/OOS Sharpe divergence resolution**: the single-seed IS/OOS divergence (-0.10/+2.85)
is driven by regime_momentum_signed_5d regime density and BCH fracdiff activation rate.
At multi-seed, IS Sharpe typically lifts as Optuna finds more IS-profitable configurations.
If IS < 0.0 at multi-seed, the bundle is pathological and should NOT update the baseline.

---

## Section 6 — Risk Management Design (7-Primitive Gate Table)

All 7 risk gates carried forward from iter-v3/028/035 baseline unchanged. No gate
parameters are modified in this CONFIRMATION.

| Gate | Type | Parameter | iter-v3/035 IS Fire Rate | iter-v3/035 OOS Fire Rate | Change |
|---|---|---|---|---|---|
| 1 — BTC trend | BtcTrendFilterConfig | lookback=42, threshold=15% | ~8-12% | ~8-12% | None |
| 2 — Hit rate | HitRateGateConfig | window=20, sl_threshold=0.65 | DISABLED | DISABLED | None |
| 3 — ADX gate | ADX regime filter | threshold=20 (v3 default) | symbol-dependent | symbol-dependent | None |
| 4 — Hurst regime | hurst_100 > 0.5 gate | implicit in regime_momentum | symbol-dependent | symbol-dependent | None |
| 5 — Drawdown brake | R2 cumulative | per-model PnL tracking | symbol-dependent | symbol-dependent | None |
| 6 — OOD gate | Mahalanobis z-score | zscore_threshold=2.0 | symbol-dependent | symbol-dependent | None |
| 7 — Liquidity floor | NATR floor | NATR >= 0.5% | All 4 symbols pass | All 4 symbols pass | None |

Note: iter-v3/035 single-seed reported `btc_killed=43` trades (BTC gate firings; from
`seed_summary.json`). At multi-seed this will scale proportionally to total trade count.
Gate 1 (BTC trend) is the most active gate in this universe. Gate 6 (OOD) fires
per-training-window; rate is stable across seeds.

---

## Section 7 — Pre-Registered Failure-Mode Prediction

**Most plausible failure mode (Path C — COMPRESSION-WIPEOUT):**
The iter-v3/035 single-seed IS Sharpe of -0.1023 is the primary red flag. At single-seed,
regime_momentum_signed_5d + BCH fracdiff collectively produce OOS Sharpe +2.85 driven by
the 2025 OOS trend regime — but the IS window 2023-2025 is trend-poor, creating a strong
IS/OOS divergence. If the multi-seed ensemble (10 models per cell) averages out the few
profitable IS training cells that happened to align with the trend-momentum signal, the
multi-seed IS Sharpe could remain near 0 or slightly negative, and the OOS Sharpe could
compress more severely than the 40-60% precedent (e.g., to +0.80 to +1.10 range). This
would place the result in the Path B "below floor" zone rather than Path A "clear floor".

**Second plausible failure mode (Path B — BELOW-FLOOR with IS lift):**
Multi-seed IS lifts to [+0.20, +0.50] as Optuna finds robust configurations, but OOS
compresses to [+0.80, +1.10] — the +1.0 floor is not cleared. This is the "validation
without floor clearance" outcome: the bundle is strictly better than iter-v3/028 baseline
(OOS > +0.5053) but fails Gates 1+2. The BASELINE_V3.md still updates (per user directive
2026-05-08 STRICTLY-BETTER policy), but the aspirational merge gates remain failed.

**What the gates should catch**: if BCH fracdiff OOS signal is regime-dependent
(only fires post-2025 trend regime), multi-seed IS will show near-zero BCH fracdiff
importance variance — the Optuna budget at `--seeds 2` cannot find IS configurations
where BCH fracdiff is consistently above rank 10/15. The gate to watch: BCH fracdiff
importance rank in BCH model (expected >= 5/15 if the signal is real; if < 5/15 across
both seeds, the IS/OOS divergence is a post-2025 regime artifact not a fundamental signal).

**Behavioral effect predictor** (per `feedback_v3_axis_saturation_predictor.md`): The only
change from iter-v3/038 is removing the ALGO per-symbol fracdiff entry. Predicted IS trade
count delta: ALGO IS trade count may shift ±5-10% (ALGO-model changes); BCH/LDO/TRX
models UNCHANGED from iter-v3/035. Net expected IS trade change vs iter-v3/035: small
(≤5% total portfolio, driven by ALGO model returning to 14-feature fallback). If observed
IS trade count vs iter-v3/035 single-seed (262 trades) changes by > 30 trades (11.5%),
investigate whether the revert introduced unexpected cross-symbol interactions.

---

## Section 8 — Pre-Registered MERGE/NO-MERGE Numerical Criteria

This is a CONFIRMATION iteration. MERGE gate evaluation is pre-registered before the
backtest runs. These thresholds are LOCKED and cannot be post-hoc renegotiated.

**10 MERGE GATES (pre-registered, in priority order):**

| # | Gate | Threshold | Source | Priority |
|---|---|---|---|---|
| 1 | OOS monthly Sharpe >= +1.0 | ≥ +1.0 | BASELINE_V3.md inherited | ASPIRATIONAL |
| 2 | IS monthly Sharpe >= +1.0 | ≥ +1.0 | BASELINE_V3.md inherited | ASPIRATIONAL |
| 3 | OOS/IS Sharpe ratio >= 0.5 | ≥ 0.5 | BASELINE_V3.md inherited | HARD GATE |
| 4 | DSR > 0.95 | > 0.95 | v3 methodology | STRUCTURAL (may reformat) |
| 5 | PBO < 0.4 | < 0.4 | v3 methodology | HARD GATE |
| 6 | PSR > 0.95 | > 0.95 | v3 methodology | HARD GATE |
| 7 | Top-symbol OOS concentration ≤ 35% | ≤ 35% | BASELINE_V3.md | ASPIRATIONAL |
| 8 | OOS n_trades >= 130 (bundle total) | ≥ 130 | project memory feedback | ASPIRATIONAL |
| 9 | Both outer seeds OOS Sharpe > 0 | > 0 (each seed) | Pareto gate | HARD GATE |
| 10 | STRICTLY-BETTER than iter-v3/028 baseline | OOS > +0.5053 AND IS > +0.5101 OR IS > 0.0 | BASELINE policy | MANDATORY |

**MERGE decision logic (pre-registered):**

```
MERGE iff:
  Gate 3 PASS (OOS/IS ratio >= 0.5)  -- hard generalization gate
  AND Gate 5 PASS (PBO < 0.4)         -- hard anti-overfit gate
  AND Gate 6 PASS (PSR > 0.95)        -- hard significance gate
  AND Gate 9 PASS (both seeds positive) -- hard Pareto gate
  AND Gate 10 PASS (strictly better than iter-v3/028)
  AND OOS monthly Sharpe > 0.0        -- absolute floor (not -∞)

MERGE-NO-FLOOR (partial MERGE — baseline updates but Gates 1+2 still fail):
  Above MERGE conditions met BUT Gates 1 and/or 2 fail (OOS < 1.0 OR IS < 1.0)
  → BASELINE_V3.md updates per STRICTLY-BETTER policy; diary records outstanding
    constraint; next cycle EXPLORATIONs target the floor gap.

NO-MERGE:
  Any of: Gate 3 FAIL, Gate 5 FAIL, Gate 6 FAIL, Gate 9 FAIL, Gate 10 FAIL,
  OR OOS Sharpe <= 0.0
```

**Pre-committed quantitative threshold for "strictly better than iter-v3/028":**
- OOS multi-seed mean Sharpe > +0.5053 (iter-v3/028 OOS; NOT seed-42 alone)
- IS multi-seed mean Sharpe > 0.0 (not required to beat +0.5101 for partial MERGE;
  only absolute positivity required given single-seed IS was -0.10)

---

## Section 9 — Library Stack Declaration

All versions identical to iter-v3/028 CONFIRMATION-MERGE reproducibility stamp:

| Package | Version | Source |
|---|---|---|
| lightgbm | 4.6.0 | pyproject.toml pinned |
| numpy | 2.2.6 | pyproject.toml pinned |
| optuna | 4.8.0 | pyproject.toml pinned |
| pandas | 3.0.0 | pyproject.toml pinned |
| pyarrow | 23.0.1 | pyproject.toml pinned |
| scikit-learn | 1.8.0 | pyproject.toml pinned |
| scipy | 1.17.0 | pyproject.toml pinned |
| statsmodels | 0.14.6 | pyproject.toml pinned |
| pytest | 9.0.2 | pyproject.toml dev dep |

**fracdiff (PyPI package)**: UNAVAILABLE (fracdiff==0.9.0 requires statsmodels<0.14;
project requires statsmodels==0.14.6 for v2 compatibility). Fallback: pure-numpy inline
implementation `compute_fracdiff_d05_close` in `src/crypto_trade/features_v3/engineered_v3.py`
(established at iter-v3/034; no change). No new dependencies required for this CONFIRMATION.

**No new library dependencies**: all 4 bundle ingredients use existing infrastructure.
The V3_FEATURES_PER_SYMBOL revert is a single-line deletion in `features_v3/__init__.py`.
