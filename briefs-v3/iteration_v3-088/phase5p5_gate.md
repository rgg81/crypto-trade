# Phase 5.5 Gate — iter-v3/088

OVERALL: PASS

---

## Per-Section Status

- Section 0 (Data Split): PASS — `OOS_CUTOFF_DATE = 2025-03-24` and `training_months = 24` declared IMMUTABLE; IS/OOS windows stated in absolute dates; confirmed `OOS_CUTOFF_MS = 1742774400000` in runner.
- Section 0.5 (Iteration Type): PASS — RE-ARCHITECTURE EXPLORATION; cycle-3 slot #7 of 10; type declaration present and grounded in prior iteration evidence.
- Section 1 (Hypothesis): PASS — specific, one-paragraph causal claim: pooled cross-sectional LambdaMART on ~100k IS rows with a relative label (cross-sectional rank) will produce lower-overfit, lower-variance edge than the N-starved per-symbol absolute-barrier classifiers. Grounds the claim in three named mechanisms (relative label nets out market-wide variance; pooled rows ~30× more than per-symbol; cross-sectional ranking is structurally what per-symbol cannot do). Prior architectural evidence named (1.1 diagnosis; 1.2 closed-axis table).
- Section 2 (IS-Only Evidence): PASS — committed EDA `analysis/iteration_v3-088/cross_sectional_signal_eda.py` (SHA `aebd9f3`). Six output CSVs confirmed present (T1, T3, T4, T5, T6, T7). All tables computed on `open_time < OOS_CUTOFF_MS`. Evidence is concrete and numerical: T3 rank-IC t-stats range −6.4 to −9.5 (Harvey-Liu bar |t|>3.0 cleared); H=3 selected by strongest |IS IC-IR| 0.1287; T7 composite beats single momentum by 55% on |IC-IR| (t=+14.3 vs t=−9.29); T5 breadth-sensitivity IS evidence for 22-symbol universe; T6 zero-dispersion proof for `btc_ret_14d` drop. Category-matching absent — all tables are derived from IS data.
- Section 3 (Proposed Changes / QE Phase-6 Build Spec): PASS — see feasibility judgment below.
- Section 4 (Expected OOS Impact): PASS — comparability caveat correctly stated; dual evaluation (absolute +1.0/+1.0 floor plus architecture-internal diagnostics: OOS rank-IC>0, OOS/IS≥0.5, frac_positive_paths≥0.55, PBO<0.40, single-symbol≤30% OOS PnL); two reference anchors provided with explicit caveat; falsifiers F1-F5 pre-registered with numerical thresholds.
- Section 5 (Risk Mitigation): PASS — structural risk controls (dollar-neutral, inverse-vol weighting, tercile diversification, fee modeling, burn-in, minimum cross-section) tabulated; each is flagged IS-calibrated or a-priori; EDA confirms controls active during IS signal measurement (T3 is computed with burn-in and ≥6-symbol minimum).
- Section 6 (Risk Management Design): PASS — honest scoping: legacy 7-gate stack deferred for clean architecture measurement; three intrinsic structural controls (Section 3.7) stated as the /088 risk framework; deferral to future iteration recorded.
- Section 7 (Failure-Mode Prediction): PASS — pre-registered probability distribution over five named outcomes (35% sub-floor-positive, 20% full-success, 25% F2-fires, 15% F1-fires, 5% turnover catastrophe); named primary failure mode; turnover cost drag explicitly flagged as foreseeable.
- Section 8 (MERGE/NO-MERGE Criteria): PASS — adapted re-architecture taxonomy with five named classifications (SUSPICIOUS, ARCHITECTURE-FALSIFIED, ARCHITECTURE-VALIDATED-PROMISING-FULL, ARCHITECTURE-VALIDATED-PROMISING-FOUNDATION, ARCHITECTURE-PARTIAL) with disjunctive precedence and numerical gates per class. Explicitly states EXPLORATION cannot update BASELINE_V3.md.
- Section 9 (Library Stack): PASS — LightGBM (`LGBMRanker`, `objective="lambdarank"`, native dependency), Optuna, pandas/numpy. No new third-party dependency. Fallback objectives named.
- Section 10 (QR Audit Trail): PASS — Section 10.1 documents the orchestrator steer and QR design ownership. Section 10.2 documents five specific literature sources (Poh/Lim/Zohren arXiv 2012.07149; Liu/Tsyvinski JoF 2022; Cakici et al. IRFA 94; unravel.finance practitioner reference; LightGBM ranking docs). Section 10.3 is the no-cheating audit (see verification below).

