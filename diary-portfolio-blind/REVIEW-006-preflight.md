# REVIEW-006-preflight — Critic Pre-Flight Audit of the EXPLORATION-006 Brief

**Reviewer:** Quant Critic (read-only). **Date:** 2026-07-10. **Persisted by orchestrator.**
**Scope:** frozen brief + RISK-006 calibration + DIAGNOSTIC-003 + engine plumbing (44 tests), BEFORE any variant run.
**OOS quarantine honored** (CONFIRMATION-005.md not read). Baseline-blinding honored.

## OVERALL VERDICT: **PASS-WITH-CONDITIONS**

The design is rigorous on the dimensions that usually break these phases: look-ahead safety,
engine byte-identity, causal DD-brake, non-vacuous leak positive-controls, IS-grounding of every
control, and consistently maintained IS-only / non-deployability framing. One load-bearing defect
(F1) must be fixed pre-run or the headline G-mania verdict is uninterpretable. Fixable without
unfreezing any calibrated C1–C5 value; if no market-only mania rule can be committed, escalate to
BLOCK.

## Per-check verdicts (9 mandated checks)

1. **Look-ahead audit C1/C2 series: PASS.** z365 is trailing (`rolling(365, min_periods=182)`,
   blind_risk_calib_006.py:59-64); disp/fund lookbacks trailing; NaN policy inert-safe; consumed
   at [k-1] (blind_engine.py:509-510); hard IS-slice before any series build makes OOS reach
   structurally impossible (blind_sanity_lowvol.py:29-36).
2. **Engine plumbing: PASS.** Byte-identity genuinely tested (5 explicit-inert variants);
   DD-brake causal (peak from equity[..k-1], blind_engine.py:466-479); short_exclude preserves
   rank partition (:183-196); composition order matches brief (:500); leak positive-controls
   non-vacuous (brake fires, exclusion fires, post-cutoff change asserted). 44/44.
3. **Selection-on-dependent-variable: FAIL → F1 (blocking condition).** CRASH bucket has a
   committed market rule (blind_diag_003_monthly.py:336). MANIA bucket is a hardcoded literal
   (blind_risk_calib_006.py:42-43) with NO generating rule; membership tracks strategy P&L.
4. **Calibration integrity: PASS (F5 note).** No strategy-Sharpe threshold scan; C1 floor 0.5
   chosen a-priori over the higher-P&L 0.0 (evidence "+1.001" was sanity check, not selector).
   C2's K/Q evidence is partly P&L-adjacent (forward short_px of excluded set) — recorded.
5. **Gate-set coherence: PASS** except G-mania's near-tautology (the mechanical face of F1).
   G-crash +1.55%/mo consistent with C3's ~12% de-gross. No gate impossible or non-discriminating.
6. **Decision-tree freeze: PASS (F3 nit).** Nested-prefix logic deterministic; surviving stack
   re-gated on all 7 HARD gates; every outcome pattern maps to exactly one prefix. Rule 2's crash
   trigger not pinned to a named run (L2 vs L3).
7. **OOS-contamination-of-design: PASS per control.** C1/C2/C3/C4 grounded in IS artifacts
   (DIAGNOSTIC-003; REVIEW-005 F1 intra-rebal drift was pre-OOS). C5 = falsification arm. No
   control requires specific OOS numbers. Residual: the fix-mania-not-crash direction rests on
   the IS thesis alone — correctly scoped as IS design-validation.
8. **Multiple-testing: PASS-with-tempering (F6).** n_eff≈4 honest for the explicit ladder DOF;
   omits the mania-list hand-definition DOF and the second-IS-redesign-after-burned-OOS
   compounding. Deflation informational-only here; future forward-validation must size against a
   larger cumulative IS selection surface.
9. **Warmup-63 protocol: PASS (F4 nit).** warmup=max(vol_lookback,30) confirmed
   (blind_engine.py:582); common [63:] re-slice correct and sufficient; turnover_ann computed
   full-array (:616-618) hence already comparable — but G-turnover's metric source unstated.

## Ranked findings

- **[F1 HIGH — BLOCKING CONDITION] MANIA bucket has no committed market-only generating rule;
  membership tracks strategy P&L.** C1 flag map: 2023-01 flagged 62%, EXCLUDED (strategy winner
  +3.3%); 2023-11 flagged 43%, EXCLUDED; 2021-03 flagged 23%, INCLUDED (strategy worst-10 loser).
  The boundary follows P&L, not the declared market signature → G-mania (V0+2.0pp) is
  near-tautological. **Fix:** commit a reproducible MARKET-ONLY rule (e.g. monthly btc_ret +
  x_disp/fund z from blind_diag_003_monthly.py, or ex-ante C1-candle-coverage threshold),
  regenerate the list, re-freeze brief §3.4 + calib script; report the delta vs the old list as
  quantified contamination.
- **[F2 MED] "C1 cannot fire in crash months" is false for the 3 BTC-UP bear-rally crash-bucket
  months** (2021-07 +18%, 2021-08 +13.1%, 2022-07 +19.0% — qualify via trailing-DD clause).
  RISK-006 §1.3 showed only the 5 BTC-down crash months. In these 3, the short leg was squeezed
  (2021-08 short_px −0.142; 2022-07 −0.146), so C1 firing HELPS — must not be misattributed as
  "crash alpha preserved." **Fix:** correct §3.3/§6 predictions (split BTC-down capitulation vs
  BTC-up bear-rally); engineer reports C1 coverage across all 20 crash months. 2022-07→08 turn
  unexamined by the stress test — noted.
