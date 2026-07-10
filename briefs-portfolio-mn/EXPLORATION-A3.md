# EXPLORATION-A3 — Squeeze-Dispersion Gross Throttle on the A2 Book (menu-F; family A's TERMINAL attempt; IS-only; pre-registered)

## Section 0 — Provenance, scope, and TERMINALITY

- **Frozen:** 2026-07-10, BEFORE any backtest runs. Frozen contract; QE runs the matrix ONCE; scored
  against the gates below. **No post-hoc tuning** — any change after the run invalidates the
  pre-registration.
- **Track / blinding / split:** baseline-BLIND MN (worktree `quant-portfolio-blind`); charter
  `ORCHESTRATOR_BRIEF_MN.md`, PLAN `diary-portfolio-mn/PLAN.md` (menu-F, §6 "deferred until a book
  survives" — now satisfied). **MN split SEALED** (`MN_IS_CUTOFF=2026-01-01`; every number on
  `open_time < cutoff` via `mn_slice_is`; `mn_guard_grid` asserted; old-track `is_mask`/`OOS_CUTOFF`/
  `slice_is` FORBIDDEN). No baseline artifact / sibling worktree read. **Backtests by this QR: ZERO.**
- **Predecessors (IS-only, revealed):** `EXPLORATION-A2.md`+eng (the byte-frozen book this forks;
  net Sharpe +1.6784 pinned-mask / +1.7307 fully-live; maxDD −25.57%), `PHASE7-A2.md` (FAIL — G-maxdd
  sole HARD miss; disguised-beta FALSIFIED; the ~25% draw is a genuine mechanism boundary),
  `FAMILY-A-SYNTHESIS.md` (the USER menu → option 2 authorized).
- **⛔ TERMINALITY (stated up front, binding):** this is **family A's LAST attempt. Shelve-on-fail.
  There is NO A4, no contingency, no escape hatch.** If A3 fails ANY HARD gate, family A is SHELVED,
  terminal, holdout UNSPENT — the ~25% drawdown is declared irreducible for this mechanism and the
  family is done. The Critic's scope-creep standing note binds: no re-spec, no re-gate, no "one more
  throttle." One bounded retry, and this is it.
- **Ledger:** family-A n_eff **8 → 9** with this registration (§6).

### 0.1 Design thesis (one paragraph)

EXPLORATION-A2 established that the funding-carry book is beta-honest (crash β +0.0088), G3-clean
(0.0699, no hedge leg), and a survive-intact carry edge (~+1.7 IS), but draws **~25 ± 1.5%** — a
robust mechanism boundary driven by **short-meme squeeze-tail dislocations** (2023-12 −11.2%,
2020-11 −7.9%, 2025-06 −6.1%, 2025-09 −6.4% monthly), which are IDIOSYNCRATIC cross-sectional events
orthogonal to β, so beta-neutralization structurally cannot touch them. A3 adds exactly ONE charter
menu-F primitive — a past-only **gross throttle** that de-risks the whole book when a **short-cohort
upside-dispersion (squeeze) regime** is detected — and asks the single falsifiable question: **can a
dispersion-conditional throttle clip the ~25% squeeze tail below the floor CHEAPER than it costs in
carry Sharpe, or is the ~25% drawdown irreducible for this mechanism?** The throttle deliberately
reads MARKET-STRUCTURE (short-cohort return dispersion), NOT the book's own realized drawdown and NOT
BTC drawdown — because the predecessor's **C5 falsification** showed generic market-drawdown gates
de-risk on BTC drawdowns, which is the WRONG regime: this cross-sectional book bleeds on short-meme
SQUEEZES that often occur in up/sideways BTC tape, so a BTC-DD (or self-referential equity-DD) brake
would throttle the wrong regime and miss the squeezes entirely. The indicator is targeted at the
exact regime that produces the boundary.

---

## Section 1 — Construction (FROZEN)

**The A2-1 book is BYTE-FROZEN.** Signal, universe, $3M liquidity floor, per-name cap, cross-
sectional BTC β-projection (§1.5/§1.6 of EXPLORATION-A2, incl. the ratified degenerate-guard
erratum), weekly cadence, and the 21-phase equal-weight tranche ensemble are UNCHANGED. Run through
the UNCHANGED `blind_engine.run_backtest` with the A2 `beta_neutralize` array. **Exactly ONE
addition:** a past-only gross throttle passed via the engine's EXISTING `gross_scalar_series`
parameter (a (T,) whole-book scalar consumed at [k−1] at rebal steps; **all-ones = byte-identical to
A2** — verified as a gate). No new engine extension; no other parameter moves.

