# portfolio-iteration EXPLORATION-015 — FIRM UP the risk-parity combiner (PROMISING, within-noise lift, critic PASS → route to held-OOS CONFIRMATION)

**Agent-driven** (full team: quant-researcher framing + risk-engineer carry-cap spec + orchestrator
build + quant-critic review). This is a **CONFIRMATION-track FIRM-UP** of iter_014's inverse-vol
risk-parity combiner (trend + carry + flow). iter_014 reported OOS **+2.40** (point estimate) with a
"PROMOTE-WORTHY (DD caveat)" verdict; the critic PASSED the **flow factor** as real + leak-free +
additive (+0.92 marginal, corruption test bit-identical) but flagged **four CONCERNS** on the
*promotion package*. This iteration fixes each, honestly, and asks: is the combiner a robust candidate,
and is the lift SIGNIFICANT or within noise? Code: `analysis/portfolio/iter_015_combiner.py`.

**Headline answer:** the combiner is a **directionally robust** candidate whose **magnitude lift over
baseline is WITHIN NOISE at n=16** (paired monthly t=+1.68, p≈0.11). The iter_014 "+1.03 / near-
doubling" framing is **retracted**; the honest claim is *consistency of sign, not confirmed magnitude*.
The knob-free RP-3 is routed to a **held-OOS CONFIRMATION**; baseline UNCHANGED (iter_005 WF-λ +1.37).

## The four critic CONCERNS, and the disposition here

### FIX 1 — ERC solver was BROKEN → replaced with a CONVERGED, VERIFIED ERC (scipy SLSQP)
iter_014's `erc_combine` used the multiplicative fixed point `w ← w/(cov·w)`, which does NOT converge
to equal risk contributions for a general 3×3 covariance. **Re-diagnosed here** (the old solver is
re-run and its realized risk-contribution shares measured):

| ERC solver | RC max-dev from 1/3 (median / p90) | cornered (max-RC > 0.45): all / OOS |
|---|---|---|
| OLD iter_014 (`w←w/(cov·w)`) | **0.333 / 0.420** | **80% / 68%** → BROKEN |
| NEW SLSQP (min RC-variance) | **0.0000 / 0.0000** | **0% / 0%**, 99.7% converged (<0.02) → VERIFIED |

The SLSQP solver minimizes the variance of the RC shares on the long-only simplex and is gated:
`erc_converged = frac_converged>0.99 AND maxdev_p90<0.02`. The cited iter_014 "ERC +2.55
corroboration" was the **same iter_013 corner pathology**, not an independent scheme. The converged
ERC-3 is **OOS +2.31**, |Δ|=0.08 vs inverse-vol RP-3 (+2.40), flowW_OOS 0.31 (~1/3). With the factor
correlations small (|corr| ≤ 0.24), a *converged* ERC **must** ≈ inverse-vol — so the agreement is
legitimate corroboration **that the inverse-vol weighting is not an artifact**, NOT a second edge.

### FIX 2 — "2× cost" was HOLLOW → REAL coin-level 2× taker stress (the one that matters)
iter_014's gate [7] only doubled the trivial **meta-layer** turnover (factor-weight L1 drift
~0.009/candle ≈ 0.044 bps) and reported +2.34 — economically meaningless. The cost that matters is the
**coin-level** taker booked *inside* each factor's own rebalancing. `factor_nets_cost(p, 2.0)` rebuilds
each factor net at `2 × COST_SIDE × Σ|Δw|` at the coin level, then recombines through the identical
risk-parity machinery.

| net | IS@1× | OOS@1× | IS@2× | OOS@2× |
|---|---|---|---|---|
| trend (standalone) | +1.61 | +0.73 | +1.31 | +0.34 |
| carry (standalone) | −0.03 | +1.07 | −0.10 | +0.84 |
| flow (standalone) | +1.67 | +1.59 | +1.45 | +1.39 |
| **RP-3 combined** | +2.06 | **+2.40** | +1.71 | **+1.93** |

Real coin-level 2× cost takes a **−0.47 OOS haircut** (+2.40 → +1.93) — exactly the degradation the
hollow iter_014 stress concealed. It still clears baseline (+1.93 ≥ +1.37; dOOS +0.56, paired t=+1.11).
**The edge survives a realistic cost doubling** — the most important of the four fixes.

