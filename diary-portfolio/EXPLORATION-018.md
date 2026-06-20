# portfolio-iteration CONFIRMATION-018 — POWER-AWARE confirmation of the trend+carry+flow combiner (HOLD: own-Sharpe NOT DSR-significant after N=14 deflation)

**Agent-driven** (full team: quant-researcher framing of the power-aware plan + orchestrator build +
quant-critic pre-registration). This is the **DECISION RUN** for the inverse-vol RISK-PARITY combiner
of trend+carry+flow (built iter_014, firmed-up iter_015). The iter_015 critic PASS pre-registered
EXACTLY the power-aware plan executed here — DSR (multiple-testing deflation), stationary block-bootstrap
on the monthly diffs, a PRIMARY directional gate, plus PBO. Code: `analysis/portfolio/iter_018_confirm.py`
(imports iter_015's combiner net byte-for-byte; adds ONLY the statistics; nothing tuned on OOS; bootstrap
SEEDED for reproducibility). Baseline (iter_005 WF-λ, IS +1.30 / OOS +1.37 / DD −23%) **UNCHANGED**.

## Headline answer: **HOLD.** Decided by condition (i) — the combiner's OWN OOS Sharpe is **NOT** multiple-testing-significant (DSR=0.73 < 0.95 after N=14 deflation). The lift CI excludes 0 but is MARGINAL; the within-noise paired t (1.68, p≈0.11) is not rescued. Baseline stays +1.37.

## PRE-REGISTERED DECISION RULE (stated BEFORE results, applied mechanically AFTER)
PROMOTE the combiner (RP-3) to baseline **IFF ALL THREE** hold:
- **(i)** combiner's OWN OOS Sharpe **DSR-significant** — DSR > 0.95 after **N=14**-trial deflation
  (LdP: deflate by E[max Sharpe] under N independent trials); **AND**
- **(ii)** the **directional gate** — block-bootstrap CI **lower bound on the mean monthly LIFT** > 0;
  **OR** (disjunctive fallback) lift sign-stable under LOO **AND** monthly win-rate > 50% **AND** every
  vol-window cell beats baseline; **AND**
- **(iii)** **PBO < 0.5** (the vol-window config is not an overfit pick).
- **CONTROLLING CLAUSE (honesty):** if the LIFT's bootstrap CI **includes 0** → improvement NOT proven
  → **HOLD even if the own-Sharpe is DSR-strong**. A DSR-strong own-Sharpe says "real vs zero"; it does
  NOT say "beats the incumbent." Promotion requires beating the INCUMBENT, and that is the lift.

## Results (n=16 OOS months; OOS_CUTOFF=2025-03-24 immutable; reused combiner sanity gates PASS)

Combiner reproduced: RP-3 inverse-vol **IS +2.06 / OOS +2.40 / DD −29%**, dOOS **+1.03** vs baseline.

### (1) DSR of the combiner's OWN OOS Sharpe — N=14 deflation → **FAIL**
| quantity | value |
|---|---|
| combiner OOS Sharpe (per-month / annualized) | +0.692 / **+2.40** |
| skew / raw-kurtosis / n | +0.09 / 4.16 / 16 |
| **E[max Sharpe] over N=14 trials** (per-month / ann.) — the **deflated threshold** | +0.515 / **+1.78** |
| PSR vs zero (single-test) | **0.9903** |
| **DSR (N=14-deflated)** | **0.7256** |

The combiner's own Sharpe is **strong vs zero** (PSR 0.99) but the **N=14 multiple-testing deflation
kills significance**: E[max Sharpe] under 14 independent trials is +1.78 annualized, so an observed
+2.40 deflates to **DSR 0.73 < 0.95**. **Condition (i) FAILS.** This is the binding result.

### (2) Stationary block-bootstrap (Politis–Romano, block~3, 5000 resamples, seed=20260620)
| stream | median | 90% CI | **LOWER-95** | P(>0) |
|---|---|---|---|---|
| (a) combiner OOS Sharpe | +2.46 | [+0.96, +4.73] | **+0.96** | 100% |
| (b) mean monthly LIFT (combiner−baseline) | +3.68%/mo | [+0.48, +6.92]%/mo | **+0.48%/mo** | 97% |

The combiner's own-Sharpe CI is robustly positive (lower-95 +0.96). The **LIFT** CI lower-95 is **+0.48%/mo
(EXCLUDES 0)** at the pre-registered block~3 — but it is **MARGINAL and block-length-sensitive**:

`lift lower-95 vs block length: bl=1:+0.09  bl=2:+0.22  bl=3:+0.48  bl=4:+0.64  bl=6:+0.93 %/mo`

At **block=1 (≈ i.i.d.) the floor sits on top of 0 (+0.09%/mo)**; longer blocks resample the clustered
positive months together and artificially widen the margin. The percentile bootstrap is also
anti-conservative at n=16. **Seed-stable** (+0.36..+0.57%/mo across 5 seeds) but **not large-margin**.
The bootstrap floor (>0) and the parametric paired **t=1.68 (p≈0.11, within-noise)** *disagree* at n=16 —
and we **do not over-read the more favorable one**.

