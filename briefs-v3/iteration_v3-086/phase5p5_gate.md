# Phase 5.5 Gate — iter-v3/086

OVERALL: PASS

---

## Per-Section Status

- Section 0 (Data Split): PASS — OOS_CUTOFF_DATE 2025-03-24 and training_months=24 declared immutable; IS/OOS windows stated; IS-data-only EDA confirmed by explicit OOS_CUTOFF_MS filter in both EDA scripts.
- Section 0.5 (Iteration Type): PASS — TYPE: EXPLORATION declared; cycle-3 EXPLORATION #5 of 10; single-axis; 3-seed EXPLORATION-mode; two mandatory /085-closeout non-axis actions itemised.
- Section 1 (Hypothesis): PASS — One sentence hypothesis present ("perp-spot basis encodes leverage/sentiment crowding that the v3 14-feature OHLCV stack cannot see"); economically grounded (Ackerer-Hugonnier-Jermann, AEA 2026, BitMEX 2025); distinct-feed argument quantified (corr(basis_z, funding_z) = 0.22-0.28); honestly concedes the evidence is weak.
- Section 2 (IS-Only Numerical Evidence): PASS — committed EDA at analysis/iteration_v3-086/ (SHA c9bf818); five tabulated checks: T0 coverage/non-degeneracy, T1 Spearman IC, T2 orthogonality, T3 incremental-information, T4 past-only audit; directional probes P1/P2/P3; all load IS rows only (open_time < OOS_CUTOFF_MS, explicit filter in code); CSV outputs committed alongside scripts; negative incremental-information result reported plainly (all 3 symbols negative in T3).
- Section 3 (Proposed Changes + Data-Acquisition Plan): PASS — see detailed assessment below.
- Section 4 (Expected OOS Impact): PASS — two-anchor declaration present and correct (ANCHOR 1 = /084 IS +0.8325 / OOS +0.3322, 3-seed; ANCHOR 2 = /059 10-seed, reserved for /092); honest Δ band [IS -0.10, +0.15 / OOS -0.20, +0.25]; behavioral-effect predictor present (8-20% IS-roster change; < 5% flags saturation); SUSPICIOUS and INERT falsifiers pre-registered.
- Section 5 (Risk Mitigation): PASS — no risk primitive changed; 4 specific basis-feed mitigations stated (NaN containment, z-score clip, OOD gate auto-extension, concentration unchanged); /059-canonical 7-gate stack inherited unchanged.
- Section 6 (Risk Management Design): PASS — /059-canonical 11-knob config-accretion pre-flight asserted at runtime; IS-calibrated thresholds declared; simulated gate-firing effect stated (identical to /059 for the 7 gates, only model probability shifts from 3 new features).
- Section 7 (Failure-Mode Prediction): PASS — four-outcome probability table present (INERT 50%, SUSPICIOUS 25%, NEGATIVE 15%, PROMISING 10%); honest pre-registration of the most likely outcome (INERT); two SUSPICIOUS sub-channels given non-tail weight per /085 closeout mandate; rationale grounded in IS evidence (weak IC + negative T3 incremental).
- Section 8 (Pre-Registered MERGE/NO-MERGE Criteria): PASS — locked classification taxonomy present with disjunctive precedence order (SUSPICIOUS > NEGATIVE > PROMISING > INERT > NULL-RESULT); quantified thresholds for all four outcomes; SUSPICIOUS sub-channels (a)-(d) enumerated including F2 and F3 holding-time gates; PROMISING requires importance >= 30 on at least one member; all Δ vs ANCHOR 1.
- Section 9 (Library Stack): PASS — no new libraries; pure numpy/pandas arithmetic; httpx + csv + zipfile already in stack; pinned versions stated (lightgbm 4.6.0, optuna 4.8.0, numpy 2.2.6, pandas 3.0.0).
- Section 10 (QR Audit Trail): PASS — literature-research path documented (3 sources cited with titles/venues); axis selection logic explicit (OI probed and rejected via history-depth; basis selected because it is the only feed with full IS depth); composed-feature variant EDA-falsified (P3 near-zero IC); no OOS data touched; windows fixed a-priori not swept.

---

## Section 3 — Data-Acquisition Plan Assessment (KEY GATE ITEM)

IMPLEMENTABLE. All five sub-elements verified:

1. Feed + source: spot 8h klines from data.binance.vision monthly ZIP archives (path template documented); /api/v3/klines REST fallback for current month. Matches project-canonical bulk mechanism (src/bulk.py pattern).

2. History-coverage claim verified by EDA and by disk: spot CSVs written by fetch_spot_klines.py prototype are present at data/spot/{BCH,LDO,TRX}USDT/8h.csv with row counts 7037/4358/8642 (+ header = 7038/4359/8643 lines). BCH starts 2019-11-28 (perp IS window 2020-01-01), TRX starts 2018-06-11 (perp IS window 2020-01-15), LDO starts 2022-05-09 (perp IS window 2022-09-22). Every spot series predates its perp IS start. Spot-merge coverage on IS perp rows is 100% (Section 2.1 T0 table + t0_coverage.csv committed).

3. Microsecond normalisation documented and implemented: _to_ms() in fetch_spot_klines.py converts 16-digit microsecond epochs (introduced 2025-01) to milliseconds via val // 1000; this is a load-bearing note in Section 3.2 and must be carried into the production fetch-spot subcommand.