### 1.1 The throttle indicator — Short-Cohort Upside-Dispersion z-score (SCUD-z), FROZEN

Past-only, computed on the IS panel with data ≤ close[t] only, consumed at [k−1]. Mechanism-faithful
to short-meme squeeze detection, market-structure (not book-equity, not BTC).

At each candle t:
1. **Short cohort** `Sₜ` = universe members[t] whose `signal_engine[t]` (= −funding-sort signal, the
   A2 book's own signal, already computed) is in the **bottom q_short = 0.33 fraction** (= highest
   funding = the names the book SHORTS — the squeeze-exposed leg). Require `|Sₜ| ≥ m_min = 5`; if
   fewer (early era / infeasible rebal), **forward-fill** the last valid indicator value (and the
   throttle is 1.0 over the pre-live warmup, where the book is flat anyway).
2. **Trailing return** per cohort name: `rᵢ = close_i[t] / close_i[t − h] − 1`, `h = 9` candles
   (3 days, the signal/persistence timescale). Past-only.
3. **Upside-dispersion** `U[t] = 75th-percentile{ rᵢ : i ∈ Sₜ }` — a robust upper-tail statistic
   (captures "the short cohort is ripping UP", robust to a single delisting/print outlier vs using
   the max).
4. **Z-score** over a trailing window `W = 90` candles (30 days), `min_periods = 45`:
   `SCUD_z[t] = (U[t] − mean_W(U)) / stdW(U)`, clipped to `[−5, +5]`. (SCUD_z is standardized by
   construction — mean ~0, std ~1 over its trailing window — which is what makes the standard-normal
   threshold calibration in §1.2 coverage-anchored without any return-scoring.)

Leak-safety: every input (close prices, `signal_engine`) is past-only; `U[t]` and its rolling
moments use only data ≤ t; consumed at [k−1]. A corrupt-future positive control is mandated (§7).

### 1.2 The throttle scalar — piecewise-linear ramp on SCUD-z, FROZEN

Thresholds are **standard-normal quantile points on the already-standardized SCUD-z** — a pure
COVERAGE calibration, NO return-scoring, NO in-sample quantile fit, live-computable (RISK-006
no-Sharpe-scan rule honored):

- **τ_lo = +0.85** (≈ standard-normal 80th percentile) — below it, no throttle (scalar = 1.0).
- **τ_hi = +1.65** (≈ standard-normal 95th percentile) — at/above it, full de-risk (scalar = φ).
- **Floor scalar φ = 0.50** — halve gross in the worst squeeze regime. Principle-anchored: halving is
  a meaningful de-risk that still keeps the carry engine ON; a full flatten (φ=0) would surrender the
  funding harvest the book exists to collect. 0.50 is a round, non-fitted choice.
- **Ramp (continuous):**
  `scalar(z) = 1.0 − (1.0 − φ) · clip( (z − τ_lo) / (τ_hi − τ_lo), 0, 1 )`.
- **Release rule: automatic and continuous** — because the scalar is a pure function of SCUD_z[k−1],
  the throttle releases as SCUD_z falls back below τ_lo (scalar → 1.0). NO separate hysteresis state
  (SCUD_z is already a smoothed z-score; adding a state machine is another DOF). Consumed at every
  rebal step [k−1]; between rebals the gross is held (engine applies the scalar only at rebal steps,
  as for all its gross mechanisms).

**Why NOT the engine's `dd_brake` or a BTC-DD gate:** the engine's `dd_brake_threshold` reads the
book's OWN realized (cost-bearing) equity — self-referential (stateful → would re-invalidate the
analytic cost twin, per the EXPLORATION-A arm-flip catalog rule) AND it de-risks AFTER the book has
already drawn down (reactive, not regime-anticipating). A BTC-DD gate throttles on market drawdowns,
which the C5 falsification showed is the WRONG regime for a short-squeeze-exposed book. SCUD-z is
market-structure, forward-of-the-drawdown, and stateless w.r.t. cost — the correct primitive.

### 1.3 Interaction with the frozen A2 book (verified, not assumed)

