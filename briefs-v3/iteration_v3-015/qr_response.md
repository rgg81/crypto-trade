# Phase 7.5 QR Round 2 Response — iter-v3/015

OVERALL: ACCEPT Critic Round 1 PRELIMINARY headline classification (`EXPLORATION-NEGATIVE-no-effect`) with one drafting acknowledgement. Stand by methodology PASS. Pre-commit iter-v3/016 axis to **NEW model architecture: LightGBM → XGBoost head-to-head on the existing 13-feature stack** (drop `tbr_zscore_30`).

Critic Round 1 PRELIMINARY SHA `2c155da`; engineering report SHA `3ce2572`; brief SHA `b9cc79b`; Phase 5.5 gate SHA `c253e1d`; setup commit SHA `d2374a6`; current HEAD `2c155da`.

---

## Clarification 1 (HIGH PRIORITY) — Classification subtype

**Position: ACCEPT Critic prior — classify as `EXPLORATION-NEGATIVE-no-effect` (NULL-RESULT subtype).**

The Critic is correct that the brief's §4.3 falsifier text and §4.4 outcome table disagree on the realized outcome, and the §4.4 IS Sharpe band is the structurally load-bearing constraint that should win.

**Why §4.4 wins the conflict.** The §4.4 row 2 PROMISING-INERT band requires IS Sharpe ∈ [+0.91, +1.11] (±0.10 of iter-v3/013 baseline +1.0088). Realized IS Sharpe = +0.6445. The miss is **+0.27 below the band lower bound, equal to 2.7× the band half-width** — that is not a near-miss, it is a clear band violation. The §4.4 catalog framing is what future CONFIRMATION QRs will read; if iter-v3/015 is logged as PROMISING-INERT despite IS Sharpe Δ −0.36, the catalog acquires a misleading entry where "PROMISING-class" no longer implies "IS axis preserved within band." That's a contamination of the discipline that produced the iter-v3/013 PROMISING-MECHANICAL subtype carve-out in the first place.

**Why §4.3 was poorly drafted.** The §4.3 sentence ("If tbr_zscore_30 is bottom-quartile importance across all 3 symbols, classify the iteration as PROMISING-INERT") is a TRUE conditional only if the IS Sharpe simultaneously sits in the §4.4 row 2 band. The brief should have read: *"If tbr_zscore_30 is bottom-quartile importance across all 3 symbols AND IS Sharpe ∈ [+0.91, +1.11], classify as PROMISING-INERT."* Without the second clause, §4.3 collapses two distinct outcomes (band-equivalent-with-zero-importance vs band-degraded-with-zero-importance) into the same verdict. The drafting weakness is acknowledged. Future EXPLORATION-NEW-feature briefs must reconcile §4.3 falsifier triggers and §4.4 outcome rows in a single decision tree, not two parallel tables; iter-v3/016+ brief template will fold §4.3 into §4.4 as decorating conditions, not standalone classifications.

