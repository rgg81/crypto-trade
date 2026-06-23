# portfolio-iteration-v2 EXPLORATION-006 — rebalance frequency + XS-mom OOS REVEAL (PROMISING)

**Type:** EXPLORATION → first OOS reveal of the converged candidate. Two findings.
Code: `iter_v2_006_rebal.py`, `verify_xsmom_8h.py`.

## Finding A — rebalance frequency (user idea): NEGATIVE for XS-mom
Tested holding the signal piecewise-constant at weekly/monthly vs 8h. Cutting turnover did NOT help the
XS-mom signal — it HURT (the rank reshuffles fast; stale ranks lose more signal than cost saved):
- xs-mom 8h: OOS **+1.20** (turn 0.185) · weekly OOS +0.51 (turn 0.076) · monthly OOS −0.73 (turn 0.058).
- trend 8h: OOS −0.03 · weekly −0.88 · monthly +0.64 (noisy). 8h is the right frequency for XS-mom.
(Lower-freq may still suit a slower signal e.g. funding-carry — deferred to iter-v2-007.)

## Finding B — XS-mom standalone 8h is the v2 EDGE (OOS revealed)
The candidate converged on in EXPLORATION-005 (xs-only, the LATE-alive low-turnover book), revealed:

**standalone dollar-neutral cross-sectional momentum (centered within-band return-rank L=84), rank 21-40,
8h, via run_book_from_signal:**
- **IS +0.43 / OOS +1.20** (anchor OOS −0.01). OOS sub-windows 2025 +1.22, 2026 +1.09 (both positive).
- per-year {2024:+1.25, 2025:+1.37, 2026:+1.09} — strong in the regime we deploy into; the weak full-IS
  is ONLY the dead 2021-23 years a forward book never trades.
- turn 0.185 (LOWER than anchor 0.297).

### Verification (verify_xsmom_8h.py)
- **Cost-robust:** 2×-taker OOS **+0.81** (both sub-windows +0.79/+0.77); 2×-slip / pessimistic OOS +1.11.
  First v2 signal to survive 2× taker — the constraint that killed /002 blend, /003 ML, /005 routing.
- **Lookback:** OOS positive at ALL L∈{42,63,84,126,168} (+0.54…+1.20), best at pre-registered L=84.
  CAVEAT: 2026 sub-window positive only at L=84/168; negative at L=42/63/126 → some L-sensitivity in 2026.
- **Risk CAVEAT:** maxDD −37% IS / **−25% OOS** — high; needs vol-target/position-cap risk layer.
- Dollar-neutral except the bounded warmup overcount (signal max|Σ|=0.835 on a few warmup candles, typ
  ~1e-16); held-book max|Σw|=0.928 is engine-inherent (anchor=1.0 too).

## Status
**PROMISING — the first v2 candidate with a real, cost-robust OOS edge.** This is "win where v1 lost":
on rank 21-40 the ported trend stack is OOS-dead (−0.01) but a dollar-neutral XS-mom book is OOS +1.20
(+0.81 at 2× taker). NOT yet a baseline — must clear an adversarial CONFIRMATION: leak re-audit of the
run_book_from_signal path + xs signal; multiple-testing deflation (~20 OOS configs revealed across
/002–/006; candidate was pre-identified but headline needs DSR/N_eff); the −25% OOS DD (risk layer);
the 2026 L-sensitivity; and whether xs-only standalone (abandoning the EARLY-strong trend) is a
legitimate v2 baseline or a regime bet. → Critic confirmation next, then risk-engineer for the DD.
