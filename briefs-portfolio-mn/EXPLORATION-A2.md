# EXPLORATION-A2 — Cross-Sectional Beta-Neutralization of the Funding-Carry Basket (engine backtest; IS-only; pre-registered)

## Section 0 — Provenance & scope (pre-registration)

- **Frozen:** 2026-07-10, BEFORE any engine backtest runs. This brief is the frozen contract; the QE
  runs the matrix ONCE and the results are scored against the gates below. **No post-hoc tuning** —
  any change to construction, variants, gates, predictions, decision map, or interpretation
  thresholds after the run invalidates the pre-registration and must be recorded as a new EXPLORATION.
- **Track:** baseline-BLIND MARKET-NEUTRAL portfolio (worktree `quant-portfolio-blind`). Charter
  `ORCHESTRATOR_BRIEF_MN.md`; PLAN `diary-portfolio-mn/PLAN.md` §2 Sketch A + §4.1 (binding).
  **Predecessors (all IS-only, holdout never touched):** `EXPLORATION-A.md` + PRE-RUN AMENDMENT 001
  (the frozen contract this one forks), `EXPLORATION-A-engineering.md` (the REVEALED IS results I
  compare against), `REVIEW-A.md` (Critic), `PHASE7-A.md` (my FAIL verdict — G3 sole HARD breach at
  0.2365; adopted Critic axis 1 → this brief).
- **BASELINE-BLINDING intact.** Designed against `mn_*` / `blind_*` infrastructure + the revealed
  EXPLORATION-A IS numbers only. **No baseline artifact read** (`BASELINE_PORTFOLIO.md`,
  `analysis/portfolio/iter_*.py`, `diary-portfolio-top20/`, `CONFIRMATION-005.md`, sibling
  worktrees — none touched). The old vol_low family is CLOSED; no signal inherited from it.
- **MN SPLIT — IS-ONLY end to end. NO holdout reveal in EXPLORATION-A2.** `MN_IS_CUTOFF =
  2026-01-01` SEALED; every number on `open_time < MN_IS_CUTOFF` via `mn_slice_is`; `mn_guard_grid`
  asserted at the top and on every tranche grid. Old-track `is_mask` / `OOS_CUTOFF` /
  `slice_is` are the WRONG split and MUST NOT be used. Verdict semantics = **IS design-validation
  only**, explicitly NOT deployability.
- **Backtests run by this QR: ZERO.** The QE runs the frozen matrix; no side-probes.
- **The ONE change vs EXPLORATION-A:** the neutralization ARCHITECTURE. Signal, universe, liquidity
  floor, per-name cap, cadence, tranche-ensemble, and costs are BYTE-FROZEN from EXPLORATION-A. The
  BTC/ETH `HedgeOverlay` is REMOVED (`hedge_overlay=None`) and replaced by folding the beta
  cancellation INTO the alpha weights (a cross-sectional projection). This isolates the architecture
  as the sole variable — the direct test of PHASE7-A's question.

### 0.1 Design thesis + the falsifiable-both-ways question (one paragraph)

PHASE7-A adjudicated EXPLORATION-A a FAIL on G3 alone (|Σw|/gross 0.2365 vs 0.10), and the QE
forensic (§9a) localized it precisely: the alpha book is dollar-neutral exactly (Σw_alpha≡0) but
carries structural **negative BTC beta ≈ −0.22 in 2024-25**, so a spot-BTC-hedge overlay must run a
**+0.22 long BTC leg = the entire post-hedge dollar-net** — a spot beta hedge cannot satisfy
|Σw|≤0.10·gross when |β_alpha|>0.10. The doctrine axis PASSED everywhere (G2-CRASH +0.0103), so the
breach was dominantly a gate-vs-doctrine mis-specification, with a genuine secondary margin-footprint
residual. **Cross-sectional beta-neutralization removes the hedge leg by construction:** the BTC-beta
cancellation is folded into the alpha weights (solve for w with Σw=0 AND Σw·β=0 simultaneously), so
there is no separate leg carrying the dollar-net and G3's |Σw| is structurally ~0. This brief runs
that construction and answers, **falsifiably both ways**, the question PHASE7-A raised: *does the
carry edge survive without the ~22% directional BTC leg?* If A2's net Sharpe survives ≈intact (≥1.3;
§3/§5), the overlay's dollar-net was an IMPLEMENTATION ARTIFACT and cross-sectional neutralization is
the correct MN architecture. If it COLLAPSES (≤0.7), the EXPLORATION-A Sharpe was materially a
DISGUISED BETA BET — the 22% leg was carrying return, not just risk — and the family's forward band
revises down. Both outcomes are valuable; the experiment is designed to discriminate them.

