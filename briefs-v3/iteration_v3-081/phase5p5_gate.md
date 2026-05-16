# Phase 5.5 Gate — iter-v3/081

OVERALL: PASS

---

## Per-Section Status

- **Section 0 (Data Split Declaration)**: PASS — `OOS_CUTOFF_DATE = "2025-03-24"` at runner line 84; `TRAINING_MONTHS = 24` at runner line 85; both confirmed IMMUTABLE, unchanged vs /059 baseline. IS window = all available data → 2025-03-24; OOS window = 2025-03-24 → present. Symbol universe = BCHUSDT/LDOUSDT/TRXUSDT (V3_MODELS lines 154-157). Sacred constants verbatim in brief Section 0.
- **Section 0.5 (Iteration Type Declaration)**: PASS — `TYPE = CYCLE 2 CONFIRMATION (NOT EXPLORATION)` stated explicitly. Cadence verified: 10 separate EXPLORATIONs /071-/080 listed in brief Section 0.5.1 table; 10th EXPLORATION (/080) was NOT collapsed into /081 (separate diary SHA `f5d2f02`). Run mode: DEFAULT (NO `--exploration` flag) → `ENSEMBLE_SIZE=10` via `CONFIRMATION_ENSEMBLE_SIZE`. `--n-trials 35`. Wall-clock target ≈3.5h; HARD CAP 6h per cadence discipline.
- **Section 1 (Hypothesis)**: PASS — ONE sentence, specific and testable: genuine /059 canonical config re-run at unified 10-seed reproduces IS +1.0894 / OOS +0.5791 within ±0.20 monthly-Sharpe tolerance on BOTH axes; if outside tolerance, Section 8 re-anchor logic fires. Falsifier (outside ±0.20 on either axis) and outcome branches (CONFIRMED / RE-ANCHOR-UP / DRIFT-NO-ANCHOR / METHODOLOGY-FAIL) pre-registered.
- **Section 2 (IS-Only Numerical Evidence)**: PASS — EDA committed at SHA `be0ccf5` (ruff-clean `f9ddea5`). Script: `analysis/iteration_v3-081/baseline_integrity_audit.py`. Outputs: T1-T4 CSVs all present in `analysis/iteration_v3-081/`. T1 audited 9 behavior-affecting config knobs between /059 setup commit `20095a8` and HEAD; found exactly 1 illegitimate accretion (`vol_scale_floor_per_symbol={"TRXUSDT": 0.5}` from iter-v3/061 INERT EXPLORATION). T2 traced the /061 floor lifecycle via git history; confirmed no `v0.v3-061` tag, no CONFIRMATION-MERGE carriage. T3 distinguished the /059 CONFIRMATION target (10-seed, no floor, IS +1.0894 / OOS +0.5791) from the /077//080 EXPLORATION-MODE-REFERENCE (3-seed, floor present). T4 pre-registered the re-validation decision logic. No new backtest run; no sacred-constant change; git-archaeology only. Evidence is reproducible and produces concrete numbers.
- **Section 3 (Proposed Changes)**: PASS — Enumerated Sub-fixes 1-6. Sub-fix 1: `vol_scale_floor_per_symbol={}` in `_build_v3_model` (runner line 1729 — CONFIRMED). Sub-fix 2: runner pre-flight `expected_floor_dict: dict[str, float] = {}` (runner line 808 — CONFIRMED). Sub-fix 3: `ITERATION_LABEL = "v3-081"` (runner line 131 — CONFIRMED). Sub-fix 4: `grep -rn "vol_scale_floor_per_symbol" tests/` returns only `test_per_symbol_vol_scale_floor.py` which constructs its own `RiskV2Config` (does NOT call `_build_v3_model`) — no runner-config assertion to update, NO CHANGE required. Sub-fix 5: no other changes (features, universe, labeling, risk stack, ensemble all UNCHANGED vs /059). Sub-fix 6: run command `uv run python run_baseline_v3.py --clean-oof` verified against argparse (lines 2336, 2359).
- **Section 4 (Expected OOS Impact + Falsifiers)**: PASS — Headline prediction table with ±0.20 IS/OOS tolerance; per-symbol expectations; behavioral-effect predictor (13 IS TRX `weight_factor` values shift off the 0.5 floor; BCH/LDO weight_factors bit-identical); SUSPICIOUS gate (OOS/IS ratio > 3.0 LOCKED); 11-gate falsifier table (G.1-G.11) fully pre-registered with specific thresholds and action-on-fail.
- **Section 5 (Risk Mitigation)**: PASS — Unchanged 7-primitive /059 risk stack enumerated. The Sub-fix 1 revert is itself classified as a risk-mitigation correction (removes TRX-specific 0.5 vol-floor override, returning TRX to the global 0.3 floor). No new risk primitive at /081 (CONFIRMATION validates; does not explore). Simulated historical effect of the revert cited from the /061 EDA (±0.008 IS wpnl / ±0.47 OOS wpnl — near-zero).
- **Section 6 (Risk Management Design)**: PASS — Labeling (triple-barrier ATR 2.0/1.0, 21-candle timeout), position sizing (vol-scaled clip, global floor 0.3 / ceiling 1.0), cooldown (4 candles), fee (0.1%), CPCV parameters (n_paths=45, embargo=27, REQUIRED_GAP=66), walk-forward embargo (22 candles via `compute_embargo_candles(10080,480)`, `train_end_ms = test_start_ms - embargo_ms`) all stated. Walk-forward lookahead bug confirmed FIXED (commit `e149e9d`, /058 RE-ANCHOR) — NOT cited as live.
- **Section 7 (Failure-Mode Prediction)**: PASS — 4 probability-weighted failure-mode table (CONFIRMED ~62%, RE-ANCHOR-UP ~16%, DRIFT-NO-ANCHOR ~17%, METHODOLOGY-FAIL ~5%). Single most-plausible narrative (mixed-drift: OOS lifts via data-extent while IS drifts via Optuna TPE stochasticity — the /039//070 IS-down/OOS-up pattern) described with expected metric signatures. Secondary failure mode (vol-floor revert wiring failure caught by pre-flight assertion) pre-registered. Forward-looking, verifiable against Phase 8 diary.
- **Section 8 (MERGE/NO-MERGE Criteria — LOCKED)**: PASS — NO MERGE path (cycle 2 = 0 PROMISING); the only locked decision is CONFIRM vs RE-ANCHOR. Section 8.1 (CONFIRMED → BASELINE_V3.md UNCHANGED, outcome label CONFIRMATION-REVALIDATE), 8.2a (RE-ANCHOR-UP — BOTH-IS-AND-OOS-improve + hard-blocking gates PASS → BASELINE_V3.md ratchets), 8.2b (DRIFT-NO-ANCHOR — single-axis or no improvement → /059 stays canonical with staleness note), 8.3 (METHODOLOGY-FAIL → iteration INVALID), 8.4 (no MERGE path explicit), 8.5 (BASELINE_V3.md code-config edit regardless of outcome) all stated. LOCKED at brief-lock (setup commit `5d42c4a`). Cannot be retroactively renegotiated.
- **Section 9 (Library Stack Declaration)**: PASS — Python 3.13, lightgbm 4.6.0, optuna 4.8.0, numpy 2.2.6, pandas 3.0.0, scikit-learn 1.8.0, scipy 1.17.0, statsmodels 0.14.6, pyarrow 23.0.1 — pinned, no fallbacks. In-tree CPCV/PBO/PSR implementation in `validation_v3.py`, unchanged at /081. No new integration test required (no new methodology field or output schema). Data-freshness pre-flight and re-fetch protocol stated (Section 9.3). Run command confirmed.
- **Section 10 (QR Audit Trail)**: PASS — Explains why /081 is a re-validation (cycle 2 = 0 PROMISING), why the config is the genuine /059 canonical config (T1/T2 EDA driven), why /081 is the first genuine /059 re-measurement (cycle 1's /070 also ran with the /061 floor active — T2 row 8). Memory-rule compliance table (Sections 10.2) and /080 Critic recommendations addressed (Section 10.3). Commit chain SHA-backfilled (Section 10.5). Cannot be retroactively renegotiated statement at Section 10.4.

---

## Code-Readiness Checks

| Check | Status | Evidence |
|---|---|---|
| `ITERATION_LABEL == "v3-081"` | PASS | runner line 131 |
| `V3_MODELS` = BCH/LDO/TRX (3 symbols) | PASS | runner lines 154-157 |
| `/061 vol-floor revert: _build_v3_model vol_scale_floor_per_symbol={}` | **PASS — CONFIRMED** | runner line 1729; explicit `{}` with provenance comment |
| `expected_floor_dict: dict[str, float] = {}` (pre-flight assertion) | **PASS — CONFIRMED** | runner line 808; asserts `{}`, consistent with Sub-fix 1 |
| Pre-flight assertion wiring: `p12_strat_check.config.vol_scale_floor_per_symbol != {}` raises `ValueError` | PASS | runner lines 809-816 |
| CONFIRMATION run mode (no `--exploration`) → `ENSEMBLE_SIZE=10` | PASS | runner line 2388-2389; `CONFIRMATION_ENSEMBLE_SIZE=10` (line 93) |
| `ensemble_summary.json` writes `"mode": "confirmation"` | PASS | runner line 2943 |
| `ENSEMBLE_SEEDS` matches BASELINE_V3.md 10-tuple | PASS | runner lines 103-114 |
| `OOS_CUTOFF_DATE = "2025-03-24"` immutable | PASS | runner line 84 |
| `TRAINING_MONTHS = 24` immutable | PASS | runner line 85 |
| `V3_FEATURE_COLUMNS` assertion: exactly 14 features | PASS | runner line 346-352; 14-count gate |
| `vol_adj_autocorr` absent from V3_FEATURE_COLUMNS | PASS | runner lines 356-361 |
| `efficiency_ratio_50` absent from V3_FEATURE_COLUMNS | PASS | runner lines 372-379 |
| `regime_momentum_signed_5d` present | PASS | runner lines 389-392 |
| `--clean-oof` flag exists in argparse | PASS | runner line 2359 |
| No `--exploration` in the brief run command | PASS | brief Section 3 Sub-fix 6 |
| Tests: `uv run pytest tests/features_v3/ tests/strategies/ml/ -q` | **PASS — 403 passed / 3 skipped** | run confirmed |
| Ruff: `uv run ruff check run_baseline_v3.py` | **PASS — All checks passed** | run confirmed |
| `grep -rn "vol_scale_floor_per_symbol" tests/` — no `_build_v3_model` runner-config assertion | PASS — only `test_per_symbol_vol_scale_floor.py` (mechanism test, no `_build_v3_model` call) | Sub-fix 4 verified |

---

## Cadence Verification

10 cycle-2 EXPLORATION precedents confirmed (brief Section 0.5.1):

| Slot | Iter | Verdict |
|---|---|---|
| #1 | /071 | SUSPICIOUS-OOS-DOMINANT |
| #2 | /072 | NEGATIVE |
| #3 | /073 | SUSPICIOUS-OOS-DOMINANT |
| #4 | /074 | INERT-AT-EXPLORATION |
| #5 | /075 | INERT-AT-EXPLORATION |
| #6 | /076 | SUSPICIOUS-OOS-DOMINANT |
| #7 | /077 | INERT-AT-EXPLORATION (PASSIVE-DIAGNOSTIC) |
| #8 | /078 | SUSPICIOUS-OOS-DOMINANT |
| #9 | /079 | NULL-RESULT |
| #10 | /080 | NULL-RESULT (PASSIVE-DIAGNOSTIC) |

**Count: 10/10. Cadence COMPLETE.** /081 is the SEPARATE CONFIRMATION after 10 SEPARATE EXPLORATIONs. The 10th EXPLORATION (/080) was NOT collapsed into /081 (separate diary at SHA `f5d2f02`). Cadence constraint satisfied per `feedback_v3_strict_10_to_1_cadence.md`.

---

## Key Findings

1. **The /061 vol-floor revert is CONFIRMED implemented.** Runner line 1729 has `vol_scale_floor_per_symbol={}` (empty); line 808 has `expected_floor_dict: dict[str, float] = {}`. Both are consistent. The pre-flight assertion will catch any re-introduction of the floor. The `RiskV2Config.vol_scale_floor_per_symbol` field and `risk_v2.py` `_vol_scale` lookup remain in place (backward-compatible mechanism) — only the runner config line is reverted. This is correct.

2. **CONFIRMATION runs DEFAULT mode (10 seeds).** No `--exploration` flag → `CONFIRMATION_ENSEMBLE_SIZE=10` → `ENSEMBLE_SIZE=10` for the run. `ensemble_summary.json` will write `"mode": "confirmation"`, `"ensemble_size": 10`. Gate G.10 will be automatically satisfied.

3. **Tests green, ruff clean.** `uv run pytest tests/features_v3/ tests/strategies/ml/ -q`: 403 passed / 3 skipped. `uv run ruff check run_baseline_v3.py`: all checks passed.

4. **Section 8 NO-MERGE path is explicit.** Cycle 2 produced 0 PROMISING — there is no edge to bundle. The only locked decision is CONFIRMED / RE-ANCHOR-UP / DRIFT-NO-ANCHOR / METHODOLOGY-FAIL. This is correctly stated and cannot be renegotiated post-hoc.

5. **One brief section numbering note (non-blocking).** The brief has 10 sections (0, 0.5, 1–10) with /081-specific additions (Section 11 = forward pointer). The v3 skill mandates 10 mandatory sections (0–9 + Section 10 QR Audit Trail). All 10 mandatory sections are substantively present. No BLOCK.

---

## Run Command

```bash
uv run python run_baseline_v3.py --clean-oof
```

Expected wall-clock: ~3.5h. HARD CAP: 6h per `feedback_v3_cadence_discipline.md`.
