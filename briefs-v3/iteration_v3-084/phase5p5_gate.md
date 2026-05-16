# Phase 5.5 Gate — iter-v3/084

OVERALL: PASS

Engineer: Claude Sonnet 4.6 (Quant Engineer role)
Branch verified: `iteration-v3/084`
Gate date: 2026-05-16

---

## Per-Section Status

- Section 0 (Data Split): PASS — `OOS_CUTOFF_DATE = 2025-03-24`, `training_months = 24` confirmed unchanged. IS and OOS windows declared in absolute dates. No-cheating declaration present; EDA reads only source constants and prior artifacts.
- Section 0.5 (Iteration Type Declaration): PASS — TYPE: REFERENCE / METHODOLOGY explicitly stated, cycle-3 slot #3 of 10, EXPLORATION mode with 2h hard cap. Wall-clock estimate 0.74h.
- Section 1 (Hypothesis): PASS — Specific, falsifiable, single declared change (`PER_CELL_GAP` 43→22) plus one configuration revert. Hypothesis: clean /059-config re-run reproduces /059 IS and OOS monthly Sharpe within ±0.10.
- Section 2 (IS-Only Numerical Evidence): PASS — Three evidence tables (T1 config audit, T2 PER_CELL_GAP correction provenance, T3 anchor-staleness Sharpe-vs-net_pnl framing). Committed EDA `analysis/iteration_v3-084/canonical_config_and_anchor_staleness.py` (SHA `401de40`); four output artifacts present in `analysis/iteration_v3-084/`. Reads source constants and prior-iteration artifacts only — no OOS data, no model fit. Appropriate for a REFERENCE iteration (no alpha-evidence table required).
- Section 3 (Proposed Changes): PASS — Exact code changes enumerated with before/after snippets: (a) `PER_CELL_GAP` 43→22 at line 1510, (b) `expected_gap=PER_CELL_GAP` guard on per-cell `combinatorial_purged_cv` call, (c) stale literal corrections at lines ~2539/~2593, (d) `V3_MODELS` 4→3 symbols (drop FILUSDT), (e) `REQUIRED_GAP` 88→66 in `validation_v3.py`, (f) config-accretion check reverted to 11/11 /059-canonical knobs, (g) `ITERATION_LABEL` → `"v3-084"`, (h) five test-file updates. No feature, label, or risk-gate change.
- Section 4 (Expected OOS Impact): PASS — Pre-registered prediction table (IS +1.0894 ± 0.10, OOS +0.5791 ± 0.10). Falsifiers F1/F2 locked with explicit numerical thresholds. Re-anchor decision rule locked (Section 4.3). OOS/IS suspicious gate pre-registered (>3.0 ratio).
- Section 5 (Risk Mitigation): PASS — Confirms zero incremental risk surface. PER_CELL_GAP fix explicitly ruled out as leakage hazard: 43→22 reduces purge gap, moving from over-conservative to exactly correct per López de Prado AFML Ch. 7. 7-primitive gate stack carried verbatim from /059.
- Section 6 (Risk Management Design): PASS — 7-primitive stack inventory confirmed unchanged. Drawdown brake `False`, OOD z-score threshold 2.0, BTC trend threshold 15.0. Kill-switch: 2h hard cap + F1/F2 falsifiers.
- Section 7 (Failure-Mode Prediction): PASS — Four pre-registered outcome buckets with probabilities (≈65% anchor confirmed, ≈20% OOS-drifts-up re-anchor, ≈10% IS-material-off re-anchor, ≈5% 3-seed lottery). Both main branches produce clean pre-registered outcomes with no post-hoc rationalization path.
- Section 8 (MERGE/NO-MERGE Criteria): PASS — REFERENCE iteration classification acknowledged explicitly; standard EXPLORATION taxonomy inapplicable. Two pre-registered states: REFERENCE-CONFIRMED (both Sharpe inside ±0.10 of /059) or REFERENCE-REANCHOR (F1 or F2 fires). BASELINE_V3.md unchanged in both states. `v0.v3-084` tag as closeout marker.
- Section 9 (Library Stack): PASS — Pinned stack listed verbatim from /083: `lightgbm 4.6.0`, `optuna 4.8.0`, `numpy 2.2.6`, `pandas 3.0.0`, `scikit-learn 1.8.0`, `scipy 1.17.0`, `statsmodels 0.14.6`, `pyarrow 23.0.1`. EDA uses stdlib only. No new dependencies.
- Section 10 (QR Audit Trail): PASS — Axis assignment traced to /083 diary Sections 6, 9, 12 and `briefs-v3/cycle3_plan.md` Section 7. Two prior precedents cited (/060→/077, revert-prior-negative pattern). `PER_CELL_GAP` defect provenance traced to iter-v3/068 and Critic FINAL `1116124` Rec #2. EDA commitment noted.

