# CONFIRMATION-A — Results Record (QE): the ONE-PER-FAMILY-FOREVER holdout reveal of A3-1

**Date:** 2026-07-11 · **Role:** Quant Engineer · **Track:** baseline-BLIND MARKET-NEUTRAL (MN)
**Contract:** `briefs-portfolio-mn/CONFIRMATION-A.md` (FROZEN 2026-07-11, pre-reveal; commit
6f236c58) — §7 executed EXACTLY. **USER-AUTHORIZED** spend of family A's one-per-family-FOREVER
holdout reveal on A3-1. **Script:** `analysis/portfolio/mn_confirmation_a.py` (new; measurement
scaffolding only — the CONSTRUCTION is imported byte-frozen from `mn_exploration_a3.py`'s
committed builders: `mn_scud`, `mn_diag_a_funding`, `mn_beta`, `blind_funding`, `blind_engine` —
zero changes). **Full log (the permanent execution record incl. the audit banner):**
`diary-portfolio-mn/CONFIRMATION-A-run.log`. **Wall-clock:** 2026-07-11T07:50:02Z →
07:53:06Z (3 min 04 s), i9-12900HK. **NOT committed** (per dispatch).

**ENGINEER SCOPE:** observed values + the MECHANICAL §4 tier bin (frozen thresholds applied
arithmetically) only. **NO verdicts** — the QR renders the formal CONFIRMATION verdict from this
record. The tiers below are the map's, frozen before any number existed.

---

## 0. THE AUDIT BANNER (verbatim from the run log — the permanent one-per-family record)

```
========================================================================
MN HOLDOUT REVEAL — SANCTIONED CONFIRMATION
  family : funding-carry
  window : [2026-01-01T00:00:00Z, 2026-07-11T00:00:00Z)
  at     : 2026-07-11T07:53:06Z
  ONE reveal per candidate FAMILY, EVER (PLAN §5.2). This banner is
  the audit record — a second reveal for this family is a violation.
========================================================================
```

`mn_guard_holdout(2026-01-01, window_end, confirmation_reveal="funding-carry")` was called
EXACTLY ONCE (grep of the log: banner count = 1; single call site in the script, verified by AST
pre-run). **Family A's holdout budget is SPENT FOREVER as of 2026-07-11T07:53:06Z.**

## 1. Protocol confirmations (§7 hard order — every gate BEFORE the reveal)

| step | check | result |
|---|---|---|
| data refresh | 8h klines 695 ACTIVE perps (per-symbol tolerant) + funding 791 panel syms | klines_ok=True, funding_ok=True; complete to 2026-07-10T16:00Z |
| §7-1 | `mn_panel_health()` FIRST | **OK** (BTC grid T=7149 contiguous 2020-01-01 → 2026-07-10T16:00Z; BTC+top40-live current; NOT degraded) |
| §7-2 | FULL-panel build, boundary pins | T=7149, C=747; IS rows 6576 == frozen; cutoff exactly on grid; warmup physics A2/A3-identical (β all-finite 135; first feasible 585 → first live rebal 588); IS regime-occupancy pin exact (CRASH 11.5 / MANIA 15.7 / CHOP 72.7%) |
| §7-2 | construction-integrity controls | funding coverage complete (745/747 direct, 2 non-members missing); funding-sort leak control PASS; SCUD ramp gate (1e-12) + monotonicity + corrupt-future leak control PASS |
| §7-2 | bit-identical re-run (full 63-run matrix × 2 passes, IS AND holdout rows in the compare) | **PASS** (all mapped streams + throttle records + counters) |
| §7-2 | leg reconciliation, 63 runs × 2 passes | max **8.33e-17** (≤1e-12) PASS; capDrop/degenerate/collapse = 0/0/0 full-window |
| §7-2 | inert control (p=0): ones ≡ None | BYTE-IDENTICAL (rets/turnover/weights/funding_rets/book_scalar_series) PASS |
| §7-2 | proportionality (p=0, full window) | 313 executed rebals, identical executed set; max \|w_A3 − s·w_A2\| = **8.33e-17**; max \|Σw\| = 2.03e-15; 61 throttled (s<1 non-vacuous) PASS |
| §7-2 | **IS-PARITY GATE** | **ALL PASS, exact at printed precision** (below) |
| pre-reveal | characterization dry-run on an IS stand-in slice (n=572, output captured) | OK — 0 section exceptions; post-reveal code path exercised end-to-end before the one-shot |
| §7-3 | THE SINGLE REVEAL | banner above; fired once |
| §7-4 | slice to `grid_ms ≥ MN_IS_CUTOFF_MS` | holdout scored candles n=572, [2026-01-01T00:00Z .. 2026-07-10T08:00Z] |
| unit suites | pre-run | 105 blind/MN tests ALL GREEN |

