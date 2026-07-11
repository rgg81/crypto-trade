# CONFIRMATION-A — Frozen Holdout-Reveal Interpretation Map for A3-1 (family A; MN track)

**Date:** 2026-07-11 · **Author:** QR, MN track · **Status:** FROZEN interpretation map, complete
BEFORE any holdout number is computed or seen. **This document is the pre-registration record; it is
locked as of this commit. Once frozen, no tier, threshold, or decision rule below may change — the
tier the holdout numbers land in IS the outcome.**

**Authorization:** the USER has decided to SPEND family A's one-per-family-FOREVER holdout reveal on
A3-1 (overriding the QR/Critic HOLD/forward-first recommendations — their informed call; SURVEY-001
closed with A3-1 the sole survivor of five mechanism families, DIAG-C/B/D/E′ all dead, the ensemble
capstone untriggerable at 1/5). This map governs that single reveal.

**Anchors read:** `PHASE7-A3.md` (the SUCCESS-MARGINAL verdict + the banked forward band + caveats),
`REVIEW-A3.md` (the Critic's forward calculus + funding-leg-erosion note), `SURVEY-001-CLOSEOUT.md`
(the field). Blinding intact; **the holdout has NEVER been touched for family A; it is touched exactly
once, by the reveal this map governs.**

---

## Section 1 — The frozen construction (A3-1, BYTE-IDENTICAL — zero changes post-reveal, EVER)

The construction is the frozen A3-1 that produced `PHASE7-A3.md` / `EXPLORATION-A3-engineering.md`,
byte-identical. **No parameter, script, or default may change before, during, or after the reveal.**

- **Runner:** `analysis/portfolio/mn_exploration_a3.py` (the tranche-ensemble driver) + the new
  throttle module `analysis/portfolio/mn_scud.py`, over the UNCHANGED `blind_engine.run_backtest`
  (throttle wired via the pre-existing `gross_scalar_series`; no engine change).
- **Book (byte-frozen A2-1):** `mn_exploration_a2.py`'s `beta_neutralize` / `apply_beta_neutralization`
  (BTC-only minimal-L2 projection onto {Σw=0, Σw·β=0}; degenerate guard `Σ(β−β̄)² ≤ 1e-12·Σβ²` per
  the ratified erratum; collapse guard `Σ|w_proj| < 0.10·g`) on the DIAG-A signal/universe
  (`mn_diag_a_funding.build_signal` — 3d-mean cross-sectional funding z, min 5/9; `build_universe` —
  PIT top-40, ≥270-candle history, **$3M/8h liquidity floor**), rolling BTC β `mn_beta.rolling_beta`
  (270/135/λ=0.33/clip[0,3]), funding `blind_funding.load_funding`, per-name cap `|w_i| ≤ 0.10·g`
  (iterative pro-rata, cap last), weekly `rebal=21`, **21-phase equal-weight tranche ensemble**,
  costs 5+2.5 bps/side + funding on every leg.
- **The SCUD throttle (the single A3 addition, frozen §1.1/§1.2 + AMENDMENT 001):** short cohort =
  bottom `q_short=0.33` of `signal_engine` (highest-funding = shorted leg), `m_min=5`; trailing
  return `h=9`; `U = 75th percentile` of cohort returns; `SCUD_z` over `W=90`, `min_periods=45`,
  clip ±5; ramp `scalar(z)=1.0 − 0.5·clip((z−0.85)/(1.65−0.85),0,1)` (`τ_lo=+0.85, τ_hi=+1.65,
  φ=0.50`, continuous release); **C2 forward-fill = the final computed SCALAR** (backward-looking).
  Consumed at [k−1].
- **n_eff = 9, TERMINAL.** This is the exact object PHASE7-A3 validated on IS (all 11 HARD pass,
  MARGINAL disposition; IS pinned-mask Sharpe +1.7341, maxDD −23.11%, crash β +0.0094, G3 0.0699,
  funding 6/6).

---

## Section 2 — The reveal protocol (executed EXACTLY ONCE)

- **Holdout window:** `[2026-01-01 00:00 UTC, last fully-closed 8h candle in the panel]`. As of
  2026-07-11 that is ~6.3 months. Forming candles are dropped (fetcher convention); the window end is
  the last candle with `close_time < now`.
- **HONEST SAMPLE MATH (governs every threshold below):** ~0.52 years ≈ ~570 8h candles.
  **SE(annualized Sharpe) ≈ √(1/0.52) ≈ 1.39.** A Sharpe reading of +0.75 carries a 95% CI of
  roughly **[−2.0, +3.5]** — the Sharpe SIGN is barely determined by this window. **Therefore the
  Sharpe reading is the LOWEST-power number the reveal produces.** By contrast, the realized β is a
  slope estimated on ~570 candles with **SE(β) ≈ 0.01–0.02** — **neutrality is the HIGHEST-power
  test**, and the mechanism behaviors (does the projection transfer, does SCUD fire, does the
  funding drip persist) are near-deterministic. The tiers (§4) weight neutrality / mechanism / risk
  OVER the noisy Sharpe, by design and on the record.
- **Data hygiene FIRST (the starvation lesson):** the full panel through present must pass
  `mn_datacheck.mn_panel_health()` BEFORE the reveal fires. On `MnDataError` (corrupt BTC grid) the
  reveal is **ABORTED** — `mn_guard_holdout` is NOT called, the data is fixed, datacheck re-run; the
  one-forever reveal is spent ONLY on a clean, complete panel. (A DEGRADED live-feed verdict is
  logged and permitted — the window ends at the last clean closed candle regardless.) **The datacheck
  precondition is not a "second look"; it is a data-integrity gate that must pass before the single
  reveal, and it never re-opens the frozen tiers.**
- **The single guarded call:** the reveal is executed EXACTLY ONCE via
  `mn_guard_holdout(lo=2026-01-01, hi=window_end, confirmation_reveal="funding-carry")`. The token's
  loud one-per-family audit banner IS the permanent record; a second call with this family token is a
  process-integrity violation. After this call fires, family A's holdout budget is spent **forever**.
- **Warmup continuity:** the A3-1 ensemble is BUILT on the FULL panel `[2020-01-01, window_end]` (so
  every tranche's rolling β, SCUD-z, universe history, and warmup are continuously populated entering
  the holdout), and holdout metrics are computed on the ensemble streams sliced to
  `grid_ms ≥ MN_IS_CUTOFF_MS`. A reproducibility assert (§7) requires the IS portion to reproduce the
  revealed A3-1 IS numbers EXACTLY — proving the full-panel build did not perturb the frozen book.

---

## Section 3 — Pre-registered expectations (from the BANKED forward band, not hope)

These are priors, stated before the reveal, so hindsight cannot reshape them. They are NOT the tier
thresholds (§4) — they are what I expect, with the adversity documented.

- **Window composition FIRST (context for every number).** The QE reports the holdout `mn_regimes`
  CRASH/MANIA/CHOP fractions BEFORE any performance number. 2026 is documented ADVERSE — the SURVEY
  calls it crash-heavy; A3-1 is a **CHOP/MANIA funding-carry harvester, break-even-neutral in CRASH**
  (CHOP+MANIA ≈ 95% of IS P&L; crash bucket earns ≈ 0). A crash-heavy window is expected to STARVE
  the earning buckets, so a weak Sharpe here is the EXPECTED-under-adversity outcome, not a surprise.
  The composition explains the numbers; it does NOT move the frozen thresholds (§4).
- **Sharpe:** central **~+0.75**, band **~+0.5 to +1.1** (the banked forward band — IS anchor shaded
  down for the +1 DOF deflation and the funding-leg erosion). But per §2, the realized reading is
  ±1.39 — I expect a WIDE, weakly-determined number; I do not expect the point estimate to land near
  +0.75 with any precision.
- **maxDD:** **likely DEEPER than the IS −23.11%** — the IS pass was fragile (+1.89pp ≈ 1.25 noise-
  units) and the crash-heavy holdout is the adverse regime; a mid-20s-to-30s% drawdown would not
  surprise. The SCUD throttle's LEAD-timed squeeze de-risk is expected to help the drawdown SIDE
  relative to an un-throttled book, but it does not immunize against a deep adverse window.
- **Funding leg:** expected **POSITIVE** — its 6/6-IS-years record is the durable prior and the
  near-deterministic drip is high-power. A negative holdout funding leg would be a genuine shock.
- **Neutrality:** expected to **HOLD** — the mechanism (projection + scale-invariant throttle)
  transfers or it does not, and this is the highest-power test. IS full-slice β_BTC was −0.0116; a
  holdout β near zero is the expectation. A break to |β| ≫ 0.15 would mean the neutralization did not
  generalize — the single most important thing the reveal can tell us.

---

## Section 4 — The FROZEN decision tiers (locked before any number is seen)

**Four reads, defined precisely (all on the holdout slice, honest cost, C5 measurement pins §7):**

- **N — Neutrality (highest power):** N **HOLDS** iff full-window OLS **|β_BTC| ≤ 0.15 AND |β_ETH| ≤
  0.20** AND (crash-bucket **|β_BTC| ≤ 0.25** when the crash bucket has ≥30 holdout candles; WAIVED-
  and-reported if <30). Else N **BROKEN**. (Bounds are transfer-bounds — generous vs the IS 0.10
  rolling given the short window, but SE(β)~0.015 makes them ~8–10σ tests that a predecessor-class
  break (β→0.3–0.5) fails decisively. Rolling and per-bucket β are REPORTED as supporting context;
  the binary gate is the full-window + crash-bucket read.)
- **D — Drawdown (risk):** holdout maxDD. **Controlled** ≥ −33%; **elevated** ∈ (−45%, −33%);
  **catastrophic** < −45%.
- **S — Edge (lowest power — deliberately modest floor):** holdout net Sharpe (honest cost).
  **Positive-edge** ≥ +0.30; **weak** ∈ [−1.0, +0.30); **clear-negative** < −1.0.
- **F — Funding leg (durable core):** holdout funding income (uncosted `−funding_rets`).
  **Positive** > 0 / **non-positive** ≤ 0.

| TIER | Condition (evaluated in this order; FAIL triggers dominate) | Meaning |
|---|---|---|
| **FAIL** | **N BROKEN**, OR **D catastrophic** (maxDD < −45%), OR **S clear-negative** (Sharpe < −1.0), OR **F non-positive** (funding ≤ 0) — ANY ONE | The mechanism did NOT transfer (neutrality broke), OR the book blew a risk hole, OR it lost money materially, OR the durable carry core broke. The funding-carry line is falsified out-of-sample. |
| **DEPLOY-CANDIDATE** | **N HOLDS AND D controlled (≥ −33%) AND S positive-edge (≥ +0.30) AND F positive** | Neutrality transferred (anti-predecessor axis held OOS), drawdown controlled, a genuinely positive edge in an ADVERSE half-year, durable carry intact. A real-deployment CANDIDATE (not a certainty). |
| **AMBIGUOUS / PARTIAL** | **N HOLDS AND F positive AND D not-catastrophic (≥ −45%) AND S ≥ −1.0**, but NOT meeting the DEPLOY bar (i.e., S ∈ [−1.0, +0.30) OR D ∈ (−45%, −33%)) | **Mechanism HELD, edge UNPROVEN in an adverse half-year.** The construction is validated as market-neutral and durable OOS, but the crash-heavy window did not prove (nor disprove) the edge. The most likely outcome under the documented adversity + the ±1.39 Sharpe noise. |

**Why the Sharpe floor is deliberately modest (+0.30) and cannot FAIL alone:** with SE ≈ 1.39, a
negative half-year Sharpe is NOT evidence the strategy is bad — so a merely-weak Sharpe routes to
PARTIAL (edge unproven), never FAIL. FAIL-by-edge is reserved for a Sharpe < −1.0 (a materially
money-losing window even by half-year standards) OR the funding leg going non-positive (the durable
core, a high-power read, breaking). The DEPLOY case rests PRIMARILY on neutrality + mechanism + DD +
durable carry; the +0.30 Sharpe is a positive-edge CONFIRMATION, not the driver. This weighting is
the whole point of a small-sample confirmation and is frozen here so it cannot be re-weighted post-
hoc.

**NO POST-HOC TUNING, NO SECOND LOOK, NO RESCUE — whatever the outcome (in /005-CONFIRMATION
language):** The construction is byte-frozen (§1); these tiers are frozen here BEFORE any holdout
number exists; the reveal fires EXACTLY ONCE (§2). **The tier the numbers land in IS the outcome.**
There is no re-parameterization of the throttle, no re-projection, no window trim, no threshold
adjustment, no "the window was too adverse so let's discount the FAIL." Arguing with the tier a fired
reveal produces is a process-integrity violation, not a research move. A FAIL is as final as a
DEPLOY-CANDIDATE: the family-A funding-carry line is CONCLUDED either way — the reveal is the terminal
spend of a one-per-family-forever budget (§6), and no adjustment to A3-1 can ever earn a second
reveal (that would be a new family, not a rescue of A). The burned reveal is burned.

---

## Section 5 — What happens after each tier (pre-committed)

- **DEPLOY-CANDIDATE → USER decision on real-money / paper next steps.** The reveal produces a
  CANDIDATE, never a certainty; the deployment case is the **risk-adjusted profile** (Sharpe / maxDD
  / vol / realized neutrality / funding durability), **NEVER a buy-and-hold or absolute-return
  comparison**. The QR presents the full holdout characterization; the USER decides deployment path
  (paper-first vs sized real-money) and sizing. No auto-deploy.
- **AMBIGUOUS / PARTIAL → forward paper-trade continues the evidence gathering, ZERO additional
  budget.** The one-forever reveal is spent either way; PARTIAL means the honest verdict is "market-
  neutral + durable, edge unproven in an adverse window," and the correct next evidence is genuinely-
  unseen post-reveal data via the recompute architecture (an `mn_paper_*` clone of `blind_paper_l1`,
  frozen params, weekly append-invariant recompute — no exchange orders, no new backtest budget). The
  paper record accumulates until it (not another reveal) resolves the edge.
- **FAIL → ARCHIVE family A; DOCUMENT; the track's future is a new idea wave or a conclusion (USER's
  call).** The funding-carry line is closed. The transferable structural knowledge (SURVEY-001
  closeout: hedge dollar-net is an implementation artifact; funding is the only all-regime-payable
  flow; the crash-beta residualization limit; two-layer rank-vs-tails inversion) is banked regardless
  of the tier. No rescue of the FAILED construction.

