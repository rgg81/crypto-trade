# iter-v3/078 — Research Brief

**Iteration**: iter-v3/078 — Cycle 2 EXPLORATION #8 of 10
**Branch**: `iteration-v3/078`
**Date**: 2026-05-15
**Axis**: UNIVERSE REVISION — replace `LDOUSDT` with `ADAUSDT` in `V3_MODELS`

---

## Section 0 — Data Split Declaration

The sacred constants are **UNCHANGED**:

```
OOS_CUTOFF_DATE = 2025-03-24       # IMMUTABLE
training_months = 24                # IMMUTABLE
```

- **IS window**: earliest available data per symbol → 2025-03-24. For the swap-in symbol ADAUSDT the IS window runs from its data start (2020-01-31 in `data/features_v3/`, well before the v3 IS span) to 2025-03-24; the walk-forward backtest's first trade-eligible month is governed by the 24-month training window plus the feature warm-up, exactly as for the incumbent symbols.
- **OOS window**: 2025-03-24 → present (data extent ~2026-05).
- The QR uses ONLY IS data in Phases 1–5. The walk-forward / CPCV backtest runs on ALL data; the reporting layer splits at `OOS_CUTOFF_DATE`. The QR sees OOS for the first time in Phase 7.

### RE-ANCHORING (Critic /077 Rec #1 — adopted at the /077 closeout)

The frozen iter-v3/060 EXPLORATION-MODE anchor (IS +0.8325 / OOS +0.1403) is **STALE** — iter-v3/077 (the first iteration since /060 to run the exact /060 14-feature config with no axis) established that it does not reproduce on current code + current data. **iter-v3/078 anchors against the current-code /060-config baseline: IS +0.8236 / OOS +0.2078.** All /078 IS/OOS deltas in this brief are computed against IS +0.8236 / OOS +0.2078, NOT the frozen /060 values.

The anchor gap decomposes exactly and additively (`analysis/iteration_v3-078/T0_anchor_values.csv`):
- **IS code-drift: −0.0089** — entirely the iter-v3/061 TRX `vol_scale_floor_per_symbol={"TRXUSDT": 0.5}` (introduced 16 iterations after /060; a permanent, deterministic offset that floors 13 IS TRX `weight_factor` values).
- **OOS data-extent: +0.0675** — the 2026-05 OOS month that post-dates /060's data fetch (monotonic with calendar time).

This is a methodology correction — a stale reference value replaced by the freshest reproducible no-axis run of the canonical config — **not** a measurement-window change. The OOS-cutoff and start dates are untouched. The /059 CONFIRMATION baseline (tag `v0.v3-059`, IS +1.0894 / OOS +0.5791) is the canonical baseline and is **NOT** the EXPLORATION anchor; it is unchanged and unaffected.

---

## Section 0.5 — Iteration Type Declaration

**TYPE: EXPLORATION** — cycle 2 EXPLORATION #8 of 10.

- Single-axis variation: ONE primary change — the universe symbol set (`LDOUSDT` → `ADAUSDT`).
- Run config: `run_baseline_v3.py --exploration --n-trials 35` → `EXPLORATION_ENSEMBLE_SIZE = 3`, 3 outer seeds (`ENSEMBLE_SEEDS` outer=42 lineage subset `[191664963, 1662057957, 1405681631]`). 3-symbol universe (BCH/ADA/TRX). REQUIRED_GAP=66, embargo 22. Total 315 Optuna trials.
- **Wall-clock budget HARD CAP: 2h.**
- This EXPLORATION does NOT update `BASELINE_V3.md` regardless of classification (only a CONFIRMATION-MERGE updates the baseline). It is cycle 2 EXPLORATION #8; the cycle-2 CONFIRMATION is iter-v3/081 or later.
- **Type justification**: an EXPLORATION is the correct vehicle — a universe revision is a single-axis structural variation whose multi-seed behaviour the cycle-2 CONFIRMATION must validate before any baseline change. The dead-paths note "ADA single-seed strong, 5-seed washes" is a CONFIRMATION-level concern; the EXPLORATION's job is to produce the single-axis data point and the IS-edge-screen evidence the CONFIRMATION QR needs.

---

## Section 1 — Hypothesis

Replacing the structurally weak `LDOUSDT` (the symbol that drags every cycle-1 and cycle-2 v3 iteration; /060 IS net_pnl −11.44%, 27.3% WR, only 11 IS trades) with `ADAUSDT` — which clears LDO on a walk-forward IS-edge screen by +1.17 IS-Sharpe (ADA +0.617 vs LDO −0.550, IS-only, 14-feature anchor stack) — lifts the IS aggregate monthly Sharpe **without** the IS-up/OOS-down regime tension that the feature and meta-labeling axes structurally trigger, because LDO is the one in-universe symbol whose drag is NOT regime-split-correlated (LDO is weak in both the IS and the OOS windows).

---

## Section 2 — IS-Only Numerical Evidence

All evidence is produced by the committed EDA `analysis/iteration_v3-078/axis_selection_eda.py` (EDA SHA in Section 10.3) and its nine output tables (`T0`–`T8`). The EDA is IS-data-only; its `_grep_no_oos_tuning()` AST self-audit returns PASS (Section 10.2).

### Section 2.1 — T0: anchor-value declaration and the re-anchor decomposition

`T0_anchor_values.csv`:

| metric | value |
|---|---:|
| frozen /060 anchor IS monthly Sharpe (STALE) | +0.8325 |
| frozen /060 anchor OOS monthly Sharpe (STALE) | +0.1403 |
| **/078 RE-ANCHOR IS monthly Sharpe (current-code /060-config)** | **+0.8236** |
| **/078 RE-ANCHOR OOS monthly Sharpe (current-code /060-config)** | **+0.2078** |
| IS code-drift component (iter-v3/061 TRX `vol_scale_floor=0.5`) | −0.0089 |
| OOS data-extent component (2026-05 OOS month) | +0.0675 |