### 0.2 MANDATORY regime relabel (PHASE7-A §3 — carried into every successor)

The PLAN §2 Sketch A claim "who pays us, in ALL regimes" is **FALSIFIED on the earnings axis and is
BANNED in this brief.** EXPLORATION-A showed the book is **crash-NEUTRAL, not crash-profitable**:
crash-bucket β is clean (+0.0103) but crash PROFIT is a burned-window artifact (+0.54 → −0.01 bps/cd
ex-2025-03→2025-12), and 98% of P&L is CHOP (69.6%) + MANIA (28.6%). **The mechanism claim for A2 is:
a CHOP/MANIA funding-carry harvester that is BREAK-EVEN-NEUTRAL in CRASH.** The funding-collects-in-
crash leg is offset by the price giveback there (DIAG-A CRASH price −22.7 vs funding +13.3 bps). The
sealed holdout (2026+) is **crash-heavy** — the adverse regime for this earner — and that is disclosed
here as a standing forward risk on any future reveal.

---

## Section 1 — Construction (FROZEN)

Byte-frozen from EXPLORATION-A except the neutralization architecture. Run through the UNCHANGED
`blind_engine.run_backtest` (`hedge_overlay=None`) plus ONE new opt-in weight-builder extension
(`beta_neutralize`, §1.5, inert-default byte-identical). All parameters frozen.

**1.1 Signal — IDENTICAL to EXPLORATION-A §1.1 (byte-frozen).** `signal_engine = -build_signal(fund,
univ)` (import `build_signal` from `mn_diag_a_funding`; high engine-signal ⇔ low/negative funding ⇔
LONG). The QE re-asserts the sign pin element-for-element.

**1.2 Universe + liquidity floor — IDENTICAL to EXPLORATION-A §1.2 (byte-frozen).** PIT top-N by
trailing-30 mean $-volume via `build_universe` (≥270-candle history mask), N=40 PRIMARY / N=20
robustness, plus the frozen **$3,000,000/8h trailing mean $-volume floor** (same 270-history-masked
trailing-$-vol array the universe ranks on; no backfill of rank-41+ names).

**1.3 Base weighting + per-name cap — IDENTICAL builders to EXPLORATION-A §1.3.**
`weighting="rank_neutral"`, `gross=1.0` (Σw_raw=0, Σ|w_raw|=gross); per-name cap `|w_i| ≤ 0.10·gross`
via the same iterative pro-rata same-leg redistribution to a fixed point; the frozen `min_members =
N/2` infeasibility rule (skip rebal, hold previous weights, counted). **The cap and min_members
interact with the projection at a PINNED point in the order of operations (§1.6).**

**1.4 Cadence + tranche ensemble — IDENTICAL to EXPLORATION-A §1.4 (byte-frozen).** `rebal=21`
(weekly); 21-phase equal-weight tranche ensemble via `trim_panel` + `map_to_grid` +
`common_metric_mask`; headline = the phase-agnostic mean (selects nothing). Same MN-split slice
(`mn_slice_is`, NOT `slice_is`).

**1.5 NEUTRALIZATION ARCHITECTURE (the ONE change) — cross-sectional minimal-distortion projection.**
NO `HedgeOverlay`. At each rebal, after the raw rank weights `w_raw` are built on the tradeable
members, project them onto the intersection of the two linear constraints while staying as close as
possible (minimal L2 distortion) to `w_raw`:

- **Neutralize BTC only** (β = `mn_beta.rolling_beta(panel)`[k−1], frozen defaults 270/135/λ=0.33/
  clip[0,3]); **the ETH criterion is MEASURED, not neutralized** (justification below). Constraint
  set: **Σw = 0 AND Σw·β = 0.**
- **Method (frozen, exact):** on the member set M (universe ∩ valid fill price ∩ finite signal ∩
  finite β), with `A = [[1,…,1],[β_M]]` (2×|M|) and `w_raw,M`:
  `w_proj,M = w_raw,M − Aᵀ (A Aᵀ)⁻¹ (A w_raw,M)` — the orthogonal (minimal-L2) projection onto
  `{w : A w = 0}`. Since Σw_raw=0, `A w_raw = [0, b]ᵀ` with `b = Σ w_raw·β` (the book beta), so the
  correction removes exactly the beta while preserving Σw=0. `(A Aᵀ) = [[|M|, Σβ],[Σβ, Σβ²]]` (2×2),
  inverted in closed form.
- **Rescale to gross:** `w_M ← w_M · gross / Σ|w_M|` — a positive scalar, so it preserves Σw=0 AND
  Σw·β=0 exactly.
