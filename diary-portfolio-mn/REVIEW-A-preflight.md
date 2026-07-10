# REVIEW-A-preflight — Critic Pre-Flight of the EXPLORATION-A Brief (MN track)

**Reviewer:** Quant Critic (Fable, read-only). **Date:** 2026-07-10. **Persisted by orchestrator.**
**Scope:** frozen brief + all MN infrastructure + predecessor methodology refs, BEFORE any run.
Quarantines honored (no baseline artifacts, no iter_*.py, no diary-portfolio-top20, no
CONFIRMATION-005; MN holdout sealed — verified at grep level).

## VERDICT: **PASS-WITH-CONDITIONS** — six pre-run fixes (C1–C6), one dated amendment to the
brief before the QE script runs. None touches a frozen gate threshold, signal parameter, or
decision-map tier (except the C4 disambiguation, frozen pre-run because it is two-readable).
Two conditions (C1, C2) would otherwise cause a deterministic mid-run abort.

## Findings (ranked)
- **F1 [HIGH] Analytic 2×-twin error repeated.** Brief §1.6 claims the exact analytic identity
  "per the /007 identity" — /007 is the document that DISPROVED it (fixed-share drift divides by
  cost-bearing equity; exact only at rebal candles; ~7e-5 elementwise drift measured). The
  frozen §7 assert (≤1e-12) is guaranteed-false. → **C1: ground-truth 2× re-runs authoritative
  on all 4 cells (+84 backtests); analytic twin demoted to cross-check, tolerance ≤1e-3
  reported, never asserted at 1e-12.**
- **F2 [HIGH] Per-name cap not implementable through the UNCHANGED engine** — no hook exists
  between the weighting builder and the hedge overlay; cap genuinely binds (post-floor
  membership ≤18 ⇒ rank-neutral max weight >10%); infeasible below n=9; no min-members guard in
  the engine. → **C2: sanctioned opt-in `weight_cap` engine extension (inert default,
  byte-identity + semantics tests, ITERATIVE redistribution to fixed point) + frozen
  infeasibility/min-members rule (suggest: skip rebal below N/2 members, counted).**
- **F3 [MED-HIGH] Ensemble warmup must be 273, not /007's 63.** rolling_residual_beta first
  all-finite at tranche-local t=269; betas consumed at [k−1]; first fully-hedged rebal k=273
  (13×21); common-mask first-True = **293** on the original grid. With warmup=63 the G1/G2
  windows include ~200 effectively-unhedged candles per tranche. → **C3: warmup=273 derived
  programmatically + asserted; identical mask across all 4 cells; trim-invariance assert scoped
  to the common slice; ensemble turnover from per-tranche series; COVID-crash-outside-window
  disclosure.**
- **F4 [MED] A2 trigger two-readable on joint failures** (G2-CRASH + another neutrality HARD).
  → **C4: freeze one rule — suggested: A2 iff G2-CRASH fails, {G1a,G1b,G2-MANIA,G3} all pass,
  mechanism gates all pass; concurrent G4 failure permitted only when the worst bucket is
  CRASH; anything broader = plain FAIL, no A2.**
- **F5 [MED] Neutrality measurement mechanics unpinned** (3 quiet DOFs on HARD gates). →
  **C5: pin — regressor = BTC/ETH hold returns (open→open) on the same grid; rolling
  min_periods=135; bucket labels = return-candle mn_regime_labels; any G2/G4 bucket with n<30
  on the common slice → loud N/A-FAIL, never a silent pass. (F7's liquidity-floor array pin —
  the same 270-candle-history-masked trailing mean the universe ranks on — folds in here.)**
- **F6 [LOW-MED] G-durable sign + cost treatment.** Engine funding sign is +=drag; the income
  stream is −funding_rets. → **C6: pin the sign flip; evaluate G-durable on the frozen uncosted
  definition; report the costed funding-only Sharpe alongside as an honesty line.**

## Check verdicts
1 Split/leak: PASS (grep-verified; import-time literal pins; guard unit-tested; no
confirmation_reveal outside mn_split). 2 DIAG-A→brief translation: PASS (signal verbatim;
floor/cap existence pre-registered, values post-diagnostic but edge-adverse and cost-measured;
rebal=21 choice disclosed and gate-adverse on the headline). 3 Gate anchoring: PASS (G1–G5
pre-date DIAG-A; 2×-cost in ratio form; survival floors framed as non-discovery; G-turnover
loose = tripwire, noted). 4 Analytic twin: FAIL as written → C1. 5 A2: PASS with C4 (genuinely
bounded; holdout unspent on second failure). 6 Predictions: PASS (crash-β band honestly
straddles the G2 bound; recommend adding a G3-margin band ~[0.02,0.12], not required).
7 Variant matrix: PASS (one-factor star; funding-only correctly a within-run decomposition).
8 Ensemble reuse: C2+C3 (imports clean; __main__-guarded; aux path unused). 9 Ledger: PASS
(~7 cells + A2 → 8; N20 promotion would be a selection event requiring re-ledgering — on the
record). 10 Decision map: C4 + C5(iv).

## Bottom line
With C1–C6 amended and dated pre-launch, the contract is sound. The blinding/split machinery is
the strongest this repo has produced; the gates put the risk where the predecessor failed
(G2-CRASH predicted as the likely failure point, and the brief says so); the contingency is
bounded. Both HIGH findings were deterministic-abort defects — exactly what pre-flight exists
to catch.
