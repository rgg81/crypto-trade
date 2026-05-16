# Phase 7.5 Critic Review — iter-v3/063

OVERALL: EXPLORATION-NEGATIVE — SUSPICIOUS-OOS-DOMINANT classification methodologically correct; IS-COLLAPSE confirms pre-registered Mode B+C; iteration is NO-MERGE for cycle 1 advancement.

## Iteration Type (from Brief Section 0.5)
TYPE: EXPLORATION (Cycle 1 #4 of 10, --exploration mode, --seeds 1, --n-trials 35, ENSEMBLE_SIZE=3, MASS FEATURE EXPANSION 14→48 originally, 14→46 after pre-flight ban filter)

## Foundation Audit (Boot Steps 9-11)

- **walk_forward.py:113**: PASS — `train_end_ms = test_start_ms - embargo_ms` (the lookahead-bias fix from main commit `5566a69`, cherry-picked at `e149e9d`, IS present in this worktree). The engineering report Section 12 INCORRECTLY claims the bug is "present in this worktree". This is FACTUALLY WRONG. Verified zero matches for the buggy line `train_end_ms = test_start_ms` outside docstrings/comments.
- **labeling.py triple-barrier σ_t**: PASS — uses precomputed `atr_values` array passed as parameter; ATR derived past-only via `tr.ewm(alpha=1/period, adjust=False).mean()` from `regime_v3.py:31`.
- **lgbm.py:451-457 cv_gap**: PASS — calls `compute_embargo_candles(label_timeout_minutes, interval_minutes) * n_symbols` (single source of truth shared with walk-forward).
- **validation_v3.py REQUIRED_GAP=66**: PASS — `(21+1)*3 = 66` correct for 3-symbol BCH+LDO+TRX bundle.
- **run_baseline_v3.py mode-flag wiring**: PASS — `--exploration` flag → ENSEMBLE_SIZE=3 → ENSEMBLE_SEEDS[0:3]=(191664963, 1662057957, 1405681631); confirmed in `ensemble_summary.json`.
- **ITERATION_LABEL = "v3-063"**: PASS — verified at `run_baseline_v3.py:128`.
- **Banned features absent from V3_FEATURE_COLUMNS_TOP_N**: PASS — `vol_normalized_ret_5d` and `hurst_drift_50_200` only appear in comments at `features_v3/__init__.py`, NOT in the active tuple. Pre-flight assertion enforces `len(V3_FEATURE_COLUMNS) == 46`.
- **Track isolation (A4)**: PASS — `grep "from crypto_trade.features " src/crypto_trade/features_v3/` returns zero matches.

## Per-Check Status

### Check 1 — Look-Ahead Audit: PASS

All 9 NEW features verified past-only by direct code reading:
- (a) `adx_14` (`technical_v3.py:71-167`): TR/+DM/-DM use `prev_high`/`prev_low`/`prev_close` via 1-bar shift; Wilder smoothing causal.
- (b) `candle_dow_sin/cos` (`calendar_v3.py:45-83`): pure timestamp-based; no rolling windows.
- (c) `trend_efficiency_signed` (`engineered_v3.py:560-623`): Kaufman ER with `.shift(1)` applied to `er`; `ret_20d` uses `log_close.shift(60)` past-only.
- (d) `vol_regime_x_momentum` (`engineered_v3.py:626-678`): `close.shift(15)` and pre-computed past-only `atr_pct_rank_200`.
- (e) `sym_vs_btc_ret_3d` and `sym_vs_btc_vol_14d` (`cross_btc_v3.py:88-103`): use `log_close[t] - log_close[t-9]` and `rolling(42).std()` past-only; merge by `open_time`.
- (f) `taker_buy_imbalance_20` (`microstructure_v3.py:28-72`): explicit `tbr.shift(1).rolling(20).mean()` past-only.
- (g) `ret_1d` (`momentum_accel_v3.py:67`): `_momentum(close, 3)` = `log(close[t]) - log(close[t-3])`.

No look-ahead in any NEW feature.

### Check 2 — Embargo Width: PASS

Required gap = (21 + 1) × 3 = 66 bars. Applied symmetrically at outer (walk_forward.py:113) and inner (lgbm.py:457) boundaries. Single source via `compute_embargo_candles()`. No leakage path identified.

### Check 3 — Multiple-Testing Correction: INFORMATIONAL (not BLOCK at EXPLORATION)

DSR=0.0, DSR_relative=0.0182, PSR=1.0, PBO=0.1054. Per `feedback_v3_dsr_mode_artifact.md`, EXPLORATION-mode DSR/PSR are STRUCTURAL ARTIFACTS at n_trials_total=315 and INFORMATIONAL ONLY. PBO=0.1054 below 0.40 threshold (informational PASS). At CONFIRMATION (/069+) gates would be evaluated with full enforcement.

### Check 4 — IC Correlation: WARN (not BLOCK)

Post-backtest `ic_matrix.csv` reveals 6 pairs with |Pearson IC| > 0.70:

| A | B | \|IC\| | Status |
|---|---|---|---|
| `fracdiff_logclose_dstat` | `fracdiff_d05_close` | 0.989 | Category-2 carveout (algebraic identity per LdP AFML Ch.5) — ACCEPTED |
| `ema_spread_atr_20` | `trend_efficiency_signed` | 0.872 | Category-2 carveout (composed × primitive per `feedback_v3_engineered_feature_pivot.md`) — ACCEPTED |
| `atr_pct_rank_500` | `atr_pct_rank_200` | 0.825 | NO carveout — **EDA DROPPED `atr_pct_rank_200` (T8_pruning_decisions.csv:19) but implementation INCLUDED IT** |
| `vwap_dev_20` | `regime_momentum_signed_5d` | 0.764 | Category-2 carveout (composed × primitive) — ACCEPTED |
| `range_realized_vol_50` | `sym_vs_btc_vol_14d` | 0.757 | NEW pair; mechanically correlated (vol primitives across horizons) |
| `btc_ret_14d` | `btc_ret_7d` | 0.710 | Mechanically correlated; both BASELINE_V3 → KEEP_BOTH per EDA |

**Brief-vs-implementation methodology divergence**: `atr_pct_rank_200` was DROPPED at EDA but INCLUDED in `features_v3/__init__.py:190` ("promoted from parquet"). Brief Section 3 (line 304) flagged it as "reserved" pending T8 verification — verification said DROP but implementation added it. Engineering report makes NO mention of this deviation. WARN not FAIL because (a) ≤1 redundant feature of 46, (b) the broader 46-dim Optuna search space is the dominant overfit driver per pre-registered Mode C.

### Check 5 — ADF Stationarity: PASS

46-feature ADF over full IS window per (symbol, month). Many early months (2020-01 through 2020-03) show NaN/non-stationary (warm-up). By later months, all features achieve stationarity-majority. The 9 NEW features all achieve p<0.05 in 2020-02+ rows. `candle_dow_sin/cos` are constant-by-period (deterministic regime indicators — acceptable per EDA).

### Check 6 — Pareto Dominance: N/A at single-seed EXPLORATION

`pareto_front.csv` not produced for EXPLORATION-mode runs (single-seed=42 lineage subset, ENSEMBLE_SIZE=3). Multi-seed Pareto deferred to /069 CONFIRMATION. Not a methodology FAIL.

### Check 7 — Reproducibility: PASS

(a) Engineering report stamps backtest commit SHA `79cb0e9d402d92a784ad739143eaa8fb95fec275`. (b) Runner uses `feature_columns=list(features_for_symbol(symbol))` per `feedback_explicit_feature_columns.md` invariant. (c) `ENSEMBLE_SEEDS[0:3] = (191664963, 1662057957, 1405681631)` verified in `ensemble_summary.json`. (d) Trade-math spot check on 3 trades — all match CSV to 4dp.

### Check 8 — Hypothesis-Implementation Alignment: PASS-WITH-FORENSIC-DETAIL

Brief Section 1 hypothesis (LOCKED at `365c5d5`): "Expanding V3_FEATURE_COLUMNS_TOP_N from 14 to 48 production-grade features lifts cycle 1 EXPLORATION-mode anchor by ≥+0.10 IS Sharpe AND ≥+0.20 OOS Sharpe vs /060."

Implementation: 46 features (not 48 due to pre-flight ban filter). Observed: IS Δ = -1.38 (DOUBLE-FALSIFIED: predicted [+0.10, +0.47], observed -1.38 — 1.48 Sharpe units below predicted lower bound). OOS Δ = +0.31 (PASSes the +0.20 gate but BCH-concentrated lottery per per-symbol forensics).

Hypothesis is FALSIFIED. CORRECTLY CLASSIFIED SUSPICIOUS-OOS-DOMINANT. Pre-registered Mode B (Section 7) anticipated: "single-seed lottery at expanded feature space; OOS spikes spuriously while IS doesn't track." Pre-registered Mode C anticipated: "INERT features at higher Optuna budget actively HARM per `feedback_v3_inert_features_at_higher_budget.md`." Both are CO-ACTIVATED.

The IS-COLLAPSE subtype (IS dropping from positive to negative -0.5507) is structurally consistent with `feedback_v3_inert_features_at_higher_budget.md`: at n_trials=35 with 46-dim colsample space, Optuna's TPE warmup is shallower relative to dimensionality, finding IS-OOF-optimizing parameter regions that fail on held-out IS test periods.

### Check 9-12 (optional): PASS (symbol exclusion, feature isolation, forming-candle, library version)

### Check 13 — Mass-Expansion-Specific Forensic: WARN

Per `model_importance_last_month_*.csv`:
- **BCH last month**: NEW features mostly mid-low rank (`adx_14` 11/46, `taker_buy_imbalance_20` 20/46, `trend_efficiency_signed` 35/46, `candle_dow_sin/cos` 45-46/46). Top-5 dominated by BASELINE_V3 features. **BCH OOS lift NOT cleanly attributable to NEW signal**.
- **LDO last month**: 7 NEW features in top-20 but LDO OOS dropped from 11 trades to 3 — confidence threshold tightening, not signal failure.
- **TRX last month**: NEW features mid-low. TRX OOS WR collapsed 50.0% → 26.7% — wrong-direction signals at expanded feature set.

Pattern is exactly what `feedback_v3_inert_features_at_higher_budget.md` predicts.

## §11 Anti-Pattern Static Scan

13/13 PASS or WARN. Notable WARNs:
- A4 IC correlation: 1 non-carveout pair above 0.70 (atr_pct_rank_500 × atr_pct_rank_200) — process slip, not methodology violation
- A12 DSR/PSR granularity: informational at EXPLORATION mode

## Adversarial Findings — Methodology Deviations

1. **Engineering report Section 12 factual error**: Claims walk-forward lookahead bug "is present in this worktree" — FALSE. Fix from main `5566a69` cherry-picked at SHA `e149e9d` and present in `walk_forward.py:113`. Should be corrected via follow-up commit. Does NOT affect verdict (the fix being present means IS+OOS are unbiased post-fix).

2. **Brief-vs-implementation divergence on `atr_pct_rank_200`**: EDA's `T8_pruning_decisions.csv:19` explicitly says DROP at |IC|=0.820 with atr_pct_rank_500. Yet `V3_FEATURE_COLUMNS_TOP_N:190` INCLUDES atr_pct_rank_200. Post-backtest IC matrix confirms 0.825 redundancy. Engineering report makes NO mention. WARN not BLOCK because contribution is ≤1/46 features.

3. **Pre-flight feature drop (48 → 46) without re-running EDA**: Two banned features dropped at pre-flight. Greedy LDP IC-pruning was performed at 48 features; orthogonality of remaining 46 not re-verified. Post-backtest IC shows 6 pairs above 0.70 — most have valid carveouts but `atr_pct_rank` pair was missed. Process slip, not methodology failure.

## Verdict Reasoning

The iteration is correctly classified SUSPICIOUS-OOS-DOMINANT with IS-COLLAPSE subtype. The IS Sharpe collapse from +0.83 to -0.55 is genuine methodological evidence consistent with pre-registered Mode C ("INERT features at higher Optuna budget actively HARM"). The OOS lift is concentrated 118% in BCH with 30 trades at 46.7% WR — single-symbol, single-seed lottery, NOT a real edge.

NEW features are NOT clearly responsible for the OOS lift (per per-symbol importance distributions: NEW features mostly mid-low rank for BCH). The 46-dimensional Optuna search space at n_trials=35 single-seed produced IS-OOF-optimizing solutions that failed on held-out IS — textbook curse-of-dimensionality at undertuned hyperparameter budget.

Decision NOT to advance to /069 CONFIRMATION as PROMISING is correct. Axis CLOSED-pending-CONFIRMATION per Section 8.3.

The two methodology slips (incorrect Section 12 lookahead claim; atr_pct_rank_200 inclusion contrary to EDA) are real but do not change the verdict.

## Recommendations to QR

1. **Engineering report factual-accuracy gate**: Future engineering reports must verify foundation-file claims against actual code (especially the lookahead-fix status). Section 12 of /063 engineering report should be corrected via follow-up commit that amends the report to state the bug is FIXED at SHA `e149e9d`.

2. **EDA-implementation parity gate**: Brief Section 3 should specify that V3_FEATURE_COLUMNS_TOP_N is BIT-IDENTICAL to EDA's `T8_final_feature_set.csv` (after documented pre-flight bans). Any deviation must be a separate commit with justification — not silently inserted. Alternative: amend Phase 5.5 gate to assert symmetric-difference equals documented banned-feature set.

3. **Mass-expansion mandate methodology amendment**: Per the engineering report's recommendation #2, `feedback_v3_mass_feature_expansion.md` may benefit from structural amendment: phased expansion (add 3-5 features at single-seed individually, validate non-collapse, then bundle survivors at multi-seed CONFIRMATION) rather than single-step 14 → 46 jump at single-seed n_trials=35. The iter-v3/063 IS collapse provides empirical falsification of "mass expansion at single-seed EXPLORATION discovers signal"; future cycle-5 attempts should consider TPE warmup adequacy at target dimensionality (n_trials ≥ 100 may be required for 46-dim colsample space at single-seed).
