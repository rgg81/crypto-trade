# Phase 7.5 Critic Review — iter-v1/019

OVERALL: EXPLORATION-PROMISING — direction-aware BTC-trend gate flipped ETH per-cohort drag with mechanism-level LOAD-BEARING confirmation; conditional carry-forward to /027 substrate

## Iteration Type
TYPE: EXPLORATION (cycle-3 #4 of 10; per-cohort-specialization-ETH; NEW 10th axis family)

## Per-Check Status

### Check 1 — Look-Ahead Audit: PASS
`walk_forward.py:113` carries `train_end_ms = test_start_ms - embargo_ms` UNCHANGED. 4 mandated regression tests at `tests/test_lookahead_embargo.py` lines 120/163/232/261. New gate at `risk_v2.py:1346-1416` uses `np.searchsorted(btc_open_times, trade.open_time, side="right") - 1` — past-only by construction. 42-bar warmup floor prevents underflow.

### Check 2 — Embargo Width: PASS
Iteration introduces no labeling or walk-forward changes. Single-symbol cohort = n_symbols=1; 7-day timeout / 8h cadence = 22 candle gap; foundation guard intact.

### Check 3 — Multiple-Testing Correction: INFORMATIONAL
Per `feedback_v3_dsr_mode_artifact.md`, EXPLORATION-mode DSR/PSR are structural artifacts. DSR IS −79.77 / OOS −21.07; PSR_monthly_vs_0 OOS **0.7793** (above PROMISING-INERT floor 0.40); PSR_monthly_vs_1 OOS 0.4042. PBO N/A (single-seed). For EXPLORATION, Check 3 FAILs do NOT trigger BLOCK.

### Check 4 — IC Correlation: PASS (vacuous; no new features)
V1_FEATURE_COLUMNS_PRUNED (40 cols) unchanged.

### Check 5 — ADF Stationarity: PASS
40 features tested; 2 baseline-precedent exceptions (`cal_hour_norm` bounded calendar feature; `vol_atr_14` raw_pass True / bonferroni_pass False at p=0.0044). INFORMATIONAL per brief Section 4 F4.

### Check 6 — Pareto Dominance: N/A (single-seed EXPLORATION)
Deferred to /027 multi-seed CONFIRMATION per brief Section 7.

### Check 7 — Reproducibility: PASS
HEAD `b33c96c`; `feature_columns = list(V1_FEATURE_COLUMNS_PRUNED)` explicit at `run_baseline_v1.py:1019`; ENSEMBLE_SEEDS literal at line 102; gate constants pinned (lookback=42, threshold=8.0, enabled=True) at lines 151-153. 159 IS / 42 OOS trades all ETHUSDT. Spot-check PASS.

### Check 8 — Hypothesis-Implementation Alignment: PASS
Brief H1 (direction-aware counter-trend kill) ↔ `risk_v2.py:1396-1398` `(direction == -1 and btc_ret_pct > threshold) or (direction == 1 and btc_ret_pct < -threshold)` 1:1 match. `assert set(symbols) == {"ETHUSDT"}` guard at `run_baseline_v1.py:1381` prevents universe drift.

### Check 13 — Anti-Pattern Static Scan: PASS
A1-A14 all clean. A8 deadlock-impossibility: gate at `risk_v2.py:1378-1416` provably stateless (pure loop; mutates only local `stats`; warmup floor falls through to pass-through). A4 cohort selection traceable to brief Section 0.3.

### Check 14 — Axis Family Validation: PASS
Declared `per-cohort-specialization-ETH` NEW 10th family. src/ diff confined to `run_baseline_v1.py` dispatch + helper-layer cross-import. Cross-track import (`risk_v2`) is HELPER-LAYER not FEATURE-LAYER — permitted under v1 track-isolation rule. Rotation valid: prior 5 distinct (labeling /014, labeling-CONF /015, sample-weighting /016, universe /017, per-cohort-specialization-LINK /018).

## Verdict-Cell Selection

Per brief Section 8 + F-AXIS-MECHANISM LOAD-BEARING evaluation order (Section 4 line 521 / LM Master §9: F-AXIS #3 evaluates BEFORE F1):

- **F-AXIS-MECHANISM #1** dispatch correctness: PASS — 100% ETHUSDT
- **F-AXIS-MECHANISM #2** trade-count + PnL: PASS — IS 159 ∈ [80,200], OOS 42 ∈ [25,90]
- **F-AXIS-MECHANISM #3 (LOAD-BEARING)** gate fire-rate: PASS — IS **19.50%** (31/159) ∈ [10%, 30%]; OOS **14.29%** (6/42) ∈ [5%, 35%]
- **F1** ETH OOS Sharpe Δ vs ETH-in-pool +0.0503: **+0.6487 → PROMISING band** (Δ ≥ +0.20)
- **F3** ETH IS Sharpe Δ vs ETH-in-pool −0.1022: **+0.0718 → INERT band** [-0.20, +0.20]
- **F5** PSR_monthly_vs_0 OOS = 0.7793 vs catastrophic floor 0.10: PASS
- **F7** sign-agreement: IS −0.03 / OOS +0.70 technical sign-mismatch. **Critic accepts LM Master §3 noise-floor interpretation**: IS PnL −1.77 USD across 159 trades = −0.01% per trade, operationally indistinguishable from zero. Treat as N/A at |IS Sharpe| << 0.10. The brief's Section 4 internal inconsistency (line 499 "F7 strongest" vs line 521 "F-AXIS #3 LOAD-BEARING") is flagged as process recommendation #2.

Hierarchy walkthrough: no NEGATIVE-DISPATCH (F-AXIS #1 PASS), no NEGATIVE-OVER-KILL/UNDER-FIRE (F-AXIS #3 inside band), no NEGATIVE-IS-COLLAPSE (F3 INERT), no NEGATIVE-INTRINSIC/CATASTROPHIC (F1 +0.65 far above any negative threshold), no PROMISING-INERT-no-effect (|F1| = 0.65 >> 0.05).

**Verdict cell: Section 8 row 1 = PROMISING.**

## PROMISING-MECHANICAL Adjacency Check

Per brief Section 6.7 + `feedback_promising_mechanical_subtype.md`:

Per LM Master Phase 7.4 §2: trade_id Jaccard between /019 kept-trade roster and v1-baseline ETH-in-pool roster = **0.04** (combined; 0.0380 IS, 0.0250 OOS; pre-gate full roster vs baseline = 0.0566).

0.04 << 0.50 → **NEW SIGNAL SOURCE (compoundable)**. Retrained Model G generates a substantially different ETH trade roster than pool-trained baseline (94% disjoint pre-gate; 96% disjoint post-gate). Gate is NOT filtering an existing roster; it is filtering a freshly-trained roster.

**Classification: NOT PROMISING-MECHANICAL.** /019 ETH+gate bundleable additively at /027 CONFIRMATION.

## Recommendations to QR (process-level)

1. **engineering_report.md missing**. Brief Section 10.1 / 10.4 step 3 mandate `reports-v1/iteration_v1-019/engineering_report.md`; /018 precedent shows it as canonical Phase 7 summary. Data artifacts (comparison.csv, trades.csv, dsr.json, ic_matrix.csv, adf_test.csv, per_symbol.csv) all present and sufficient for the 8-check audit, so this is NOT a methodology-blocker — but the brief cites "Critic /017 Rec #2" as binding. **Phase 8 closeout must write engineering_report.md retrospectively from existing CSVs (zero backtest re-run)** and commit to `reports-v1/iteration_v1-019/`. Future briefs should make Phase 6 vs Phase 7 timing unambiguous.

2. **F7 sign-agreement vs F-AXIS-MECHANISM #3 hierarchy inconsistency**. Brief Section 4 line 499 ("F7 strongest") and Section 4 line 521 ("F-AXIS #3 LOAD-BEARING") cannot BOTH be the strongest. LM Master §3 noise-floor argument is principled but post-hoc. Pre-register at Phase 5: "When |anchor IS Sharpe| < 0.10, F7 is N/A and F-AXIS-MECHANISM #3 supersedes."

3. **/027 CONFIRMATION cross-correlation pre-validation**. Per LM Master Phase 7.4 §4, multi-seed regression target for /019 = +0.45 to +0.55 (vs single-seed +0.6990). At /027 bundle math (LINK +0.80 + ETH+gate +0.50 + others), projected portfolio Sharpe lift +0.85 to +1.05 assumes cross-correlation between LINK-only and ETH+gate roster Sharpe paths < 0.40 — currently un-validated. Pre-register a 10-seed CONFIRMATION rejection threshold if cross-correlation > 0.60.

## Path Forward (advisory on PROMISING)

Verdict is PROMISING; Path Forward is advisory. Per LM Master Phase 4.5 §9 + brief Section 11.7: **/020 = BTC-only specialization** (convergent recommendation from Critic + LM Master + brief).

Cycle-3 cadence after /019 PROMISING = 4/10 EXPLORATIONs complete; 6 more EXPLORATIONs needed before /027 CONFIRMATION. Suggested cycle-3 #5-7 axes from families NOT recently used:

1. **BTC-only specialization** — family `per-cohort-specialization-BTC` — BTC IS catastrophic rotation vs OOS positive; cohort isolation tests intrinsic vs pool-borrowed edge.

2. **DOT-only specialization** with optional TBR-momentum gate — family `per-cohort-specialization-DOT` — DOT IS +96.07 at /017 catastrophic-positive rotation; tests intrinsic IS-driven edge.

3. **2-symbol pooled cohort BTC+ETH separated** — family `per-cohort-pooled-2sym` (NEW family) — tests "pooling helps" vs "pooling masks" hypothesis underlying /018-/019 cohort isolation success.

## BLOCK-PENDING-FIX Rerun Protocol

N/A — verdict is EXPLORATION-PROMISING. /019 closes; /020 advances per Path Forward.