- **[F3 LOW-MED] Decision-tree Rule 2 crash trigger ambiguous** between crash(L2)/crash(L3).
  **Fix:** pin to crash(L2).
- **[F4 LOW] Metric-source under-specification:** G-turnover reads
  `res.metrics['turnover_ann_one_way']` (full-array) vs other HARD gates on rets[63:] — state it.
- **[F5 LOW] C2 calibration evidence P&L-adjacent** (recorded for the multiple-testing ledger;
  parameter values themselves are ex-ante distribution facts).
- **[F6 LOW] n_eff accounting** should name the mania-list DOF + IS-reuse compounding in §7.

## Conditions for PASS (all pre-run, none unfreezes a calibrated value)

1. **[MANDATORY — F1]** Committed market-only MANIA rule + regenerated frozen list + re-frozen
   brief/calib references; delta vs old list documented. No rule → BLOCK.
2. **[REQUIRED — F2]** Corrected §3.3/§6 C1-crash predictions; engineer must report C1 flag
   coverage on all 20 crash months.
3. **[REQUIRED — F3]** Rule 2 pinned to crash(L2).
4. **[REQUIRED — F4]** Exact metric source for G-turnover vs [63:]-recomputed gates stated.
5. **[RECORD — F5/F6]** Ledger notes in §7.

## Style note vs /005
/006 matches or exceeds /005's structure (frozen gates, decision tree, falsification arm, leak
spec, n_eff accounting) with ONE regression: /005 carried an explicit forthright selection-bias
defense section; /006 asserted the mania bucket "market-regime-defined" without disclosing the
hand-authored list. Fixing F1 restores parity of candor.

---

# ADDENDUM — Focused re-verification after QR condition fixes (same date)

## VERDICT: **CLEARED-FOR-RUN** (matrix numbers unaffected by the one remaining prose item)

1. **F1 fix CONFIRMED real.** `blind_mania_rule.py` is market-only (membership consumes only the
   C1 mania_gate array + ms grid; no strategy P&L/weights/equity), reproducible (`__main__`
   self-test regenerates the frozen 13-month list), and the hardcoded literal in
   blind_risk_calib_006.py is replaced by the import (line 37). New frozen bucket (n=13):
   2020-08, 2020-11, 2020-12, 2021-01, 2021-02, 2021-08, 2021-10, 2023-01, 2023-11, 2023-12,
   2024-02, 2024-03, 2024-11. Delta vs retired hand list: +{2020-08, 2021-08, 2021-10, 2023-01,
   2023-11}, −{2021-03}. G-mania re-anchored: V0_mania +2.52%/mo → threshold ≥ +4.52%/mo.
2. **P&L-during-threshold-selection concern: ACCEPTABLE-WITH-DISCLOSURE, no re-fix.** Independent
   a-priori anchor exists (0.40 ≈ 2× the gate's 19.3% base rate); the consultation was exercised
   in the ANTI-favorable direction (the gate-favorable ≥50% list, V0 −1.6%/mo, was rejected; the
   harder ≥40% list chosen); the +2.0pp margin was frozen pre-fix and unchanged.
3. **Conditions 2–5 verified landed** (crash-bucket sub-regime split + engineer C1-coverage
   requirement; Rule 2 pinned to crash(L2); turnover metric source stated; §7 ledger notes).
4. **NEW FINDING — winner-clip miscount [MANDATORY prose fix pre-Phase-7]:** brief §3.4/§7 and
   the blind_mania_rule.py docstring claim four "C1-clip-HURTS" months (2020-08/2020-12/2021-08/
   2024-02). Short-leg attribution says otherwise: 2020-08 short_px −0.086, 2021-08 −0.142,
   2024-02 −0.041 are short-LOSERS where C1 HELPS; only 2020-12 (short_px +0.143) is a genuine
   clip-hurts month. So 12/13 bucket months push G-mania toward pass by C1's construction.
   G-mania must be reframed as a MECHANISM-EFFICACY test (discriminating for C3-in-stack
   candidates via the symmetric de-gross of 2020-12/2024-02 winners; near-tautological for a
   V1-only candidate); a G-mania pass must NOT be read as independent regime alpha. Plus two §7
   anti-tuning affirmations (the V0-P&L threshold-review consultation, anti-favorable direction;
   the frozen +2.0pp margin) and a one-line non-disjointness disclosure (crash ∩ mania =
   {2021-08} → G-crash/G-mania mildly correlated).
5. **Bucket overlap ruling:** 2021-08 in both buckets is COHERENT (a bear-rally squeeze is both a
   drawdown-regime and a mania month); gates move the same direction; disclose non-independence.

**Binding condition:** items in (4) must be committed to the frozen brief BEFORE the Phase-7
SUCCESS/PARTIAL/FAIL verdict is rendered. The 9-variant matrix may run meanwhile — no produced
number depends on the prose.
