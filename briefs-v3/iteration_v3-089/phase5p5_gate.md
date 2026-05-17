# Phase 5.5 Gate — iter-v3/089

OVERALL: PASS

iter-v3/089 is a CORRECTED-BUILD EXPLORATION on the RETAINED /088 cross-sectional `LGBMRanker` architecture — it carries the two mandatory corrections (Critic /088 Recs #2/#3) plus the genuine cost-aware-construction axis. The QR brief is complete across all 11 sections, every design parameter is IS-selected or a-priori from cited research, and the Section-3 build spec is precise and already wired at the /089 setup commit. PASS.

---

## Per-Section Status

- **Section 0 (Data Split)**: PASS — `OOS_CUTOFF_DATE = 2025-03-24` and `training_months = 24` declared IMMUTABLE; `OOS_CUTOFF_MS = 1742774400000` confirmed in the runner; IS/OOS windows stated.
- **Section 0.5 (Iteration Type)**: PASS — CORRECTED-BUILD EXPLORATION, cycle-3 slot #8 of 10; explicitly NOT a fresh re-architecture and NOT a /059 incremental knob — the corrected next build on the RETAINED /088 architecture. Grounded in the /088 closeout (the cross-sectional line is the active v3 research direction).
- **Section 1 (Hypothesis)**: PASS — a specific, causal one-paragraph claim: the /088 model transfers OOS (rank-IC +0.043, t≈4.6); the book lost money to a sign inversion + turnover drag; correcting the sign and attacking turnover structurally (quintile + overlapping holds + no-trade band) materially reduces the net loss. The hypothesis is HONEST — it pre-states that the construction fixes alone do NOT reach a positive IS net Sharpe and that the gross-signal expansion is deferred to /090. Section 1.3 explicitly addresses the bold-research mandate (this is relentless iteration, not defeatism).
- **Section 2 (IS-Only Evidence)**: PASS — TWO committed EDA scripts, both IS-only. `turnover_construction_eda.py` (E1–E6) runs a TRUE IS-internal walk-forward of the RETAINED `LGBMRanker` (trains on IS months, predicts the next IS month — no OOS row read). `gross_signal_eda.py` (G1–G4) is a model-free cross-sectional-predictor EDA. All 10 output CSVs confirmed present. The evidence is concrete and numerical: E1 corrected-sign IS gross Sharpe +0.0485; E2 quintile gross Sharpe +0.077 vs tercile +0.049; E3 hold=3 cuts turnover 2.2× and lifts net Sharpe −0.57→−0.42; E4 τ=0.020 IS-best net Sharpe −0.31; E5 the combined construction halves the IS net loss (−0.65→−0.31) and cuts turnover 2.7×; E6 the 0.138 turnover ceiling; G1 quintile is the spread sweet spot and decile is too thin at N=22; G4 the gross-signal feature expansion is +2% IC-IR (real but marginal — deferred to /090). Category-matching absent — every figure is IS-data-derived.
- **Section 3 (Proposed Changes / Build Spec)**: PASS — see feasibility judgment below.
- **Section 4 (Expected OOS Impact)**: PASS — the comparability caveat vs the per-symbol baseline is correctly carried from /088; the dual evaluation (absolute +1.0/+1.0 floor plus architecture-internal diagnostics) is present; the /088 cross-sectional book (IS −0.6403 / OOS −0.5418) is the honest like-for-like ANCHOR 1; the /059 baseline is ANCHOR 2 with the caveat. The five falsifiers F1–F5 are pre-registered with numerical thresholds — and F2 (the HARD turnover ceiling 0.138) is a genuine MERGE-blocking gate, not a footnote. The predicted OOS impact is honest (modal OOS monthly Sharpe in [−0.30, +0.10] — materially improved on /088 but most likely sub-floor).
- **Section 5 (Risk Mitigation)**: PASS — the turnover controls (overlapping holds + no-trade band + the hard ceiling) are the /089-specific risk addition; the table flags each control IS-calibrated or a-priori AND gives the simulated historical effect (the IS-internal walk-forward turnover 0.325→0.120, net Sharpe −0.65→−0.31). The structural controls (dollar-neutral, inverse-vol, quintile diversification, burn-in, embargo) are carried from /088.
- **Section 6 (Risk Management Design)**: PASS — honest scoping: the legacy 7-gate stack stays deferred (re-introducing it would confound the construction measurement — the same call /088 made and the Critic accepted); /089's risk apparatus is the structural construction plus the two new turnover controls.
- **Section 7 (Failure-Mode Prediction)**: PASS — a pre-registered probability distribution over five named outcomes (45% construction-works-but-sub-floor, 20% net-positive-sub-floor, 20% F3-fires, 10% F2-fires, 5% full-success). The /088 calibration lesson (a thin-signal turnover-cost outcome is the modal risk, not a tail) is explicitly recorded and applied — the modal outcome is honestly named as sub-floor.
- **Section 8 (MERGE/NO-MERGE Criteria)**: PASS — a LOCKED taxonomy with five classifications (SUSPICIOUS, CONSTRUCTION-FALSIFIED, CONSTRUCTION-VALIDATED-PROMISING with FULL/FOUNDATION sub-cases, CONSTRUCTION-PARTIAL, NULL) in disjunctive precedence with numerical gates per class. The turnover ceiling and the /088-book OOS Sharpe are wired into the gates. States explicitly that an EXPLORATION cannot update BASELINE_V3.md.
- **Section 9 (Library Stack)**: PASS — LightGBM (`LGBMRanker`, `lambdarank` — the RETAINED /088 model), Optuna, pandas/numpy. No new third-party dependency — every /089 change is pure pandas/numpy.
- **Section 10 (QR Audit Trail)**: PASS — Section 10.1 documents the orchestrator scope-steer and the QR design ownership. Section 10.2 documents five literature sources with IDs (Poh/Lim/Zohren arXiv 2012.07149; Constantinides 1986 / Davis-Norman 1990 *Math. OR* 15(4):676; Jegadeesh-Titman 1993 *JoF* 48(1) + the 2023 review; the cost-aware-rebalancing literature *FMPM* 2022 + Baldi-Lanfranchi 2024; the crypto cross-sectional reversal net-of-cost literature *IRFA* 2024/2025). Section 10.3 is the no-cheating audit (see below). Section 10.4 is an honest senior read.
- **Section 11 (Reproducibility Stamp)**: PASS — EDA / brief / setup SHAs to be backfilled; reports path and run mode declared; the deferred future-iteration axes recorded (notably /090's gross-signal feature expansion).

---

## Feasibility Judgment — Section-3 Build Spec

Section 3 is precise and the build is in fact already wired at the /089 setup commit (`bb8c231`). The QE Phase-6 step is the backtest run + the engineering report. The specified changes:

**Correction #1 — the SIGN FIX (Section 3.1)**: `build_positions` LONGs the TOP quantile (`sorted_syms[-n_leg:]`, highest scores) and SHORTs the BOTTOM (`sorted_syms[:n_leg]`, lowest scores) — the inverse of /088. The `predict_ranking` and `label_cross_sectional_rank` docstrings are corrected to state the forward mapping from first principles. Verified: a deterministic-score functional test confirms `build_positions` longs the highest scores (`test_sign_fix_longs_highest_scores`).

**Correction #2 — the CPCV-PROXY FIX (Section 3.2)**: `_compute_xs_cpcv` now takes the backtest `results` and computes each CPCV path's Sharpe + max-DD from the ACTUAL realised long-short net return (the per-bar book net_pnl), not a label-grade self-correlation. The `XS_REQUIRED_GAP = 88` `expected_gap` assertion is retained.

**The cost-aware construction (Section 3.3)**: three new constants in `cross_sectional.py` — `XS_QUANTILE_FRAC = 0.20` (quintile, EDA E2/G1), `XS_HOLD_BARS = 3` (overlapping holds, EDA E3 + Jegadeesh-Titman), `XS_NO_TRADE_BAND = 0.020` (EDA E4 + Constantinides/Davis-Norman). `run_cross_sectional_backtest` forms a 1/3-sized tranche each bar, maintains the live overlapping tranches → the raw book, applies `apply_no_trade_band` → the book, and accrues PnL + turnover fee on the book. All three are passed explicitly at the runner call site.

**The HARD turnover ceiling (Section 3.4)**: `XS_TURNOVER_CEILING = 0.138`; `compute_turnover_per_bar` + the gate evaluation are wired into `comparison.csv` and `dsr.json`.

**Unchanged from /088**: the 13-feature set, the 22-symbol universe, the H=3 label, the `XS_REQUIRED_GAP = 88` embargo, the monthly walk-forward + the e149e9d fix.

The build is feasible and is already implemented; the Phase-6 step is the run.

---

## No-Cheating Verification

Verified against the committed EDA code, not the brief's prose:

- `turnover_construction_eda.py` — the IS-internal walk-forward filters `panel[panel["open_time"] < OOS_CUTOFF_MS]` and trains/tests only inside IS; no OOS row enters the EDA. The quantile/hold/band are selected on the IS net Sharpe.
- `gross_signal_eda.py` — `_load_is` filters `df["open_time"] < OOS_CUTOFF_MS`; every G1–G4 table is IS-only. Sign-alignment uses the same IS rank-IC.
- The sign fix and CPCV-proxy fix involve no parameter tuning — a first-principles correction and a methodology correction.
- The turnover ceiling 0.138 is the IS-best construction's IS turnover (0.120) × 1.15 — an IS-derived a-priori gate.
- `OOS_CUTOFF_DATE` / `training_months` untouched; the IS window is never trimmed.

---

## Test Coverage Verification

`tests/strategies/ml/test_cross_sectional.py` carries 6 new /089 tests (36 tests total, all passing): `test_sign_fix_longs_highest_scores` (the sign fix), `test_no_trade_band_holds_within_band` / `test_no_trade_band_zero_is_identity` / `test_no_trade_band_reduces_turnover` (the no-trade band), `test_compute_turnover_per_bar` (the turnover diagnostic), `test_iter089_construction_constants` (the EDA-selected construction constants). The 30 /088 tests still pass — no regression.

---

## Gate Decision

PASS. The brief is complete, every design parameter is IS-grounded or a-priori from cited research, the corrections and the cost-aware construction are precisely specified and already wired, the turnover ceiling is a genuine pre-registered hard gate, and the brief is honest about the residual (the gross signal is thin; /089's modal outcome is sub-floor; the gross-signal expansion is deferred to /090). The QE Phase-6 step is the backtest run + the engineering report.