**IS-PARITY GATE (the full-panel build's IS slice [293, 6574], n=6282 == frozen):**

| metric | observed | revealed A3-1 | delta | |
|---|---|---|---|---|
| A3-1 IS Sharpe (1×) | +1.734131 | +1.7341 | +3.1e-05 | PASS (exact at printed precision) |
| A3-1 IS maxDD | −0.231103 | −0.2311 | −3.1e-06 | PASS (exact) |
| A3-1 IS CRASH β (n=658) | +0.009391 | +0.0094 | −8.7e-06 | PASS (exact) |
| A3-1 IS G3 rebal-row max | +0.069919 | +0.0699 | +1.9e-05 | PASS (exact) |
| A3-1 IS Sharpe (2× GT) | +1.510703 | +1.5107 | +2.8e-06 | PASS (exact) |
| A2-REPRO IS Sharpe | +1.678442 | +1.6784 | +4.2e-05 | PASS (exact) |
| A2-REPRO IS maxDD | −0.255700 | −0.2557 | −2.7e-07 | PASS (exact) |

The full-panel build (warmup continuity per map §2) did NOT perturb the frozen book.

**Disclosure:** the single candle opening 2025-12-31T16:00Z (the last IS row) is scored in
NEITHER the frozen IS mask [293, 6574] NOR the holdout slice (grid ≥ cutoff) — the frozen
[.., T−2] mask convention; one 8h candle, disclosed.

## 2. §7-1 WINDOW COMPOSITION FIRST (the context for every number below)

- **Window:** 2026-01-01T00:00Z → 2026-07-10T08:00Z, **n=572 scored candles ≈ 0.52 yr**.
  **SE(annualized Sharpe) ≈ 1.38** — the Sharpe is the LOWEST-power read, per the map's §2
  honest sample math.
- **Regime fractions (frozen mn_regimes):** **CRASH 28.5% (n=163) / MANIA 0.0% (n=0) /
  CHOP 71.5% (n=409)**.
- Context vs IS (CRASH 11.5 / MANIA 15.7 / CHOP 72.7%): the holdout is **crash-heavy (2.5× the
  IS crash fraction) and completely MANIA-free** — the map §3 documented-ADVERSE composition.
  A3-1's IS P&L was ≈95% CHOP+MANIA; the MANIA earner bucket (+24.9% of IS P&L) has **zero
  candles** in this window.

## 3. THE FOUR §4 TIER-INPUT READS — observed vs frozen thresholds (mechanical)

| read | observed (holdout, honest cost) | frozen threshold (§4) | mechanical read |
|---|---|---|---|
| **N — neutrality** (highest power) | full-window OLS **β_BTC = −0.0587** (se 0.0343, n=572); **β_ETH = −0.0611** (se 0.0255, n=572); **crash-bucket β_BTC = −0.0519** (se 0.0555, n=163 ≥ 30 → NOT waived) | \|β_BTC\| ≤ 0.15 AND \|β_ETH\| ≤ 0.20 AND crash \|β_BTC\| ≤ 0.25 (n≥30) | **N HOLDS** |
| **D — drawdown** | **maxDD = −25.26%** | controlled ≥ −33%; elevated (−45%,−33%); catastrophic < −45% | **controlled** |
| **S — edge** (lowest power) | **net Sharpe (1×) = −0.5327** | positive-edge ≥ +0.30; weak [−1.0,+0.30); clear-negative < −1.0 | **weak** |
| **F — funding leg** (durable core) | **funding income = +0.5006** (uncosted −funding_rets, cum arith) | positive > 0 | **positive** |

**MECHANICAL §4 BIN (arithmetic only — NOT a verdict):**

> **AMBIGUOUS / PARTIAL — mechanism HELD, edge UNPROVEN**: N HOLDS, F positive, D controlled
> (≥ −33%, so also not-catastrophic), S ∈ [−1.0, +0.30) (Sharpe −0.5327). No FAIL trigger fired;
> the DEPLOY bar (S ≥ +0.30) is not met. Per the frozen map this is "the most likely outcome
> under the documented adversity + the ±1.39 Sharpe noise."

Neutrality supporting context (reported per C5, NOT the gate): window-local rolling-270/135
β_BTC estimable on 438 of 572 candles; within \|β\|≤0.10 on **59.4%**; max \|β\| = **0.1724**;
mean −0.0676. (IS was 97.2% / 0.1760 — see anomaly (e).)

## 4. §7-3 HEADLINE (1× honest cost; 2× = GROUND-TRUTH re-runs)

| metric | holdout observed | IS anchor (A3-1) | map §3 prior |
|---|---|---|---|
| net Sharpe (1×) | **−0.5327** | +1.7341 | central ~+0.75, band ~+0.5..+1.1, ±1.39 noise |
| net Sharpe (2× GT) | **−0.6622** | +1.5107 | — |
| ann return (compounded) | **−22.72%** | +33.50% | — |
| ann vol | **36.14%** | 17.55% | — (vol ~doubled OOS) |
| maxDD | **−25.26%** | −23.11% | "likely DEEPER than IS; mid-20s-to-30s would not surprise" |
| turnover (1-way) | **62.5×/yr** | 52.3× | — |
| monthly win rate | **57.1%** (4/7) | 56.5% | — |
| worst month | **−11.57%** (2026-05) | −9.82% | — |

## 5. §7-4 Regime-bucket P&L + funding-vs-price attribution (the F read)

| bucket | n | mean bps/cd | t | P&L share |
|---|---|---|---|---|
| CRASH | 163 | **+1.50** | +0.16 | −24.4% |
| MANIA | 0 | — | — | — (no candles) |
| CHOP | 409 | **−3.06** | −0.59 | +124.4% |

- **Cum (arith): total −0.1006 = price −0.5767 + funding +0.5006 − tcost 0.0245.**
- Per-candle: **funding +8.75 bps/cd** (IS: +1.50) vs **price −10.08 bps/cd** (IS: +1.64);
  funding "Sharpe" (uncosted) +21.05 — the known income-drip artifact, informational.
- **F read: funding income +0.5006 > 0 → POSITIVE.** The durable carry core paid MORE per
  candle than in IS (crash-heavy windows pay large funding to the short leg); the LOSS is
  entirely the PRICE leg. (Shares >100% are an arithmetic artifact of the small total —
  anomaly (c).)
- CRASH bucket earned +1.50 bps/cd (break-even-to-slightly-positive) — consistent with the IS
  "break-even-neutral in CRASH" characterization; CHOP (the IS workhorse, +2.63 bps/cd IS) went
  −3.06 bps/cd here.
- Top-5 |per-name P&L share| (holdout records): LAB +135.3%, SIREN +101.6%, PIPPIN +77.9%,
  RIVER −68.0%, H −67.1% (inflated by the small denominator; anomaly (c)).

## 6. §7-5 SCUD throttle behavior OOS (the mechanism-transfer forensic)

- **Rebal-consumed coverage** (572 executed rebals pooled over 21 tranches): scalar<1 on
  **20.1%** [IS 19.4%]; scalar=φ on **9.8%** [IS 7.0%]; mean **0.9267** [IS 0.9385]; min 0.5000.
- **SCUD-z realized quantiles** (12,012 pooled tranche-candles): z>τ_lo **20.1%** (anchor ~20%);
  z>τ_hi **9.8%** (anchor ~5% — right tail heavy, same direction as IS 7.2%).
- **Ensemble activity:** ≥1/21 tranches held-throttled on **71.9%** of candles [IS 69.3%];
  all-21 on 0.0%; mean held scalar 0.9263 [IS 0.9413].
- **Throttle effect (A3 − A2-REPRO, holdout):** total **+0.0330** (+0.58 bps/cd), ALL of it in
  active windows; loss-averted +0.1982 (209 A2-losing candles) vs carry-foregone −0.1651
  (202 A2-winning candles). The throttle was RETURN-POSITIVE here (IS: ~return-neutral).
- **A2-REPRO (un-throttled) holdout context: Sharpe −0.6500, maxDD −28.55%, vol 39.35%** —
  the throttle improved all three (Sharpe +0.117, maxDD +3.29pp, vol −3.21pp).
- **C4 episode timing on the holdout's own negative months (A2-path peak/mid/trough, pinned
  rules; FIRED = scalar<1 on ≥1 rebal-consumed candle in the month):**