- **Why BTC-only (justified, evidence-grounded):** (i) EXPLORATION-A REVEALED that the BTC leg alone
  already neutralized ETH — G1b 100% within-bound / max|β_ETH| 0.1016, ETH-arm fired only 2.0% of
  rebals; a separate ETH constraint was empirically near-redundant. (ii) PLAN §4.1 point 3: per-name
  BTC and ETH betas are heavily collinear across alts, so a JOINT two-factor projection is
  ill-conditioned and churns window-to-window — the exact reason the PLAN rejected cross-sectional
  neutralization for the overlay; using ONE well-estimated constraint (BTC) and MEASURING ETH is the
  parsimonious, well-conditioned choice. (iii) Minimal distortion — one constraint moves the weights
  least. **G1b/G2-ETH are still gated (§4) on the realized stream**; if BTC-only fails them, that is
  the pre-registered `A2-ETH` contingency (§5), a tightly-scoped ONE-shot add of the ETH constraint.

**1.6 PINNED order of operations at each rebal (exact — no ambiguity):**
1. Determine member set M = universe[k−1] ∩ finite signal[k−1] ∩ valid fill price at k ∩ finite
   β[k−1]. (Valid-fill-price matches the engine's force-exit set, so the projected book is Σw=0 over
   TRADEABLE names.)
2. **Feasibility (min_members):** if |M| < N/2 → INFEASIBLE: skip the rebal, hold previous weights,
   increment `n_infeasible_rebal`. (Frozen C2 rule, identical to EXPLORATION-A.)
3. **Build raw rank weights** `w_raw` on M (`target_weights`, Σw=0, Σ|w|=gross).
4. **β-projection** (§1.5) → `w_proj` (Σw=0, Σw·β=0).
   - **Degenerate-β fallback:** if `det(A Aᵀ) < 1e-12 · |M| · Σ(β−β̄)²` (β near-constant across M ⇒
     the β-constraint is degenerate/rank-deficient), SKIP the projection, keep `w_raw` (already
     Σw=0), increment `n_beta_degenerate_rebal`. The book is merely dollar-neutral that rebal; G1/G2
     catch any realized β.
   - **Projection-collapse guard:** if `Σ|w_proj| < 0.10 · gross` (the β-correction nearly cancelled
     the book ⇒ rescaling would explode individual weights), treat as INFEASIBLE (skip, hold
     previous), increment `n_projection_collapse_rebal`.
5. **Rescale** `w_proj` to Σ|w| = gross (preserves both constraints).
6. **Per-name cap** (iterative pro-rata same-leg to fixed point) — LAST. The cap preserves Σw=0
   (same-leg redistribution) but perturbs Σw·β by a second-order residual; **this residual is
   MEASURED and REPORTED** (post-cap target `Σw·β`) alongside the realized rolling/bucket β. Cap-last
   is chosen so the HARD per-name notional cap (a real risk limit) is honored EXACTLY on the weights
   held, at the cost of a tiny measured target-β residual that the realized-β gates (windowed
   averages) tolerate.
7. The engine fills `w_target` and applies its standard mid-hold mechanics. **Mid-hold force-exits**
   (a held name going invalid-price before the next rebal) create a transient |Σw|≠0 residual —
   IDENTICAL to EXPLORATION-A Cell-3's mechanism (unhedged), NOT a hedge leg. This is the honest G3
   floor (§3).

**1.7 Costs — IDENTICAL to EXPLORATION-A §1.6 (byte-frozen).** `CostModel(5.0, 2.5, funding=True)`;
funding on every perp leg; **2×-cost twin `CostModel(10.0, 5.0, True)`.** A2 is **STATELESS w.r.t.
cost** (no arming, no dd-brake, no vol-target; the projection uses price-return betas β[k−1], not
book returns), so the analytic twin `rets_2x = rets_1x − turnover·cost_side` is valid again (expected
agreement ~2.6e-4, pure fixed-share drift, no arm-flips). **Per PHASE7-A §4.1 the QE STILL runs
ground-truth 2× re-runs (authoritative), analytic as cross-check** — the new catalog rule is
"ground-truth for anything that could be stateful; analytic is stateless-only and is a cross-check
regardless."

---

## Section 2 — Variants (FROZEN — kept minimal; ledger is at ~7 DOF)

| Cell | Neutralization | Floor+Cap | N | Purpose |
|---|---|---|---|---|
| **A2-1 (PRIMARY)** | cross-sectional BTC projection | ON | 40 | the candidate MN carry book, no hedge leg |
| **A2-N20** | cross-sectional BTC projection | ON | 20 | pre-registered robustness column (DIAG-A both-N mandate) |

