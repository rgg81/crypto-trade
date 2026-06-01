# Phase 5.5 Gate — iter-v1/029

OVERALL: PASS

Re-evaluation at brief HEAD `586a791` (patch commit: "Phase 5.5 BLOCK fix — add Sections 6, 7, 9").
Prior gate verdict: BLOCK (3 missing sections). This gate replaces the prior.

---

## Iteration Type (from Brief Section 0.1 + header)
TYPE: EXPLORATION — "Cycle-4 EXPLORATION 2/10" declared in header and Section 0.1.
No formal `0.5`-labeled subsection; brief's Section 0.5 is "LM Master tail re-weighting."
Content unambiguously declares EXPLORATION. Treating as PARTIAL-PASS consistent with
established v1 brief format for prior iterations. Non-blocking.

## (v1 only) Axis Family + Rotation Status
FAMILY: per-cohort-specialization-DOT-v2
ROTATION_STATUS: VALID

Verification — prior 5 EXPLORATIONs (excluding /026 sanity slot and /027 CONFIRMATION-technical-failure
per skill Rule 4; /028 row absent from exploration_catalog.md but family confirmed from
`briefs-v1/iteration_v1-028/research_brief.md` Section 0.6):

| iter | family                                       |
|------|----------------------------------------------|
| /022 | per-cohort-specialization-LTC                |
| /023 | feature-family (funding-rate)                |
| /024 | model-arch (regime-conditional)              |
| /025 | feature-family (OI delta)                    |
| /028 | per-cohort-specialization-LTC-v2             |

Three distinct families across 5 slots — NOT 5-of-5 monoculture. Rotation discipline honored.
/029 `per-cohort-specialization-DOT-v2` is a NEW family (different cohort + orthogonal mechanism
class: symmetric BTC-trend gate vs /028's atr_sl label-shift vs /022's asymmetric long-suppress).
VALID.

## (v1 only) HIGH-RISK Declaration
HIGH-RISK: NO (NORMAL-RISK)
Brief Section 2.5: Path C (symmetric BTC-trend gate ±8%) is a post-Optuna stateless trade-stream
filter applied via `risk_v2.apply_btc_trend_filter`. Does NOT change Optuna's training-objective
domain (label distribution, feature set, training universe, bar interval). Rationale adequate.

## (v1 only) LM Master Response Verification
- briefs-v1/iteration_v1-029/lgbm_advisor.md exists: PASS (commit `c4a4d14`)
- Brief Section 3.4 addresses each LM Master recommendation: PASS

LM Master §1-§7 cross-check:
- §1 HYBRID classification: ADOPTED in Section 3.4 §1
- §2 Hyperparameter recs + §2.5 ESCALATE n_trials/ENSEMBLE_SIZE: ADOPTED (n_trials 18→35,
  ENSEMBLE_SIZE 3→10); sub-recs explicitly DEFERRED with single-axis isolation rationale
- §3 Feature rank predictions: ADOPTED INFORMATIONAL
- §4 Path C BINDING: ADOPTED; Paths A/B/D/E explicitly rejected with mechanistic rationale
- §5 Falsifier pre-registration: ADOPTED VERBATIM (5 F-AXIS items carried into Section 2)
- §6 Track-record commentary: ACKNOWLEDGED
- §7 /030 routing: ADOPTED PRE-COMMIT

All 7 LM Master sections explicitly addressed. PASS.

## Cadence Check (v1)
- Wall-clock budget declared: 35-55 min total (Section 3.6); INSIDE 2h EXPLORATION cap: PASS
- Cycle-4 EXPLORATION 2/10 declared: PASS
- CONFIRMATION precedent count: N/A (this is EXPLORATION)
- CONFIRMATION imports prior EXPLORATION variations: N/A

---

## Per-Section Status

