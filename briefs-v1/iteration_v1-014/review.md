# Phase 7.5 Critic Review — iter-v1/014

OVERALL: EXPLORATION-NEGATIVE — basin draw catastrophic IS (Δ -0.8941), negative OOS (Δ -0.4809); mechanism F7-NEW PARTIAL (4/5; ETH deviant); Check 8 FAIL on C1 barrier-source asymmetry CONFIRMED + engineering_report.md MISSING (4th-strike)

## Iteration Type
TYPE: EXPLORATION (cycle-2 #9 of 10; HIGH-RISK declared; /015 = labeling CONFIRMATION pre-committed BINDING regardless of /014)

## Per-Check Status

### Check 1 — Look-Ahead Audit: PASS

- `walk_forward.py:113` carries `train_end_ms = test_start_ms - embargo_ms` (iter-v3/057 fix intact)
- `tests/test_lookahead_embargo.py` has all 4 mandated tests
- `labeling.py:333` σ_t path uses precomputed `sigma_values[idx]` — no forward-window std
- `lgbm.py:425-426` computes `pd.Series.ewm(halflife=N, adjust=False).std()` then applies `.shift(1)` with explicit "A2 GUARD — past-only" comment. LM Master Phase 4.5 Rec #3 SATISFIED.

### Check 2 — Embargo Width: PASS

`compute_embargo_candles` shared by walk_forward and CV gap; REQUIRED_GAP=110 inherited.

### Check 3 — Multiple-Testing Correction: INFORMATIONAL (TYPE=EXPLORATION)

DSR_IS=0, DSR_OOS=0, PSR_monthly_vs_0 IS=0.0006/OOS=0.237, PBO=null. All edge thresholds FAIL — informational per EXPLORATION-mode artifact rule.

**Durable structural finding**: `n_eff_per_cell_median=19` (range 14-22, per-symbol 18-20) — **FIRST material n_eff shift in v1 cycle-2**. /008-/013 all stayed at 13. Strongest mechanism signal in 12 v1 iterations. Independent of F1/F3 basin draw direction.

### Check 4 — IC Correlation: PASS

No new feature family added. Cross-family IC inherited from BASELINE_V1.

### Check 5 — ADF Stationarity: PASS (with caveat)

All active features bonferroni_pass=True. LM Master Phase 7.4 closing-note Rec #2 raised concern about ADF on σ_t-labeled labels (not just raw σ_t feature); current artifact tests features only. Carry forward to /015 brief Section 2 EDA-mandate.

### Check 6 — Pareto Dominance: N/A

Single-seed EXPLORATION; 10-seed Pareto reserved for /015 CONFIRMATION.

### Check 7 — Reproducibility: PASS (with C1 smoking gun)

Trade spot-check (LTC long, entry 147.97, exit 139.378956, SL):
- pnl_pct = -5.806%; net_pnl_pct = -5.9059 (matches CSV; PnL arithmetic correct)
- **SL = 5.806% of entry; TP price = 165.152089 → TP = 11.612%; ratio TP/SL ≈ 2.0**
- This ratio is consistent with BASELINE `atr_tp=2.9, atr_sl=1.45` NATR-based execution barriers, NOT σ_t × k_tp=1.06/k_sl=0.53 × √21 path
- **Execution-time barriers were UNCHANGED from /013 NATR×atr_mult — code-and-data smoking gun for Concern C1**

PnL reproducibility PASS. C1 inconsistency is AXIS-ATTRIBUTION defect (Check 8).

### Check 8 — Hypothesis-Implementation Alignment: FAIL (TWO issues)

**C1 — Barrier-source inconsistency confounds the axis**:

Brief Section 10.1 RESOLUTION explicitly mandated "barrier-source consistency at both label-time AND execution-time". Code audit:
- Label-time `labeling.py:333,350-357`: σ_t × k path WIRED CORRECTLY
- Execution-time `lgbm.py:907-915`: `tp_pct = natr * self.atr_tp_multiplier` and `sl_pct = natr * atr_sl_multiplier` — **UNCHANGED from /013** (no σ_t branch)
- Trades.csv row-1 TP/SL ratio confirms execution used NATR path

Per EDA Section 2.4: EWMA/NATR ratio is 1.11-1.13 BTC/ETH (label barriers ~12% WIDER than execution) and 0.92-0.94 alts (label barriers ~7% TIGHTER than execution). LM Master Phase 7.4 §3 attribution:
- LTC IS+OOS WINNER (+95.51 / +24.49): tighter σ_t labels + wider NATR execution = LTC trades survive longer than labels predict = **C1 WINDFALL**
- BTC/ETH catastrophic (BTC -24.25, ETH -99.73): wider σ_t labels + tighter NATR execution = Optuna trains on labels saying "TP would hit" but execution closes narrower = **C1 PENALTY**

The C1 asymmetry corrupts F1 + F3 attributions. /014 is structurally a CONFOUNDED experiment.

**4th-strike missing engineering_report.md**:

- Brief Section 10.2 declares `reports-v1/iteration_v1-014/engineering_report.md` BLOCKING for Phase 7.5 dispatch
- Critic /013 Rec #1 explicit: "For /014, escalate to Critic Phase 7.5 dispatch hard-reject if missing"
- File MISSING (Glob confirms)
- Runner only emitted `[WARNING]` at `run_baseline_v1.py:1217-1229` (not non-zero exit)
- This is the 4th-strike on /011 Rec #3 / /012 Rec #2 / /013 Rec #1 enforcement
- `reports-v1/iteration_v1-014/per_symbol.csv` (top-level F7-NEW diagnostic per Section 10.2 item 3) ALSO MISSING

**F7-NEW verification by Critic** (engineering should have done this):

| Symbol | Baseline TO% | /014 TO% | ΔTO | Predicted | Match |
|---|---|---|---|---|---|
| BTC | 13.3% | 17.5% | +4.2pp | UP | YES |
| ETH | 20.0% | 16.8% | -3.2pp | UP | **NO** |
| LTC | 29.0% | 26.6% | -2.4pp | DOWN | YES |
| LINK | 31.5% | 22.6% | -8.9pp | DOWN | YES |
| DOT | 28.0% | 24.8% | -3.2pp | DOWN | YES |

F7-NEW = PARTIAL (4/5). Mechanism sound on 4 symbols; ETH deviates due to C1 asymmetry.

F8-NEW = PASS (598 ∈ [466, 776]).

**Cell-assignment**: F1 NEGATIVE + F3 NEGATIVE-extreme + F7-NEW PARTIAL + F8-NEW PASS → Cell 5 EXPLORATION-NEGATIVE.

**Check 8 verdict**: FAIL. C1 confound + missing engineering report are dispatch-side violations of brief's own discipline.

### Check 13 — Anti-Pattern Static Scan: PASS

A1/A2/A3/A4/A5/A7/A8/A9/A10/A11/A12/A13 all PASS. The σ_t guard at `lgbm.py:426` (`ewma_std_shifted = ewma_std.shift(1)  # A2 GUARD — past-only`) is exemplary anti-pattern guard documentation.

### Check 14 — Axis Family Validation: PASS

`labeling` family declared; src/ diff modifies labeling.py + lgbm.py + run_baseline_v1.py. No risk-primitive, feature-family, model-arch, or universe changes. Rotation VALID (labeling differs from prior 5).

## Verdict Rationale

Cell 5 assignment per brief Section 8.1: F1 OOS Δ -0.4809 ∈ NEGATIVE band; F3 IS Δ -0.8941 < -0.60 extreme; F7-NEW PARTIAL; F8-NEW PASS. **EXPLORATION-NEGATIVE** with PARTIAL-F7 flag.

**Mechanism evidence is durable**: n_eff 13→19 shift is structurally significant and independent of basin direction. C1 asymmetry explains the per-symbol pattern (LTC windfall + BTC/ETH penalty).

Why NOT BLOCK-PENDING-FIX:
- BLOCK-PENDING-FIX requires "single isolated specific defect" fixable WITHOUT methodology change. C1 is methodology-level (execution-time barriers need σ_t rewiring = changing experimental design).
- /015 = labeling CONFIRMATION binding pre-commit fires REGARDLESS. C1 fix belongs in /015 axis-completion.

Why NOT EXPLORATION-PROMISING-PARTIAL:
- Brief Cell 2 requires F1 PROMISING (Δ ≥ +0.05). Observed -0.48 firmly NEGATIVE.
- n_eff diversification is mechanism evidence; not promoted to PROMISING without F1 positive.

Final verdict: **EXPLORATION-NEGATIVE** (catastrophic IS, negative OOS, confounded by C1, mechanism-level diversification durable but not edge-confirming).

## Recommendations to QR (process-level for /015 and beyond)

1. **C1 fix MANDATORY for /015**: execute-time barriers MUST use σ_t × k × √timeout when `sigma_source="ewma14d"`. COMPLETES the labeling axis brief Section 10.1 RESOLUTION mandated. Implementation: modify `lgbm.py:907-915` to dispatch on `self.sigma_source`. Add /015 falsifier F-AXIS-C1: "execution-time barrier matches label-time within 1e-6 tolerance for all IS candles". Critic Phase 7.5 at /015 will FAIL Check 8 if engineering report doesn't disclose C1 status.

2. **4th-strike engineering report enforcement requires HARD STOP**: `run_baseline_v1.py:1217-1229` only emits `[WARNING]`. Add `sys.exit(1)` if `engineering_report.md` is missing AND `--no-engineering-report` is not explicitly passed. Brief mandate is fragile across 4 iterations of dispatch-side violation.

3. **F7-NEW PARTIAL needs explicit verdict-class in /015 matrix**: brief Section 8.1 only enumerates PASS vs FAIL. Add explicit cell for "F1×F3 negative AND F7-NEW PARTIAL" indicating "mechanism 80% functional; engineering attention needed per-symbol".

## Path Forward (mandatory on EXPLORATION-NEGATIVE)

/015 = labeling CONFIRMATION binding per pre-commit (PRIMARY; cannot be renegotiated). C1 FIX mandated as part of /015 setup. Alternative axes for /016+ if /015 multi-seed NULL/NEGATIVE:

1. **Universe expansion to 7-symbol with concentration cap** (UNUSED `universe` family). Add BNB + SOL with per-symbol PnL share cap. Denominator expansion attenuates basin-lottery extreme draws. NOT proportional cap (v3/020 closed that).

2. **XGBoost head-to-head replacement** (UNUSED `model-arch` family). Depth-wise vs leaf-wise growth may favor different feature interactions. v3/016 closed this for v3 but v1's PRUNED feature set is different.

3. **Sample weighting by past-realized vol** (NEW `sample-weighting` family — never used in v1). Replace `abs(labeled_pnl)` weighting with weights inversely proportional to past-realized 30-day vol. Attenuates extreme-vol-regime trade influence on IS basin.

Per constructive duty: each from family NOT used in prior 5 EXPLORATIONs.

## BLOCK-PENDING-FIX Rerun Protocol

N/A — verdict is EXPLORATION-NEGATIVE. Defects (C1, missing engineering report) are forward-looking lessons codified for /015. /014 closed as EXPLORATION-NEGATIVE.