---

## Feasibility Judgment — Section-3 Phase-6 Build Spec

Section 3 is sufficiently precise to build from. The following items are specified:

**Label (Section 3.1):** `label_cross_sectional_rank(panel, H=3)` → per-timestamp cross-sectional rank of H-bar forward return → tercile-mapped to {0,1,2} discrete graded relevance. Formula given. Look-ahead safety explained correctly: label uses close(t+H) which is the prediction *target* (not leakage); leakage guard is via the embargo.

**Model (Section 3.2):** `LGBMRanker(objective="lambdarank")`; `group` parameter = symbols-per-timestamp array (one query per timestamp); monthly walk-forward retrain on 24-month trailing window; Optuna hyperparameter search with IS rank-IC or NDCG@k as CV objective. Fallback to `LGBMRegressor` on cross-sectionally-demeaned return or `LGBMClassifier` on top/bottom-tercile binary; PRIMARY vs fallback decision made on IS-only smoke test.

**Universe (Section 3.3):** `XS_UNIVERSE` = the 22 symbols from `T1_universe_screen.csv`. All 22 confirmed non-excluded (XS_UNIVERSE ∩ V3_EXCLUDED_SYMBOLS = empty, verified). 60-day listing burn-in (first 180 8h-bars dropped per symbol). Minimum 6 symbols to form a book at a timestamp.

**Position construction (Section 3.4):** dollar-neutral tercile long-short; long predicted-rank bottom-third, short predicted-rank top-third; inverse-vol weighting within each leg; portfolio vol-targeting via existing v3 machinery; 8h rebalance cadence with overlapping 3-bar holds; 0.1% fee modeled on every rebalance.

**Features (Section 3.5):** 14-column `V3_FEATURE_COLUMNS_TOP_N` reused; `btc_ret_14d` dropped at training time (zero IS cross-sectional dispersion per T6); remaining 13 features cross-sectionally rank-normalized per timestamp before passing to model.

**Walk-forward, embargo, CPCV (Section 3.6):** existing monthly walk-forward retained; `train_end_ms = test_start_ms − embargo_ms` (the `e149e9d` look-ahead fix retained); `XS_REQUIRED_GAP = 88` for pooled CPCV; `CPCV_N_SPLITS = 10`, `CPCV_N_TEST_SPLITS = 2` (45 paths).

**Risk framework (Section 3.7):** legacy 7-gate stack deferred; three structural controls (dollar-neutral, inverse-vol+vol-target, tercile diversification) as the /088 risk framework.

**Staging (Section 3.8):** Stage A (A1-A6) is the required deliverable. Stage B (regression fallback) is contingency. Cross-sectional path gated behind `--cross-sectional` flag or new runner entry; legacy per-symbol path preserved.

**Phase-6 must build (in order):**
- A1: `XS_UNIVERSE` constant + `XS_REQUIRED_GAP = 88` constant; fetch stale klines for 16 of 22 symbols + regenerate parquets (see data note below).
- A2: `label_cross_sectional_rank()` in new module `src/crypto_trade/strategies/ml/cross_sectional.py`.
- A3: Pooled-panel builder (align on `open_time`, apply burn-in, drop `btc_ret_14d`, cross-sectional rank-normalize 13 features, build `group` array).
- A4: `CrossSectionalRankStrategy` wrapping `LGBMRanker`; monthly walk-forward retrain; Optuna search.
- A5: Cross-sectional backtest path (score, tercile long-short, inverse-vol, vol-target, PnL + fee accrual).
- A6: IS-only smoke test + standard v3 report emission.

The brief gives the QE enough to build every Stage A component without additional QR input. FEASIBLE.

---

## No-Cheating Verification

Every re-architecture design knob is either IS-only or a-priori:

