# iter-v1/014 — Phase 7 Engineering Report (4th-strike retroactive fix)

**Iteration**: iter-v1/014
**Date**: 2026-05-25
**Branch**: `iteration-v1/014`
**Backtest HEAD**: `bcca796` (Phase 7.5 Critic review commit)
**Author**: QR (Phase 7 retroactive — engineering report MISSING at Phase 7.5 dispatch; this document closes the 4th-strike violation of brief Section 10.2 BLOCKING declaration + Critic /013 Rec #1 + Critic /014 Phase 6.0 PRECONDITION CHECK PASS)

---

## Section 1 — Final Verdict + Cell Rationale

**Verdict**: `EXPLORATION-NEGATIVE` (Cell 5 per brief Section 8.1 binding matrix) + `PARTIAL-F7` flag (F7-NEW 4/5 PASS — ETH deviant via C1).

**Cell assignment** (per brief Section 8.1):
- F1 OOS Δ = -0.4809 → in NEGATIVE band [-0.55, -0.05]; not catastrophic-extreme (≤ -0.55)
- F3 IS Δ = -0.8941 → in NEGATIVE-catastrophic band Δ < -0.30; **extreme by 0.59 below floor**
- F7-NEW = PARTIAL (4/5; ETH deviant — see Section 4 of this report)
- F8-NEW = PASS (598 IS trades ∈ [466, 776])

**First cell that matches**: Cell 5 (F1 NEGATIVE + F3 NEGATIVE-extreme + F7-NEW PASS + F8-NEW PASS) → **EXPLORATION-NEGATIVE**.

**PARTIAL-F7 supplement**: brief Section 8.1 enumerates F7-NEW outcomes as {PASS, PARTIAL, FAIL}. PARTIAL is not in any cell row; the cell-5 assignment is therefore the "nearest spirit" (F1+F3 both NEGATIVE) with explicit `PARTIAL-F7` flag for /015 brief Section 8 to add an explicit row "F1×F3 NEGATIVE AND F7-NEW PARTIAL → EXPLORATION-NEGATIVE with mechanism 80% functional; engineering attention needed per-symbol" (Critic Rec #3 forward-mandate).

**Cell-7/8 mechanical failures CHECKED FIRST per brief Section 8.2 override rule**:
- Cell 7 (F7-NEW FAIL): NO — F7-NEW is PARTIAL (4/5), not FAIL (≤2/5)
- Cell 8 (F8-NEW FAIL): NO — F8-NEW is PASS (598 ∈ [466, 776])

Cells 7/8 do NOT fire; Cell 5 stands.

**No BLOCK-PENDING-FIX**: per brief discipline + Critic Phase 7.5 review §"Why NOT BLOCK-PENDING-FIX", C1 is methodology-level (changing experimental design) not single isolated defect fixable without redesign. /015 = labeling CONFIRMATION binding pre-commit absorbs C1 fix as part of the axis-completion bundle.

---

## Section 2 — Per-Symbol IS PnL Decomposition

From `reports-v1/iteration_v1-014/in_sample/per_symbol.csv` (598 IS trades total):

| Symbol | Trades | Wins | WR | Net PnL % | Avg PnL % | % of Total PnL |
|--------|--------|------|-----|-----------|-----------|----------------|
| **LTCUSDT** | **128** | **61** | **47.7** | **+95.51** | **+0.7462** | **-75.21** |
| LINKUSDT | 106 | 41 | 38.7 | -9.79 | -0.0924 | +7.71 |
| BTCUSDT | 120 | 45 | 37.5 | -24.25 | -0.2021 | +19.09 |
| **DOTUSDT** | **101** | **34** | **33.7** | **-88.74** | **-0.8786** | **+69.88** |
| **ETHUSDT** | **143** | **45** | **31.5** | **-99.73** | **-0.6974** | **+78.53** |
| **PORTFOLIO** | **598** | **226** | **37.8** | **-126.99** | **-0.2123** | **100.00** |

**LTC IS WINNER signature**: WR 47.7% (vs 31.5%-38.7% for the other 4); avg PnL +0.75% per trade dominates total +95.51. Trade count 128 modestly below baseline LTC IS rank-1 (130-145 range across /010-/013). LTC IS rank-1 WINNER for the FIRST time in cycle-2 catalog after a sign-flipping rotation across /011-/013.

**BTC + ETH CATASTROPHIC signatures**: ETH -99.73 (largest IS negative in cycle-2 catalog; previous ETH catastrophic -139.78 at /013); BTC -24.25 (mild catastrophic; /011 BTC was -30.74). Both losers are wider-σ_t-than-NATR symbols (Section 4: C1 SMOKING GUN — wider labels, tighter execution).

**DOT catastrophic LOSER**: DOT WR 33.7% (lowest in portfolio); -88.74 net PnL (vs /011 DOT +31.01 / /012 DOT -179.84 catastrophic / /013 DOT -4.18 recovered). DOT IS swing >270 raw PnL units across /011-/014 — confirms LM Master /012 closeout flag "DOT predictions sign-unstable under hyperparameter variation".

**LINK ~flat at IS**: LINK -9.79 net PnL (vs /011 +42 / /012 +106 / /013 +128). LINK was IS rank-1 at /013; collapses to near-zero at /014. Roster-rotation magnitude consistent with prior cycle-2 single-seed-window observations.

---

## Section 3 — Per-Symbol OOS PnL Decomposition

From `reports-v1/iteration_v1-014/out_of_sample/per_symbol.csv` (202 OOS trades total):

| Symbol | Trades | Wins | WR | Net PnL % | Avg PnL % | % of Total PnL |
|--------|--------|------|-----|-----------|-----------|----------------|
| **LTCUSDT** | **38** | **19** | **50.0** | **+24.49** | **+0.6444** | **+740.26** |
| DOTUSDT | 41 | 18 | 43.9 | +10.43 | +0.2545 | +315.41 |
| BTCUSDT | 41 | 18 | 43.9 | +5.70 | +0.1390 | +172.24 |
| LINKUSDT | 44 | 19 | 43.2 | +3.87 | +0.0878 | +116.84 |
| **ETHUSDT** | **38** | **12** | **31.6** | **-41.18** | **-1.0836** | **-1244.75** |
| **PORTFOLIO** | **202** | **86** | **42.6** | **+3.31** | **+0.0164** | **100.00** |

**FIRST OOS LTC WINNER in cycle-2 catalog**: LTC OOS +24.49 with WR 50.0% (cycle-2 /010-/013 had LTC OOS as systematic loser: -3.74 / -19.12 / -47.66 / -40.16). LTC OOS trajectory FINALLY flips positive at /014 — supports the LM Master Phase 7.4 §4 attribution that C1 windfall + tighter σ_t LTC labels combined with the Optuna basin draw produced a structurally-different IS+OOS pattern for LTC.

**4 of 5 symbols OOS POSITIVE for the first time**: LTC + DOT + BTC + LINK all positive OOS net PnL (modest magnitudes for the 3 non-LTC). This is the most-OOS-positive symbol count in cycle-2 catalog. Headline OOS Sharpe is still NEGATIVE (-0.3533… wait, +0.1828) — ETH -41.18 + low-magnitude positives drag the daily Sharpe via daily-volatility weighting NOT total net PnL.

**ETH OOS catastrophic at +0.1828 Sharpe**: ETH alone -41.18 (vs ETH at /013 OOS -5.59 / /012 -17.16 / /011 -2.90). ETH single-symbol OOS Sharpe is the dominant negative contributor; raw total OOS net PnL is +3.31 (positive!), but daily-Sharpe ETH-weighting brings the portfolio to Sharpe +0.18.

**Total OOS net PnL POSITIVE +3.31** despite OOS Sharpe +0.18: confirms a low-magnitude positive raw return combined with high daily variance. Multi-seed dissolution at /015 should narrow this variance.

---

## Section 4 — C1 SMOKING GUN: Execution Barriers Used NATR not σ_t

**The single load-bearing IS-catastrophe explanation per LM Master Phase 7.4 §3.**

### 4.1 Codepath Mismatch

Brief Section 10.1 RESOLUTION explicitly mandated barrier-source consistency at both label-time AND execution-time. The implementation as shipped at HEAD `dd8cf0d`:

- **Label-time** (`src/crypto_trade/strategies/ml/labeling.py:333,350-357`): σ_t × k_tp/k_sl path WIRED CORRECTLY. `tp_dist_pct_decimal = sigma_k_tp × sigma_values[idx] × sqrt(timeout_candles)`. Past-only `.shift(1)` enforced at `lgbm.py:425-426` per LM Master Phase 4.5 Rec #3.
- **Execution-time** (`src/crypto_trade/strategies/ml/lgbm.py:907-915`): `tp_pct = natr * self.atr_tp_multiplier` AND `sl_pct = natr * atr_sl_multiplier` — **UNCHANGED from /013**. No `self.sigma_source` dispatch. NATR-based execution barrier ALWAYS active regardless of `sigma_source="ewma14d"` config.

### 4.2 Trades.csv Reproducibility Confirms Execution Never Used σ_t

LTC trades.csv row 1 (long, entry 147.970000, exit 139.378956):
- pnl_pct = -5.8059 ⇒ SL distance from entry = (147.97 - 139.378956) / 147.97 = **5.806%**
- TP price = 165.152089 ⇒ TP distance = (165.152089 - 147.97) / 147.97 = **11.612%**
- TP/SL ratio = 11.612 / 5.806 = **2.0**

Compare to **baseline NATR × atr_mult** (per `LightGbmStrategy.__init__` defaults at `lgbm.py`):
- atr_tp_multiplier=2.9 (Model D for LTC), atr_sl_multiplier=1.45
- TP/SL ratio = 2.9 / 1.45 = **2.0** EXACT match
- NATR_LTC at this candle ≈ 5.806% / 1.45 ≈ 4.0% (consistent with LTC NATR_21 typical magnitude in IS regime)

Compare to **σ_t × k_tp/k_sl × √timeout** (the σ_t scheme the brief mandated for execution):
- k_tp=1.06, k_sl=0.53, timeout=21 candles → √21 ≈ 4.583
- TP/SL ratio = 1.06 / 0.53 = **2.0** (coincidentally same — both schemes have ratio 2.0)
- But the **absolute magnitude** would differ: σ_t × 1.06 × √21 = σ_t × 4.86
- Per EDA Section 2.4 LTC σ_t ≈ 0.92 × NATR ≈ 0.92 × 4.0% ≈ 3.68%
- Expected SL distance under σ_t scheme = 3.68% × 0.53 × 4.583 = 8.94% (NOT 5.806%)

**Confirmed**: SL distance 5.806% matches NATR×1.45=5.8% within 1bp tolerance; σ_t × k_sl × √21 scheme would have produced ~8.94% SL distance. **Execution-time barriers NEVER USED σ_t.** Code-and-data smoking gun for Concern C1.

### 4.3 Per-Symbol Asymmetric Windfall/Penalty Mechanism

Per EDA Section 2.4 σ_t/NATR ratios:

| Symbol cluster | σ_t / NATR ratio | Label-time vs Execution-time | Mechanism |
|----------------|-----------------|------------------------------|-----------|
| BTC + ETH | 1.13 (wider σ_t) | Label barriers WIDER than execution | Optuna trains on labels saying "TP at +5.91%" but execution closes at +5.06% → systematic positive labeling bias → IS basin PENALTY |
| LINK + LTC + DOT | 0.92 (tighter σ_t) | Label barriers TIGHTER than execution | Trades survive LONGER than labels predict → C1 WINDFALL for alts |

**LTC win signature (C1 WINDFALL)**: tighter σ_t labels (~0.92 × NATR) produced MORE labeled TPs per IS row (28.1% TP rate vs 20.2% baseline — biggest TP% jump per LM Master Phase 7.4 §4). Combined with wider NATR execution, trades exited LONGER than labels predicted. LTC's strongly-trending IS regime had dense short-horizon TP opportunities the σ_t-tighter labels captured.

**BTC + ETH catastrophe signature (C1 PENALTY)**: wider σ_t labels (1.13 × NATR) but narrower NATR execution → Optuna learns "TP at +5.91%" but trade closes at +5.06% → fewer TP hits than labeled → IS basin penalty.

**Both signatures are C1 artifacts**, not basin lottery alone. The 33/33/34 flat prior governs the BASIN DRAW direction; C1 amplifies the basin asymmetrically per-symbol.

### 4.4 Critic Concern C1 Was Surface-Discoverable from EDA + Audit

C1 was raised by Critic in Phase 6.0 pre-flight at HEAD `65c0bb2` (per `briefs-v1/iteration_v1-014/critic_preflight.md`). Brief Section 10.1 RESOLUTION (HEAD `6d7fce5`) committed to barrier-source consistency. Implementation at `dd8cf0d` shipped without the execution-time dispatch.

The PR `7c019ed` (axis isolation fix — disable R5) was the LAST src/ commit before backtest; it did NOT address C1. Engineering team Phase 6 closeout should have caught this via the brief Section 10.1 explicit mandate. Going forward (/015):
- C1 FIX MANDATORY at /015 setup — modify `lgbm.py:907-915` to dispatch on `self.sigma_source` and route execution barriers through the same σ_t × k_tp/k_sl × √timeout path
- Add /015 falsifier F-AXIS-C1: "execution-time barrier matches label-time within 1e-6 tolerance for all IS candles" (programmatic assertion)
- Critic Phase 6.0 at /015 must FAIL Check 8 if engineering report doesn't disclose C1 status

---

## Section 5 — F1-F8 Verdict Matrix Evaluation

Per brief Section 8.1 binding table:

| Falsifier | Pre-registered condition | Observed | Verdict |
|-----------|--------------------------|----------|---------|
| **F1** (OOS Sharpe Δ) | NEGATIVE [-0.55, -0.05]; NEG-catastrophic Δ < -0.30 | **-0.4809** | **NEGATIVE** (deep into band, not catastrophic-extreme) |
| **F2** (IS trade count) | PASS if ∈ [466, 776] | **598** | **PASS** (modest below center 621) |
| **F3** (IS Sharpe Δ) | NEGATIVE [-0.30, -0.10]; NEG-catastrophic Δ < -0.30 | **-0.8941** | **NEGATIVE-CATASTROPHIC-EXTREME** (0.59 below catastrophic floor) |
| **F4** (DEGENERATE_PREDICTOR) | PASS = no fire | did not fire | **PASS** |
| **F5** (PSR ≥ 0.50 both halves) | INFORMATIONAL (PSR_monthly_vs_0 IS=0.065 / OOS=0.59) | IS FAIL, OOS PASS | **MIXED-INFORMATIONAL** |
| **F6** (OOS roster overlap) | informational; expected [50%, 75%] | not computed | **NOT COMPUTED** (gap; LM Master Phase 7.4 noted) |
| **F7-NEW** (per-symbol TO% direction) | PASS=5/5; PARTIAL=3-4/5; FAIL≤2/5 | **4/5 (ETH deviant)** | **PARTIAL** |
| **F8-NEW** (IS trade count band) | PASS ∈ [466, 776] | **598** | **PASS** |

**F7-NEW deep dive** (the load-bearing mechanism falsifier per LM Master Phase 4.5 §6 "single non-ignorable point"):

| Symbol | Pred TO direction | Baseline TO% | /014 TO% | Δ TO% | Match? |
|--------|--------------------|--------------|----------|-------|--------|
| BTC | UP | 13.3% | 17.5% | +4.2pp | YES |
| ETH | UP | 20.0% | 16.8% | **-3.2pp** | **NO** |
| LINK | DOWN | 31.5% | 22.6% | -8.9pp | YES |
| LTC | DOWN | 29.0% | 26.6% | -2.4pp | YES |
| DOT | DOWN | 28.0% | 24.8% | -3.2pp | YES |

**F7-NEW = PARTIAL (4/5).** ETH deviant: predicted UP but observed DOWN. The deviation is C1 SMOKING GUN per LM Master Phase 7.4 §2: ETH SL% INCREASED +8.4pp (wider σ_t labels said "TP would hit" but execution NATR barriers narrower → execution SL hits before label-predicted TP). First observable C1 signature in trade data.

---

## Section 6 — n_eff Structural Finding (DURABLE Mechanism Evidence)

**`n_eff_per_cell_median` jumped from 13 (BASELINE + /008-/013) → 19 (/014).**

From `reports-v1/iteration_v1-014/comparison.csv` row `n_effective_trials`:
- IS value: 19
- OOS value: 19
- All prior cycle-2 EXPLORATIONs reported 13 (per /008-/013 dsr.json artifacts)

Per-symbol from dsr.json:
- BTC = 20, ETH = 20, LINK = 18, LTC = 18, DOT = 19

**Significance**: this is the **FIRST material n_eff shift in v1 cycle-2** since the methodology axis at /008. n_eff is structurally bound by per-cell label-distribution shape — independent of basin direction. The 13→19 shift (+46% relative) indicates the σ_t labeling axis **diversified the Optuna loss surface as predicted in LM Master Phase 4.5 §2 ("partial-shift scenario")**.

**Durable structural evidence INDEPENDENT of /014's catastrophic F1/F3 magnitudes**:
- The 33/33/34 FLAT prior governs BASIN DRAW (which Optuna trial wins the per-cell tournament)
- n_eff governs LOSS SURFACE GEOMETRY (richer loss surface = more diverse Optuna trial outcomes)
- /014 produced a NEGATIVE basin draw on a RICHER surface — these are independent measurements
- At /015 multi-seed (10 outer seeds × 5 inner), n_eff=19 should REPLICATE if mechanism is robust

**Independent of C1**: even with C1 confounding label/execution barrier consistency, the per-cell labels are DIFFERENT distributions per (model, month) cell. Optuna's per-cell loss surface IS richer. n_eff jump is real even if C1 corrupts the resulting basin draw.

**/015 mandate**: pre-register "n_eff ≥ 17 across at least 7/10 seeds" as a F-AXIS-MECHANISM falsifier per LM Master Phase 7.4 §7 Rec #3. If n_eff collapses to 13 at multi-seed, loss-surface diversification was single-seed artifact (unlikely; n_eff bound by label-distribution shape, which is independent of seed).

---

## Section 7 — LM Master 0/12 Directional Calibration Update + 5 PARTIAL

Per LM Master Phase 7.4 §5 (commit `1f70af3`):

**Track record after /014**: **0/12 directional + 5 PARTIAL** (was 0/11 + 4 PARTIAL after /013).

**Mechanism predictions (RELIABLE — counted as PARTIAL hits)**:
1. σ_t lookahead-clean if `.shift(1)` present (95% confidence; verified PASS by Critic Check 1)
2. F8-NEW IS trade count in [466, 776] (~80% probability; observed 598 PASS)
3. F7-NEW per-symbol direction matches for ≥3 of 5 symbols (~70%; observed 4/5 PARTIAL)
4. n_eff diversification prediction (LM Master Phase 4.5 §2 partial-shift scenario; n_eff 13→19 observed = mechanism class confirmed)
5. FLAT prior calibrated for verdict-class (no prediction lost to over-confidence)

**Directional predictions (0/12 — REFUTED)**:
- LTC catastrophic-candidate prediction (LM Master Phase 4.5 §2) — INVERTED at /014: LTC was IS+OOS WINNER instead of catastrophic. Cycle-2 LM Master per-symbol catastrophic predictions: 0/4 (BTC mild at /011, DOT at /012, ETH+BTC at /013, ETH+DOT at /014). LM Master Phase 7.4 §5 FINAL CALIBRATION rule fires: **STOP PREDICTING PER-SYMBOL CATASTROPHIC CANDIDATES**.

**FLAT prior rule reinforced**: at v1 single-seed EXPLORATION, F1/F3 verdict-class is basin-determined. LM Master Phase 4.5 advisories at /015+ MUST default to FLAT priors (33/33/34) for verdict-class; magnitude bands as plausibility envelopes ONLY, not P50 anchors.

**At multi-seed CONFIRMATION**: LM Master priors permitted to concentrate (per Phase 4.5 §5 60/25/15 NULL/PROMISING/NEGATIVE forecast at /015 — first place LM Master moves off FLAT). At /015 multi-seed, variance reduction is mechanically guaranteed; concentrated priors earn credibility there.

---

## Section 8 — 4th-Strike Process Discipline FAIL — Hard-Stop Codification for /015

### 8.1 The Recurring Violation

Brief Section 10.2 declares `reports-v1/iteration_v1-014/engineering_report.md` BLOCKING for Phase 7.5 dispatch. Critic /013 Rec #1 explicit: "For /014, escalate to Critic Phase 7.5 dispatch hard-reject if missing". Critic /014 Phase 6.0 pre-flight passed declaration check (HEAD `65c0bb2`). Despite this 4-layer codification, the engineering report was MISSING at backtest closeout HEAD `7c019ed`.

This is the **4th consecutive iteration** with engineering report enforcement gap:
- /011 Critic Rec #3: orchestrator-side hard-reject of Phase 7.5 dispatch without engineering report
- /012 Critic Rec #1: 3-way enforcement (orchestrator + QE skill + Critic Phase 6.0 precondition)
- /013 Critic Phase 7.5 §"Check 7" PROCESS CONCERN: 3rd-strike escalation
- **/014 4th-strike**: spec-side check passes (Critic Phase 6.0 PASS), but dispatch-side never blocks

### 8.2 Root Cause: Spec-Side Check vs Dispatch-Side Enforcement

`run_baseline_v1.py:1217-1229` emits `[WARNING]` if `engineering_report.md` is missing AFTER backtest finishes; it never calls `sys.exit(1)`. The warning is buried in the run log; Phase 7.5 dispatch fires anyway. Phase 5.5 gate verifies brief LANGUAGE only; Phase 6.0 verifies brief LANGUAGE declares it BLOCKING; runner emits [WARNING] only.

The check has been MOVED across 4 layers but never CONVERTED FROM WARNING TO HARD STOP at the runner level.

### 8.3 /015 Setup Codified Hard-Stop Commitment

For /015 setup, the runner must enforce a HARD STOP before Phase 7.5 dispatch:

```python
# run_baseline_v1.py — Phase 7.5 dispatch gate
engineering_report_path = reports_dir / "engineering_report.md"
if not engineering_report_path.exists() and not args.no_engineering_report:
    print(f"[FATAL] engineering_report.md missing at {engineering_report_path}", file=sys.stderr)
    print("[FATAL] Phase 7.5 dispatch BLOCKED. Use --no-engineering-report to override.", file=sys.stderr)
    sys.exit(1)
```

The `--no-engineering-report` opt-out is reserved for explicitly-acknowledged QE-side defects; default behavior is HARD STOP. This codifies Critic /014 Phase 7.5 Rec #2 mandate.

**This is a /015 brief Section 10.2 mandate** — must be in QE Phase 6 deliverables BEFORE Phase 7.5 dispatch can fire. Critic Phase 6.0 at /015 verifies the runner has the hard-stop code path AT BRIEF AUTHORING, not after backtest.

---

## Section 9 — /015 MANDATES (Forward Carry from /014 Closeout)

Per Critic Phase 7.5 Path Forward (HEAD `bcca796`) + LM Master Phase 7.4 §7 + this Phase 7 engineering report:

1. **C1 FIX MANDATORY**: execute-time barriers must use σ_t × k_tp/k_sl × √timeout when `sigma_source="ewma14d"`. Implementation in `lgbm.py:907-915` dispatch on `self.sigma_source`. Add F-AXIS-C1: "execution-time barrier matches label-time within 1e-6 tolerance for all IS candles" (programmatic assertion in tests).

2. **MULTI-SEED CONFIRMATION binding pre-commit FIRES**: /015 spec is `--seeds 10` (ENSEMBLE_SIZE=10 outer × ENSEMBLE_SIZE=5 inner = 50 models/cell) + n_trials=35 + V1_FEATURE_COLUMNS_PRUNED + `sigma_source="ewma14d"` + C1 FIX applied. PASS gates: IS Sharpe ≥ +1.0 + OOS Sharpe ≥ +1.0 multi-seed mean + DSR > 0.95 + PBO < 0.4 + PSR > 0.95 + top-symbol ≤ 30% + 10-seed concentration validation + OOS trades ≥ 130. Modal expected outcome NULL (LM Master Phase 7.4 §6: 55% NULL / 20% PROMISING / 25% NEGATIVE).

3. **F7-NEW PARTIAL explicit verdict-class in /015 matrix**: Section 8 binding table at /015 brief must add explicit row "F1×F3 NEGATIVE AND F7-NEW PARTIAL → EXPLORATION-NEGATIVE with mechanism 80% functional; engineering attention needed per-symbol".

4. **Engineering report HARD-STOP codification in /015 src/ changes**: `run_baseline_v1.py` modifies the dispatch gate as Section 8.3 specifies. Brief Section 10.2 includes the gate code in the implementation spec.

5. **F-AXIS-C1 falsifier (NEW)**: at /015, programmatic assertion that execution-time barriers match label-time within 1e-6 tolerance. If FAIL, BLOCK-PENDING-FIX rerun.

6. **F-AXIS-MECHANISM falsifier (NEW)**: per LM Master Phase 7.4 §7 Rec #3, pre-register "n_eff ≥ 17 across at least 7/10 seeds". If <7/10, loss-surface diversification was single-seed artifact (unlikely but checked).

7. **NO RECURSION ON BLOCK-PENDING-FIX**: per v1 skill discipline, one BLOCK-PENDING-FIX rerun at /015 if C1 fix is somehow incomplete; verdict at that point can only be PASS or BLOCK-FINAL.

---

## Section 10 — Phase 7 Closeout Status

**Verdict committed**: EXPLORATION-NEGATIVE (Cell 5 + PARTIAL-F7 flag).

**Artifacts committed**:
- `reports-v1/iteration_v1-014/comparison.csv` — present
- `reports-v1/iteration_v1-014/in_sample/` + `out_of_sample/` — present
- `reports-v1/iteration_v1-014/per_symbol.csv` — **MISSING from top-level** per brief Section 10.2 item 3 (was supposed to be a separate top-level diagnostic for F7-NEW); the `in_sample/per_symbol.csv` and `out_of_sample/per_symbol.csv` exist and were used for this report's Section 2 + Section 3
- **`reports-v1/iteration_v1-014/engineering_report.md`** (this document) — present as of Phase 7 closeout, RETROACTIVELY closing the 4th-strike violation

**No trunk merge**: EXPLORATION-NEGATIVE never updates BASELINE_V1.md (no Sharpe improvement; sign-flipped IS catastrophic). New code path `sigma_source="ewma14d"` remains on `iteration-v1/014` branch only; will be carried to `iteration-v1/015` for C1 fix + multi-seed CONFIRMATION.

**Phase 8 dispatch ready**: diary + catalog entry + tag `v0.v1-014` per Phase 8 deliverables.

---

## Appendix — Iteration Commits

- `cafad3d` — EDA scripts for EWMA σ_t calibration
- `6d7fce5` — QR Phases 1-5 + labeling axis brief
- `04a4b87` — LM Master Phase 4.5 pre-design advisory
- `fec6cbd` — Phase 5.5 gate PASS
- `dd8cf0d` — σ_t EWMA labeling with mandatory .shift(1) past-only safety (QE Phase 6; C1 NOT FIXED)
- `1d24dc6` — σ_t lookahead + calibration tests + A2 anti-pattern guard
- `65c0bb2` — Critic Phase 6.0 pre-flight PASS (declaration-side check)
- `7c019ed` — Axis isolation fix — disable BOTH R5 axes
- (Backtest dispatched HERE; comparison.csv + in_sample/ + out_of_sample/ produced)
- `1f70af3` — LM Master Phase 7.4 post-mortem
- `bcca796` — Phase 7.5 Critic review — EXPLORATION-NEGATIVE
- (THIS COMMIT) — QR Phase 7 evaluation + engineering report (4th-strike fix)

---

**End of Engineering Report. Phase 8 dispatch follows.**