| episode | FIRED | timing | t_first | peak | mid | trough | mean scalar pk→tr | A3 vs A2 month | delta |
|---|---|---|---|---|---|---|---|---|---|
| 2026-02 | Y | COINCIDENT | 2026-02-08 | 2026-01-26 | 2026-02-05 | 2026-02-16 | 0.9012 (65) | −5.26% vs −5.93% | **+0.68pp** |
| 2026-04 | Y | COINCIDENT | 2026-04-07 | 2026-04-02 | 2026-04-06 | 2026-04-11 | 0.9418 (30) | −7.56% vs −7.70% | **+0.14pp** |
| 2026-05 | Y | COINCIDENT | 2026-05-01 | 2026-04-02 | 2026-04-22 | 2026-05-13 | 0.8988 (126) | −11.57% vs −14.71% | **+3.14pp** |

  **FIRED 3/3; 0 LEAD / 3 COINCIDENT / 0 LAG.** No fired-at-the-trough LAG signature; the
  largest clip (+3.14pp, 2026-05) landed on the window's worst month.
- **Projection health (572 projected rebals, ALL executed rebals projected):** Σ|w_proj|/g_eff
  med 0.9720 / min 0.8017; amp>2× flags 0; ρ(w_proj, w_raw) mean +0.9756 / min +0.8588;
  post-cap target-β max|.| 0.0020. The projection transferred cleanly (IS-like values).