The throttle scales the effective target gross `g = gross · gross_scalar_series[k−1]` BEFORE the A2
weighting pipeline (rank → β-projection → rescale-to-g → cap-at-0.10·g). Because A2's book is
dollar-neutral AND beta-neutral, a throttled book is a **clean positive-scalar multiple** of the
un-throttled book that rebal: `Σ(s·w) = 0` and `Σ(s·w)·β = s·0 = 0` EXACTLY, and the cap fraction
`|w_i| ≤ 0.10·g` is scale-invariant (same names bind at the same fraction). **Therefore the
neutrality gates (G1a/G1b/G2/G3) are structurally unchanged-to-better** (de-risking shrinks realized
exposure magnitude) — but this is VERIFIED as gates (§4), not assumed.

### 1.4 Costs / cadence / ensemble — IDENTICAL to A2 (byte-frozen)

`CostModel(5.0,2.5,funding=True)`; funding on every leg; **2×-cost twin `CostModel(10.0,5.0,True)`**.
A3 is **STATELESS w.r.t. cost** (SCUD-z reads market prices/signal, not book returns; the throttle is
not path-dependent on the book's P&L), so the analytic twin is valid as a cross-check (~2.6e-4
expected) — but **ground-truth 2× re-runs remain authoritative** per the catalog rule. Weekly rebal,
21-phase equal-weight tranche ensemble, `mn_slice_is`, **293 comparability mask** (§7) — all frozen.

---

## Section 2 — Variants (FROZEN — one new run; ablation OMITTED, justified)

| Cell | Book | Purpose |
|---|---|---|
| **A3-1 (PRIMARY, only new full run)** | A2-1 byte-frozen + SCUD-z throttle | the drawdown-targeted candidate |
| A2-1 (comparator) | revealed | CITED (net +1.6784, maxDD −25.57%, G2-CRASH +0.0088, G3 0.0699, funding 6/6) — never re-run |

**Ablation OMITTED (justified):** any ablation (e.g., a symmetric all-universe dispersion indicator
instead of short-cohort-specific) requires a SECOND throttle spec = a second indicator DOF = a
scan-in-disguise on the family's TERMINAL attempt. The single frozen throttle is the cleanest
falsifiable test. The throttle's effect is instead isolated by a WITHIN-RUN forensic (throttle-active
windows: A3-1 vs cited-A2-1 per-window returns + episode alignment, §7) — a citation/attribution, not
a new run or DOF.

---

## Section 3 — Pre-registered predictions + the both-ways interpretation

Anchored to the revealed A2-1 (same 293 mask) where a ratio applies; WIDE bands on the genuine
unknown (whether the throttle FIRES during the actual squeeze episodes — the mechanism-faith bet).

| Quantity | Point | Band | Reasoning |
|---|---:|---|---|
| **maxDD (the target)** | **−20%** | **[−15%, −26%]** | throttle halves gross in the worst squeeze regime; IF it fires in the episodes, it clips ~1/3–1/2 of the incremental depth; band INCLUDES failure (−26%, throttle misses) — episode alignment is the real unknown |
| **Net ensemble Sharpe (throttle tax)** | **+1.55** | **[+1.2, +1.75]** | throttle de-risks ~15% of rebals; if those are the LOSING squeeze windows, the tax is small-to-neutral (you de-risk into losses); if some are profitable-dispersion windows, it costs carry |
| **Sharpe ratio A3 / A2** | 0.92 | [0.72, 1.04] | the throttle can even HELP Sharpe if it de-risks net-losing windows |
| **Throttle coverage (rebals with scalar < 1.0)** | ~20% | [10%, 30%] | τ_lo=+0.85 (≈80th pct); realized coverage reported (heavy tails may shift it) |
| **Full-floor coverage (scalar = φ)** | ~5% | [1%, 12%] | τ_hi=+1.65 (≈95th pct) |
| **Mean gross scalar (live rebals)** | 0.93 | [0.86, 0.97] | mostly 1.0, dips to 0.5 rarely |
| **Episode alignment (fires in ≥3 of 4 major DD episodes)** | ≥3/4 | (mechanism-faith) | if it fires in <2/4, the indicator is mis-designed → likely FALSIFIER |
| **G2-CRASH β_BTC** | +0.008 | [−0.02, +0.04] | scalar multiply preserves Σw·β=0 → unchanged-to-better |
| **G1a within-bound** | ≥97% | [95%, 99%] | unchanged-to-better (de-risk shrinks exposure) |
| **Turnover (ann one-way)** | 62× | [55×, 85×] | throttle transitions add churn over A2's 54.3×; well under 250× |
| **2×-cost net Sharpe (GT)** | +1.35 | [+1.0, +1.55] | weekly turnover; stateless twin agrees ~2.6e-4 |
| **funding-only years positive** | 6/6 | (G-durable) | scaling gross doesn't flip funding sign |

