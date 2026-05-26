# Phase 5.5 Gate — iter-v1/019

OVERALL: PASS

## Iteration Type (from Brief Section 0.5)
TYPE: EXPLORATION
Cadence position: cycle-3 #4 of 10 (CONFIRMATION earliest at /027).

## Axis Family + Rotation Status (v1 mandatory)
FAMILY: per-cohort-specialization-ETH (NEW 10th axis family; FIRST usage)
ROTATION_STATUS: VALID

Prior 5 EXPLORATIONs from `briefs-v1/exploration_catalog.md`:
- iter-v1/014: labeling
- iter-v1/015: labeling (CONFIRMATION-spec; rotation N/A)
- iter-v1/016: sample-weighting
- iter-v1/017: universe
- iter-v1/018: per-cohort-specialization-LINK

`per-cohort-specialization-ETH` does not match any of the prior 5 families.
Even treating /018 + /019 as the same parent family `per-cohort-specialization`,
the COHORT + SPECIALIZATION dimension differs (LINK-only isolation vs ETH-only + direction-aware BTC-trend gate at +-8%).
Brief Section 0.6 declares orthogonality on three dimensions: different cohort, different specialization,
opposite-sign structural prior. LM Master Phase 4.5 independently confirms this is NOT a v2/019 same-pattern
re-discovery (per lgbm_advisor.md §1). Rotation VALID.

## HIGH-RISK Declaration (v1 mandatory)
HIGH-RISK: YES
Reason: dropping Models A/C/D/E + adding ETH-only Model G + post-hoc gate alters Optuna
training-objective domain (5 sym → 1 sym) AND realized trade stream simultaneously.
Mitigation: NONE opted in (single-seed-style EXPLORATION at ENSEMBLE_SIZE=3; /027 multi-seed
handles basin-lottery dissolution). Per HIGH-RISK cumulative tracker: /016 catastrophic,
/017 INERT, /018 PROMISING-INERT. No 3-consecutive catastrophic HIGH-RISK trigger yet;
no mandatory multi-seed requirement fires for /019.

## LM Master Response Verification (v1 mandatory)
- briefs-v1/iteration_v1-019/lgbm_advisor.md exists (commit 62e5056): PASS
- lgbm_advisor.md has Phase 4.5 section with numbered recommendations: PASS
- Brief Section 3.4 addresses each LM Master recommendation: PASS
  - Recs #1/#2 (informational confirmations): acknowledged in Section 3.4 intro + Informational block
  - Rec #3 (verdict-interpretation principle): ADOPTED — integrated as "directional flip" block in Section 3.4
  - Rec #4 (realistic IS lift +13-25%): ADOPTED — cross-referenced to Section 4 F3 band
  - Rec #5 (verdict-class priors 35/40/25): ADOPTED — Section 5 updated from QR 30/40/30
  - Rec #6 (n_eff_per_cell band [4,8]): ADOPTED — F-AXIS-MECHANISM #4 added informational
  - Recs #7/#8/#9/#10 (hyperparameter freezes: n_trials=18, ENSEMBLE_SIZE=3, Optuna bounds, gate constants): ADOPTED — Section 3.3 pins confirmed
  - Rec #11-#15 (informational confirmations): acknowledged in Informational block
  - Rec #16 (F-AXIS #3 elevated to LOAD-BEARING): ADOPTED — "LOAD-BEARING" marker added to Section 4 F-AXIS #3 row
  - Rec #17 (/020+ verdict-conditional matrix): ADOPTED — Section 11.7 cross-references LM §9
  - Rec #18 (cross-track import risk / fallback): ADOPTED informational — Section 3.1 documents vendor copy fallback

## Cadence Check (v1)
- Wall-clock budget declared: 26 minutes total (78% margin vs 2h cap; 70+ min buffer vs 1.6h BLOCK threshold): PASS
- EXPLORATION type: 2h cap applies: PASS
- CONFIRMATION type: N/A (this is EXPLORATION)

## Per-Section Status

- Section 0 (Data Split): PASS — OOS_CUTOFF_DATE = 2025-03-24 and training_months = 24 referenced
  throughout; IS window (earliest klines through 2025-03-24) and OOS window (2025-03-24 onward) implicit
  from config constants; per-cohort anchor IS -0.1022 / OOS +0.0503 from IS EDA script 01.

- Section 0.5 (Iteration Type, v1 mandatory): PASS — "EXPLORATION (cycle-3 #4 of 10)" at Section 0.1
  and repeated in iteration header. Cadence ledger reproduced.

- Section 0.6 (Architecture-Family Justification, v1 mandatory): PASS — axis family declared as
  per-cohort-specialization-ETH (NEW 10th family); prior 5 families listed; rotation VALID verified above;
  one-sentence rationale present; 3-way orthogonality check documented with LM Master + Critic
  convergence requirement noted.

- Section 1 (Hypothesis): PASS — one-paragraph specific hypothesis naming ETH-only cohort, Model A
  parameters, direction-aware BTC-trend gate at +-8% on 14d BTC return, AND the directional-flip
  claim vs ETH-in-pool OOS anchor +0.0503. Contains falsification logic with PROMISING/INERT/NEGATIVE/
  CATASTROPHIC branches. Not vague.

