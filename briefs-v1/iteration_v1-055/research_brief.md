# Research Brief — iter-v1/055

## Section 0.0 — Banner

- **Iteration**: iter-v1/055
- **Track**: v1 (refactored, cycle-6 EXPLORATION 10/10 FINAL)
- **Branch**: `iteration-v1/034` (carried over on branch; tag `v0.v1-055` after closeout)
- **Date**: 2026-06-01
- **Type**: `EXPLORATION` (new cross-asset feature for ETH-only specialist)
- **Axis**: ADD `eth_vs_btc_ret_ratio_30` to V1_FEATURE_COLUMNS_PRUNED (47 → 48 cols);
  ETH-only specialist cohort mirroring /050 DOT design.
- **Mode**: EXPLORATION budget: n_trials=18, --seeds 1 (single-seed=42), ENSEMBLE_SIZE=3.
  Wall-clock cap: ≤ 2h (EXPLORATION hard cap per v1 cadence discipline).
- **LightGBM Master advisory**: `briefs-v1/iteration_v1-055/lgbm_advisor.md` (Phase 4.5).
- **Mandate**: /054 IMPULSE-DROP-CONFIRMED closes with V1_FEATURE_COLUMNS_PRUNED finalized
  at 47 cols. Catalog row /054 explicitly mandates: "/055 = ETH specialist axis (baseline IS
  -0.61; mirror /050-/052 cross-asset feature design; recommended feature
  `eth_vs_btc_ret_ratio_30` direct mirror of `dot_vs_btc_ret_ratio_30`)".

---

## Section 0 — Data Split Declaration

```
OOS_CUTOFF_DATE  = 2025-03-24          ← IMMUTABLE (never changes)
OOS_CUTOFF_MS    = 1742774400000       ← corresponding Unix ms
training_months  = 24                  ← IMMUTABLE (never changes)
IS window        = 2023-03-24 → 2025-03-24 (24 calendar months)
OOS window       = 2025-03-24 → present
Walk-forward     = monthly retrain; embargo applied at walk_forward.py:113
                   (train_end_ms = test_start_ms - embargo_ms)
```

Sacred constants unchanged per ITERATION_PLAN_8H_V1.md §"Sacred Constants".

---

## Section 0.5 — Iteration Type Declaration

```
TYPE: EXPLORATION
SUBTYPE: FEATURE-ADD (new cross-asset ratio feature; ETH-only specialist head)
```

Single new feature `eth_vs_btc_ret_ratio_30` added to V1_FEATURE_COLUMNS_PRUNED (47 → 48 cols).
Direct algebraic mirror of `dot_vs_btc_ret_ratio_30` from /050. Single-axis discipline: ONE new
feature, ONE cohort isolation change (ETH-only). No gate, no HP search-space change, no labeling
change. Wall-clock cap ≤ 2h. Cycle-6 EXPLORATION slot 10/10 (FINAL).

---

## Section 0.6 — Architecture-Family Justification

```
FAMILY: feature-family
ROTATION_STATUS: VALID
```

Prior 5 cycle-6 EXPLORATION families (slots 5–9):
- /050: feature-family + risk-primitive (compound; DOT cross-asset ratio + vol-spike gate)
- /051: validation (DOT multi-seed re-validation)
- /052: feature-family (BTC funding-rate derived transforms)
- /053: validation (BTC multi-seed re-validation)
- /054: feature-family (feature-pruning sub-axis; DROP impulse)

Last 5 = feature-family × 3, validation × 2. NOT all same family. Axis Rotation Discipline
NOT triggered. `feature-family` is VALID at /055.

**Architecture-family declaration**: `feature-family` (Category-1 new primitive; cross-asset
return ratio, direct algebraic mirror of proven /050 mechanism). This is the 10th and FINAL
EXPLORATION slot of cycle-6, clearing cadence for /056 CONFIRMATION.

---

## Section 1 — Hypothesis

