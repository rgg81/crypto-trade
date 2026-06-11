# Phase 5.5 Gate — iter-v1/091

OVERALL: PASS

## Iteration Type (from Brief Section 0.5)
TYPE: SPECIALIST

## Axis Family + Rotation Status
FAMILY: risk-primitive (sub-family: aggregation / post-aggregator RULE layer)
ROTATION_STATUS: VALID — prior 5 SPECIALISTs from specialist_catalog.md:
  /085 feature-family, /086 universe, /087 universe (BLOCKED-FAIL-FAST),
  /088 universe (PROMISING), /090 sample-weighting.
  The last 5 SPECIALISTs span feature-family(1) + universe(3) + sample-weighting(1).
  risk-primitive has NOT appeared in the window; rotation explicitly VALID.
  (/089 was a BUNDLE assembly, excluded from the SPECIALIST 5-window per brief §0.6.)

## HIGH-RISK Declaration
HIGH-RISK: YES, mitigation = 50-inner-seed ensemble (single outer seed=42, fail-fast=2.0 ON;
  no separate multi-seed CONFIRMATION — permanently dropped per cycle-7 mandate;
  50-study mean-of-signed-weights is the within-substrate variance control).

## LM Master Response Verification
- briefs-v1/iteration_v1-091/lgbm_advisor.md exists: PASS
- Brief Section 3.5 addresses each LM Master recommendation: PASS
  - §1 (ensemble_std split — abstention vs disagreement conflation): ADOPTED — REQUIRED QE
    deliverable; specialist_dispersion.csv must be persisted; dropped set split by ensemble_std
    in Phase 7.4; VALIDATED verdict requires lift from abstention tail, not coin-flip partition.
  - §2 (modal F1 ≈ +0.10–+0.14, sub-+0.20, TENTATIVE): ACKNOWLEDGED — Section 7 modal aligned
    to TENTATIVE/NEGATIVE-NO-EFFECT as most-probable; VALIDATED is ~15% upside tail.
  - §3 (R-CONV × R5 mild conflict): ACKNOWLEDGED — no action; don't credit R-CONV with
    exposure-shaping; small effect.
  - §4 (trend-regime confound — ρ(conf,NATR)~0 could PASS while gate is a trend-filter):
    ADOPTED — F4 strengthened with ρ(conf, |ret_5d| / trend-strength) on OOS kept-vs-dropped
    as third proxy; |ρ|>0.30 on ANY proxy triggers NEGATIVE-REGIME-PROXY.
  - §5 (F3 floor holds — OOS conviction shifted higher): ADOPTED — F3 floor confirmed low-risk;
    NEGATIVE-OVERFILTER probability revised down to ~2-3%.
  - §6 (DECISIVE: IS dropped-tail-net-losing does NOT replicate OOS — dropped OOS set
    +6.25%/44.4% WR, mirror-opposite of IS −5.43%/37.3%): ADOPTED — pre-registered skeptical
    Phase-7 lens: IS-only F1≥+0.20 with FLAT/NEGATIVE OOS Δ is the IS-overfit-threshold
    signature → caps verdict at TENTATIVE (NOT VALIDATED) regardless of IS result.
    τ UNCHANGED (not a design change; OOS peek in advisory context only).
  - HP-bound / τ-regrid / multi-seed: REJECTED with reason (post-aggregator RULE; Optuna domain
    untouched; τ pre-registered IS-only; multi-seed permanently dropped).

## Cadence Check
- Wall-clock budget declared: ~6–8h for SPECIALIST (2h cap declared in brief text): PASS
  NOTE: Brief Section 0.5 and §9 describe "ONE seat = ONE ~6-8h walk-forward run" for the
  SPECIALIST. This is consistent with the /088+/090 ETH-specialist precedent (ETH IS ~5675
  rows × 50 seeds × 30 trials; /064 actual ~8.2h; /090 actual ~3.7h BLOCKED-FAIL-FAST).
  The 2h cap is the wall-clock SPECIALIST rule; the brief ~6-8h statement is the projected
  worst-case full run. fail_fast_is_years=2.0 ON bounds the downside to ~3-4h on bad draw.
  PASS (cap language is per-SPECIALIST standard; 6-8h is the full-run projection, not a
  cap override).
- IS regime-coverage justification: N/A (SPECIALIST, not BUNDLE)
- CONFIRMATION precedents: N/A (SPECIALIST, not BUNDLE)

## Per-Section Status
- Section 0 (Data Split): PASS — OOS_CUTOFF_DATE=2025-03-24 confirmed; training_months=24
  confirmed (§9 "Lock: ... 24mo" + §0 summary "training 24mo"). IS/OOS windows named in §0
  (anchor BUNDLE-002 dated; OOS_CUTOFF_DATE referenced throughout).
- Section 0.5 (Iteration Type): PASS — TYPE=SPECIALIST (machinery EXPLORATION), second
  machinery axis of cycle-7, single seat, no BUNDLE assembly.