---

## Code-Readiness Checks

### CR1 — ITERATION_LABEL

`run_baseline_v3.py:131` → `ITERATION_LABEL = "v3-084"`: PASS

### CR2 — PER_CELL_GAP = 22

`run_baseline_v3.py:1510` → `PER_CELL_GAP = 22` with full provenance comment referencing the stale 43=(42+1) origin, the /068→/069/070 timeline, and the single-symbol cell rationale: PASS

### CR3 — expected_gap guard on per-cell combinatorial_purged_cv call

`run_baseline_v3.py:~1602-1609` — `combinatorial_purged_cv` call passes `expected_gap=PER_CELL_GAP`: PASS. Guard comment explains the /083 Critic FINAL `1116124` Rec #2 mandate. The constant cannot silently drift again.

### CR4 — Stale literals corrected

- Line ~2539: runtime error message now references `[sym for _, sym in V3_MODELS]` dynamically — no hardcoded "88" or contradictory gap value: PASS
- Line ~2610-2611 (the gap print): `f"Gap: {REQUIRED_GAP} (= (21+1)*3; iter-v3/084 REVERT /083 FILUSDT expansion; 3-sym universe BCH+LDO+TRX; timeout UNCHANGED 10080 min)"` — uses the live constant, correct 3-symbol narrative, no internal contradiction: PASS

### CR5 — V3_MODELS = 3 symbols (BCH/LDO/TRX), FILUSDT dropped

`run_baseline_v3.py:170-174` → V3_MODELS contains exactly ("A (BCHUSDT)", "BCHUSDT"), ("C (LDOUSDT)", "LDOUSDT"), ("D (TRXUSDT)", "TRXUSDT"): PASS

### CR6 — REQUIRED_GAP = 66 in validation_v3.py

`src/crypto_trade/strategies/ml/validation_v3.py:65` → `REQUIRED_GAP: int = (21 + 1) * 3  # 66` with /084 narrative comment: PASS

### CR7 — _verify_label_leakage_gap pre-flight

`run_baseline_v3.py:1050-1056` — formula-driven assertion `(timeout_candles+1) * len(V3_MODELS) == REQUIRED_GAP`; with 3-symbol V3_MODELS and REQUIRED_GAP=66 this evaluates to 22×3=66==66: PASS. Inline comment at call site (line 2556) updated to iter-v3/084.

### CR8 — Config-accretion check (11/11 knobs, all /059-canonical)

`run_baseline_v3.py:902-941` — All 11 knobs listed: V3_MODELS symbols=("BCHUSDT","LDOUSDT","TRXUSDT"), REQUIRED_GAP=66, DEFAULT_ATR_MULTIPLIERS=(2.0,1.0), V3_ATR_MULTIPLIERS_PER_SYMBOL={}, zscore_threshold=2.0, adx_threshold=20.0, adx_threshold_per_symbol={}, vol_scale_floor_per_symbol={}, block_long_for=(), block_short_for=(), enable_per_symbol_drawdown_brake=False. All 11 match /059-canonical. Zero axis delta carved out (this is a baseline restore, not a new axis): PASS

