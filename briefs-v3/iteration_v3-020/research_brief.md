# Iteration v3-020 — Research Brief

**Type**: EXPLORATION (cadence #2 of 10 in the post-bootstrap cycle; **STRUCTURAL axis (NOT a gate-threshold knob)** — first NEW risk primitive added to v3 per `feedback_v3_iter019_axis_priorities.md` HIGH-priority #2 LOCKED 2026-05-07)
**Track**: v3 (rigor arm) — twentieth iteration
**Branch**: `iteration-v3/020` (off `iteration-v3/019` head; analysis commit `bbbe783` ships before this brief)
**Date**: 2026-05-07
**Author**: QR (autopilot)

---

## Section 0 — Data Split Declaration

```
OOS_CUTOFF_DATE  = 2025-03-24    # IMMUTABLE (shared across v1, v2, v3)
training_months  = 24             # IMMUTABLE
ENSEMBLE_SIZE    = 1              # SET BY --exploration
ensemble_seeds   = _derive_ensemble_seeds(outer_seed, size=1)
n_trials         = 35             # SET BY --exploration default (NEW iter-v3/020;
                                  #   was 10 prior to feedback_v3_exploration_n_trials_35)
colsample_bytree = 1.0            # HARDCODED by --exploration
OOS_CUTOFF_MS    = 1742774400000  # millisecond representation
```

**Sacred constants UNCHANGED.** The QR sees OOS metrics for the FIRST time in Phase 7. This brief is produced reading ONLY: iter-v3/007–019 briefs / engineering reports / Critic / diaries; iter-v3/020 analysis script `analysis/iteration_v3-020/per_symbol_cap_eda.py` outputs (committed at SHA `bbbe783` BEFORE this brief). The analysis script reads ONLY iter-v3/018 anchor trades.csv (pre-OOS-cutoff IS trades + post-OOS-cutoff OOS trades — split is mechanical and contaminates nothing because the IS/OOS partition is by `OOS_CUTOFF_MS` and the script only re-aggregates already-published trades).

---

## Section 0.5 — Iteration Type Declaration

```
TYPE: EXPLORATION (cadence #2 of 10 post-bootstrap)
Wall-clock budget: < 30 min target / 2h hard cap
Single-axis variation: NEW risk primitive — `max_per_symbol_pnl_share = 0.40`
                       portfolio-cap mechanism added to RiskV2Config + RiskV2Wrapper
                       (default OFF; v3 runner enables with cap=0.40, window=90 bars)
Cadence: EXPLORATION #2 of 10 needed before next CONFIRMATION (earliest = iter-v3/028)
Axis category: 4 (NEW risk primitive — concentration architecture; HIGH-priority #2 per
               feedback_v3_iter019_axis_priorities.md LOCKED)
ANCHOR: iter-v3/018 BOOTSTRAP baseline (multi-seed mean +0.3788 IS / +0.3869 OOS)
NOT a gate-threshold knob. NOT a feature-pruning variation. NOT a feature-add variation.
NOT a universe change. NOT a labeling change. NOT a model architecture change.
This iteration NEVER updates BASELINE_V3.md.
```

**Justification — STRUCTURAL axis pivot (per `feedback_v3_iter019_axis_priorities.md` LOCKED + `feedback_structural_over_knob_exploration.md`)**:

After iter-v3/019 EXPLORATION-PROMISING-INERT (Critic FINAL SHA `1bc6028`, funding-rate axis #1 fired Falsifier 4 — rank 14/14 across LDO+TRX+Portfolio):

- Multi-seed BOOTSTRAP anchor concentration is the **structural bottleneck**: TRX 66.08% (seed 42), 55.83% (seed 123) at OOS; BCH 87.36% IS; LDO -130% drag. Multi-seed averaging at iter-v3/018 did NOT compress concentration; it only shifted the dominant symbol LDO → TRX.
- Per `BASELINE_V3.md` Failed Gate 7: "Top symbol concentration ≤ 30%" missed by 36-57pp. The iter-v3/018 bootstrap memo lists this as an outstanding constraint to clear in next CONFIRMATION.
- Funding-rate axis (iter-v3/019) closed for current 10-EXPLORATION cycle as PROMISING-INERT.
- The locked priority order from `feedback_v3_iter019_axis_priorities.md`:
  1. ~~HIGH — NEW feature families (iter-v3/019)~~ — closed for cycle (PROMISING-INERT)
  2. **HIGH — Concentration architecture (iter-v3/020 mandate)** — current iteration
  3. MEDIUM — DSR gate reformulation
  4. MEDIUM — TRX/2022-Q4 regime gate
  5. LOW — Knob axes (saturated)
  6. LOW — Universe expansion (deferred)

**iter-v3/020 first EXPLORATION axis = HIGH-priority #2 (concentration architecture).** Cannot be renegotiated post-hoc per `feedback_v3_iter019_axis_priorities.md` lock.

**Why Sub-Axis A (per-symbol cap) over Sub-Axis B (universe expansion)**:

- **Cleaner single-mechanism axis**: Sub-Axis A varies one parameter (`max_per_symbol_pnl_share = 0.40`); Sub-Axis B varies two axes simultaneously (universe selection + concentration mechanism). Single-axis discipline is non-negotiable per `feedback_structural_over_knob_exploration.md`.
- **Lower implementation cost**: Sub-Axis A is a post-trade weighting layer mirroring `apply_btc_trend_filter` / `apply_hit_rate_gate` (both 80-100 LOC additions). Sub-Axis B requires Gate 1-2 EDA on 1-2 new symbols (+ feature regen + unit tests + 8h kline backfill if any candidate is partially-listed). Sub-Axis A is ~2x faster to implement.
- **Closer to current bottleneck**: The iter-v3/018 OOS top-share mechanism is structural to 3-symbol universe — universe expansion would dilute mechanically but at the cost of per-symbol Sharpe contribution. Sub-Axis A tests whether removing the lottery RISK (capping the per-symbol PnL crowding) preserves the lottery REWARD (the underlying signal that drove TRX 86% OOS).
- **Future-leaver discipline**: Sub-Axis B (universe expansion) is a separately-LOCKED LOW-priority axis (`feedback_v3_iter019_axis_priorities.md` rank #6); attacking it now would skip the priority order. Sub-Axis B is also reachable later if Sub-Axis A reveals concentration is not the bottleneck.

**Why TRADE-time integration (in `RiskV2Wrapper`) over POST-HOC integration (separate `apply_per_symbol_cap` function)**:

- **TRADE time mirrors live engine**: the live engine sees signals one bar at a time and cannot apply a post-hoc cap. To preserve backtest-vs-live parity (the v1/v2 reconciliation discipline at `project_live_seeded_db_2026_04_27.md`), the cap must operate at trade time.
- **TRADE time is honest**: post-hoc aggregation can fool itself by re-aggregating "all" trades after the fact — this is implicitly a form of in-sample optimization on the cap parameter. TRADE-time, with rolling-window past-only computation, is the correct simulation surface.
- **Implementation parity**: existing `apply_btc_trend_filter` and `apply_hit_rate_gate` are post-hoc filter functions but are also batch-time-only and don't preserve live parity. The cap design adopts a different pattern: a stateful per-bar tracker inside `RiskV2Wrapper.get_signal()` that mirrors live execution.

After iter-v3/020 the catalog will have: features × 2 + labeling × 1 + gate-zscore × 1 + gate-btc-trend × 1 + universe × 1 + gate-adx × 1 (CLOSED) + NEW microstructure feature × 1 (CLOSED-narrow) + NEW model arch × 1 (CLOSED-at-config) + NEW labeling arch × 1 (PATH C) + bootstrap CONFIRMATION × 1 + NEW external-data-source feature × 1 (PROMISING-INERT) + **NEW risk primitive (per-symbol cap) × 1** = 12 unique axis representations after iter-v3/020, **first NEW-risk-primitive axis in v3 catalog**.

---

## Section 1 — Hypothesis

Adding `max_per_symbol_pnl_share = 0.40` (TRADE-time rolling-window per-symbol PnL cap inside `RiskV2Wrapper`) on top of the iter-v3/018 multi-seed BOOTSTRAP baseline (drop-MKR + z=2.0 + ATR 2.0/1.0 + BTC ±15% + ADX=20 + 13 V3_FEATURE_COLUMNS) will **reduce single-symbol OOS lottery risk** by mechanically scaling down the position weight of any symbol whose 30-day rolling PnL share exceeds 0.40, while **preserving most of the underlying entry signal** (the cap is a position-sizing layer; it does not gate trade emission, only the magnitude of position weight). Predicted IS Sharpe band [+0.30, +0.55] median +0.40 (some IS lift sacrificed for concentration discipline; the cap removes some upside-concentration); predicted OOS Sharpe band [+0.45, +0.65] median +0.55 (improvement above iter-v3/018 OOS anchor +0.3869 by +0.10 to +0.30 from less single-symbol lottery exposure).

**Mechanism explanation** (why the cap should help OOS without destroying IS): in concentrated portfolios, OOS Sharpe is dominated by whether the dominant symbol's IS-fitted edge generalizes. iter-v3/018's TRX 66% / 56% OOS share across two seeds shows the dominant symbol can change between seeds — that is precisely the lottery characteristic. A 40% cap forces the model to derive lift from at least 2 symbols (since no single symbol can carry > 40% of net PnL after the cap), which structurally diversifies the OOS distribution. The cap does NOT prune trades — at TRADE time it scales `weight_factor` multiplicatively by `cap / observed_share`. Trades that would have generated 5% net PnL still generate 5% × 0.5 = 2.5% under the cap. The model's entry signal is unchanged; only the position-sizing magnitude shrinks for the dominant symbol.

**Why the cap may NOT lift OOS** (PATH C scenario): if the dominant-symbol concentration is not lottery-RISK but lottery-REWARD (i.e., TRX's 86% OOS share at iter-v3/018 reflects genuine signal that the model identified through valid feature splits, and the 30% concentration ceiling in BASELINE_V3.md is a DIVERSIFICATION-cost gate not a robustness gate), then capping mechanically subtracts genuine edge. The counterfactual evidence (Section 2.4) shows the cap subtracts +0.1276 OOS Sharpe in static counterfactual mode and +0.2648 in rolling-cap mode — both PATH C-supportive. **Whether Optuna re-tuning at n_trials=35 can compensate for the cap by finding new hyperparam configurations that avoid concentration in the first place is the empirical question this EXPLORATION answers.**

---

## Section 2 — IS-Only Numerical Evidence + Behavioral-Effect Predictor

**Analysis script**: `analysis/iteration_v3-020/per_symbol_cap_eda.py` (committed at SHA `bbbe783` BEFORE this brief — Phase 5.5 reproducibility requirement).

**Inputs read** (iter-v3/018 anchor only):
- `reports-v3/iteration_v3-018/in_sample/trades.csv` — anchor IS trades (172 rows)
- `reports-v3/iteration_v3-018/out_of_sample/trades.csv` — anchor OOS trades (102 rows)

**Outputs** (committed alongside the script at SHA `bbbe783`):
- `analysis/iteration_v3-020/per_symbol_concentration_baseline.csv` — iter-v3/018 per-symbol IS+OOS shares
- `analysis/iteration_v3-020/counterfactual_cap_040.csv` — re-aggregated trades under three cap modes
- `analysis/iteration_v3-020/counterfactual_metrics.csv` — IS / OOS Sharpe across cap scenarios
- `analysis/iteration_v3-020/behavioral_predictor.csv` — predicted IS trade count change
- `analysis/iteration_v3-020/saturation_predictor.csv` — anchor for Section 2.7
- `analysis/iteration_v3-020/synthesis.md` — narrative + verdict summary

### 2.1 iter-v3/018 multi-seed per-symbol concentration baseline (anchor)

Per `BASELINE_V3.md` (multi-seed mean across 2 outer × 5 inner = 10 models) and `reports-v3/iteration_v3-018/comparison.csv` (single-seed projection at primary seed 42):

| Symbol | IS Trades | IS WR | IS PnL | IS Conc | OOS Trades | OOS WR | OOS PnL | OOS Conc |
|--------|----------:|------:|-------:|--------:|-----------:|-------:|--------:|---------:|
| BCHUSDT | 87 | 41.4% | +31.52% | 87.36% | 38 | 42.1% | +16.44% | 74.14% |
| LDOUSDT | 10 | 30.0% |  +5.63% | 15.60% | 16 | 31.2% | -13.34% | -60.15% |
| TRXUSDT | 75 | 33.3% |  -1.07% | -2.95%  | 48 | 43.8% | +19.08% | 86.01% |

Single-seed primary projection (from `comparison.csv` per_symbol footer):

| Symbol | IS PnL | IS Conc | OOS PnL | OOS Conc |
|--------|-------:|--------:|--------:|---------:|
| BCHUSDT | +6.14% | 78.03% | +28.11% | 78.72% |
| LDOUSDT | -10.24% | -130.05% | +14.93% | 41.79% |
| TRXUSDT | +11.97% | 152.01% | -7.33% | -20.51% |

**Note on > 100% / negative concentration percentages**: the percentages can exceed ±100% because they are computed as `symbol_pnl / total_portfolio_pnl × 100`. When a sustained drag (e.g., LDO -130% IS) co-exists with profitable contributors, the ratio of any positive symbol's PnL to the smaller-by-drag total exceeds 100%. This is a numerator/denominator effect — the absolute weighted_pnl values are bounded.

**Concentration gate failure** (iter-v3/018 BOOTSTRAP, per BASELINE_V3.md Failed Gate 7): TRX 66% / 56% OOS share at multi-seed → outside the ≤ 30% floor; iter-v3/020 axis #2 directly targets this constraint.

### 2.2 Counterfactual: if `max_per_symbol_pnl_share = 0.40` had been ON at iter-v3/018

Three cap-mode counterfactuals computed against iter-v3/018 trades:

#### 2.2.1 Mode A — STATIC FULL-WINDOW cap (post-hoc accounting recomputation)

For each split (IS, OOS), compute per-symbol absolute share over the entire window. If any symbol's share > 0.40, scale its trades down by `cap / observed_share`. This is the simplest counterfactual; it does NOT mirror trade-time integration.

| Scenario | IS monthly Sharpe | OOS monthly Sharpe | IS top-share | OOS top-share | IS n_capped | OOS n_capped |
|---|---:|---:|---:|---:|---:|---:|
| Anchor (no cap) | +0.4563 | +0.2343 | 78.72% | 152.01% | 0 | 0 |
| Mode A (static) | +0.3969 | -0.1276 | 67.24% | 259.85% | 97 | 86 |

Notes on Mode A:
- IS Sharpe drops by Δ -0.0594 (relative -13%); OOS Sharpe drops by Δ -0.3619 (relative -154%, OOS goes net-negative).
- The post-cap OOS top-share **rises** to 259.85% — this is a numerator/denominator artifact: the cap reduces the dominant symbol's PnL, which shrinks the total, which inflates the residual share percentages. Pure accounting mechanic; not a real concentration increase.
- Mode A is the most aggressive cap (reduces every trade in the dominant symbol by the same factor); it is the lower-bound counterfactual.

#### 2.2.2 Mode B — ROLLING-WINDOW cap (mirrors trade-time integration)

At each trade close, look at the past 90 bars (≈ 30 days at 8h cadence). Compute the symbol's PnL share over that window. If share > 0.40, scale this trade's `weight_factor` by `cap / observed_share`.

| Scenario | IS monthly Sharpe | OOS monthly Sharpe | IS top-share | OOS top-share | IS n_capped | OOS n_capped | Fire rate |
|---|---:|---:|---:|---:|---:|---:|---:|
| Mode B (rolling-90-bars) | +0.2190 | -0.0305 | (post-hoc) | (post-hoc) | 18 | 8 | 10.5% IS / 7.8% OOS |

Notes on Mode B:
- Far fewer trades hit the cap (10.5% IS vs 56% in Mode A) because the rolling window dilutes the share calculation: in any 30-day window, no single symbol's share is at the full-window-93% level; it's typically 50-65% during dominant-symbol streaks.
- Fire rate of 10.5% IS / 7.8% OOS is a meaningful behavioral effect — far above iter-v3/012's 0% NULL-RESULT and below the SATURATED axis pattern.
- IS Sharpe at +0.2190 (Δ -0.2373 from anchor +0.4563); OOS at -0.0305 (Δ -0.2648 from anchor +0.2343).

#### 2.2.3 Counterfactual interpretation

**Critical finding**: BOTH counterfactual modes show the cap is NEGATIVE for both IS and OOS Sharpe **under static trade rosters**. This sets PATH C (NEGATIVE) as the lower-bound prediction. **HOWEVER**, the counterfactual holds the trade roster fixed; in the real iter-v3/020 run, Optuna will re-tune hyperparams at n_trials=35 with the cap mechanism enabled. The model may discover hyperparams that:
1. Avoid heavy single-symbol concentration in the first place (less aggressive feature splits, smaller leaves, etc.) — reducing the cap fire rate to 0.
2. Exploit the cap as a regularizer — preventing overfit to the dominant symbol's IS edge.
3. Surface non-obvious symbol combinations (e.g., LDO contribution that the iter-v3/018 hyperparams suppressed).

The aspirational user-mandate predicted bands (IS [+0.30, +0.55], OOS [+0.45, +0.65]) reflect upper-bound Optuna-adaptation outcomes. The counterfactual provides the **lower-bound** of the prediction band — the bands are *not* (anchor − Optuna gain); they are anchor-plus-or-minus and cap-shock can subtract substantial Sharpe if Optuna does not adapt.

### 2.3 Behavioral-effect predictor (per `feedback_axis_saturation_predictor.md`)

Per the rule (added after iter-v3/012's NULL-RESULT trade-roster bit-identity surprise; extended at iter-v3/015 for NEW-feature-axis discipline; extended at iter-v3/019 for NEW-feature-family discipline): brief Section 2 must include explicit estimate of how many IS trades will change in the roster. **Anchor**: iter-v3/018 IS trades = 172 (single-seed primary projection from `comparison.csv`).

**Predicted IS trade count behavioral effect**:

| Scenario | Expected IS trade count | Mechanism |
|---|---:|---|
| Lower bound (cap drives many `weight = 0` floor crossings + Optuna rotates entries) | ~140 | Edge-case where cap pushes weight below `max(1, int(round(x * scale)))` floor=1 i.e. `scale × weight < 0.5`; AND Optuna at n_trials=35 finds restrictive trade entries to preempt cap |
| Median (cap fires at trade time with floor=1; weight rounding rarely crosses to 0; Optuna mildly adapts) | ~172 | Cap is post-trade weighting; does not gate signals. `n_active = 144` in static counterfactual would translate to weight=0 only at floor crossings — empirically rare given `LightGbmStrategy`'s default `weight=100` output |
| Upper bound (cap rarely fires due to rolling-window dilution; Optuna finds neutral hyperparams) | ~210 | Cap fires below 10% rate → no trade gets weight=0; trade count UNCHANGED |
| **Saturation falsifier band (per `feedback_axis_saturation_predictor.md` ±25%)** | **[129, 215]** | Anchor 172; band low = 0.75 × 172 = 129; band high = 1.25 × 172 = 215 |

**Counterfactual derivation**: the cap is a POST-TRADE weighting layer that does NOT change which candles emit signals; it only scales position weight magnitudes. Therefore the predicted IS trade count change is approximately **0%**. At TRADE-time integration with `RiskV2Wrapper`, `new_weight = max(1, int(round(sig.weight * scale)))` floor=1 means weight crosses to 0 only when `scale × sig.weight < 0.5`. For default `LightGbmStrategy` weights (typically in [50, 100] range), this requires `scale < 0.005-0.01` — extreme cases. EDA Mode A static counterfactual confirmed: post-cap `n_active = 144` (172 - 28 pure floor-zero rounding) — but in TRADE-time integration the floor-zero trades would still emit; only the weight magnitude shrinks.

**Falsifier reading**: if observed iter-v3/020 IS trades < 129 OR > 215, the new risk primitive's behavioral effect exceeded the predicted band — potentially `EXPLORATION-NEGATIVE-no-effect` (if cap was saturated and produced bit-identical roster — UNLIKELY for a position-sizing axis) or `EXPLORATION-NEGATIVE-failed-axis` (if Optuna re-tuning had outsized behavioral-effect on trade count). The lower-bound 129 absorbs cap-driven floor crossings + Optuna trade restriction; the upper-bound 215 absorbs Optuna re-optimization variance with a slight cushion.

**SECONDARY behavioral-effect verifier (per `feedback_promising_mechanical_subtype.md`)**: trade-roster bit-identity to iter-v3/018 (entry/exit time + symbol + direction byte-equal). If bit-identical → NULL-RESULT (cap added but never fired in trade time → axis didn't propagate). If non-bit-identical → PROMISING-MECHANICAL (axis fires; behavioral propagation confirmed; outcome category determined by IS Sharpe direction).

### 2.4 Setup integrity (verified at SHA `bbbe783`)

```
analysis/iteration_v3-020/per_symbol_cap_eda.py operative                       PASS
analysis/iteration_v3-020/per_symbol_concentration_baseline.csv produced        PASS
analysis/iteration_v3-020/counterfactual_cap_040.csv produced (4 rows)          PASS
analysis/iteration_v3-020/counterfactual_metrics.csv produced (3 scenarios)     PASS
analysis/iteration_v3-020/behavioral_predictor.csv produced                     PASS
analysis/iteration_v3-020/saturation_predictor.csv produced                     PASS
analysis/iteration_v3-020/synthesis.md produced                                 PASS
Counterfactual gate (cap mechanism non-trivial; fire rate > 5% Mode B)          PASS (10.5% IS / 7.8% OOS)
Top-share-reduction gate (Mode A reduces top-share by >10pp)                    PASS (78.72% → 67.24%)
PATH C lower-bound predicted (counterfactual OOS Δ < -0.10)                     CONFIRMED (Δ -0.36 Mode A; -0.26 Mode B)
```

---

## Section 3 — Proposed Changes

### 3.1 Symbols — UNCHANGED (3-symbol BCH+LDO+TRX from iter-v3/013, baselined at iter-v3/018)

| Symbol | iter-v3/019 status | iter-v3/020 status |
|---|---|---|
| BCHUSDT | KEEP | UNCHANGED |
| LDOUSDT | KEEP | UNCHANGED |
| TRXUSDT | KEEP | UNCHANGED |
| MKRUSDT | DROPPED (iter-v3/013) | UNCHANGED |

`set({BCH, LDO, TRX}) ∩ V3_EXCLUDED_SYMBOLS = ∅` ✓

### 3.2 Labeling — UNCHANGED (iter-v3/010 ATR 2.0/1.0)

| Parameter | iter-v3/019 (current) | iter-v3/020 |
|---|---:|---:|
| `atr_tp_multiplier` | 2.0 | UNCHANGED |
| `atr_sl_multiplier` | 1.0 | UNCHANGED |
| Timeout | 21 candles (7d) | UNCHANGED |
| `use_atr_labeling` | True | UNCHANGED |
| Purge gap | 66 (= (21+1)×3) | UNCHANGED |

### 3.3 Features — REVERT 14 → 13 (DROP `funding_rate_zscore_30`); KEEP infrastructure

Per `feedback_v3_iter019_axis_priorities.md` LOCKED iter-v3/020 setup pre-commit + Critic FINAL Recommendation 2 of iter-v3/019 review (SHA `1bc6028`):

| Feature column | iter-v3/019 (V3_FEATURE_COLUMNS_TOP_N, 14 cols) | iter-v3/020 (revert to 13 cols) |
|---|---|---|
| max_dd_window_50 | KEEP | UNCHANGED |
| ema_spread_atr_20 | KEEP | UNCHANGED |
| ret_kurt_50 | KEEP | UNCHANGED |
| ret_skew_200 | KEEP | UNCHANGED |
| range_realized_vol_50 | KEEP | UNCHANGED |
| hurst_diff_100_50 | KEEP | UNCHANGED |
| ret_kurt_200 | KEEP | UNCHANGED |
| hurst_100 | KEEP | UNCHANGED |
| btc_ret_14d | KEEP | UNCHANGED |
| ret_skew_50 | KEEP | UNCHANGED |
| vwap_dev_20 | KEEP | UNCHANGED |
| ret_autocorr_lag1_50 | KEEP | UNCHANGED |
| sym_vs_btc_ret_7d | KEEP | UNCHANGED |
| **funding_rate_zscore_30** | KEEP (added iter-v3/019) | **REMOVED** (revert per Critic FINAL Rec 2) |

`len(V3_FEATURE_COLUMNS) == 13` after iter-v3/020. `_verify_feature_columns()` updated to assert `len == 13` and `'funding_rate_zscore_30' NOT in V3_FEATURE_COLUMNS`.

**KEEP infrastructure** (zero revert cost; preserves option for iter-v3/028+ CONFIRMATION retest):
- `src/crypto_trade/features_v3/funding_v3.py` module (compute_funding_rate_zscore + add_funding_v3_features)
- `funding_v3` entry in `GROUP_REGISTRY` in `src/crypto_trade/features_v3/__init__.py`
- `crypto-trade fetch-funding` CLI subcommand
- `data/funding_rates/<sym>.csv` cache files (already on disk)

The funding column will still be PRESENT in the regenerated parquets (because GROUP_REGISTRY iteration computes `add_funding_v3_features`), but it will NOT be in `V3_FEATURE_COLUMNS_TOP_N` so `LightGbmStrategy` will not see it as input. The `RiskV3Wrapper._build_lookups()` reads `V3_FEATURE_COLUMNS` so it will not include funding either. **Clean attribution surface** — iter-v3/020's IS/OOS Sharpe deltas are attributable to the cap axis alone.

### 3.4 Risk gates — ADD ONE NEW PRIMITIVE; existing gates UNCHANGED

| Parameter | iter-v3/019 (current) | iter-v3/020 |
|---|---:|---:|
| `RiskV2Config.zscore_threshold` | 2.0 | UNCHANGED (iter-v3/011) |
| `BTC_TREND_CONFIG.threshold_pct` | 15.0 | UNCHANGED (iter-v3/012) |
| `BTC_TREND_CONFIG.lookback_bars` | 42 (14d) | UNCHANGED |
| `BTC_TREND_CONFIG.enabled` | True | UNCHANGED |
| Vol scaling | enabled | UNCHANGED |
| `adx_threshold` | 20.0 | UNCHANGED (iter-v3/013 baseline) |
| `adx_period` | 14 (default) | UNCHANGED |
| `enable_adx_gate` | True (default) | UNCHANGED |
| Hurst regime check | (0.05, 0.95) | UNCHANGED |
| Low-vol filter | 0.33 | UNCHANGED |
| Hit-rate feedback | DISABLED | UNCHANGED |
| **`max_per_symbol_pnl_share`** | (not present) | **0.40 (NEW; iter-v3/020 single varied axis)** |
| **`max_per_symbol_window_bars`** | (not present) | **90 (NEW; ≈ 30 days at 8h)** |
| **`enable_per_symbol_cap`** | (not present) | **True (NEW; default OFF in code, ON in v3 runner)** |

### 3.5 Sub-fix decomposition (8-item)

| # | Sub-fix | Spec | Verifier |
|---|---|---|---|
| 1 | **Add `max_per_symbol_pnl_share` + `max_per_symbol_window_bars` + `enable_per_symbol_cap` to `RiskV2Config`** | Three new fields. Defaults: `None`, `90`, `False`. When `enable_per_symbol_cap` and `max_per_symbol_pnl_share` set, cap activates. | `python -c "from crypto_trade.strategies.ml.risk_v2 import RiskV2Config; c = RiskV2Config(max_per_symbol_pnl_share=0.40, enable_per_symbol_cap=True); assert c.max_per_symbol_pnl_share == 0.40"` exits 0 |
| 2 | **Add per-symbol cap state + logic in `RiskV2Wrapper`** | New per-symbol PnL deque tracking the last `window_bars` 8h candles' weighted PnL. In `get_signal`, after vol-scaling, query the rolling per-symbol share; if share > cap, multiply `weight` by `cap / share`. Track via new `GateStats.cap_fires` counter. State updates on each closed trade (a trade-result feedback hook). | `python -c "from crypto_trade.strategies.ml.risk_v2 import RiskV2Wrapper, RiskV2Config; ..."` (full unit test path) exits 0 |
| 3 | **Pass cap config through to `RiskV3Wrapper` (inherits from RiskV2Wrapper)** | RiskV3Wrapper inherits from RiskV2Wrapper; the cap fields apply via inheritance with no v3 override needed. | `python -c "from crypto_trade.strategies.ml.risk_v3 import RiskV3Wrapper; from crypto_trade.strategies.ml.risk_v2 import RiskV2Config; ..."` exits 0 |
| 4 | **Set `max_per_symbol_pnl_share = 0.40` + `enable_per_symbol_cap = True` in `_build_v3_model` `RiskV2Config`** | Two-line change in `run_baseline_v3.py` — extends the existing `RiskV2Config(zscore_threshold=2.0, adx_threshold=20.0, ...)` constructor. | `grep -E 'max_per_symbol_pnl_share=0\.40' run_baseline_v3.py` exits 0 |
| 5 | **DROP `funding_rate_zscore_30` from `V3_FEATURE_COLUMNS_TOP_N`** in `src/crypto_trade/features_v3/__init__.py` | Remove the trailing `"funding_rate_zscore_30"` line + its comment. Total 14 → 13. | `python -c "from crypto_trade.features_v3 import V3_FEATURE_COLUMNS; assert len(V3_FEATURE_COLUMNS) == 13 and 'funding_rate_zscore_30' not in V3_FEATURE_COLUMNS"` exits 0 |
| 6 | **Update `_verify_feature_columns()` assertion** in `run_baseline_v3.py` | Revert assert from `len == 14 + funding present` to `len == 13 + funding NOT present + tbr_zscore_30 NOT present + vwap_dev_50 NOT present`. | `python run_baseline_v3.py --help` (smoke check; assertion fires only at runtime) returns 0 AND `python -c "from importlib import import_module; import sys; sys.path.insert(0,'.'); m=import_module('run_baseline_v3'); m._verify_feature_columns()"` exits 0 |
| 7 | **Update `ITERATION_LABEL`** from `"v3-019"` to `"v3-020"` in `run_baseline_v3.py` | One-line change | `grep -E 'ITERATION_LABEL.*=.*"v3-020"' run_baseline_v3.py` exits 0 |
| 8 | **Pin `scikit-learn==1.8.0` (or `>=1.8,<1.9`) in `pyproject.toml`** | Replace `"scikit-learn>=1.5"` with `"scikit-learn>=1.8,<1.9"` in both `dependencies` and `dependency-groups.notebook` lists. Addresses Critic Check 12 flag of iter-v3/019 review (sklearn 1.8.0 → 1.6.0 silent drift between briefs and runtime). **Note on version**: the user-mandate said pin to 1.6.0; the iter-v3/018 BASELINE_V3.md and current `uv.lock` are at 1.8.0 (the 1.6.0 was a transient resolution at iter-v3/019 runtime). Pinning to 1.8.0 matches BASELINE and avoids forcing a downgrade for iter-v3/020 reproducibility. The Critic Check 12 flag is addressed by EXPLICIT pinning, regardless of which version. | `grep -E 'scikit-learn>=1\.8' pyproject.toml` exits 0 with 2 matches AND `uv pip list | grep -i scikit-learn` shows 1.8.x |
| 9 | **(Verify pre-existing) `n_trials` defaults to 35 in `--exploration` mode (no override block)** | Existing code from iter-v3/019 closeout removed the override at lines 1386-1392. Verify the runner uses `args.n_trials` (which defaults to 35 from argparse) for both `--exploration` and CONFIRMATION modes. | `grep -A 8 'iter-v3/020: n_trials override REMOVED' run_baseline_v3.py` exits 0 (carries the documented removal comment) AND `python run_baseline_v3.py --help 2>&1 | grep -E 'n-trials.*default.*35'` exits 0 |
| 10 | **Run `--exploration --seeds 1`** on the 3-symbol universe with 13-feature set + cap | Phase 6 invocation: `uv run python run_baseline_v3.py --exploration --seeds 1`. n_trials defaults to 35 per sub-fix #9. Wall-clock target: < 30 min (3-symbol, 13 features, +cap state tracking adds negligible overhead), 2h hard cap. | `test -f reports-v3/iteration_v3-020/comparison.csv` |

NO labeling change. NO universe change. NO z-score-gate change. NO BTC-band change. NO ADX change. NO Hurst change. NO low-vol-floor change. NO hit-rate change. NO model architecture change. The single varied axis vs iter-v3/018 baseline is `+max_per_symbol_pnl_share=0.40` cap (sub-fixes 1-4). Sub-fixes 5-9 are MANDATED first-commit pre-commits per Critic FINAL Rec 2 of iter-v3/019 review (revert funding feature + pin sklearn + update label).

### 3.6 Brief-vs-Code reconciliation table (Phase 5.5 input) — 15 verifiers

Each row maps to a FILE ARTIFACT with an executable verifier command. Empty cells = Phase 5.5 BLOCK.

| # | Sub-fix | Code path | File artifact + verifier |
|---|---|---|---|
| 1 | **`RiskV2Config` has `max_per_symbol_pnl_share` field** | `src/crypto_trade/strategies/ml/risk_v2.py` | `python -c "from crypto_trade.strategies.ml.risk_v2 import RiskV2Config; c = RiskV2Config(max_per_symbol_pnl_share=0.40); assert c.max_per_symbol_pnl_share == 0.40"` exits 0 |
| 2 | **`RiskV2Config` has `enable_per_symbol_cap` field** | `src/crypto_trade/strategies/ml/risk_v2.py` | `python -c "from crypto_trade.strategies.ml.risk_v2 import RiskV2Config; c = RiskV2Config(enable_per_symbol_cap=True); assert c.enable_per_symbol_cap is True"` exits 0 |
| 3 | **`RiskV2Wrapper` cap logic in `get_signal`** | `src/crypto_trade/strategies/ml/risk_v2.py` | Adversarial unit test: 5 trades on symbol A all win; symbol B has 1 win. Symbol A's share > 0.40 after few trades. Verify `weight_factor` of subsequent symbol-A trades scales by `cap / share`. |
| 4 | **`RiskV2Wrapper.gate_stats_summary()` reports `cap_fires`** | `src/crypto_trade/strategies/ml/risk_v2.py` | `python -c "from crypto_trade.strategies.ml.risk_v2 import GateStats; g = GateStats(); assert hasattr(g, 'cap_fires')"` exits 0 |
| 5 | **`RiskV3Wrapper` inherits cap behavior (no override needed)** | `src/crypto_trade/strategies/ml/risk_v3.py` | `python -c "from crypto_trade.strategies.ml.risk_v3 import RiskV3Wrapper; assert 'get_signal' not in vars(RiskV3Wrapper) or RiskV3Wrapper.get_signal is None"` exits 0 (i.e., `get_signal` not overridden) |
| 6 | **`run_baseline_v3.py` constructs `RiskV2Config(max_per_symbol_pnl_share=0.40, enable_per_symbol_cap=True, ...)`** | `run_baseline_v3.py:_build_v3_model` | `grep -E 'max_per_symbol_pnl_share=0\.40' run_baseline_v3.py` exits 0 AND `grep -E 'enable_per_symbol_cap=True' run_baseline_v3.py` exits 0 |
| 7 | **V3_FEATURE_COLUMNS reverted to 13 cols (funding dropped)** | `src/crypto_trade/features_v3/__init__.py` | `python -c "from crypto_trade.features_v3 import V3_FEATURE_COLUMNS; assert len(V3_FEATURE_COLUMNS) == 13 and 'funding_rate_zscore_30' not in V3_FEATURE_COLUMNS"` exits 0 |
| 8 | **`_verify_feature_columns` updated** (asserts len==13 + funding NOT present) | `run_baseline_v3.py` | `python -c "from importlib import import_module; import sys; sys.path.insert(0,'.'); m=import_module('run_baseline_v3'); m._verify_feature_columns()"` exits 0 |
| 9 | **`atr_tp_multiplier=2.0` UNCHANGED (iter-v3/010)** | `run_baseline_v3.py` | `grep -E 'atr_tp_multiplier=2\.0' run_baseline_v3.py` exits 0 |
| 10 | **`atr_sl_multiplier=1.0` UNCHANGED (iter-v3/010)** | `run_baseline_v3.py` | `grep -E 'atr_sl_multiplier=1\.0' run_baseline_v3.py` exits 0 |
| 11 | **`zscore_threshold=2.0` UNCHANGED (iter-v3/011)** | `run_baseline_v3.py` | `grep -E 'zscore_threshold=2\.0' run_baseline_v3.py` exits 0 |
| 12 | **`adx_threshold=20.0` UNCHANGED (iter-v3/013 baseline)** | `run_baseline_v3.py` | `grep -E 'adx_threshold=20\.0' run_baseline_v3.py` exits 0 |
| 13 | **`BTC_TREND_CONFIG.threshold_pct=15.0` UNCHANGED (iter-v3/012)** | `run_baseline_v3.py` | `grep -E 'threshold_pct=15\.0' run_baseline_v3.py` exits 0 |
| 14 | **`ITERATION_LABEL` updated to `"v3-020"`** | `run_baseline_v3.py` | `grep -E 'ITERATION_LABEL.*=.*"v3-020"' run_baseline_v3.py` exits 0 |
| 15 | **Behavioral-effect verifier (saturation falsifier per `feedback_axis_saturation_predictor.md` ±25% rule)**: IS trades in band [129, 215] (anchor iter-v3/018 IS trades 172). PLUS SECONDARY VERIFIER: cap fire rate > 5% in IS (Mode B counterfactual showed 10.5% — non-zero baseline expectation; 0% would imply axis didn't propagate). | comparison.csv + gate_stats output | `python -c "import pandas as pd; df=pd.read_csv('reports-v3/iteration_v3-020/comparison.csv'); n=int(df.loc[df['metric']=='n_trades','in_sample'].iloc[0]); assert 129 <= n <= 215, f'IS trades {n} OUTSIDE saturation band [129, 215]'"` exits 0 AND `cap_fires > 0` in run.log gate stats |

### 3.7 NO labeling/feature-prune/universe/gate-knob changes

iter-v3/020 is a single-axis (NEW risk primitive — concentration architecture) EXPLORATION. The labeling, model architecture, ATR labeling multipliers, z-score OOD threshold, BTC trend filter band, ADX threshold, low-vol floor, Hurst regime check, hit-rate feedback (disabled), CPCV parameters, and walk-forward window are unchanged from iter-v3/018. The only differences vs iter-v3/018 (NOT iter-v3/019, since funding axis is reverted):

- **NEW**: `max_per_symbol_pnl_share = 0.40` cap mechanism in `RiskV2Wrapper`
- **NEW**: `max_per_symbol_window_bars = 90` (~30-day rolling window)
- **NEW**: `enable_per_symbol_cap = True` flag (default OFF in code, ON in v3 runner)
- `ITERATION_LABEL` (cosmetic)
- `_verify_feature_columns` assertion bump (14 → 13)
- `pyproject.toml` sklearn pin (`>=1.5` → `>=1.8,<1.9`) — addresses Critic Check 12 flag

### 3.8 Inheritance from iter-v3/019 (and revert to iter-v3/018 feature surface)

The `iteration-v3/020` branch was branched from `iteration-v3/019` head. Inherited commits include all iter-v3/008-019 lineage. Critical inheritance verifiers (run before any code edits in Phase 6):

- BEFORE iter-v3/020 sub-fix #5 (revert funding):
  - `python -c "from crypto_trade.features_v3 import V3_FEATURE_COLUMNS; assert len(V3_FEATURE_COLUMNS) == 14 and 'funding_rate_zscore_30' in V3_FEATURE_COLUMNS"` exits 0 (still iter-v3/019 state)
- BEFORE iter-v3/020 sub-fix #1 (cap fields):
  - `python -c "from crypto_trade.strategies.ml.risk_v2 import RiskV2Config; c = RiskV2Config(); assert not hasattr(c, 'max_per_symbol_pnl_share')"` exits 0 (cap fields not yet present)
- AFTER iter-v3/020 sub-fix #5: 13-feature stack restored
- AFTER iter-v3/020 sub-fix #6: assertion at len==13
- AFTER iter-v3/020 sub-fixes #1-4: cap mechanism active in `_build_v3_model`
- `grep -E 'atr_tp_multiplier=2\.0' run_baseline_v3.py` exits 0 (still iter-v3/010 value)
- `grep -E 'zscore_threshold=2\.0' run_baseline_v3.py` exits 0 (still iter-v3/011 value)
- `grep -E 'adx_threshold=20\.0' run_baseline_v3.py` exits 0 (still iter-v3/013 baseline)
- `grep -E 'threshold_pct=15\.0' run_baseline_v3.py` exits 0 (still iter-v3/012 value)
- `python -c "from importlib import import_module; import sys; sys.path.insert(0,'.'); m=import_module('run_baseline_v3'); assert len(m.V3_MODELS)==3"` exits 0 (still iter-v3/013 universe)
- `uv run pytest tests/strategies/ml/ -v` exits 0 with all tests passing (Engineer adds adversarial cap unit test)

---

## Section 4 — Expected OOS Impact

### 4.1 EXPLORATION → headline metrics are GUIDANCE not GATES

Per Section 0.5 + skill spec, headline metrics are NOT BLOCK-triggering for the Critic on EXPLORATION iterations. The Critic emits `EXPLORATION-PROMISING`, `EXPLORATION-NEGATIVE`, `EXPLORATION-PROMISING-MECHANICAL`, `EXPLORATION-PROMISING-INERT`, `EXPLORATION-NEGATIVE-no-effect`, or `BLOCK` (process). iter-v3/020 NEVER updates BASELINE_V3.md regardless of verdict.

### 4.2 Predicted IS / OOS Sharpe ranges

Anchor: iter-v3/018 BOOTSTRAP baseline IS Sharpe **+0.3788 (multi-seed mean)** / **+0.4563 (seed 42 single)**; OOS Sharpe **+0.3869 (multi-seed mean)** / **+0.2343 (seed 42 single)**. iter-v3/020 runs at `--seeds 1 --n-trials 35` (EXPLORATION mode), so the closest-comparable single-seed metric is iter-v3/018 seed 42 = +0.4563 IS / +0.2343 OOS.

| Metric | iter-v3/018 anchor (multi-seed) | iter-v3/018 anchor (seed-42) | iter-v3/020 prediction (3-symbol, 13-feature, +cap) |
|---|---:|---:|---:|
| IS monthly Sharpe | +0.3788 | +0.4563 | **predicted [+0.30, +0.55] median +0.40** = Δ vs multi-seed [-0.08, +0.17]; Δ vs seed-42 [-0.16, +0.09] |
| OOS monthly Sharpe | +0.3869 | +0.2343 | **predicted [+0.45, +0.65] median +0.55** = Δ vs multi-seed [+0.06, +0.26]; Δ vs seed-42 [+0.22, +0.42] |
| IS top-share % | 87.36% (BCH multi-seed) / 78.72% (BCH seed-42) | — | **predicted < 40%** (mechanically enforced) |
| OOS top-share % | 86.01% (TRX multi-seed) / 152.01% (TRX seed-42) | — | **predicted < 40%** (mechanically enforced) |
| IS trades | 172 (cumulative) | 172 (seed 42) | **predicted [129, 215]** (saturation band ±25%) |
| OOS trades | 90.5 (mean) / 102 (seed 42) | 102 (seed 42) | **informational ~75-130** |
| Cap fire rate | (not present) | — | **expected 8-15% IS / 5-10% OOS** (rolling-cap counterfactual showed 10.5% / 7.8%) |
| Phase 6 wall-clock | 4.54h (CONFIRMATION) | — | predicted 15-25 min (3 symbols, 13 features, cap state tracking ~1% overhead, no parquet regen needed since features unchanged from iter-v3/019 set after column drop) |

The IS prediction band [+0.30, +0.55] reflects the **mid-prediction** (anchor multi-seed +0.3788 ± Optuna-adaptation from cap mechanism). Calibration:
- Lower bound +0.30: cap subtracts edge in IS by Δ -0.08 from multi-seed anchor; counterfactual evidence (Mode A static IS Δ -0.06; Mode B rolling IS Δ -0.24) supports a sub-anchor outcome under static rosters. Optuna at n_trials=35 typically narrows this loss.
- Upper bound +0.55: best-case where Optuna at n_trials=35 finds new hyperparams that compensate for the cap by avoiding heavy concentration in the first place; equivalent to "cap acts as regularizer that improves generalization".
- Median +0.40: balanced expectation; cap shaves a few basis points off IS but the overall Sharpe stays in the multi-seed anchor's vicinity.

The OOS prediction band [+0.45, +0.65] reflects the **upper-bound aspiration** (Optuna fully adapts to the cap mechanism + concentration discipline materially reduces single-symbol lottery risk):
- Lower bound +0.45: anchor multi-seed +0.3869 + Optuna-discovered diversification gain +0.06.
- Upper bound +0.65: anchor + cap reduces lottery risk by enabling LDO contribution that was suppressed in iter-v3/018 — substantial OOS lift.
- Median +0.55: balanced expectation; cap moderately improves OOS by reducing single-symbol lottery exposure.

**The counterfactual evidence is more pessimistic** (Mode A OOS Δ -0.36; Mode B OOS Δ -0.26 from anchor), supporting PATH C (NEGATIVE) as the lower-bound scenario. The user-mandated bands reflect upper-bound Optuna-adaptation. The empirical question is whether n_trials=35 Optuna can find hyperparams that recover the cap's lift on an OOS surface that the iter-v3/018 hyperparams (at n_trials=50) missed.

### 4.3 Falsifiers (locked before backtest)

**Falsifier 1**: IS Sharpe < iter-v3/018 multi-seed anchor (+0.3788) AND OOS Sharpe < anchor +0.2869 (anchor-0.10) → cap is NEGATIVE on both axes. PATH C verdict: EXPLORATION-NEGATIVE (clean) — concentration carries genuine signal that the cap removes; iter-v3/021+ would explore a different axis (NOT another concentration variant).

**Falsifier 2 (saturation predictor per `feedback_axis_saturation_predictor.md`)**: IS trade count outside [129, 215] (= [0.75 × 172, 1.25 × 172]) → axis behavioral effect deviates from prediction. If trades < 129 (<-25% reduction): the cap's floor-zero rounding fired aggressively OR Optuna re-tuning produced restrictive entries. If trades > 215 (>+25% expansion): the cap loosened entry restrictions OR an unexpected interaction with feature regeneration. Verdict path: BLOCK if the cap mechanism didn't propagate (verified via Falsifier 4 secondary check); otherwise EXPLORATION-NEGATIVE-no-effect or NEGATIVE-failed-axis.

**Falsifier 3** (process): Phase 6 wall-clock > 30 min on 3-symbol universe with 13-feature set → unexpected slowdown in cap state tracking pipeline. Engineer documents the cause.

**Falsifier 4 (NEW for NEW-risk-primitive-axis discipline)**: cap fires < 5% in IS run (cap state never activates because Optuna found hyperparams that preempt concentration before the cap fires) → axis is INERT — IS Sharpe direction is not attributable to the cap. Analogous to iter-v3/015's INERT pattern (model demonstrably ignored feature). Verdict: EXPLORATION-PROMISING-INERT (if Sharpe direction positive) or NEGATIVE-no-effect (if Sharpe direction negative). The counterfactual fire rate of 10.5% is the calibrated lower-bound expectation; < 5% indicates Optuna substantially adapted, which is itself a research finding (cap as silent regularizer).

**Falsifier 5 (NEW — concentration enforcement gate)**: post-cap top-share > 40% in IS or OOS → cap mechanism failed to enforce the constraint. This would indicate an implementation defect (e.g., the rolling window only sees future trades, the share computation uses absolute or signed shares incorrectly, the cap fires but doesn't propagate to weight_factor). Verdict: BLOCK (process) — Engineer fixes implementation before iter-v3/020 verdict is recorded.

**Process falsifier**: pre-flight `grep max_per_symbol_pnl_share src/crypto_trade/strategies/ml/risk_v2.py` exits non-zero, OR `python -c "from crypto_trade.strategies.ml.risk_v2 import RiskV2Config; assert hasattr(RiskV2Config(), 'max_per_symbol_pnl_share')"` exits non-zero, OR runner doesn't include `enable_per_symbol_cap=True` → setup drift; Phase 6 must not start.

### 4.4 EXPLORATION outcome interpretation (pre-commit catalog framing)

Per `feedback_promising_mechanical_subtype.md` + `feedback_axis_saturation_predictor.md` + iter-v3/015-019 precedent. §4.4 row 5 NEGATIVE-clean condition follows iter-v3/017's update: "either |Δ trades| ≥ 11 OR per-symbol shift > 5".

| Critic verdict | Conditions | Catalog row | Next iteration |
|---|---|---|---|
| `EXPLORATION-PROMISING` (PATH A) | OOS Sharpe Δ ≥ +0.10 vs iter-v3/018 multi-seed anchor (i.e., OOS ≥ +0.4869) AND post-cap top-share < 40% (Falsifier 5 PASS) AND IS trades in [129, 215] (Falsifier 2 PASS) AND cap fire rate ≥ 5% (Falsifier 4 PASS) | "Per-symbol cap reduced single-symbol lottery risk; OOS lift from concentration discipline" | iter-v3/021 EXPLORATION on a DIFFERENT axis category (DSR gate reformulation MEDIUM-priority OR another NEW risk primitive) — single-axis discipline preserved |
| `EXPLORATION-PROMISING-INERT` | OOS Sharpe within ±0.10 of iter-v3/018 multi-seed anchor (i.e., in [+0.2869, +0.4869]) AND IS trades in [129, 215] AND cap fire rate ≥ 5% | "Cap mechanism propagated but lift attribution ambiguous; concentration is not the bottleneck" | iter-v3/021 on a DIFFERENT axis |
| `EXPLORATION-PROMISING-MECHANICAL` | OOS Sharpe up ≥ +0.10 BUT trade-roster bit-identity to iter-v3/018 (Critic verifies via per-symbol shift ≤ 5) — UNLIKELY for cap axis given counterfactual fire rate 10.5% | "Cap added without behavioral change — accounting drift; non-compoundable" | similar to iter-v3/013 framing |
| `EXPLORATION-NEGATIVE-no-effect` (NULL-RESULT) | IS Sharpe direction wrong (Δ < 0 vs iter-v3/018 multi-seed) AND cap fire rate < 5% (Falsifier 4 fires) | "Optuna at n_trials=35 found hyperparams preempting cap fires; cap saturated; concentration was already managed" | iter-v3/021 on a DIFFERENT axis — should NOT be another concentration variant |
| `EXPLORATION-NEGATIVE` (clean) (PATH C) | (IS Sharpe Δ < -0.10 vs iter-v3/018 multi-seed anchor AND/OR OOS Sharpe < anchor -0.10 AND post-cap top-share < 40% AND non-bit-identical roster: \|Δ trades\| ≥ 11 OR per-symbol shift > 5) AND cap fire rate ≥ 5% (Falsifier 4 PASS) | "Concentration carries genuine signal; cap subtracts edge — lottery-REWARD not lottery-RISK" | iter-v3/021 on a DIFFERENT axis category — NOT another concentration variant |
| `BLOCK` (process) | Methodology check FAILED, OR Falsifier 2 (saturation, IS trades outside [129, 215]) AND axis didn't propagate, OR Falsifier 3 (wall-clock) triggered, OR Falsifier 5 (post-cap top-share > 40% indicating cap implementation defect) | (none) | Diary documents, iter-v3/021 fixes the methodology gap |

---

## Section 5 — Risk Mitigation

### 5.1 Cadence-discipline structural safeguards (5 inherited + 4 methodology-specific = 9 total)

iter-v3/020 inherits the cadence-discipline safeguards from skill SHA `d5c9f21` + the saturation-predictor rule + the new structural-axis preference rule + `feedback_v3_iter019_axis_priorities.md` LOCKED:

1. **2h wall-clock hard cap**: Engineer kills Phase 6 if elapsed > 2h. Wall-clock target < 30 min for 3-symbol + 13-feature `--exploration` mode.
2. **Single-axis variation rule** honored (only `+max_per_symbol_pnl_share=0.40` cap added; ATR/zscore-OOD/BTC-band/Hurst/low-vol/hit-rate/CPCV byte-for-byte identical to iter-v3/018; no gate threshold tuning; no universe change; no labeling change; no model architecture change). The funding-feature revert (sub-fix #5) is a MANDATED-pre-commit per Critic FINAL Rec 2 of iter-v3/019, NOT a separate axis — it returns the feature surface to the iter-v3/018 anchor for clean attribution.
3. **EXPLORATION never updates BASELINE_V3.md** — outcome (PROMISING / PROMISING-INERT / PROMISING-MECHANICAL / NEGATIVE / NEGATIVE-no-effect / BLOCK) records only in `briefs-v3/exploration_catalog.md` and `diary-v3/iteration_v3-020.md`.
4. **Saturation predictor falsifier** (Section 3.6 row 15 + Section 4.3 Falsifier 2, threshold derived from anchor `iter-v3/018 IS trades = 172` ±25% = [129, 215] per `feedback_axis_saturation_predictor.md`) actively verifies that the new risk primitive's behavioral effect is in expected band.
5. **Two-round Critic flow**: any methodology issue surfaces before Phase 6 launches.

Methodology-specific safeguards (NEW-risk-primitive concentration-architecture axis):

6. **Cap fire rate verifier** (Section 3.6 row 15 secondary): cap_fires > 0 in run.log gate stats — distinguishes "cap mechanism propagated and fired" from "cap added but never fired" (the iter-v3/015-019 INERT-via-noncontribution pattern adapted to a risk primitive).
7. **Concentration enforcement gate** (Section 4.3 Falsifier 5): post-cap top-share < 40% in IS AND OOS — verifies the cap actually enforces the constraint at backtest time. A cap that fires but doesn't reduce concentration < 40% is an implementation defect.
8. **Past-only computation discipline**: cap state uses rolling window over PAST closed trades only. Sub-fix #2 spec mandates `close_time < t` exclusivity. Critic Check 1 (Look-Ahead) verifier: adversarial unit test where 5 trades in symbol A close in [t-30d, t-1] window; the 6th trade at time t sees the cap-trigger; verify the CURRENT trade at time t is NOT included in its own past-share denominator.
9. **Adversarial unit test for cap mechanism** (sub-fix #3 verifier): test scenarios — (a) symbol A has 5 winning trades; symbol A's share > 40%; verify subsequent A trades scale by `cap / share`. (b) Symbol B has 1 win; symbol B's share < 40%; verify B's weight_factor unchanged. (c) Empty rolling window (warmup); verify pass-through at scale 1.0. (d) Negative-PnL symbol; verify share computed with absolute value OR positive-only-share semantics (Engineer's design choice — must be documented).

### 5.2 Methodology-pipeline safety (inherited from iter-v3/006-019)

1. **Adversarial unit tests** must PASS before backtest.
2. **File-artifact reconciliation table** (§3.6). 15 verifier commands; empty cells = Phase 5.5 BLOCK.
3. **Pre-flight grep-checks**: `max_per_symbol_pnl_share` field present in `RiskV2Config`, `enable_per_symbol_cap=True` in runner, `_verify_feature_columns` asserts len==13. Catches the case where setup edits were silently lost.
4. **Two-round Critic flow**: any methodology issue surfaces before Phase 6 launches.

### 5.3 NEW-risk-primitive-axis-specific risks (4 explicit)

1. **Cap implementation: per-symbol PnL share semantics**: signed-share vs absolute-share. Signed-share has a sign-flip pathology — when a sustained drag (LDO -130% IS) co-exists with profitable contributors, ratios cross zero erratically. Absolute-share is more robust but penalizes profitable contributors more aggressively. **Mitigation**: Engineer's sub-fix #2 implementation MUST document the chosen semantics in the function docstring AND in the engineering report. Recommended: positive-share-only — only cap symbols whose share > +cap; never cap negative-share symbols (drag is self-limiting via the model's loss-stopping mechanism). The EDA's Mode A/B counterfactuals used positive-share-only — Engineer should match.
2. **Look-ahead from cap state**: the rolling window must include only PAST closed trades. **Mitigation**: sub-fix #2 spec mandates `close_time < t` exclusivity. Critic Check 1 adversarial test (sub-fix #3) verifies past-only.
3. **Cap scaling vs the existing vol-scaling primitive**: both modify `weight`. Order of operations: `weight = sig.weight * vol_scale * cap_scale`. **Mitigation**: order specified in sub-fix #2; vol_scale and cap_scale computed independently. Both gates applied via multiplication — commutative operation, no order dependency on the final weight.
4. **Optuna's response to cap mechanism at n_trials=35**: at single-seed --exploration, Optuna may discover hyperparams that preempt cap fires (smaller leaves, tighter thresholds), yielding cap fire rate < 5% (Falsifier 4 fires). **This is a feature, not a bug**: it indicates Optuna found a regularization path that the cap previously enforced manually. The verdict in this case is PROMISING-INERT or NEGATIVE-no-effect (depending on Sharpe direction), with the catalog row explicitly flagging "cap saturated by Optuna preemption". This is a known structural risk for any risk-primitive axis at single-seed EXPLORATION.

---

## Section 6 — Risk Management Design

### 6.1 7-primitive table — UPDATED (one new primitive added; v3 now 8-primitive risk gate stack at iter-v3/020)

| # | Primitive | Spec | Fire-rate prediction (IS, 3-symbol, 13-feature) | Regime coverage |
|---|---|---|---|---|
| 1 | Vol scaling | `scale = clip(atr_pct_rank_200, 0.3, 1.0)` | Always on; mean scale ≈ 0.6 | High-vol → scale down |
| 2 | ADX gate | trade only when ADX ≥ 20 (iter-v3/013 baseline) | ≈ 60% of bars pass | Trend filter |
| 3 | Hurst regime check | trade only when 0.05 < hurst_100 < 0.95 | ≈ 90% of bars pass | Filters bond-like regimes |
| 4 | Feature z-score OOD | kill if any \|z\| > 2.0 (over **13** features now — reverted from iter-v3/019's 14) | ≈ 25–35% killed (back to iter-v3/018 range) | Distributional drift |
| 5 | Low-vol filter | trade only when atr_pct_rank_200 ≥ 0.33 | ≈ 67% of bars pass | Filters dead chop |
| 6 | Hit-rate feedback | DISABLED | 0% | Reserved for future tuning |
| 7 | BTC trend alignment | kill alt trade fighting BTC 14d ±15% | ≈ 12–13% killed | Macro flips |
| **8** | **Per-symbol PnL cap (NEW)** | scale `weight` by `cap / share` when symbol's 30-day rolling share > 0.40 | **expected 8-15% IS / 5-10% OOS** (rolling-cap counterfactual = 10.5% / 7.8%) | Concentration discipline |

Combined kill rate target: **80–90%** (matches iter-v3/018's range; primitive 8 is a SCALING primitive not a KILL primitive — it does not zero `weight`, only multiplies by `< 1.0`).

**Important sub-point**: primitive 8 is fundamentally different from primitives 1-7. Primitives 2-7 either scale weight (1, vol scaling) or kill weight to 0 (2-5, 7). Primitive 8 multiplicatively scales weight by `cap / share` only when the rolling per-symbol share exceeds the cap. The trade is NOT killed; only the position size shrinks. This is by design — a kill semantics would be PATH C-guaranteed (capping forces the model to abandon profitable concentrations entirely); scaling allows the model to retain the directional edge while reducing the single-symbol lottery exposure.

**Gate orthogonality**: Primitive 8 operates per-(symbol, candle) and is independent of the other 7. The order of operations in `get_signal` is: signal direction (from inner strategy) → primitive 4 (z-score OOD) → primitive 3 (Hurst) → primitive 2 (ADX) → primitive 5 (low-vol) → primitive 1 (vol scaling, multiplicative) → **primitive 8 (cap scaling, multiplicative)** → primitive 7 (BTC trend, post-aggregation) → primitive 6 (hit-rate, disabled).

### 6.2 Regime coverage — UNCHANGED

3-symbol IS data spans 2023-03-24 → 2025-03-23 — same as iter-v3/018. Regime coverage includes 2023 banking crisis, 2024 halving + Trump rally, 2024-08 yen-carry crash, 2025 January correction. The cap operates UNIFORMLY across regimes — its mechanism is portfolio-internal (per-symbol PnL share), not regime-conditional. Specifically, when TRX dominates in any regime (e.g., 2023-Q4 TRON rally), the cap fires for TRX trades; this is the desired behavior.

### 6.3 Concentration enforcement — primary axis, EXPLORATION-mode informational

iter-v3/018 multi-seed showed TRX 66.08% / 55.83% concentration (gate 7 floor 30% missed); BCH 87.36% IS. iter-v3/020's cap mechanism mechanically enforces a 40% ceiling at TRADE time. The OOS top-share is informational at EXPLORATION, but the cap activation IS the iteration's mechanism — the verdict cell is driven by IS Sharpe direction + cap fire rate (Falsifier 4). The concentration metric itself (post-cap top-share < 40%) is verified via Falsifier 5 — it's a process-correctness check, not the primary success metric.

---

## Section 7 — Pre-Registered Failure-Mode Prediction (7 predictions calibrated against 11 prior EXPLORATIONs + iter-v3/018 multi-seed evidence + iter-v3/020 EDA counterfactual evidence)

**Prediction P1 (process, P=10%)**: cap field added to `RiskV2Config` but not propagated to `RiskV2Wrapper.get_signal`. Engineer adds the dataclass field but a path-resolution issue in the get_signal logic causes runtime to silently no-op the cap. **Detection signal**: Falsifier 4 (cap fire rate) shows 0% across all 3 symbols OR Falsifier 2 (saturation predictor) fires. **Mitigation**: §3.6 rows 1-3 verifiers (3 independent signals + adversarial unit test).

**Prediction P2 (process, P=15%)**: cap state's rolling window has a look-ahead bug (e.g., includes the current trade in its own denominator, or uses `close_time <= t` instead of `< t`). **Detection signal**: adversarial unit test fails; Critic Check 1 fires. **Mitigation**: pre-flight verifier blocks Phase 6 launch.

**Prediction P3 (process, P=10%)**: per-symbol-share semantics ambiguity (signed vs absolute) produces unexpected cap activations. **Detection signal**: Falsifier 5 (post-cap top-share > 40%) fires OR cap fire rate way outside [5%, 25%] band. **Mitigation**: sub-fix #2 spec mandates positive-share-only semantics, mirroring EDA Mode A/B.

**Prediction P4 (model, P=20%)**: OOS Sharpe lifts to [+0.50, +0.65] (PATH A); the cap reduces single-symbol lottery risk and the resulting diversified portfolio has better OOS generalization. Optuna at n_trials=35 finds hyperparams compatible with the cap. PROMISING.

**Prediction P5 (model, P=30%)**: OOS Sharpe stays in iter-v3/018 multi-seed anchor range [+0.2869, +0.4869]; the cap fires but the redistribution doesn't materially shift OOS Sharpe. Concentration is not the primary bottleneck — feature signal weakness is. PROMISING-INERT (if Sharpe lifts but within the band) or NEGATIVE-no-effect.

**Prediction P6 (model, P=30%)**: OOS Sharpe drops below iter-v3/018 multi-seed anchor (-0.10 → < +0.2869); concentration carries genuine signal that the cap removes. The counterfactual evidence (Mode A OOS Δ -0.36; Mode B OOS Δ -0.26) calibrates this prior at high probability — PATH C. NEGATIVE-clean. iter-v3/021+ would explore a different axis (DSR gate reformulation OR TRX/2022-Q4 regime gate) since the concentration axis demonstrated edge-detrimental risk.

**Prediction P7 (model, P=15%)**: OOS Sharpe spikes to > +0.65; cap unlocks LDO contribution that was suppressed in iter-v3/018, the redistributed weight produces an unexpectedly strong OOS lift. PROMISING-strong. This would be the strongest evidence yet that concentration-architecture axes are higher-impact than feature-family axes.

**Prediction P8 (process, P=5%)**: cap fire rate < 5% in IS — Optuna at n_trials=35 found hyperparams that preempt cap fires entirely. PROMISING-INERT or NEGATIVE-no-effect verdict; catalog row flags "cap saturated by Optuna preemption". This is itself a research finding (cap-as-implicit-regularizer that Optuna duplicates internally).

P4 + P5 + P6 + P7 + P8 sum to 100% (model-axis outcomes). PATH C (P6) at 30% is HIGHER than usual for the EXPLORATION because the counterfactual evidence is PATH-C-supportive. Process predictions P1-P3 sum to 35% (failure-mode hedging, comparable to iter-v3/019's 35% reflecting NEW-axis-category complexity).

**Calibration vs prior EXPLORATIONs**:
- The NEW-risk-primitive axis category has ZERO prior calibration data points in v3 — iter-v3/020 is the first. Predictions are calibrated against iter-v3/015 (NEW microstructure feature, same INERT pattern at n_trials=10) and iter-v3/019 (NEW external-data-source feature, PROMISING-INERT) — both showed Optuna can saturate NEW axes at low trial counts. n_trials=35 is the new default, addressing this risk.
- Counterfactual evidence (Mode A IS Δ -0.06, OOS Δ -0.36; Mode B IS Δ -0.24, OOS Δ -0.26) supports a HIGHER probability for PATH C than typical EXPLORATION priors. P6 = 30% reflects this.
- The user-mandated bands (IS [+0.30, +0.55], OOS [+0.45, +0.65]) are upper-bound aspirational; the QR's primary belief is OUTCOME band [-0.10 vs anchor IS, -0.10 vs anchor OOS], with PATH A as low-probability upside and PATH C as moderate-probability downside.

---

## Section 8 — Pre-Registered MERGE/NO-MERGE Criteria — 11 EXPLORATION criteria

EXPLORATION never updates BASELINE_V3.md, so traditional MERGE thresholds do not apply. The 11 criteria below pre-register the catalog-row decision and provide unambiguous Critic verdict triggers.

1. **OOS Sharpe ≥ iter-v3/018 multi-seed anchor + 0.10 (i.e., ≥ +0.4869)**: catalog row records PROMISING verdict (PATH A).
2. **OOS Sharpe < iter-v3/018 multi-seed anchor − 0.10 (i.e., < +0.2869)**: Falsifier 1 fires — EXPLORATION-NEGATIVE if non-bit-identical roster (PATH C), or NEGATIVE-no-effect if axis didn't propagate (Falsifier 4 fires).
3. **OOS Sharpe in [+0.2869, +0.4869] (= anchor ± 0.10)**: PROMISING-INERT (inert verdict) — catalog row records INERT.
4. **n_trades ≥ 50 IS, ≥ 50 OOS**: BUNDLE-LEVEL trade-rate floor per `feedback_trade_rate_floor_bundle_level` (informational at EXPLORATION; predicted IS in [129, 215] — well above 50; OOS predicted ~75-130 — ≥50). Bundle (5 outer × 3-4× ensemble) at CONFIRMATION will multiply this 3-4×.
5. **PBO < 0.40 (per-cell mean)** AND `n_high_pbo_cells_99 ≤ 4`: methodology hygiene; both inherited unchanged from iter-v3/018 multi-seed (mean 0.0892; max 1.0 on TRX/2022-Q4 carry-forward — outstanding constraint flagged in BASELINE_V3.md but NOT iter-v3/020's axis to fix). iter-v3/020 expected near-identical PBO unless cap mechanism has unexpected cell-level effect.
6. **IC max abs < 0.70**: per Critic Check 4 — NO new feature added; existing 13-feature IC matrix unchanged from iter-v3/008 (max 0.685). PASS by inheritance.
7. **ADF p < 0.05 on 13 V3_FEATURE_COLUMNS** (or stationarity rationale): the 13 features unchanged from iter-v3/018; ADF inherits PASS.
8. **Reproducibility verifier**: SHAs stamped in engineering report (analysis `bbbe783`, runner setup commit, brief commit, Phase 5.5 gate, engineering report).
9. **Pareto dominance**: vacuous under single-seed EXPLORATION (Section 8 criterion 9 waiver inherited from iter-v3/006-019).
10. **Symbol exclusion + feature isolation + NEW: track isolation for risk_v2 cap field**: `set({BCH, LDO, TRX}) ∩ V3_EXCLUDED_SYMBOLS = ∅` ✓; `risk_v2.py` has no new imports from features modules; the cap mechanism uses only `TradeResult` schema fields (already present). Zero cross-track contamination.
11. **Behavioral-effect verifier (saturation falsifier per `feedback_axis_saturation_predictor.md` ±25% rule)**: IS trades in **[129, 215]** (= anchor iter-v3/018 IS trades 172 ± 25%). The threshold is DERIVED from §2.3's anchor; not a hardcoded constant. **PLUS SECONDARY VERIFIER (Falsifier 4)**: cap fire rate ≥ 5% in IS run. **PLUS CONCENTRATION ENFORCEMENT (Falsifier 5)**: post-cap top-share < 40% in IS AND OOS. Critic uses BOTH/THREE signals to disambiguate "axis propagated AND mechanism active" from "axis added but Optuna preempted (cap-saturation-by-preemption pattern)".

**Catalog-axis verdicts** map to §4.4 table. The catalog row records the verdict exactly as Critic FINAL emits it.

---

## Section 9 — Library Stack Declaration

**SAME stack as iter-v3/008-019** — one explicit pin update in iter-v3/020:

```
python = 3.13
lightgbm = 4.6.0
numpy = 2.2.6
pandas = 3.0.0 (or recent compatible)
scikit-learn = 1.8.0  # PINNED EXPLICITLY (sub-fix #8) — was >=1.5 prior
pyarrow = 23.0.1 (for parquet I/O)
mlfinpy = 1.4.0 (CPCV; MIT-licensed fork)
pypbo = 0.10.0 (PBO via CSCV)
fracdiff = 0.10.0 (Numba-accelerated; FracdiffStat + ADF auto-d*)
statsmodels = 0.14.6 (adfuller for ADF stationarity)
optuna = 4.8.0
scipy = 1.17.0
httpx = (already used for kline fetcher; reused for funding-rate fetcher in iter-v3/019)
```

**The sklearn pin is the iter-v3/020 first-commit pre-commit per Critic FINAL Rec of iter-v3/019 review (Check 12 flag: 1.8.0 → 1.6.0 silent drift between briefs and runtime).** The iter-v3/018 BASELINE_V3.md stamps sklearn 1.8.0; the current `uv.lock` is at 1.8.0; the iter-v3/019 runtime was at 1.6.0 (transient resolution). Pinning to `>=1.8,<1.9` matches BASELINE and the current install state. **No new package additions.** The cap mechanism uses only `dataclass` (stdlib) + numpy (already imported). No new dependencies.

---

## Section 10 — Adversarial Tests (one new test mandatory)

The Engineer SHOULD add ONE new test in Phase 6 (mandatory for this axis):

- `tests/strategies/ml/test_per_symbol_cap.py::test_per_symbol_cap_basic` — assert that when symbol A has 5 winning trades all in the rolling window, the 6th trade's `weight_factor` scales by `cap / share`. Verify with synthetic trade list.
- `tests/strategies/ml/test_per_symbol_cap.py::test_per_symbol_cap_warmup` — assert that during warmup (fewer than 5 prior trades), all trades pass through at scale 1.0 (no cap applied).
- `tests/strategies/ml/test_per_symbol_cap.py::test_per_symbol_cap_past_only` — assert the rolling window uses STRICTLY past closed trades (close_time < t); the current trade is not in its own denominator. Critic Check 1 (Look-Ahead) verifier.
- `tests/strategies/ml/test_per_symbol_cap.py::test_per_symbol_cap_disabled_by_default` — assert that with `enable_per_symbol_cap=False`, `weight_factor` is unchanged from inner strategy's default. Backward compatibility for v1/v2 runners.
- `tests/strategies/ml/test_per_symbol_cap.py::test_per_symbol_cap_concentration_enforcement` — assert post-cap rolling-window top-share is mathematically bounded ≤ cap (Falsifier 5 verifier).

If Engineer runs out of time (2h cap), the basic + past-only tests are mandatory; warmup + disabled + concentration-enforcement tests are deferrable but recommended.

---

## Section 11 — Catalog Row Pre-Commit (audit-trail discipline)

Per iter-v3/006+ catalog discipline, this brief pre-commits a structural template for the iter-v3/020 catalog row before backtest results are known:

```
| iter-v3/020 | 2026-05-07 | NEW risk primitive → +max_per_symbol_pnl_share=0.40 (concentration architecture; HIGH-priority axis #2) | IS Sharpe Δ TBD vs iter-v3/018 multi-seed +0.3788 | OOS Sharpe TBD vs anchor +0.3869 | TBD verdict | TBD candidate? |
```

The catalog row will be filled by the Phase 8 diary entry. The verdict cell maps to §4.4 + §8 criteria 1-3 + 11. The "candidate?" cell maps to whether the next CONFIRMATION-bundling QR should consider iter-v3/020 as a stack ingredient.

**Pre-committed disposition** (cannot be renegotiated post-hoc):
- If verdict = `EXPLORATION-PROMISING` (PATH A) AND Falsifier 4 PASSES (cap fire rate ≥ 5%): catalog row marked YES candidate (compoundable as a structural ingredient in any future CONFIRMATION bundle; first NEW-risk-primitive ingredient).
- If verdict = `EXPLORATION-PROMISING-INERT`: catalog row marked NO candidate (cap propagated but no material lift — concentration is not the bottleneck; future risk-primitive axes should test orthogonal mechanisms — e.g., per-symbol drawdown brake, time-decaying weight).
- If verdict = `EXPLORATION-PROMISING-MECHANICAL` (UNLIKELY given counterfactual fire rate 10.5%; flagged for completeness): catalog row marked YES with NON-COMPOUNDABLE flag.
- If verdict = `EXPLORATION-NEGATIVE` or `EXPLORATION-NEGATIVE-no-effect`: catalog row marked NO; iter-v3/021 explores a DIFFERENT axis category. Per `feedback_v3_iter019_axis_priorities.md` MEDIUM #3 (DSR gate reformulation) or MEDIUM #4 (TRX/2022-Q4 regime gate) is the natural next axis. NEXT iteration MUST NOT be another concentration variant — single-axis discipline + axis-category-rotation discipline.

**Catalog count after iter-v3/020**: 2 of 10 EXPLORATIONs in the post-bootstrap cycle; **8 more required** before any CONFIRMATION can launch (earliest = iter-v3/028). Axis coverage after iter-v3/020: features × 2 + labeling × 1 + gate-zscore × 1 + gate-btc-trend × 1 + universe × 1 + gate-adx × 1 (CLOSED) + NEW microstructure feature × 1 (CLOSED-narrow) + NEW model arch × 1 (CLOSED-at-config) + NEW labeling arch × 1 (PATH C) + bootstrap CONFIRMATION × 1 + NEW external-data-source feature × 1 (PROMISING-INERT) + **NEW risk primitive (per-symbol cap) × 1** = 12 unique axis representations after iter-v3/020.

**Forward axis pipeline** (iter-v3/021-028 candidates pre-pre-committed for QR continuity, NOT mandates per `feedback_v3_iter019_axis_priorities.md` LOCKED priority order):
- iter-v3/021 candidates: depending on iter-v3/020 verdict, the natural next axis is MEDIUM-priority #3 (DSR gate reformulation) OR MEDIUM-priority #4 (TRX/2022-Q4 regime gate). If iter-v3/020 is PROMISING and yields a clean concentration mechanism, iter-v3/021 may attack the OUTSTANDING TRX/2022-Q4 PBO=1.0 regime issue with a regime-aware kill gate.
- iter-v3/022+ candidates: depend on iter-v3/020 + iter-v3/021 verdicts; further NEW risk primitives (per-symbol drawdown brake, time-decaying weight, vol-target ceiling) only if a risk-primitive workflow is well-established post-iter-v3/020; else MEDIUM/LOW priority axes.

---

## Final Brief-Authoring Checklist (Phase 5.5 self-check)

- [x] §0 sacred constants UNCHANGED, restated.
- [x] §0.5 EXPLORATION declaration with cadence count (2 of 10 in post-bootstrap cycle); STRUCTURAL axis declared; explicit "NOT a gate-threshold knob"; references `feedback_v3_iter019_axis_priorities.md` LOCKED HIGH #2 + `feedback_structural_over_knob_exploration.md`.
- [x] §1 hypothesis: one sentence, falsifiable; mechanism explanation (cap reduces single-symbol lottery risk while preserving directional edge; predicted IS [+0.30, +0.55] median +0.40 / OOS [+0.45, +0.65] median +0.55).
- [x] §2 IS-only numerical evidence with COMMITTED analysis script SHA `bbbe783`; per-symbol concentration baseline; counterfactual under 3 cap modes (anchor, static, rolling) showing PATH C lower-bound; behavioral-effect predictor with derived saturation band [129, 215] anchored at iter-v3/018 IS trades 172.
- [x] §3 sub-fixes (10-item) with verifier commands; reconciliation table 15 rows; new cap fields + cap state + RiskV3Wrapper inheritance + funding-revert + sklearn pin + ITERATION_LABEL update + n_trials=35 verification.
- [x] §4 predicted IS Sharpe band [+0.30, +0.55] median +0.40, OOS Sharpe band [+0.45, +0.65] median +0.55; 5 catalog framings + falsifiers 1-5 + process locked; §4.4 row 5 condition `|Δ| ≥ 11 OR per-symbol shift > 5` per iter-v3/017 update.
- [x] §5 risk mitigation (5 cadence + 4 methodology + 4 axis-specific risks: implementation semantics, look-ahead, vol-scaling interaction, Optuna preemption).
- [x] §6 8-primitive table — UPDATED (primitive 8 = per-symbol cap NEW; primitives 1-7 byte-identical to iter-v3/018; z-score OOD reverts to 13-feature scope).
- [x] §7 8 failure-mode predictions calibrated against 11 prior EXPLORATIONs + iter-v3/018 multi-seed evidence + iter-v3/020 EDA counterfactual evidence (process P1-P3 = 35%; model P4-P8 = 100%; PATH C P6 = 30% reflecting counterfactual support).
- [x] §8 11 EXPLORATION criteria; criterion 11 = saturation falsifier with derived band [129, 215] per `feedback_axis_saturation_predictor.md` + Falsifier 4 cap-fire-rate verifier + Falsifier 5 concentration-enforcement verifier.
- [x] §9 library stack with sklearn pin update flagged (sub-fix #8); no new dependencies.
- [x] §10 adversarial tests (5 new tests recommended; 2 mandatory).
- [x] §11 catalog row pre-commit + dispositions; forward axis pipeline (iter-v3/021+ candidates per `feedback_v3_iter019_axis_priorities.md` LOCKED priority order).

**Brief authorship complete.** Engineer Phase 5.5 gate is the next step.