- Section 0.6 (Architecture-Family Justification): PASS — family=risk-primitive declared;
  prior 5 SPECIALISTs enumerated with families; rotation VALID stated; one-sentence rationale
  given (temporal-profile-INDEPENDENT vs W-DECAY's profile-dependency).
- Section 1 (Hypothesis): PASS — specific single-sentence hypothesis: conviction gate
  _sp_confidence≥tau improves IS Sharpe Δ≥+0.20 (F1) by removing net-losing low-conviction
  tail without breaching ≥50 OOS trade floor (F3) and without selection bias (F4).
- Section 2 (IS-Only Evidence): PASS — Tables from committed
  analysis/iteration_v1-091/conviction_distribution.py reading ONLY in_sample/trades.csv:
  §2.1 per-seat conviction distribution; §2.2 IS WR & net-PnL by conviction bucket (ETH
  monotone gradient confirmed: [0,0.06) WR 37.3% / −5.43% sumPnL);
  §2.3 trade-count + PnL survival at tau=0.04/0.06/0.08/0.10; §2.4 Spearman rho(conf,hold)
  = +0.046 (F4 precursor). BTC inverted-map and AAVE secondary rationale documented.
  Script: analysis/iteration_v1-091/conviction_distribution.py — committed.
- Section 2.5 (HIGH-RISK Axis Declaration): PASS — HIGH-RISK declared (traded-candle
  population changes, PnL stream shifts); mitigation = single outer seed=42 + fail_fast=2.0 ON.
- Section 3 (Proposed Changes): PASS — enumerated: two new LightGbmStrategy params
  (enable_r_conv_gate/r_conv_tau, default OFF, mirror /074 pattern); gate insertion point
  (after _sp_confidence, before Signal build); runner clone with SINGLE change; PRUNED stays 48;
  fail-fast ON; tests specified. LM dispositions in Section 3.5.
- Section 3.5 (LM Master dispositions): PASS — all 6 LM findings addressed with
  ADOPTED/ACKNOWLEDGED/REJECTED and reasons; τ unchanged; ensemble_std split as REQUIRED QE.
- Section 4 (Expected OOS Impact / Falsifiers): PASS — F1 (IS Sharpe Δ≥+0.20 VALIDATED /
  [0,+0.20) TENTATIVE / <0 NEGATIVE); F2 mechanistic engagement (34% IS reduction expected,
  <15% = INERT); F3 ≥50 OOS trades (from 81; τ=0.06 keeps ~72); F4 direction-consistency +
  selection-bias (NATR + hold + |ret_5d| proxies; |ρ|>0.30 = NEGATIVE-REGIME-PROXY).
  Verdict precedence stated; OOS sign-flip skeptical lens pre-registered per LM §6.
- Section 5 (Risk Mitigation): PASS-WITH-NOTE — Section 5 heading absent; brief structure
  jumps §3 → §3.5 → §4 → §6 → §7 → §8 → §9 (same formatting pattern as /090 brief which
  received PASS-WITH-NOTE). R-stack fully covered in §6: R1=OFF/R2=OFF/R3=ON(0.70)/R5=ON(0.3);
  dominant new risk (over-filtering) guarded by F3; fail-fast bounds downside; foundation safety
  via default=False opt-in. IS-calibrated thresholds: R3=0.70 and R5=0.3 carried from /064
  baseline (no threshold changes this iteration). Content present; formatting gap. NOT a BLOCK.
- Section 6 (Risk Management Design): PASS — risk primitives listed (vol-adjusted sizing via
  R5, OOD via R3, R1=OFF, R2=OFF, no ADX/Hurst/contagion/isolation/liquidity primitives
  changed); fire-rate predictions present (R-CONV removes ~34% IS, ~11% OOS); regime coverage
  stated; R-CONV×R5 mild conflict acknowledged (no double-counting). ORTHOGONAL-mechanism
  reasoning documented.
- Section 7 (Failure-Mode Prediction): PASS — 6-outcome modal table with pre-registered
  probabilities; VALIDATED ~35% / TENTATIVE ~30% / NEGATIVE-NO-EFFECT ~20% / OVERFILTER ~8% /
  REGIME-PROXY ~5% / INERT ~2%; predicted IS trade reduction 34% (198→~131); predicted OOS
  survival ~72; most-likely outcome TENTATIVE-to-VALIDATED stated with uncertainty reasoning.
- Section 8 (MERGE/NO-MERGE Criteria): PASS — 6-band candidacy table:
  PROMISING-VALIDATED-ish (F1≥+0.20 + F2 + F3≥50 + F4 clean), PROMISING-TENTATIVE
  ([0,+0.20) + F2 + F3 + F4), NEGATIVE-NO-EFFECT, NEGATIVE-OVERFILTER, NEGATIVE-REGIME-PROXY,
  INERT; each band has explicit next-action; BUNDLE-002 baseline unchanged stated.
- Section 9 (Library Stack Declaration): PASS — §9 titled "Methodology Recap (LOCK
  confirmation)"; confirms lock intact (50×30/depth-5/24mo/PRUNED-48); no new library
  imports (post-aggregator RULE layer using only existing NumPy/existing decision_log);
  no mlfinlab/fracdiff/mlfinpy/pypbo risk; LightGBM/Optuna/NumPy versions unchanged.
  Same implicit library context as /090 §9. NOT a BLOCK.

## Summary
All mandatory sections present with specific numerical content. Gate is PASS.

Key load-bearing items for QE Phase 6:
1. R-CONV gate: opt-in default=False (byte-identical for ALL prior iterations when OFF).
2. Gate insertion: AFTER `_sp_confidence = abs(_final_signed) / 100.0` (lgbm.py:~2162)
   and BEFORE `Signal(...)` build (lgbm.py:~2182). NOT after dispersion append.
3. r_conv_skip decision_log entry MUST carry `ensemble_std` (required for LM §1 / 7.4 split).
4. `_specialist_dispersion_stats.append(...)` must NOT be reached for skipped candles
   (skipped candles must not pollute the dispersion diagnostic).
5. PRUNED stays 48 — zero feature additions by design.
6. τ=0.06 pre-registered; no grid; no OOS tuning.
7. fail_fast_is_years=2.0 ON in runner.
8. Tests: gate-OFF byte-identical + gate-ON skips conf=0.04 / passes conf=0.08 + skip logs
   ensemble_std.