## 7. §7-6 maxDD path + monthly table

- **maxDD −25.26%: peak 2026-01-26 → trough 2026-06-01** (trough regime CHOP, trough month
  2026-06) — a ~4-month grind spanning the Feb/Apr/May negative months, on the SAME path shape
  as the A2-REPRO book (A2 −28.55%); the throttle clipped the shared path by 3.29pp.

```
month       n      ret   long_px  short_px  net_fund    tcost    A2ret
----------------------------------------------------------------------
2026-01    93   +2.33%   -0.1659   +0.1191   +0.0759   0.0037   +2.62%
2026-02    84   -5.26%   -0.0811   -0.0260   +0.0590   0.0035   -5.93%
2026-03    93   +5.47%   -0.0487   +0.0279   +0.0819   0.0041   +6.16%
2026-04    90   -7.56%   -0.0890   -0.0746   +0.1008   0.0039   -7.70%
2026-05    93  -11.57%   -0.0562   -0.0743   +0.0146   0.0042  -14.71%
2026-06    90   +4.56%   -0.0666   -0.0061   +0.1303   0.0037   +3.89%
2026-07    29   +0.00%   -0.0780   +0.0428   +0.0381   0.0013   +0.24%
```

  (ret compounded, legs arithmetic sums; 2026-07 partial, 29 candles through 07-10T08:00Z.
  net_fund positive in ALL 7 months.)

## 8. Per-tranche dispersion + integrity (holdout window)

- **21 tranche Sharpes:** min −1.941 / p25 −1.263 / med −0.595 / p75 +0.579 / max +1.022;
  **positive 9/21**; ensemble −0.5327. Wide phase dispersion on a 572-candle window (each
  tranche ~27 rebals) — consistent with the ±1.39 SE regime.
- Ensemble leg reconciliation (holdout window): max **1.39e-17** (≤1e-12) PASS.
- Analytic 2× twin vs GROUND-TRUTH (cross-check only): max drift 2.70e-04 (stateless
  expectation ~2.6e-4); analytic ens 2× Sharpe −0.6624 vs GT −0.6622. GT authoritative.
- **Reproducibility:** independent PASS-2 matrix → holdout Sharpe −0.5327 / maxDD −25.26% /
  funding +0.5006; holdout stream bit-identical to pass-1: PASS; Sharpe exact-equal: PASS.
- Post-reveal section exceptions: **0** (all sections completed).

## 9. Map §3 pre-registered expectations vs observed (stated, not scored — QR's read)