- Section 0 (Data Split): PARTIAL-PASS
  `OOS_CUTOFF_DATE = 2025-03-24` and `training_months = 24` present in Section 10.1
  (Reproducibility). IS window and OOS window absolute dates not explicitly named in a
  standalone Section 0 block — embedded across Sections 0 and 10.1. Anchor dates
  verifiable from brief. Consistent with prior v1 briefs (/028, /027). Non-blocking.

- Section 0.5 (Iteration Type Declaration, v1): PARTIAL-PASS
  Brief header + Section 0.1 unambiguously declare EXPLORATION. No formal "Section 0.5"
  sub-label (Section 0.5 is "LM Master tail re-weighting"). Non-blocking per established
  v1 brief format.

- Section 0.6 (Architecture-Family Justification, v1-only): PASS
  Full axis family + prior 5 families table + rotation status VALID + mechanism-class
  differentiation rationale present in Section 0.6 and Section 3.8. PASS.

- Section 1 (Hypothesis): PASS
  Section 0 H1 paragraph: specific cohort (DOT-only) + mechanism (symmetric BTC-trend gate
  ±8%) + expected OOS Δ band ([+0.05, +0.55] centered modal +0.30) + causal mechanism
  (removes OOS LONG weak-up-BTC −8.47% drag) + prior analog (ETH /019 PROMISING +0.50).
  PASS.

- Section 2 (IS-Only Evidence): PASS — committed script: `analysis/iteration_v1-029/dot_cohort_classification.py` (commit `0d7a090`)
  Numerical tables from committed CSVs: dot_direction_split.csv (8 rows), dot_btc_trend_bucket.csv
  (16 cells), dot_monthly_pnl.csv (IS H1/H2 split), dot_exit_reasons.csv. CSVs committed at
  `0d7a090`. Brief cites SHA `bbab148` (reference error; actual commit is `0d7a090`). Minor
  reference error — non-blocking; CSVs confirmed committed and verifiable. PASS.

- Section 2.5 (HIGH-RISK Axis Declaration, v1-only): PASS
  NORMAL-RISK declared with mechanism rationale (post-Optuna stateless filter; no training-objective
  domain change). PASS.

- Section 3 (Proposed Changes + LM Master responses): PASS
  Sections 3.1-3.8 present: universe, labels, mechanism spec, LM Master responses §1-§7 all
  addressed, configuration, wall-clock, code changes (single `elif` branch + 4 constants),
  axis family declaration for Critic Check 14. PASS.

- Section 4 (Expected OOS Impact): PASS
  Section 4 (Verdict Matrix): 6-row OOS Δ band table with explicit verdict cells + F-AXIS
  override caps (F-AXIS #3 < 5% → INERT-NO-EFFECT; F-AXIS #3 > 35% → NEGATIVE; F-AXIS #5
  < 2 → PROMISING-INERT). Modal prediction documented. Falsifier present. PASS.

- Section 5 (Risk Mitigation): PASS
  R1 (ON, IS-calibrated 15-day cooldown), R2 (OFF, documented with rationale), R3 (ON,
  70th-pctl Mahalanobis cutoff), gate fire-rate monitoring, TP-exit floor monitoring,
  wall-clock kill-switch. PASS.

- Section 6 (Risk Management Design): PASS  [PREVIOUSLY BLOCK — now verified]
  Section 6 contains a structured 4-row gate-stack table (R1 cooldown, R2 DD scaling, R3
  Mahalanobis, BTC-trend gate ±8%) with columns: State, IS fire-rate (pred), OOS fire-rate
  (pred), Regime coverage, Gate-attribution estimate. Section 6.1 provides regime coverage
  narrative (BTC-trend gate targets OOS LONG weak-up-BTC −8.47% + strong-down −5.80% buckets;
  R3 targets OOD months; R1 targets micro-streaks). Section 6.2 provides IS-calibrated gate-off
  vs gate-on PnL attribution (+14.58% IS net recovery estimate from symmetric fire). Section 6.3
  repeats verdict-capping reminders. Required structured content is present. PASS.

