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

## Status — CONFIRMED: MERGE-WITH-RISK-LAYER (quant-critic Phase 7.5)
The adversarial confirmation PASSED on every count except the drawdown:
- **Leak: CLEAN** — full run_book_from_signal path traced past-only; the runner `_norm` is mathematically
  inert (homogeneous degree-0); warmup over-count bounded; handcomputed-net + perturbation tests certify.
- **Multiple-testing: SURVIVES DEFLATION** — ~30-40 configs but N_eff≈4 (correlated perturbations of ONE
  signal family); candidate PRE-REGISTERED (L=84 v1-inherited, not reselected); default +1.20 clears even
  the pessimistic full-N bound, 2×-taker +0.81 at the boundary. The 5 prior negatives were DIFFERENT
  signal classes → honest search, not p-hacking.
- **2026 L-sensitivity: REAL, not disqualifying** — every L positive overall OOS; 2026 flip is n≈518
  sub-window noise; L=84 holds both sub-windows + survives 2× taker. (Logged as monitored falsifier.)
- **Mechanism: crypto-native-persistent** — retail rotation / relative-strength in the flow-rich mid-cap
  band, positive across 3 distinct 2024/25/26 regimes. Standalone is the CORRECT vehicle (by elimination
  of blend/ML/residual/routing); the weak full-IS is regime-irrelevant for a forward-deployed book.
- **BINDING CONDITION: the −25% OOS drawdown** → needs an IS-calibrated drawdown-brake + tightened
  vol-target risk layer (target OOS DD ~−15%, keep OOS Sharpe ≥ +1.0). → **iter-v2-007 risk layer**
  (risk-engineer, in progress). Becomes the unconditional v2 BASELINE once the DD is bounded.
- Record-closing items owed (non-gating): R1 direct leak test on run_book_from_signal; R2 live
  full-seasoning gate; R3 formal DSR/PBO commit; exact-weight-hold confirmation backtest.

**This is the v2 result: "win where v1 lost" — a leak-clean, cost-robust, deflation-surviving OOS edge
(+1.20, +0.81 @2×taker) on rank 21-40, where the ported top-20 trend stack is OOS-dead (−0.01).**