### (3) PBO via CSCV over the combiner config space (vol-window {42,84,168}) → **PASS**
Config space = the ONE structural knob (inverse-vol vol-window, 3 configs); CSCV S=10 → 252 balanced
splits. **PBO = 0.206 < 0.5** (logit median +0.55). The IS-best vol-window generalizes OOS more often
than not — the combiner is **not** an overfit lottery pick of its lone knob. (Small d.o.f. — a low PBO
is expected; this is a guard, not a strong independent edge claim.)

### (4) Directional / sign-stability → gate **PASS**
- paired-monthly t (SECONDARY): **t=+1.68, p≈0.113**, mean_diff +3.68%/mo, **win-rate 62%**
- LOO lift **sign-stable=True**, no one-month artifact; combiner LOO Sharpe range **[+2.16, +3.46]**
- **every vol-window beats baseline**: OOS {42:+2.31, 84:+2.40, 168:+2.62} (all ≥ +1.37−0.05)
- OOS per-year net%: 2025 combiner +54% / base +14%; 2026 combiner +50% / base +32%
- **lift concentration: top-3 months = 71% of the total OOS lift** (the critic's flag — directionally
  consistent but driven by a few months)

## Pre-registered decision table
| condition | result |
|---|---|
| **(i) DSR > 0.95 (N=14 deflation)** | **FAIL** (DSR 0.73) |
| (ii) directional gate (lift CI lower>0 OR sign-stable+win>50%+all-windows-beat) | PASS |
| (iii) PBO < 0.5 | PASS (0.206) |
| controlling clause — LIFT bootstrap CI vs 0 | EXCLUDES 0 (lower-95 +0.48%/mo, MARGINAL) |

## VERDICT: **HOLD** — failed condition (i) DSR. Baseline UNCHANGED (iter_005 WF-λ, OOS +1.37).
The combiner clears the WHOLE directional/overfit side of the rule (directional gate PASS, PBO 0.206,
lift CI technically excludes 0). But the rule is **CONJUNCTIVE** — **(i) DSR FAILS**, so a strong-vs-
incumbent lift does **NOT** rescue an own-Sharpe the multiple-testing correction cannot clear. Honest
framing held throughout iter_014→015 is **confirmed by the power-aware lens, not overturned**: the
combiner is a **directionally robust candidate** whose case does **not** reach a promotion bar once we
deflate for the ~14 variants searched. **This is the within-noise → HOLD case the task warned about.**

**Two independent reasons HOLD is the honest call (either alone suffices):**
1. **DSR FAIL (binding):** N=14 deflation → DSR 0.73 < 0.95. The own-Sharpe is real vs zero (PSR 0.99)
   but not multiple-testing-significant.
2. **The lift edge is marginal/fragile:** lift CI lower-95 +0.48%/mo at block~3 but **+0.09 at block=1**
   (on top of 0), and the parametric paired **t=1.68 (p≈0.11) is within-noise**. The bootstrap floor and
   the t disagree; 71% of the lift is in 3 months. We do not promote on the more favorable statistic.

**The obstacle is n, not effect size.** DSR clears only as **genuinely forward** OOS months accumulate
(E[max] deflation shrinks relative to a longer, still-positive Sharpe record) — **not by re-reading this
window**. The combiner **stays a candidate**; promotion is the critic's call on a separate review.

## Honesty / leak / cost notes
- **Reuse, not redefine:** imports iter_015 (re-exports iter_014 `risk_parity_combine` + baseline
  `wf.walkforward`); sanity gates confirm trend==iter_005 λ=0 and flow==iter_012 standalone byte-for-byte.
- **Leak-safe by construction:** no signal is recomputed on OOS; the file only computes statistics on the
  already-reviewed combiner/baseline nets, sliced at the immutable OOS_CUTOFF. Realistic cost is inherited
  (the iter_015 REAL coin-level 2× stress remains +1.93 — itself above baseline but also within-noise).
- **Seeded:** BOOT_SEED=20260620 frozen; verified seed-stable (5 seeds) and block-length sweep reported.
- **DSR units:** computed in PER-MONTH Sharpe units (de-annualized) consistent with the LdP order-statistic
  E[max_SR]; skew/kurtosis of the realized monthly stream feed the non-Gaussian σ(SR). N=14 from the
  search breadth across iter-001..017 (only taker-flow added independent signal).

## Axis status
- **Risk-parity multi-factor combiner (trend+carry+flow): OPEN — CANDIDATE, power-aware-confirmed as
  WITHIN-NOISE.** The combiner is directionally robust + PBO-clean, but its own OOS Sharpe is NOT
  DSR-significant at N=14 and the lift edge is marginal. NO PROMOTION. Baseline stays iter_005 WF-λ +1.37.
- **Outstanding:** the verdict is n-gated. Accumulate genuinely forward OOS months (post-iter-018) and
  re-read DSR + the lift CI on the *new, unseen* window — the only honest path to a promotion bar.

## Next
- **iter-019:** either (a) accumulate forward OOS months and re-run the iter_018 power-aware lens on the
  unseen window (the clean way to move DSR), or (b) attack the **carry single-regime fragility** (carry IS
  −0.03, −67% standalone DD at a ~1/3 risk share) — pre-register a falsifier: if carry's OOS contribution
  flips negative, the candidate is a 2-factor (trend+flow) story. Keep the baseline frozen at +1.37 until a
  power-aware reveal on a forward window clears DSR > 0.95.