| §3 prior | observed |
|---|---|
| composition ADVERSE (crash-heavy starves the earners) | CONFIRMED-adverse: CRASH 28.5%, **MANIA 0.0%** |
| Sharpe central ~+0.75, band ~+0.5..+1.1, "wide, weakly-determined" | **−0.5327** (below the band; ~0.9–1.2 SE below, SE≈1.38) |
| maxDD "likely DEEPER than −23.11%; mid-20s-to-30s would not surprise" | **−25.26%** (deeper, in the anticipated range) |
| funding leg POSITIVE ("a negative leg would be a genuine shock") | **+0.5006 POSITIVE** (+8.75 bps/cd, stronger than IS) |
| neutrality expected to HOLD (highest power) | **HELD** (β_BTC −0.0587 / β_ETH −0.0611 / crash −0.0519) |

## 10. ANOMALY / FORENSIC NOTES (reported, not resolved)

**a. Ann vol roughly DOUBLED OOS (36.1% vs 17.6% IS)** despite the throttle being MORE active
(mean held scalar 0.9263 vs 0.9413). The 2026 window is high-dispersion; the throttle reduced
vol vs the un-throttled book (39.4% → 36.1%) but the base regime is simply wilder. This also
inflates the OLS β standard errors (se_BTC 0.0343 vs IS 0.0038).

**b. The price leg broke, not the carry: price −10.08 bps/cd vs funding +8.75 bps/cd.** The
IS engine was price +1.64 / funding +1.50. OOS the funding drip TRIPLED-to-quintupled per
candle (crash-heavy → shorts collect) while the cross-sectional price alpha inverted. The F
core (the family's thesis) survived; the CHOP price alpha did not, in a MANIA-free window.

**c. Per-name and per-bucket "shares" exceed 100%** (CHOP +124.4%; LAB +135.3%): arithmetic
artifact of a small total (−0.1006) as denominator. Reported for completeness; magnitudes,
not shares, are the informative read on this window.

**d. Throttle was RETURN-POSITIVE OOS (+0.58 bps/cd; +3.29pp maxDD; −3.21pp vol)** — stronger
than its IS profile (return-neutral, risk-reducing). FIRED 3/3 negative months, all
COINCIDENT (0 LEAD / 0 LAG vs IS 2 LEAD / 2 COINCIDENT). The 2026-05 clip (+3.14pp) is the
largest single-month clip observed in any window, IS included.

**e. Window-local rolling-270 β_BTC within-0.10 only 59.4% (max 0.1724)** vs IS 97.2%. The
rolling estimator on 572 candles at doubled vol is noisy (se per 270-candle window ~0.03-0.05);
the frozen N gate is the full-window OLS + crash bucket (both comfortably inside bounds).
Reported as the C5 supporting context it is.

**f. SCUD-z right tail heavier OOS (z>τ_hi 9.8% vs ~5% anchor; IS 7.2%)** — same direction the
brief's coverage note anticipated, more pronounced in the crash-heavy window; τ_lo coverage
20.1% sits on the anchor.

**g. MANIA n=0** — the first entirely MANIA-free scoring window in the family's history. The
map's tier design (edge read deliberately low-power, mechanism/neutrality/durability weighted
over Sharpe) is exactly the configuration this composition stresses.

**h. 2026-07 partial month prints +0.00% compounded while legs sum to +0.16% arithmetic** —
compounding drag at 36% ann vol over 29 candles; convention artifact, not a reconciliation
failure (window recon 1.39e-17).

**i. Turnover 62.5×/yr vs IS 52.3×** — higher churn OOS (more throttle transitions + wilder
cross-section). Still far under the 250×/yr IS gate bound (context only; no OOS turnover gate).

---

## Status

Reveal executed EXACTLY ONCE per the frozen map; all §7 pre-reveal gates PASS (IS parity exact
at printed precision); characterization complete, 0 exceptions; reproducibility bit-identical.
**Family A's holdout budget is SPENT FOREVER.**

**MECHANICAL §4 BIN: AMBIGUOUS / PARTIAL — mechanism HELD (N, F, D all inside bounds), edge
UNPROVEN (S = −0.5327 ∈ [−1.0, +0.30)) in a crash-heavy, MANIA-free half-year.** Per map §5 the
pre-committed consequence of PARTIAL is forward paper-trade evidence accumulation at ZERO
additional backtest budget — the QR renders that verdict formally; no verdict is stamped here.

*— QE, MN track, 2026-07-11.*
