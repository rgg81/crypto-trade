# REVIEW-005 — Critic Integrity Audit of EXPLORATION-005 (MERGE candidate)

**Reviewer:** Quant Critic (read-only). **Date:** 2026-07-10. **Verdict: MERGE-TO-CONFIRMATION.**
Track's first MERGE candidate → maximally rigorous review. (Persisted by orchestrator.) OOS sealed.

## OVERALL: CONDITIONAL-PASS → MERGE-TO-CONFIRMATION
+0.913 is the genuine output of a leak-safe engine at rebal=21. Parity (rebal=6 = +0.088 = /002 ±0.005).
No new engine code (param change only) → 33/33 green is the right surface. The +0.09→+0.91 delta is
attributable SOLELY to cadence. NOT a small-sample artifact: 2025Q1-stripped 2020-24 avg = **+0.898**.

## Selection-bias verdict: DEFENSIBLE-BUT-TEMPER (not airtight, not too thin)
- **A-priori STRONG:** 5 pre-result artifacts name "weekly first" (skill mandate; REVIEW-002 S1;
  REVIEW-004 Path-Forward; RISK-004; PHASE7-004) — BEFORE the +0.91 was observed.
- **Plateau not spike:** {21,42,63} all clear +0.84–0.97; {6} lone fast outlier +0.09.
- **Pre-registered point ≠ IS-max (STRONGEST):** brief froze rebal=21; IS-max of the 4-pt scan is 42 (+0.97).
  If mined, 42 would've been picked. Signature of legitimate pre-registration.
- **All-years-positive:** 2020 +1.51 / 2021 +1.10 / 2022 +1.07 / 2023 +0.35 / 2024 +0.46 / 2025Q1 +2.15.
  Both diagnostic regimes (2021 shorts-don't-blow-up, 2022 longs-don't-crash) strongly positive.
- **TEMPERING:** multiple-testing across the TRACK (5 explorations × constructions + cadence scan ≈ n_eff 10-15) →
  Bailey DSR haircut ~0.15-0.25 Sharpe → honest OOS expectation +0.65-0.80, NOT +0.91. The +0.91 is an upper bound.
  Brief §3(b) "monotone slow>fast" is hump-shaped in Sharpe (true only for turnover) — re-word in future artifacts.

## The +0.91 decomposition — REAL
- Turnover channel ~+0.10-0.20 (138x→55x saves ~6.3%/yr).
- Signal-quality channel ~+0.60-0.70 (the bulk): short-leg net price P&L −0.86 (rebal=6) → −0.06 (rebal=21) —
  weekly filters the pump-and-drop adverse-selection churn (2021 short −0.73 vs −0.01) while preserving 2022
  bear dampening (+0.94 vs +0.93). Carver half-life rule; empirically visible in leg attribution.
- Funding channel preserved (2021 −208bps net income vs /002 −240bps).

## Leak@rebal=21 — MEANINGFUL (non-vacuous)
`test_..._midvol_rebal21`: corrupts sig+open+funding forward at cutoff=260 (260%21=8, BETWEEN rebal steps
252 & 273 — the general case). Asserts weights/turnover/equity/funding_rets[:260] bit-identical; non-vacuous
guard confirms post-cutoff change. Catches cadence-dependent look-ahead at the sparser decision points. PASS.

## /002 FREEZE — NOT BREACHED
/002 §3.4 verbatim characterizes rebal=6 as a CONTROL variable ("isolates the one change"), inherited from
DIAGNOSTIC-002's sanity, never optimized/claimed optimal. Cadence is an externally-mandated axis (5 pre-result
recommendations). /005 is a new EXPLORATION with its own frozen gates on /002's frozen construction. Legitimate.

## Findings ranked
- **[F1 MED] Intra-rebal drift:** ORDIUSDT short grew target 0.10→0.36 effective weight between weekly rebals
  (k=4304, intra-rebal squeeze); gross-lev [0.49,1.94]. Real, disclosed, absorbed IS (G3 −33% passes) but an
  unsystematic OOS risk — maxDD could deepen to −40/−45% OOS even if Sharpe holds. Named complement: hysteresis/
  eligibility-exit (REVIEW-002 S1). Not a BLOCK.
- [F2 LOW] "monotone" wording imprecise (hump in Sharpe, monotone in turnover).
- [F3 LOW] LITUSDT funding residual (3.92bps, conservative). [F4 LOW] 2025Q1 small-sample (not load-bearing).
- [F5 LOW] 2023 +0.35 weakest year — most likely to flip negative in a choppy OOS window.
- [F6 LOW] adverse-selection persists at weekly (mitigated, not eliminated).

## OVERTURN of REVIEW-004 "alpha too weak" — LEGITIMATE
/005 tests an orthogonal axis (cadence) that REVIEW-004's own path-forward named as the highest-ROI untried lever.
The per-rung ceiling REVIEW-004 found was cadence-DEPENDENT (all of /001-/004 ran at rebal=6). Not a re-evaluation;
a genuinely new lever. Legitimate overturn.

## BOTTOM LINE
+0.91 real; selection-bias defensible-but-temper (multiple pre-result recommendations + pre-reg point ≠ IS-max +
plateau + all-years-positive); leak@rebal=21 PASS; /002 freeze not breached; G1-G6 PASS; mechanism sound.
**Verdict: MERGE-TO-CONFIRMATION** — promote to baseline PENDING the single OOS reveal. IS necessary-not-sufficient;
OOS is the real falsifier and stays sealed until CONFIRMATION. Deployable claim contingent on OOS holding ~IS Sharpe.
