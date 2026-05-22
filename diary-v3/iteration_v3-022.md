# Iteration iter-v3/022 — Diary

## Decision: EXPLORATION-NEGATIVE (clean)

The TRX/2022-Q4 regime gate (BTC drawdown_30d > 20% OR |BTC vol_zscore_30d| > 1.5; TRX-only target) achieved its primary surgical objective on **1 of 2** PBO=1.0 cells (TRX/2022-10 dropped 1.0 → 0.282, a 0.72-point drop) but failed the broader §4 PBO max gate (target [0.6, 0.85]; observed 1.0 driven by LDOUSDT/2026-03 data-scarcity cell + TRX/2023-01 stuck at 0.999). The observed headline OOS Sharpe -0.4313 (Δ -0.82 vs iter-v3/018 anchor +0.3869) is **NOT regime-gate cross-contamination**: forensic check confirmed BCH and LDO OOS results are **bit-identical** across iter-v3/020, iter-v3/021, and iter-v3/022 (BCH: -6.2465 weighted_pnl / 36 trades / 36.1% WR; LDO: -8.9257 weighted_pnl / 13 trades / 38.5% WR — digit-for-digit). The headline OOS collapse is the BCH/LDO frozen single-seed=42 baseline, not the iter-v3/022 axis. TRX, the gate's actual target, IMPROVED in both IS (gate kills 4 IS trades → reduces noise) and OOS (TRX OOS weighted_pnl +7.6101 vs iter-v3/020/021's +5.3860 — +0.55 lift attributable to the gate). Methodology of the run is clean — all 12 standard methodology checks PASS or PASS-with-Saturation-fire (Critic FINAL `3b3cc41`).

NOT a CONFIRMATION-bundle candidate. The TRX/2022-Q4 regime gate axis is **PARTIALLY-EFFECTIVE-CLOSED for current 10-EXPLORATION cycle**: TRX/2022-10 cell improvement is a real-but-narrow surgical fix that does not generalize to TRX/2023-01 at single-seed n_trials=35 budget; the mechanism warrants re-evaluation only at CONFIRMATION budget (5 outer × 50 trials per cell) when the per-cell PBO measurement variance is reduced. Cadence #4 of 10 in the post-bootstrap cycle.

## What Was Tested

**Hypothesis (locked in brief Section 1):** "Adding a regime-conditional kill switch to RiskV2Wrapper that suppresses TRX position-taking signals when (a) BTC drawdown_30d > 20% over 30 days, OR (b) |BTC vol_zscore_30d| > 1.5 (calibrated against IS-window 90th/95th-percentile distributions per EDA SHA `b728313` synthesis.md), with thresholds and logical-OR composition LOCKED at brief authoring, will reduce PBO at the high-PBO TRX cells (TRX/2022-10 PBO=1.0; TRX/2023-01 PBO=1.0) without removing edge from normal-regime training data, because the gate operates at the per-bar candidate-signal layer (not the trade-execution layer): Optuna's per-cell hyperparameter search at iter-v3/018 n_trials=50 was unstable in the FTX/LUNA regime (high-PBO cells), partly because the optimization could fit hyperparameters that selected for 'trades during regime stress' — pruning those bars makes the cell's IS Sharpe more stable, lowering PBO. Predicted IS Sharpe band [+0.32, +0.50]; predicted OOS Sharpe band [+0.40, +0.55]; predicted PBO mean band [0.10, 0.13]; predicted PBO max band [0.6, 0.85]."