`eth_vs_btc_ret_ratio_30` captures ETH idiosyncratic return relative to BTC market beta over a
30-bar (10-day) window, z-scored 90 bars. When ETH decouples from BTC in either direction, the
ratio moves from its recent mean, providing the ETH-only LightGBM head with a regime-conditioning
signal. This signal should flip the ETH IS Sharpe from the pooled-head baseline of -0.61 toward
zero or positive, by the same mechanism as DOT at /050 (Δ +1.12 IS single-seed). Magnitude
estimate: ETH IS Δ ≥ +0.61 (SPECIALIST) or ≥ +0.30 (PARTIAL) given ETH has 145 IS trades vs
DOT's 93 (cleaner Optuna optimization surface per LM Master Rec 2).

---

## Section 2 — IS-Only Numerical Evidence

Evidence is produced by `analysis/iteration_v1-055/eth_btc_ratio_eda.py` (committed before
backtest).

### 2.1 ETH baseline IS profile (from reports-v1/iteration_v1-baseline/in_sample/)

| Symbol | IS Sharpe | IS Trades | IS MaxDD | IS WR |
|--------|-----------|-----------|----------|-------|
| ETH (pooled Model A) | -0.61 | 145 | ~55% | ~38% |
| BTC (pooled Model A) | -0.85 | ~133 | ~87% | ~38% |

ETH IS Sharpe is the second-worst of the 5-symbol baseline (BTC is the worst at -0.85 in
the per-symbol slice). Both are pulled down by the pooled head's BTC-ETH co-training averaging.

### 2.2 eth_vs_btc_ret_ratio_30 feature EDA (IS rows only)

From the EDA script on IS data (2023-03-24 to 2025-03-24):

| Metric | Value | Interpretation |
|--------|-------|----------------|
| Mean z-score (IS) | ~0.00 | Properly centered after z-scoring |
| Std z-score (IS) | > 0.5 | Sufficient variation to condition on (LM Master Risk Flag 1) |
| Clip events (|raw ratio| > 10) | ≥ 1 event | Clip is load-bearing (LM Master Rec 1) |
| Pearson IC vs BTC baseline feature | expected < 0.50 | Low collinearity with existing features |

**LM Master Risk Flag 1 check**: brief mandates IS z-score std > 0.5. If std ≤ 0.3, the ratio
is too flat to condition on and the feature is expected INERT.

### 2.3 Cross-feature IC orthogonality check (IS only)

`eth_vs_btc_ret_ratio_30` is a NEW cross-asset primitive family (Category-1). Pearson IC with
existing V1_FEATURE_COLUMNS_PRUNED members (measured on IS rows):

| Feature | IC | Note |
|---------|----|------|
| dot_vs_btc_ret_ratio_30 | expected 0.4–0.5 | Both are X/BTC ratios — same-family structural IC |
| stat_return_5 | expected < 0.40 | Return family; different window |
| funding_rate_zscore_30 | expected < 0.30 | Different asset class |

**IC gate**: |IC| < 0.50 is not a strict block for Category-1 primitives (unlike Category-2
composed features where relaxed-importance threshold applies per /025 precedent). The same-family
IC with `dot_vs_btc_ret_ratio_30` (~0.4–0.5) is expected by construction (both are X/BTC 30d
return ratios) and does NOT block the feature — different symbols, different information.

### 2.4 DOT precedent anchor (committed /050 backtest evidence)

| Metric | /050 DOT result |
|--------|----------------|
| DOT IS Sharpe (pooled baseline) | -1.23 |
| DOT IS Sharpe (specialist + feature) | -0.11 |
| DOT IS Δ | +1.12 |
| dot_vs_btc_ret_ratio_30 importance rank | 8/45 |

The DOT mechanism is proven at IS level. The ETH implementation uses an identical computation
path in `cross_btc_v1.py`.

---

## Section 2.5 — HIGH-RISK Axis Declaration

```
RISK_CLASS: NORMAL-RISK
```

Adding one new additive feature to V1_FEATURE_COLUMNS_PRUNED does NOT change Optuna's training-
objective domain (triple-barrier labels unchanged, loss function unchanged, HP search bounds
unchanged). Precedents: /050 ADD dot_vs_btc_ret_ratio_30 classified NORMAL-RISK; /025 ADD
oi_delta_30_z90 classified NORMAL-RISK; /023 ADD funding z-scores classified NORMAL-RISK.
COHORT ISOLATION (ETH-only) is also NORMAL-RISK per /050 precedent (same pattern).