4. Past-only reporting-lag handling: basis(t) = (perp_close[t] - spot_close[t]) / spot_close[t] requires both closes at bar t CLOSE. Every basis feature is computed on basis.shift(1) — bar t uses basis[t-1] and earlier only. Confirmed in basis_v3.py (Step 3 comment: "PAST-ONLY — shift basis one full candle before ALL stats", then b = basis.shift(1) used for all three features). T4 past-only audit CSV confirms bars < K bit-identical for all 3 symbols after a perp_close spike at K=400.

5. QE Phase-6 fetcher spec: Section 3.3 gives a 6-point implementation spec (fetch-spot subcommand, timestamp normalisation, basis_v3.py module, GROUP_REGISTRY entry, adversarial past-only test, data-extent guard). The prototype fetch_spot_klines.py is committed as a direct reference. This is sufficient for a QE to build the production subcommand.

---

## Code-Readiness Checks

1. ITERATION_LABEL: "v3-086" — CONFIRMED (run_baseline_v3.py line 131).

2. V3_FEATURE_COLUMNS_TOP_N = 17 — CONFIRMED (features_v3/__init__.py: 14 /059-anchor features + basis_zscore_30 + basis_momentum_3 + basis_extreme_flag = 17; _verify_feature_columns asserts len == 17 at runtime).

3. funding_regime_momentum_5d ABSENT from feature list — CONFIRMED (not in V3_FEATURE_COLUMNS_TOP_N); ABSENT-assertion present in _verify_feature_columns (raises RuntimeError if found); banned in the features_v3/__init__.py docstring BANNED section.

4. validation_v3.py:594 docstring fix — CONFIRMED. The cpcv_walk_forward_splits docstring now reads "Default gap = REQUIRED_GAP = (timeout_candles+1)*n_symbols = 66 (3-symbol BCH+LDO+TRX universe ... docstring corrected at iter-v3/086 per Critic /085 Rec #3 — the prior text described the reverted iter-v3/069 4-symbol BCH+LDO+TRX+ADA gap=88 era)". The stale "88 4-symbol" text is gone.

5. basis_v3.py look-ahead discipline — CONFIRMED. b = basis.shift(1) is applied at Step 3 before all three feature computations. The z-score, momentum, and sign-persistence are all computed on b (lagged basis), not on basis itself. No look-ahead.

6. Spot-merge geometry — CONFIRMED. Merge is a left-join on open_time from df to spot (merged = df.merge(spot, on="open_time", how="left")). Missing spot candles produce NaN (handled by LightGBM natively). No forward-fill or backfill that could introduce look-ahead.

7. GROUP_REGISTRY entry — CONFIRMED ("basis_v3": add_basis_v3_features registered in features_v3/__init__.py at line 105).

8. Config-accretion 11-knob _canonical_v059 check — CONFIRMED present (run_baseline_v3.py lines 973-1008); all 11 knobs are /059-canonical; a feature axis is not a RiskV3 knob so the check correctly fires only on RiskV3Wrapper config fields.

9. feature_columns explicit list — CONFIRMED (run_baseline_v3.py line 1821: feature_columns=list(features_for_symbol(symbol))); this is an explicit non-None, non-empty list.

10. Track isolation — CONFIRMED. grep for "from crypto_trade.features " and "from crypto_trade.features_v2" in src/crypto_trade/features_v3/ returns no actual imports (only docstring references). basis_v3.py imports only numpy, pandas, pathlib — fully isolated.

11. Test file test_basis_v3.py — CONFIRMED. 8 test functions present: basis columns appended + close preserved, past-only no-lookahead (the adversarial spike-perturbation test), zscore clip bounds, NaN warmup, GROUP_REGISTRY smoke (reads data/spot/<SYM>/8h.csv via tmp_path), missing cache raises FileNotFoundError, missing symbol column raises KeyError, basis genuinely distinct from close.

12. Test suite pass — CONFIRMED. uv run pytest tests/features_v3/ tests/strategies/ml/ -q: 438 passed, 3 skipped (0 failures). QR reported 223 v3 tests; the full count is 438 tests across the two suites.

13. Ruff check — CONFIRMED. All checks passed on basis_v3.py, features_v3/__init__.py, test_basis_v3.py, run_baseline_v3.py.

---

## Phase 6 Requirements

The QE must build exactly the following before running the backtest:

1. `crypto-trade fetch-spot` CLI subcommand in main.py — `--symbols`, `--interval` (default 8h), `--output-dir` (default data/spot/). Downloads data.binance.vision monthly spot-kline ZIPs; incremental; current month via /api/v3/klines. MUST carry the microsecond normalisation (_to_ms logic from the prototype).

2. Pre-flight data-freshness guard for data/spot/<SYM>/8h.csv — same 16h staleness check as perp CSVs.

3. Feature regen via process_symbol_v3 which calls add_basis_v3_features via GROUP_REGISTRY — requires data/spot/<SYM>/8h.csv to be present BEFORE features are generated. The QR prototype already wrote these files; the QE must ensure they are fresh (<16h) before parquet regen.

Spot data is already on disk (data/spot/{BCH,LDO,TRX}USDT/8h.csv). The QE may use these directly for the backtest run, but must verify data freshness before proceeding.

---

## Status

OVERALL: PASS. All 10 mandatory brief sections present and substantive. Data-acquisition plan is implementable. History-depth claim is verified by disk (spot CSVs present with correct row counts predating each perp IS window). Basis features are look-ahead-clean (basis.shift(1) throughout). /085 mandates executed: funding_regime_momentum_5d dropped and ABSENT-banned; validation_v3.py:594 docstring corrected from "88 4-symbol" to "66 3-symbol". ITERATION_LABEL=v3-086, V3_FEATURE_COLUMNS=17, config-accretion 11-knob check intact. Tests green (438 passed), ruff clean. Phase 6 may proceed.
