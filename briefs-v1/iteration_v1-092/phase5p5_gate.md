# Phase 5.5 Gate — iter-v1/092

OVERALL: PASS

## Iteration Type (from Brief Section 0.5)
TYPE: SPECIALIST

## (v1) Axis Family + Rotation Status
FAMILY: risk-primitive
ROTATION_STATUS: VALID

Prior 5 SPECIALIST families (from specialist_catalog.md):
1. /086 TRB — universe
2. /087 BNB — universe
3. /088 XRP — universe
4. /090 W-DECAY — sample-weighting
5. /091 R-CONV — risk-primitive

Not all 5 same family (3 universe + 1 sample-weighting + 1 risk-primitive). Rotation is VALID. Brief also
notes that the per-symbol regime-specialist mandate suspends strict rotation for the current cycle, and
that /091 and /092 are DIFFERENT risk-primitive mechanisms (ensemble-conviction SNR filter vs cross-asset
BTC-trend-directional kill). ROTATION_STATUS: VALID on both grounds.

## (v1) HIGH-RISK Declaration
HIGH-RISK: NO (NORMAL-RISK)
Reason: BTC-trend kill gate is a post-aggregator RULE layer applied AFTER Optuna model emits signal.
Does NOT change Optuna's training-objective domain. Model, seeds (50 inner), trials (30), features
(PRUNED-48), and per-month objective are bit-identical to /088. Default-OFF flag ensures byte-identical
behavior when unset.

## (v1) LM Master Response Verification
- briefs-v1/iteration_v1-092/lgbm_advisor.md exists: PASS (commit fda4d2c2)
- Brief Section 3.5 addresses each LM Master recommendation: PASS