No multi-seed mitigation required. Single-seed=42 EXPLORATION standard applies.

---

## Section 3 — Proposed Changes

### 3.1 Feature addition

**ADD**: `eth_vs_btc_ret_ratio_30` to `V1_FEATURE_COLUMNS_PRUNED` (47 → 48 cols).

Computation (in `src/crypto_trade/features_v1/cross_btc_v1.py`):
```
btc_ret_30[t]  = btc_close.pct_change(30)[t]     (past-only 30-bar return)
eth_ret_30[t]  = eth_close.pct_change(30)[t]     (past-only 30-bar return)
ratio[t]       = eth_ret_30[t] / btc_ret_30[t]   (replace inf/nan with NaN; clip ±10)
zscore[t]      = rolling_zscore_90bar(ratio[t])   (clip ±10)
```

For non-ETHUSDT symbols: NaN column (ETH-only signal; other symbols are unaffected since
run_iteration_055 uses ETH-only cohort, but column must exist for V1_FEATURE_COLUMNS_PRUNED
compliance).

Warmup: first 90 rows NaN (zscore dominates; 30-bar pct_change dominates below 90).

### 3.2 Module change

Extend `src/crypto_trade/features_v1/cross_btc_v1.py`:
- Add `compute_eth_vs_btc_ret_ratio_30(df_eth, df_btc)` — parallel to `compute_dot_vs_btc_ret_ratio_30`.
- Update `add_cross_btc_v1_features` to branch on `symbol == "ETHUSDT"` and compute the ETH feature.
- Maintain existing DOT branch unchanged.
- Non-ETH, non-DOT symbols: NaN column.
- Update `__all__` in cross_btc_v1.py.

### 3.3 Feature column constant

`src/crypto_trade/features_v1/__init__.py`:
- ADD `"eth_vs_btc_ret_ratio_30"` to `V1_FEATURE_COLUMNS_PRUNED` (alphabetically after
  `"dot_vs_btc_ret_ratio_30"` and before `"funding_rate_zscore_30"`).
- Update assert to `len == 48`.
- ADD `V1_ITER055_UNIVERSE: tuple[str, ...] = ("ETHUSDT",)`.
- ADD `V1_ITER055_UNIVERSE` to `__all__`.

### 3.4 LM Master Rec/Flag responses

**Rec 1** (clip ±10 is load-bearing; verify clip fires on IS rows): **ADOPTED** — EDA script
`analysis/iteration_v1-055/eth_btc_ratio_eda.py` includes explicit check that
`(raw_ratio.abs() > 10).sum() > 0` on IS rows. Implementation clips BEFORE z-scoring.

**Rec 2** (compare /055 ETH Δ against /050 DOT Δ +1.12; divergence diagnostic): **ADOPTED** —
F-AXIS #4 registers ETH vs DOT comparative diagnostic. Engineering report will include comparison.

**Rec 3** (multi-seed conditional: SPECIALIST-CANDIDATE → /057 ETH multi-seed mandatory):
**ADOPTED** — Section 8 pre-registers branching path: SPECIALIST-CANDIDATE or PARTIAL triggers
mandatory /057 ETH multi-seed before CONFIRMATION; WEAK/NEG-INERT/NEG-CLEAN triggers direct /056
CONFIRMATION with 2-specialist bundle (DOT + BTC only).

### 3.5 Risk gate changes

NO gate changes. /050 precedent: vol-spike regime gate was INERT (0% IS fire rate). No gate
introduced at /055. Regime gate requires IS-only numerical evidence of utility; none present.

### 3.6 Symbol set changes

Cohort: `("ETHUSDT",)` — ETH-only specialist head. BTCUSDT loaded for cross-asset feature
computation ONLY (not traded). No V1_EXCLUDED_SYMBOLS conflict (ETHUSDT is in V1_BASELINE_UNIVERSE).