**Comparison column — DO NOT RE-RUN.** EXPLORATION-A **Cell-1** (overlay, floor+cap, N40) is already
REVEALED on the identical common metric window: **net Sharpe +1.7753, 2×-GT +1.5616, maxDD −24.68%,
turnover 54.9×, G2-CRASH β +0.0103, G3 max 0.2365, funding 6/6 yrs.** These numbers stand as the
comparison and are CITED, never re-run. (EXPLORATION-A **Cell-3**, unhedged floor+cap N40, is also
cited for its G3 force-exit floor: max |Σw| **0.1080** from invalid-price force-exits — the mechanism
A2 inherits.) No unhedged/no-projection A2 cell is run: Cell-3 already IS the "no-neutralization"
reference, revealed.

**Funding-only lens** (uncosted `−funding_rets`; costed honesty line `−funding_rets − turnover·
cost_side`) is a within-run attribution on both cells — no extra runs (G-durable, §4/C6).

**Compute footprint:** 2 constructions × 21 tranches × 2 cost tiers (ground-truth) = **84 tranche
backtests** + analytic cross-check (post-processing). IS-only; fast; no long-run flag.

---

## Section 3 — Pre-registered predictions (point + bands; the load-bearing unknowns)

Anchored to the REVEALED EXPLORATION-A Cell-1 (same metric window) where a ratio applies; WIDE bands
on genuine unknowns (the /007 rho_bar discipline). All refer to A2-1 (PRIMARY) unless noted.

| Quantity | Point | Band | Reasoning |
|---|---:|---|---|
| **Net ensemble Sharpe (headline)** | **+1.45** | **[+0.9, +1.75]** | β-projection shrinks the high-β short-meme leg (which carries funding income), a real but modest tax vs Cell-1's +1.7753 |
| **Sharpe ratio A2 / Cell-1** | **0.82** | [0.51, 0.99] | the both-ways discriminator (thresholds below) |
| **Projection distortion — Spearman ρ(w_proj, w_raw)** | +0.90 | [0.75, 0.97] | minimal-L2 projection stays close except in the high-\|book-β\| 2024-25 era |
| **Realized G3 max \|Σw\|/gross** | **+0.10** | **[+0.05, +0.15]** | projection makes target Σw=0 EXACTLY every rebal; residual is the FORCE-EXIT/drift floor — Cell-3 hit 0.1080 by this mechanism, A2 inherits it (NOT a hedge leg) |
| **Crash-conditional β_BTC** | +0.02 | [−0.03, +0.08] | direct neutralization via trailing β[k−1]; DIAG-E1: trailing OLS under-estimates crash-state β → comparable to Cell-1's +0.0103, maybe marginally higher; well inside 0.15 |
| **Full-slice OLS β_BTC** | +0.00 | [−0.03, +0.03] | direct target neutralization → tighter than Cell-1's −0.0120 |
| **Rolling-270 β_ETH within-bound (G1b)** | 99% | [95%, 100%] | BTC-only projection; EXPLORATION-A showed BTC leg alone gave ETH 100%/0.1016 |
| **Post-cap target-β residual (Σw·β)** | 0.01 | [0.00, 0.04] | cap (last) re-introduces a second-order β; larger at N20 (cap binds 22.3%) |
| **maxDD** | −20% | [−12%, −28%] | neutralization removes the negative-β tail that drove some DD; but lower gross-return |
| **2×-cost net Sharpe (ground truth)** | +1.25 | [+0.7, +1.55] | weekly turnover; stateless → analytic agrees ~2.6e-4 |
| **Turnover (ann one-way)** | 60× | [45×, 90×] | projection adds modest rebal churn over Cell-1's 54.9× (weights move toward β-neutral each rebal) |
| **MANIA-bucket net mean (/mo)** | +3.0% | [+1.0%, +5.0%] | shrinking short-meme leg cuts mania income vs Cell-1's +5.13% |
| **Min per-year Sharpe** | 0.0 | (2022 the thin year, as Cell-1) | 2022 TOTAL was −0.165 for Cell-1; neutralization may push it either way |
| **Beta-degenerate rebal fraction** | <1% | [0%, 3%] | β rarely near-constant across 20-40 members |

### 3.1 The both-ways interpretation thresholds (FROZEN, pre-registered NOW)

Scored on A2-1 net ensemble Sharpe vs the revealed Cell-1 +1.7753 (same window):

- **SURVIVE-≈INTACT — A2 Sharpe ≥ 1.30 (≥ ~0.73× Cell-1):** the carry edge survives beta-
  neutralization with a modest tax. **Interpretation: the overlay's 0.2365 dollar-net was an
  IMPLEMENTATION ARTIFACT** of the spot-hedge architecture, not a property of the edge. Cross-
  sectional neutralization is the correct MN architecture. (Tier still requires all HARD, incl.
  frozen G3 — §5.)