---

## Section 6 — Ledger

- **The reveal is the TERMINAL spend of family A's budget.** Family-A n_eff = **9** (DIAG-A 3 cadence
  cells + EXPLORATION-A 3 construction cells + 1 researcher-DOF + EXPLORATION-A2 1 + EXPLORATION-A3 1
  = 3+3+1+1+1). No further family-A trials, ever; no second reveal, ever.
- **Deflation already priced in:** the §3 expectations (central ~+0.75, band ~+0.5–1.1) are the
  BANKED forward band, which already carries the +1-DOF deflation and the funding-leg-erosion shading
  (REVIEW-A3 Ruling 3). The tiers do not re-deflate; they read the realized numbers against
  pre-committed, already-deflated bars.

---

## Section 7 — QE spec (`analysis/portfolio/mn_confirmation_a.py`)

**No verdicts — observed values + the MECHANICAL tier bin (the §4 map applied arithmetically) only.**
The QR renders the formal CONFIRMATION verdict in a later doc.

**Hard order (ABORT on any failure BEFORE the reveal fires):**
1. `mn_panel_health()` on the FULL panel through present FIRST; on `MnDataError` **ABORT — do NOT
   call `mn_guard_holdout`** (fix data, re-run). DEGRADED is logged and permitted.
2. Build A3-1 BYTE-IDENTICAL on the FULL panel `[2020-01-01, window_end]` (warmup continuity, §2);
   assert the construction is bit-identical to the frozen A3-1 (inert-control: `gross_scalar_series`
   reproduces A2; proportionality throttled = s·A2 at ≤1e-12; **the IS-slice metrics reproduce the
   revealed A3-1 IS numbers EXACTLY** — Sharpe +1.7341, maxDD −23.11%, crash β +0.0094, G3 0.0699).