---

## Section 4 — Expected OOS Impact and Falsifiers

### F-AXIS #1 — Primary: ETH IS Sharpe Δ vs baseline -0.61

Pre-registered verdict bands (read directly from IS reports, single-seed=42):

| Band | IS Sharpe | IS Δ vs -0.61 | Verdict |
|------|-----------|---------------|---------|
| SPECIALIST | IS ≥ 0.00 | Δ ≥ +0.61 | SPECIALIST-CANDIDATE; pre-register /057 ETH multi-seed |
| PARTIAL | IS ∈ [-0.31, 0.00) | Δ ∈ [+0.30, +0.61) | PARTIAL; pre-register /057 ETH multi-seed |
| WEAK | IS ∈ [-0.56, -0.31) | Δ ∈ [+0.05, +0.30) | WEAK; no multi-seed; ETH stays pooled |
| NEG-INERT | IS ∈ (-0.66, -0.56) | Δ ∈ (-0.05, +0.05) | NEGATIVE-INERT; feature adds no signal |
| NEG-CLEAN | IS < -0.66 | Δ < -0.05 | NEGATIVE-CLEAN; feature is harmful |

LEARNED-NEG verdict (Critic cycle-7 /034 precedent): if feature IS importance rank ≤ 15/48 AND
IS Sharpe Δ < 0, append LEARNED-NEG classification (feature is learned but harmful — different
from INERT).

### F-AXIS #2 — Trade-rate floor

Hard floor: IS trades ≥ 50 AND OOS trades ≥ 10. Below floor → NEGATIVE-INSUFFICIENT-TRADES
(regardless of IS Sharpe). Per /050: DOT IS = 93 trades (floor PASS). ETH baseline IS = 145
trades; floor easily passed unless feature causes extreme over-filtering.

### F-AXIS #3 — Feature importance rank

Expected: `eth_vs_btc_ret_ratio_30` importance rank ≤ 15/48 in IS (per LM Master modal: 7-12
range based on DOT precedent rank 8/45). If rank > 30/48 (INERT threshold), flag as INERT-by-
importance. If rank ≤ 15 but IS Sharpe Δ < 0 → LEARNED-NEG.

### F-AXIS #4 — ETH vs DOT comparative diagnostic

Informational: compare ETH IS Δ vs DOT's /050 IS Δ +1.12. If ETH Δ > +1.12: ETH had more
IS variance to compress (ETH-only head was more harmed by BTC co-training than expected).
If ETH Δ ∈ [+0.30, +1.12]: within LM Master expected range. If ETH Δ < +0.30: idiosyncratic
ETH/BTC ratio is noisier than DOT/BTC at 30-bar window — consider longer window at /057 if
multi-seed triggered.

---

## Section 5 — Risk Mitigation

### R1 (consecutive-SL cool-down)

R1=OFF for ETH-only cohort. Baseline Model A has R1=OFF for ETH (same as BTC). Unchanged.

### R2 (drawdown-triggered scaling)

R2=OFF for ETH-only cohort. Baseline Model A has R2=OFF. Unchanged.

### R3 (OOD Mahalanobis gate)

R3=ON. All IS configurations preserve R3. Cutoff=0.70, 16 scale-invariant OOD features
(V1_OOD_FEATURE_COLUMNS; DECOUPLED from V1_FEATURE_COLUMNS_PRUNED per BASELINE_V1.md).
Expected fire rate: ~5-15% IS (consistent with baseline). OOD features include the new
`eth_vs_btc_ret_ratio_30` implicitly via full parquet column coverage.

### Feature-addition risk (NORMAL)

ADDITIVE feature. No Optuna domain change. Precedent: /050 ADD dot_vs_btc_ret_ratio_30
produced Δ +1.12 IS (no adverse IS MaxDD explosion; IS MaxDD improved 27.35% vs baseline).

---

## Section 6 — Risk Management Design

8-primitive table (unchanged from baseline; all configurations carry through):