### FIX 3 — SIGNIFICANCE: the +2.40 vs +1.37 gap is WITHIN NOISE at n=16
Paired-monthly t-stat of (RP-3 − baseline) over the 16 OOS months: **mean_diff +3.68%/mo, t=+1.68,
p≈0.113** (proper Student-t(15), not the normal approx which understates the tail), **monthly
win-rate 62%**. The gap is **NOT statistically distinguishable from baseline** (|t| < 2.1). RP-3's OWN
Sharpe is significant vs zero; its **edge over baseline is not**. The iter_014 "near-doubling" is
**retracted**.

What IS robust is the **direction**: leave-one-month-out, the mean monthly difference is **sign-stable**
(range [+2.94, +4.86]/mo), **no one-month artifact**, and every vol-window cell {42,84,168} beats
baseline (OOS +2.31/+2.40/+2.62; paired t +1.63/+1.68/+1.93). We claim **consistency of sign, not
magnitude.**

### FIX 4 — carry vol-ceiling (optional polish) → Pareto-helps but COSMETIC; ship knob-free
Risk-engineer spec: cap carry's exposure when its own realized vol is high, `scale = min(1, VOL_CEIL /
rv)`, `rv = carry_net.rolling(42).std().shift(1)`, **VOL_CEIL = IS p60 of carry's rolling vol =
0.010871 (FROZEN, IS-only, index < OOS_CUTOFF)**, applied pre-combine. Result: carry leg IS −0.03 →
+0.03, DD −67% → −62%; RP-3+cap IS +2.10 / OOS +2.42 / full-DD −28% (+0.9pp) / OOS +0.02. It
Pareto-helps on the *full-sample* DD — **but the DD it targets is an IN-SAMPLE 2020 trough**: OOS-only
DD is **−23% with and without the cap** (= baseline; the critic's iter_014 "good news" catch). The cap
polishes a non-problem on live OOS and adds two tuned constants. **Headline ships the knob-free RP-3**
(degrees-of-freedom discipline); the cap is documented but NOT promoted.

## Sanity gates (all PASS — verified before reading any firm-up result)
- `factor_nets_cost(1×)` == `rp.factor_nets` (cost-rebuild byte-identical): **PASS** (gated; halts on fail)
- trend factor net == iter_005 fixed-λ=0: **PASS** | flow factor net == iter_012 standalone MOM 1×: **PASS**
- Baseline reproduced: iter_005 WF-λ **IS +1.30 / OOS +1.37 / −23%** | RP-3 reproduced **IS +2.06 / OOS +2.40 / −29%**
- OOS-only maxDD: RP-3 **−23%** vs baseline **−22%** (the −29% full-sample DD is an IN-SAMPLE 2020 trough)

## Pre-registered firm-up verdict (n=16 OOS months)
| gate | result |
|---|---|
| [F1] direction sign-robust (LOO-stable, no one-month artifact, win-rate>50%) | **PASS** (t=+1.68, p≈0.11 — gap WITHIN NOISE, not claimed) |
| [F2] survives REAL coin-level 2× cost (OOS ≥ baseline−0.05) | **PASS** (+1.93) |
| [F3] ERC CONVERGES (verified RC≈1/3) and AGREES with inverse-vol (|Δ|≤0.20) | **PASS** (+2.31, |Δ|=0.08) |
| [robust] every vol-window cell OOS ≥ baseline−0.05 | **PASS** (+2.31/+2.40/+2.62) |
| [F5] carry-cap Pareto-dominates plain RP-3 | YES (but cosmetic; ship knob-free) |

## Read — PROMISING, honestly within-noise; the cleanest version is the KNOB-FREE RP-3
The firm-up did what a firm-up should: it tried to BREAK the iter_014 promotion case on its weakest
points, found the cost-stress hollow and the ERC broken, fixed both honestly, and arrived at a **more
modest, more defensible** claim. The combiner is a directionally robust improvement whose magnitude is
not yet statistically distinguishable at n=16. RP-3's own Sharpe is significant vs zero; its edge over
baseline is not — that is exactly what a **held-OOS CONFIRMATION** is for (accumulate independent OOS
months to move the paired t). **Cleanest vehicle = plain inverse-vol RP-3**: no scipy, no carry-cap,
one structural knob (the vol window) already shown robust.

## CRITIC REVIEW (2026-06-20) — PASS: route the knob-free RP-3 to a held-OOS CONFIRMATION
The critic verified ALL FOUR iter_014 concerns are **genuinely** addressed (not cosmetic) and the new
code is **leak-free**:
- **Leak check PASS** — (a) converged ERC covariance uses `.shift(1)` vols + past-only correlation
  (`.shift(len(names))` = one full date-block, the correct past-only shift); (b) carry vol-ceiling
  VOL_CEIL is computed IS-ONLY (index < OOS_CUTOFF) and FROZEN, rv `.shift(1)`, `min(1,·)` monotone
  risk-reducing (cannot manufacture OOS return by levering up); (c) `factor_nets_cost(1×)` byte-
  identical to `rp.factor_nets` (gated).
- **Fixes are REAL** — old ERC re-diagnosed (68% OOS cornered) and the +2.55 retired; coin-level 2×
  is the right stress location and the −0.47 haircut to +1.93 is fairly reported; t-stat is the correct
  paired-monthly test, honestly framed WITHIN NOISE, "doubling" retracted.
- **Selection/multiple-testing** — routing on robust SIGN (not magnitude) with the baseline FROZEN at
  +1.37 is the **conservative** action, not a rationalization; the flow factor was already independently
  confirmed in iter_012, and only ~one marginal d.o.f. (the vol window, robustness-swept) was added.
- **Carry-cap** — agree: ship knob-free RP-3; keep the cap as a dropped, documented diagnostic.
- One methodological nit (applied): report the **Student-t(df)** two-sided p (≈0.11), not the normal
  approx (≈0.09). Fixed before commit.

**Constructive next steps for the CONFIRMATION (per critic):**
1. The t-stat is gated by **n**, not effect size (≈n=30 months needed at this effect to clear |t|≥2.1).
   Highest-value action = accumulate **genuinely forward** OOS months (post-iter-015 commit) unseen by
   the 012→015 search; read the significance verdict on that *new* window.
2. Designate a **true forward held window**; pre-register the Sharpe floor (don't give back below the
   real-2×-cost +1.93) and the DD target (combined OOS ≤ −23%, i.e. hold baseline) BEFORE the reveal.
3. **Carry is the structural fragility, not flow** — IS −0.03, single-regime, −67% standalone DD at a
   ~1/3 risk share. Pre-register a carry-regime falsifier: if carry's contribution to the combined OOS
   net flips negative on the held window, the candidate is a 2-factor (trend+flow) story.
4. Benchmark vs equal-weight 3-factor basket AND baseline on **Sharpe and DD**, never total return.

## Verdict: PROMISING → route the KNOB-FREE inverse-vol RP-3 to a held-OOS CONFIRMATION. Baseline UNCHANGED.
Honest framing: a **directionally robust** lift over the WF-λ baseline whose **magnitude is within
n=16 noise** (paired t=+1.68, p≈0.11), that **survives a real coin-level 2× cost** (+1.93), corroborated
by a **converged, verified** ERC (+2.31, agrees). NOT a confirmed doubling. Baseline stays iter_005
WF-λ (IS +1.30 / OOS +1.37 / −23%) until a separate held-OOS CONFIRMATION + critic PASS — promotion is
the orchestrator's call after that reveal.

## Axis status
- **Risk-parity multi-factor combiner (trend+carry+flow): OPEN — PROMISING, FIRMED, routed to
  held-OOS CONFIRMATION.** The iter_014 promotion package is now honest: the ERC corroboration is real
  (converged + verified), the cost stress is real (coin-level 2× → +1.93), and the lift is correctly
  labeled within-noise-but-sign-robust. Cleanest vehicle = knob-free inverse-vol RP-3.
- **Outstanding for the CONFIRMATION:** forward held-OOS window (move the paired t on unseen months),
  carry single-regime falsifier, Sharpe/DD pre-registration.

## Next
- **iter-016 (CONFIRMATION-track): held-OOS reveal of the knob-free RP-3** on a forward window unseen by
  the 012→015 search, with pre-registered Sharpe floor (≥ +1.93 at real 2× cost) and DD target
  (combined OOS ≤ −23%), the carry-regime falsifier, and the equal-weight-basket + baseline benchmarks
  on Sharpe/DD. If the direction survives the held window → PROMOTE to baseline.
