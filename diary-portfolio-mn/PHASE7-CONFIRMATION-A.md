# PHASE7-CONFIRMATION-A — QR Formal Verdict on the A3-1 Holdout Reveal (family A; MN track)

**Date:** 2026-07-11 · **Role:** Quant Researcher (Phase 7 — confirmation evaluation) · **Track:**
baseline-BLIND MARKET-NEUTRAL (MN). **Map scored against:** `briefs-portfolio-mn/CONFIRMATION-A.md`
(FROZEN pre-reveal, commit 6f236c58). **Inputs:** `CONFIRMATION-A-results.md` (QE execution record)
+ `CONFIRMATION-A-run.log` (the audit banner). **The one-per-family-FOREVER holdout reveal was
executed EXACTLY ONCE (banner count = 1) and family A's holdout budget is SPENT FOREVER as of
2026-07-11T07:53:06Z.** No new numbers, no runs, no re-gating in this document.

---

## 1. TIER — per the frozen §4 map: **AMBIGUOUS / PARTIAL**

The four frozen reads, observed vs the thresholds I pinned BEFORE any holdout number existed:

| read | observed (holdout, honest cost, n=572 ≈ 0.52yr) | frozen threshold (§4) | mechanical read |
|---|---|---|---|
| **N — neutrality** (highest power) | full-window OLS **β_BTC −0.0587** (se 0.034), **β_ETH −0.0611** (se 0.026), **crash-bucket β_BTC −0.0519** (n=163 ≥30, not waived) | \|β_BTC\|≤0.15 AND \|β_ETH\|≤0.20 AND crash \|β_BTC\|≤0.25 | **N HOLDS** |
| **D — drawdown** | **maxDD −25.26%** | controlled ≥ −33% | **controlled** |
| **S — edge** (lowest power) | **net Sharpe −0.5327** (SE ≈ 1.38) | positive-edge ≥ +0.30; weak [−1.0,+0.30) | **weak** |
| **F — funding leg** (durable core) | **funding income +0.5006** (+8.75 bps/cd, 7/7 months positive) | positive > 0 | **positive** |

No FAIL trigger fired (N not broken, D not catastrophic, S not < −1.0, F positive). The DEPLOY bar
(S ≥ +0.30) is not met. Per the frozen map, this is exactly **AMBIGUOUS / PARTIAL** — and exactly the
outcome the map pre-registered as "the most likely under the documented adversity + the ±1.39 Sharpe
noise." **The tier is what the frozen map says it is; I do not re-weight it.**

---

## 2. The pre-committed interpretation — "mechanism held, edge unproven in an adverse half-year"

The map's PARTIAL definition is validated with unusual clarity by the observed specifics: **both
engineered mechanisms transferred to unseen data; what failed to appear was the REGIME the book earns
in, not any layer of the book.**

- **The earner bucket was ABSENT.** Window composition (reported first, per the map): CRASH 28.5%
  (2.5× the IS 11.5%) and **MANIA 0.0% — n=0, the first entirely MANIA-free scoring window in the
  family's history.** A3-1's IS P&L was ≈95% CHOP+MANIA, and the MANIA bucket (+24.9% of IS P&L)
  simply did not occur. The book was asked to earn in a window composed almost entirely of the two
  regimes where its IS edge is weakest (crash: break-even; MANIA-free chop: its price alpha's worst).
- **The durable carry core OVER-DELIVERED.** Funding income +8.75 bps/cd — **~3–6× the IS +1.50
  bps/cd** — positive in 7/7 months. The thesis's durable component (the funding leg, 6/6 IS years)
  not only survived out-of-sample, it paid MORE per candle (crash-heavy windows pay large funding to
  the short leg). The map called a negative funding leg "a genuine shock"; the opposite happened.
- **The price leg inverted in MANIA-free chop.** Price −10.08 bps/cd (IS +1.64); CHOP bucket −3.06
  bps/cd (IS workhorse +2.63). The entire −0.5767 cumulative price loss is here. The cross-sectional
  price-mean-reversion alpha — always the FRAGILE leg (2022 IS total Sharpe −0.06) — did not hold in
  a window with no mania dispersion to mean-revert.
- **The throttle transferred, RETURN-POSITIVE, 0 LAG.** SCUD fired 3/3 negative months (0 LEAD /
  3 COINCIDENT / 0 LAG — no fired-at-the-trough LAG signature), was **return-positive OOS** (+0.58
  bps/cd; +3.29pp maxDD; −3.21pp vol vs the un-throttled A2 book), and produced the largest single-
  month clip in the family's history (+3.14pp, 2026-05). The projection also transferred cleanly
  (ρ(w_proj,w_raw) 0.976, post-cap target-β max 0.0020).

So: **the two things we engineered — hedge-free beta-neutralization and the squeeze throttle — both
worked on unseen data. The one thing we do not control — the market handing us the CHOP/MANIA regime
the carry earns in — did not appear.** That is the precise meaning of "mechanism held, edge unproven."

---

## 3. What CANNOT be claimed — and what CAN (both on the record)

**CANNOT be claimed:**
- **NOT** that the edge is validated. A −0.53 Sharpe (SE ≈ 1.38) in a MANIA-free half-year proves
  nothing about the edge in either direction — it is neither confirmation nor refutation; it is
  non-informative on edge, by construction of the sample.
- **NOT** that A3-1 is deployment-proven. PARTIAL is explicitly not a DEPLOY-CANDIDATE; there is no
  validated positive-Sharpe evidence, and the one adverse window we spent the reveal on did not
  supply it.
- **NOT** any comparison to buy-and-hold or absolute return — the frozen frame is the risk-adjusted
  profile, and that frame did not clear the DEPLOY bar.

**CAN be claimed (confirmed on genuinely unseen data — the design LAYERS work):**
- **Beta-neutrality TRANSFERRED** — full-window β_BTC −0.059, β_ETH −0.061, and crucially the
  **crash-bucket β_BTC −0.052 in a 28.5%-crash window** — the anti-predecessor axis, the highest-
  power test, held OOS with room to spare. The predecessor's failure mode (realized crash/mania beta)
  did not recur.
- **The squeeze throttle TRANSFERRED** — fired in every OOS drawdown month, 0 LAG, return-positive,
  improving Sharpe / maxDD / vol vs the un-throttled book. The mechanism generalizes.
- **The funding-carry durability TRANSFERRED** — the durable core paid positive every month, stronger
  than IS. The one part of the thesis with a mechanistic all-regime-payer claim delivered.

The honest one-line summary: **the construction is a confirmed market-neutral, squeeze-throttled,
funding-carry book; its EDGE remains unproven because the reveal window contained none of the regime
it earns in.**

---

## 4. Pre-committed path (§5 of the frozen map — no rescue)

Per the map's §5, frozen before the reveal and binding now:
- **The reveal is SPENT FOREVER.** Family A's one-per-family holdout budget is gone (audit banner,
  2026-07-11T07:53:06Z). There is **no rescue, no second look, no re-parameterization, no re-gate, no
  "the window was too adverse so discount it."** PARTIAL is the outcome; arguing with it would be a
  process-integrity violation. No adjustment to A3-1 can ever earn a second reveal (that would be a
  new family, not a rescue of A).