- Section 7 (Pre-Registered Failure-Mode Prediction, v1/v3 mandatory): PASS  [PREVIOUSLY BLOCK — now verified]
  Section 7 contains 3 forward-looking failure mode predictions with metric signatures:
  7.1 GATE OVER-KILL (OOS fire-rate > 30%; symmetric gate kills +5.59% SHORT strong-up wins;
      metric signature: fire-rate > 30% + TP-exit count < 2 + Δ ∈ [−0.30, −0.10]);
  7.2 H1-CATASTROPHIC BASIN-FLIP (Optuna relocates to H1-fit basin; metric signature:
      OOS Δ < −0.20 + H1-month cluster underperform + IS stays near baseline);
  7.3 SHORT-DOMINANT BASIN LOTTERY (single-seed=42 flips to SHORT-dominant boundary;
      metric signature: OOS LONG < 10 trades + conditional Δ on gate preserving SHORT strong-up).
  All 3 failure modes have named metric signatures for Phase 8 diary verification. Meets
  the 1-2 paragraph forward-looking prediction requirement with more detail. PASS.

- Section 8 (Pre-Registered MERGE/NO-MERGE Numerical Criteria, v1/v3 mandatory): PASS
  Section 8 (Verdict Cell Determination Table): 8-row pre-registered verdict table with specific
  F-AXIS conditions and verdict cells (TECHNICAL-FAILURE, INERT-NO-EFFECT, NEGATIVE-INERT,
  PROMISING-INERT cap, PROMISING, PROMISING-INERT mild, INERT, NEGATIVE-CLEAN/CAT). Pre-committed
  before backtest. PASS.

- Section 9 (Library Stack Declaration, v1/v3 mandatory): PASS  [PREVIOUSLY BLOCK — now verified]
  Section 9 declares:
  - mlfinlab: NOT INSTALLED (fallback: in-tree implementations; not invoked at /029)
  - mlfinpy: NOT INSTALLED (same in-tree path; not invoked)
  - pypbo: N/A (EXPLORATION single-seed; PBO informational only, not invoked)
  - fracdiff: NOT INSTALLED (no new features; ADF flow N/A)
  - statsmodels: 0.14.6 (not invoked — no new feature stationarity checks)
  - lightgbm: 4.6.0 (LOAD-BEARING)
  - optuna: 4.8.0 (LOAD-BEARING)
  - numpy: 2.2.6 (LOAD-BEARING)
  - pandas: 3.0.0 (LOAD-BEARING)
  Section 9.1 documents invocation status per library. Section 9.2 confirms no version bumps
  and uv.lock unchanged. PASS.

---

## Reasons (if BLOCK)
None — all 3 prior BLOCK items now satisfy requirements.

---

## Path Forward

OVERALL=PASS. Dispatch to Phase 6.0 Critic pre-flight.

**Phase 6.0 dispatch** (v1 mandatory, per skill §3.5):

Orchestrator must invoke `quant-critic` with the following Phase 6.0 pre-flight prompt:

```
[Phase 6.0 PRE-FLIGHT] [track: v1] Run pre-flight review for iter-v1/029.
Read briefs-v1/iteration_v1-029/research_brief.md AND
briefs-v1/iteration_v1-029/phase5p5_gate.md (confirm OVERALL=PASS).
Read QE's src/ diff: `git diff <parent-baseline>..iteration-v1/029 -- src/`.
Run mini-checks 1, 13, foundation regression, cadence, falsifier.
Emit critic_preflight.md content as final message text with
OVERALL=PASS or BLOCK + Path Forward (if BLOCK).
```

QE must NOT launch the backtest until Phase 6.0 Critic pre-flight returns OVERALL=PASS.

---

## Non-blocking notes preserved from prior gate

- Brief Section 0.3 cites commit SHA `bbab148` for analysis CSVs; actual commit is `0d7a090`. QR should correct the SHA reference at Phase 8 closeout.
- /028 row is absent from `briefs-v1/exploration_catalog.md`. QR documentation debt; not blocking /029 but should be addressed at /028 Phase 8 closeout.