3. **The single reveal:** `mn_guard_holdout(2026-01-01, window_end,
   confirmation_reveal="funding-carry")` — the audit banner is the record. Fired EXACTLY ONCE.
4. Slice all ensemble streams to `grid_ms ≥ MN_IS_CUTOFF_MS`; compute holdout metrics on that slice.

**Full holdout characterization (report ORDER matters):**
1. **Window composition FIRST** — `mn_regimes` CRASH/MANIA/CHOP fractions over the holdout + candle
   count + window dates; every subsequent number annotated with the crash-fraction context.
2. **Neutrality panel (C5 pins: BTC/ETH HOLD-return regressor open→open; rolling 270/135; RETURN-
   candle `mn_regime_labels`; bucket n<30 → N/A-report):** full-window OLS β_BTC / β_ETH (with SE);
   rolling-270 β where estimable; bucket-conditional β_BTC for CRASH/MANIA/CHOP (with n; crash bucket
   flagged if <30). The N read (HOLDS/BROKEN) printed mechanically.
3. **Headline:** net Sharpe (honest + 2×-GT), ann vol, maxDD, turnover, ann return, monthly win rate.
4. **Regime-bucket P&L + funding/price attribution** (funding income = `−funding_rets`; the F read).
5. **SCUD throttle behavior OOS:** coverage (scalar<1 / =φ fractions; mean scalar); did SCUD fire in
   any 2026 drawdown episode(s) and with what timing (reuse the C4 LEAD/COINCIDENT/LAG annotation on
   the holdout's own worst months) — the mechanism-transfer forensic.
6. **maxDD path** (dates, depth) + **monthly table** (compounded + leg split).
7. **The mechanical tier bin** (DEPLOY-CANDIDATE / PARTIAL / FAIL) from §4, arithmetic only.

**Reproducibility asserts:** bit-identical re-run of the full script; leg reconciliation
`price − tcost − funding ≡ rets` ≤1e-12; ground-truth 2× authoritative (analytic cross-check only);
the IS-portion parity assert (step 2). **Do NOT:** change any frozen A3-1 parameter; call
`mn_guard_holdout` more than once or with any other token; trim the window; tune anything after
seeing a number. Hand the report to the QR for the CONFIRMATION verdict. **The reveal is spent on
execution; there is no second run.**

---

**FROZEN 2026-07-11, pre-reveal.** Construction (§1), reveal protocol (§2), expectations (§3), tiers
(§4), post-tier actions (§5), and ledger (§6) are locked before any holdout number is computed or
seen. **The tier the numbers land in is the outcome. No post-hoc tuning, no second look, no rescue —
DEPLOY-CANDIDATE, PARTIAL, or FAIL, the funding-carry line is resolved by this one reveal.**

*— QR, MN track, 2026-07-11.*