- **Further evidence, if any, comes ONLY from the zero-budget forward paper-trade** — an `mn_paper_*`
  clone of the `blind_paper_l1` recompute architecture (frozen params, weekly append-invariant
  recompute, no exchange orders, no new backtest budget). It accumulates genuinely-unseen post-reveal
  data until that record — not another reveal — resolves the edge. This is the charter's designated
  final arbiter and the pre-committed PARTIAL consequence.
- **Family A's disposition now rests with the USER.** The options are: (a) stand up the forward
  paper-trade to keep gathering unseen evidence at zero budget; (b) archive A3-1 as banked structural
  knowledge (beta-neutrality without a hedge leg; squeeze-throttle-for-free-Sharpe; funding as the
  only all-regime-payable flow at these costs); (c) hold A3-1 as a component to feed a future ensemble
  IF a second family ever banks (the ensemble capstone needs ≥2 families; the field ended 1/5). No
  new family-A construction work happens regardless — n_eff 9, terminal.

---

## 5. Anomaly notes worth carrying

- **Vol roughly DOUBLED OOS (36.1% vs 17.6% IS)** — the 2026 window is high-dispersion; the throttle
  reduced vol vs the un-throttled book (39.4% → 36.1%) but the base regime is simply wilder. This also
  inflates the β standard errors (se_BTC 0.034 vs IS 0.004) — the neutrality read HELD despite the
  noisier estimator, which strengthens, not weakens, the N conclusion.
- **Funding TRIPLED-to-quintupled per candle (8.75 vs 1.50 bps/cd)** while the price leg inverted —
  the split is mechanistically coherent: crash-heavy windows pay large funding to the short leg, and
  the cross-sectional price alpha has no mania dispersion to harvest. The thesis's durable leg and its
  fragile leg behaved exactly as their IS characters predicted, in opposite directions.
- **Small-sample honesty, load-bearing:** n=572 ≈ 0.52yr, SE(Sharpe) ≈ 1.38; 21-tranche Sharpes span
  −1.94 to +1.02 (9/21 positive). The Sharpe reading is genuinely near-uninformative on edge — which
  is precisely why the frozen map weighted neutrality/mechanism/durability (all high-power, all
  passed) over the noisy Sharpe. The map's design was validated by the very composition (MANIA n=0)
  that stressed it.
- **Reporting artifacts (non-substantive):** per-bucket/per-name "shares" exceed 100% (small −0.1006
  denominator); the 2026-07 partial month prints +0.00% compounded vs +0.16% arithmetic (compounding
  drag at 36% vol over 29 candles). Both are convention artifacts; window leg-reconciliation is
  1.39e-17. IS-parity gate exact at printed precision (the full-panel build did not perturb the frozen
  book), reveal fired exactly once, reproducibility bit-identical.

---

## Bottom line

The A3-1 holdout reveal lands **AMBIGUOUS / PARTIAL** per the frozen §4 map — and it is a clean,
honest PARTIAL: on genuinely unseen data the two engineered layers TRANSFERRED (beta-neutrality held,
crash-bucket β −0.052 in a 28.5%-crash window; the squeeze throttle fired 3/3 return-positive, 0 LAG)
and the durable funding core OVER-delivered (+8.75 bps/cd, 7/7 months), while the EDGE went unproven
because the window was crash-heavy and entirely MANIA-free — the book was denied the regime it earns
in, and its fragile price leg inverted (Sharpe −0.53, SE ±1.38, non-informative on edge). We CAN claim
the design works — market-neutral, squeeze-throttled, funding-durable, all confirmed out-of-sample; we
CANNOT claim the edge is validated or the book is deployable. Per the map's pre-committed §5: the
reveal is spent forever, no rescue; further evidence comes only from the zero-budget forward paper-
trade; family A is terminal (n_eff 9) and its disposition — forward-trade, archive as knowledge, or
hold as a future-ensemble component — now rests with the USER. The holdout is fully consumed; the
funding-carry line is resolved to "mechanism confirmed, edge unproven."

*— QR, MN track, 2026-07-11. Reveal spent; no re-gating; no new numbers.*