The re-anchor values are independently corroborated by the /077 `comparison.csv` (`monthly_sharpe` IS 0.8236 / OOS 0.2078).

### Section 2.2 — T1: IS regime-stratified attribution (confirms the /077 reframing)

`T1_regime_stratification.csv` — /060's IS monthly PnL stratified by the exogenous per-calendar-month BTC-regime label (`build_btc_monthly_regime`; a month is BULL if ≥50% of BTC 8h bars have `close[t-1] > SMA_270[t-1]`, `.shift(1)` before the rolling SMA — past-only):

| IS stratum | n_months | monthly_sharpe | % positive | n_trades |
|---|---:|---:|---:|---:|
| IS_BEAR_CHOP | 15 | **+1.2909** | 46.7% | 55 |
| IS_BULL | 18 | **+0.4100** | 33.3% | 104 |
| OOS_all (INFORMATIONAL) | 14 | +0.1403 | 50.0% | 102 |

The /077 reframing finding **reproduces exactly**: the IS drag is in the BULL months (Sharpe +0.41, 33% positive), not bear/chop (+1.29, 47%).

### Section 2.3 — T2: IS per-symbol / per-direction decomposition

`T2_symbol_direction.csv`:

| cut | n_trades | win_rate_pct | net_pnl_pct | mean_dur |
|---|---:|---:|---:|---:|
| symbol=BCHUSDT | 73 | 45.2 | **+79.45** | 6.85 |
| symbol=LDOUSDT | 11 | 27.3 | **−11.44** | 4.91 |
| symbol=TRXUSDT | 75 | 29.3 | −23.04 | 6.00 |
| regime=BULL,dir=LONG | 57 | 36.8 | +13.80 | 6.40 |
| regime=BULL,dir=SHORT | 47 | 27.7 | **−14.29** | 6.11 |
| regime=BEAR/CHOP,dir=LONG | 21 | 47.6 | +14.90 | 6.14 |
| regime=BEAR/CHOP,dir=SHORT | 34 | 41.2 | +30.56 | 6.56 |

Two facts. **(1) LDO structural weakness**: LDO produces only 11 IS trades (chronic under-trading; the /071 M2 collapsed LDO to 8 OOS trades) at 27.3% WR and −11.44% net_pnl. **(2) The bull-month drag is concentrated in counter-trend SHORTs**: `regime=BULL,dir=SHORT` is 27.7% WR / −14.29 net_pnl — the directional-quality drag the /077 reframing localized.

### Section 2.4 — T3/T4: NEW-feature candidate EXHAUSTION (candidate #1 — rejected)

The /077 diary's HIGHEST-priority candidate is "a bull-month entry-discrimination feature." The QR built and screened **two** candidate features with the /077 conditional-orthogonality methodology (a 15-feature walk-forward LightGBM, per-IS-month gain-importance map). `T3_feature_candidate_exhaustion.csv`:

| candidate_feature | mean_rank BCH/LDO/TRX | last-month rank BCH/LDO/TRX | max cond-ortho corr | engineered falsifier |
|---|---|---|---:|---|
| `overext_atr_50` (raw `\|close−SMA50\|/ATR21`) | 13.0 / 13.7 / 14.5 | 12 / 15 / 15 | 0.1769 | **FAILS** |
| `momentum_extension_brake_5d` (`ret_5d·(1−clip(overext/4,0,1))`) | 13.9 / 13.5 / 14.2 | 14 / 15 / 15 | 0.3156 | **FAILS** |

**Both candidates are INERT** — rank 12-15/15 across all three symbols, mean rank 13.0-14.5/15. Both FAIL the `feedback_v3_engineered_feature_pivot.md` PATH B engineered-feature falsifier (rank ≤10 AND importance ≥30 for ≥1 symbol). The mechanism is the `feedback_v3_engineered_features_dont_stack.md` same-family displacement rule — another `ret_5d`-derived feature competes for `colsample_bytree` picks against the incumbent `regime_momentum_signed_5d` and is not allocated splits at n_trials=35 / 3-seed EXPLORATION. A NEW feature reproduces the rank-14/14-INERT channel (the funding-rate family, microstructure `tbr_zscore_30`, etc.).

**Conditional-orthogonality cross-check (`T4_cross_check.csv`)**: both candidates' max conditional-orthogonality correlation (0.18 / 0.32) is **below** the a-priori 0.35 ceiling — so the NEW-feature axis is rejected for **INERT importance rank**, NOT for conditional regime-loading. T4 also reports the ADAUSDT model-stability sanity: ADA's per-IS-month top-feature importance share is 0.119 (mean), identical to TRX (0.123) and LDO (0.116) — a normal, non-degenerate distribution; ADA's top-share-vs-BULL correlation is +0.170, comparable in magnitude to TRX (−0.247) and LDO (−0.213). ADA does not behave like a pathologically regime-loaded symbol.

### Section 2.5 — T5: meta-labeling M2 candidate EXHAUSTION (candidate #2 — rejected)

The /077 diary's second candidate is "a re-scoped meta-labeling M2." An M2 take/skip classifier needs a feature that discriminates the /060 IS roster's winners from its losers **at entry**. `T5_m2_candidate_exhaustion.csv` measures the per-trade winner/loser discrimination AUC on the /060 IS roster:

| scope | n_trades | max \|AUC−0.5\| |
|---|---:|---:|
| ALL_IS | 159 | **0.0640** |
| BULL_months | 104 | **0.0664** |
| BCH | 73 | 0.0864 |
| LDO | 11 | 0.4167 *(n=11 — small-sample noise, not signal)* |
| TRX | 75 | 0.1038 |

