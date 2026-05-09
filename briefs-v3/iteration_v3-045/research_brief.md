# Iteration v3-045 — Research Brief (QR EDA-driven per-symbol ATR for LDO)

**Type**: EXPLORATION (Cycle 3 #6 of 10)
**Track**: v3 (rigor arm) — forty-fifth iteration
**Branch**: `iteration-v3/045` (off iter-v3/044 head)
**Date**: 2026-05-09
**Author**: QR (autopilot)

---

## Section 0 — Data Split Declaration

```
OOS_CUTOFF_DATE  = 2025-03-24    # IMMUTABLE
training_months  = 24             # IMMUTABLE
ENSEMBLE_SIZE    = 5              # single outer seed (EXPLORATION-spec)
n_trials         = 35             # EXPLORATION default
colsample_bytree = Optuna-tuned   # NOT hardcoded 1.0
OOS_CUTOFF_MS    = 1742774400000
```

**IS window (24 months)**: 2023-03-24 00:00 UTC through 2025-03-23 23:59 UTC
**OOS window**: 2025-03-24 00:00 UTC onward

Sacred constants UNCHANGED. The QR sees iter-v3/045 OOS metrics for the FIRST time in Phase 7.

---

## Section 0.5 — Iteration Type Declaration

```
TYPE: EXPLORATION
Cycle: 3 — #6 of 10 (after iter-v3/040 baseline-restore + iter-v3/041 pruning + 042 universal ATR + 043 Kaufman ER + 044 ALGO ATR PROMISING)
Wall-clock budget: <= 2h hard cap (EXPLORATION spec)
Spec: uv run python run_baseline_v3.py --seeds 1
  - ENSEMBLE_SIZE=5 (auto; inner ensemble)
  - n_trials=35 (default)
  - colsample_bytree Optuna-tunable (NOT hardcoded 1.0)
  - outer_seeds=1 (EXPLORATION-spec)
Single axis: per-symbol ATR widening for LDOUSDT only
  V3_ATR_MULTIPLIERS_PER_SYMBOL = {"ALGOUSDT": (2.0, 1.5), "LDOUSDT": (2.0, 1.5)}  -- TP unchanged, SL +50%
  V3_FEATURE_COLUMNS_TOP_N = 14 (UNCHANGED — regime_momentum_signed_5d preserved)
  V3_FEATURES_PER_SYMBOL = {} (UNCHANGED — empty)
  V3_MODELS = 4 (BCH, LDO, TRX, ALGO) — UNCHANGED.
  REQUIRED_GAP = 88 = (21+1)*4 — UNCHANGED.
  DEFAULT_ATR_MULTIPLIERS = (2.0, 1.0) — UNCHANGED.
Predicted classification: PROMISING (35%), PROMISING-INERT (40%), NEGATIVE (25%).
```

**Context**: iter-v3/044 (QR EDA-driven ALGO ATR (2.0, 1.5)) was PROMISING — ALGO swing
+49 OOS via wider SL targeting LONG SL/TP asymmetry. iter-v3/045 applies the SAME
mechanism to LDO, the next chronic underperformer at iter-v3/044 (LDO OOS -3.07%, 36.4% WR,
11 trades). The QR diagnosis (SHA `ed949fe`, `analysis/iteration_v3-045/`) shows LDO's
bottleneck is a **regime mismatch causing IS-OOS exit-composition divergence** (SL:TP ratio
1.14 IS → 2.33 OOS; SL rate 53.3% IS → 63.6% OOS). The mechanism is the same as ALGO
(wider SL gives trades more headroom before stop-out under regime-shifted volatility), but
the magnitude is much smaller (LDO is a marginal drag, not catastrophic). LDO's natr_21_raw
median is 1.35× peer median (per iter-v3/032 EDA), so wider absolute SL barriers in price-%
terms align with LDO's volatility regime.

---

## Section 1 — Hypothesis

Widening LDOUSDT's stop-loss multiplier from 1.0×ATR to 1.5×ATR (TP unchanged at 2.0×ATR)
reduces the per-trade SL hit rate on LDO trades — which currently rises from IS 53.3% to
OOS 63.6% as a consequence of the IS→OOS volatility-regime distribution shift — by giving
trades 50% more drawdown headroom before stop-out. The mechanism mirrors iter-v3/044's
PROMISING ALGO ATR (2.0, 1.5). Expected effect: LDO OOS PnL lifts from -3.07% toward 0% to
+5%; LDO IS PnL stays approximately neutral (current +41.85% IS is already positive — wider
SL slightly reduces SL-then-cooldown sequences but TP captures are unchanged at TP=2.0×ATR).

---

## Section 2 — IS-Only Numerical Evidence

### 2.1 — LDO bottleneck @ iter-v3/044 (from `analysis/iteration_v3-045/synthesis.md`)

| Direction | n_IS | WR_IS | net_pnl_IS | n_OOS | WR_OOS | net_pnl_OOS |
|---|---:|---:|---:|---:|---:|---:|
| LONG  | 4  | 50.0% | +14.40% | 1  | 0.0%  | -4.30% |
| SHORT | 11 | 45.5% | +27.45% | 10 | 40.0% | +1.23% |
| TOTAL | 15 | 46.7% | +41.85% | 11 | 36.4% | -3.07% |

LDO IS = positive contributor (+41.85%, 173.41% pct_of_total at iter-v3/044). LDO OOS = small
drag (-3.07%, -2.87% pct_of_total). Direction asymmetry is structurally insignificant
(only 1 LONG OOS trade; underpowered). The dominant pattern is the IS→OOS exit-composition
shift (Section 2.2).

### 2.2 — LDO IS→OOS exit composition shift (the binding constraint)

| Period | n | TP% | SL% | TIMEOUT% | SL:TP ratio | mean_pnl |
|---|---:|---:|---:|---:|---:|---:|
| iter-v3/044 IS  | 15 | 46.7% | 53.3% | 0.0%  | 1.14 | +2.79% |
| iter-v3/044 OOS | 11 | 27.3% | 63.6% | 9.1%  | 2.33 | -0.28% |

Δ TP% = -19.4pp (worse OOS). Δ SL% = +10.3pp (worse OOS). The SL:TP ratio doubled. SL hit rate
was already 53% IS — wider SL would compress this if regime-shift OOS produces larger
adverse excursions before recovery. Mean SL of -4.21% IS (well below 1.0×ATR=5.01% theoretical
barrier) suggests SLs are hit close to entry, consistent with regime-noise penetrating the
1.0×ATR band. At 1.5×ATR=7.51%, SL is wider than typical adverse excursion.

### 2.3 — LDO regime mismatch (carry-forward from iter-v3/032 EDA)

iter-v3/032 per_symbol_atr_eda.py established that LDOUSDT has **median natr_21_raw =
5.01% vs peer (BCH/TRX/ALGO) median 3.70% — 1.35× higher**. This was the original motivation
for the iter-v3/032 LDO ATR (1.5, 0.75) "tighter barriers to align with peer" hypothesis,
which was MULTI-SEED-FALSIFIED at iter-v3/039 (broke IS Sharpe -0.59).

**The structural insight is preserved but the direction is reversed**: LDO's higher natr
implies LDO's adverse excursions are LARGER in absolute price-% than peer adverse
excursions. Tighter barriers (iter-v3/032 path) made labels too noisy IS — IS WR collapsed
from 47% to 21% (catastrophic). Wider barriers (this iteration's path) increase the SL band
to match LDO's natural volatility regime in OOS, where the IS-barrier-calibrated rate
under-fires.

### 2.4 — Counterfactual: LDO OOS lift estimate

If LDO OOS SL rate compresses from 63.6% to 50% (matches IS regime), the converted-from-SL
trades become 50/50 TP-or-timeout. Assume average SL (-4.21% mean) becomes -2% (timeout) or
+5% (TP at 2.0×ATR≈10.01%). For 1.5 trades redirected from SL to other:
- Net pnl shift: 1.5 × (-(-4.21) + 0.5×(-2) + 0.5×(5)) ≈ 1.5 × (4.21 + 1.5) = +8.6 pp PnL
- LDO OOS PnL: -3.07 + 8.6 = +5.5%
- Bundle OOS lift: +5.5pp on LDO of total bundle PnL (107.10% iter-v3/044) → +0.05 OOS Sharpe

If LDO OOS SL rate compresses MORE aggressively (to 40%, matching iter-v3/032 OOS pattern
where wider barrier alignment helped), the lift could be ~+0.10 OOS Sharpe.

### 2.5 — Per-symbol importance for LDO at iter-v3/044

| Rank | Feature | Importance |
|---:|---|---:|
| 1 | hurst_diff_100_50 | 347 |
| 2 | range_realized_vol_50 | 337 |
| 3 | vwap_dev_20 | 334 |
| 4 | ret_skew_200 | 332 |
| 5 | btc_ret_14d | 331 |
| 6 | ema_spread_atr_20 | 286 |
| 7 | ret_kurt_200 | 263 |
| 8 | ret_skew_50 | 260 |
| 9 | ret_kurt_50 | 257 |
| 10 | sym_vs_btc_ret_7d | 249 |
| 11 | regime_momentum_signed_5d | 232 |
| 12 | hurst_100 | 214 |
| 13 | ret_autocorr_lag1_50 | 214 |
| 14 | max_dd_window_50 | 190 |

LDO's importance distribution is FLAT (range 190-347, ratio 1.83×) — no single feature
dominates. Universal feature additions targeting LDO would dilute colsample_bytree picks
without addressing the IS→OOS regime-shift (Sections 2.2, 2.3). The per-symbol ATR axis
operates at the LABELING layer, downstream of features — directly addressing the regime
shift without disturbing the model's learned signal hierarchy.

### 2.6 — Why NOT iter-v3/032 LDO ATR (1.5, 0.75)

The (1.5, 0.75) configuration was MULTI-SEED-FALSIFIED at iter-v3/039 CONFIRMATION
(IS Sharpe -0.59 vs +0.51 baseline). Per `feedback_v3_per_symbol_lifts_oos_breaks_is.md`,
specific per-symbol customizations from the iter-v3/035 4-ingredient bundle (including
LDO ATR (1.5, 0.75)) were REJECTED for the bundle. The cycle 3 plan (`briefs-v3/cycle3_plan.md`)
explicitly forbids re-applying these. **iter-v3/045 proposes the OPPOSITE direction**:
wider barriers (1.5×SL), not tighter (0.75×SL). The mechanism is symmetric to iter-v3/044
ALGO ATR (2.0, 1.5), which was PROMISING.

### 2.7 — Predicted Behavioral Effect (per `feedback_v3_axis_saturation_predictor.md`)

Predicted IS trade count delta vs iter-v3/044 anchor:
- LDO IS trades: 15 → 14-17 (modest change; wider SL slightly lengthens trade durations,
  reducing trade frequency, but cooldown mechanics may also redistribute).
- LDO IS SL count: 8 → 5-7 (−1 to −3; primary mechanism).
- LDO IS TP count: 7 → 7-9 (+0 to +2; some former-SLs reach TP given wider band).
- BCH/TRX/ALGO bit-identical (per-symbol architecture isolates LDO).
- Bundle IS trades: 247 → 246-249 (within ±1.5%).

**Falsifier**: if observed LDO IS trade count change is > 30% relative vs iter-v3/044, the
ATR widening produced cascade effects beyond barrier geometry (investigate label-pipeline
correctness).

### Analysis Script

`analysis/iteration_v3-045/ldo_bottleneck_diagnosis.py` (committed SHA `ed949fe`) produces
`ldo_diagnosis.csv` and `synthesis.md` documenting the LDO bottleneck. The diagnosis covers:
direction asymmetry IS/OOS, exit-reason distribution IS/OOS, ALGO sanity check (reproduces
iter-v3/044 LONG-bottleneck claim), iter-v3/032 (1.5, 0.75) comparison, per-month LDO PnL,
and LDO feature importance. `candidate_axes_ranking.md` ranks 5 candidate axes; the
recommended axis is LDO ATR (2.0, 1.5).

---

## Section 3 — Proposed Changes

### Sub-fix 1: ADD V3_ATR_MULTIPLIERS_PER_SYMBOL["LDOUSDT"] = (2.0, 1.5)

In `src/crypto_trade/features_v3/__init__.py`, set:

```python
V3_ATR_MULTIPLIERS_PER_SYMBOL: dict[str, tuple[float, float]] = {
    "ALGOUSDT": (2.0, 1.5),  # iter-v3/044 — PROMISING
    "LDOUSDT": (2.0, 1.5),   # iter-v3/045 — QR EDA-driven; mirror iter-v3/044 mechanism
}
```

This widens LDO's SL multiplier from 1.0× ATR (DEFAULT) to 1.5× ATR (50% wider band). TP
multiplier unchanged at 2.0× ATR. Other 2 symbols (BCH/TRX) remain on
DEFAULT_ATR_MULTIPLIERS = (2.0, 1.0) via fallback.

### Sub-fix 2: Update _verify_feature_columns in run_baseline_v3.py

Update assertions for iter-v3/045 state:
- `len(V3_ATR_MULTIPLIERS_PER_SYMBOL) == 2` (was 1; now ALGOUSDT + LDOUSDT)
- `V3_ATR_MULTIPLIERS_PER_SYMBOL["LDOUSDT"] == (2.0, 1.5)` (NEW per-symbol entry)
- `atr_multipliers_for_symbol("LDOUSDT") == (2.0, 1.5)` (per-symbol)
- `atr_multipliers_for_symbol("ALGOUSDT") == (2.0, 1.5)` (per-symbol; UNCHANGED)
- `atr_multipliers_for_symbol("BCHUSDT") == (2.0, 1.0)` (DEFAULT fallback; UNCHANGED)
- `atr_multipliers_for_symbol("TRXUSDT") == (2.0, 1.0)` (DEFAULT fallback; UNCHANGED)
- Reject non-{ALGOUSDT, LDOUSDT} keys in V3_ATR_MULTIPLIERS_PER_SYMBOL
- All other assertions UNCHANGED from iter-v3/044 (V3_FEATURE_COLUMNS=14, regime_momentum
  PRESENT, ER ABSENT, regime_momentum_signed_3d ABSENT, etc.)

### Sub-fix 3: Update tests/features_v3/test_atr_multipliers_for_symbol.py

- Update docstring header from "iter-v3/044 state" to "iter-v3/045 state".
- Update `test_atr_multipliers_default`:
  - LDOUSDT must now return (2.0, 1.5) (was (2.0, 1.0) at iter-v3/044).
  - BCH/TRX still return (2.0, 1.0).
  - ALGOUSDT still returns (2.0, 1.5).
- Update `test_atr_multipliers_ldo_universal_tighter` →
  rename `test_atr_multipliers_ldo_per_symbol_widened`:
  - LDOUSDT key MUST be present in V3_ATR_MULTIPLIERS_PER_SYMBOL (was MUST be absent).
  - LDOUSDT value must be (2.0, 1.5).
  - Update assertion error messages to reflect iter-v3/045 state.
- Update `test_v3_atr_multipliers_per_symbol_has_algo` →
  rename `test_v3_atr_multipliers_per_symbol_has_algo_and_ldo`:
  - Length must be 2 (was 1).
  - Both ALGOUSDT and LDOUSDT keys must be present with (2.0, 1.5).
- Update `test_atr_multipliers_runner_dispatch`:
  - `strat_ldo.inner.atr_tp_multiplier == 2.0` (UNCHANGED)
  - `strat_ldo.inner.atr_sl_multiplier == 1.5` (CHANGED from 1.0).
  - BCH still 2.0/1.0 via DEFAULT.

### Sub-fix 4: Update `V3_ATR_MULTIPLIERS_PER_SYMBOL` docstring in features_v3/__init__.py

Append iter-v3/045 entry to docstring history:

```
iter-v3/045: LDOUSDT entry added (2.0, 1.5) — QR EDA-driven per-symbol axis selection,
  cycle 3 #6. LDO IS→OOS exit-composition shift (SL:TP 1.14 → 2.33; SL rate 53.3% → 63.6%);
  wider SL targets the IS→OOS regime-shift directly, mirroring iter-v3/044 ALGO mechanism.
  Predecessor (1.5, 0.75) at iter-v3/032 was MULTI-SEED-FALSIFIED at iter-v3/039 — this is
  the OPPOSITE direction (wider not tighter) per QR EDA candidate-ranking.
  Source: analysis/iteration_v3-045/ldo_bottleneck_diagnosis.py SHA `ed949fe`.
```

### Sub-fix 5: Update ITERATION_LABEL

In `run_baseline_v3.py`, ITERATION_LABEL = "v3-045".

### Sub-fix 6: Update _verify_feature_columns docstring

Replace "iter-v3/044" references with "iter-v3/045" in docstring blocks. The PART A
(REVERT efficiency_ratio_50) sub-section is unchanged — efficiency_ratio_50 still ABSENT.
The PART B (per-symbol ATR axis) sub-section now describes 2 entries (ALGOUSDT + LDOUSDT),
both at (2.0, 1.5).

### Bundle state verification (what _verify_feature_columns must assert)

```
V3_FEATURE_COLUMNS_TOP_N: 14 features (UNCHANGED from iter-v3/044)                    PASS
DEFAULT_ATR_MULTIPLIERS: (2.0, 1.0) — UNCHANGED                                       PASS
V3_ATR_MULTIPLIERS_PER_SYMBOL: 2 entries (ALGOUSDT, LDOUSDT) — both (2.0, 1.5)        PASS
V3_FEATURES_PER_SYMBOL: {} (empty — UNCHANGED)                                        PASS
features_for_symbol("BCHUSDT") == 14 features (TOP_N fallback)                        PASS
features_for_symbol("ALGOUSDT") == 14 features (TOP_N fallback)                       PASS
features_for_symbol("LDOUSDT") == 14 features (TOP_N fallback)                        PASS
features_for_symbol("TRXUSDT") == 14 features (TOP_N fallback)                        PASS
atr_multipliers_for_symbol("ALGOUSDT") == (2.0, 1.5) (per-symbol — UNCHANGED)         PASS
atr_multipliers_for_symbol("LDOUSDT") == (2.0, 1.5) (per-symbol — NEW iter-v3/045)    PASS
atr_multipliers_for_symbol("BCHUSDT") == (2.0, 1.0) (DEFAULT — UNCHANGED)             PASS
atr_multipliers_for_symbol("TRXUSDT") == (2.0, 1.0) (DEFAULT — UNCHANGED)             PASS
"regime_momentum_signed_5d" IN V3_FEATURE_COLUMNS_TOP_N (mandate PRESENT)             PASS
"regime_momentum_signed_3d" NOT IN V3_FEATURE_COLUMNS_TOP_N (REVERTED at iter-v3/044) PASS
"efficiency_ratio_50" NOT IN V3_FEATURE_COLUMNS_TOP_N (DROPPED at iter-v3/043)        PASS
"ret_skew_50" IN V3_FEATURE_COLUMNS_TOP_N (PRESENT)                                   PASS
"sym_vs_btc_ret_7d" IN V3_FEATURE_COLUMNS_TOP_N (PRESENT)                             PASS
V3_MODELS = (BCH, LDO, TRX, ALGO) — 4 symbols (UNCHANGED)                             PASS
REQUIRED_GAP = 88 = (21+1) x 4 (UNCHANGED)                                            PASS
```

---

## Section 4 — Expected OOS Impact

**IS Sharpe prediction (single-seed, vs iter-v3/044 single-seed anchor)**:
- iter-v3/044 IS Sharpe is the comparison anchor. From the catalog, iter-v3/044 was
  PROMISING (+49 ALGO swing); the QR brief predicted IS [+0.65, +1.05]. Reading
  `reports-v3/iteration_v3-044/in_sample/per_symbol.csv`: BCH +23.62%, LDO +41.85%,
  TRX -7.28%, ALGO -34.05%. Net IS PnL = +24.13%. Iter-v3/044 anchor IS Sharpe
  approximated from comparison.csv would be needed for exact lift; using iter-v3/040
  proxy +0.79 as anchor (cycle 3 anchor per cycle3_plan.md).
- Predicted band: [+0.70, +1.00]
- Median point estimate: +0.80 to +0.90
- Rationale: Wider LDO SL redirects ~1-3 SL exits to TP/timeout. Each redirected SL→TP is
  approximately +6-9 PnL swing per trade (TP +5% to +10% minus former SL -4%). 1-3 trades
  redirected = ~+10 to +25 PnL on LDO contribution (current LDO IS = +41.85). Bundle IS
  total +24.13 → +34 to +49 (+40-100% LDO-driven). With variance also lifting modestly,
  Sharpe lifts proportionally less. Estimate +0.05 to +0.15 IS Sharpe lift (modest;
  smaller than iter-v3/044's predicted +0.10 to +0.20 because LDO's bottleneck is
  smaller-magnitude than ALGO's was).

**OOS Sharpe prediction (single-seed, vs iter-v3/044 single-seed anchor)**:
- Predicted band: [iter-v3/044 OOS, iter-v3/044 OOS + 0.20]
- Median point estimate: iter-v3/044 OOS + 0.05 to +0.10
- Rationale: ATR multiplier change preserves per-symbol model architecture (no LightGBM
  retrain shift; same Optuna search space). LDO OOS PnL expected to lift +3 to +9pp from
  -3.07% toward 0% to +5% (Section 2.4 counterfactual). Bundle OOS lift: small (LDO is
  -2.87% pct_of_total at iter-v3/044; even if LDO doubles in magnitude positive, bundle
  contribution ~+3 to +8% PnL on bundle base 107% = +0.03 to +0.07 Sharpe). ALGO/TRX/BCH
  bit-identical (per-symbol isolation).

**OOS falsifier (pre-registered)**:
- If LDO OOS PnL drops below -10% (worse than -3.07% by > -7%): wider SL backfired (more
  losses absorbed before stop-out, with WR not improving); NEGATIVE classification.
- If BCH/TRX/ALGO trade rosters are non-bit-identical to iter-v3/044: per-symbol-ATR
  dispatch path bug; PATH C — REVERT.

**Pathway-A trigger (PROMISING)**:
- LDO OOS PnL ≥ 0% AND BCH/TRX/ALGO bit-identical to iter-v3/044 AND bundle OOS Sharpe
  not regressed by more than -0.10.

**Pathway-B trigger (PROMISING-INERT or PROMISING-MECHANICAL)**:
- LDO trade roster bit-identical to iter-v3/044 (Falsifier 1 fires; ATR multipliers did
  not propagate to model output) — PROMISING-MECHANICAL.
- LDO trade roster differs but LDO OOS PnL within [-3%, 0%] (modest improvement, not
  enough to call PROMISING) — PROMISING-INERT.

**Pathway-C trigger (NEGATIVE)**:
- LDO OOS PnL < -10% OR
- BCH/TRX/ALGO non-bit-identical (architecture bug) OR
- Bundle OOS Sharpe regressed by more than -0.20.
- Action: REVERT V3_ATR_MULTIPLIERS_PER_SYMBOL["LDOUSDT"] at iter-v3/046; consider per-symbol
  features for LDO (regime_momentum_signed_3d via V3_FEATURES_PER_SYMBOL with IS-axis
  pre-validation per cycle 3 plan Axis 5) as next axis.

---

## Section 5 — Risk Mitigation

**R1 (cooldown)**: unchanged. Cooldown=2 candles post-trade per symbol.

**R2 (drawdown scaling)**: unchanged. R2 gate parameters carried forward.

**R3 (OOD detection)**: zscore_threshold=2.0 unchanged. Feature subspace unchanged at 14
features (Mahalanobis covariance space identical to iter-v3/044). Expected effect on OOD
firing rate: <2% relative (no feature dimensionality change).

**LDO ATR widening risk**: wider SL means individual losing trades can lose MORE per trade.
Mean SL pnl_pct shifts from ~-4.21% (iter-v3/044 IS) to ~-6.30% per losing trade. If the
wider SL doesn't redirect enough SLs to TPs, LDO would lose MORE per trade with similar
frequency, making the small bottleneck WORSE. Falsifier: if observed LDO IS SL count
remains ≥7 (vs predicted 5-7) AND mean SL pnl_pct ≤ -6%, the wider SL is hurting more than
helping. This would trigger Pathway-C and REVERT at iter-v3/046.

**Stacking risk (2 per-symbol customizations: ALGO + LDO)**: iter-v3/039 multi-seed
established that BCH-fracdiff + LDO-(1.5,0.75) bundle BROKE IS aggregate. iter-v3/045 stacks
ALGO-(2.0,1.5) + LDO-(2.0,1.5) — both wider-SL ATR adjustments at the labeling layer
only (no per-symbol features). The mechanism is symmetric and architecturally cleaner than
the iter-v3/039 stack (which mixed feature-layer + label-layer customizations across 2
symbols). However, the IS-divergence pattern (`feedback_v3_per_symbol_lifts_oos_breaks_is.md`)
remains a cycle-3 hazard; if iter-v3/045 IS Sharpe regresses meaningfully (> -0.10 vs
iter-v3/044), this stacking risk is REPLICATED at the labeling layer, and the catalog row
must be classified NEGATIVE-stacking-suspect with a feedback rule update.

**IS trade-rate stability**: ATR multipliers change for LDO only; non-LDO label distribution
identical to iter-v3/044 (assuming dispatch path is correct — verified by Sub-fix 3 test).
LDO IS trade count expected within ±20% of iter-v3/044 (15 → 12-18 predicted). Portfolio total
IS trade count expected within ±2% (247 → ~245-250 predicted). If portfolio total deviates >
30%, investigate parquet freshness (stale features, incorrect feature_columns list).

**Cross-symbol contagion risk**: per-symbol ATR change affects only LDO model training data.
BCH/TRX/ALGO models are completely independent (separate Optuna runs, separate feature
parquets at the model-input level). Cross-symbol contagion possible only via portfolio-level
risk gates (BTC trend filter, drawdown brake). Both gates use portfolio-aggregate signals;
LDO trade-rate change shifts portfolio aggregates by single-digit percent. Expected
portfolio risk-gate firing rate change: <3%.

---

## Section 6 — Risk Management Design (7-Primitive Gate Table)

All 7 risk gates carried forward from iter-v3/044 baseline UNCHANGED.

| Gate | Type | Parameter | Change |
|---|---|---|---|
| 1 — BTC trend | BtcTrendFilterConfig | lookback=42, threshold=15% | None |
| 2 — Hit rate | HitRateGateConfig | window=20, sl_threshold=0.65 | DISABLED (unchanged) |
| 3 — ADX gate | ADX regime filter | threshold=20 (v3 default) | None |
| 4 — Hurst regime | hurst_100 > 0.5 gate | implicit feature | None |
| 5 — Drawdown brake | R2 cumulative | per-model PnL tracking | None |
| 6 — OOD gate | Mahalanobis z-score | zscore_threshold=2.0, 14-D space | None (no feature change) |
| 7 — Liquidity floor | NATR floor | NATR >= 0.5% | None |

**Predicted OOD fire rate**: within ±2% of iter-v3/044 baseline. No feature subspace change.

---

## Section 7 — Pre-Registered Failure-Mode Prediction

**Most plausible failure mode (PROMISING-INERT — minimal LDO impact at single-seed)**:
LDO trade rate changes by <10%, LDO OOS WR rises modestly (36.4% → 38-40% range), but
the absolute PnL improvement is too small to move the needle. Bundle OOS Sharpe lift
< +0.05. Classification: PROMISING-INERT. The mechanism is honest at the labeling layer
but LDO's signal is the binding constraint; relabeling alone cannot lift past the model's
predictive capacity.

**Second plausible failure mode (PROMISING-MECHANICAL — bit-identical LDO trades)**:
At single-seed n_trials=35, Optuna converges to a similar hyperparameter region for LDO
regardless of label-barrier geometry. LDO's IS+OOS trade rosters are bit-identical (or
very near-bit-identical) to iter-v3/044. Falsifier 1 fires. PROMISING-MECHANICAL.
Diagnostic: per-symbol-ATR architecture validated as architecturally-neutral on LDO; the
axis effect was not propagated through the LightGBM head. iter-v3/046 should pivot to a
different axis. Probability: 25-30%.

**Third plausible failure mode (NEGATIVE — wider SL increases loss per trade without raising WR)**:
LDO mean SL pnl_pct shifts from -4.21% to ~-6.30%. If the wider SL doesn't redirect enough
SLs to TPs, LDO trades just lose MORE per trade with similar frequency. LDO OOS PnL
deepens to -8% to -15%. Per-trade Sharpe could WORSEN if WR rises only marginally.
Classification: NEGATIVE; close per-symbol-ATR axis on LDO. Probability: 15-20%.

**Fourth plausible failure mode (cross-symbol architecture bug — Falsifier 2)**:
BCH/TRX/ALGO trade rosters non-bit-identical to iter-v3/044. The per-symbol-ATR dispatch
path has unintended side-effects from adding a second entry (most likely: a global Optuna
seed or random-state cross-pollination). PATH C — REVERT and diagnose. Probability: <5%
(per-symbol architecture validated at iter-v3/032+iter-v3/044; second entry is mechanically
analogous to first).

**What the gates should catch**:
- Gate 5 (R2 drawdown): LDO label-distribution shift may alter R2 firing rate. Monitor.
- Gate 7 (liquidity): NATR floor unchanged; LDO trades that were marginal NATR-wise before
  still pass.

**Behavioral effect predictor**: predicted IS trade count delta -10% to +20% (LDO model
specifically; -2% to +1% portfolio-wide). Falsifier: > 30% portfolio delta triggers
investigation.

---

## Section 8 — Pre-Registered MERGE/NO-MERGE Numerical Criteria

This is an EXPLORATION iteration. MERGE gates do NOT apply. Classification criteria
(pre-registered before backtest runs):

**PATH A — PROMISING (clean)**:
  LDO OOS PnL ≥ 0% AND BCH+TRX+ALGO trade rosters bit-identical to iter-v3/044 AND
  bundle OOS Sharpe not regressed by more than -0.10 vs iter-v3/044 anchor AND
  LDO trade roster differs from iter-v3/044 (Falsifier 1 PASS).
  Classification: PROMISING. Per-symbol ATR widening for LDOUSDT contributes positive lift.
  Catalog entry: candidate for next CONFIRMATION bundle (compoundable with iter-v3/044
  ALGO ATR per same-mechanism principle; both wider-SL labeling-layer adjustments).

**PATH B — PROMISING-INERT or PROMISING-MECHANICAL**:
  - PROMISING-INERT: LDO trade roster differs but LDO OOS PnL in [-3%, 0%]; bundle OOS
    Sharpe within ±0.05 of iter-v3/044. Mechanism dispatched but signal not lifted. Retain
    as zero-cost addition to CONFIRMATION bundle if other axes succeed.
  - PROMISING-MECHANICAL: LDO trade roster bit-identical to iter-v3/044 (Falsifier 1 fires).
    Architecture validated as neutral on LDO; NOT a CONFIRMATION-bundle ingredient per
    `feedback_promising_mechanical_subtype.md`.

**PATH C — NEGATIVE**:
  - NEGATIVE-LDO-deepens: LDO OOS PnL < -10% (worse than iter-v3/044 by > -7%).
  - NEGATIVE-bundle-regression: bundle OOS Sharpe regressed by more than -0.20 vs
    iter-v3/044.
  - NEGATIVE-architecture-bug: BCH/TRX/ALGO trade rosters non-bit-identical to iter-v3/044
    (Falsifier 2 fires) — REVERT.
  Classification: NEGATIVE. Per-symbol ATR axis FALSIFIED for LDO.
  Action: REVERT V3_ATR_MULTIPLIERS_PER_SYMBOL["LDOUSDT"] at iter-v3/046; consider per-symbol
  features for LDO (with IS-axis pre-validation per cycle 3 Axis 5) as next axis.
  Catalog entry: "LDO ATR widening (1.5×SL) FALSIFIED — bottleneck not addressable via
  mechanical ATR widening despite ALGO precedent".

**Pre-registered classification thresholds (locked before backtest)**:
- PATH A: LDO OOS PnL ≥ 0% AND BCH+TRX+ALGO bit-identical AND bundle OOS Sharpe Δ ≥ -0.10
  AND LDO trades differ
- PATH B-INERT: LDO trades differ AND LDO OOS PnL in [-3%, 0%] AND bundle Sharpe Δ ∈ [-0.05, +0.05]
- PATH B-MECHANICAL: LDO trades bit-identical (Falsifier 1 fires)
- PATH C: LDO OOS PnL < -10% OR bundle OOS Sharpe Δ < -0.20 OR BCH/TRX/ALGO drift (Falsifier 2)

These thresholds are LOCKED and cannot be post-hoc renegotiated.

---

## Section 9 — Library Stack Declaration

All versions identical to iter-v3/044 reproducibility stamp. No new libraries introduced.
Per-symbol ATR is a config-only change (no new feature implementations dispatched).

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

**No mlfinlab/mlfinpy/pypbo/fracdiff dependencies.** v3 uses scipy + statsmodels for all
statistical tests (ADF, PBO, DSR, PSR).

---

## Section 10 — QR Audit Trail (per `feedback_v3_axis_selection_quant_discipline.md`)

**EDA basis**: `analysis/iteration_v3-045/ldo_bottleneck_diagnosis.py` (committed SHA
`ed949fe`). Outputs: `ldo_diagnosis.csv`, `synthesis.md`, `candidate_axes_ranking.md`.
Establishes:
- LDO IS @ iter-v3/044 = +41.85% PnL (positive contributor); LDO OOS = -3.07% (small drag)
- LDO direction asymmetry: structurally insignificant (1 LONG OOS trade)
- LDO IS exit ratio SL:TP = 1.14; OOS = 2.33 (+10pp SL rate IS→OOS — the binding constraint)
- LDO regime mismatch (natr 1.35× peer median; structural per iter-v3/032 EDA)
- Comparison vs iter-v3/032 LDO ATR (1.5, 0.75): IS catastrophic (-21.91% PnL, 21.4% WR);
  the (1.5, 0.75) tighter-barrier path was MULTI-SEED-FALSIFIED at iter-v3/039 (forbidden)
- LDO feature importance: FLAT distribution (190-347, 1.83× ratio); per-symbol ATR axis
  operates downstream of features and doesn't disturb learned signal hierarchy
- 5 candidate axes ranked: top recommendation is LDO ATR (2.0, 1.5) — wider SL mirroring
  iter-v3/044 ALGO mechanism; OPPOSITE direction of forbidden (1.5, 0.75) tighter variant

**Original orchestrator pick**: NONE (per `feedback_v3_axis_selection_quant_discipline.md`,
established at iter-v3/044, the orchestrator no longer pre-commits axes; QR drives axis
selection from EDA).

**QR-driven selection**: per-symbol ATR widening for LDOUSDT only
(V3_ATR_MULTIPLIERS_PER_SYMBOL["LDOUSDT"] = (2.0, 1.5)). EDA shows LDO's bottleneck is the
IS→OOS exit-composition shift (SL:TP doubling); wider SL targets it mechanically. Mechanism
mirrors iter-v3/044 PROMISING ALGO ATR (2.0, 1.5). Cleanest single-axis test; lowest-risk
candidate from the 5-axis ranking.

**Setup commit SHA**: <to be filled at setup commit; brief committed FIRST per Phase 5.5
discipline; setup commit must reference brief SHA>.
**Phase 5.5 verification**: brief Section 2 numerical evidence committed BEFORE setup
commit (committed at `ed949fe`); brief is iter-v3/045 single-rev (no orchestrator-pick
predecessor).

This Section 10 satisfies the process-discipline requirement that QR EDA precedes axis
selection. Cannot be retroactively renegotiated.

---

## Section 11 — Catalog-Row Pre-Commit Disposition

The catalog row to be appended at Phase 8 (diary closure) is pre-registered for ALL outcomes:

**Outcome A — PROMISING-clean** (LDO OOS PnL ≥ 0% AND BCH+TRX+ALGO bit-identical AND bundle
OOS Sharpe Δ ≥ -0.10 AND LDO trades differ):
> `| iter-v3/045 | 2026-05-09 | Per-symbol ATR widening for LDOUSDT (2.0, 1.5); 4-sym BCH+LDO+TRX+ALGO; QR EDA-driven mirror of iter-v3/044 ALGO ATR mechanism; cycle 3 #6 | <IS Δ> | <OOS Δ> | EXPLORATION-PROMISING (clean) | YES — STRONG candidate; iter-v3/050 CONFIRMATION-bundle ingredient (compoundable with iter-v3/044 ALGO ATR per same-mechanism principle) |`

**Outcome B-INERT — PROMISING-INERT** (LDO trades differ AND LDO OOS PnL in [-3%, 0%] AND
bundle Sharpe Δ within ±0.05):
> `| iter-v3/045 | 2026-05-09 | Per-symbol ATR widening for LDOUSDT (2.0, 1.5); cycle 3 #6 | <IS Δ> | <OOS Δ> | EXPLORATION-PROMISING-INERT | RETAIN as zero-cost CONFIRMATION-bundle addition if other axes succeed; mechanism dispatched but signal not lifted |`

**Outcome B-MECHANICAL — PROMISING-MECHANICAL** (LDO trades bit-identical to iter-v3/044):
> `| iter-v3/045 | 2026-05-09 | Per-symbol ATR widening for LDOUSDT (2.0, 1.5); cycle 3 #6 | ~iter-v3/044 (bit-identical) | ~iter-v3/044 (bit-identical) | EXPLORATION-PROMISING-MECHANICAL | NO — strictly architectural; per-symbol-ATR architecture validated as neutral on LDO; iter-v3/046 may apply ATR widening to a different symbol or pivot to per-symbol features for LDO with IS-axis pre-validation |`

**Outcome C — NEGATIVE-LDO-deepens** (LDO OOS PnL < -10%):
> `| iter-v3/045 | 2026-05-09 | Per-symbol ATR widening for LDOUSDT (2.0, 1.5); cycle 3 #6 | <IS Δ> | <OOS Δ> | EXPLORATION-NEGATIVE (LDO deepens) | NO — closes per-symbol-ATR axis on LDO; LDO bottleneck not addressable via mechanical SL widening despite ALGO precedent; iter-v3/046 = different axis (consider per-symbol features for LDO with IS-axis pre-validation) |`

**Outcome C — NEGATIVE-architecture-bug** (BCH/TRX/ALGO non-bit-identical):
> `| iter-v3/045 | 2026-05-09 | Per-symbol ATR widening for LDOUSDT (2.0, 1.5); cycle 3 #6 | <IS Δ> | <OOS Δ> | EXPLORATION-NEGATIVE (architecture-bug — BCH/TRX/ALGO drift) | NO — REVERT; iter-v3/046 = different axis category after architectural fix |`

**Outcome C — NEGATIVE-stacking-suspect** (bundle OOS Sharpe Δ < -0.20):
> `| iter-v3/045 | 2026-05-09 | Per-symbol ATR widening for LDOUSDT (2.0, 1.5); cycle 3 #6 | <IS Δ> | <OOS Δ> | EXPLORATION-NEGATIVE (stacking-suspect; replicates iter-v3/039 IS-divergence pattern at labeling layer) | NO — closes per-symbol-ATR stacking axis; even labeling-layer per-symbol customizations break IS aggregate when stacked. Update memory with new feedback rule: per-symbol-ATR customizations are non-stackable. iter-v3/046 = REVERT to single-symbol per-symbol-ATR (ALGO only) and pivot to universal axes |`

The diary commit closes the catalog row regardless of outcome. The 5-row pre-commit prevents
post-hoc rationalization.

---

## Section 12 — Phase 5.5 Gate Self-Check (10 mandatory sections inventory)

| # | Section | Status |
|---|---|---|
| 1 | Section 0 — Data Split Declaration | PRESENT (sacred constants UNCHANGED) |
| 2 | Section 1 — Hypothesis | PRESENT (per-symbol ATR widening LDO; expected effect; mechanism named) |
| 3 | Section 2 — IS-Only Numerical Evidence | PRESENT (7 sub-sections; 5 numerical tables; falsifiers with explicit thresholds; behavioral-effect predictor) |
| 4 | Section 3 — Proposed Changes | PRESENT (6 sub-fixes; bundle state verification table with 19 assertions) |
| 5 | Section 4 — Expected OOS Impact | PRESENT (PATH A/B-INERT/B-MECHANICAL/C bands; pre-registered classification thresholds) |
| 6 | Section 5 — Risk Mitigation | PRESENT (R1/R2/R3 + LDO ATR risk + stacking risk + IS trade-rate stability + cross-symbol contagion) |
| 7 | Section 7 — Pre-Registered Failure-Mode Prediction | PRESENT (4 plausible failure modes; most plausible PROMISING-INERT; 2nd PROMISING-MECHANICAL; 3rd NEGATIVE-LDO-deepens; 4th architecture-bug) |
| 8 | Section 8 — Pre-Registered MERGE/NO-MERGE Criteria | PRESENT (PATH A/B-INERT/B-MECHANICAL/C with locked thresholds) |
| 9 | Section 9 — Library Stack | PRESENT (UNCHANGED from iter-v3/044) |
| 10 | Section 10 — QR Audit Trail | PRESENT (NEW required per `feedback_v3_axis_selection_quant_discipline.md`; EDA SHA cited; QR-driven selection rationale) |
| 11 | Section 11 — Catalog-Row Pre-Commit | PRESENT (5 outcomes pre-registered) |

**All 11 sections (10 mandatory + Section 11 pre-commit) PRESENT.** Engineer's Phase 5.5
gate should PASS this brief.

---

## Section 13 — Status

**READY-FOR-PHASE-5.5** — research brief complete. Engineer reads this brief, verifies the
sections, runs the bundle state assertions, runs the updated 5 adversarial pytest tests
(test_atr_multipliers_for_symbol.py with iter-v3/045 expectations), and writes
`phase5p5_gate.md` with OVERALL=PASS. Phase 6 backtest then runs at single-seed
--exploration; budget 25-35 min; well within 2h cap.

After Phase 6 closes, Critic Phase 7.5 review fires; QR Phase 7 evaluates OOS for first
time; QR Phase 8 closes the catalog row at one of the 5 pre-registered dispositions.

iter-v3/045 is cycle 3 #6 of 10; 4 EXPLORATIONs remain in this cycle (iter-v3/046, /047, /048,
/049); CONFIRMATION at iter-v3/050.
