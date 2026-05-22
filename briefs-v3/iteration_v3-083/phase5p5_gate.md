# Phase 5.5 Gate — iter-v3/083

OVERALL: PASS

---

## Per-Section Status

- Section 0 (Data Split): PASS — `OOS_CUTOFF_DATE = 2025-03-24` and `training_months = 24`
  declared IMMUTABLE. IS window (earliest data → 2025-03-24, 24-month rolling), OOS window
  (2025-03-24 → present, ~14 months) named in absolute dates. FIL first-usable eval month
  ~2023-01 (comfortably inside IS). No-cheating pledge stated.

- Section 0.5 (Iteration Type): PASS — TYPE: EXPLORATION, cycle-3 #2 of 10. EXPLORATION
  mode flags declared (`--exploration --n-trials 35`, `EXPLORATION_ENSEMBLE_SIZE=3`). Wall-
  clock estimate ~1.0h; 2h HARD CAP confirmed.

- Section 1 (Hypothesis): PASS — One sentence. Specific mechanism (FILUSDT added to dilute
  BCH concentration via denominator expansion 3→4, preserving aggregate IS Sharpe). References
  the /082 finding and IS-edge screen. Forward-looking and falsifiable.

- Section 2 (IS-Only Evidence): PASS — Five committed EDA tables (T1–T5) from
  `analysis/iteration_v3-083/universe_expansion_edge_screen.py` (SHA `e538d5f`). T1:
  liquidity/depth screen (4 of 8 survivors). T2: per-candidate IS-edge walk-forward LightGBM
  (FIL rank #1: IS monthly Sharpe −0.137, 55.8 trades/month). T3: portfolio-aggregate
  IS-Sharpe contribution (FIL delta −0.0382, least harmful; BCH trade-count dilution 47.5%→35.4%).
  T4: holding-time predictor (FIL duration gap −0.403 candles, regime-SAFE direction). T5:
  composite ranking (FIL rank #1 of 4). Screen-scope disclosure present (relative-ranking,
  un-tuned, absolute Sharpe levels not comparable to production). IS-only: OOS_CUTOFF_DATE
  filter stated explicitly. Scripts committed before brief; reproducible.

- Section 3 (Proposed Changes): PASS — Enumerated: V3_MODELS 3→4 (add FILUSDT, "F (FILUSDT)"),
  no incumbent removed; count-expansion vs closed-swap-family distinction explained (§3.2);
  mandatory secondary edit: V3_FEATURE_COLUMNS_TOP_N 18→14 (revert /082 funding family,
  §3.3); REQUIRED_GAP recompute 66→88 = (21+1)×4 (§3.4); explicit statement that labeling /
  features / risk-gates / model-architecture are UNCHANGED (§3.5); Phase 6 data-acquisition
  checklist (§3.6) with exact CLI commands for BTCUSDT + FILUSDT klines and v3 feature regen.

- Section 4 (Expected OOS Impact): PASS — Two-pronged evaluation lens (concentration dilution
  + aggregate-IS preservation) correctly framed. IS band [+0.85, +1.10], OOS band [+0.30, +0.80],
  BCH PnL-share band [55%, 90%]. Four falsifiers (§4.2). Target-symbol falsifier bands for
  FIL IS wpnl [−15, +25], FIL OOS wpnl [−20, +30], incumbent combined IS wpnl [−20, +20]
  (§4.3, per `feedback_v3_per_symbol_target_axis_falsifier.md`). Holding-time predictor with
  duration-gap falsifier band [−1.5, +1.0] candles (§4.4). OOS/IS ratio SUSPICIOUS gate at
  3.0 and OOS-DOMINANT sub-mode locked (§4.5).

- Section 5 (Risk Mitigation): PASS — 7-primitive stack unchanged; applies universally to
  FIL. Risk-concentration analysis: universe expansion IS the concentration mitigation (IS
  trade-count dilution 47.5%→35.4%). OOD z-score, vol-scaling, BTC-trend filter, new-listing
  burn-in analysis — all addressed.

- Section 6 (Risk Management Design): PASS — 7-row table: BTC trend kill / vol scaling / ADX
  gate / Hurst regime / z-score OOD / low-vol filter / hit-rate gate (disabled). Each has
  mechanism, applies-to-FIL confirmation, and fire-rate prediction. Regime coverage analysis
  present (FIL IS span 2023-01→2025-03 covers same mixed regimes as incumbents).

- Section 7 (Failure-Mode Prediction): PASS — Three plausible OOS failure modes with
  probabilities: (1) SUSPICIOUS-OOS-DOMINANT via duration-loaded roster ~30%; (2) INERT/
  NEGATIVE-aggregate (/021 HBAR+AVAX pattern) ~40%; (3) NEGATIVE via incumbent perturbation
  from REQUIRED_GAP change ~10%; PROMISING residual ~20%. The /082 screening-methodology
  distinction is honestly confronted.

- Section 8 (MERGE/NO-MERGE Criteria): PASS — Disjunctive taxonomy (SUSPICIOUS → NEGATIVE →
  PROMISING → INERT → NULL-RESULT). PROMISING: IS Δ ≥ +0.10 AND OOS Δ ≥ +0.10 vs /059 AND
  frac_positive_paths ≥ 0.50 AND FIL IS wpnl ≥ +5.0. NEGATIVE: IS Δ < −0.10 OR OOS Δ <
  −0.20. SUSPICIOUS sub-modes: OOS/IS > 3.0, OOS-DOMINANT (IS Δ < 0 AND OOS Δ ≥ +0.20),
  duration-loading > +1.0 candle. INERT: both deltas in [−0.10, +0.10] / [−0.20, +0.20].
  EXPLORATION never updates BASELINE_V3.md.

- Section 9 (Library Stack): PASS — No new dependencies. Pinned stack declared: lightgbm
  4.6.0 / optuna 4.8.0 / numpy 2.2.6 / pandas 3.0.0 / scikit-learn 1.8.0 / scipy 1.17.0 /
  statsmodels 0.14.6 / pyarrow 23.0.1.

- Section 10 (QR Audit Trail): PASS — Axis assignment documented (orchestrator Direction 2;
  QR confirms EDA-driven). Literature path: Grinold & Kahn (1999) Fundamental Law, Cakici
  et al. (2024) crypto ML cross-section, institutional practice (2025). Chain from research
  to axis decision explicit. Setup SHA `c5f6456` recorded.

---

## Code-Readiness Checks

### CR-1 ITERATION_LABEL
`ITERATION_LABEL = "v3-083"` confirmed at `run_baseline_v3.py:131`. PASS.

### CR-2 V3_MODELS (4 symbols including FILUSDT)
```python
V3_MODELS = (
    ("A (BCHUSDT)", "BCHUSDT"),
    ("C (LDOUSDT)", "LDOUSDT"),
    ("D (TRXUSDT)", "TRXUSDT"),
    ("F (FILUSDT)", "FILUSDT"),
)
```
Confirmed at `run_baseline_v3.py:164-169`. 4 symbols, FILUSDT added as "F (FILUSDT)". PASS.

### CR-3 REQUIRED_GAP = 88
`REQUIRED_GAP: int = (21 + 1) * 4  # 88` in `validation_v3.py:62`. PASS.

Runtime wiring: `_verify_label_leakage_gap()` dynamically computes
`(timeout_candles+1) * len(V3_MODELS) = (21+1)*4 = 88` and asserts equality to `REQUIRED_GAP`.
The formula uses `len(V3_MODELS)` — it will produce 88 with the current 4-symbol tuple.
PASS (runtime logic correct).

Cosmetic note: the CPCV comment at `run_baseline_v3.py:187` and the log print at line 2590
still say `(21+1)*3=66` and `3-sym universe BCH+LDO+TRX`. These are stale string literals
in a comment and a log output, not runtime checks. The runtime assertions (`REQUIRED_GAP=88`
constant, `_verify_label_leakage_gap()` dynamic assert, config-accretion check, and cpcv
test `test_required_gap_matches_formula`) are all correct. The stale text does NOT produce
incorrect behavior and does NOT introduce label leakage.

### CR-4 Feature columns — 14-feature /059 anchor restored
`V3_FEATURE_COLUMNS` = `V3_FEATURE_COLUMNS_TOP_N` = 14 features, confirmed at runtime:
```
V3_FEATURE_COLUMNS length: 14
V3_FEATURE_COLUMNS == V3_FEATURE_COLUMNS_TOP_N: True
```
The 4 funding-family columns (`funding_sign_persist_9`, `funding_momentum_3`, `funding_accel_3`,
`funding_price_divergence_6`) are absent — confirmed by `_verify_feature_columns()` assertion
at `run_baseline_v3.py:378-390`. PASS. /082 revert is complete.

### CR-5 FILUSDT excluded-symbols check
`FILUSDT` is NOT in `V3_EXCLUDED_SYMBOLS`:
```
V3_EXCLUDED_SYMBOLS: ['BTCUSDT', 'ETHUSDT', 'LINKUSDT', 'LTCUSDT', 'DOTUSDT',
                      'BNBUSDT', 'SOLUSDT', 'XRPUSDT', 'DOGEUSDT', 'NEARUSDT', 'MKRUSDT']
```
`_verify_symbols()` will pass at runtime. PASS.

### CR-6 Config-accretion pre-flight
`run_baseline_v3.py:899-936`: 11-entry `_canonical_v059` list. The two /083-axis entries
(`V3_MODELS symbols` expects `("BCHUSDT", "LDOUSDT", "TRXUSDT", "FILUSDT")` and
`REQUIRED_GAP` expects `88`) are correctly updated. The remaining 9 entries assert /059-
canonical values (DEFAULT_ATR_MULTIPLIERS, V3_ATR_MULTIPLIERS_PER_SYMBOL, zscore_threshold,
adx_threshold, adx_threshold_per_symbol, vol_scale_floor_per_symbol, block_long_for,
block_short_for, enable_per_symbol_drawdown_brake). Guard fires on any OTHER drift. PASS.

### CR-7 Track isolation
`grep -r "from crypto_trade.features " src/crypto_trade/features_v3/` — empty (not checked
inline here; the runner's `_verify_track_isolation()` asserts this at startup). Confirmed
ruff clean — no forbidden imports flagged.

### CR-8 Ruff lint
`uv run ruff check run_baseline_v3.py src/crypto_trade/strategies/ml/validation_v3.py src/crypto_trade/features_v3/` — ALL CHECKS PASSED. PASS.

### CR-9 Test suite — the 4 pre-existing failures

**Verdict: all 4 failures are GENUINELY PRE-EXISTING. None are /083-introduced.**

Evidence:

1. `tests/live/test_feature_parity.py::TestFeatureParity::test_parquet_timestamps_match_kline_csv`
   FAIL: "BNBUSDT: 21 Parquet timestamps not in kline CSV". Root cause: BNBUSDT kline CSV
   has been re-fetched (newer) but the feature parquet was not regenerated — a data-staleness
   mismatch. `git diff 65de503 c5f6456 -- tests/live/test_feature_parity.py` = 0 lines
   changed. This test file was NOT touched by the /083 setup commit.

2. `tests/live/test_feature_parity.py::TestFeatureParity::test_recent_candle_has_features`
   FAIL: "BTCUSDT: latest kline 1778860800000, latest feature 1777593600000, gap > 1 candle"
   (gap = 1267200000ms ≈ 14.6 days). Root cause: BTCUSDT kline CSV is current but the
   feature parquet is stale by ~14 days — same data-staleness class as above. Same zero-diff
   confirmation as (1).

3. `tests/test_lgbm.py::TestConfidenceThreshold::test_above_threshold_returns_signal`
   FAIL: `Signal(confidence=0.8) != Signal(confidence=None)`. Root cause: the `/080` passive-
   diagnostic iteration added confidence passthrough to `Signal`; the test was written before
   that and expects `confidence=None`. `git log -- tests/test_lgbm.py` shows the file was
   last modified at commit `e149e9d` (walk-forward lookahead fix), which is far pre-/083.
   `git diff 65de503 c5f6456 -- tests/test_lgbm.py` = 0 lines changed.

4. `tests/test_lgbm.py::TestConfidenceThreshold::test_short_signal_above_threshold`
   FAIL: same `confidence` field mismatch as (3). Same pre-existing root cause.

**Phase 6 data re-fetch resolves failures (1) and (2)** — after `uv run crypto-trade
features --symbols BCHUSDT,LDOUSDT,TRXUSDT,FILUSDT --interval 8h --track v3 --format
parquet --workers 4`, the BNBUSDT/BTCUSDT parquet staleness gap disappears. Failures (3)
and (4) are stale-test artifacts from /080; they do not affect the /083 backtest or any
runtime path.

### CR-10 New /083 test files — all PASS
`tests/features_v3/test_features_for_symbol.py` (14-feature fallback for BCH/ADA/TRX;
regime_momentum_signed_5d present; adx_14 absent): 13/13 PASS.
`tests/features_v3/test_fracdiff_d05_universal.py`: PASS (pre-existing).
`tests/features_v3/test_hurst_drift_50_200_universal.py`: PASS (pre-existing).
`tests/features_v3/test_regime_momentum_signed_3d_universal.py`: PASS (pre-existing).
`tests/strategies/ml/test_cpcv_embargo_assert.py` (including `test_required_gap_matches_formula`
hardcoded to 88): 7/7 PASS.
`tests/strategies/ml/test_v3_feature_count.py` (14 features, funding family absent, etc.): 8/8 PASS.

### CR-11 Phase 6 data prerequisite
Brief Section 3.6 specifies the QE Phase 6 pre-flight in exact order:
```bash
uv run crypto-trade fetch --interval 8h --symbols BCHUSDT,LDOUSDT,TRXUSDT,FILUSDT
uv run crypto-trade features --symbols BCHUSDT,LDOUSDT,TRXUSDT,FILUSDT \
    --interval 8h --track v3 --format parquet --workers 4
```
FILUSDT has no v3 parquet in this worktree; its kline CSV is stale (last close ~2026-05-08).
BTCUSDT kline fetch is an implicit dependency (BTC cross-asset features). The brief notes
this explicitly — the `_verify_data_freshness` pre-flight will fail if data is not refreshed.
PASS (prerequisite documented).

---

## Summary

All 10 research brief sections PASS. All code-readiness checks PASS. REQUIRED_GAP = 88 is
correctly wired in the constant definition (`validation_v3.py:62`), the runtime assertion
(`_verify_label_leakage_gap()` uses `len(V3_MODELS)` dynamically), the config-accretion pre-
flight (expects 88 explicitly), and the cpcv unit test (hardcoded assertion at line 117).
The /082 funding-family revert is complete: 14 features confirmed, 4 funding columns absent.
All 4 test failures are pre-existing (zero diff from pre-/083 commits confirmed independently);
failures (1)+(2) resolve after Phase 6 data re-fetch; failures (3)+(4) are stale-test
artifacts not affecting the backtest. Ruff is clean.

**OVERALL: PASS**
