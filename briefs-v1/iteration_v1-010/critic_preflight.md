# Phase 6.0 Critic Pre-Flight — iter-v1/010

OVERALL: PASS

## Pre-Flight Checks

### Check 1 (mini) — Brief Look-Ahead Audit: PASS

R5 reads `vol_natr_14` from per-symbol feature parquets keyed on `(symbol, open_time)`. NATR_14 is a bar-close-stable feature (computed from past N=14 candles); the brief Section 2 EDA uses IS-only filter `open_time < OOS_CUTOFF_MS`. In `backtest.py:198-227`, the `r5_natr_lookup` is populated once at backtest init from existing feature parquets (built by `features` subcommand BEFORE the backtest) — no runtime feature regeneration, no forward leak. The dict key is `(symbol, open_time)` matching the candle on which the signal fires; lookup at `backtest.py:430` uses `(sym, ot)` where `ot = int(open_time_arr[i])` of the candle at decision time. Identical timestamp domain. No subtle look-ahead in the R5 path. Brief Sections 1, 2, 3.1, 4 describe past-only mechanics; mini-Check 1 catches obvious cases only — full Phase 7.5 will do the deep trace.

### Check 13 (mini) — Anti-Pattern Static Scan: PASS

Scanned src/ tree against all 14 catalog signatures focused on QE's f316dae+22cf829 diff:

- **A1 (train/test boundary lookahead)**: PASS. `grep -rn "train_end_ms\s*=\s*test_start_ms" src/` returns only safe `test_start_ms - embargo_ms` forms (walk_forward.py:113, cross_sectional.py:1325/1345). Foundation regression UNCHANGED by QE.
- **A2 (labeling-window σ_t look-ahead)**: PASS. `grep -rn "returns\[.*:.*\].std|labels.*std" src/crypto_trade/strategies/ml/labeling.py` returns no matches.
- **A3 (combined fit_transform)**: PASS. `grep -rn "fit_transform|StandardScaler|MinMaxScaler" src/` returns only a fracdiff_v3.py docstring reference (no sklearn pipeline applied across train+test).
- **A5 (master-data-extent dependency)**: PASS. R5 features are loaded from per-symbol feature parquets at init; no master DataFrame slicing semantics introduced.
- **A6 (Optuna trial contamination)**: PASS. R5 is BacktestConfig only — no Optuna study modifications.
- **A7 (parquet append-without-clearing)**: PASS. No `to_parquet append` or `pd.concat.read_parquet` patterns introduced.
- **A8 (stateful gate deadlock)**: PASS. R5 is STATELESS per brief Section 2.3 (`STATELESS-gate-VALID per /054`). No persistent state across candles. ORACLE EDA on baseline roster is methodologically VALID.
- **A12 (DSR/PSR granularity)**: PASS. No `psr()` / `dsr()` call sites modified; no new methodology fields added to dsr.json or comparison.csv at the math layer (R5 doesn't alter Sharpe input granularity).
- **A13 (report file write-before-read)**: PASS. R5 emits a single stdout print at backtest end (line 487-492); no runner-side read-from-disk loop reads R5 outputs in the same execution. Note: see WARN in Advisory Notes — brief Section 10.3 promised `r5_fire_log.csv` + `comparison.csv` row not implemented; this is reporting incompleteness not write-before-read.

QE's diff is small (~19 lines src/ + 211 lines test). All scanned heuristics return zero unexplained matches in active code.

### Foundation Regression: PASS

`walk_forward.py:113` confirmed at HEAD `22cf829`:
```
train_end_ms = test_start_ms - embargo_ms  # purge labels that would peek into test
```
The iter-v3/057 fix (`e149e9d`) is intact. `compute_embargo_candles` helper at walk_forward.py:10-38 derives the formula `label_timeout_minutes // interval_minutes + 1` (no duplication). `lgbm.py:502-504` uses the same helper for CV gap (`cv_gap = embargo_candles * n_symbols`). `validation_v1.py:58` declares `REQUIRED_GAP = (21+1)*5 = 110` for v1's 5-symbol universe. QE's diff (f316dae, 22cf829) touched only `backtest_models.py`, `backtest.py`, `run_baseline_v1.py`, and `tests/test_iteration_v1_010_r5.py` — no foundation file regression. `tests/test_lookahead_embargo.py` contains all 4 mandated tests.

### Cadence + Axis Sanity: PASS

- Phase 5.5 gate confirmed PASS (briefs-v1/iteration_v1-010/phase5p5_gate.md `OVERALL: PASS`).
- Brief Section 0.6 declares `axis family: risk-primitive`.
- Rotation status: VALID — risk-primitive is UNUSED in prior 5 EXPLORATIONs (005=hyperparameter-region, 006=universe, 007=feature-family, 008=methodology, 009=feature-family). First appearance in v1 catalog.
- Check 14 (Axis Family Validation): PASS. QE src/ diff is entirely BacktestConfig fields + post-R2 hook in vt_scale pipeline + unit tests. No scope creep into features/labeling/model-arch/universe layers. Declared family matches observed change.
- HIGH-RISK declaration present at Section 2.5 with appropriate mitigation (multi-seed CONFIRMATION at /011 IF /010 PROMISING).
- LM Master /009 PRIMARY recommendation ADOPTED (Section 3.2); Critic /009 Path Forward #1 ADOPTED (Section 3.3); SECONDARY methodology-debt explicitly REJECTED with reason.

### Falsifier Presence: PASS

Brief Section 4 contains 5 explicit numerical falsifiers:
- **F1 (PRIMARY)**: `(/010 OOS monthly Sharpe) - (BASELINE_V1 OOS monthly Sharpe +0.6637) < -0.05` → NEGATIVE; `< -0.20` → catastrophic.
- **F2 (BEHAVIORAL)**: portfolio OOS fire rate ∈ [10%, 60%]; outside band → NEGATIVE-mis-calibrated.
- **F3**: `(/010 IS monthly Sharpe) - (+0.2829) < -0.10` → NEGATIVE-catastrophic-IS.
- **F4**: any DEGENERATE_PREDICTOR fire → NEGATIVE-data-integrity.
- **F5**: `dsr.json` n_eff_per_cell_median ≥ 4 + dsr_is_finite → else NEGATIVE-methodology-regression.

Verdict gates Section 8 codify these into PROMISING / PROMISING-INERT / NEGATIVE / NEGATIVE-NEGATIVE / NEGATIVE-mis-calibrated bands with explicit numerical thresholds for each.

---

## Phase 6.0 Verdict: PASS — backtest may launch.

QE setup is methodologically sound: foundation untouched, no anti-pattern signatures, axis-family declaration matches src/ diff, falsifiers explicit and numerical, A14 dead-feed guard implemented (backtest.py:215-227 raises ValueError if vol_natr_14 has >10% constant-row fraction), R5↔R2 multiplicative ordering verified correct (backtest.py:428-435 applies R5 AFTER R2 in vt_scale pipeline), R5↔R1/R3 documented orthogonality (Section 6.2/6.3), worst-case joint weight ~0.10 (Section 6.1) acceptable.

## Advisory Notes (NOT BLOCK — flagged for Engineer's awareness before launch)

The following are deliverables promised by the brief Section 10.3 but not implemented in QE's setup commits. These do NOT corrupt methodology and do NOT trigger BLOCK, but they will require workaround at Phase 7 evaluation. The Engineer should consider patching before launch OR the Phase 7 evaluator should be aware that F2 fire-rate evaluation will require log parsing:

- **Brief Section 10.3 line 476**: comparison.csv promised to include row `r5_fire_rate_oos`. QE's `run_baseline_v1.py:591-612` does not append an R5 row to comparison.csv. F2 falsifier evaluation will need to extract fire rate from stdout log (`[R5] fired on X of Y signals (Z%)`) instead of structured CSV.
- **Brief Section 10.3 line 480**: `r5_fire_log.csv` (per-trade NATR_14, r5_cap_applied, r5_fired_bool) promised for forensic checks. Not implemented. Per-trade R5 firing forensic is not extractable from current trades.csv schema.
- **Brief Section 10.1 line 449-454**: An `r5_fires` counter print at backtest end is implemented (backtest.py:487-492) and provides aggregate observability — but not structured per-OOS-vs-IS split. The F2 condition specifies "portfolio OOS fire rate" — the print covers the full backtest, not separately segmented IS vs OOS. The Engineer should either split the counter by IS/OOS half or the Phase 7 evaluator should compute fire rate from per-half trade-count cross-reference (achievable via stdout log parse + trade roster).

These gaps are reporting-completeness, not methodology defects. Phase 6.0 PASSES; the issues are advisory and surface at Phase 7 evaluation. Phase 7.5 full Critic will hard-check whether the F2 verdict was properly evaluated.