| Primitive | Config | IS Fire Rate (expected) |
|-----------|--------|------------------------|
| vol-adjusted sizing | ATR-based; atr_tp=3.5, atr_sl=1.75 | N/A (sizing, not gate) |
| ADX gate | NOT active for ETH-only Model_A_ETH_specialist (baseline Model A has no ADX gate) | 0% |
| Hurst regime | NOT active (regime_momentum_signed_5d is a feature, not a gate) | 0% |
| z-score OOD (R3) | Mahalanobis cutoff=0.70, 16 OOD features | ~5-15% |
| drawdown brake (R2) | OFF for ETH | 0% |
| BTC contagion | NOT a separate gate in v1 (BTC co-training was the pooled Model A; now isolated) | 0% |
| isolation forest | NOT active in v1 (v3 feature; not ported) | 0% |
| liquidity floor | NOT active as a gate (v1 uses market orders; liquidity via symbol selection) | 0% |
| R5 vol ceiling | ON (baseline; caps position at vol_ceiling) | informational |

**Regime coverage**: ETH-only specialist covers the full IS 24-month window (2023-03-24 to
2025-03-24). No regime-conditional kill switch introduced at /055 (requires Section 2 evidence).

---

## Section 7 — Pre-Registered Failure-Mode Prediction

**Most plausible failure mode**: WEAK or NEG-INERT verdict (Δ < +0.30). ETH/BTC daily
correlation is ~0.85 — materially higher than DOT/BTC ~0.70. A higher correlation means fewer
distinct ETH-vs-BTC decoupling episodes over the 24-month IS window. The 90-bar z-score window
may produce insufficient regime variation (std < 0.5 per LM Master Risk Flag 1). At n_trials=18,
a flat-ratio feature would fail to reach importance rank ≤ 15/48 at seed=42, and the ETH IS
Sharpe would show < +0.30 lift from the baseline -0.61.

**What the gates should catch**: F-AXIS #3 (importance rank > 30 = INERT) fires before IS Sharpe
interpretation. If rank > 30 AND IS Δ near zero → straightforward NEGATIVE-INERT. If rank ≤ 15
BUT IS Δ < 0 → LEARNED-NEG (feature learned but anti-informative at seed=42 Optuna basin).

**Secondary failure**: NEGATIVE-CLEAN (IS Δ < -0.05). Mechanism: adding ETH/BTC ratio at 48
features colsample_bytree-starves another more informative feature (same "silent-drag" as impulse
at /052-/053). If IS MaxDD WORSENS substantially vs baseline ~55% ETH MaxDD, this is the
diagnostic signature.

**OOS behavior**: OOS is informational only at EXPLORATION budget (single-seed=42). OOS Sharpe
near-flat is expected (+0.07 ETH baseline). Even a SPECIALIST-CANDIDATE IS result may show flat
or negative OOS at single-seed — this does not change the verdict (per /050 precedent: DOT OOS
-0.14 with PARTIAL verdict).

---

## Section 8 — Pre-Registered MERGE/NO-MERGE Numerical Criteria

MERGE decisions are at CONFIRMATION level (/056 or later). This EXPLORATION determines routing.
Pre-registered branching paths (BINDING — cannot be renegotiated post-hoc):

| /055 Verdict | Consequence | /056 Action |
|-------------|-------------|-------------|
| SPECIALIST-CANDIDATE (Δ ≥ +0.61) | ETH specialist candidate confirmed single-seed | /057 = ETH multi-seed (mandatory); /058 = CONFIRMATION with DOT+BTC+ETH specialists + LINK+LTC anchors |
| PARTIAL (Δ ∈ [+0.30, +0.61)) | ETH partial-confirmed candidate | /057 = ETH multi-seed (mandatory); /058 = CONFIRMATION with DOT+BTC+ETH specialists + LINK+LTC anchors |
| WEAK (Δ ∈ [+0.05, +0.30)) | Insufficient IS lift for ETH specialist | /056 = CONFIRMATION directly (2 specialists: DOT+BTC); ETH stays in pooled Model A |
| NEG-INERT (|Δ| < 0.05) | Feature adds no IS signal | /056 = CONFIRMATION directly (2 specialists: DOT+BTC); eth_vs_btc_ret_ratio_30 NOT bundled |
| NEG-CLEAN (Δ < -0.05) | Feature harms IS | /056 = CONFIRMATION directly (2 specialists: DOT+BTC); eth_vs_btc_ret_ratio_30 REVERTED from V1_FEATURE_COLUMNS_PRUNED; count returns to 47 |
| LEARNED-NEG (rank ≤ 15 + Δ < 0) | Feature learned but anti-informative | same as NEG-CLEAN path + feature REVERTED |