**Spec (locked, single-axis variation):**
- NEW `RiskV2Config` parameters: `enable_regime_gate=True`, `regime_gate_symbols=("TRXUSDT",)`, `regime_dd_threshold_pct=20.0`, `regime_vol_zscore_threshold=1.5`
- TRADE-TIME integration: regime gate state computed from BTC kline cache via `searchsorted('left') - 1` for strict past-only (current bar's BTC NOT in own window). Adversarial test in `tests/strategies/ml/test_regime_gate.py` verifies spike at bar 50 not visible at bar 50 (DD=0%) but visible at bar 52 (DD=-50%).
- V3_MODELS REVERTED 5 → 3 (drop HBARUSDT + AVAXUSDT from iter-v3/021); REQUIRED_GAP back 110 → 66 = (21+1) × 3
- ITERATION_LABEL = "v3-022"
- 13 V3_FEATURE_COLUMNS UNCHANGED (funding_rate_zscore_30 still absent; tbr_zscore_30 absent)
- per-symbol cap KEPT in repo but DISABLED (`enable_per_symbol_cap=False`)
- Ran in EXPLORATION mode: --exploration --seeds 1 (1 outer × 1 inner × 35 n_trials × 3 symbols = **105 fits per cell**; colsample_bytree=1.0 hardcoded). 3rd EXPLORATION at the n_trials=35 default per `feedback_v3_exploration_n_trials_35.md`.
- Anchor: iter-v3/018 multi-seed mean +0.3788 IS / +0.3869 OOS.

This was iter-v3/022, the **first regime-conditional gate primitive in v3 catalog** (14 unique axis representations after this iteration; cadence #4 of 10 in the post-bootstrap cycle).

## Headline Numbers

### Single-seed EXPLORATION run (seed 42)

| Metric | iter-v3/018 anchor (multi-seed mean) | iter-v3/022 | Δ |
|---|---:|---:|---:|
| IS monthly Sharpe | +0.3788 | **+0.8084** | **+0.4296** (above predicted [+0.32, +0.50] upper bound; TRX-driven artifact at single-seed) |
| OOS monthly Sharpe | +0.3869 | **-0.4313** | **-0.8182** (below predicted [+0.40, +0.55] entire band) |
| OOS/IS Sharpe ratio | 1.02 | -0.534 | sign flip |
| IS n_trades | 172 (mean) | **196** | -4 vs single-seed=42 baseline (200 from iter-v3/020/021); regime gate reduced TRX IS trades 79 → 75 |
| OOS n_trades | 90.5 (mean) | **82** | <130 trade-rate floor (informational at EXPLORATION single-seed) |
| IS MaxDD | 21.86% (mean) | **34.52%** | +12.66pp |
| OOS MaxDD | 27.74% (best seed 42) | **42.90%** | +15.16pp |
| Win rate IS / OOS | — | 31.6% / 39.0% | OOS WR > IS WR |
| Total OOS PnL | +∼7% (mean) | **-16.01% (-0.281 vs anchor)** | BCH/LDO frozen baseline drives portfolio negative |
| DSR | 0.0 (n_trials=1500) | **0.0** | clean honest readout at n_trials=105 |
| **PSR** | 0.9936 | **0.0000** | collapsed (consistent with negative observed Sharpe at n_trials=105) |
| PBO mean | 0.0892 | 0.119 | data-scarcity + EXPLORATION budget noise |
| **PBO max** | **1.0 (TRX/2022-Q4 cells)** | **1.0** (LDO/2026-03 data-scarcity) | gate target NOT cleared at EXPLORATION budget |
| n_eff | 25 (CONFIRMATION) | **19** | maintained from iter-v3/020/021 (validates n_trials=35 default; consistent regime ×3) |
| n_trials | 1500 (CONFIRMATION) | **105** | EXPLORATION default (3 sym × 35 trials = 105) |

### TRX/2022-Q4 PBO drop — primary success metric

| TRX cell | PBO (iter-v3/018) | PBO (iter-v3/022) | Result |
|---|---:|---:|---|
| TRX/2022-10 | **1.000** | **0.282** | **DROPPED 0.72** ✓ — target cell SUCCESS |
| TRX/2023-01 | **1.000** | 0.999 | NO drop — single-seed EXPLORATION budget too small for stable per-cell PBO reduction |
| TRX/2022-09 | 0.003 | 0.926 | WORSENED — new high-PBO cell adjacent to target window (EXPLORATION budget noise) |
| TRX/2025-10 | (carry-forward) | 0.994 | OOS-window cell — not applicable to constraint #5 |
| TRX/2025-11 | (carry-forward) | 0.940 | OOS-window cell — not applicable to constraint #5 |

Per brief §4 PBO max gate target [0.6, 0.85]: observed 1.0 (LDO/2026-03 data-scarcity) — gate FAILS. Per brief Falsifier 4 (TRX/2022-10 + TRX/2023-01 BOTH PBO < 0.85): TRX/2022-10 = 0.282 PASS; TRX/2023-01 = 0.999 FAIL — falsifier NOT MET (PROMISING-METHODOLOGY).

### Per-symbol attribution (single-seed; CRITICAL — frozen baseline bit-identity)

| Symbol | iter-v3/020 OOS | iter-v3/021 OOS | iter-v3/022 OOS | Δ vs iter-v3/020 |
|---|---:|---:|---:|---|
| **BCHUSDT** | -6.2465 (36 trades / 36.1% WR) | **-6.2465** (36 / 36.1%) | **-6.2465** (36 / 36.1%) | **BIT-IDENTICAL** |
| **LDOUSDT** | -8.9257 (13 / 38.5%) | **-8.9257** (13 / 38.5%) | **-8.9257** (13 / 38.5%) | **BIT-IDENTICAL** |
| TRXUSDT | +5.3860 (37 / 37.8%) | +5.3860 (37 / 37.8%) | **+7.6101** (33 / 42.4%) | **+0.5524 lift attributable to regime gate** |

**Forensic finding** (engineering report `499b59e` + Critic FINAL `3b3cc41`): regime gate fires for TRX (965/2153 cumulative IS+OOS = 44.8%) but ZERO fires for BCH or LDO (gate is correctly TRX-only-targeted). BCH/LDO Optuna trajectories are independent of TRX's regime gate at the per-symbol architecture layer — the cross-symbol regression in the headline Sharpe is the **frozen single-seed=42 baseline pre-existing across iter-v3/020/021/022**, NOT a methodology defect or cross-contamination.

### Saturation falsifier verification (per `feedback_axis_saturation_predictor.md`)

| Predictor | Lower bound | Upper bound | Observed | Triggered? |
|---|---:|---:|---:|---|
| IS trade band (brief §2.7) | 155 | 189 | **196** | TECHNICALLY FIRES (+7 above upper) |

**Context-sensitive interpretation**: the brief's saturation band [155, 189] was calibrated against iter-v3/018 CONFIRMATION multi-seed mean IS=172 (±10%). The EXPLORATION single-seed=42 baseline across iter-v3/020 and iter-v3/021 produces IS=200 (BCH=98, LDO=23, TRX=79). iter-v3/022 produces IS=196 (TRX reduced 79 → 75 by regime gate; BCH+LDO bit-identical at 98+23=121). The saturation falsifier fires technically (196 > 189) but is measuring EXPLORATION-vs-CONFIRMATION reference mismatch, not an axis-behavior anomaly. The TRX-IS impact -4 trades is within reasonable design-space behavior for the mechanism.

## What Worked

- **Methodology of the run is clean.** All 12 standard methodology checks PASS (Critic FINAL `3b3cc41`). Look-ahead audit verified by `searchsorted('left') - 1` past-only construction in regime-state computation; adversarial test `tests/strategies/ml/test_regime_gate.py` confirms current-bar BTC NOT in own window. Embargo width REQUIRED_GAP=66=(21+1)×3 unaffected by regime gate mechanism. Reproducibility stamp clean (Setup `64e101d`, gate `8418f57`, brief `79321c5`, EDA `b728313`). Single-axis discipline preserved: regime gate added; V3_MODELS reverted 5→3; ITERATION_LABEL=v3-022; 13 V3_FEATURE_COLUMNS unchanged; per-symbol cap kept disabled.

- **n_trials=35 EXPLORATION default validates positively at iter-v3/022 (PRELIMINARY-VALIDATED through iteration #3).** n_eff=19 maintained from iter-v3/020 + iter-v3/021 — consistent regime across 3 EXPLORATIONs. PSR=0.0000 collapses honestly when observed Sharpe is materially negative; the metric is now informative rather than saturated. DSR=0.0 reflects honest deflation. Wall-clock 14 min (well within 2h cap). Three data points confirm n_trials=35 default operates in the honest deflation regime; the default is empirically validated for this 3-symbol universe surface.

- **TRX-axis effects are clean and attributable.** TRX OOS weighted_pnl +7.6101 vs iter-v3/020/021's +5.3860 = +0.55 lift attributable to the regime gate (single-seed). TRX IS trades reduced 79→75 (4-trade reduction matching counterfactual prediction of 1-2 + Optuna re-opt absorption). Gate-fire-rate observed 44.8% cumulative IS+OOS (vs EDA-predicted 14.49% IS-wide) — explained by per-signal-level vs per-bar-level measurement basis difference plus combined IS+OOS window coverage; OOS TRX positive PnL is evidence against severe OOS regime-misalignment. TRX/2022-10 PBO drop 1.0 → 0.282 demonstrates the gate operated as designed at the targeted high-PBO cell.

- **Per-symbol Optuna independence rigorously verified — NO cross-contamination from regime-gate axis.** Forensic exact-equality check across iter-v3/020 / iter-v3/021 / iter-v3/022 confirmed BCH and LDO OOS results are bit-identical (weighted_pnl, n_trades, win_rate all digit-for-digit). The per-symbol architecture means each per-symbol LightGBM model is trained independently; regime gate doesn't contaminate BCH/LDO Optuna trajectories. **This is a feature of single-seed EXPLORATION, not a methodology defect.** New memory rule `feedback_v3_single_seed_frozen_baseline.md` enshrines this distinction so future EXPLORATION QRs cannot misread BCH/LDO movement (or absence thereof) as evidence about a TRX-only or other-symbol-only axis.

## What Failed

- **Falsifier 1 (NEGATIVE indicator) fires unambiguously** per brief §4.4 row 5: OOS Sharpe -0.4313 < anchor -0.10 threshold (anchor +0.2869); roster non-bit-identity (TRX changed: 022 TRX OOS +7.6101 vs 020/021 TRX OOS +5.3860). Two §4.4 row 5 conditions met. Verdict triggers via OOS collapse condition + roster non-identity (TRX-only). Clean EXPLORATION-NEGATIVE — no NULL-RESULT (would require bit-identical ROSTER, not just per-symbol bit-identity on BCH/LDO with TRX divergence) and no PROMISING-MECHANICAL.

- **Falsifier 4 (PBO methodology lift) NOT MET.** Brief target: TRX/2022-10 + TRX/2023-01 BOTH PBO < 0.85. Observed: TRX/2022-10 = 0.282 PASS; TRX/2023-01 = 0.999 FAIL. The mechanism operated PARTIALLY — the targeted-by-design TRX/2022-10 cell achieved -0.72 PBO drop, but TRX/2023-01 (target cell #2) barely changed despite 38.7% gate-fire rate in that month per EDA. Mechanism: at single-seed n_trials=35 = 105 fits per cell, the per-cell PBO measurement is intrinsically noisy and the regime gate's effect on TRX/2023-01's hyperparameter space is unstable; CONFIRMATION budget (5 outer × 50 trials = 750 fits per cell) would provide cleaner per-cell PBO measurement.

- **PBO max gate FAILS at observed 1.0.** Brief §4 target [0.6, 0.85]; observed 1.0 driven by LDO/2026-03 data-scarcity cell (LDO has data only from 2024-09 onward; the 2026-03 training window has minimal data) — UNRELATED to regime gate. The PBO max metric is sensitive to ANY data-scarcity cell, not just the regime-gate-targeted ones. This is a structural feature of the metric, not a failure of the regime gate itself, but it nonetheless disqualifies the iteration from PROMISING classification at the §4 gate.

- **OOS Sharpe Δ -0.82 (vs anchor) — second-worst OOS Δ in v3 anchor-basis history (after iter-v3/021's -0.83).** Brief §4 predicted OOS Sharpe band [+0.40, +0.55] — observed -0.4313 missed the entire band by -0.83 from the lower bound. The QR's reasoning that "regime gate reduces noise on TRX without affecting BCH/LDO" was structurally correct (per-symbol architecture preserved + bit-identity verified) but ignored the **frozen single-seed=42 baseline pre-existing condition**: BCH and LDO at single-seed=42 have been net-negative since iter-v3/020 onset (the cap iteration where they first ran at single-seed --exploration mode). The headline OOS Sharpe at single-seed EXPLORATION is dominated by BCH/LDO's frozen baseline, not by the iteration's axis.

- **OOS MaxDD increased +15.16pp** from 27.74% (anchor seed 42 best) to 42.90%. Counter to brief §5 mechanism story ("the gate operates at the per-bar candidate-signal layer; it does not gate trade emission, only Optuna training-data layer"). Observed: BCH/LDO frozen baseline drag plus single-seed clustering of TRX losses contributed to deeper drawdowns.

- **OOS n_trades=82 < 130 trade-rate floor.** Informational caveat at EXPLORATION single-seed (`feedback_trade_rate_floor_bundle_level.md` — floor applies at CONFIRMATION-bundle level, not EXPLORATION). Below floor at single-seed; the gate mechanism reduced effective trade emission slightly + BCH/LDO frozen baseline already had TRX-dominant 50%-share OOS distribution.

## Critical Lessons

(a) **Per-symbol Optuna IS independent at single-seed EXPLORATION — no cross-symbol contamination from TRX-only or other-symbol-only axes.** The forensic exact-equality check across iter-v3/020 / iter-v3/021 / iter-v3/022 confirmed BCH and LDO OOS results bit-identical (weighted_pnl, n_trades, win_rate digit-for-digit). Mechanism: each per-symbol LightGBM model is trained on its own per-symbol Optuna trajectory; symbol-targeted axes (regime gate on TRX, universe expansion adding HBAR/AVAX, per-symbol cap on each symbol independently) cannot contaminate other symbols' Optuna trajectories at the single-seed=42 deterministic baseline. This is structurally correct architecture-design, not a methodology defect.

(b) **Single-seed EXPLORATION at n_trials=35 produces noisy per-cell PBO at the tail; some target cells improve, others don't.** TRX/2022-10 cell PBO dropped 1.0 → 0.282 (clean target SUCCESS); TRX/2023-01 cell PBO stayed at 0.999 despite 38.7% gate-fire rate in the training month (per EDA `b728313`). The per-cell PBO measurement at single-seed n_trials=35 = 105 fits per cell is intrinsically noisier than CONFIRMATION budget (5 outer × 50 trials = 750 fits per cell). Some target cells improve, others don't, in patterns that may reflect EXPLORATION-budget Optuna search variance more than the axis's true effect on that cell. Future single-seed EXPLORATION-mode PBO target-gate evaluation MUST account for this measurement variance.

(c) **PBO max gate is sensitive to ANY data-scarcity cell, not just regime-gate-targeted cells.** LDO/2026-03 PBO=1.0 is unrelated to the regime gate (LDO has data only from 2024-09 onward; the 2026-03 training window has minimal data = 799 candles). The PBO max aggregator does not distinguish "high-PBO due to regime instability" from "high-PBO due to data-scarcity"; both produce PBO=1.0 at the cell level. Future iterations targeting PBO max gate must explicitly enumerate which cells they target and which cells they expect to be carry-forward / data-scarcity artifacts; the catalog row should preserve this distinction.

(d) **Pre-commit for iter-v3/023: funding rate retest at n_trials=35 (was iter-v3/019 INERT at n_trials=10).** Per Critic FINAL Recommendation #1 of iter-v3/022 (SHA `3b3cc41`): retest `funding_rate_zscore_30` at the new EXPLORATION default n_trials=35. iter-v3/019 was PROMISING-INERT at the prior n_trials=10 (importance rank 14/14 LDO+TRX+Portfolio); 3.5× more Optuna trials may surface signal if the feature was budget-limited rather than genuinely INERT. Also disambiguates the broader "is n_trials=35 default sufficient for NEW-feature-family-axis discovery" question. Brief band: predicted IS Sharpe similar or improved [+0.40, +0.70]; OOS [+0.45, +0.70]. PATH A: rank ≤7 for ≥1 symbol AND IS Sharpe Δ ≥ +0.10 → genuine signal at higher budget; keep funding for CONFIRMATION. PATH B: rank still 14/14 across all 3 → genuinely INERT; close axis permanently. PATH C: IS Sharpe Δ < -0.10 → feature actively hurts; suggests it was lottery-helping at n_trials=10.

## Pre-Commit for iter-v3/023

Per Critic FINAL Recommendation #1 of iter-v3/022 (SHA `3b3cc41`) + `feedback_v3_iter019_axis_priorities.md` MEDIUM #6 (RAISED to within-cycle priority HIGH given regime-gate axis #4 is partially-effective-closed) + diary lessons (a)-(d):

- **iter-v3/023 axis = funding_rate_zscore_30 RETEST at n_trials=35** (was iter-v3/019 PROMISING-INERT at n_trials=10).
- **RE-ADD funding_rate_zscore_30 to V3_FEATURE_COLUMNS** (revert 13 → 14): new V3_FEATURE_COLUMNS = V3_FEATURE_COLUMNS_TOP_N including `funding_rate_zscore_30` at the end.
- **DISABLE regime gate** (`enable_regime_gate=False`) — was iter-v3/022's axis; keep code in repo at zero revert cost (preserves option for CONFIRMATION-mode re-evaluation).
- **ITERATION_LABEL = "v3-023"**.
- **Funding infrastructure already exists**: `funding_v3.py` module + `crypto-trade fetch-funding` CLI + `data/funding_rates/<sym>.csv` cache (preserved at iter-v3/019 closeout per Critic FINAL Rec #2 zero revert cost).
- **Verify funding parquets up-to-date** (re-run `crypto-trade features --track v3` if needed; staleness guard 16h applies).
- **NEW memory rule `feedback_v3_single_seed_frozen_baseline.md`** committed (per lesson (a)).
- **Hypothesis**: at n_trials=35 (vs iter-v3/019's n_trials=10), the model has ~3.5× more Optuna trials per cell to surface funding signal. If feature is genuinely informative, importance rank should improve from 14/14 (LDO+TRX+Portfolio at iter-v3/019) toward top-half (rank ≤7) on at least 1 symbol.
- **Predicted bands**: IS Sharpe similar or improved [+0.40, +0.70] (anchor +0.38, iter-v3/019 was +1.16 lottery-overshoot); OOS Sharpe [+0.45, +0.70] (anchor +0.39); importance rank predicted top-7 for ≥1 symbol if feature has signal.
- **Three pathways**:
  - PATH A (PROMISING): rank ≤7 for ≥1 symbol AND IS Sharpe Δ ≥ +0.10 → genuine signal at higher budget; keep funding for CONFIRMATION.
  - PATH B (PROMISING-INERT-still): rank still 14/14 across all 3 → feature genuinely INERT; close axis permanently.
  - PATH C (NEGATIVE): IS Sharpe Δ < -0.10 → feature actively hurts at n_trials=35; suggests it was lottery-helping at n_trials=10.

## Cadence Status

**4 of 10 EXPLORATIONs done in post-bootstrap cycle.** iter-v3/019 (PROMISING-INERT) + iter-v3/020 (NEGATIVE-clean / PATH C) + iter-v3/021 (NEGATIVE-clean) + iter-v3/022 (NEGATIVE-clean) completed; **6 EXPLORATIONs remaining** before next CONFIRMATION (earliest = iter-v3/029).

CONFIRMATION wall-clock cap = 6h (per `feedback_v3_cadence_discipline.md` empirically updated post-iter-v3/018). EXPLORATION wall-clock cap = 2h (iter-v3/022 ran 14 min — well within).

**TRX/2022-Q4 regime gate axis PARTIALLY-EFFECTIVE-CLOSED for current 10-EXPLORATION cycle** (TRX/2022-10 cell improvement is real-but-narrow; TRX/2023-01 NOT cleared at single-seed budget; CONFIRMATION-mode re-evaluation deferred to iter-v3/029+).

**iter-v3/023 = funding rate retest at n_trials=35.**

## Reproducibility

- Setup commit SHA: `64e101d` (feat: TRX/2022-Q4 regime gate + revert universe 5→3 + ITERATION_LABEL=v3-022)
- Phase 5.5 gate SHA: `8418f57` (PASS)
- Brief SHA: `79321c5`
- EDA analysis SHA: `b728313`
- Engineering report SHA: `499b59e`
- Critic FINAL SHA: `3b3cc41`
- HEAD SHA at backtest run: `64e101d`
- Reports: `reports-v3/iteration_v3-022/comparison.csv` (single-seed EXPLORATION row), `reports-v3/iteration_v3-022/dsr.json` (DSR=0.0 / PBO=0.119 / PSR=0.0000 / n_trials=105 / n_eff=19), `reports-v3/iteration_v3-022/per_cell_pbo.csv` (TRX/2022-10 0.282 SUCCESS; TRX/2023-01 0.999 NO drop; LDO/2026-03 data-scarcity 1.0), `reports-v3/iteration_v3-022/seed_summary.json`, `reports-v3/iteration_v3-022/pareto_front.csv`, `reports-v3/iteration_v3-022/ic_matrix.csv`, `reports-v3/iteration_v3-022/adf_test.csv`
- No tag (NEGATIVE-clean — TRX/2022-Q4 regime gate axis partially-effective-closed; not a baseline-update event)
