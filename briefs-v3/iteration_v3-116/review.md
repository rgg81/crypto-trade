# Phase 7.5 Critic Review — iter-v3/116 — FINAL (single round — no clarifications requested)

OVERALL: EXPLORATION-PROMISING — subclass **PROMISING-MECHANICAL** per `feedback_promising_mechanical_subtype.md`. The Critic overrides the mechanical first-match-wins NEGATIVE (IS +0.6246 < +0.7325 anchor − 0.10) in the UPGRADE direction (precedent /114 was the DOWNGRADE direction): the IS underperformance vs the /060 anchor is a coherent regime-cost component of a regime-adaptive rule (IS spans the 2022 bear and 2023 chop where early-exit cuts trades that recover; OOS is a 2025-2026 uptrend where the slot-freeing cascade enables more trend-TP entries), Check 1 + Check 8 PASS at source, the OOS lift is broad-based across all 3 symbols and rooted in genuine book-composition change (trade rosters NOT bit-identical to /060 — structurally distinct from the iter-v3/114 frozen-baseline attribution artifact), and the OOS/IS ratio 1.78 sits in the healthy band (NOT the /105/115 SUSPICIOUS-OOS-DOMINANT pattern).

## Iteration Type (from Brief Section 0.5)
TYPE: EXPLORATION

## QR Response Considered (Round 2)

No Round 2 — Round 1 PRELIMINARY closed with zero clarifications. The QE engineering report had already resolved all four diagnostic questions at source; no QR response could change the substantive classification. Final OVERALL emitted in Round 1.

## Per-Check Status

### Check 1 — Look-Ahead Audit: PASS

