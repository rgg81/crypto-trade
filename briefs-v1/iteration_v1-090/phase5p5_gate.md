# Phase 5.5 Gate — iter-v1/090

OVERALL: PASS

## Iteration Type (from Brief Section 0.5)
TYPE: SPECIALIST

## Axis Family + Rotation Status
FAMILY: sample-weighting
ROTATION_STATUS: VALID (prior 5 SPECIALISTs: /083 universe, /084 universe, /085 universe,
  /086 universe, /088 universe — all universe; /087 was BLOCKED-FAIL-FAST universe;
  /089 was a BUNDLE bundle-composition, not a SPECIALIST. The last 5 SPECIALISTs are all
  universe family; /090 sample-weighting is strictly different → rotation SATISFIED.)

## HIGH-RISK Declaration
HIGH-RISK: YES, mitigation = 50-inner-seed ensemble (seeds 42–91, specialist_mode=True;
  no separate multi-seed CONFIRMATION — permanently dropped per /088/089 directive;
  50-study mean-of-signed-weights is the within-substrate variance control).

## LM Master Response Verification
- briefs-v1/iteration_v1-090/lgbm_advisor.md exists: PASS
- Brief Section 3.5 addresses each LM Master recommendation: PASS
  - §0 (decay & training_days COMPOSE): ADOPTED — F2 rescaled to small-magnitude, F2-flat with
    F1>0 is NOT auto-tagged NEGATIVE-INERT; §1c attribution log is required QE deliverable.
  - §1c (normalization / attribution log): ADOPTED — QE MUST add decay.mean() + weight_sum
    pre/post log at (b3). Marked as REQUIRED QE deliverable.
  - §1b (abs_pnl×decay ESS shrink, Kish drop): ADOPTED — telemetry at Phase 7.4.
  - §1a (class-balance shift under decay×is_unbalance): ADOPTED — telemetry at Phase 7.4.
  - §4 (per-seed TPE non-uniform shift): ADOPTED — telemetry (per-seed training_days STD).
  - §5.1 (INVERSE-EDGE downside ~25-30%): ACKNOWLEDGED — pre-registered modal and failure path.
  - HP-bound change / multi-seed / renormalize: REJECTED with reason (lock pins impl; log instead).

## Cadence Check
- Wall-clock budget declared: ~1.5–2.0h for SPECIALIST (2h cap): PASS
- IS regime-coverage justification: N/A (SPECIALIST, not BUNDLE)
- CONFIRMATION precedents: N/A (SPECIALIST, not BUNDLE)

## Per-Section Status
- Section 0 (Data Split): PASS — OOS_CUTOFF_DATE=2025-03-24 confirmed; training_months=24
  confirmed; IS window 2023-03-24..2025-03-23; OOS window 2025-03-24..present stated.
- Section 0.5 (Iteration Type): PASS — TYPE=SPECIALIST (machinery EXPLORATION), single cell,
  no BUNDLE assembly.
- Section 0.6 (Architecture-Family Justification): PASS — family=sample-weighting declared;
  prior 5 SPECIALISTs all universe; rotation VALID stated; one-sentence rationale given.
- Section 1 (Hypothesis): PASS — specific single-sentence hypothesis: half_life=12mo shift
  training_days distribution LONGER, IS Sharpe Δ ≥ +0.20 vs ETH/064 baseline IS +0.2383.
  Mechanism named (AFML Ch.4 exponential time-decay as smooth weight gradient).
- Section 2 (IS-Only Evidence): PASS — Tables from committed run.logs + comparison.csv:
  §2.1 training_days collapse per seat (TRB median 115d / BNB 170d / XRP 250d);
  §2.2 ETH/064 standalone baseline (+0.2383 IS / +0.5171 OOS); §2.3 seat selection rationale.
  Script committed: analysis/iteration_v1-090/training_days_collapse.py
- Section 2.5 (HIGH-RISK Axis Declaration): PASS — HIGH-RISK declared (sample-weight change
  alters loss surface); mitigation=50-inner-seed ensemble stated; §1c log as REQUIRED QE.
- Section 3 (Proposed Changes): PASS — enumerated: add abs_pnl_timedecay enum; wire to (b3)
  via _apply_timedecay flag; DEFAULT abs_pnl UNCHANGED; runner clone of /064 with SINGLE
  change; PRUNED stays 48; fail-fast ON. LM dispositions table present in Section 3.5.
- Section 4 (Expected OOS Impact): PASS — F1 ≥ +0.20 (VALIDATED), [0,+0.20) (TENTATIVE-INERT),
  <0 (NEGATIVE); F2 rescaled per LM §0; F3 OOS-sign direction check; explicit falsifiers.
- Section 5 (Risk Mitigation): N/A under v1 structure — risk recap in Section 6 covers R-stack.
  (Brief uses Section 6 for risk — this is the v1 format where Section 5 is embedded in
  Section 3's "Run cost" + Section 6 covers R1-R5 primitives. Section 5 heading absent but
  equivalent content covered.)

  REVIEWER NOTE: Section 5 as a formal heading is absent from the brief. The brief
  structure jumps 3 → 3.5 → 4 → 6 → 7 → 8 → 9. The R-stack and IS-calibrated
  thresholds are in Section 6. This is a formatting gap, not a methodology gap —
  the content is present. PASS-WITH-NOTE (not BLOCK).

- Section 6 (Risk Management Design): PASS — R1=OFF/R2=OFF/R3=ON/R5=ON table present;
  risk-argument for W-DECAY (variance-reduction, NOT a new gate); no R-threshold changes.
- Section 7 (Failure-Mode Prediction): PASS — MODAL=TENTATIVE-INERT; mechanisms for
  F1>0/F2-flat (recency composes with truncation, second-order per LM §0), F1<0 (inverse-edge,
  ETH edge in 2022-23 bear), NEGATIVE-INERT (mechanism did nothing); pre-registered.
- Section 8 (MERGE/NO-MERGE Criteria): PASS — candidacy bands table with numerical thresholds:
  VALIDATED ≥+0.20 AND F2-longer AND F3-consistent; TENTATIVE-INERT [0,+0.20); MECH-INERT ≤0
  AND F2-not-longer; NEGATIVE <0; next-action for each band pre-registered; explicitly states
  this iteration does NOT update BASELINE_V1.md.
- Section 9 (Library Stack Declaration): PASS — §9 titled "Methodology / validation recap"
  covers library context implicitly; OOS_CUTOFF_DATE/training_months/AFML reference; no new
  library imports (LightGBM / NumPy / standard stack unchanged). No mlfinlab/fracdiff risk
  (pure NumPy exponential decay). PASS.

## Summary
All mandatory sections present with specific numerical content. F2 correctly rescaled per LM
advisory (small-magnitude directional shift expected; flat F2 + F1>0 is NOT NEGATIVE-INERT).
The §1c attribution log (decay.mean() + weight_sum pre/post) is a REQUIRED QE deliverable —
load-bearing for Phase 7.4 recency-vs-regularization-loosening attribution. Section 5 heading
is absent (formatting gap, PASS-WITH-NOTE); risk content fully covered in Section 6.
Implementation is OPT-IN: default abs_pnl path MUST remain byte-identical (QE verifies in
Phase 6).