The maximum per-trade discrimination |AUC−0.5| is **0.064** (ALL_IS) and **0.066** (BULL months) — essentially identical to the near-zero wall the /071 meta-labeling EDA hit (portfolio mean |AUC−0.5| = 0.0577; /071 went SUSPICIOUS-OOS-DOMINANT). The bull-month overextension signal is real at the **monthly-aggregate / regime-stratum** level but the **per-trade entry discrimination is near-random** — the structural meaning of "directional-quality problem." An M2 built on these features filters at near-random and reproduces /071. The LDO AUC 0.42 is on n=11 trades — pure small-sample noise, not exploitable.

### Section 2.6 — T6: the escapability bound (the load-bearing structural finding)

`T6_escapability_bound.csv` — the /060 IS **and** OOS rosters stratified by (regime=BULL, direction). The OOS rows are INFORMATIONAL escapability-bound evidence and feed NO selection:

| cohort | n_trades | win_rate_pct | net_pnl_pct |
|---|---:|---:|---:|
| IS_BULL_LONG | 57 | 36.8 | +13.80 |
| IS_BULL_SHORT | 47 | 27.7 | **−14.29** |
| OOS_BULL_LONG | 19 | 52.6 | +10.45 |
| OOS_BULL_SHORT | 28 | 42.9 | **+10.76** |
| IS_BULL_SHORT_TRXUSDT | 18 | 16.7 | **−23.74** |
| OOS_BULL_SHORT_TRXUSDT | 12 | 50.0 | **+12.07** |
| IS_BULL_SHORT_LDOUSDT | 6 | 33.3 | −1.16 |
| OOS_BULL_SHORT_LDOUSDT | 8 | 25.0 | **−12.58** |

**The IS bull-month drag is NOT escapable by any IS-improving intervention.** The IS bull-month losers ARE the OOS bull-month winners: portfolio bull-SHORT is IS 27.7% WR / −14.29 but OOS 42.9% WR / +10.76. Per-symbol the extreme is TRX — IS bull-SHORT 16.7% WR / −23.74 (the single largest IS drag) flips to OOS 50.0% WR / +12.07. Any feature, M2, or gate that suppresses the IS bull-month drag also suppresses a profitable OOS cohort — the /075 IS-up/OOS-down structural tension (`feedback_v3_is_oos_regime_divergence.md`), where the discriminator's sign is regime-correlated with the IS/OOS split.

**LDOUSDT is the one exception.** LDO bull-SHORT is the only cohort weak in **both** windows: IS −1.16 *and* OOS −12.58. LDO's drag is NOT regime-split-correlated — so replacing LDO does **not** trip the /075 tension. This is precisely why the universe-revision axis is the EDA-supported one: the in-universe feature/M2/gate space is exhausted (T3, T5) and bounded by escapability (T6), and LDO is the binding structural constraint that a universe swap — and only a universe swap — can address without re-triggering the regime tension.

### Section 2.7 — T7: the IS-edge screen (selects the swap target)