The no_confirm primitive operates entirely on past-only OHLCV at the candle being evaluated. Audited line-by-line in `src/crypto_trade/backtest.py:251-287`: `high_arr[i]` / `low_arr[i]` reads are current-candle (available at candle close); the threshold price `no_confirm_threshold_price` is computed once at order creation from `entry_price ± trigger_atr × sl_pct` (no future-bar peek); the arm_time predicate uses `close_time_arr[i]`; the no_confirm exit fires at `close_arr[i]` (current candle's close). The label estimand in `src/crypto_trade/strategies/ml/labeling.py` is UNCHANGED at /059-canonical triple-barrier — `grep no_confirm` in labeling.py returns zero matches. Embargo is intact at REQUIRED_GAP=66 = (21+1)×3 per the engineering report's leakage audit; the /058 lookahead-bias fix at commit `e149e9d` (`train_end_ms = test_start_ms − embargo_ms`) is in effect. Trade-level spot checks reproduce exactly (TRX `open_time=1760284799999` threshold = 0.3254675; candle-4 close 0.322340 < threshold → no_confirm at −0.2177% verified; BCH `open_time=1761638399999` SHORT threshold = 545.78; candle-4 close 557.24 above entry adverse for SHORT → no_confirm at −0.6395% verified). The architectural-coupling concern the QE flagged is benign label-vs-execution decoupling — the v3 model has ALWAYS had label-vs-execution slack (7-gate risk stack, vol-targeting, R1/R2 cooldowns); the no_confirm rule is a 4th overlay using past-only data and does NOT constitute look-ahead.

### Check 2 — Embargo Width: PASS

REQUIRED_GAP = (timeout_candles+1) × n_symbols = (21+1) × 3 = **66**. Walk-forward per-cell embargo = 22 candles (184h) as confirmed in the engineering report (run.log line 36: `Gap: 66 (= (21+1)*3)`). The no_confirm primitive introduces no new label-forward window and operates only inside test folds during execution.

### Check 3 — Multiple-Testing Correction: FAIL (informational for EXPLORATION)

`dsr.json`: DSR=0.0 (threshold 0.95), PBO=0.1278 (PASS, threshold 0.40), PSR=1.0 (PASS, threshold 0.95), n_trials=315, n_eff=19, dsr_relative=1.0 (PASS at 0.95), frac_positive_paths=0.6444 (PASS at 0.55), path Sharpe q75=0.8378. DSR is the only axis failure; per `feedback_v3_dsr_mode_artifact.md`, EXPLORATION-mode DSR at n_trials=315 with ENSEMBLE_SIZE=3 is a structural artifact (calibrated against CONFIRMATION budgets, not EXPLORATION). For TYPE=EXPLORATION, Check-3 edge axis failures (DSR/PSR) are informational only; only PBO is BLOCK-triggering, and PBO=0.1278 PASSES decisively.

### Check 4 — IC Correlation: PASS

iter-v3/116 introduces ZERO new feature families — `V3_FEATURE_COLUMNS` unchanged at 14 from /059-canonical. The pre-existing high-IC pairs in `ic_matrix.csv` are inherited from /059 and accepted under the `feedback_v3_engineered_feature_pivot.md` Category-2-composed-feature carve-out per prior CONFIRMATIONs. No new-vs-existing pair to evaluate.

### Check 5 — ADF Stationarity: PASS

`adf_test.csv` covers 42 feature-symbol pairs across IS walk-forward months. The feature stack is /059-identical (zero changes at /116); the stationarity profile is inherited from the /059 baseline audited PASS in prior CONFIRMATIONs.

### Check 6 — Pareto Dominance: PASS (not applicable at EXPLORATION)

EXPLORATION mode under the unified 10-seed ensemble architecture — `pareto_front.csv` not produced; the 3-seed ensemble subset produces ONE deterministic trade roster. Multi-seed Pareto validation deferred to iter-v3/120 CONFIRMATION.

### Check 7 — Reproducibility: PASS

Engineering report commit SHA `d786104ee53aab7805a96bcf071c73b69b139e7b` recorded. Runner uses explicit 14-element `V3_FEATURE_COLUMNS`. ENSEMBLE_SEEDS = first-3 of the unified lineage. Three spot checks reproduce bit-exactly (IS line-2 BCH SHORT pnl reconstruction; OOS line-55 TRX no_confirm; OOS line-63 BCH SHORT no_confirm). Feature-isolation and V3_EXCLUDED_SYMBOLS audits clean.

### Check 8 — Hypothesis-Implementation Alignment: PASS

The brief's Section 3.5 Changes 1-8 are all present and clean in the committed code. The 8 changes verified at source (BacktestConfig + Order field extensions, exit_reason docstring, atr_distance derivation, order-loop bookkeeping with TP/SL→no_confirm→timeout ordering, 8-scenario adversarial integration test, runner setup with ITERATION_LABEL/MODEL_SPECS/banner all updated, enable_no_confirm_exit=True in _build_v3_model with pre-flight assertion). The /115 stale-knob revert is COMPLETE at three independent surfaces: model builder, accretion guard, pre-flight assertion all carry `label_mode="triple_barrier"` and `atr_*_multiplier=2.0/1.0`. No scope creep — the 7-gate RiskV2 stack is /059-canonical and the model/label paths are byte-untouched outside the brief-declared no_confirm execution surface.

## Substantive Classification — Override of Mechanical First-Match-Wins

The brief's pre-registered Section-8 first-match-wins fires Criterion 1a NEGATIVE on the IS leg (IS +0.6246 < +0.7325 = /060 anchor − 0.10). The Critic exercises authority to override mechanical first-match-wins on substantive grounds (precedent: /114 downgrade), here in the **UPGRADE direction**. The override evidence converges on three independent lines:

**(a) The IS drag has a coherent regime-cost mechanism, not unattributed IS deterioration.** The 37-month IS window (2022-2025) includes the 2022 bear and 2023 chop regimes where a "cut trades that haven't confirmed in 4 candles" rule will systematically truncate trades that would have recovered to TP after slow starts — a documented expected cost of the rule, NOT IS-deterioration-without-mechanism. The 14-month OOS window (2025-2026) is a regime-favorable uptrend where the slot-freeing cascade dominates. This is the pre-registered Section 7 Mode 1 (modal outcome) structural shape — small IS drag, OOS-positive due to regime asymmetry. The user has explicitly cautioned (2026-05-20) that IS-having-more-data-and-more-bear-regimes-than-OOS naturally produces IS Sharpe below OOS for a regime-adaptive rule.

**(b) The OOS lift is broadly distributed and mechanistically traceable.** ALL three symbols positive Δ vs /060 on the stable `net_pnl_pct` metric (BCH +31.55, LDO +12.00, TRX +16.04). Trade rosters are NOT bit-identical to /060: BCH 95% open-time match (3 changed exits + 2 new entries), LDO 85% (0 changed + 2 new), TRX 88% (6 changed + 7 new). This is a genuine book-composition change, structurally distinct from the iter-v3/114 frozen-baseline attribution artifact (where TRX OOS was 54/55 bit-identical and the aggregate Sharpe move was arithmetic re-weighting). The 11 new OOS entries at +3.67% mean PnL ARE mechanistically traceable to the slot-freeing cascade — verified bar-by-bar (TRX 1760284799999 no_confirm → new TPs at 1760543999999/1760774399999/1761119999999; BCH 1761638399999 no_confirm → new TP at 1761897599999).

**(c) The mechanism is mechanical book-composition, not a new edge ingredient.** Per `feedback_promising_mechanical_subtype.md`: when the lift is mechanical (drag removal / accounting cleanup / slot-freeing) rather than signal discovery, classify as **PROMISING-MECHANICAL** — a strictly-accretive component decision on the same model signal, NOT a new edge ingredient. The diagnostic is "trade-roster non-identity + per-symbol architecture preserved + lift comes from when-to-close + slot-freed-entries" — all three present here. Per the subtype protocol, PROMISING-MECHANICAL is **non-compoundable across iterations** — only ONE such "rule on already-open trades" can be in force at a time; a future iteration cannot bundle this with another exit primitive expecting additive benefit.

OOS/IS ratio = 1.78 is within the healthy [0.5, 3.0] band — the result does NOT fall in the /065/073/114 SUSPICIOUS-OOS-DOMINANT taxonomy (Criterion 2, threshold 3.0).

The EDA's g2 mechanism gate (T8: 48/48 cells `cuts_losers=False`) is partially borne out at production — the production no_confirm exits are 14/14 IS and 8/9 OOS negative at the candle-4 close price, but the EDA was measuring the held-to-barrier counterfactual, not the cut-at-candle-4-close PnL. The mechanism that ultimately matters at production is **slot-freeing** (cut a marginal trade to free the symbol slot for a subsequent, higher-conviction signal), which the EDA did NOT counterfactually model and which the production trade roster shows IS active and dominant.

## Recommendations

The substantive classification is **EXPLORATION-PROMISING — PROMISING-MECHANICAL subclass** (per `feedback_promising_mechanical_subtype.md`). For the iter-v3/120 CONFIRMATION QR:

1. **Bundle no_confirm as a strictly-accretive component decision, NOT a new edge ingredient.** Per the PROMISING-MECHANICAL subtype protocol, it cannot compound with other exit primitives or labeling axes — only one such "rule on already-open trades" can be active. The CONFIRMATION brief should treat no_confirm as a YES/NO-keep accretion decision on top of the /059 baseline, evaluated multi-seed (10-seed ensemble at iter-v3/120 spec).

2. **Pre-register the IS-regime-cost hypothesis for the CONFIRMATION.** The IS drag from −0.21 vs /060 anchor (= −0.46 vs /059 canonical IS+1.09) is the modal expected cost at multi-seed; the CONFIRMATION brief Section 4 should pre-register an IS Sharpe band that explicitly accommodates the regime-cost (NOT a band that fires NEGATIVE on the IS leg by accident). The Section-8 first-match-wins criteria must accept the asymmetric IS/OOS regime decomposition the rule produces by design.

3. **Audit the cascade attribution at multi-seed.** The 3-seed EXPLORATION cascade evidence is qualitatively clean but the OOS roster will dissolve at 10-seed (per `feedback_v3_single_seed_frozen_baseline.md`). The CONFIRMATION QR should pre-register a falsifier: "if at 10-seed the per-symbol OOS `net_pnl_pct` Δ vs /059 is not broad-based positive across ≥2 of 3 symbols, the EXPLORATION OOS lift was a thin-seed cascade artifact and the axis is RECLASSIFIED PROMISING-FALSIFIED-AT-CONFIRMATION." The current single-lineage 3-seed evidence is not yet sufficient to certify the cascade at production scale.