- Section 2 (IS-Only Evidence): PASS — committed at 2028c1d. 5 scripts + 12 CSVs under
  analysis/iteration_v1-019/. Scripts verified: 01_eth_trajectory.py, 02_btc_trend_separation.py,
  03_btc_trend_direction_aware.py, 04_gate_robustness.py, 05_predicted_eda_summary.py. Output tables
  reproduced in brief Sections 0.3, 2.1-2.7. IS-only per no-cheating rule (OOS columns in threshold
  sweep are labeled "informational" and use projected extrapolation, not OOS lookup).

- Section 2.5 (HIGH-RISK Axis Declaration, v1 mandatory): PASS — explicitly labeled HIGH-RISK with
  one-sentence reason (multi-domain training-objective change: universe 5→1 + post-hoc gate).
  Mitigation: NONE (opted not to multi-seed at /019; /027 handles). HIGH-RISK cumulative tracker
  populated (3 prior HIGH-RISK outcomes listed).

- Section 3 (Proposed Changes): PASS — single src/ file change (run_baseline_v1.py ~50 lines);
  zero changes to foundation files listed explicitly. LM Master responses at Section 3.4 (18 items:
  10 adopted, 0 modified, 0 rejected, 8 informational). Gate constants pinned at Section 3.3.
  Cross-track import documented with vendor-copy fallback if Critic blocks.

- Section 4 (Expected OOS Impact / Falsifiers): PASS — F1 through F8 + F-AXIS-MECHANISM 3-sub-check
  (#1 dispatch, #2 trade band, #3 gate fire-rate LOAD-BEARING) + F-AXIS #4 n_eff informational.
  All falsifier bands pre-registered with explicit pass/fail criteria. F1 anchored against ETH-in-pool
  OOS +0.0503 (not portfolio-level). F8 ETH-cohort trade band IS [80,200] / OOS [25,90].
  F-AXIS #3 fire-rate band IS [10%,30%] / OOS [5%,35%] with LOAD-BEARING marker from LM Master §9.
  Verdict-class probability prior at Section 5: 35/40/25 (INERT modal).

- Section 5 (Risk Mitigation / Verdict Priors): PASS — predicted verdict prior present (35% PROMISING /
  40% INERT / 25% NEGATIVE) with per-cell mechanism reasoning. Two specific mechanism predictions
  (gate fire rate 17.2% IS, ~55 OOS trades post-gate). Verdict hierarchy defined.

- Section 6 (Risk Management Design / Failure Modes): PASS — 7 failure modes including:
  (1) basin lottery, (2) gate over-kills OOS, (3) gate under-fires OOS, (4) ETH-drag-not-BTC-
  trend-conditional, (5) stateless gate deadlock proof (deadlock-impossible by construction per
  Section 6.5), (6) wall-clock breach (low probability with 78% margin), (7) PROMISING-MECHANICAL
  adjacency risk from LM Master §7. Stateless deadlock impossibility proof explicit (Section 6.5):
  numpy boolean mask pass, no persistent state, no drawdown-conditional ON/OFF.

- Section 7 (Pre-Registered Failure-Mode Prediction, v1 mandatory): PASS — Section 6 covers all
  failure-mode prediction categories: basin lottery, over-kill/under-fire gate regime shifts,
  INTRINSIC ETH drag mechanism falsification, PROMISING-MECHANICAL adjacency. Forward-looking and
  specific to this iteration's mechanism.

- Section 8 (Pre-Registered MERGE/NO-MERGE Criteria, v1 mandatory): PASS — 10-row verdict matrix
  with named verdict cells (PROMISING, PROMISING-INERT, PROMISING-INERT-no-effect, NEGATIVE-INERT,
  NEGATIVE-INTRINSIC, NEGATIVE-CATASTROPHIC, NEGATIVE-OVER-KILL, NEGATIVE-UNDER-FIRE,
  NEGATIVE-IS-COLLAPSE, NEGATIVE-DISPATCH), each with F1/F3/F-AXIS-MECHANISM/F7 threshold rows
  and Action column. EXACTLY ONE cell required. Hierarchy for tie-breaking defined. Thresholds
  locked pre-backtest.

- Section 9 (Library Stack, v1 mandatory): PASS — library versions declared (mlfinlab==1.4, pypbo,
  fracdiff>=0.10, statsmodels, lightgbm>=4.0, optuna>=3.0). Cross-track re-use declared:
  crypto_trade.strategies.ml.risk_v2.{apply_btc_trend_filter, BtcTrendFilterConfig,
  load_btc_klines_for_filter}. No new library dependency introduced. Fallback path
  (vendor copy into risk_v1_gates.py) documented if Critic Phase 6.0 blocks the import.

## New Family Declaration Check (v1 Critic Phase 7.5 Check 14 requirement)
per-cohort-specialization-ETH declared as NEW 10th axis family. Brief documents that
3-way convergence (QR + LM Master + Critic) on orthogonality is required for Check 14 PASS.
LM Master Phase 4.5 §1 independently confirms orthogonality. Critic Phase 6.0 will re-verify.
Convergence requirement explicitly noted in brief Section 0.6 and Section 3.5.

## Reasons (if BLOCK)
N/A — OVERALL=PASS.

---
Gate file written by QE at: 2026-05-26
Branch: iteration-v1/019
HEAD at gate time: f4b2884c0158a636653a655998debf8916cf9a91
