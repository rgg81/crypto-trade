# Iteration v3-032 — Research Brief

**Type**: EXPLORATION (cadence #4 of 10 in post-iter-v3/028 cycle; **STRUCTURAL axis (Category 7 — NEW per-symbol-LABELING architecture)** — first iteration in v3 history where individual model heads use DIFFERENT triple-barrier ATR multipliers per symbol; methodology innovation triggered by iter-v3/031 Critic FINAL diagnosis of LDO regime mismatch as a LABELING-layer problem)
**Track**: v3 (rigor arm) — thirty-second iteration
**Branch**: `iteration-v3/032` (off `iter-v3/031` head)
**Date**: 2026-05-08
**Author**: QR (autopilot)

---

## Section 0 — Data Split Declaration

```
OOS_CUTOFF_DATE  = 2025-03-24    # IMMUTABLE
training_months  = 24             # IMMUTABLE
ENSEMBLE_SIZE    = 1              # SET BY --exploration
ensemble_seeds   = _derive_ensemble_seeds(outer_seed, size=1)
n_trials         = 35             # default per feedback_v3_exploration_n_trials_35
colsample_bytree = 1.0            # HARDCODED by --exploration
OOS_CUTOFF_MS    = 1742774400000
```

**Sacred constants UNCHANGED.** IS window: 2023-03-24 to 2025-03-23 (24 months). OOS window: 2025-03-24 onward. The QR sees iter-v3/032 OOS metrics for the FIRST time in Phase 7. This brief is produced reading ONLY: iter-v3/007–031 briefs / engineering reports / Critic FINALs / diaries; iter-v3/032 EDA artifact (committed BEFORE this brief at SHA `9834e84` — Phase 1 per-symbol ATR distribution analysis). The EDA reads ONLY pre-OOS-cutoff IS-window feature parquets + iter-v3/029 IS trades.csv. iter-v3/029 OOS exit-reason composition is reported informationally but NOT used in candidate scoring or recommendation logic.

---

## Section 0.5 — Iteration Type Declaration

```
TYPE: EXPLORATION (cadence #4 of 10 in post-iter-v3/028 cycle)
Wall-clock budget: ≤ 2h hard cap (per feedback_v3_cadence_discipline.md)
Single-axis variation: NEW per-symbol-LABELING architecture
                       (LDO model: ATR multipliers (2.0, 1.0) → (1.5, 0.75); 0.75× scale)
                       (BCH+TRX+ALGO models: ATR multipliers (2.0, 1.0) UNCHANGED)
                       + RESTORE LDOUSDT to V3_MODELS (3 → 4: BCH+LDO+TRX+ALGO)
                       + REQUIRED_GAP 66 → 88 (formula consequence of n_symbols 3 → 4)
Cadence: 4 of 10 EXPLORATIONs in this cycle (next CONFIRMATION = iter-v3/039)
Axis category: 7 (NEW labeling-architecture variant — per-symbol ATR multipliers)
ANCHOR: iter-v3/029 single-seed (PROMISING; +0.7926 IS / +1.7653 OOS,
        4-symbol BCH+LDO+TRX+ALGO; LDO contribution -3.07 OOS / +40.03 IS)
NOT a gate-threshold knob. NOT a feature-pruning variation. NOT a feature-add variation.
NOT a risk-primitive variation. NOT a model architecture change (still LightGBM + RiskV3Wrapper).
NOT a universe variation in net (LDO restored at iter-v3/031's drop reversal).
This iteration NEVER updates BASELINE_V3.md (single-seed --exploration mode).
```

**Justification — STRUCTURAL per-symbol-LABELING architecture (Category 7 NEW)**:

iter-v3/030 NEGATIVE (per-symbol features for LDO): LDO subset hurt; per-symbol-feature axis closed for LDO.

iter-v3/031 NEGATIVE (DROP LDO): LDO IS-positive (+40.03 weighted_pnl) means dropping it killed IS aggregate Sharpe (+0.79 → +0.28, Δ -0.51) — drop-MKR precedent didn't transfer because LDO is IS-positive/OOS-marginally-negative (overfit signature), NOT a true drag like MKR was (-23/-25). The Critic FINAL of iter-v3/031 (`12ca079`) explicitly recommended axis = **RESTORE LDO + per-symbol ATR multipliers** as the next iteration:

> *"LDO's issue is REGIME MISMATCH (different volatility profile) → addressable at LABELING layer, not feature layer. ATR(2.0, 1.0) is universal across all symbols; LDO might need different multipliers."*

This brief implements the recommendation. The architecture parallels V3_FEATURES_PER_SYMBOL from iter-v3/030 (which validated the per-symbol dispatch architecture as bit-identical when subset matches default — see iter-v3/030 BCH/TRX/ALGO bit-identity in engineering report). The new axis introduces the same dispatch pattern at the labeling layer: V3_ATR_MULTIPLIERS_PER_SYMBOL with helper `atr_multipliers_for_symbol(symbol)` defaulting to (2.0, 1.0).

**Why this is NOT a violation of `feedback_v3_engineered_features_proven.md`**:

That rule applies at the portfolio feature-set level (regime_momentum_signed_5d MUST remain in V3_FEATURE_COLUMNS). iter-v3/032 keeps V3_FEATURE_COLUMNS=14 BIT-IDENTICAL to iter-v3/029 (regime_momentum_signed_5d included). The variation is at the LABELING layer for LDO only.

**Why this is NOT a violation of `feedback_v3_drop_symbol_requires_dual_drag.md` (recommended at iter-v3/031 Critic)**:

Per the iter-v3/031 Critic's recommended memory rule, LDO does NOT meet the dual-drag (IS-neg AND OOS-neg) bar required to drop. Restoring LDO honors this rule directly.

**Single-axis discipline**: ONE NEW architectural element (per-symbol ATR multipliers; LDO subset (1.5, 0.75); BCH+TRX+ALGO unchanged at default (2.0, 1.0)). V3_FEATURE_COLUMNS=14 BIT-IDENTICAL. V3_MODELS net unchanged at 4 (LDO restored at iter-v3/031's drop reversal). REQUIRED_GAP=88 restored (mandatory formula consequence of n_symbols=4). KEEP regime_momentum_signed_5d. KEEP 7-primitive risk gate stack BIT-IDENTICAL. KEEP V3_FEATURES_PER_SYMBOL empty (iter-v3/030 LDO 7-feat subset NOT restored — that axis closed NEGATIVE).

After iter-v3/032 the catalog will have: 16 unique axis representations (15 prior + iter-v3/032 NEW per-symbol-LABELING architecture).

---

## Section 1 — Hypothesis

Adding a per-symbol triple-barrier ATR multiplier subset for LDO ((1.5, 0.75) replacing default (2.0, 1.0); BCH+TRX+ALGO unchanged at default per `atr_multipliers_for_symbol()` fallback) will **align LDO's effective barrier widths in price-% terms with the peer (BCH/TRX/ALGO) median, lifting LDO IS+OOS contribution from -3.07 OOS / +40.03 IS (single-seed iter-v3/029) toward a more peer-like exit-reason composition (more take_profit hits, fewer stop_loss whipsaws), while leaving BCH+TRX+ALGO contributions BIT-IDENTICAL** (their ATR multipliers, training data, hyperparameter search spaces, and ensemble seeds are unchanged via the dict fallback). Predicted IS Sharpe band [+0.70, +1.10] median +0.90 (anchor iter-v3/029 +0.79; LDO labeling improvement plausibly lifts at IS aggregate). Predicted OOS Sharpe band [+1.50, +2.00] median +1.75 (anchor +1.77; LDO contribution likely shifts toward 0 or positive; bands honestly reflect single-seed-lottery uncertainty).

**Mechanism explanation** (why per-symbol ATR multipliers should help on LDO specifically): LDO's median natr_21_raw = 5.0068 vs peer (BCH/TRX/ALGO) median 3.6959 — LDO has **1.35× HIGHER realized volatility** than peers. At the universal (2.0, 1.0) multipliers, LDO's effective TP barrier is 10.01% (vs peer 7.39%) and SL barrier 5.01% (vs peer 3.70%). LDO's barriers are **TOO WIDE** in price-% terms — labels carve trades into "huge winners or huge losers", missing the medium-magnitude moves that the LightGBM model is most likely to predict reliably. The 0% IS timeout rate confirms barriers fire before the 21-candle timeout — the geometry is structurally different from peers.

The iter-v3/032 EDA (SHA `9834e84`) shows the chosen 0.75× scaling produces:
- LDO TP barrier 7.51% / SL barrier 3.76% (LDO/peer ratio 1.0160 — closest to 1.0 in candidate grid)
- Effective triple-barrier geometry matches the peer regime that has been profitable across 9 iterations
- LDO IS hit-rate composition is expected to shift from 46.7% TP / 53.3% SL / 0.0% timeout toward peer-aggregate 30.6% TP / 63.2% SL / 6.2% timeout

**Why per-symbol ATR multipliers may NOT lift OOS** (3 PATH-suspect scenarios):

1. **PATH A-MARGINAL — PROMISING-INERT (Falsifier 1 fires): trade-roster bit-identical.** The (1.5, 0.75) multipliers produce a model whose trades are bit-identical (or very near-bit-identical) to iter-v3/029's LDO trades. Causes: (a) Optuna at n_trials=35 with the same outer seed converges to similar hyperparameters; (b) the new labels still produce similar LightGBM decision boundaries because LDO's underlying signal is the binding constraint, not the barrier geometry. PROMISING-MECHANICAL or NULL-RESULT. Probability: 15-20%.
2. **PATH B — LDO regression deepens.** LDO's signal is structurally weak; tighter barriers don't help and may hurt by producing more frequent SL hits as noise penetration increases at the tighter SL. OOS LDO < -10% weighted_pnl. PATH B; close per-symbol-LABELING axis on LDO. Probability: 25-30% (the bear prior; LDO has been OOS-negative across 9 iterations).
3. **PATH C — BCH/TRX/ALGO regression** (Falsifier 2 fires). The unchanged-multiplier symbols' decisions or PnL drift materially from iter-v3/029 due to: (a) per-symbol ATR-multiplier dispatch path bug; (b) global Optuna seed perturbation through dict-based resolution; (c) `LightGbmStrategy` constructor receives non-default ATR multipliers via accidental cross-pollination. PATH C — REVERT and diagnose. Probability: <10% (engineering risk; mitigated by adversarial test in Section 10).

The counterfactual evidence Phase 1 cites (LDO natr_21_raw 35% higher than peer median; 0% IS timeout rate is structurally distinct; LDO's exit-reason composition is uniquely barrier-saturating) shows LDO's volatility regime is genuinely differential. The empirical question this EXPLORATION answers is whether the regime-aligned barriers translate into productive LightGBM fitting at single-seed n_trials=35 when LDO's training labels are reshaped to match peer effective barrier widths.

---

## Section 2 — IS-Only Numerical Evidence + Behavioral-Effect Predictor

**Phase 1 EDA**: `analysis/iteration_v3-032/per_symbol_atr_eda.py` (committed at SHA `9834e84` BEFORE this brief — Phase 5.5 reproducibility requirement).

**Inputs read** (IS-only):
- `data/features_v3/{BCHUSDT,LDOUSDT,TRXUSDT,ALGOUSDT}_8h_features.parquet` (column `natr_21_raw`, IS-window only)
- `reports-v3/iteration_v3-029/in_sample/trades.csv` (4-symbol IS trades; exit-reason composition)
- `reports-v3/iteration_v3-029/out_of_sample/trades.csv` (informational only; NOT used in candidate scoring)

**Outputs** (committed alongside the script at SHA `9834e84`):
- `per_symbol_atr_distribution.csv` — per-symbol natr_21_raw IS-window percentiles
- `per_symbol_label_outcome_pattern.csv` — per-symbol exit-reason composition at iter-v3/029
- `per_symbol_label_outcome_pattern_oos.csv` — informational OOS composition
- `atr_multiplier_recommendation.csv` — per-symbol recommended multipliers
- `ldo_candidate_grid.csv` — 8-row candidate grid with effective barrier ratios
- `synthesis.md` — narrative + chosen LDO multipliers

### 2.1 Per-symbol natr_21_raw IS-window distribution

| symbol | n_is_natr | min | p25 | median | p75 | p95 | mean | std |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| BCHUSDT | 5727 | 1.36 | 3.03 | 3.70 | 4.93 | 7.62 | 4.21 | 1.95 |
| LDOUSDT | 2741 | 2.00 | 4.18 | **5.01** | 6.50 | 8.39 | 5.36 | 1.69 |
| TRXUSDT | 5669 | 0.77 | 1.65 | 2.65 | 4.11 | 7.68 | 3.27 | 2.18 |
| ALGOUSDT | 5225 | 1.78 | 3.50 | 4.77 | 6.44 | 9.71 | 5.27 | 2.40 |

**Peer (BCH+TRX+ALGO) median**: 3.6959 | **LDO median**: 5.0068 | **LDO/peer ratio**: **1.3547**.

LDO has the SECOND-HIGHEST median natr (after ALGO) but the LOWEST std relative to mean (CV = 0.32 vs ALGO 0.46, BCH 0.46, TRX 0.67). LDO's volatility distribution is NARROWER (less skewed-right) than peers — LDO has a tighter, higher-mean vol regime.

### 2.2 Per-symbol IS exit-reason composition (iter-v3/029 trades.csv)

| symbol | n_trades | n_tp | n_sl | n_timeout | %_tp | %_sl | %_timeout | mean_pnl |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| BCHUSDT | 94 | 29 | 56 | 9 | 30.9% | 59.6% | 9.6% | +0.371 |
| LDOUSDT | 15 | 7 | 8 | **0** | **46.7%** | **53.3%** | **0.0%** | +2.669 |
| TRXUSDT | 85 | 25 | 56 | 4 | 29.4% | 65.9% | 4.7% | -0.068 |
| ALGOUSDT | 63 | 20 | 41 | 2 | 31.7% | 65.1% | 3.2% | -0.052 |

**LDO is structurally different**: 0% timeout rate AND highest %_tp (46.7%) AND highest mean_pnl per trade (+2.669). LDO's trades are BARRIER-DOMINATED — every trade hits TP or SL within 21 candles. LDO's high mean_pnl reflects the +40.03 IS aggregate (small n_trades but large per-trade magnitude). The peer aggregate (BCH+TRX+ALGO): 30.6% TP / 63.2% SL / 6.2% timeout.

The LABELING-layer hypothesis: the (2.0, 1.0) multipliers compute LDO's TP at 10.01% and SL at 5.01% — TOO WIDE relative to peer barriers (TP 7.39% / SL 3.70%). LDO's 0% timeout rate confirms barriers fire on every trade; the model fits to a label distribution dominated by these wider-than-peer barriers, which may not match the per-trade signal-prediction distribution LightGBM produces.

### 2.3 LDO candidate ATR multiplier grid

| scale | atr_tp | atr_sl | LDO_tp_barrier% | LDO_sl_barrier% | peer_tp_barrier% | LDO/peer_tp_ratio |
|---:|---:|---:|---:|---:|---:|---:|
| 0.500 | 1.0000 | 0.5000 | 5.01 | 2.50 | 7.39 | 0.6774 |
| 0.625 | 1.2500 | 0.6250 | 6.26 | 3.13 | 7.39 | 0.8467 |
| **0.750** | **1.5000** | **0.7500** | **7.51** | **3.76** | **7.39** | **1.0160** |
| 0.875 | 1.7500 | 0.8750 | 8.76 | 4.38 | 7.39 | 1.1854 |
| 1.000 | 2.0000 | 1.0000 | 10.01 | 5.01 | 7.39 | 1.3547 |
| 1.125 | 2.2500 | 1.1250 | 11.27 | 5.63 | 7.39 | 1.5240 |
| 1.250 | 2.5000 | 1.2500 | 12.52 | 6.26 | 7.39 | 1.6934 |
| 1.500 | 3.0000 | 1.5000 | 15.02 | 7.51 | 7.39 | 2.0321 |

**Chosen LDO multipliers: (1.5, 0.75)** — scale 0.75×. LDO/peer TP barrier ratio 1.0160 (closest to 1.0 in the grid). This aligns LDO's effective triple-barrier geometry with the peer regime.

### 2.4 Behavioral-effect predictor (per `feedback_axis_saturation_predictor.md`)

**Predicted LDO IS trade volume change**: iter-v3/029 single-seed LDO IS trades = 15 (per `reports-v3/iteration_v3-029/in_sample/per_symbol.csv`). Tighter barriers (0.75× scale) typically:
- INCREASE LDO trade volume by 20-50% (tighter barriers fire faster → cooldown re-armed sooner → more trade opportunities) — predicted band [18, 23] LDO IS trades.
- DECREASE LDO trade volume by 0-15% (cleaner labels → tighter probability thresholds → fewer marginal trades) — predicted band [13, 15].
- LEAVE LDO trade volume bit-identical — Falsifier 1 fires (NULL-RESULT or PROMISING-MECHANICAL).

Net predicted LDO IS trade band: **[15, 23]** trades (range +0% to +50% of iter-v3/029's 15). Predicted bundle-level IS trades: [260, 270] (iter-v3/029 was 257; +3 to +13 from LDO-only delta; BCH+TRX+ALGO bit-identical).

**Predicted LDO IS hit-rate composition shift**: tighter barriers should compress %_tp toward peer aggregate (30.6%) AND introduce non-zero timeout rate (>0%). Specifically:
- Predicted %_tp_LDO: [30%, 50%] (shift toward peer; current 46.7%).
- Predicted %_sl_LDO: [50%, 65%] (shift toward peer; current 53.3%).
- Predicted %_timeout_LDO: [0%, 8%] (shift toward peer 6.2%; current 0%). **Non-zero timeout rate is the diagnostic signature** — if LDO timeout rate stays at 0%, the barriers are still saturating despite the 0.75× compression.

**Predicted OOS LDO weighted_pnl**: iter-v3/029 LDO OOS = -3.07%. Tighter barriers + regime alignment hypothesis predicts band **[-3.0%, +10.0%]** (median +3.0%). Lift required: at minimum, LDO OOS ≥ 0% to validate regime-alignment hypothesis.

**Saturation falsifier** (per `feedback_axis_saturation_predictor.md` ±25% rule): if observed LDO IS trades ∈ [12, 18] AND LDO trade-roster is **bit-identical** to iter-v3/029 LDO, axis SATURATED — the (1.5, 0.75) multipliers did not propagate to model output. Classify PROMISING-MECHANICAL or NULL-RESULT. If observed LDO IS trades < 11, axis OVERSHOOT-DOWN; if > 25, axis OVERSHOOT-UP — flag for risk-amplification review.

**Falsifier 1 — Bit-identical LDO trade roster** (load-bearing for axis classification): if iter-v3/032 LDO trades are bit-identical (same open_time, close_time, side, sl/tp/exit triggers) to iter-v3/029 LDO trades, the axis is **mechanically inert** — the (1.5, 0.75) labels produced the same decisions as the (2.0, 1.0) labels. PROMISING-MECHANICAL (sister to iter-v3/013 drop-MKR per `feedback_promising_mechanical_subtype.md`). NOT compoundable with regime_momentum_signed_5d as a CONFIRMATION-bundle ingredient.

**Falsifier 2 — BCH+TRX+ALGO bit-identity** (load-bearing): BCH+TRX+ALGO trade rosters MUST be bit-identical to iter-v3/029. If any of the 3 symbols' rosters drift, the per-symbol-ATR-multiplier dispatch path has unintended side-effects (most likely: a global Optuna seed or random-state cross-pollination through the dict-based atr_multipliers_for_symbol resolution). PATH C — REVERT and diagnose.

**Falsifier 3 — LDO drag worsens**: LDO OOS weighted_pnl < -10% (worse than iter-v3/029's -3.07%). Tighter barriers FAILED on LDO; close per-symbol-LABELING axis on LDO. PATH B.

**Falsifier 4 — Unintended portfolio Sharpe drop**: bundle OOS Sharpe < +1.50 (Δ < -0.27 vs iter-v3/029 single-seed +1.7653). Even if LDO improves, unintended interaction effects somewhere in the 4-symbol stack drove the bundle below the iter-v3/029 anchor. PATH C — REVERT.

### 2.5 Counterfactual: LDO contribution under PATH A

iter-v3/029 single-seed bundle metrics (same 4-symbol universe, baseline ATR):

| Symbol | OOS weighted_pnl % | OOS Conc % |
|---|---:|---:|
| TRXUSDT | +29.24% | 50.59% |
| ALGOUSDT | +20.87% | 36.11% |
| BCHUSDT | +10.75% | 18.60% |
| LDOUSDT | **-3.07%** | -5.31% |
| **Total** | **+57.79%** | (numerator) |

Under PATH A counterfactual LDO OOS = +3.0% (median band):

| Symbol | OOS weighted_pnl % | OOS Conc % (LDO+3.0%) |
|---|---:|---:|
| TRXUSDT | +29.24% | 48.18% |
| ALGOUSDT | +20.87% | 34.39% |
| BCHUSDT | +10.75% | 17.71% |
| LDOUSDT | **+3.00%** | 4.94% |
| **Total** | **+60.69%** | (numerator) |

Total OOS weighted_pnl lift: +2.90 pp (from +57.79% to +60.69%). Daily Sharpe lift estimate: +0.05 to +0.15 (PnL lift on similar trade count). This is the **median floor** of PATH A — actual lift may be larger if regime-aligned LDO labels produce a higher LDO trade count (predicted [15, 23]) which expands LDO's denominator share at positive contribution.

Under PATH A-MARGINAL INERT counterfactual (LDO trades bit-identical, LDO OOS = -3.07%): bundle OOS = +57.79% UNCHANGED. Sharpe ≈ +1.7653 UNCHANGED. PROMISING-MECHANICAL classification.

This is the **lower bound** of the per-symbol-LABELING architecture's contribution: even if LDO doesn't improve, the architecture is informationally validated as *strictly architectural neutral* — paving the way for iter-v3/033+ to apply per-symbol ATR multipliers to other symbols without architectural risk.

---

## Section 3 — Sub-fixes (7-item) with Verifier Commands

| # | Sub-fix | File | Description | Verifier |
|---|---|---|---|---|
| 1 | **RESTORE LDOUSDT to V3_MODELS** | `run_baseline_v3.py` | Add `("C (LDOUSDT)", "LDOUSDT")` back to `V3_MODELS` tuple. New V3_MODELS = 4 symbols: BCH+LDO+TRX+ALGO (iter-v3/029 byte-identical universe). | `uv run python -c "from importlib import import_module; import sys; sys.path.insert(0,'.'); m=import_module('run_baseline_v3'); assert len(m.V3_MODELS)==4 and ('C (LDOUSDT)','LDOUSDT') in m.V3_MODELS"` |
| 2 | **REQUIRED_GAP 66 → 88** | `src/crypto_trade/strategies/ml/validation_v3.py` | `REQUIRED_GAP: int = (21 + 1) * 4  # 88` (4-symbol universe). | `uv run python -c "from crypto_trade.strategies.ml.validation_v3 import REQUIRED_GAP; assert REQUIRED_GAP == 88"` |
| 3 | **Add `V3_ATR_MULTIPLIERS_PER_SYMBOL` dict** | `src/crypto_trade/features_v3/__init__.py` | Add `V3_ATR_MULTIPLIERS_PER_SYMBOL: dict[str, tuple[float, float]]` constant. Maps `LDOUSDT` to `(1.5, 0.75)`. BCH/TRX/ALGO not specified → falls back to `DEFAULT_ATR_MULTIPLIERS = (2.0, 1.0)`. | `uv run python -c "from crypto_trade.features_v3 import V3_ATR_MULTIPLIERS_PER_SYMBOL; assert V3_ATR_MULTIPLIERS_PER_SYMBOL.get('LDOUSDT') == (1.5, 0.75)"` |
| 4 | **Add `atr_multipliers_for_symbol()` helper** | `src/crypto_trade/features_v3/__init__.py` | Helper returning `V3_ATR_MULTIPLIERS_PER_SYMBOL[symbol]` if symbol in dict, else `DEFAULT_ATR_MULTIPLIERS`. | `uv run python -c "from crypto_trade.features_v3 import atr_multipliers_for_symbol; assert atr_multipliers_for_symbol('BCHUSDT') == (2.0, 1.0); assert atr_multipliers_for_symbol('LDOUSDT') == (1.5, 0.75)"` |
| 5 | **Runner uses `atr_multipliers_for_symbol(symbol)`** | `run_baseline_v3.py` | In `_build_v3_model`, replace hardcoded `atr_tp_multiplier=2.0, atr_sl_multiplier=1.0` with values from `atr_multipliers_for_symbol(symbol)`. Add import. | `grep -n 'atr_multipliers_for_symbol' run_baseline_v3.py` shows the import + the `_build_v3_model` call site. |
| 6 | **ITERATION_LABEL update v3-031 → v3-032** | `run_baseline_v3.py` | Update `ITERATION_LABEL = "v3-032"`. | `grep '^ITERATION_LABEL' run_baseline_v3.py` shows `"v3-032"` |
| 7 | **Restore `_verify_label_leakage_gap()` n_symbols=4 message** | `run_baseline_v3.py` | The docstring/comment in `_verify_label_leakage_gap()` references n_symbols=3 (from iter-v3/031). Restore to n_symbols=4 (iter-v3/029/032). The formula `(timeout_candles + 1) * n_symbols` is dynamic from `len(V3_MODELS)`. | `grep -n 'n_symbols' run_baseline_v3.py | grep -q '4'` (in gap comment) |

**V3_FEATURE_COLUMNS = 14 unchanged** — `regime_momentum_signed_5d` preserved. **V3_FEATURES_PER_SYMBOL stays empty** (iter-v3/030 LDO 7-feat subset NOT restored — that axis closed NEGATIVE).

**Reconciliation table** (Engineer Phase 5.5 verifier — 8 commands):

```
1. uv run python -c "from importlib import import_module; import sys; sys.path.insert(0,'.'); m=import_module('run_baseline_v3'); assert len(m.V3_MODELS)==4 and ('C (LDOUSDT)','LDOUSDT') in m.V3_MODELS"
2. uv run python -c "from crypto_trade.strategies.ml.validation_v3 import REQUIRED_GAP; assert REQUIRED_GAP == 88"
3. uv run python -c "from crypto_trade.features_v3 import V3_ATR_MULTIPLIERS_PER_SYMBOL, DEFAULT_ATR_MULTIPLIERS; assert V3_ATR_MULTIPLIERS_PER_SYMBOL.get('LDOUSDT') == (1.5, 0.75); assert DEFAULT_ATR_MULTIPLIERS == (2.0, 1.0)"
4. uv run python -c "from crypto_trade.features_v3 import atr_multipliers_for_symbol; assert atr_multipliers_for_symbol('BCHUSDT') == (2.0, 1.0); assert atr_multipliers_for_symbol('LDOUSDT') == (1.5, 0.75); assert atr_multipliers_for_symbol('TRXUSDT') == (2.0, 1.0); assert atr_multipliers_for_symbol('ALGOUSDT') == (2.0, 1.0)"
5. uv run python -c "from crypto_trade.features_v3 import V3_FEATURE_COLUMNS; assert len(V3_FEATURE_COLUMNS) == 14 and 'regime_momentum_signed_5d' in V3_FEATURE_COLUMNS"
6. uv run python -c "from crypto_trade.features_v3 import V3_FEATURES_PER_SYMBOL; assert V3_FEATURES_PER_SYMBOL == {}"
7. grep '^ITERATION_LABEL' run_baseline_v3.py | grep -q '"v3-032"'
8. uv run pytest tests/features_v3/test_atr_multipliers_for_symbol.py -v
```

**Adversarial Test (mandatory pytest)** — `tests/features_v3/test_atr_multipliers_for_symbol.py`:

```python
"""Adversarial test for iter-v3/032 per-symbol ATR multipliers."""

def test_atr_multipliers_default():
    """Symbols not in V3_ATR_MULTIPLIERS_PER_SYMBOL fall back to (2.0, 1.0)."""
    from crypto_trade.features_v3 import atr_multipliers_for_symbol, DEFAULT_ATR_MULTIPLIERS
    assert DEFAULT_ATR_MULTIPLIERS == (2.0, 1.0)
    assert atr_multipliers_for_symbol("BCHUSDT") == (2.0, 1.0)
    assert atr_multipliers_for_symbol("TRXUSDT") == (2.0, 1.0)
    assert atr_multipliers_for_symbol("ALGOUSDT") == (2.0, 1.0)
    assert atr_multipliers_for_symbol("UNKNOWN_SYMBOL") == (2.0, 1.0)


def test_atr_multipliers_ldo():
    """LDO returns the iter-v3/032 EDA-tuned (1.5, 0.75) multipliers."""
    from crypto_trade.features_v3 import atr_multipliers_for_symbol, V3_ATR_MULTIPLIERS_PER_SYMBOL
    assert "LDOUSDT" in V3_ATR_MULTIPLIERS_PER_SYMBOL
    assert V3_ATR_MULTIPLIERS_PER_SYMBOL["LDOUSDT"] == (1.5, 0.75)
    assert atr_multipliers_for_symbol("LDOUSDT") == (1.5, 0.75)


def test_atr_multipliers_runner_dispatch():
    """The runner's _build_v3_model uses atr_multipliers_for_symbol() and
    correctly applies different multipliers per symbol."""
    import sys
    from pathlib import Path
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
    from run_baseline_v3 import _build_v3_model

    cfg_bch, strat_bch = _build_v3_model(
        symbol="BCHUSDT", seed=42, n_trials=1, ensemble_seeds=[42]
    )
    cfg_ldo, strat_ldo = _build_v3_model(
        symbol="LDOUSDT", seed=42, n_trials=1, ensemble_seeds=[42]
    )
    # The strategy is RiskV3Wrapper(LightGbmStrategy); attribute access goes
    # through the wrapper to the inner M1.
    assert strat_bch._m1.atr_tp_multiplier == 2.0
    assert strat_bch._m1.atr_sl_multiplier == 1.0
    assert strat_ldo._m1.atr_tp_multiplier == 1.5
    assert strat_ldo._m1.atr_sl_multiplier == 0.75
```

---

## Section 4 — Predicted Bands & Catalog Framings

**Anchor (iter-v3/029 single-seed PROMISING)**:
- iter-v3/029 single-seed IS Sharpe = +0.7926 / OOS Sharpe = +1.7653
- iter-v3/029 LDO OOS = -3.07% / iter-v3/029 LDO IS = 15 trades / +40.03% net_pnl
- iter-v3/029 LDO IS exit composition: 46.7% TP / 53.3% SL / 0.0% timeout
- iter-v3/028 multi-seed IS Sharpe = +0.5101 / OOS Sharpe = +0.5053 (formal BASELINE_V3.md)

**Single-seed iter-v3/032 expectation** (PROMISING bands shifted to iter-v3/029 anchor):

| Band | IS Sharpe | OOS Sharpe | LDO OOS PnL | LDO IS trades | Interpretation |
|---|---:|---:|---:|---:|---|
| PATH A — PROMISING (clean) | [+0.85, +1.10] | [+1.85, +2.05] | [≥0%, +10%] | [16, 23] | LDO labeling lift; bundle maintained |
| PATH A-MARGINAL — PROMISING-INERT | ~+0.79 | ~+1.77 | ~-3% | ~15 | LDO bit-identical (Falsifier 1 fires); axis MECHANICAL |
| PATH B — NEGATIVE (LDO worsens) | [+0.65, +0.85] | [+1.50, +1.75] | [-15%, -8%] | [13, 22] | LDO drag deepens; close per-symbol-LABELING axis on LDO |
| PATH C — NEGATIVE (architecture bug) | < +0.65 | < +1.50 | varies | varies | BCH/TRX/ALGO drift (Falsifier 2 fires); REVERT |

**§4.4 catalog framing table** (4 rows):

| # | Verdict | Conditions | Catalog row tag |
|---|---|---|---|
| 1 | EXPLORATION-PROMISING (clean) | LDO OOS PnL ≥ 0 AND BCH+TRX+ALGO bit-identical AND bundle OOS Sharpe ≥ +1.85 AND LDO trade-roster differs from iter-v3/029 (Falsifier 1 PASS) | YES — STRONG candidate; iter-v3/039 CONFIRMATION-bundle ingredient (compoundable with regime_momentum + ALGO universe expansion as "per-symbol LABELING-architecture decision") |
| 2 | EXPLORATION-PROMISING-MECHANICAL | LDO trade-roster bit-identical to iter-v3/029 (Falsifier 1 fires) AND BCH+TRX+ALGO bit-identical (Falsifier 2 PASS) AND bundle metrics bit-identical | NO — strictly architectural (sister to iter-v3/013 drop-MKR per `feedback_promising_mechanical_subtype.md`); per-symbol-LABELING methodology validated as architecturally-neutral; iter-v3/033 may apply the architecture to a DIFFERENT symbol with stronger per-symbol-natr dispersion |
| 3 | EXPLORATION-NEGATIVE (LDO drag) | LDO OOS PnL < -10% (Falsifier 3 fires) AND BCH+TRX+ALGO bit-identical | NO — closes per-symbol-LABELING axis on LDO; tighter barriers structurally inappropriate; iter-v3/033 = different axis category |
| 4 | EXPLORATION-NEGATIVE (architecture bug) | BCH/TRX/ALGO non-bit-identical to iter-v3/029 (Falsifier 2 fires) | NO — REVERT and diagnose; iter-v3/033 = different axis category after architectural fix; per-symbol-LABELING discipline cannot proceed until clean dispatch path established |

---

## Section 5 — Risk Mitigation

### Cadence-discipline risks (4)

| Risk | Mitigation |
|---|---|
| iter-v3/032 EXPLORATION budget overrun | Hard 2h wall-clock cap. iter-v3/032 is a 4-symbol single-seed run identical structure to iter-v3/029 (~30 min) — only difference is LDO's (1.5, 0.75) ATR multipliers (similar Optuna search space; barrier-width changes don't materially affect LightGBM training time). Estimate 25-35 min. Well within cap. |
| Cycle-cadence inflation | iter-v3/032 is FOURTH EXPLORATION of new cycle; 6 EXPLORATIONs remaining; CONFIRMATION at iter-v3/039. STRICT 10:1 per `feedback_v3_strict_10_to_1_cadence.md`. |
| Catalog-row pre-commit cleanup | Section 11 pre-commits 4 dispositions. Diary commit closes catalog row regardless of outcome. |
| Single-axis discipline drift | ONE NEW architectural element (per-symbol ATR multipliers; LDO subset (1.5, 0.75)); V3_FEATURE_COLUMNS UNCHANGED; V3_MODELS net unchanged at 4 (LDO restoration is iter-v3/031's drop reversal); risk gates UNCHANGED; V3_FEATURES_PER_SYMBOL stays empty (iter-v3/030 axis closed NEGATIVE; not re-introduced). Engineer Phase 6 rejection if any other knob is tuned. |

### Methodology-hygiene risks (4)

| Risk | Mitigation |
|---|---|
| OOS contamination | EDA reads only iter-v3/029 IS-only trades + IS-window features parquet. iter-v3/029 OOS exit-reason composition is reported informationally for sanity check — NOT used in candidate scoring. Phase 7 is QR's first iter-v3/032 OOS view. |
| Look-ahead in LDO multipliers | LDO multipliers (1.5, 0.75) are computed on iter-v3/029 IS-only natr_21_raw distribution + iter-v3/029 IS-only exit-reason composition; the iter-v3/032 LDO model's training labels apply (1.5, 0.75) to LDO's training data with NO information from OOS. The natr_21_raw at any timestamp t uses only past returns (21-bar Wilder ATR with proper `.shift(1)` discipline already verified at iter-v3/025 SHA `3b1f979`). |
| Survivorship bias | LDO listed 2024-09 (33+ months IS). No survivorship issue. The vol-regime hypothesis is structural, not survivor-related. |
| Concentration risk | With 4 symbols (BCH+LDO+TRX+ALGO) the iter-v3/029 baseline TRX concentration was 50.59% — UNCHANGED expectation here unless LDO PnL share grows materially (which would, helpfully, dilute TRX share). The concentration constraint is pre-registered as OUTSTANDING per BASELINE_V3.md §"Failed MERGE Gates"; iter-v3/032 does not worsen it relative to iter-v3/029. |

### Axis-specific risks (3)

| Risk | Mitigation |
|---|---|
| LDO model collapse at single-seed n_trials=35 with (1.5, 0.75) labels | Per-symbol architecture isolates LDO; if LDO fits poorly under tighter barriers, BCH+TRX+ALGO are unaffected (default fallback preserves their multipliers). Engineering report records per-symbol IS PnL, OOS PnL, OOS WR, n_trades, exit-reason composition; if LDO collapses (OOS < -10%), Falsifier 3 fires; PATH B; close axis on LDO. |
| BCH/TRX/ALGO bit-identity violation via dict-based dispatch | Most likely failure mode: `atr_multipliers_for_symbol()` resolution interacts with Optuna's global state (e.g., `optuna.create_study(seed=...)`), or the `LightGbmStrategy` constructor receives default args that introduce drift. Mitigation: Section 3 adversarial test asserts bit-identity directly via `_build_v3_model("BCHUSDT")` returning `atr_tp=2.0, atr_sl=1.0`. |
| Tighter barriers reduce LDO trade quality (more SL whipsaws) | If 0.75× scale produces more frequent SL hits at 3.76% threshold (tighter than peer 3.70% by 0.06pp; effectively same), LDO's mean_pnl may decrease while %_sl rises. Engineering report records LDO mean_pnl, %_sl, %_timeout shift; if LDO mean_pnl < 0 AND %_sl > 70%, the regime-alignment hypothesis is FALSIFIED — close axis. |

---

## Section 6 — 7-Primitive Risk Gate Stack — UNCHANGED

| Primitive | Threshold | Status |
|---|---|---|
| BTC trend kill | ±15% over 14d (42 bars 8h) | UNCHANGED |
| Vol scaling | RiskV2Wrapper internal | UNCHANGED |
| ADX gate | 20.0 | UNCHANGED |
| Hurst regime | hurst_100 in [0.3, 0.7] band | UNCHANGED |
| Feature z-score OOD | \|z\| ≤ 2.0 | UNCHANGED |
| Low-vol filter | NATR-percentile-based | UNCHANGED |
| Hit-rate feedback | DISABLED | UNCHANGED |
| Per-symbol cap | DISABLED (iter-v3/020 closed) | UNCHANGED |
| Regime-conditional kill | DISABLED (iter-v3/022 partial result deferred) | UNCHANGED |

**Gate fire rates** are expected to shift on LDO (tighter barriers → faster trade closures → more frequent gate checks per unit calendar time). BCH+TRX+ALGO gate fire rates expected BIT-IDENTICAL to iter-v3/029 via default fallback.

---

## Section 7 — Pre-Registered Failure-Mode Prediction

**Most plausible failure**: LDO trade-roster bit-identical to iter-v3/029 despite different ATR multipliers (Falsifier 1 fires). The mechanism: at single-seed n_trials=35, Optuna converges to a similar hyperparameter region for LDO regardless of label-barrier geometry — LightGBM's depth-bounded representation (depth 3-5) finds similar decision boundaries because LDO's underlying signal is the binding constraint, not the barrier width. Manifests as: LDO IS trades = 15 (bit-identical), LDO OOS = -3.07% (bit-identical), bundle Sharpe ≈ +1.77 (bit-identical). PROMISING-MECHANICAL classification.

**What the gates should catch**: The Section 2.4 saturation falsifier (LDO IS trades within ±25% of 15 AND trade-roster bit-identical) catches this directly. The Engineer Phase 6 engineering report MUST diff LDO's trades.csv from iter-v3/029's trades.csv on (open_time, close_time, side, exit_reason) tuples; if 100% match, Falsifier 1 fires.

**What failure looks like (PATH B-1 — LDO regression)**: LDO IS Sharpe collapses (LDO IS net_pnl < +20 vs iter-v3/029 +40.03), LDO OOS deepens to <-10%, LDO %_sl rises to >70%. The (1.5, 0.75) tighter barriers caused excessive SL whipsaws because LDO's signal-to-noise at 8h cadence is lower than the peer aggregate; tighter barriers amplified noise penetration. Bundle OOS drops below +1.50 (Falsifier 4 fires). REVERT and close per-symbol-LABELING axis on LDO.

**Second most plausible failure (PATH C — BCH/TRX/ALGO regression)**: Per-symbol ATR multiplier dispatch path bug introduces unintended changes to BCH/TRX/ALGO models. Manifests as: BCH/TRX/ALGO trade rosters non-bit-identical to iter-v3/029 (Falsifier 2 fires). REVERT and diagnose; per-symbol-LABELING discipline cannot proceed until clean dispatch path established. The Section 3 adversarial test (`test_atr_multipliers_runner_dispatch`) catches this BEFORE backtest by asserting `_build_v3_model("BCHUSDT")` returns `atr_tp=2.0, atr_sl=1.0` and `_build_v3_model("LDOUSDT")` returns `atr_tp=1.5, atr_sl=0.75`.

**Third most plausible failure (PATH A-MARGINAL — over-fitting risk)**: tighter barriers produce MORE LDO trades (predicted [16, 23]) but the additional trades are noise-driven — model fits to label-barrier geometry rather than genuine signal. Manifests as: LDO IS trade count up 30-50%, LDO IS Sharpe up, but LDO OOS Sharpe DOWN due to label-engineered overfit. The IS-OOS daily Sharpe ratio outside [0.5, 2.0] would flag this NEGATIVE-SUSPICIOUS-OOS pattern.

---

## Section 8 — Pre-Registered EXPLORATION Criteria (MERGE/NO-MERGE)

**This is an EXPLORATION — BASELINE_V3.md is NEVER updated.**

Pre-registered catalog-row decision criteria (cannot be renegotiated post-result):

| # | Criterion | PASS threshold | Verdict on PASS | Verdict on FAIL |
|---|---|---|---|---|
| 1 | Bundle OOS Sharpe (PROMISING-clean) | ≥ +1.85 (PROMISING floor) | PROMISING-clean | — |
| 2 | Bundle OOS Sharpe floor (PATH C falsifier) | ≥ +1.50 (hard) | — | NEGATIVE (Falsifier 4 fires) |
| 3 | LDO OOS weighted_pnl | ≥ 0% (regime-alignment validated) | PROMISING-clean | PROMISING-MECHANICAL or NEGATIVE-LDO |
| 4 | LDO trade roster differs from iter-v3/029 | ≥ 1 trade differs on (open_time, close_time, side, exit_reason) | Falsifier 1 PASS | PROMISING-MECHANICAL (Falsifier 1 fires) |
| 5 | BCH+TRX+ALGO trade roster bit-identical to iter-v3/029 | 0 differences across 3 symbols | Falsifier 2 PASS | NEGATIVE-architecture-bug (REVERT) |
| 6 | IS Sharpe | in [+0.85, +1.10] median +0.92 | PASS | SUSPICIOUS if outside [+0.65, +1.25] |
| 7 | PBO mean | < 0.40 (inherited from iter-v3/029 0.0974) | PASS | BLOCK |
| 8 | n_trades OOS bundle | ≥ 100 (iter-v3/029 was 124; predicted 110-130) | PASS | Note if < 80 |
| 9 | V3_FEATURE_COLUMNS | = 14, regime_momentum_signed_5d present | PASS | HARD BLOCK |
| 10 | REQUIRED_GAP | = 88 in validation_v3.py | PASS | HARD BLOCK |
| 11 | Adversarial test passes | `test_atr_multipliers_for_symbol.py` 3/3 | PASS | HARD BLOCK |
| 12 | Classification | PROMISING-clean / PROMISING-MECHANICAL / NEGATIVE | Pre-registered | Cannot be upgraded post-hoc |
| 13 | Non-compoundable rule | If PROMISING-MECHANICAL: NOT a CONFIRMATION-bundle ingredient | Pre-registered | Cannot be bundled at iter-v3/039 as "new signal" |

---

## Section 9 — Library Stack Declaration

**UNCHANGED from iter-v3/031** — no version updates:

```
python = 3.13
lightgbm = 4.6.0
numpy = 2.2.6
pandas = 3.0.0
scikit-learn = 1.8.0
pyarrow = 23.0.1
statsmodels = 0.14.6
optuna = 4.8.0
scipy = 1.17.0
```

mlfinpy / pypbo unavailable on Python 3.13 — pure-Python + numpy + scipy implementations used (established at iter-v3/002; unchanged throughout). No new dependencies for a per-symbol LABELING architecture iteration.

---

## Section 10 — Single-Axis Verifier (Engineer Phase 5.5 must check)

The single-axis variation IS the per-symbol ATR multiplier architecture. Everything else BIT-IDENTICAL to iter-v3/029.

**What's NEW (introduced by iter-v3/032)**:
1. `V3_ATR_MULTIPLIERS_PER_SYMBOL: dict[str, tuple[float, float]] = {"LDOUSDT": (1.5, 0.75)}`
2. `DEFAULT_ATR_MULTIPLIERS: tuple[float, float] = (2.0, 1.0)`
3. `atr_multipliers_for_symbol(symbol)` helper
4. Runner dispatches per-symbol ATR multipliers via the helper
5. Adversarial test `tests/features_v3/test_atr_multipliers_for_symbol.py` (3 tests)

**What's BIT-IDENTICAL to iter-v3/029** (must verify in engineering report):
1. V3_FEATURE_COLUMNS = 14 (regime_momentum_signed_5d KEPT)
2. V3_MODELS = 4 symbols (BCH+LDO+TRX+ALGO; iter-v3/031 universe shrink REVERSED)
3. REQUIRED_GAP = 88 (iter-v3/031 66 REVERSED)
4. V3_FEATURES_PER_SYMBOL = {} (iter-v3/030 LDO 7-feat subset NOT restored)
5. RiskV2Config (z=2.0, ADX=20, BTC ±15%, regime_gate disabled, per-sym cap disabled)
6. ENSEMBLE_SIZE=1 (--exploration mode)
7. n_trials=35 (default EXPLORATION)
8. colsample_bytree=1.0 (--exploration hardcoded)
9. ensemble_seeds (5-inner default)
10. cooldown_candles=4
11. Per-symbol BCH/TRX/ALGO atr_multipliers = (2.0, 1.0) via fallback
12. data/features_v3/{BCH,LDO,TRX,ALGO}USDT_8h_features.parquet upstream UNCHANGED

**LDO is the ONLY symbol whose training labels change**. Its barrier widths in price-% terms shift from (10.01%, 5.01%) to (7.51%, 3.76%) — a structural relabeling but no change to features, model class, hyperparameter search space, or Optuna seed.

---

## Section 11 — Catalog-Row Pre-Commit Disposition

The catalog row to be appended at Phase 8 (diary closure) is pre-registered for ALL 4 outcomes:

```
| iter-v3/032 | 2026-05-08 | RESTORE LDO + per-symbol ATR multipliers (LDO: (2.0,1.0)→(1.5,0.75); 4-symbol BCH+LDO+TRX+ALGO; per-symbol-LABELING architecture innovation) | <IS Sharpe Δ vs iter-v3/029 +0.7926> | <OOS Sharpe Δ vs iter-v3/029 +1.7653> | <EXPLORATION-{PROMISING / PROMISING-MECHANICAL / NEGATIVE-LDO / NEGATIVE-architecture-bug}> | <YES/NO bundle ingredient at iter-v3/039> |
```

**Outcome A — PROMISING-clean** (LDO OOS ≥ 0% AND BCH+TRX+ALGO bit-identical AND bundle OOS ≥ +1.85 AND LDO trade-roster differs):
> `| iter-v3/032 | 2026-05-08 | RESTORE LDO + per-symbol ATR multipliers (LDO: (2.0,1.0)→(1.5,0.75); 4-symbol; per-symbol-LABELING architecture) | <IS Δ> | <OOS Δ> | EXPLORATION-PROMISING (clean) | YES — STRONG candidate; iter-v3/039 CONFIRMATION-bundle ingredient (compoundable) |`

**Outcome B — PROMISING-MECHANICAL** (LDO trade-roster bit-identical AND BCH+TRX+ALGO bit-identical AND bundle bit-identical):
> `| iter-v3/032 | 2026-05-08 | RESTORE LDO + per-symbol ATR multipliers (LDO: (2.0,1.0)→(1.5,0.75); 4-symbol; per-symbol-LABELING architecture) | ~+0.79 (bit-identical) | ~+1.77 (bit-identical) | EXPLORATION-PROMISING-MECHANICAL | NO — strictly architectural; per-symbol-LABELING methodology validated as architecturally-neutral; iter-v3/033 may apply to a different symbol with stronger natr dispersion |`

**Outcome C — NEGATIVE (LDO drag)** (LDO OOS PnL < -10%):
> `| iter-v3/032 | 2026-05-08 | RESTORE LDO + per-symbol ATR multipliers (LDO: (2.0,1.0)→(1.5,0.75); 4-symbol; per-symbol-LABELING architecture) | <IS Δ> | <OOS Δ> | EXPLORATION-NEGATIVE (LDO drag — tighter barriers amplified SL whipsaws) | NO — closes per-symbol-LABELING axis on LDO; LDO regime mismatch is deeper than barrier-width geometry |`

**Outcome D — NEGATIVE (architecture bug)** (BCH/TRX/ALGO non-bit-identical):
> `| iter-v3/032 | 2026-05-08 | RESTORE LDO + per-symbol ATR multipliers (LDO: (2.0,1.0)→(1.5,0.75); 4-symbol; per-symbol-LABELING architecture) | <IS Δ> | <OOS Δ> | EXPLORATION-NEGATIVE (architecture-bug — BCH/TRX/ALGO drift) | NO — REVERT; iter-v3/033 = different axis category after architectural fix |`

The diary commit closes the catalog row regardless of outcome. The 4-row pre-commit prevents post-hoc rationalization.

---

## Section 12 — Phase 5.5 Gate Self-Check (10 mandatory sections inventory)

| # | Section | Status |
|---|---|---|
| 1 | Section 0 — Data Split Declaration | PRESENT (sacred constants UNCHANGED) |
| 2 | Section 1 — Hypothesis | PRESENT (per-symbol-LABELING; expected IS+OOS bands; LDO mechanism tied to natr 1.35× peer) |
| 3 | Section 2 — IS-Only Numerical Evidence | PRESENT (5 numerical tables; 4 falsifiers with explicit thresholds; behavioral-effect predictor) |
| 4 | Section 3 — Proposed Changes | PRESENT (7 sub-fixes; 8 reconciliation verifier commands; adversarial test) |
| 5 | Section 4 — Expected OOS Impact | PRESENT (PATH A/A-MARGINAL/B/C bands; 4-row catalog framing) |
| 6 | Section 5 — Risk Mitigation | PRESENT (3 categories; 11 mitigations) |
| 7 | Section 7 — Pre-Registered Failure-Mode Prediction | PRESENT (most plausible PROMISING-MECHANICAL; 2nd plausible PATH B-1 LDO regression; 3rd plausible PATH A-MARGINAL overfit) |
| 8 | Section 8 — Pre-Registered MERGE/NO-MERGE Criteria | PRESENT (13 numbered criteria with PASS thresholds; pre-registered for non-renegotiation) |
| 9 | Section 9 — Library Stack | PRESENT (UNCHANGED from iter-v3/031; no new deps for per-symbol-LABELING arch) |
| 10 | Section 11 — Catalog-Row Pre-Commit | PRESENT (4 outcomes pre-registered) |

**All 10 mandatory sections PRESENT.** Engineer's Phase 5.5 gate should PASS this brief.

---

## Section 13 — Status

**READY-FOR-PHASE-5.5** — research brief complete. Engineer reads this brief, verifies the 10 mandatory sections, runs the 8 reconciliation verifier commands, runs the 3 adversarial pytest tests, and writes `phase5p5_gate.md` with OVERALL=PASS. Phase 6 backtest then runs at single-seed --exploration; budget 25-35 min; well within 2h cap.

After Phase 6 closes, Critic Phase 7.5 review fires; QR Phase 7 evaluates OOS for first time; QR Phase 8 closes the catalog row at one of the 4 pre-registered dispositions.

iter-v3/032 is cadence #4 of 10; 6 EXPLORATIONs remain in this cycle; CONFIRMATION at iter-v3/039.
