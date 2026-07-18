# Critic audit — team-06 (t06-ls-ratio-contrarian-v1) — VERDICT: PASS

- **HARNESS: PASS.** All six checks PASS on rerun, zero violations; rerun byte-identical to
  frozen `teams/team-06/out/harness.json`.
- **SCAN+GREP: CLEAN.** `strategy.py` consumes only `aux["ls_accounts"]` + `aux["eligibility"]`,
  numpy import only; no prohibited paths/network/obfuscation anywhere; scratch reaches data
  only via the evaluator seam.
- **SHAS: CLEAN.** sources_sha256 and net_is.csv SHA match; `reported` equals
  `out/is_metrics.json`; tree matches freeze commit 542e9d9e.
- **LEDGER: CLEAN.** 10/40 entries, evaluator-stamped, monotone (19:11:41→19:18:46), freeze
  19:28:19 after last entry. The journaled data amendment (19:21:14, source "team-06 e01")
  traces to the ledgered e01 coverage diagnostic (19:11:41) — ordering coherent.
- **FAMILY FIDELITY: CONFIRMED.** Per-coin z-score fade of the global L/S account ratio,
  centered rank = exactly `t06-ls-ratio-contrarian-v1`. Boundary discipline is exemplary: e06
  pre-committed "no sign flips — follow-sign variants belong to other families and are
  dropped," and the taker_ls_vol follow-sign variant was dropped citing team-05's claim rather
  than harvested.
- **ARTIFACT CONSISTENCY: CLEAN, one prose nit.** All §1/§3/§4/§5 numbers match
  `out/is_metrics.json` (1.1757/0.7437, −32.6/−40.1%, 93.8, 20/20, funding +0.0701, cost
  0.2576/0.5152, regime table exact). Breadth floor met. The ratio-panel corruption and
  dilution are carried prominently and honestly (honest window 2023-01-13→2024-06-30, ~21 of
  54 live months, honest-window ≈1.60 @1× labeled *[scratch, e05/e09]*; bear regime declared
  untestable; 2×-chop 0.113 called out as the weakest honest number). **Nit (informational):**
  the "diluted ≈ 0.58×" factor is the sqrt-live-fraction approximation (√(18/54) ≈ 0.577); the
  empirical headline-to-run-rate ratio is ≈ 0.73 (1.1757/1.60) because the three
  corrupt-coverage island months contributed positive P&L. The labeled numbers themselves are
  consistent; only the derived factor is loose.
- **OVERFIT SMELL (informational):** selection-wise low — plateau-center W=90 chosen over a
  higher-scoring W=45 peak (disclosed), extra-lag robustness tested (e10). Evidence-wise the
  caution is sample size, not tuning: the run-rate claim rests on ~18 live months, and the
  strategy has effectively zero bear-regime evidence — both stated plainly.
