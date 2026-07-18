# Critic audit — team-08 (t08-oi-price-confirmation-v3, approved pivot) — VERDICT: PASS

- **HARNESS: PASS.** All six checks PASS on rerun, zero violations; byte-identical to frozen
  `out/harness.json`.
- **SCAN+GREP: CLEAN.** `strategy.py` uses close + `aux["oi"]` + eligibility only; scratch
  clean; no prohibited access.
- **SHAS: CLEAN.** All match; tree matches freeze commit 836b9f8a.
- **LEDGER: CLEAN.** 8/40 entries, evaluator-stamped, monotone. Pivot ordering verified:
  e01–e03 (reversal family) precede the journaled pivot approval ("ledger continues at 3/40" —
  matches); e04, the first OI experiment, is stamped AFTER approval. Dead-family record (§6)
  matches the e01–e03 hypotheses and pre-registered thresholds.
- **FAMILY FIDELITY: CONFIRMED.** Confirm-only S1γ0 structure: σ-scaled 18-candle displacement
  rank hard-gated by sign(Δlog OI over 18 candles) — exactly the approved pivot
  `t08-oi-price-confirmation-v3`. Distinctness protections honored: the
  conditioned-minus-unconditioned kill criterion from the pivot approval was actually run
  (e08) and reported. See the cohort cross-team section for the t08-vs-t10/t03/t04
  construction comparison.
- **ARTIFACT CONSISTENCY: CLEAN — both orchestrator-flagged disclosures verified against
  primary artifacts.** (a) The V2 thin margin appears in `is_report.md` §4 exactly as the
  scratch artifact records it — recomputed from `out/scratch/results_e08.json`: selected
  config conditioned act_1x 0.939 vs gate-off 0.904 ⇒ **Δ = +0.035 @1×**, called "formal PASS
  but noise-level (SE ≈ ±0.4)"; Δ = +0.179 @2× (0.578 vs 0.399); the NEGATIVE neighbor Δ@1×
  −0.044 at (18,4) is disclosed rather than hidden; (9,4) +0.320/+0.493. (b) The ~0.49
  dilution is stated in §2 with the arithmetic shown (0.4596/0.939), the "worse than the ~0.7
  estimated at pivot time" admission included, and the board number explicitly owned. All
  §1/§3 numbers match `out/is_metrics.json` (0.4596/0.2049, −28.9/−32.6%, 131.9, 24/15, cost
  0.3604/0.7208, funding +0.0848, net +0.163, regime table exact). Breadth floor met (15
  short-side median ≥ 5).
- **OVERFIT SMELL (informational):** the honest reading — which the team itself states — is
  that at the shipped 6-day horizon the OI gate's 1× marginal value over plain displacement is
  statistically indistinguishable from zero; its value shows up in stress-cost robustness,
  drawdown, and chop. The book is bull-loaded (active-window bull +2.55; effectively bull-only
  at 2×) and net-long-tilted (mean_net +0.163), all disclosed. This is a weak result reported
  with high integrity; weak performance is never a FAIL.