- **DISGUISED-BETA — A2 Sharpe ≤ 0.70 (≤ ~0.40× Cell-1):** the edge collapses when the ~22%
  directional BTC exposure is removed. **Interpretation: EXPLORATION-A's Sharpe was materially a
  DISGUISED BETA BET** — the leg carried return, not just risk. The funding-carry edge is weaker
  than it appeared; the family's forward band revises DOWN (a genuine negative finding about the
  edge's nature). The family may retain a lower-Sharpe chop/mania-harvester identity, disclosed.
- **PARTIAL — 0.70 < A2 Sharpe < 1.30:** the edge survives with a QUANTIFIED neutralization tax;
  report the magnitude; the forward band adjusts proportionally. Not a kill; a measured cost.

These ratios are pre-registered against my own REVEALED IS number (fair iterative-research anchor),
not fitted to any A2 output.

---

## Section 4 — Pre-registered GATES (FROZEN charter/PLAN set, VERBATIM — ZERO deltas from EXPLORATION-A)

**Identical gate set and thresholds to EXPLORATION-A §4 + AMENDMENT 001, including G3 as written
(|Σw| ≤ 0.10·gross at every rebal).** G3 is scored on A2's UNSEEN numbers — that is the axis-1 point.
C5 measurement mechanics (BTC/ETH HOLD-return regressor open→open; rolling 270/135; RETURN-candle
`mn_regime_labels`; any G2/G4 bucket n<30 → loud N/A-FAIL) and C6 funding-income sign (`−funding_rets`,
G-durable on the years-positive count) carry over verbatim.

| # | Gate | Threshold | H/S |
|---|---|---|---|
| G1a | rolling-270 \|β_BTC\| ≤ 0.10 on ≥95% AND max ≤ 0.20 | | HARD |
| G1b | rolling-270 \|β_ETH\| ≤ 0.15 on ≥95% AND max ≤ 0.25 | | HARD |
| G2 | bucket-conditional \|β_BTC\| ≤ 0.15 in CRASH and MANIA each | | HARD |
| **G3** | **max \|Σw\|/gross ≤ 0.10 at every rebal (post-construction; unseen)** | | **HARD** |
| G4 | worst-bucket net-return t > −1.0 | | HARD |
| G5 | no bucket > 60% of total P&L | | SOFT |
| G-sharpe-floor | net ensemble Sharpe ≥ +0.35 | | HARD |
| G-sharpe-target | ≥ +0.90 | | SOFT |
| G-durable | funding-only positive in ≥5/6 IS years (uncosted `−funding_rets`) | | HARD |
| G-2xcost | 2×-cost net Sharpe > 0 AND ≥ 0.5×(1×) | | HARD |
| G-2xcost-target | ≥ +0.60 | | SOFT |
| G-maxdd | ≥ −25% | | HARD |
| G-maxdd-target | ≥ −15% | | SOFT |
| G-turnover | ≤ 250×/yr | | HARD |
| G-sample | ≥200 live rebals/tranche AND ≥40 names | | HARD |
| G-contam | ex-2025-03→12 Sharpe ≥ 0.7× full-IS | | SOFT |

**11 HARD, 5 SOFT** (unchanged). **G-durable clarification (PHASE7-A §4.2):** the drip "Sharpe" is
NOT informative; G-durable is scored on the **6/6-years-positive count only** (Sharpe magnitude
reported but not gating).

**G4/G5 handling under the honest relabel (§0.2), pre-registered:**
- **G4 (worst-bucket t > −1.0):** the mechanism is crash-BREAK-EVEN-neutral, so a **CRASH t near 0 is
  the EXPECTED and PASSING outcome** — G4 fails only if a bucket SIGNIFICANTLY loses (t ≤ −1.0). A
  crash t ≈ 0 is neutrality delivered, not a failure.