The /077 diary mandates a replacement clear an IS-edge screen BEFORE inclusion. `T7_is_edge_screen.csv` runs a walk-forward IS-only edge proxy (a coarse single-seed long/short LightGBM, screen-grade `n_estimators=120`, on the 14-feature anchor stack with fixed triple-barrier exits — a SCREEN, not a backtest; every test month's loop terminates strictly before `OOS_CUTOFF_MS`):

| symbol | status | IS monthly Sharpe | n_months | % positive months |
|---|---|---:|---:|---:|
| **ADAUSDT** | screened | **+0.617** | 59 | 54.2 |
| ALGOUSDT | screened | +0.283 | 55 | 54.5 |
| VETUSDT | screened | −0.107 | 59 | 49.2 |
| **LDOUSDT** *(replacement target)* | screened | **−0.550** | 28 | 42.9 |
| AVAXUSDT | stale parquet | n/a | — | — |
| HBARUSDT | stale parquet | n/a | — | — |

**ADAUSDT is the IS-edge-screen argmax** — it clears the replacement target LDOUSDT by **+1.17 IS-Sharpe** (+0.617 vs −0.550), the decisive IS-only edge gap. ALGO clears LDO too (+0.283) but by far less; VET fails the screen (−0.107). AVAX/HBAR `features_v3` parquets are stale (missing `regime_momentum_signed_5d` — generated before that feature existed) and are excluded from the screen — the QE will regenerate them in Phase 6 only as a fallback if ADA fails a Phase-6 check, but the QR pre-commits ADA as the target on the screen evidence. The T7 screen is a **direct walk-forward IS-edge measurement**, not a price-level correlation test — it does not repeat the /021 universe-expansion failure mode ("EDA correlation captured price diversity not signal diversity").

### Section 2.8 — T8: holding-time predictor (removed LDO vs added ADA)

`T8_holding_time.csv` — the label-implied first-touch trade duration of the REMOVED cohort (LDO) vs the ADDED cohort (ADA):

| cohort | IS label-dur mean | IS label-dur median | IS TP% / SL% / timeout% |
|---|---:|---:|---|
| removed (LDOUSDT) | 6.04 candles | 4.0 | 27.4 / 69.2 / 3.4 |
| added (ADAUSDT) | 6.42 candles | 4.0 | 28.8 / 65.7 / 5.5 |
| **ADDED minus REMOVED gap** | **+0.38 candles** | — | falsifier >+1.0 candle → **NOT fired** |

The added-vs-removed mean-duration gap is **+0.38 candles** — well inside the +1.0-candle falsifier; the medians are identical (4.0). The swap is **holding-time-orthogonal**: it does not load the IS/OOS regime factor via barrier-mechanics extension (channel a) and does not skew the roster toward longer-held trades (channel c, the /076 selection channel).

### Section 2.9 — Why this is NOT the closed iter-v3/069 ADA axis (replacement ≠ expansion)

iter-v3/069 tested **adding ADAUSDT as a 4th symbol** (universe EXPANSION: BCH+LDO+TRX+ADA) and classified INERT-AT-EXPLORATION; in that 4-symbol context ADA contributed OOS +0.42 wpnl (18 trades, 27.8% OOS WR). /078 is a structurally DIFFERENT axis and the /069 INERT verdict does not transfer:

1. **/069 added ADA on top of LDO** — the LDO drag (/069 LDO OOS −20.73 wpnl) was STILL in the portfolio. /078 **removes** LDO entirely. At the symbol-slot level the swap is a +21-wpnl OOS swing vs /069 (ADA's +0.42 replacing LDO's −20.73), and removes the standing cycle-long LDO IS drag (T2: −11.44% IS net_pnl).
2. **/069's ADA was selected by feature-space distance** (the /069 EDA chose ADA by "lowest feature-space distance to BCH+LDO+TRX" — a correlation criterion, the /021 failure mode). /078's T7 IS-edge screen is a **direct walk-forward IS-edge measurement** (ADA +0.617 vs LDO −0.550) — the correct gate the /077 diary mandates, not a correlation proxy.
3. **The dead-paths catalog and the /069 closeout close ADA-as-EXPANSION, not ADA-as-REPLACEMENT.** A 4-symbol expansion dilutes `colsample_bytree` and per-symbol model budget; a 3→3 replacement does not. `feedback_v3_concentration_is_signal.md` treats universe expansion (denominator expansion) and replacement as distinct mechanisms.

**Honest caveat carried forward**: ADA's measured /069 OOS profile (27.8% WR, +0.42 wpnl as a symbol) is modest — the IS-edge screen makes the IS case strong, but ADA's OOS edge is genuinely uncertain to the QR. Section 4.1 widens the OOS prediction band accordingly and Section 7 floors SUSPICIOUS at the cycle base rate.

---

## Section 3 — Proposed Changes

Exactly **ONE** primary axis. /078 starts from the /060 14-feature anchor + the /077 `conditional_orthogonality.csv` report instrumentation (which STAYS — accretive tooling, no revert), and applies the single new axis on top.

### 3.1 — PRIMARY AXIS: universe revision — replace `LDOUSDT` with `ADAUSDT`

`V3_MODELS` in `run_baseline_v3.py` changes one symbol:

```python
V3_MODELS = (
    ("A (BCHUSDT)", "BCHUSDT"),
    ("C (ADAUSDT)", "ADAUSDT"),   # was ("C (LDOUSDT)", "LDOUSDT")
    ("D (TRXUSDT)", "TRXUSDT"),
)
```

This is a **universal** change (the universe), not a per-symbol customization — every symbol still uses the same 14-feature anchor stack, the same labeling, the same risk gates. The 3-symbol universe count is unchanged. ADAUSDT is **NOT** in `V3_EXCLUDED_SYMBOLS` (verified against the runner constant — the EDA `main()` asserts this).

**What does NOT change** — the feature set stays the 14-feature `V3_FEATURE_COLUMNS_TOP_N` anchor; the ATR labeling stays `DEFAULT_ATR_MULTIPLIERS = (2.0, 1.0)` with `V3_ATR_MULTIPLIERS_PER_SYMBOL = {}` empty; the 7-primitive risk-gate stack is unchanged; `ENSEMBLE_SEEDS` unchanged; the Optuna search unchanged; `V3_FEATURES_PER_SYMBOL = {}` stays empty. The /077 `_write_conditional_orthogonality` report instrumentation **stays** (accretive tooling — no revert).

**`vol_scale_floor_per_symbol` handling.** The `RiskV2Config` carries `vol_scale_floor_per_symbol={"TRXUSDT": 0.5}` (iter-v3/061). LDOUSDT is **not** a key in that dict — so removing LDO from the universe leaves the dict untouched and correct (TRX-only floor; ADA, like LDO before it, uses the global floor). No `RiskV2Config` change is needed.

### 3.2 — Affected code (setup commit)

| File | Change |
|---|---|
| `run_baseline_v3.py` | `V3_MODELS`: `LDOUSDT` → `ADAUSDT`; `ITERATION_LABEL` → `"v3-078"`; pre-flight assertion sites that hardcode the `("BCHUSDT","LDOUSDT","TRXUSDT")` universe tuple updated to `("BCHUSDT","ADAUSDT","TRXUSDT")` (the ATR-multiplier check loop, the `features_for_symbol` check loop, the `_build_v3_model` per-symbol smoke checks, the pre-flight print strings). The `vol_scale_floor_per_symbol={"TRXUSDT": 0.5}` assertion is unchanged (LDO was never a key). |
| `src/crypto_trade/features_v3/__init__.py` | NO change — the feature set, ATR dicts, and per-symbol dicts are universe-agnostic; `V3_EXCLUDED_SYMBOLS` does not list ADA. |
| Affected test files | Any test asserting the v3 universe contains `LDOUSDT` is updated to `ADAUSDT`; the feature-count test (`test_v3_feature_count.py`) is **unaffected** — a universe swap does not change the 14-feature set. |

### 3.3 — Single-axis discipline

The brief declares exactly ONE varied axis: the universe symbol set (`LDOUSDT` → `ADAUSDT`). No feature is added or removed (the 14-feature anchor is unchanged). No labeling change. No risk-gate change. No model-architecture change. The /077 conditional-orthogonality instrumentation is carried unchanged (accretive tooling, not a varied axis). The feature-count, ATR-multiplier, and per-symbol-feature dicts are all unchanged. This is a clean single-axis EXPLORATION.

---

## Section 4 — Expected OOS Impact

### 4.1 — Predicted IS / OOS deltas

Anchor: IS +0.8236 / OOS +0.2078 (the re-anchored current-code /060-config baseline).

| Metric | Predicted /078 | Predicted Δ vs anchor | Basis |
|---|---:|---:|---|
| IS monthly Sharpe | +0.95 to +1.15 | **+0.13 to +0.33** | ADA clears LDO by +1.17 IS-Sharpe on the T7 screen; LDO contributes 0.78% of /059 IS PnL (a near-zero IS contributor that ADA's +0.617 IS-edge replaces) |
| OOS monthly Sharpe | −0.05 to +0.35 | **−0.27 to +0.13** | wide band — ADA's OOS behaviour is genuinely unknown to the QR (OOS-blind); the central estimate is roughly flat (LDO's /060 OOS wpnl was −19.72, a drag ADA need only not-worsen) |
| IS n_trades | ~150–200 | ADA trades more than LDO's 11 | ADA's IS data is deep; the under-trading LDO is replaced |
| OOS n_trades | ~95–130 | similar or higher than /060's 102 | ADA replaces LDO's ~12-trade OOS contribution |

The central prediction is an **IS lift of ≈ +0.20** with OOS **roughly flat** (the IS-edge screen is IS-only; ADA's OOS edge is not measured and must not be — Section 10.2). The IS lift band is set by ADA clearing LDO on the screen by +1.17 and LDO being a near-zero IS contributor (/059: LDO 0.78% of IS PnL) — replacing a near-zero contributor with a +0.617-IS-Sharpe symbol should lift the aggregate, but the aggregate IS Sharpe is dominated by BCH (95.76% of /059 IS PnL), so the lift is bounded.

### 4.2 — Falsifier

**The hypothesis is falsified if the /078 IS monthly Sharpe Δ vs the +0.8236 anchor is below +0.10** (the lower edge of the predicted band and the INERT IS noise-band edge). An IS Δ < +0.10 means ADA did not lift the aggregate despite clearing LDO +1.17 on the IS-edge screen — i.e. the screen's coarse single-seed proxy did not transfer to the production 3-seed walk-forward, or BCH IS dominance (95.76%) absorbed the ADA lift entirely. **A second falsifier**: if the /078 OOS monthly Sharpe Δ is below −0.20 (the NEGATIVE OOS floor), the swap traded an IS lift for a material OOS cost — which would mean ADA, unlike the EDA's premise, also carries the regime-split tension. Either falsifier → the universe-revision axis does not advance to the cycle-2 CONFIRMATION as an edge ingredient.

### 4.3 — Behavioral-effect predictor (mandated by `feedback_v3_axis_saturation_predictor.md`)

A universe swap is a **maximal-behavioral-effect** axis — it changes the entire LDO sub-roster. **Prediction**: the /078 roster drops **100% of LDO's trades** (/060: 11 IS + ~12 OOS) and adds ADA's full IS+OOS roster (predicted ≈ 50–90 IS trades and ≈ 25–45 OOS trades, given ADA trades far more actively than the under-trading LDO). The BCH and TRX sub-rosters are predicted **unchanged** — they are independent per-symbol models; a universe swap of the third symbol cannot touch them (the v3 architecture trains one model per symbol).

**Falsifier**: if the BCH or TRX `(symbol, open_time)` IS sub-roster differs from /060's by more than the 3-seed Optuna non-determinism band (a handful of trades), the swap leaked into the non-target symbols — a Phase-6 wiring defect. This axis is NOT saturated (`feedback_v3_axis_saturation_predictor.md`) — it is a maximal-effect axis on the LDO slot; the predicted IS-trade-count change is large and concrete.

### 4.4 — Holding-time-effect predictor + added-vs-removed sub-channel (mandated by `feedback_v3_is_oos_regime_divergence.md` + Critic /076 Rec #2)

A universe swap changes the roster wholesale, so the binding channel is the **added-vs-removed roster-composition mean-duration sub-channel** (Critic /076 Rec #2):

| Channel | Predicted | Falsifier |
|---|---|---|
| Full-roster mean/median trade-duration delta vs /060 | small — bounded by the added-vs-removed gap, predicted ≈ +0.1 to +0.2 candles (the LDO slot is ~1/3 of the roster and the added-vs-removed gap is +0.38) | >+1.0 candle full-roster shift → regime-loading via barrier mechanics |
| **Added (ADA) vs removed (LDO) label-implied mean-duration gap** | **+0.38 candles** (T8 — ADA 6.42 vs LDO 6.04) | added-vs-removed gap > +1.0 candle → the swap loads the regime factor via selection |

The T8 added-vs-removed gap is **+0.38 candles**, comfortably inside the +1.0-candle sub-channel falsifier; the label-implied medians are identical (4.0). The swap is **holding-time-orthogonal** — it does not lengthen effective holding time via barrier mechanics (channel a — /065/071/073) and does not skew the roster toward longer-held trades (channel c — /076). The /076 selection channel cannot operate the way it did at /076 because the swap does not add a feature that re-selects trades within a symbol — it replaces an entire symbol's model with another symbol's model, and ADA's label-implied duration profile is near-identical to LDO's.

### 4.5 — OOS/IS ratio SUSPICIOUS pre-registration (mandated by `feedback_v3_oos_is_ratio_gate.md`)

**Pre-registered SUSPICIOUS gate: if the /078 OOS/IS monthly Sharpe ratio > 3.0, the axis is classified SUSPICIOUS regardless of absolute OOS Sharpe magnitude.** The canonical ratio definition is the within-iteration `comparison.csv` `monthly_sharpe` ratio column.

**Predicted /078 OOS/IS ratio ≈ 0.0 to 0.4** — the central prediction (IS ≈ +1.0, OOS ≈ +0.15) gives a ratio ≈ 0.15, well below 3.0. The ratio gate is **unlikely to fire**: the EDA premise is that LDO is the non-regime-split symbol, so a swap that lifts IS should NOT produce an OOS soar (the regime-divergence signature). The SUSPICIOUS-OOS-DOMINANT sub-mode (IS shift < 0 AND OOS shift ≥ +0.20) is likewise unlikely — the predicted IS shift is positive. **However**, see Section 7: a universe swap is a roster-wholesale change and ADA's OOS behaviour is genuinely OOS-blind, so SUSPICIOUS is NOT mechanically excluded and is floored near the cycle base rate.

---

## Section 5 — Risk Mitigation

iter-v3/078 ships **no strategy-mechanism change** beyond the universe swap — the 14-feature stack, the labeling, the 7-primitive risk-gate stack, and `ENSEMBLE_SEEDS` are all unchanged. The risk surface is the swap itself.

| Risk | Mitigation |
|---|---|
| ADA underperforms in production despite the IS-edge screen | The T7 screen (IS-only walk-forward, +1.17 over LDO) is the IS-calibrated pre-validation gate the /077 diary mandates. The Section 4.2 IS-Δ < +0.10 falsifier is the explicit detector. |
| ADA loads the IS/OOS regime tension (the /075 trap) | T6 establishes LDO is the one non-regime-split symbol; T8 shows the added-vs-removed duration gap is +0.38 (sub-channel falsifier not fired). The Section 4.2 OOS-Δ < −0.20 falsifier catches a regime-tension outcome. |
| ADA over-concentrates the OOS portfolio | Pre-registered: the within-iteration top-symbol concentration is reported; a CONFIRMATION-level >30% concentration gate applies at /081, not at this EXPLORATION (informational here). |
| Trade-rate floor — ADA under-trades like LDO did | T7 shows ADA produced 59 screened IS months (vs LDO's 28) — ADA trades far more actively than the under-trading LDO; the swap should *raise* the trade rate, not lower it. Reported in Phase 6. |
| Phase-6 wiring defect — the swap leaks into BCH/TRX | The Section 4.3 falsifier (BCH/TRX sub-roster bit-stability) is the detector; the QE pre-flight verifies `V3_MODELS`, `ITERATION_LABEL`, and the unchanged `RiskV2Config`. |
| ADA `features_v3` parquet staleness | The QE Phase-6 pre-flight regenerates ADA's `features_v3` parquet from fresh klines (per `feedback_data_staleness_per_worktree.md`); the ADA parquet currently in `data/features_v3/` extends to 2026-05-14 (fresh) but the QE re-fetches and regenerates as the non-negotiable Phase-6 step. |

The risk-gate thresholds are IS-calibrated and unchanged from /060; the simulated historical effect of the gate stack is identical to /060 for the BCH and TRX models, and is freshly computed for the ADA model in Phase 6.

---

## Section 6 — Risk Management Design

The 7-primitive v3 risk-gate stack is **UNCHANGED** at its /060 configuration. No primitive is added, removed, re-scoped, or re-thresholded. The swap changes which symbol the gates apply to (ADA instead of LDO), not the gates themselves.

| # | Primitive | /078 state | Fire-rate prediction |
|---|---|---|---|
| 1 | BTC trend kill | /060 config (`threshold_pct=15.0`) | BCH/TRX identical to /060; ADA freshly evaluated |
| 2 | Vol scaling | /060 config; `vol_scale_floor_per_symbol={"TRXUSDT": 0.5}` (ADA uses the global floor, as LDO did) | BCH/TRX identical; ADA on the global floor |
| 3 | ADX threshold | /060 config (`adx_threshold=20.0`) | BCH/TRX identical; ADA freshly evaluated |
| 4 | Hurst regime | /060 config | BCH/TRX identical; ADA freshly evaluated |
| 5 | Feature z-score OOD | /060 config (`zscore_threshold=2.0`) | BCH/TRX identical; ADA freshly evaluated |
| 6 | Low-vol filter | /060 config | BCH/TRX identical; ADA freshly evaluated |
| 7 | Hit-rate | DISABLED (as /060) | n/a |
| — | Regime-conditional kill switch (primitive 9) | DISABLED (CLOSED axis) | not fired |
| — | BTC-trend position-SIZE de-rate (primitive 12) | DISABLED | not fired |
| — | Per-symbol PnL cap / drawdown brake | DISABLED (CLOSED axes) | not fired |

Regime coverage: identical to /060 for BCH and TRX; the ADA model's gate fire-rates are freshly computed in Phase 6 and reported. The gates fire on ADA exactly as the same-configuration gates fired on LDO — the swap does not alter the gate logic, only the symbol it scores.

---

## Section 7 — Pre-Registered Failure-Mode Prediction

The most plausible failure mode is **INERT-AT-EXPLORATION**: the swap lifts IS modestly but inside the [−0.10, +0.10] noise band, OR the IS lift the T7 screen predicts (+1.17 ADA-over-LDO) does not transfer to the production 3-seed walk-forward because BCH dominates the IS aggregate (95.76% of /059 IS PnL) and absorbs the ADA contribution. A second plausible failure mode is **SUSPICIOUS-OOS-DOMINANT**: although T6 establishes LDO is the one non-regime-split in-universe symbol, ADA is genuinely OOS-blind to the QR — it is possible ADA's OOS window happens to be a strong directional tape, lifting OOS while the IS aggregate moves little, producing an OOS/IS ratio > 3.0. The third failure mode is **NEGATIVE**: ADA's production walk-forward edge is weaker than the screen's coarse proxy suggested, and the swap regresses IS.

In metrics, INERT looks like IS Δ ∈ [−0.10, +0.10] and OOS Δ ∈ [−0.20, +0.20] with a materially changed roster (the LDO sub-roster fully replaced). SUSPICIOUS looks like the OOS/IS ratio > 3.0 or the OOS-dominant sub-mode (IS Δ < 0, OOS Δ ≥ +0.20). NEGATIVE looks like IS Δ < −0.10. The gates that should catch each: the Section 8 disjunctive classifier (SUSPICIOUS ratio gate + sub-mode), the IS/OOS noise bands, and the Section 4.3/4.4 behavioral and holding-time falsifiers (which confirm the swap is a clean roster-wholesale change and not a leaked or regime-loading one).

**SUSPICIOUS probability is floored at the running cycle-2 base rate of ≈ 43%** (3 SUSPICIOUS-OOS-DOMINANT of 7 EXPLORATIONs: /071, /073, /076) per Critic /076 Rec #3. The QR does **not** float SUSPICIOUS below the base rate: a universe swap is not a bit-identical roster (the /077 PASSIVE-DIAGNOSTIC's sub-base-rate justification does not apply here) and ADA's OOS behaviour is genuinely unknown to the QR — there is no conditional-orthogonality *proof* that ADA cannot load the regime factor, only the T6 argument that LDO (the symbol being removed) is the non-regime-split one. T6 is evidence that the *removal* is regime-clean; it is not a proof about the *added* symbol. Honest calibration holds SUSPICIOUS at ≈ 43%. The QR's central estimate is INERT/PROMISING-leaning (the IS-edge screen is strong), but the pre-registered SUSPICIOUS weight respects the cycle base rate per the discipline rule.

---

## Section 8 — Pre-Registered MERGE/NO-MERGE Numerical Criteria (LOCKED)

The /078 classification is the per-brief disjunctive taxonomy, evaluated in this DISJUNCTIVE ORDER (**SUSPICIOUS → NULL-RESULT → NEGATIVE → PROMISING → INERT** — first match is canonical). All thresholds are LOCKED before the backtest. Anchor = the re-anchored current-code /060-config baseline **IS +0.8236 / OOS +0.2078**. "IS shift" / "OOS shift" = /078 minus anchor monthly Sharpe. "OOS/IS ratio" = the within-iteration `comparison.csv` `monthly_sharpe` ratio column.

**8.1 — PROMISING-AT-EXPLORATION**: IS shift ≥ **+0.10** AND OOS shift ≥ **+0.20** AND `frac_positive_paths` ≥ 0.50 AND not SUSPICIOUS.

**8.2 — NEGATIVE-AT-EXPLORATION** (disjunctive OR): IS shift < **−0.10** OR OOS shift < **−0.20**, AND not SUSPICIOUS.

**8.3 — INERT-AT-EXPLORATION**: both shifts within the noise bands (**[−0.10, +0.10]** IS and **[−0.20, +0.20]** OOS), AND not SUSPICIOUS. (A universe swap fully replaces the LDO sub-roster, so the roster is NOT bit-identical to /060 — NULL-RESULT cannot fire; INERT is the in-band outcome.)

**8.4 — SUSPICIOUS** (disjunctive — fires on EITHER ground; SUSPICIOUS takes precedence over NEGATIVE/INERT/NULL-RESULT with no magnitude qualifier):
- **Ratio gate**: OOS/IS monthly Sharpe ratio > **3.0**.
- **SUSPICIOUS-OOS-DOMINANT sub-mode**: IS shift < 0 AND OOS shift ≥ +0.20.

**8.5 — NULL-RESULT**: the /078 trade roster is bit-identical to /060. **Mechanically impossible here** — a universe swap fully replaces the LDO sub-roster with the ADA sub-roster; NULL-RESULT is listed only for taxonomy completeness and cannot fire.

**Evaluation order:** SUSPICIOUS (8.4) → NULL-RESULT (8.5) → NEGATIVE (8.2) → PROMISING (8.1) → INERT (8.3). First match is canonical.

**Disjunctive taxonomy — the five canonical outcomes:**
1. **PROMISING-AT-EXPLORATION** — IS Δ ≥ +0.10 AND OOS Δ ≥ +0.20 AND `frac_positive_paths` ≥ 0.50, not SUSPICIOUS → the universe swap is a candidate edge ingredient for the cycle-2 CONFIRMATION bundle (subject to the CONFIRMATION's multi-seed BOTH-must-improve gate and the "ADA washes at 5-seed" catalog concern).
2. **NEGATIVE-AT-EXPLORATION** — IS Δ < −0.10 OR OOS Δ < −0.20 → the swap regresses; LDO is retained; the universe-revision axis is closed for the cycle and recorded in the catalog.
3. **INERT-AT-EXPLORATION** — both shifts in-band → the swap is roster-changing but performance-neutral; does not advance to the CONFIRMATION; recorded in the catalog.
4. **SUSPICIOUS-OOS-DOMINANT / SUSPICIOUS (ratio gate)** — OOS/IS ratio > 3.0 OR the OOS-dominant sub-mode → regime exposure unmasked, not robust edge; does NOT advance; LDO retained; recorded as a fourth cycle-2 SUSPICIOUS data point.
5. **NULL-RESULT** — bit-identical roster → mechanically impossible for a universe swap (listed for completeness).

**MERGE / NO-MERGE**: This is an EXPLORATION — it does NOT update `BASELINE_V3.md` regardless of classification (only a CONFIRMATION-MERGE updates the baseline). "MERGE" at the EXPLORATION level means the Critic certifies the classification clean and the iteration's data point lands on the branch. A **PROMISING** outcome advances the universe swap (replace LDO with ADA) as a candidate component for the cycle-2 CONFIRMATION (/081); a NEGATIVE/INERT/SUSPICIOUS outcome does NOT advance it, and `LDOUSDT` is retained as the v3 universe symbol. Per `feedback_v3_strict_both_is_oos_baseline.md`, a CONFIRMATION would still require BOTH IS and OOS to improve at multi-seed before any baseline change — a strong-IS-only EXPLORATION result is informational, not a baseline update.

---

## Section 9 — Library Stack Declaration

Unchanged from the /077 stack (pinned in `pyproject.toml` / `uv.lock`):

- lightgbm 4.6.0
- optuna 4.8.0
- numpy 2.2.6
- pandas 3.0.0
- scikit-learn 1.8.0
- scipy 1.17.0
- statsmodels 0.14.6
- pyarrow 23.0.1

No new library is added. The EDA uses only numpy + pandas + scipy + lightgbm (all already in the stack). SHAP is **not** added — the T3/T4 conditional-orthogonality probes use LightGBM gain-importance share as the split-allocation proxy (consistent with the /077 EDA).

---

## Section 10 — QR Audit Trail

### 10.1 — Axis selection provenance (per `feedback_v3_axis_selection_quant_discipline.md`)

- **EDA SHA**: `e48ebad` — `analysis/iteration_v3-078/axis_selection_eda.py` + 11 output CSVs (the nine tables `T0`–`T8` + `T_regime_label` + `axis_selection_summary`). Committed BEFORE this brief.
- **Orchestrator-seeded candidates** (`/077` diary Section 12, non-binding): (1) a bull-month entry-discrimination feature; (2) a re-scoped meta-labeling M2; (3) a universe-revision axis (replace LDO).
- **QR axis decision**: candidate **#3 — universe revision, replace `LDOUSDT` with `ADAUSDT`**. The QR EXHAUSTED candidates #1 and #2 with committed numerical evidence before selecting #3 (the /077 diary makes #3 conditional on #1/#2 being exhausted):
  - **Candidate #1 (a NEW feature) is rejected** — T3 screened two candidate features (`overext_atr_50` raw overextension distance; `momentum_extension_brake_5d` the composed momentum-damping form), built directly from the T2/EDA finding that bull-month losers enter over-extended. Both are **INERT** (rank 12-15/15 across all 3 symbols, mean rank 13.0-14.5/15) and FAIL the engineered-feature falsifier. T4 confirms the rejection is for INERT importance rank, NOT for conditional regime-loading (both candidates' conditional-orthogonality corr — 0.18 / 0.32 — is below the 0.35 ceiling).
  - **Candidate #2 (a re-scoped M2) is rejected** — T5 measured the per-trade winner/loser discrimination AUC of every candidate feature on the /060 IS roster; the maximum |AUC−0.5| is 0.064 (ALL_IS) / 0.066 (BULL months), at the near-zero wall the /071 M2 EDA hit (portfolio mean 0.0577 → /071 SUSPICIOUS). No feature powers an M2.
  - **Candidate #3 (universe revision) is the EDA-supported axis** — T6 establishes the load-bearing structural finding: the bull-month drag is escapability-bounded (IS bull-month losers are OOS bull-month winners — the /075 tension), and LDOUSDT is the one in-universe symbol whose drag is NOT regime-split-correlated (weak in BOTH windows). T7's IS-edge screen selects ADAUSDT as the swap target — ADA clears LDO by +1.17 IS-Sharpe (IS-only walk-forward). T8 confirms the swap is holding-time-orthogonal (added-vs-removed duration gap +0.38 candles).
- **No orchestrator setup commit was made ad-hoc.** The QR EDA backs the axis; this brief is the first setup artifact. The orchestrator's seeded candidate #1 (a NEW feature) was the highest-priority seed; the QR superseded it with candidate #3 on EDA evidence (T3/T5/T6) — this Section 10 records that supersession per `feedback_v3_axis_selection_quant_discipline.md` Rule 4.

### 10.2 — Per-parameter IS-only / a-priori selection-function disclosure (mandated by Critic /075 Rec #2)

Every design parameter is selected by a function whose inputs are demonstrably IS-only or a-priori. The EDA module docstring carries the same disclosure verbatim; it is reproduced here:

| Parameter | Selection function | Input columns | IS-only / a-priori |
|---|---|---|---|
| PARAMETER 1 — the AXIS. AXIS TYPE (universe revision) | `_pick_axis()` — QR a-priori structural call; justified by T3/T5/T6 exhausting candidates #1/#2 | NONE for the type (data-free) | **a-priori (type)** |
| PARAMETER 1 — the SWAP TARGET (ADAUSDT) | argmax of `t7_is_edge_screen()` IS monthly Sharpe | IS-window OHLCV + the 14 anchor features ONLY; the screen's walk-forward loop terminates every test month strictly before `OOS_CUTOFF_MS` | **IS-only** |
| PARAMETER 2 — the BTC monthly regime label (T1/T2/T6) | `build_btc_monthly_regime()` — month tagged BULL if ≥50% bars have `close[t-1] > SMA_270[t-1]` | BTCUSDT 8h `open_time`, `close` ONLY (a calendar/price label, not an OOS performance metric) | **a-priori** |
| PARAMETER 3 — the IS-edge-screen barrier params (ATR 2.0/1.0, timeout 21) + the screen confidence cut (0.45) | a-priori constants — the sacred /059 labeling + an a-priori round-number cut identical for every candidate (so it cannot bias the relative ranking) | NONE | **a-priori (sacred labeling)** |
| PARAMETER 4 — the conditional-orthogonality ceiling (0.35) | a-priori constant `COND_ORTHO_CEILING = 0.35`, reused verbatim from the /077 EDA | NONE | **a-priori** |
| PARAMETER 5 — the EDA per-month training window | a-priori — `training_months = 24`, the SACRED CONSTANT | NONE | **a-priori (sacred)** |

The EDA computes **no** per-candidate OOS counterfactual. The only OOS-window quantities anywhere are (a) the INFORMATIONAL `OOS_all` row of T1 and (b) the OOS bull-SHORT rows of T6 — BOTH clearly labelled informational and feeding NO `sort`, `filter`, `argmax`, or threshold. **T6's OOS rows are the EVIDENCE that the bull-month drag is escapability-bounded — a finding, not a tuning input.** The axis (universe revision) is the QR's structural call; the swap target (ADA) is the T7 IS-edge-screen argmax — an IS-only quantity. The EDA carries a `_grep_no_oos_tuning()` self-audit (an AST scan that flags any OOS-metric token used as a live identifier — a `Name`, `Attribute`, `Subscript` key, or non-docstring string `Constant`); it returns **PASS**. **No design parameter was selected on OOS data.**

### 10.3 — Setup commit SHA

- EDA commit SHA: `e48ebad` (`analysis/iteration_v3-078/` — committed before the brief)
- Brief commit SHA: `7be5323` (this file)
- Setup commit SHA: `0648504` (`run_baseline_v3.py` — `V3_MODELS` `LDOUSDT`→`ADAUSDT`, `ITERATION_LABEL` `"v3-078"`, pre-flight assertions + 5 affected test files)
- Phase 5.5 gate SHA: `<GATE_SHA>`