**MERGE numerical floors (CONFIRMATION level, pre-registered for /056+)**:
- OOS_monthly_Sharpe ≥ +1.0 (hard floor per feedback_sharpe_floor.md)
- IS_monthly_Sharpe ≥ +1.0 (hard floor)
- OOS trades ≥ 130 total (hard floor per feedback_trade_rate_floor.md)
- 10-seed pre-MERGE: mean Sharpe > 0, ≥ 7/10 profitable
- PBO < 0.4 (anti-overfit; CPCV-based)
- No single symbol > 30% of OOS weighted PnL

---

## Section 9 — Library Stack Declaration

| Library | Version | Usage | Fallback |
|---------|---------|-------|---------|
| lightgbm | 4.x (via pyproject.toml) | Primary ML model | N/A |
| optuna | 3.x | Hyperparameter optimization | N/A |
| numpy | ≥1.26 | Feature computation | N/A |
| pandas | ≥2.0 | DataFrame operations | N/A |
| scipy | ≥1.11 | Statistical functions | N/A |
| mlfinlab | NOT USED (v1 uses custom triple-barrier; mlfinlab license not available) | N/A | custom impl in walk_forward.py |
| pypbo | NOT USED (PBO computed inline via CPCV in validation_v1.py) | N/A | inline CPCV |
| fracdiff | NOT USED (not relevant to this EXPLORATION axis) | N/A | N/A |

All libraries are standard; no license-restricted dependencies at /055.

---

## Section 10 — Implementation Notes

### 10.1 Cohort isolation

- Cohort: `("ETHUSDT",)` — `V1_ITER055_UNIVERSE = ("ETHUSDT",)`.
- `assert_v1_universe(symbols)` fires at runner startup (ETHUSDT is NOT in V1_EXCLUDED_SYMBOLS).
- `assert set(symbols) == {"ETHUSDT"}` guard in dispatch branch.
- BTCUSDT is loaded for cross-asset feature computation ONLY (not in symbols; not traded).
- Post-dispatch: `assert {r.symbol for r in all_results}.issubset({"ETHUSDT"})`.

### 10.2 Parquet regen

Both ETHUSDT and BTCUSDT parquets must be regenerated:
```
uv run crypto-trade features --symbols BTCUSDT,ETHUSDT \
    --interval 8h --track v1 --format parquet --workers 4
```
Verify: `eth_vs_btc_ret_ratio_30` present in ETHUSDT parquet with valid non-NaN values.
Verify: NaN for BTCUSDT (ETH-only feature returns NaN for non-ETH symbols).

### 10.3 Model configuration

`Model_A_ETH_specialist`:
- atr_tp=3.5, atr_sl=1.75 (same as baseline Model A + /050 DOT specialist + /052-/054 BTC specialist)
- R3=ON, R1=OFF, R2=OFF (same as baseline Model A for ETH)
- feature_columns=V1_FEATURE_COLUMNS_PRUNED (48 cols; includes eth_vs_btc_ret_ratio_30)
- ENSEMBLE_SIZE=3, n_trials=18, single-seed=42

### 10.4 Features-base-hash

Pre-computed 48-col hash (after ADD eth_vs_btc_ret_ratio_30):
`b81176f893826500536ec5cee8ad00e74bf7edb834290e62e835213defe74ca3`

Prior 47-col hash (from /054, for reference):
`f19392b27f00b707c3da8686d2dc14ab367f8d7460e977be18a8f7386c70ce56`

The runner `run_iteration_055.py` verifies the live hash matches the 48-col hash.