- **G5 (no bucket > 60% of P&L):** a carry harvester earns most in CHOP by nature; **G5 SOFT-fail is
  EXPECTED and DISCLOSED** (EXPLORATION-A CHOP 69.6%). It does not gate the tier; the concentration
  is reported and carried in the relabel. Neutralization may shift the CHOP/MANIA split (shrinking
  the mania short-meme leg raises CHOP's relative share) — reported.

---

## Section 5 — Frozen decision map (IS design-validation only; NO holdout reveal)

Discriminating axes: (i) **frozen G3 on unseen numbers** (the architecture test), and (ii) the
**both-ways Sharpe interpretation** (§3.1, the edge-nature test). SUCCESS requires BOTH neutrality
AND a surviving edge.

| Outcome | Condition | Interpretation |
|---|---|---|
| **SUCCESS** | ALL 11 HARD pass (incl. frozen G3 ≤0.10, G2-CRASH, G-durable-years) AND A2 Sharpe ≥ 1.30 | Cross-sectional neutralization delivers realized-beta neutrality AND holds \|Σw\|≤0.10 by construction AND the edge survives ≈intact → **the overlay's dollar-net was an implementation artifact; A2 becomes THE candidate for the family-A holdout-reveal DECISION** (which goes to the USER, never automatic — §5.1). |
| **SUCCESS-TAXED** | ALL 11 HARD pass AND 0.70 < A2 Sharpe < 1.30 | Neutral, G3-clean, edge survives with a QUANTIFIED tax → still a holdout-reveal candidate, presented to the USER with the measured neutralization cost and a band-adjusted forward expectation. |
| **FAIL — edge collapse** | (regardless of gates) A2 Sharpe ≤ 0.70 | The edge was substantially DISGUISED BETA. Not a reveal candidate; family forward band revises DOWN; documented as a negative finding on the edge's nature. |
| **FAIL — G3 at the force-exit floor** | G3 breaches (max \|Σw\| in ~[0.10, 0.15]) BUT the breach is FORCE-EXIT/drift (not a hedge leg — verify via the p=0 forensic that Σw_target≡0 at rebal and the residual is mid-hold force-exit) AND realized β G1/G2 PASS | Pre-registered SPECIFIC outcome. Yields (a) the Sharpe-cost answer (still scored vs Cell-1) and (b) evidence that frozen G3 (|Σw|≤0.10 through delisting force-exits) is un-meetable by ANY crypto-perp book → **triggers the bounded axis-2 CONSIDERATION** (§5.2). NOT a reveal; NOT an automatic amendment. |
| **FAIL — other neutrality HARD** | G1a/G1b/G2/G4 fails, or G3 breaches by a NON-force-exit mechanism | Localize; document; not revealed. If G1b/G2-ETH is the sole failure → the bounded **A2-ETH** contingency (§5.3). |
| **FAIL — other performance HARD** | G-2xcost/G-maxdd/G-turnover/G-sample fails with edge intact | Localize; document; not revealed. |

### 5.1 What SUCCESS means + reveal protocol (unchanged from EXPLORATION-A §5.1)
SUCCESS/SUCCESS-TAXED makes A2 the **candidate for the family-A holdout-reveal DECISION — a USER
decision, never automatic.** The holdout stays SEALED in this exploration. The reveal is spent ONCE
per family, ever, only at a future CONFIRMATION-A after IS robustness is documented (phase sweep —
already built as the ensemble; 2×-GT twin; regime buckets; contamination twin; the both-ways
interpretation). The reveal, when the USER sanctions it, is the single call
`mn_guard_holdout(..., confirmation_reveal="funding-carry")`. **This brief does NOT authorize any
reveal; the QE script never passes `confirmation_reveal`.** Standing disclosure on that decision: the
holdout is crash-heavy, the adverse regime for a CHOP/MANIA harvester (§0.2).

### 5.2 Bounded axis-2 CONSIDERATION (pre-registered NOW, tight scope)
Triggered ONLY by the "FAIL — G3 at the force-exit floor" row. It is a CONSIDERATION, not an action:
I would author a dated **PLAN-AMENDMENT** proposing a force-exit-aware G3 (e.g., |Σw| measured at
REBAL only, or excluding the mid-hold force-exit transient), **principle-anchored, number NOT fitted
to the observed force-exit floor, denominator pinned, scored ONLY on unseen data, contamination
disclosed** (+1 family-A n_eff → 9). It requires coordinator/USER assent — never automatic, never in
this doc. If the observed G3 breach is NOT force-exit-mechanism (e.g., a projection artifact), this
consideration does NOT fire; plain FAIL.

### 5.3 Bounded A2-ETH contingency (pre-registered NOW, tight scope)
Triggered ONLY when G1b or G2-ETH is the SOLE HARD failure (BTC-only projection left too much ETH
beta). ONE-shot: add the ETH constraint to the projection (`A = [1; β_BTC; β_ETH_resid]`, 3×|M|),
accepting the PLAN §4.1 conditioning cost, with a condition-number guard (fall back to BTC-only +
flag if `cond(AAᵀ) > 1e6`). Signal/universe/cap/cadence stay byte-frozen; +1 family-A n_eff. If
A2-ETH still fails G1b/G2-ETH ⇒ the collinearity is irreducible; family shelved on the ETH axis,
holdout NOT spent. Bounded to ONE attempt.

### 5.4 What explicitly does NOT happen
- **NO holdout spend** (SUCCESS produces only a USER-facing candidate). **NO re-gate to any observed
  A2 number** (G3 stays ≤0.10 as scored; any re-spec is §5.2, unseen-data only). **NO construction
  change post-run.** **NO automatic follow-up** beyond the two tightly-scoped, pre-registered §5.2/
  §5.3 contingencies. The EXPLORATION-A `A2` hedge-retry does not exist here (no hedge overlay).

---

## Section 6 — Multiple-testing honesty (family-A n_eff ledger)

- Running family-A n_eff BEFORE this brief: **≈ 7 DOF** (DIAG-A 3 cadence cells + EXPLORATION-A 3
  construction cells + 1 researcher-DOF).
- **This registration: +1** (the cross-sectional-neutralization construction; A2-1 is the PRE-
  DESIGNATED primary, not a best-of selection; A2-N20 is a robustness column, not a selection). →
  **family-A n_eff ≈ 8.**
- **+1 each** IF the §5.2 axis-2 G3 re-spec OR the §5.3 A2-ETH contingency fires (→ 9). N20 stays a
  robustness read; promoting it to PRIMARY would be a selection event requiring re-ledgering (on the
  record).
- **Critic haircut instruction:** DSR/deflation consistent with n_eff ≈ 8 on any Sharpe; **IS-only,
  NO reveal → informational only** (sizes the future CONFIRMATION-A expectation, does not gate the IS
  verdict).

---

## Section 7 — QE deliverables spec

**Script:** `analysis/portfolio/mn_exploration_a2.py`. **No verdicts — tables + mechanical pass/fail
only.**

**Reuse VERBATIM (single source of truth):** everything EXPLORATION-A reused (§7 of that brief) —
`build_signal`, `build_universe`, `TOP_N_*` from `mn_diag_a_funding`; `rolling_beta` from `mn_beta`;
`load_funding`; `mn_regime_labels`/`regime_occupancy`; `run_backtest`/`CostModel`/`target_weights`/
`_metrics`/`PERIODS_PER_YEAR` and the sanctioned `weight_cap`/`min_members` engine params from
`blind_engine`; `load_panel`/`Panel`; `mn_slice_is`/`mn_guard_grid`/`MN_IS_CUTOFF_MS`/`MN_STEP_MS`;
`mn_panel_health`/`MnDataError`; the pure ensemble helpers (`map_to_grid`, `common_metric_mask`,
`ensemble_result`, `ann_vol`, `dd_path`, `ensemble_monthly_table`) + `trim_panel` (re-implement
locally if they don't import clean). **`mn_slice_is`, NOT `slice_is`.**

**New engine/weight-builder extension — `beta_neutralize` (opt-in, inert-default byte-identical):**
- A module function `apply_beta_neutralization(w_raw, beta_row, member_mask, gross)` implementing
  §1.5/§1.6 steps 3–5 exactly (minimal-L2 projection onto {Σw=0, Σw·β=0}, degenerate-β fallback,
  projection-collapse guard, rescale to gross). Wired into `run_backtest` behind a new
  `beta_neutralize: (T,C) array | None = None` param (the per-name β at [k−1]); **`None` = byte-
  identical to the current engine** (required test). Applied AFTER `target_weights`, AFTER the
  invalid-price force-exit (so M = valid-price members), and BEFORE the `weight_cap` (order §1.6).
- New forensic metrics (inert-zero when off): `n_beta_degenerate_rebal`, `n_projection_collapse_rebal`,
  `post_cap_target_beta_max/mean` (the §1.6-step-6 residual), plus the existing EXPLORATION-A
  counters.

**Required tests (house style, ABORT on fail):**
- **Inert-default byte-identity:** `beta_neutralize=None` reproduces the current engine bit-for-bit
  on one Cell (weights/turnover/equity/rets/funding_rets `assert_array_equal`).
- **Corrupt-future-β positive control:** corrupt `beta_neutralize[t:, :]` (set ±large) → the
  projected weights `w[:t]` are bit-identical to the uncorrupted build (β consumed at [k−1], past-
  only); future changed (non-vacuous).
- **Projection-correctness on synthetic cases:** given random `w_raw` with Σ=0 and a known β, assert
  post-projection (pre-cap, pre-rescale) `|Σw| ≤ 1e-12` AND `|Σw·β| ≤ 1e-12`; post-rescale
  `|Σ|w|−gross| ≤ 1e-12` with both constraints still ≤1e-12; **minimal-distortion property** (the
  correction is orthogonal to the constraint null space — `w_proj − w_raw ∈ row-space(A)`, checked
  numerically); **degenerate-β fallback** (β constant → w unchanged, flag set); **projection-collapse
  guard** (construct a case where Σ|w_proj| < 0.1·gross → skip/hold, flag set).
- **Cap-after-projection ordering:** the cap operates on the projected+rescaled book; assert Σw=0
  preserved post-cap and `post_cap_target_beta` is REPORTED (not asserted to zero — it is the
  measured residual).
- **DIAG-A funding-sort signal corrupt-future leak positive control** (carried from EXPLORATION-A).

**Top-of-script hard order (ABORT on fail):** `mn_panel_health()` first; `pis = mn_slice_is(
load_panel())`; `mn_guard_grid(pis.grid_ms)` + last-candle extent assert; sign pin
`signal_engine == -build_signal(...)`; NEVER `is_mask`/`OOS_CUTOFF`/`slice_is`; `confirmation_reveal`
NEVER passed.

**Warmup / common mask (DERIVE + PIN; PHASE7-A / C3 discipline):**
- Derive the construction-minimum warmup programmatically as the first rebal `k` (multiple of 21)
  with `k−1 ≥ max( first-all-finite row of β_BTC , first rebal with ≥ N/2 feasible members )`.
- **Predicted:** the binding constraint is the universe's **270-candle-history filter** (feasibility
  ≈ index 270), NOT β_BTC (all-finite ≈ 135), so the warmup does **NOT** shorten despite dropping the
  ETH-residual-beta dependency — it lands at **k = 273, common-mask first-True = 293, IDENTICAL to
  EXPLORATION-A.** DISCLOSE this explicitly (dropping the ETH beta was expected to shorten the warmup;
  it does not, because the universe history filter — coincidentally ≈ the old ETH-beta warmup — is
  the true binding constraint).
- **Score A2 on the SAME common mask as EXPLORATION-A (first-True 293)** so the Cell-1 comparison is
  candle-for-candle identical. If the programmatic derivation comes out SHORTER than 293 (universe
  fills earlier than predicted), still score the Cell-1 comparison on the 293 intersection mask, and
  report the shorter A2-native window separately as informational. Assert the derived k and common
  first-True; print both; IDENTICAL mask across both cells and both cost tiers (asserted per
  cell/tier).

**Ground-truth 2× (per PHASE7-A §4.1):** re-run every cell's 21 tranches at `CostModel(10,5,True)`
(authoritative for G-2xcost); compute the analytic `rets_1x − turnover·cost_side` as a CROSS-CHECK,
report max elementwise drift (expected ~2.6e-4 since STATELESS — no arm-flips), **never assert 1e-12.**

**Internal reproducibility asserts:** bit-identical full re-run; leg reconciliation
`price − tcost − funding ≡ rets` ≤1e-12 all runs; hedge-inert control moot (no overlay) — instead a
**`beta_neutralize=None` inert control** on one tranche (≤1e-12 vs current engine); IS-guard on every
tranche grid.

**Required tables (observations only; verdicts BLANK — Phase 7):** the EXPLORATION-A table set (1:
headline per cell + funding-only lenses; 2: neutrality panel Cell A2-1 with C5 mechanics; 3: G3 +
projection/cap/floor/infeasibility forensics incl. `n_beta_degenerate`, `n_projection_collapse`,
`post_cap_target_beta`, and a **p=0 G3 forensic decomposing the max |Σw| into rebal-target vs
mid-hold-force-exit** — the §5 "force-exit floor" discriminator; 4: per-year Cell A2-1 total +
funding; 5–8: monthly, attribution, contamination, phase dispersion) **PLUS**: the **projection-
distortion table** (Spearman ρ(w_proj,w_raw) overall + per-era) and the **A2-vs-Cell-1 comparison
block** (net Sharpe, 2×-GT, maxDD, turnover, G2-CRASH β, G3 max, funding-years, and the Sharpe RATIO
with the §3.1 threshold bin printed — SURVIVE-INTACT / PARTIAL / DISGUISED-BETA — as a mechanical
bin, not a verdict). Gate scorecard: all 16 lines, observed vs frozen threshold, verdict cells BLANK.

**Do NOT:** touch the holdout / pass `confirmation_reveal`; read any baseline/CONFIRMATION artifact
or sibling worktree; use the old-track split; change any BYTE-FROZEN signal/universe/cap/floor/
cadence parameter; add any neutralization variant beyond the frozen BTC-only projection; select or
weight any phase unequally; re-run or re-tune after seeing results. Hand the report to the QR for
Phase-7 IS evaluation. **There is no holdout reveal in this phase.**

---

**FROZEN.** Construction (§1, incl. the pinned §1.6 order of operations and the BTC-only projection),
variants (§2), predictions + both-ways thresholds (§3), gate set (§4, zero deltas from EXPLORATION-A),
decision map + bounded contingencies (§5), and the n_eff ledger (§6) are locked as of 2026-07-10,
pre-run. Any deviation is a new EXPLORATION.

*— QR, MN track, 2026-07-10.*
