# Critic audit — team-09 (t09-trade-size-composition-v3, approved pivot) — VERDICT: PASS

- **HARNESS: PASS.** All six checks PASS on rerun, zero violations; byte-identical to frozen
  `out/harness.json`.
- **SCAN+GREP: CLEAN.** No prohibited access; scratch via evaluator seam only.
- **SHAS: CLEAN.** All match; tree matches freeze commit c0ac4838.
- **LEDGER: CLEAN.** 10/40 entries, evaluator-stamped, monotone. Pivot ordering verified:
  e01–e04 (liq-squeeze family) precede the pivot approval ("ledger continues at 4/40" —
  matches); e05, the first composition experiment, follows it. The (9,1)→(42,1) selection
  amendment is written INTO the e09 ledger entry (stamped before e09/e10 results) — the audit
  trail the report claims exists, does.
- **FAMILY FIDELITY: CONFIRMED — the crux verified in code.** `strategy.py` consumes exactly
  `pn["quote_volume"]`, `pn["trades"]`, and `aux["eligibility"]` — **zero price inputs** (no
  `close` access anywhere; verified by reading the full file). The registry text is
  implemented literally (ratio-of-sums average trade size, recent-vs-overlap-free-baseline,
  centered rank, 1–4wk horizon W=42). F3 load-bearing controls decisive (vol-attention fade
  −0.58, count-fade −0.30 vs +0.83) — the composition term, not volume attention, is the edge.
- **ARTIFACT CONSISTENCY: CLEAN — escalation-ruling disclosure verified verbatim.** §3
  contains everything the journaled ruling required: the +0.46 monthly correlation (+0.69 for
  W=9), the net residual −0.03 with the turnover-doubling cost explanation, the +0.50 pre-cost
  (+0.38 funding-off) gross residual, the statement that the e09 ex-ante bar FIRED, and the
  SHIP-with-full-disclosure ruling itself. All §1 numbers match `out/is_metrics.json`
  (0.8299/0.5900, −43.93/−45.32%, 80.72, 19/19, funding +0.1147, cost 0.2305/0.4610, regime
  table exact, chop −0.2849 disclosed in bold). Dead-family record (§5) is a model negative
  result (evidence-monotone continuation, sign-flip NOT shipped because it belongs to claimed
  families). Breadth floor met.
- **OVERFIT SMELL (informational):** moderate, fully disclosed. The net edge is substantially
  carried by the momentum-correlated component (residual net −0.03) — the correlated-failure-
  mode warning is in §6. The shipped cell sits at the favorable end of its robustness band
  (B=180 +0.54, z-transform +0.60 vs +0.83), disclosed with the pre-registration defense
  (defaults fixed in the brief before the grid ran).