### CR9 — V3_FEATURE_COLUMNS = 14-feature /059 anchor stack

`src/crypto_trade/features_v3/__init__.py:263` → `V3_FEATURE_COLUMNS: tuple[str, ...] = V3_FEATURE_COLUMNS_TOP_N`. `V3_FEATURE_COLUMNS_TOP_N` contains exactly 14 features: the BASELINE_V3 /059 anchor (adx_14 removed at /064 closeout; range_efficiency_50 removed at /077; /082 funding family reverted at /083). _verify_feature_columns asserts len==14, funding absent, vwap_dev_50/tbr_zscore_30 absent, regime_momentum_signed_5d present, sym_vs_btc_ret_7d present, ret_skew_50 present: PASS

### CR10 — Track isolation

`grep -r "from crypto_trade.features " src/crypto_trade/features_v3/` returns only comments and docstring text (no import statements): PASS

### CR11 — Test suite

`uv run pytest tests/strategies/ml/ tests/features_v3/ tests/test_lookahead_embargo.py`: 427 passed, 3 skipped (unrelated). Matches brief Section 11 claim exactly: PASS

Specific test regression coverage for /084's fix:
- `test_per_cell_pbo_synthetic.py`: PER_CELL_GAP=22 in the test was already correct (runner was out of sync; now in sync): 4 PASS
- `test_cpcv_embargo_assert.py`: N_SYMBOLS=3, CORRECT_GAP=(21+1)×3=66, REQUIRED_GAP==66 assertion: 7 PASS
- `test_v3_feature_count.py`: 14-feature count, all baseline features present, prohibited features absent: 8 PASS

### CR12 — Ruff

`uv run ruff check run_baseline_v3.py src/crypto_trade/strategies/ml/validation_v3.py`: All checks passed: PASS

### CR13 — Commit SHAs verified

All four SHAs cited in Section 11 exist in the repo:
- EDA: `401de40` — analysis(iter-v3/084): config audit + anchor-staleness EDA
- Brief: `c18a2dc` — docs(iter-v3/084): research brief
- Setup: `1073f32` — feat(iter-v3/084): PER_CELL_GAP 43->22 + FILUSDT revert
- SHA-backfill: `f08709b` — docs(iter-v3/084): backfill SHA block in Section 11

### CR14 — Data freshness

Kline CSVs (8h.csv) for BCHUSDT, LDOUSDT, TRXUSDT: close_time age 8.5h — within the 16h staleness threshold: PASS (FRESH, no re-fetch needed before Phase 6)

v3 parquets (`data/features_v3/`): BCHUSDT, LDOUSDT, TRXUSDT parquets exist and are newer than their respective CSVs (age ~2.4-2.5h, regenerated at /083 Phase-6): PASS. No Phase-6 re-generation required — the runner's feature pipeline will regenerate parquets at Phase-6 launch unless `--skip-features` is passed. Standard Phase-6 launch (without `--skip-features`) will re-gen from the fresh CSVs.

---

## One Variable at a Time — Confirmation

iter-v3/084 changes exactly ONE methodology artifact (`PER_CELL_GAP` 43→22 + the `expected_gap` guard) bundled with a mandatory baseline restore (FILUSDT drop, REQUIRED_GAP revert). This is a REFERENCE / METHODOLOGY iteration, not an axis; no axis research is declared. The bundled methodology fix + baseline restore is the established pattern (per /077, /079, /083 precedents). Single-change discipline: PASS

---

## Summary

All 10 mandatory brief sections PASS. All 14 code-readiness checks PASS. Tests 427/427 non-skipped green. Ruff clean. Data fresh. Commits traceable.

Phase 6 is authorized to proceed with:
```
uv run python run_baseline_v3.py --exploration --clean-oof --n-trials 35
```
Wall-clock estimate: ~0.74h. Hard cap: 2h.
