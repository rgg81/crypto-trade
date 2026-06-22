# portfolio-iteration-v2 EXPLORATION-002 — cross-sectional momentum on rank 21–40 (SPECIALIST-NEGATIVE)

**Type:** EXPLORATION (OOS HIDDEN). ONE change: add a dollar-neutral XS-momentum tilt (γ on a centered
within-band return-rank, L=84) to the rank-21–40 trend+carry anchor, parity-preserving at γ=0.
**Verdict:** **SPECIALIST-NEGATIVE / NO-PROMOTE** — honest negative (code leak-clean, parity intact);
the factor fails its own pre-registered load-bearing gates on this cohort. Brief: `BRIEF_iter002_xsmom.md`.

## What was built (reusable; stays in the engine at γ=0 default = anchor)
- `engine_v2._xsmom` (bit-identical to v1 `iter_002_top20.py:86-89`) + `_xs_gate_mask` (past-only
  dispersion/min-names gate), threaded `xs_gamma/xs_lookback/xs_nmin/xs_disp_min` through
  `fixed_lambda_book` → `run_book` with a HARD γ=0 early-return parity guard.
- Tests: `test_xsmom_gamma_zero_parity` (γ=0 net == anchor, **max|Δ|==0.0**, other XS knobs non-default),
  `test_xsmom_dollar_neutral`. 11/11 green. `parity_check.py` UNCHANGED at 1.041e-16.
- Run script `analysis/portfolio_v2/iter_v2_002_xsmom.py` (OOS suppressed; `--reveal` for CONFIRMATION).

## Results (IS + EARLY[2021–23] / LATE[2024→cutoff] in-sample split; OOS hidden)
Anchor (γ=0): IS +1.53, EARLY +2.17, LATE +1.16, turn 0.297.
| config | IS | EARLY | LATE | ΔLATE | turn | gateFire |
|---|---|---|---|---|---|---|
| standalone γ=1 L=84 noGate | +0.63 | +0.18 | +1.38 | — | 0.205 | — |
| blended γ=0.15 L=84 | +1.28 | +1.67 | +1.21 | +0.05 | 0.288 | 20.5% |
| blended γ=0.25 L=84 | +1.26 | +1.63 | +1.13 | −0.03 | 0.282 | 20.5% |
| **blended γ=0.40 L=84 (deploy)** | **+1.32** | +1.53 | +1.24 | **+0.08** | 0.273 | 20.5% |
| blended γ=0.60 L=84 | +1.19 | +1.36 | +0.94 | −0.22 | 0.262 | 20.5% |
| γ=0.40 L=42 | +1.09 | +1.35 | +1.09 | −0.07 | 0.288 | — |
| γ=0.40 L=126 | +1.40 | +1.64 | +1.23 | +0.07 | 0.270 | — |
| γ=0.40 L=168 | +1.41 | +1.61 | +1.33 | +0.17 | 0.267 | — |
Cost stress (γ=0.40 L=84) ΔLATE: default +0.08, 2×slip +0.15, **2×taker +0.02**, pessimistic +0.15.
DISP_MIN frozen = IS-p20 = 0.139887. Dollar-neutrality typ_max ≈ 4.4e-16 (2.27 on 4/5051 warmup candles).

## Gate adjudication (critic-confirmed, pre-registered standard)
At the pre-registered deploy (γ=0.40, L=84): **G1 FAIL** (IS +1.32 < +1.43 floor — XS-mom costs IS),
**G2 FAIL** (ΔLATE +0.08 < +0.15, the load-bearing anti-regime gate), G3 PASS, **G4 FAIL** (non-monotone
in γ; γ=0.60 ΔLATE −0.22 — knife-edge in the weight dim), G5 PASS, G6 PASS. Three gates down, two
load-bearing → NOT PROMISING.
- **L=168 (ΔLATE +0.17) is NOT a rescue** — L=84 was the pre-registered deploy lookback; reselecting
  L=168 post-OOS-hidden is still post-hoc selection (forbidden by the brief). And L=168 (56d) is the
  LEAST aligned with the stated 1–4wk rotation mechanism — a falsification signal, not a fit.

## The real finding (the one asset to carry forward)
Standalone XS-mom is **EARLY-dead / LATE-alive** (per-year `2024:+1.26, 2025:+1.38, 2026:+1.15`,
EARLY≈0) — the OPPOSITE era-profile of the trend anchor, carrying exactly the regime where directional
trend died. This is NOT alt-season beta in disguise (K1 not triggered). The thesis is validated at the
SIGNAL level. BUT it is marginal and cost-fragile: standalone IS only +0.63, it DILUTES the IS-strong
years when blended (G1), and it **dies at 2× taker** (ΔLATE +0.02 — rank-churn turnover is the binding
constraint). Real edge, wrong vehicle: a constant-γ blend with the still-EARLY-strong trend is not it.

## Path forward (critic-endorsed)
**PURSUE (strongest first):**
1. **Regime-conditional γ (iter-v2-003)** — route to XS-mom ONLY when a past-only trend-health statistic
   is low (e.g. cohort-aggregate |trend| strength, or the λ-book's trailing realized Sharpe below a
   pre-registered IS-only floor), fail-safe to the anchor when trend is healthy. Monetizes the
   EARLY-dead/LATE-alive complementarity WITHOUT picking γ on outcomes. NOT a bare walk-forward-γ.
2. **Shorter-horizon relative-strength / XS-REVERSAL at L∈{21,42}** as a SEPARATE factor — the mechanism
   (1–4wk) and the only-passing config (L=168, 56d) DISAGREE, so L=84 may be a dead zone. Standalone-first.
3. **Cross-sectional FUNDING-rank** (dollar-neutral carry cross-section) — orthogonal to price; harvests
   the same crowding the thesis invokes via a different input panel.

**DO NOT CHASE:** bare walk-forward-γ on the L=84 price-rank XS-mom (not earned — fails G2 at every fixed
γ, non-monotone, dies at 2× taker); reselecting L=168.

**Pre-registration carried forward:** any XS-mom revival on this cohort must clear its gate **under 2×
taker** (turnover is binding for rank-churn factors on the 20-name mid-cap band). DEAD PATH LOGGED:
fixed-γ price-rank XS-mom on rank 21–40, L=84.
