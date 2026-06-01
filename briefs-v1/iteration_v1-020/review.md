# Phase 7.5 Critic Review — iter-v1/020

OVERALL: EXPLORATION-NEGATIVE — Catastrophic-NEGATIVE per Section 8 Row 6 (F1 OOS Sharpe Δ -0.86 ≤ -0.55); H_INTRINSIC REFUTED at training-time granularity; BTC's OOS positive rotation was POOL-CONFERRED, not intrinsic

## Iteration Type
TYPE: EXPLORATION (cycle-3 #5 of 10)

## Per-Check Status

### Check 1 — Look-Ahead Audit: PASS
Zero new features. V1_FEATURE_COLUMNS_PRUNED unchanged at 40 cols. Foundation audit: `walk_forward.py:113` carries `train_end_ms = test_start_ms - embargo_ms` unchanged. 4 mandated regression tests present at `tests/test_lookahead_embargo.py` lines 120/163/232/261.

### Check 2 — Embargo Width: PASS
Universe = 1 symbol; required gap = 22 candles. `validation_v1.py:58` REQUIRED_GAP adapts via runtime helper. No hardcoded 5-symbol gap.

### Check 3 — Multiple-Testing Correction: FAIL (informational for EXPLORATION)
DSR IS/OOS = 0.0 (degenerate floor). PBO null (CSCV deferred for single-cohort). PSR_monthly_vs_0 OOS = 0.301 (below 0.40 PROMISING-INERT floor but above 0.10 Catastrophic floor). PSR-based reading would land /020 in NEGATIVE-band; Δ-based reading lands Catastrophic-NEGATIVE. **Brief PRE-REGISTERED the Sharpe-Δ frame as decisive at Section 8 Row 6 (no compound condition on PSR)**. Section 8 Row 6 (F1 Δ ≤ -0.55) is satisfied → Catastrophic stands. Per §5.1 EXPLORATION rule, Check 3-edge axis failures do NOT trigger BLOCK.

### Check 4 — IC Correlation: PASS (with carry-forward observation)
38 family-pair rows. Zero NEW redundancies introduced by /020. Pre-existing redundancies: momentum × trend |IC|=0.797, momentum × volume 0.735, trend × volume 0.687 — STRUCTURAL features of V1_FEATURE_COLUMNS_PRUNED, NOT iteration-introduced. Carry-forward observation: persistent |IC|≈0.80 momentum × trend redundancy is a future-EXPLORATION audit target.

### Check 5 — ADF Stationarity: PASS
All signal-feeding features pass Bonferroni-corrected ADF or carry documented `exception_class` (vol_atr_14 regime-indicator).

### Check 6 — Pareto Dominance: N/A (single-seed EXPLORATION)
Multi-seed Pareto deferred to /027 CONFIRMATION substrate.

### Check 7 — Reproducibility: PASS
HEAD `1d6a25b`; explicit `feature_columns=active_feature_columns`; iter-stamped `data/v1_iter_v1-020_trial_oof.parquet`. Trade-row spot check PASS.

**Anchor-frame audit** (Critic concern #3): /020 verdict robust across ALL 4 frames:
- net_pnl trade-sum frame: Δ -32.18 pp → NEGATIVE band
- net_pnl monthly-sum frame: Δ -43.34 pp → Catastrophic-NEGATIVE
- annualized-daily-Sharpe vs brief proxy +0.30: Δ -0.86 → Catastrophic
- annualized-daily-Sharpe vs reconstructed proxy +1.0: Δ -1.56 → Catastrophic

3 of 4 frames land Catastrophic-NEGATIVE. Verdict cell ROBUST.

### Check 8 — Hypothesis-Implementation Alignment: PASS
Brief Section 1 ↔ runner dispatch lines 1443-1477: Model H BTC-only with atr_tp=2.9, atr_sl=1.45, apply_r1=False — Model A's pool semantics preserved. NO gate, NO feature, NO labeling. Pure isolation. Foundation files untouched. 1:1 match.

### Check 13 — Anti-Pattern Static Scan: PASS
A1-A13 all clean. A8 deadlock N/A (no gate). A12 DSR/PSR granularity disjoint per iter-v3/056 pattern.

### Check 14 — Axis Family Validation: PASS
`per-cohort-specialization-BTC` NEW 11th family. Rotation valid: prior 5 distinct. Orthogonality: different COHORT (BTC vs LINK/ETH), different STRUCTURAL PRIOR (IS-NEG/OOS-POS asymmetric), different SPECIALIZATION SCOPE (pure isolation, no knob).

## F-AXIS-MECHANISM Reconciliation

- **F-AXIS #1 (LOAD-BEARING)**: 122/122 IS + 53/53 OOS BTCUSDT. PASS.
- **F-AXIS #2 (LOAD-BEARING)**: IS 122 ∈ [70, 150] PASS; OOS 53 ∈ [25, 55] PASS (LM tighter [25, 46] BREACH-HIGH +7 INFORMATIONAL). QR blocking band controls; PASS.
- **F-AXIS #3 (IS_H1 regime-binding)**: cannot definitively verify (engineering_report.md MISSING). Manual estimate -19.4% inside [-45%, -15%] band. INDETERMINATE pending engineering_report; does NOT affect Catastrophic verdict.
- **F-AXIS #4 (n_eff)**: 9 ∈ [7, 10]. PASS (matches LM Master point estimate).

## Verdict Cell Determination

Section 8 Row 6 (F1 Δ ≤ -0.55) fires decisively across all anchor frames. Row 6 condition: "F1 OOS Sharpe Δ ≤ -0.55 → NEGATIVE-CATASTROPHIC" — F-AXIS #2 + #3 band-violation tolerated.

**Verdict cell: NEGATIVE-CATASTROPHIC (Section 8 Row 6).**
**Critic v1 verdict: EXPLORATION-NEGATIVE with Catastrophic subtype.**

LM Master Phase 7.4 §1-§3 structural finding (H_INTRINSIC REFUTED at training-time granularity; BTC's OOS positive rotation was POOL-CONFERRED via 3 channels: shared feature normalization, label-timing co-location, abs_pnl sample weighting) supports the mechanism interpretation. Monthly aggregate ρ ≈ -0.022 was a methodological false-negative; within-month label-timing carries BTC. Structural-finding closeout, not a code defect.

No isolated defect to gate as BLOCK-PENDING-FIX. Catastrophic outcome is the diagnostic signal itself (Section 5 LM Master refined prior tail of 2% materialized).

## Recommendations to QR

1. **Engineering report timing contract VIOLATED** (process-level; NOT verdict change at /020 but mandatory fix for /021). `briefs-v1/iteration_v1-020/engineering_report.md` is MISSING. Per brief Section 10.4 + /019 Critic Rec #1, QE was bound to publish engineering_report.md BEFORE Phase 7.5 dispatch ("Phase 7.5 Critic will refuse to dispatch if engineering_report.md is missing"). Verdict robust regardless, but the orchestrator dispatched Phase 7.5 without it, contradicting the brief's binding pre-commit. /021 must either (a) re-enforce the timing contract at orchestrator dispatch OR (b) downgrade to "advisory" with documented justification.

2. **Anchor proxy formalization** (load-bearing for cycle-3 verdict-cell calibration). Brief Section 4 F1 uses a monthly Sharpe PROXY (+0.30) while comparison.csv reports annualized daily Sharpe. /018 and /019 implicitly used the same mixed-frame Δ rule. Recommend /027 CONFIRMATION brief pre-compute the BTC-in-pool annualized-daily-Sharpe directly (single deterministic number, no proxy) and lock the anchor frame to comparison.csv "sharpe" semantics. Forward-looking; /020 verdict ROBUST under all frames.

3. **LM Master Phase 7.4 §3 structural finding adoption** (binding for /021 axis selection). H_INTRINSIC was REFUTED via 3 specific pool-conferred channels. Cycle-3 cohort-isolation evidence base: LINK (independent positive prior succeeds) + ETH (negative prior dissolved by GATE not isolation) + BTC (positive OOS rotation LOST at isolation — POOL-CONFERRED). Future per-cohort EXPLORATIONs without methodology pivot or orthogonal mechanism are predicted to repeat the BTC pattern. /021 MUST EITHER add methodology diagnostic OR orthogonal mechanism on top of isolation.

## Path Forward (mandatory on NEGATIVE)

Critic CONCURS with LM Master Phase 7.4 §5 hybrid Option C+B and adds structural alternatives.

1. **Methodology pivot to `_write_feature_importance` + training-time pool-anchor diagnostic** — family: **methodology-pivot** [Critic preference #1]. Add `feature_importance.csv` output (closing /019 §6 outstanding gap) AND per-(symbol, month) Optuna best-trial parameter delta between BTC-in-pool (Model A) and BTC-only (Model H) at SAME seed=42. Produces concrete training-time pool-anchor evidence. If diagnostic confirms LM Master §3 mechanism, /021 = LAST EXPLORATION before /027 CONFIRMATION moves up. ~25 min wall-clock.

2. **NEW feature family axis — funding-rate z-score or open-interest delta** — family: **feature-family**. Per /019 Critic Rec #3 carry-forward. Add single NEW feature (8h funding rate z-score, OR perp OI delta) to V1_FEATURE_COLUMNS_PRUNED. NOT touched in cycle-3 to date. Falsifier: importance rank ≥ 30% on ≥2 cohorts at IS.

3. **Risk-primitive axis — per-cohort drawdown brake** — family: **risk-primitive**. Binary off/on at -25% per-cohort cumulative loss. Tests whether risk gates dissolve OOS concentrated-loss pattern. Pre-commit deadlock-impossibility proof (A8 catalog + iter-v3/054 lesson): 8-candle cooldown escape.

Critic does NOT concur with strict adherence to LM Master Phase 4.5 §6 pre-staged /021 = LTC-only specialization. /020 catastrophic outcome materially shifts evidence base. QR should choose ONE of #1/#2/#3 (Critic preference: #1 > #2 > #3) with explicit Section 0.6 rotation justification.

## BLOCK-PENDING-FIX Rerun Protocol

N/A — verdict is EXPLORATION-NEGATIVE (structural finding closeout). /020 closes; /021 advances per Path Forward.