### 3.1 The both-ways interpretation (FROZEN — principle-anchored; the Critic will audit this)

Scored on A3-1 (pinned mask), with the tier still binary on the frozen gates (§5).

- **THROTTLE-WORKS (the "worth it" reading):** **maxDD ≥ −22% AND net Sharpe ≥ +1.30.**
  → the throttle clips the squeeze tail with REAL margin (≥3pp over A2's −25.57%, not a razor re-pass)
  at a bounded carry cost → the ~25% drawdown is **REDUCIBLE**; the throttle is deployable.
- **FALSIFIER (→ SHELVE, stated in advance):** **maxDD ≥ −25% (throttle MISSED the episodes) OR net
  Sharpe < +1.30 (throttle shaved too much carry).** Either → the ~25% drawdown is **IRREDUCIBLE for
  this mechanism** → family A SHELVED, terminal, holdout unspent.
- **MARGINAL (gate passes, reading weak):** maxDD ∈ (−25%, −22%] with Sharpe ≥ +1.30 — clears the
  frozen G-maxdd gate but by <3pp (a fragile re-pass, inheriting Cell-1's 0.32pp-fragility lesson).
  Pre-registered stance: I will NOT present a <3pp marginal pass as a STRONG candidate, even though
  the TIER is SUCCESS if the gate passes.

**Principle anchoring of the +1.30 Sharpe floor (audit-transparent):** the throttle is worth
deploying only if it buys the DD reduction at a BOUNDED carry cost. +1.30 = **0.77× of A2's revealed
+1.6784** — i.e., I allow the throttle to cost UP TO ~23% of Sharpe, and a throttle that shaves MORE
than 23% to clip the tail is declared not worth it (FALSIFIER). This is a DEMANDING tax ceiling
(consistent with EXPLORATION-A2's SURVIVE-INTACT ≥0.73× logic), the OPPOSITE of a pass-guaranteeing
floor set just under A2's number — a bad throttle FAILS it. Stated this way so the Critic can audit
that the floor is a tax ceiling, not an escape hatch.

**maxDD −22% anchoring:** A2 draws −25.57%; the family boundary is ~25 ± 1.5%. −22% requires the
throttle to move the drawdown ≥3pp OUT of the boundary band — a genuine clip, not window noise. The
frozen HARD gate stays −25% (§4); −22% is the stricter "worth-it" interpretation bar.

---

## Section 4 — Pre-registered GATES (FROZEN charter/PLAN set, VERBATIM — ZERO deltas from A2)

**Identical 11 HARD / 5 SOFT set and thresholds to EXPLORATION-A2 §4, including G-maxdd ≥ −25%
UNCHANGED — A3 must BEAT the same floor on UNSEEN numbers.** C5 measurement mechanics (BTC/ETH
HOLD-return regressor open→open; rolling 270/135; RETURN-candle `mn_regime_labels`; any G2/G4 bucket
n<30 → loud N/A-FAIL) and C6 funding-income sign carry over verbatim. The 293 comparability mask
carries over.

| # | Gate | Threshold | H/S |
|---|---|---|---|
| G1a | rolling-270 \|β_BTC\| ≤ 0.10 on ≥95% AND max ≤ 0.20 | | HARD |
| G1b | rolling-270 \|β_ETH\| ≤ 0.15 on ≥95% AND max ≤ 0.25 | | HARD |
| G2 | bucket-conditional \|β_BTC\| ≤ 0.15 in CRASH and MANIA each | | HARD |
| G3 | max \|Σw\|/gross ≤ 0.10 at every rebal (rebal-row, PHASE7-A2 ruling) | | HARD |
| G4 | worst-bucket net-return t > −1.0 | | HARD |
| G5 | no bucket > 60% of total P&L | | SOFT |
| G-sharpe-floor | net ensemble Sharpe ≥ +0.35 | | HARD |
| G-sharpe-target | ≥ +0.90 | | SOFT |
| G-durable | funding-only positive in ≥5/6 IS years (uncosted `−funding_rets`; years-count only) | | HARD |
| G-2xcost | 2×-cost net Sharpe > 0 AND ≥ 0.5×(1×) | | HARD |
| G-2xcost-target | ≥ +0.60 | | SOFT |
| **G-maxdd** | **≥ −25%** (the gate A3 TARGETS; unchanged, unseen numbers) | | **HARD** |
| G-maxdd-target | ≥ −15% | | SOFT |
| G-turnover | ≤ 250×/yr | | HARD |
| G-sample | ≥200 live rebals/tranche AND ≥40 names | | HARD |
| G-contam | ex-2025-03→12 Sharpe ≥ 0.7× full-IS | | SOFT |

**Neutrality-non-degradation (verify as gates, §1.3):** the throttle is gross-scaling, so realized
β should be unchanged-to-better; G1a/G1b/G2/G3 are re-measured on A3's stream and must PASS (a
degradation would signal an implementation error, not a design property). G4/G5 handling per the
EXPLORATION-A2 relabel (crash t≈0 = neutrality delivered; G5 CHOP-concentration SOFT-fail expected).

---

## Section 5 — Frozen decision map (IS design-validation only; NO reveal; TERMINAL)

| Outcome | Condition | Consequence |
|---|---|---|
| **SUCCESS** | ALL 11 HARD pass (incl. G-maxdd ≥ −25% on unseen numbers) | Family A becomes **THE candidate for the (separate, USER-ONLY) holdout-reveal decision.** The §3.1 reading (THROTTLE-WORKS vs MARGINAL) is reported to qualify the candidate's strength. **NO reveal here** — the reveal is a later, USER-only call. |
| **FAIL** | ANY HARD fails (G-maxdd, or a neutrality gate degraded, or any other) | **FAMILY A SHELVED — TERMINAL. Holdout UNSPENT.** The ~25% drawdown is declared irreducible for the funding-carry mechanism. **NO contingency, NO A4, NO re-spec, NO re-gate** — zero escape hatches (the last bounded retry is spent). |

**What explicitly does NOT happen, under EITHER outcome:** no holdout spend in this phase; no maxDD
floor re-spec (rejected permanently as post-hoc); no fourth attempt; no reading of any broken-
invariant robustness number as a result. On SUCCESS the ONLY forward action is presenting family A
to the USER as a reveal candidate; on FAIL the ONLY action is shelving.

---

## Section 6 — Multiple-testing honesty (family-A n_eff ledger)

- Family-A history: **DIAG-A 3 cadence cells + EXPLORATION-A 3 construction cells + 1 researcher-DOF
  (build the engine book) + EXPLORATION-A2 1 + EXPLORATION-A3 1 = 3+3+1+1+1 = 9 DOF.**
- This registration: **8 → 9.** A3-1 is the single pre-designated primary (no best-of selection; no
  ablation; the throttle spec is frozen with NO scan — thresholds are standard-normal coverage points,
  φ a principle choice). No further inflation is possible: TERMINAL, no contingencies.
- **Critic haircut:** DSR/deflation consistent with n_eff ≈ 9 on any Sharpe; **IS-only, NO reveal →
  informational only** (sizes a future CONFIRMATION-A, does not gate the IS verdict).

---

## Section 7 — QE deliverables spec

**Script:** `analysis/portfolio/mn_exploration_a3.py`. **No verdicts — tables + mechanical pass/fail
only** (the §3.1 bin printed arithmetically, not as a verdict).

**Reuse VERBATIM:** the entire A2 stack (`mn_exploration_a2`'s book construction — signal, universe,
floor, `beta_neutralize`, cap, projection; `blind_engine.run_backtest` with `gross_scalar_series=`;
the ensemble helpers; `mn_slice_is`/`mn_guard_grid`; `mn_regime_labels`; `mn_panel_health`). **The
A2 book is byte-frozen; the ONLY new code is the SCUD-z throttle series + its wiring via
`gross_scalar_series`.**

**Throttle construction (frozen §1.1/§1.2):** build the (T,) SCUD-z series past-only, map to the
scalar ramp, pass as `gross_scalar_series` (per tranche, front-trim-aligned like every other series).
Pin the constants: `q_short=0.33, m_min=5, h=9, W=90, min_periods=45, clip=[−5,5], τ_lo=+0.85,
τ_hi=+1.65, φ=0.50`.

**Required tests (ABORT on fail):**
- **Inert control:** `gross_scalar_series = ones` reproduces the A2-1 run BYTE-IDENTICAL (proves the
  throttle is the only change).
- **Throttle leak positive control:** corrupt `close[t:, :]` (and `signal_engine[t:]`) → `SCUD_z[:t]`
  and the scalar series `[:t]` are BIT-IDENTICAL to the uncorrupted build; future changed
  (non-vacuous). Consumed at [k−1] verified.
- **Ramp correctness:** synthetic SCUD_z sweep → scalar exactly matches the piecewise-linear formula
  (1.0 below τ_lo, φ above τ_hi, linear between) to 1e-12; monotone non-increasing in z.
- **Neutrality preservation under scaling:** on one tranche, assert the throttled executed-rebal
  weights equal `s · (A2 weights)` to 1e-12 (Σw=0 and Σw·β=0 preserved), and cap fraction invariant.

**Top-of-script hard order:** `mn_panel_health()` first; `mn_slice_is` + `mn_guard_grid` + extent
assert; A2 sign pin re-asserted; NEVER old-track split; `confirmation_reveal` NEVER passed.

**Mask / warmup:** PIN the **293 comparability mask** (identical to A2 / Cell-1) across the cell and
both cost tiers (assert first-True=293). The throttle is 1.0 over the pre-live warmup (book flat).

**Ground-truth 2×** (authoritative) + analytic cross-check (report drift, expect ~2.6e-4 stateless,
never assert 1e-12). **Internal reproducibility:** bit-identical re-run; leg reconciliation ≤1e-12;
IS-guard per tranche; ensemble leg recon.

**Throttle forensics (C1–C4-class — the mechanism-faith audit):**
- **Coverage:** fraction of live rebals with scalar < 1.0 and scalar = φ; mean/min scalar; SCUD-z
  distribution (realized quantiles at τ_lo/τ_hi — did the standard-normal points give ~20%/~5%?).
- **EPISODE ALIGNMENT (the load-bearing forensic):** for each of the 4 revealed major DD episodes
  (2023-12, 2020-11, 2025-06, 2025-09 — dates REVEALED, used ONLY to locate episodes, never to score
  throttle variants), report whether the throttle fired (scalar < 1.0) DURING the episode and the
  mean scalar over the episode window. **Did it fire IN the drawdowns?** — the direct test of whether
  SCUD-z targets the right regime.
- **Throttle-effect attribution:** A3-1 vs cited-A2-1 returns on the throttle-active windows (how much
  loss was averted vs how much carry was foregone) — the "cheaper than it costs?" decomposition.
- **maxDD path:** the A3-1 drawdown path vs A2-1's, annotated with throttle-active spans.

**Required tables:** the full A2 table set (headline; neutrality panel with C5 mechanics + the C3
β-decomposition; G3 forensics; per-year total+funding; monthly + worst-10; contamination twin; phase
dispersion) recomputed for A3-1 — **PLUS** the throttle forensics above and the **A3-1-vs-A2-1
comparison block** (net Sharpe + ratio, maxDD + delta, G2-CRASH β, G3, turnover, funding-years, with
the §3.1 THROTTLE-WORKS / MARGINAL / FALSIFIER bin printed MECHANICALLY). Gate scorecard: all 16
lines observed vs frozen threshold, verdict cells BLANK.

**Do NOT:** touch the holdout / pass `confirmation_reveal`; read any baseline/sibling artifact; use
the old-track split; change ANY byte-frozen A2 parameter; scan or add a second throttle spec; select
or weight any phase unequally; re-run/re-tune after seeing results. Hand the report to the QR for
Phase-7. **There is no holdout reveal in this phase, and this is family A's terminal attempt.**

---

**FROZEN.** The byte-frozen A2 book + the single SCUD-z throttle (indicator, thresholds, floor,
release — §1.1/§1.2), the variant (§2, one run, no ablation), predictions + both-ways thresholds
(§3), the gate set (§4, zero deltas), the terminal decision map (§5), and the n_eff ledger (§6) are
locked as of 2026-07-10, pre-run. **Shelve-on-fail; no A4.** Any deviation is a process violation.

*— QR, MN track, 2026-07-10.*