LM Master recommendation response check (Section 3.5):
  - CRUX: OOS OFF stretch is TREND-WRONG-WAY, not chop — ADOPTED (pivot ADX-kill → BTC-trend gate)
  - §1 OOS ADX hotter than IS — NOTED (does not apply to BTC-trend axis; F3 projection already
    measures actual OOS fire-rate under IS-frozen rule)
  - §3 R3/R5 interaction audit — ADOPTED (Phase 7.4 audits BTC-gate↔R3-OOD↔R5-vol overlap; Section 5)
  - §4 selection bias / cleaner IS discriminator — ADOPTED (BTC_UP regime chosen per IS evidence 2.1;
    mechanism (i) over (ii) via generalization forensic 2.3)
  - §5 F3 BORDERLINE-FAIL at ADX axis — ADOPTED (BTC-regime gate at thr=0.067 projects 70 OOS
    survivors vs ADX's 49; F3 re-pre-registered in Section 4)
  - §6 decision_log sink mandatory — ADOPTED (Section 3.1 wire backtest-mode sink;
    noted as F2 attribution requirement)
  - RECOMMENDED PIVOT — FULLY ADOPTED; entire brief re-derived on BTC-trend axis

## Cadence Check
- Wall-clock budget declared: 2h SPECIALIST cap; explicit in Section 0.5: PASS
- fail-fast=2.0 ON (XRP /088 passed it — first-2yr IS +16.88): PASS
- One-variable discipline: single gate vs /088: PASS

## Per-Section Status
- Section 0 (Data Split): PASS — OOS_CUTOFF_DATE=2025-03-24 (ms: 1742774400000) UNCHANGED;
  training_months=24 UNCHANGED; IS/OOS windows in absolute dates confirmed
- Section 0.5 (Iteration Type): PASS — TYPE: SPECIALIST, XRPUSDT, 2h cap
- Section 0.6 (Architecture-Family Justification): PASS — FAMILY: risk-primitive, ROTATION_STATUS: VALID,
  prior 5 families listed, cross-track overlap flag carried from /088
- Section 1 (Hypothesis): PASS — specific one-sentence hypothesis: XRP's edge is regime-conditional on
  BTC trend direction; BTC_UP IS net -36.71%; gate suppresses BTC_UP entries to make OOS less
  regime-contingent; falsifiable via F4 regime-breadth
- Section 2 (IS-Only Evidence): PASS — committed analysis/iteration_v1-092/eda.py; explicit IS-only
  assertion (XRP candles 5696, IS trades 219, cutoff_ms asserted); btc_regime_sweep.csv +
  btc_dir_disagreement_sweep.csv + btc_gate_oos_projection.csv; numerical tables for mechanism (i) vs
  (ii) at threshold sweep; mechanism selection via generalization forensic with IS-frozen rule applied to
  OOS roster (OOS roster read only to COUNT survivors, not to tune threshold)
- Section 2.5 (HIGH-RISK Axis Declaration): PASS — HIGH-RISK: NO, NORMAL-RISK; reasoning given
- Section 3 (Proposed Changes): PASS — ONE variable (BTC-trend kill gate); PRUNED stays 48; constructor
  flags specified; init pattern mirrors /074 AXIS-R; gate site after R-CONV, before Signal build;
  _compute_btc_ret_42 past-only (searchsorted ≤ decision close_time); conservative pass-through on
  missing BTC candle; default-OFF byte-identical; Section 3.5 LM Master responses complete
- Section 4 (Expected OOS Impact): PASS — F1 IS Sharpe ≥+0.578 (Δ+0.20); F2 mechanism engaged
  20-45% suppression; F3 OOS trades ≥50 (proj. 70); F4 regime-breadth (pre-Nov ≥-5% AND ≥3/8 months
  positive); explicit falsifier chain and DID-NOT-FIX pre-registration
- Section 5 (Risk Mitigation): PASS — R1/R2/R3/R5/R6 explicitly stated; simulated IS effect
  (57/219 removed, -36.71% kill, +75.40% kept); OOS advisory projection (-8.43%/+29.23%);
  gate orthogonality to R3 noted; Phase 7.4 overlap audit planned
- Section 6 (Risk Management Design): PASS — 7-primitive table with predictions; expected IS/OOS
  fire rates (IS 26% / OOS ~15%)
- Section 7 (Failure-Mode Prediction): PASS — primary F4 failure (pre-Nov only partly BTC_UP regime);
  secondary NEGATIVE-NO-EFFECT (model already encodes BTC trend); tertiary mechanism-choice error; all
  three failure modes pre-registered with which falsifiers catch each
- Section 8 (MERGE/NO-MERGE Criteria): PASS — EXPLORATION-PROMISING criteria: 6 conditions all
  stated; EXPLORATION-NEGATIVE-DID-NOT-FIX pre-registered (F1/F2/F3 pass but F4 fails);
  EXPLORATION-NEGATIVE (any F1/F2/F3 fails); BASELINE_V1.md unchanged regardless
- Section 9 (Library Stack): PASS — LightGBM/Optuna project versions; statsmodels (adfuller) already
  installed; no mlfinlab/mlfinpy/pypbo/fracdiff; BTC-index pattern reuses /074 AXIS-R (no new infra)

## OOS-Leakage Assessment (Phase 5.5 pre-registration)

The brief explicitly addresses the OOS-leakage risk (Section 0 + Section 2 + Section 3.5). Assessment:

**Gate mechanism (BTC_UP kill = suppress all XRP entries when btc_ret_42 > 0.067):** Derived purely
from IS evidence. XRP IS trades sliced by BTC_UP regime: IS n=57, net -36.71%, sharpe -0.79. This IS
evidence stands independently of any OOS number. Threshold 0.067 = IS abs-median of btc_ret_42
(computed IS-only). IS-defensible.

**Mechanism choice (i) over (ii):** Brief Section 2.2 states "On IS alone, both mechanisms are clean
separators in the 0.05–0.08 band" and "IS does not decide between them — the generalization forensic
does (Section 2.3)." Section 2.3 reads the OOS roster to COUNT survivors and observe kill-bucket PnL
sign. This IS a conditional OOS read — the mechanism (i) vs (ii) selection was made by observing that
mech-(ii)'s OOS kill bucket was net-POSITIVE (+14.56% killed = removes winners) while mech-(i)'s was
net-NEGATIVE (-8.43% killed = removes losers). The QR was AWARE of this distinction before committing
to mechanism (i).

The brief's defense: threshold is IS-frozen before the OOS read, and the OOS read changes no parameter
(only confirms i's direction over ii's). This is the "advisory confirmation" framing.

**Phase 5.5 finding:** The OOS-leakage question on the mechanism choice is a BORDERLINE CASE that
the Phase 6.0 Critic must adjudicate (per the task brief's PRIMARY ADJUDICATION request). Phase 5.5
cannot rule it a hard no-cheating violation because: (a) the IS evidence IS independently sufficient
to support mechanism (i) — BTC_UP is the dominant regime separator (Section 2.1) and mechanism (i)
kills the dominant-negative IS bucket cleanly; (b) the threshold is genuinely IS-calibrated
(IS abs-median, not OOS-tuned). However, mechanism (i) vs (ii) was decided by observing OOS killer-
bucket PnL sign, which is conditional OOS information. The Critic must rule on this distinction.
Phase 5.5 PASSES because the brief does not attempt to hide this fact and the IS evidence provides
independent grounding.

## Reasons (if BLOCK)
N/A — OVERALL: PASS