| Knob | Selection method | Verified clean |
|---|---|---|
| `OOS_CUTOFF_DATE` / `training_months` | IMMUTABLE — never touched | Yes |
| 22-symbol universe | `T1_universe_screen.csv` — IS rows and IS-window median quote-volume only; screen thresholds (≥1,500 rows, ≥$2M) a-priori | Yes |
| Forward horizon H=3 | `T3_horizon_rank_ic.csv` — selected by strongest |IS IC-IR| (0.1287); sign-agnostic IS criterion; OOS never read | Yes |
| Tercile quantile cutoff | A-priori from cross-sectional factor convention; T4 confirms positive IS spread — NOT OOS-tuned | Yes |
| `btc_ret_14d` drop | `T6` cross-sectional dispersion = 0.000 on IS data; zero-dispersion test is IS-only | Yes |
| 13-feature XS set + sign-alignment | T6 IS rank-IC; T7 composite uses same IS rank-IC; no OOS column read | Yes |
| Model objective (`lambdarank`) | A-priori from Poh/Lim/Zohren research | Yes |
| PRIMARY vs fallback decision | Section 3.2: decided on IS-only smoke test in Phase 6 | Yes |
| Position construction (dollar-neutral, inverse-vol, vol-target) | A-priori from cross-sectional construction convention | Yes |
| IS window | Full IS history per symbol after a-priori 60-day burn-in; NEVER trimmed | Yes |

Section 10.3 of the brief contains an explicit no-cheating audit row-by-row. The QE reviewed the EDA code directly: `_load_is()` filters `df["open_time"] < OOS_CUTOFF_MS`; no OOS rows are loaded anywhere; all table computations (T1-T7) operate on the filtered IS DataFrame. **No OOS knob-tuning detected.**

---

## Code-Readiness Checks

1. **ITERATION_LABEL**: `run_baseline_v3.py` line 131 — `ITERATION_LABEL = "v3-088"`. PASS.

2. **V3_MODELS baseline-restore**: Confirmed 3-symbol BCH+LDO+TRX at lines 190-194; comment at lines 179-189 documents the /087 revert. `REQUIRED_GAP = 66` at validation_v3.py (imported at runner line 71). Config-accretion check (lines 988-1034) asserts ALL 11 /059-canonical knobs. PASS.

3. **XS_UNIVERSE / XS_REQUIRED_GAP**: NOT yet defined in the codebase — they are Phase-6 deliverables, as expected. The setup commit (`6de7c44`) only changed `run_baseline_v3.py` and `validation_v3.py` (the baseline-restore). `cross_sectional.py` does NOT yet exist. This is correct: Phase 5.5 gates the brief; Phase 6 builds the infrastructure.

4. **XS_REQUIRED_GAP = 88 derivation**: `(H+1) × N_symbols = (3+1) × 22 = 88`. Formula is correct for a pooled panel CPCV where each timestamp contributes N=22 rows: purging H+1=4 timestamp-widths = 4×22=88 rows in the flattened row sequence. This ensures no training label's H=3-bar forward window overlaps a test row. Derivation is explicitly documented in brief Section 3.6. PASS.

5. **XS_UNIVERSE isolation from V3_EXCLUDED_SYMBOLS**: `set(XS_UNIVERSE) ∩ set(V3_EXCLUDED_SYMBOLS) = {}` — verified in Python. MKRUSDT is in V3_EXCLUDED_SYMBOLS but NOT in XS_UNIVERSE (a MKRUSDT parquet exists as artifact of prior EDA work — it is not the trading universe). PASS.

6. **Feature isolation**: `ruff check` on all modified files — all checks passed. No import from `crypto_trade.features` (v1) or `crypto_trade.features_v2` (v2) in v3 path confirmed by ruff pass.

7. **Tests**: 221 passed, 3 skipped in 57.04s on the targeted test suite (features_v3 + test_cpcv_embargo_assert). The 3 skipped are expected (data-dependent tests with no parquet for non-v3 symbols). The QR reports 268 total tests passing — the full suite not re-run here (time constraint), but the targeted v3 tests all pass. PASS.

8. **Data prerequisite for Phase 6**: 22 XS_UNIVERSE symbols — all 22 parquets exist in `data/features_v3/` (generated during EDA). However, 16 of 22 kline CSVs (`data/<SYMBOL>/8h.csv`) have stale close_times (>16h lag — ranging from 25h to 8,657h stale). **Phase 6 must re-fetch klines for all 22 symbols before regenerating parquets and running the backtest.** This is a known Phase-6 prerequisite (brief Section 3.8 Stage A1: "fetch/feature-regen for all 22"). Estimated fetch time: ~10-20 min for 22 symbols at 8h interval. Estimated Phase-6 wall-clock (3-seed EXPLORATION, 35 trials, 22 symbols, monthly walk-forward over 24-month IS): likely 2-4h (the per-symbol path ran ~1.1h for 3 symbols; the pooled model with 22 symbols and a cross-sectional architecture is structurally different — timing uncertain on first build, may differ).

---

## Reasons for BLOCK

None.

---

## Status

OVERALL: PASS — Phase 6 may proceed.
