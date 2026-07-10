# REVIEW — Critic Pre-Flight of PROTOCOL-ENSEMBLE-L1-FORWARD (v2), pre-arming

**Reviewer:** Quant Critic (read-only). **Date:** 2026-07-10. **Persisted by orchestrator.**

## VERDICT: **CLEARED-FOR-ARMING — WITH CONDITIONS** (C1/C2 mandatory pre-T0; C3/C4 low; all
threshold/prose edits to the protocol doc, no re-runs, threshold-agnostic to the runner retarget)

## Supersession integrity: VERIFIED CLEAN (against logs, not claims)
paper-l1 equity/decisions header-only; gates.csv 3 rows all nan/0-months; runs.log 3 pre-T0 runs
all appended(eq=0,dec=0,phase_fwd=0); no post-T0 or burned-window metric ever computed. Retiring
the v1 protocol pre-T0 discards ZERO forward data; no peek informed the switch (IS evidence +
/007 adjudication only); sibling ban honored.

## Anchoring audit: /007 lesson applied
- FF-1 −28% / FF-2 −12%: CLEAN — single-phase IS numbers used as principled STRESS CEILINGS
  ("diversification evaporated to single-phase level"), not pass-guarantees; appropriately
  tighter than the retired −35%/−15%. Structural note: FF gates are catastrophe stops with a
  wide dead-band; decision weight correctly sits on P-Sharpe + M-gates + weekly rho telemetry.
- M-rho (rho_bar > 0.75 AND vol > 0.26, one-sided): SOUND — dual AND tests "diversification
  failed AND it hurts"; low rho grants nothing; high-bar backstop complemented by weekly logs.
- P-Sharpe +0.50→+0.60: LEGITIMATE post-observation calibration — the gated quantity (forward
  Sharpe) is genuinely unseen; conservative direction; 0.20 below central expectation with a
  quoted 42% miss rate — not tuned-to-pass. (C4: make this framing explicit.)
- T0 mechanical rule + §6.10 readiness criteria: crisp; ensemble is phase-symmetric so the
  T0-A/T0-B nominal wiggle has no gaming surface.

## Conditions
- **C1 [HIGH — MANDATORY pre-T0] M-crash strict-≥ mis-specified.** PASS required ensemble crash
  ≥ forward V0-ENSEMBLE crash — but /007 established the overlay is crash-NEUTRAL (IS: ENS-L1
  +0.933% vs V0-ENS +0.935% — the strict clause FAILS on the IS numbers themselves). Forward, a
  faithfully-neutral overlay coin-flips a spurious CONTRADICTION → overall FAIL. This re-creates
  the /007 mis-anchored-gate failure on the same gate. FIX: tolerance band — ensemble crash ≥
  V0-ENSEMBLE crash − 0.25pp (preserve, not improve); absolute clauses (crash > 0, short_px > 0)
  unchanged.
- **C2 [HIGH — MANDATORY pre-T0] M-crash N/A verdict completeness.** Crash months cluster
  (bimodal): a bull 12-month window plausibly (~20–40%) yields <2 forward crash months → the
  decisive gate is N/A, and §4.2's "PASS-or-N/A" would declare a HOLLOW full SUCCESS without the
  phase's raison-d'être ever tested. FIX (legitimate pre-registered extension trigger, not scope
  creep): (a) M-crash N/A at 12mo → extend once (6mo) to seek ≥2 crash months; (b) still N/A at
  18mo → verdict is QUALIFIED ("SUCCESS-except-crash-not-forward-tested"), NOT full SUCCESS,
  with the open-question deployment caveat.
- **C3 [LOW]** M-overlay dead zone [V0-ENS−0.25, V0-ENS): intentional buffer, coherent, but make
  the routing explicit — an evaluable CONCERN/dead-zone result blocks SUCCESS → PARTIAL.
- **C4 [LOW]** P-Sharpe +0.60: add the explicit "post-IS-observation, conservative direction,
  forward quantity unseen, deflated screen" disclosure.

## Passed cleanly
M-crash principle+relative re-anchoring (direction right; needs C1 tolerance); M-rho; FF floors;
supersession; T0 rule; sibling ban; n_eff=1 forward; dual parity anchors (+1.2826 / +1.1638);
honest error rates; carried cost-bias disclosures. Once C1+C2 land, ARM.