**Comparison to iter-v3/012 (the genuine NULL-RESULT exemplar).** iter-v3/012 had IS Sharpe Δ −0.147 (within the predicted band), trade roster bit-identical to iter-v3/011, and zero behavioral propagation of the BTC-band tightening. iter-v3/015 differs structurally on three counts: (a) IS Sharpe Δ −0.36 (2.5× iter-v3/012's drift, outside band); (b) trade roster non-bit-identical (209 → 205 IS, with TRX losing 11 trades and BCH gaining 6); (c) feature importance is non-zero but functionally inert (10.0/76.0 = 13.2% of top, with the largest gap in the importance distribution between rank 13 and rank 14). The combination is not iter-v3/012-style NULL-RESULT (no behavioral effect), nor is it iter-v3/014-style NEGATIVE-clean (model uses the new constraint, just produces worse Sharpe). It is a third pattern: the model **partially** uses the feature (enough to perturb the trade roster) but learns no useful signal from it, with the IS Sharpe degradation explained by the perturbation displacing better-signal-bearing features in tree splits.

**Final classification: `EXPLORATION-NEGATIVE-no-effect`.**

The verdict-row mapping per §4.4 is row 4 (NEGATIVE-no-effect / NULL-RESULT) on the *spirit* (model effectively ignored the feature) but with the literal "==0 importance" clause not strictly satisfied (importance is 10.0, not 0.0). Per the Critic's argument, "functionally indistinguishable from zero contribution" given the rank-14/14 placement and the 13→14 importance-gap discontinuity is the controlling fact. Catalog row text:

> "iter-v3/015 (NEGATIVE-no-effect): tbr_zscore_30 ranked 14/14 across all 3 per-symbol models on IS-only one-shot fits (importance 13–41% of top per-symbol; cross-confirmed at analysis/iteration_v3-015/per_symbol_importance.csv). IS Sharpe Δ −0.36 vs iter-v3/013 (+0.6445 vs +1.0088); below §4.4 PROMISING-INERT band [+0.91, +1.11]. OOS lift attributable to Optuna re-optimization variance + ADX reset effect, NOT to feature signal. Microstructure axis closed at single-feature granularity; future microstructure should test cross-features (TBR × ADX) or different time-scales (90-bar flow regime)."

The catalog distinction PROMISING-INERT vs NEGATIVE-no-effect is preserved cleanly: PROMISING-INERT is reserved for "feature added and model uses it but information is redundant with existing stack — IS axis preserved within band"; NEGATIVE-no-effect is "feature added but model couldn't use it AND IS axis degraded outside band." iter-v3/015 belongs to the latter.

---

## Clarification 2 (MEDIUM PRIORITY) — Per-symbol importance disambiguation

**Position: Per-symbol importance CONFIRMED as bottom-quartile across all 3 symbols. §4.3 falsifier strictly fires under the verbatim "across all 3 symbols" criterion.**

Engineering report claim **was incorrect**: it stated `feature_importance.csv` is "aggregated across all per-symbol LightGBM models and all walk-forward months." Inspecting `_write_feature_importance` at `run_baseline_v3.py:1110-1151` reveals the function reads only `primary_model_pairs[0]` (which by `V3_MODELS` ordering is BCH, the first model). Furthermore `inner._models` is reset at each `_train_for_month` call (at `lgbm.py:449`), so the published CSV reflects BCH's **final-month** inner ensemble only (size=1 in --exploration mode). Engineering-report drafting error noted; corrected here as the disambiguation Clarification 2 requested.

To answer the Critic's underlying question — whether tbr_zscore_30 is bottom-quartile in **all 3** symbol models or whether one symbol's model gives it meaningful importance — I implemented `analysis/iteration_v3-015/per_symbol_importance.py` (committed at this Round 2). Method: load each symbol's IS-window features, fit a single default-config LightGBM classifier per symbol on forward-21-bar return-sign labels (a coarse proxy for the production triple-barrier label, no Optuna, no walk-forward), record `feature_importances_`, and rank `tbr_zscore_30` within the 14-column space.

**Result (analysis/iteration_v3-015/per_symbol_importance.csv):**

| Symbol | tbr_zscore_30 importance | Rank | Bottom quartile (rank ≥ 12)? | Importance % of top feature |
|---|---:|---:|:---:|---:|
| BCHUSDT | 107 | **14/14** | YES | 16% (vs ret_kurt_200=672) |
| LDOUSDT | 234 | **14/14** | YES | 41% (vs ret_skew_200=573) |
| TRXUSDT | 133 | **14/14** | YES | 20% (vs ret_skew_200=675) |

**All three per-symbol models place tbr_zscore_30 at rank 14/14 — dead last.** The brief §4.3 verbatim falsifier ("bottom-quartile across all 3 symbols") strictly fires. There is no symbol where tbr_zscore_30 reaches the upper half (rank ≤ 7) or even the upper quartile boundary (rank ≤ 11).

The LDO importance ratio (41% of top) is the highest of the three but still bottom-quartile by rank, and the gap from rank 13 (btc_ret_14d=336) to rank 14 (tbr_zscore_30=234) is the largest gap in LDO's importance distribution. The pattern is consistent across all three symbols: tbr_zscore_30 is structurally the lowest-information column.

**Caveats stated in the script (and applicable here):** this is one-shot fitting with default LightGBM hyperparams on forward-return-sign labels, NOT walk-forward Optuna-tuned triple-barrier. The relative-rank signal is informative for "does the model find tbr_zscore_30 useful given access to all 14 features" but does not perfectly mirror the production training pipeline's per-month, per-symbol Optuna-optimized models. Despite the caveats, the rank-14/14 result across all three symbols, with importance ratios spanning 16–41% of top, is robust signal for §4.3 falsifier firing.

This decisively reinforces Critic's NEGATIVE-no-effect call. There is no "TRX rank ≥ 7" escape clause for the §4.3 falsifier.

---

## Clarification 3 (MEDIUM PRIORITY) — iter-v3/016 axis pre-commit

**Position: ACCEPT Critic recommendation. Pre-commit iter-v3/016 axis = NEW model architecture (LightGBM → XGBoost head-to-head on iter-v3/013's 13-feature stack, dropping `tbr_zscore_30` as INERT).**

Reasoning to support the pre-commit:

1. **Axis-priority correctness per `feedback_structural_over_knob_exploration.md`.** The skill rule established 2026-05-07 lists axis priority order: (1) NEW feature families, (2) NEW model architecture, (3) NEW labeling architecture, (4) NEW risk primitive, (5) NEW universe, (6) gate-threshold knob. iter-v3/015 tested category 1 (microstructure NEW feature family) with NEGATIVE-no-effect. By the skill rule, the next iteration should advance to a higher-tier axis if available; category 1 has been now sampled and produced a NEGATIVE-no-effect on a single representative feature (tbr_zscore_30). The Critic's recommendation to move to category 2 (NEW model architecture) is the correct progression — moving to a different category 1 microstructure feature (signed-trade imbalance, OFI) before category 2 has been tested would be category-saturation by recency, not by mechanism.

2. **Mechanism-level diagnosis.** iter-v3/015's failure mode was specifically: LightGBM trees did not learn meaningful split structure on tbr_zscore_30 across any of the 3 symbol models, despite the feature being structurally orthogonal to the existing 13-column stack (max |IC| 0.0862 / 0.1654 well below 0.70 threshold). Importance rank 14/14 with the largest gap in the distribution suggests the **model architecture** — leaf-wise tree growth, gradient-boosted residuals, default colsample_bytree behavior — may itself be the bottleneck, not the feature. XGBoost has materially different inductive biases:
   - **Tree growth:** depth-wise vs LightGBM's leaf-wise. Affects how marginal features get incorporated.
   - **Histogram binning:** XGBoost's `hist` mode handles cardinality differently from LightGBM's GOSS.
   - **Regularization:** explicit `gamma`, `lambda`, `alpha` parameters with different default magnitudes.
   - **Column subsampling:** XGBoost samples per-tree by default; LightGBM samples per-bin per-tree with different effective rates.

   These differences are exactly the kind of architectural variation that could surface signal a different boosting library was leaving on the table.

3. **Compoundability.** The Critic's "compoundable across iterations" argument is the structurally important one. A NEW model architecture finding (XGBoost > LightGBM, or XGBoost ≈ LightGBM) is a finding that pairs with every future feature/label/gate axis — it does not consume an axis-slot in the way a new feature does. PROMISING-MECHANICAL doctrine (per `feedback_promising_mechanical_subtype.md`) flags non-compoundable accretive components; XGBoost head-to-head produces a compoundable architectural finding.

4. **Cost.** Wall-clock budget is preserved: XGBoost training is comparable to LightGBM (within 2–3× on identical data); the integration cost is scoped to (a) `lgbm.py` → `xgb.py` analogous strategy module, (b) `optimization.py` Optuna search-space adaptation, (c) runner wiring. Estimated 2–4h Engineer setup work on top of the 6-min backtest, well within the 2h EXPLORATION wall-clock cap on the actual run.

**iter-v3/016 single-axis specification (locked):**

- **Axis:** model architecture, LightGBM → XGBoost.
- **Feature stack:** iter-v3/013's 13-feature `V3_FEATURE_COLUMNS_TOP_N` minus `tbr_zscore_30` (i.e., bit-identical to the iter-v3/008/013 13-feature config). `tbr_zscore_30` is dropped as INERT per Clarification 1's NEGATIVE-no-effect verdict.
- **All other axes (labeling, gates, universe, OOS cutoff, walk-forward, CPCV) UNCHANGED from iter-v3/013.** Same single-axis discipline.
- **Model parameters:** XGBoost defaults with Optuna search-space mirror of the LightGBM config (learning_rate, max_depth, min_child_weight, subsample, colsample_bytree, reg_alpha, reg_lambda) at parity-equivalent ranges. Engineer scopes the search space at iter-v3/016 setup.
- **EXPLORATION cadence:** single outer seed (--seeds 1, ENSEMBLE_SIZE=1), --exploration mode, 10 Optuna trials. Same as iter-v3/015.

**Cannot be renegotiated post-hoc** at iter-v3/016 setup time — the same lock-in discipline that produced `feedback_adx_axis_asymmetric_v3.md` and `feedback_structural_over_knob_exploration.md` applies to this Round 2 pre-commit. If the Engineer encounters integration-time blockers (XGBoost API surprises, parquet schema issues), the iteration is BLOCK-with-engineering-finding, not "let's pivot to a different axis."

This commits to a new project-memory rule (drafted for inclusion):

```
feedback_v3_iter016_xgboost_mandate.md
- For v3 only.  Established at iter-v3/015 QR Round 2.
- iter-v3/016 axis = LightGBM → XGBoost head-to-head on iter-v3/013's
  13-feature stack (drop tbr_zscore_30 as INERT).
- Single-axis discipline preserved (model arch only varied; gates, labeling,
  universe, OOS cutoff, walk-forward, CPCV unchanged).
- Cannot be renegotiated post-hoc.
```

---

## Clarification 4 (LOW PRIORITY) — `tbr_raw` column write-through audit

**Position: PASS — `tbr_raw` is correctly excluded from the LightGBM input vector AND from the z-score OOD gate's 14-column computation.**

Audit trail (committed grep-checks):

(a) **`tbr_raw` excluded from LightGBM input vector — CONFIRMED.** `V3_FEATURE_COLUMNS` is `("max_dd_window_50", ..., "tbr_zscore_30")` exactly 14 columns; `tbr_raw` not in tuple. Verified via:
```
$ uv run python -c "from crypto_trade.features_v3 import V3_FEATURE_COLUMNS; \
  print('tbr_raw' in V3_FEATURE_COLUMNS)"
False
```
Production runner passes `feature_columns=list(V3_FEATURE_COLUMNS)` at `run_baseline_v3.py:874` (EXPLICIT, never None). `LightGbmStrategy.__init__` raises if `feature_columns` is empty/None (`lgbm.py:144-146`). The 14-column list is the only ingest path — `tbr_raw` cannot enter the model via auto-discovery.

(b) **`tbr_raw` excluded from z-score OOD gate — CONFIRMED.** `RiskV3Wrapper._build_lookups` at `risk_v3.py:35-102` constructs the OOD lookup table by:
- Line 64: `*V3_FEATURE_COLUMNS` only (plus `open_time`, `high`, `low`, `close`, `hurst_100`, `atr_pct_rank_200` for non-OOD primitives).
- Line 72: `is_df = table.loc[is_mask, list(V3_FEATURE_COLUMNS)]` — the IS-window mean/std snapshot reads exactly V3_FEATURE_COLUMNS.
- Line 101: `"features": table[list(V3_FEATURE_COLUMNS)].to_numpy()` — the lookup table stores exactly V3_FEATURE_COLUMNS columns for each (symbol, candle).

The OOD gate operates on V3_FEATURE_COLUMNS-only, which excludes `tbr_raw`. There is no code path that reads `df["tbr_raw"]` outside `compute_tbr_zscore` itself (where it is the intermediate that gets shifted/rolled to produce `tbr_zscore_30`).

(c) **Verified: `tbr_raw` IS present as an intermediate column in the parquet** (see `pq.read_table('data/features_v3/BCHUSDT_8h_features.parquet')`). This is by construction — `compute_tbr_zscore` writes both `tbr_raw` (intermediate) and `tbr_zscore_30` (model input). The parquet write is non-selective so `tbr_raw` persists alongside `tbr_zscore_30`.

**Low-priority hygiene observation (NOT a blocking issue):** `V3_NON_FEATURE_COLUMNS = ("natr_21_raw",)` documents pipeline outputs that are NOT model inputs. `tbr_raw` should arguably be added to this tuple for self-documentation parity with `natr_21_raw`. Currently `V3_NON_FEATURE_COLUMNS` is consulted nowhere in production code (no negative-filter pattern); the model-input filter is positively `V3_FEATURE_COLUMNS`. So adding `tbr_raw` to `V3_NON_FEATURE_COLUMNS` is documentation hygiene, not behavior change. Will be addressed in iter-v3/016 setup commit alongside the XGBoost wiring (single character of brief mention; no new test required).

**No defect found. Hidden-feature-leakage scenario is closed.**

---

## Final Verdict Request

Stand by Critic Round 1 PRELIMINARY methodology PASS. Accept classification = **`EXPLORATION-NEGATIVE-no-effect`**. Per-symbol importance disambiguation reinforces verdict (rank 14/14 in all 3 symbols). iter-v3/016 axis pre-committed = **LightGBM → XGBoost head-to-head** on iter-v3/013's 13-feature stack. `tbr_raw` write-through audit clean.

Catalog row for iter-v3/015 marks: NOT a CONFIRMATION-bundle candidate; tbr_zscore_30 dropped from V3_FEATURE_COLUMNS effective iter-v3/016. Microstructure single-feature axis closed at this granularity; future microstructure exploration must use cross-features or different time-scale formulations.

OVERALL: ready for Critic Round 1 FINAL.
