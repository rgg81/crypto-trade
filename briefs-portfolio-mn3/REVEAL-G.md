# REVEAL-G — FROZEN holdout-reveal pre-registration for the family-G slow-c1 continuous book (MN3; Stage-2; single-use MN3-G)

**Track:** MN3 (two-year sealed holdout, market-neutral). **Date:** 2026-07-11. **Author role:**
Quant Researcher (Stage-2 reveal pre-registration). **IS window:** 2020-01-01 → 2024-06-30
(`MN3_IS_CUTOFF_MS = 1719792000000`). **HOLDOUT window (the reveal target):** `[2024-07-01 00:00 UTC,
2026-07-01 00:00 UTC)` — 2 years, SEALED, `mn3_split.mn3_guard`-enforced, **never evaluated for this
construction** (REVEAL-LEDGER zero spends; `MN3-G` UNSPENT as of this document).

**Status: FROZEN interpretation map, complete BEFORE any holdout number is computed or seen.** Once
this document goes to the Critic pre-flight and (only on PASS) is executed, no read, threshold, tier,
anchor, or construction detail below may change. The tier the holdout numbers land in IS the outcome.
Nothing in this document is computed on holdout data; every number cited is IS-only or a
principle/precedent anchor. Nothing is committed to git by this authoring step.

> **MODEL-NOTE (charter deviation, disclosed).** The MN3 charter mandates ALL AGENTS ON FABLE. The
> Fable mandate is **user-suspended for this phase** (Fable-5 rate limit; user direction: "continue on
> Opus"). This map was authored on **Opus 4.8, not Fable** — the same posture as DIAG-G / EXPLORATION-G
> / EXPLORATION-S4 / the Critic pre-flight. Pre-registration integrity is unaffected: everything is
> frozen in this document BEFORE the reveal fires; the holdout is sealed; `MN3-G` is unspent (verified
> against `REVEAL-LEDGER.md`, zero SPENT lines). Adversarial burden unchanged.

**Anchors read (IS + governance only — NO holdout):** `diary-portfolio-mn3/EXPLORATION-G-engineering.md`
(the scored IS run — the construction to freeze + its scorecard + the §5.1 finding), `briefs-portfolio-mn3/EXPLORATION-G.md` + `AMENDMENT-001` (frozen construction spec + gates + Critic conditions),
`diary-portfolio-mn3/REVIEW-G-preflight.md` (Critic ratifications), `ORCHESTRATOR_BRIEF_MN3.md`
(lifecycle + contamination map), `diary-portfolio-mn3/PLAN.md` §5.1/§6/§6.1 + AMENDMENT-002 §C +
AMENDMENT-005, `REVEAL-LEDGER.md` (zero spends — this authors the FIRST), the v2 precedent
`briefs-portfolio-mn/CONFIRMATION-A.md` + `diary-portfolio-mn/PHASE7-CONFIRMATION-A.md` (the reveal-map
+ single-use-token + audit-banner pattern reused verbatim), `analysis/portfolio/mn3_split.py` (the
guard/token mechanism), `analysis/portfolio/mn3_exploration_g.py` + `mn3_g_oof_slow.py` (the byte-frozen
construction the reveal re-runs on the holdout).

---

## Section 0 — GOVERNANCE OVERRIDE: this reveal spends MN3-G on a construction whose IS mechanical TIER was FAIL. Read this first; the Critic must adjudicate it.

**The central fact, stated without softening.** EXPLORATION-G's mechanical decision map returned
**FAIL** (`EXPLORATION-G-engineering.md` §9). Two things fired:

1. **§5.1 mechanism-provenance falsifier (the discriminating one).** The registered mechanism — "the
   horizon-matched SLOW LABEL suppresses turnover, cutting cost" — was falsified. The slow label did NOT
   slow the book (turnover ratio slow/fast = 0.951, not `< 0.5`), and 97% of its net win over the fast
   label is **higher GROSS (a better signal: IC +0.0369→+0.0502, gross +12.1%→+20.5%)**, not lower cost
   (only +0.25% of the +8.66% Δnet). The true turnover cure was the **continuous IC-proportional
   weighting** (quintile→`rank_neutral`), which the brief had bundled with the label.
2. **G-durable ECON-HARD** (H1 net −0.35 bps): a thin 3-month Q1-2022 OOF-start artifact (the OOF span
   begins 2022-01), per the diary an structural OOF-start effect — but a FAIL by the frozen gate.

Under EXPLORATION-G's frozen map + PLAN §6.2 ("failing any stage terminates the family — no rescue")
+ AMENDMENT-005 ("the LAST revision round; a further failure closes G"), **family G is closed and the
default disposition is that `MN3-G` is never spent.** This reveal OVERRIDES that default. The override
is a USER decision, exercised through the orchestrator, exactly as the v2 CONFIRMATION-A precedent
established (there the USER spent family A's one-forever token over the QR/Critic HOLD recommendation).
Here the override is STRONGER — A3-1 had PASSED its IS map (SUCCESS-MARGINAL, 11/11 HARD); G FAILED
its IS map. I record that asymmetry plainly.

**The honest case FOR the override (why the FAIL does not disqualify the reveal):** the §5.1 FAIL is a
**mechanism-PROVENANCE** failure, not an **economics / neutrality / all-weather** failure. On the
as-shipped book, **13/14 HARD gates pass**: it is a genuinely dollar-and-beta-neutral (G1a/G1b/G2/G3
all pass, rolling |β_BTC| max 0.0705), all-weather (G4 worst-bucket t −0.56 > −1.0), crash-robust
(CRASH net +6.56 bps/cd t +2.61; fresh CRASH quintile-spread t +11.03), honest-2×-cost-surviving
(net-2× Sharpe +0.70, turnover 62×) market-neutral book — the strongest, most crash-robust signal the
MN/MN3 effort has measured, now executed at a cost that clears the 2× wall DIAG-G's quintile book
blew (−5.3%/yr). §5.2 (GROSS placebo, two-sided CI ∋ 0, real−placebo +1.45) and §5.3 (direction, +1.07
vs reversed −1.74) both PASSED — the edge is the signal, correctly signed, not plumbing. What FAILED
is the *story about WHY the trade is cheap*, not the trade.

**The honest case AGAINST the override (the Critic must weigh this):** (a) an IS falsifier is supposed
to be BINDING; spending the terminal token on a construction that fired its own frozen §5.1 risks
setting the precedent that falsifiers are advisory. (b) The book being revealed embeds the slow
label's un-registered **signal improvement** (the thing §5.1 flagged as "smuggled better alpha"); a
purist would reveal the *fast-c1 continuous* book instead (§2), which isolates the ratified DIAG-G
signal + the proven weighting fix with NO new label DOF. (c) The IS `+0.70 / −21.6% / t+11` were all
SEEN during the mechanism falsification — the IS is design-contaminated (§6), so none of it is
independent evidence; the reveal rests entirely on GENERALIZATION.

**The reveal's honestly re-framed hypothesis (NOT the falsified one).** The reveal does **not** test
the falsified turnover-suppression mechanism. It tests: *does the composite slow-c1 continuous book —
a neutral, crash-robust, cost-surviving MN book on IS — GENERALIZE to the pristine 2-year holdout?*
Neutrality transfers or it does not (highest power); crash-robustness holds in the crash-heavy holdout
or it does not (high power, on trial); drawdown stays controlled or it does not; the net-2× economics
clear a modest deployment floor or they do not (lowest power). The turnover cure (continuous weighting)
and the label's role (horizon-matched signal) are UNDERSTOOD; what is UNKNOWN is generalization.

**Critic action item #1 (load-bearing).** The Critic pre-flight MUST rule on the override itself —
whether spending `MN3-G` on a §5.1-FAIL construction is legitimate given the mechanism-provenance vs
economics distinction. A ruling that IS-falsifiers must bind and the token must not be spent is a
valid BLOCK; the reveal does not fire without the Critic clearing this section. Everything below is
authored so that IF the override is cleared, the reveal is mechanical and mining-proof.

---

## Section 0.5 — Contamination & regime-composition disclosure (family-G §1.3 row VERBATIM + the reveal-specific leak)

**Family-G row (PLAN §1.3), verbatim:** *"G ML residual alpha — univariate ICs of constituent feature
classes (funding/taker/OI/resid-mom) were measured here as MN-v2 IS (DIAG-A/C/D/E1) [W1–W2]; same +
vol_low book P&L revealed (different, closed mechanism) [W2]; never evaluated [holdout].
Sealed-as-achievable. Feature-class univariate-IC knowledge over W1–W2 is in-head and shaped the §3.1
feature list; disclosed. No G book has ever touched any of it."*

**The two contaminations that matter for THIS reveal, named:**

1. **IS is DESIGN-CONTAMINATED.** The IS scorecard (`net-2× Sharpe +0.70, maxDD −21.56%, IC +0.0502,
   CRASH quintile-spread t +11.03, rolling |β| maxes, turnover 62×`) was seen *while falsifying
   EXPLORATION-G's mechanism*. It is the design surface, not independent evidence. **No IS number is
   re-used as a pass criterion.** Every threshold in §5 is anchored on a principle, a charter/v2
   precedent value, or a zero/sign floor — never on an IS draw. The consequence: this reveal can only
   ever validate GENERALIZATION; it cannot "re-confirm" the IS.

2. **Holdout is PRISTINE for this construction, but its REGIME COMPOSITION leaks.** No G book has ever
   touched the holdout (LEDGER zero spends). But I hold disclosed in-head knowledge that the holdout is
   **crash-heavy and mania-free** (ORCHESTRATOR_BRIEF §CONTAMINATION MAP: "2025-11→2026-07 crash-heavy;
   2026-H1 mania-free"), and additionally I know from the *separate* family-A CONFIRMATION-A reveal that
   the 2026-01→2026-07 slice was CRASH 28.5% / MANIA 0.0% — that window overlaps ~6 months of the MN3
   holdout. This is MARKET-regime knowledge (shared across families), not G-book knowledge.

**Why this leak is DANGEROUS here, stated plainly.** G is crash-ROBUST and I know the holdout is
crash-heavy — a naive reader can suspect I am steering a crash-hardened book at a target I know is
crash-heavy, and worse, that a strong holdout Sharpe would be *partly the favorable-regime tailwind I
knew about in advance*. Based on IS regime P&L, the holdout composition is **favorable** to G: CRASH is
G's best regime (+6.56 bps/cd, 64.6% of IS P&L) and MANIA is G's ONLY losing regime (−1.83 bps/cd) —
crash-heavy + mania-free over-samples G's earner and removes its loser. I confront this, not hide it.

**The five pre-committed defenses (the leak is neutralized, and in one respect made MORE probative):**
1. **Market-only regime bucketing** — `mn3_regimes` frozen buckets (trailing-90c BTC return; CRASH
   ≤ −15%, MANIA ≥ +25%, else CHOP), computed from BTC price alone, never from G's P&L.
2. **This pre-committed map** — frozen before any holdout number exists; the interpretation under every
   composition (including crash-heavy) is written below (§5, §9) and cannot be reshaped post-hoc.
3. **Every threshold is principle/precedent-anchored, demonstrably NOT fitted** to G's revealed IS
   numbers — each carries a one-sentence non-fitted proof in §5.
4. **The crash gate is SIGN-only** (CRASH net > 0 AND quintile-spread t > 0), never fitted to the IS
   `t +11.03`. And — the load-bearing inversion — **a crash-heavy holdout is exactly where a SPURIOUS
   crash-robustness claim would break**, so making C a high-power FAIL trigger turns the favorable leak
   into a *harder, fairer* test, not an easier one: if G's crash edge were an IS artifact, the crash-
   heavy holdout is precisely the window that exposes it.
5. **Single-use token audit banner** (§7) — the reveal fires exactly once; the ledger + banner are the
   permanent record.

**Killed-at-mechanism families stay closed** (vol_low, pairs-persistence, taker-standalone,
resid-mom-standalone, OI-fade); the S3-C4 `rvratio_xz`/`rv_ownpctl` disposition is unchanged
(the feature set is untouched vs EXPLORATION-G). The R1 `mkt_fund_agg` level-z definition stays
locked-immutable.

---

## Section 1 — The byte-frozen construction (pinned by module + content hash; the reveal re-runs THIS, unchanged)

The reveal scores the **exact object EXPLORATION-G scored** — the as-shipped (THROTTLED, disposition
NEUTRAL) slow-c1 continuous-IC-weighted book — with **zero parameter, script, or default change**. It
is pinned two ways so the execution cannot silently differ: (a) by module path + SHA-256 content hash
(the analysis tree is gitignored; hashes are the freeze), and (b) by the explicit spec table below.

**Content-hash pins (SHA-256, recorded 2026-07-11 at authoring; the reveal MUST assert these before
running):**

| Artifact | Path | SHA-256 |
|---|---|---|
| Scored construction | `analysis/portfolio/mn3_exploration_g.py` | `5baa80436fb7b4d185b5e3e6f3b8acef4235df3d1deb7b2c06880a454638ca76` |
| Slow-label OOF retrain | `analysis/portfolio/mn3_g_oof_slow.py` | `adffffad11e6470055420e9e9cff21cea8f4a967f9bcd2b43a657af5ca7d2ad4` |
| Split/guard/token module | `analysis/portfolio/mn3_split.py` | `1b37170d542e866d7c2369f0ba44b9b504e29d7cd6ddd992d7078fea12596d25` |
| IS-only slow OOF parquet (IS-parity reference) | `data/mn3_g_slow/oof_predictions.parquet` | `749e21402b7e25b23368935e0a258b0caa040c536864501448ddbb5c9bbec4c4` |

Any hash mismatch ⇒ the construction changed ⇒ **ABORT before the token is spent.** The engine core
(`blind_engine.run_backtest`) is unchanged (leak-proven, 105-test suite); no engine edit is part of
this reveal.

**Spec (frozen; every value inherited from EXPLORATION-G §1–§2, cross-checked against the module):**

| Element | Frozen value |
|---|---|
| **Signal** | config **c1** (num_leaves=15, min_data_in_leaf=200, lambda_l2=10), **seed-ensemble mean** over seeds {42,123,456,789,1001}, from the slow-label OOF parquet (§8 re-run over the holdout) |
| **Label (of the signal)** | forward **21-candle** residual TOTAL return (price+funding), winsor **±0.53** (=0.20·√(21/3)), **purge 21** at every train/OOF boundary; monthly walk-forward retrain, trailing **24-month** window (house sacred constant) |
| **Weighting** | `weighting="rank_neutral"` — continuous cross-sectional rank of the c1-slow prediction over live members, demeaned (dollar-neutral), normalized to Σ\|w\|=gross. **gross = 1.0** |
| **Beta projection** | BTC-only minimal-L2 (`apply_beta_neutralization`); rolling BTC β `rolling_beta` (ref=BTCUSDT, window 270, min_periods 135, shrink λ=0.33, clip[0,3]); consumed at **[k−1]**; degenerate-β + collapse guards frozen |
| **Per-name cap** | \|w_i\| ≤ **0.10**·gross, iterative same-leg pro-rata |
| **min_members** | **20** (skip a rebal with < 20 finite-signal members) |
| **Universe** | `mn3_diag_j.build_universe`, PIT **top-40** by trailing-30c mean quote-$-vol, ex-stablecoins, ≥270c history (the DIAG-G universe the OOF was generated on) |
| **Cadence** | weekly **rebal = 21**; full **21-phase** equal-weight tranche ensemble; **phase-agnostic mean is the ONLY headline** (single-phase numbers never load-bearing) |
| **Costs 1×** | `CostModel(taker_fee_bps=5.0, slippage_bps=2.5, funding_enable=True)` — 7.5 bps/side on Σ\|dw\| + funding every leg |
| **Costs 2× (GT twin)** | `CostModel(10.0, 5.0, funding_enable=True)` — **full engine re-run** (ground-truth, not analytic; throttle/projection make the book non-stateless). **This is the honest primary cost object** (G is a full-cross-section liquid top-40 book) |
| **Layer-2 throttle** | **G-LCDD-z**, `build_lcdd_throttle_g`: cohort = live members in the **top q=0.33** of the c1-slow prediction (m_min=5), trailing return h=9, downside-dispersion D=−P25, z over W=90 (min_periods 45, clip ±5), ramp `scud_ramp` (τ_lo=0.85, τ_hi=1.65, φ=0.50, VERBATIM from `mn_scud`); consumed [k−1]. **Disposition NEUTRAL on IS ⇒ as-shipped book = THROTTLED** — this frozen IS disposition is NOT re-decided on the holdout |

**As-shipped book = THROTTLED.** EXPLORATION-G's §2.2 partition returned NEUTRAL (Δmaxdd +0.99pp,
s=0.967 ≥ 0.90), which ships throttled. The reveal scores the throttled book. It does **not** re-run
the HURTS/NEUTRAL/HELPS disposition on holdout data (that would be re-selecting the scored object on
the holdout — banned mining). The throttled book is the single frozen scored object.

---

## Section 2 — A-priori justification for revealing SLOW-c1 (not fast-c1): the horizon-match principle, and why this is NOT a selection on the IS +0.70

I saw **both** IS scorecards during EXPLORATION-G's §5.1 comparison: slow-c1 continuous (net-2× Sharpe
+0.70) and fast-c1 continuous (Sharpe(1×) +0.507, net-2× ≈ +0.15–0.19 implied from gross +12.11% −
2×5.13%). Choosing to reveal slow-c1 is therefore choosing the higher-IS-Sharpe of two known books —
the exact shape of a selection-mining move. The choice must rest on an **a-priori principle that would
pick slow-c1 EVEN IF its IS Sharpe were the lower of the two.** It does:

**The horizon-match principle (Grinold–Kahn), stated as the a-priori-correct label for a weekly-hold
book.** The IC that PAYS is the IC measured over the *holding period*. This book HOLDS 21 candles
(weekly). The a-priori-correct forecast target is therefore the **21-candle forward return** — the
slow-c1 label. The fast-c1 label (3-candle forecast, 21-candle hold) is a horizon MISMATCH: it
forecasts a 24h return but harvests a weekly one; by day 2–3 of the hold the forecast that put the
position on is stale. **This is a property of the book's hold horizon, decided before any backtest —
it does not reference G's IS economics.** If fast-c1 had shown the *higher* IS Sharpe, the horizon-
match principle would STILL select slow-c1, because a weekly book should forecast weekly returns. That
counterfactual is the non-fitted anchor: the selection is horizon-driven, not Sharpe-driven.

**Confronting the §5.1 falsification head-on (why the principle survives it).** The §0.5 argument in
EXPLORATION-G had two legs: (1) the slow label suppresses TURNOVER (cost); (2) the slow label makes the
alpha PERSIST over the hold because forecast horizon = holding period. §5.1 **falsified leg (1)** — the
turnover cure was the continuous weighting, not the label. But §5.1 **CONFIRMED leg (2)** — the
horizon-matched label produced a *better holding-period IC* (+0.0369→+0.0502) and a persistent-over-the-
hold alpha (gross +12.1%→+20.5%), exactly as "the position is put on to harvest the very return it is
held to collect" predicted. Leg (2) IS the Grinold–Kahn core (holding-period IC is what pays); leg (1)
was a turnover *corollary* that the continuous weighting pre-empted. **The core survived; the corollary
died.** The core is what makes slow-c1 a-priori-correct for a weekly book. I am NOT rationalizing the
+0.70; I am using the principle whose central prediction the data confirmed, and I disclose that its
turnover corollary was falsified.

**The honest alternative I considered and rejected (disclosed per the task).** The *fast-c1 continuous*
book is the cleaner mechanism-isolation: it takes the byte-frozen, DIAG-G-ratified signal (IC +0.037,
CRASH t +3.21, all-year/all-seed positive — Critic-ratified, never re-fit) and applies ONLY the proven
continuous-weighting fix, with NO new label DOF. It has a strong purist claim (§0's case-against). I
reject it as the reveal target for two reasons, both a-priori: (i) **horizon-match** — fast-c1 is the
horizon-mismatched book; revealing it would reveal the a-priori-WRONG label for a weekly hold; (ii)
**it was never fully scored** — EXPLORATION-G scored fast-c1 only in the §5.1 control (gross/turnover/
net), never its full 14-HARD neutrality/crash-preserve/durable/maxDD panel; revealing it would require
a fresh IS scoring run (more ledger, re-opening the IS), whereas slow-c1 is the completely-scored
13/14-HARD object. **If the Critic judges the horizon-match anchor insufficient to clear the selection-
mining concern, the correct fallback is to BLOCK this reveal and register a fresh fast-c1 pre-flight —
NOT to silently swap targets here.** I make the slow-c1 case honestly and stand on it; I do not pretend
the choice is costless.

---

## Section 3 — Sample-power framing (governs the weighting of every read)

The holdout is **2 years ≈ 730 days ≈ ~2190 8h candles ≈ ~104 weekly rebals/phase.** This is ~4×
CONFIRMATION-A's 6-month window, and the power difference drives the map's read-weighting:

- **SE(annualized Sharpe) ≈ √(1/2.0) ≈ 0.71.** A holdout Sharpe of +0.70 carries a 95% CI of roughly
  [−0.7, +2.1] — the sign is *reasonably* determined (far better than CONFIRMATION-A's ±1.39), but the
  Sharpe point estimate is still the **lowest-power** number the reveal produces.
- **SE(β) ≈ 0.01–0.02** over ~2190 candles — **neutrality is the HIGHEST-power test.** A predecessor-
  class break (β→0.3–0.5) fails the §5 bound by ~15–30σ; a transferred projection lands near zero.
- **Crash-preservation is HIGH power in THIS window** because the holdout over-samples CRASH — there are
  many crash candles to estimate the CRASH-bucket mean and the fresh crash quintile-spread on. This is
  the read the leak makes *more* probative (§0.5 defense 4).

The tiers (§5) therefore weight **neutrality + crash-preservation + drawdown OVER the noisy Sharpe**,
by design and on the record — exactly the CONFIRMATION-A weighting, and the correct one for a small
(even 2-year) confirmation. A weak Sharpe cannot FAIL the book alone (§5); a broken neutrality or a
broken crash edge can.

---

## Section 4 — Pre-registered expectations (priors stated before the reveal; NOT the §5 tiers)

These are what I expect, with adversity documented, so hindsight cannot reshape them. They are NOT
thresholds.

- **Window composition (context for every number).** I expect the holdout to read **crash-heavy,
  mania-light-to-absent** (disclosed §0.5). For G this is a **favorable** composition (over-samples its
  earner, removes its loser) — the opposite of A3-1's adverse mania-free window. **This raises, not
  lowers, the interpretive bar:** a weak edge here cannot be excused by "the earning regime was absent."
- **Neutrality:** expected to HOLD near zero (the projection + scale-invariant throttle transfer or they
  do not; IS full-window β_BTC +0.0047, β_ETH +0.0039). A break to \|β\| ≫ 0.15 is the single most
  important negative the reveal could produce.
- **Crash-preservation:** expected to HOLD (CRASH net > 0, quintile-spread t > 0) — the crowding-
  syndrome crash edge is mechanism-predicted (features flag the squeeze side hardest when liquidity is
  scarcest), measured IS-only, and the crash-heavy window gives it high power. A CRASH-bucket net ≤ 0
  in a crash-heavy holdout would be a genuine falsification of the all-weather claim.
- **maxDD:** expected controlled — crash-robust + low-turnover + mania-free ⇒ plausibly shallower than a
  mania-heavy window; I do NOT expect the adverse-window deepening A3-1 saw. A mid-20s%–30s% draw would
  not surprise; > −33% would.
- **net-2× Sharpe:** genuinely uncertain (SE 0.71). Given the favorable composition I lean positive but
  hold no strong prior on the magnitude; I will not be surprised by anything in [−0.5, +1.5].
- **Throttle:** expected to fire in some 2024–2026 dumps, return-neutral-to-mildly-helpful (IS NEUTRAL);
  it is not the alpha (a scalar ∈ [0.50,1.0] cannot manufacture positive alpha).

---

## Section 5 — THE FROZEN DECISION MAP (the heart; MECE; each threshold + its non-fitted anchor)

Four reads, on the holdout slice `[2024-07-01, 2026-07-01)`, honest cost, as-shipped (throttled) book.
Mapping vs CONFIRMATION-A: G has **no funding-carry durable core**; its durable mechanistic claim is
**crash-robustness**, so read **C** (crash-preservation) takes the high-power "durable mechanism" role
that F (funding leg) held for A3-1 — and the crash-heavy holdout gives C real power. Every threshold is
a charter/v2-precedent value or a zero/sign floor; **none is set near an IS draw.**

### The four reads and their thresholds

**N — Neutrality (highest power).** `N HOLDS` iff full-window OLS **\|β_BTC\| ≤ 0.15 AND \|β_ETH\| ≤
0.20 AND (crash-bucket \|β_BTC\| ≤ 0.25** when the CRASH bucket has ≥30 holdout candles; WAIVED-and-
reported if <30). Else `N BROKEN`.
- *Non-fitted anchor:* **CONFIRMATION-A §4 VERBATIM** — the MN-track transfer standard, set for A3-1
  *before* A3-1's holdout existed. It is ~10× G's IS rolling-β max (0.0705) and ~30× G's IS full-window
  β (0.0047); with SE(β)≈0.015 it is an ~8–15σ break-detector, not a "just above IS" nudge. It is a
  TRANSFER bound (generous vs the IS 0.10 rolling gate, because the short window has a noisier
  estimator), NOT the IS gate lowered/raised to fit G. Rolling-270 β and per-bucket β are REPORTED as
  context; the binary read is full-window + crash-bucket.

**C — Crash-preservation (load-bearing; HIGH power in this crash-heavy window).** `C HOLDS` iff **(i)
CRASH-bucket mean net return > 0 AND (ii) fresh CRASH quintile-spread of the c1-slow prediction t > 0**
(right-signed). Else `C BROKEN`.
- *Non-fitted anchor:* **SIGN floor**, EXPLORATION-G's G-crash-preserve verbatim, Critic-ratified
  (REVIEW-G-preflight §2) as "CORRECT not lax" — a 21c-forward label has heavy label-overlap that
  deflates the achievable t even for an identical edge, so a t-magnitude bar would risk a FALSE FAIL.
  It is NOT the IS `t +11.03` nor the CRASH net `+6.56 bps` — only their SIGNS. Load-bearing because a
  crash-heavy holdout is precisely where a spurious crash-robustness claim breaks (§0.5 defense 4), so
  `C BROKEN` is a FAIL trigger.

**D — Drawdown (risk).** holdout maxDD (as-shipped, gross=1.0). **Controlled ≥ −33%; elevated ∈
(−45%, −33%); catastrophic < −45%.**
- *Non-fitted anchor:* **CONFIRMATION-A §4 VERBATIM.** −33% (controlled) is **+11.4pp WIDER** than G's
  IS maxDD (−21.56%) — deliberately loosened to allow the adverse regime, NOT tightened to fit the IS.
  −45% (catastrophic) ≈ 2× the IS depth, a "blew a risk hole" bound independent of G's number.

**S — Edge (lowest power; the honest primary cost object = net-2× Sharpe).** **positive-edge ≥ +0.30;
weak ∈ [−1.0, +0.30); clear-negative < −1.0.** (net-1× Sharpe reported as a higher context read.)
- *Non-fitted anchor:* **CONFIRMATION-A §4 edge tiers VERBATIM.** +0.30 is the precedent economic-
  relevance DEPLOY floor — **less than half** of G's IS net-2× +0.70, so demonstrably not a "just below
  IS" gate; it is applied to the MORE-demanding net-2× object (the symmetric GT twin, §3.1), which is
  the conservative choice. The −1.0 FAIL-by-edge is a materially-money-losing-window bound. *(Cross-
  check only, NOT the derivation: +0.30 also happens to be ≈ G's +0.70 shaded by a v2-precedent-
  magnitude IS→OOS haircut [A3-1: +1.73→~+0.75 central, ~57%]; I note the coincidence but the floor is
  the verbatim precedent value, computed with zero reference to +0.70.)*

**Reported-not-gated context (per CONFIRMATION-A pattern; never a FAIL trigger):** window regime
composition (FIRST, before any performance number); turnover vs the 104×/yr geometric ceiling (52
weekly rebals × 2.0 full-flip — pure geometry, a mechanical-anomaly sanity bound, NOT fitted; a breach
is flagged in interpretation, not an independent FAIL because net-2× already charges turnover cost);
per-year (2024-H2 / 2025 / 2026-H1) and per-half net; net-1× Sharpe, ann vol, ann return; throttle
coverage + fire-timing (LEAD/COINCIDENT/LAG on the holdout's worst months); G3 dollar-neutrality;
worst-bucket t; per-name concentration; 21-phase Sharpe distribution + positive count.

### The frozen tiers (MECE; evaluated in this order; FAIL triggers dominate)

| TIER | Condition (mechanical, exhaustive) | Meaning |
|---|---|---|
| **FAIL** | **N BROKEN**, OR **C BROKEN**, OR **D catastrophic** (maxDD < −45%), OR **S clear-negative** (net-2× Sharpe < −1.0) — ANY ONE | The book did NOT generalize: neutrality broke (the projection didn't transfer), OR the crash-robust all-weather claim broke in the very regime the holdout over-samples, OR it blew a risk hole, OR it lost money materially in a *favorable* window. **Family G is CLOSED FOREVER; the reveal is spent; no rescue, no second look, no re-parameterization.** |
| **SUCCESS** | **N HOLDS AND C HOLDS AND D controlled (≥ −33%) AND S positive-edge (net-2× ≥ +0.30)** | Neutrality transferred (highest power), the crash-robust all-weather property held on the crash-heavy holdout (high power), drawdown controlled, and a genuinely positive net-2× edge cleared the deployment floor. An **IS-out-of-sample-generalized, neutral, crash-robust, cost-surviving MN candidate → proceed to Stage-3 (6-month forward paper-trade).** Necessary, not sufficient, for deployment (§9). |
| **PARTIAL** | **N HOLDS AND C HOLDS AND D not-catastrophic (≥ −45%) AND S ≥ −1.0**, but NOT SUCCESS (i.e. **D ∈ (−45%, −33%) OR S ∈ [−1.0, +0.30)**) | **Mechanism generalized (neutral + crash-robust confirmed OOS), edge unproven** — but note the asymmetry vs A3-1: the holdout regime was FAVORABLE to G, so a weak edge here is a WEAKER result than PARTIAL was for A3-1 (it cannot be excused by an absent earning regime). Terminal spend; no rescue. |

MECE proof: `FAIL = ¬(N ∧ C ∧ D≥−45% ∧ S≥−1.0)`; within not-FAIL (⟹ N HOLDS ∧ C HOLDS ∧ D≥−45% ∧
S≥−1.0), `SUCCESS ⟺ (D≥−33% ∧ S≥+0.30)`, `PARTIAL ⟺ ¬(D≥−33% ∧ S≥+0.30)` — exhaustive and mutually
exclusive. The throttle disposition is NOT in the tier logic (it is frozen upstream from IS as
NEUTRAL→throttled — the one as-shipped book). There is exactly one scored object and the tier is a pure
function of the four reads on it.

**The discriminating read.** As for A3-1, neutrality + mechanism (here C) + drawdown carry the verdict;
the noisy Sharpe is a positive-edge confirmation, not the driver. The SUCCESS case rests PRIMARILY on
N + C + D; +0.30 net-2× is the edge confirmation. This weighting is frozen here so it cannot be
re-weighted post-hoc.

---

## Section 6 — No-post-hoc-tuning discipline (CONFIRMATION-A §4/§5 language, binding)

The construction is byte-frozen (§1, hash-pinned); these tiers are frozen BEFORE any holdout number
exists; the reveal fires EXACTLY ONCE (§7). **The tier the numbers land in IS the outcome.** No
re-parameterization of the throttle, no re-projection, no window trim, no threshold adjustment, no "the
window was crash-heavy so let's discount the FAIL" and no "the window was favorable so let's discount
the SUCCESS." Arguing with a fired reveal's tier is a process-integrity violation, not a research move.
A FAIL is as final as a SUCCESS: the family-G line is CONCLUDED either way; the reveal is the terminal
spend of `MN3-G` (§7), and no adjustment to the construction can ever earn a second reveal (that would
be a new family, not a rescue of G).

---

## Section 7 — Token governance (single-use MN3-G; audit banner; no ensemble; terminal)

- **The reveal spends `MN3-G`** — family G's one-forever token. The slow-c1 continuous book is a
  **re-parameterization of family G** (SAME features, config, seeds, walk-forward window, universe,
  projection; only the label horizon + the continuous weighting differ from DIAG-G), so per PLAN §6.1
  anti-gaming it **shares `MN3-G` FOREVER** — it earns no new token and spends family G's entire holdout
  budget. There is exactly ONE `MN3-G` reveal, EVER.
- **Single-use audit banner (the CONFIRMATION-A pattern, reused verbatim).** The reveal executes the
  guard EXACTLY ONCE: `mn3_guard_grid(reveal_grid, reveal_token="MN3-G")` — which validates the token is
  never-spent (reads `REVEAL-LEDGER.md`), atomically appends `- SPENT token=MN3-G at=<ts>
  window=[2024-07-01…,2026-07-01…) note=family-reveal`, and prints the loud one-per-family banner. That
  banner + the ledger line ARE the permanent audit record. A second guarded call with `MN3-G` raises
  `Mn3TokenError` (already spent). After it fires, family G's holdout budget is gone forever.
- **NO ensemble.** G is the ONLY live MN3 family (H + S4 dead, I/J/K dead). This is `MN3-G` STANDALONE,
  NOT `MN3-ENSEMBLE` (which requires ≥2 member families and would consume every member's token). The
  born-ensemble/capstone path is dormant with no second survivor.
- **Stage-3 is the real arbiter (PLAN §1.1/§6.2).** Even a clean SUCCESS is followed by a pre-registered
  6-month forward paper-trade on genuinely-unseen post-2026-06-30 data (the `mn3_paper_*` recompute
  architecture) — that forward test, not this IS-gated reveal, is the deployment arbiter. The reveal
  produces a Stage-3 CANDIDATE, never a deployment.

---

## Section 8 — Execution recipe (mechanical; for the POST-pre-flight step; NOT run by this authoring task)

Executed ONLY after the Critic clears §0 (the override) and the full map. Precise enough to be
mechanical; QE reports observed values + the arithmetic tier bin ONLY; QR renders the verdict in a
later `PHASE7-REVEAL-G.md` (CONFIRMATION-A pattern — no verdict inside the QE run).

**Hard order (ABORT on any failure BEFORE the token is spent):**

1. **Hash pins.** Assert the four SHA-256 pins in §1. Any mismatch ⇒ ABORT (construction changed).
2. **Data hygiene FIRST.** `mn3_panel_health()` on the full panel through present. On `Mn3DataError`
   (corrupt BTC grid) ⇒ **ABORT — do NOT call the guard, do NOT spend the token** (fix data, re-run).
   DEGRADED (live-feed staleness) is logged and permitted. The token is spent only on a clean panel.
3. **Extend the slow-label OOF retrain over the holdout** — re-run the `mn3_g_oof_slow.py` logic
   (hash `adffffad…`) walk-forward through the holdout months on the panel sliced to
   `[2020-01-01, 2026-07-01)` (Stage-3 candles dropped; see step 5), producing c1 seed-ensemble
   predictions covering `2022-01 → 2026-06`. Output → a NEW path `data/mn3_g_slow_full/` — **do NOT
   overwrite** the frozen IS parquet `data/mn3_g_slow/` (hash `749e2140…`). Two mandatory asserts,
   both ABORT-on-fail, both BEFORE the token is spent:
   - **Purge-21 assert (MUST-1 extended to the holdout).** For EVERY walk-forward month (IS AND holdout),
     the last permitted training candle's forward-21 label window ends at index < the OOF month's first
     candle (`last_train + 21 < b_idx`); purge changed at BOTH sites (module constant + inline). Zero
     train-label / OOF overlap. (Walk-forward training windows for holdout-month predictions legitimately
     include earlier holdout data on the trailing-24-month roll — this is how the live system operates;
     the purge assert guarantees no FUTURE leak.)
   - **IS-parity assert.** The IS-portion predictions (`open < 2024-07-01`) of the full-panel retrain
     must be **BIT-IDENTICAL** to the frozen IS parquet (hash `749e2140…`). Proves the holdout extension
     did not perturb the frozen IS book. Mismatch ⇒ ABORT.
4. **THE SINGLE GUARDED REVEAL (spends `MN3-G`).** Build the byte-frozen book (§1) on the panel sliced
   to `[2020-01-01, 2026-07-01)` for warmup continuity (rolling β, LCDD-z, universe history continuously
   populated entering the holdout). Call `mn3_guard_grid(panel_grid, reveal_token="MN3-G")` **EXACTLY
   ONCE** as the first holdout-touching operation — it spends the token, prints the banner, records the
   ledger line, and authorizes all subsequent holdout compute. (The panel MUST be pre-clipped to
   `< 2026-07-01`; the guard refuses any `hi > MN3_HOLDOUT_END_MS` UNCONDITIONALLY as Stage-3, token or
   not.)
5. **Slice + score.** Slice all book streams to the holdout `MN3_IS_CUTOFF_MS ≤ grid_ms < MN3_HOLDOUT_END_MS`.
   Compute, in report order: (1) window regime composition FIRST (`mn3_regimes` CRASH/MANIA/CHOP fracs +
   candle count + dates); (2) neutrality panel (full-window OLS β_BTC/β_ETH with SE; rolling-270 β;
   bucket-conditional β_BTC CRASH/MANIA/CHOP with n, crash flagged if <30) → the **N** read printed
   mechanically; (3) crash-preservation (CRASH-bucket mean net + t; fresh CRASH quintile-spread t) → the
   **C** read; (4) headline (net-2× Sharpe [primary] + net-1× [context], ann vol, maxDD → the **D** read,
   turnover vs 104× ceiling, ann return); (5) per-year/per-half; (6) throttle coverage + fire-timing; (7)
   G3, worst-bucket t, concentration, 21-phase distribution; (8) the **S** read; (9) the **arithmetic
   tier bin** from §5.
6. **IS-parity of the scored book.** The IS-slice metrics of the full-panel build must reproduce the
   EXPLORATION-G IS scorecard EXACTLY (net-2× Sharpe +0.7035, net-1× +1.0376, maxDD −21.56%, turnover
   61.8×, pooled IC +0.0502, CRASH quintile-spread t +11.03, rolling |β_BTC| max 0.0705). Proves the
   full-panel build did not perturb the frozen book. Mismatch ⇒ the run is void (but the token, once
   spent, is spent — hence steps 1–3 gate BEFORE step 4).
7. **Leak battery (assert-enforced):** corrupt-future on LCDD-z + composed scalar (rows ≥ t corrupted ⇒
   scalar[<t] bit-identical); decision-lag [k−1]; inert-default byte-identity (throttle None ≡ ones);
   ground-truth 2× authoritative (analytic only as cross-check); leg reconciliation
   `price − tcost − funding ≡ rets` ≤ 1e-12; bit-identical full re-run.

**Do NOT:** change any frozen parameter; call the guard more than once or with any other token; trim the
holdout window; re-decide the throttle disposition on holdout data; touch Stage-3 (≥2026-07-01) data;
tune anything after seeing a number. Hand the observed values + tier bin to the QR for `PHASE7-REVEAL-G.md`.

---

## Section 9 — Pre-committed post-tier consequences (frozen; no rescue)

- **SUCCESS → Stage-3 6-month forward paper-trade.** The reveal produces a Stage-3 CANDIDATE, not a
  deployment. Stage-3 gates are registered per PLAN §6.2 at Stage-2-pass time, BEFORE the paper window
  opens: neutrality gates verbatim, a maxDD bound, the crash-preservation mechanism-attribution read,
  and an edge read honest about 6-month power (SE(Sharpe) ≈ 1.4 — high-power reads carry the verdict).
  **Load-bearing caveat, pre-committed:** a SUCCESS here was earned in a FAVORABLE (crash-heavy, mania-
  free) regime I knew about; it confirms generalization of neutrality + crash-robustness + cost-survival
  in that regime, which is **necessary but not sufficient** for all-weather deployment. Stage-3 (all-
  regime forward) remains the real arbiter; a SUCCESS may NOT be over-sold as deployment-proven, and
  NEVER via a buy-and-hold or absolute-return comparison — the frame is the risk-adjusted profile only.
- **PARTIAL → zero-budget forward paper-trade continues the evidence.** The reveal is spent either way;
  PARTIAL = "neutral + crash-robust confirmed OOS, edge unproven — and note it was unproven in a
  FAVORABLE window (a weaker result than A3-1's adverse-window PARTIAL)." The `mn3_paper_*` recompute
  architecture accumulates genuinely-unseen post-reveal data until that record — not another reveal —
  resolves the edge. Family disposition rests with the USER.
- **FAIL → family G is CLOSED FOREVER; document; archive the structural knowledge.** The
  mechanism-provenance lesson (the continuous weighting, not the horizon-match, is the cost fix; the
  slow label is a horizon-matched signal improvement) is banked regardless. No rescue of the FAILED
  construction; no second reveal; the born-ensemble path stays dormant with no survivor.

---

## Section 10 — Where I was tempted toward a fitted gate, and how I avoided it (for the Critic)

Full disclosure of every mining temptation and its non-fitted resolution:

1. **Crash-strong threshold.** Tempted to gate the CRASH quintile-spread at `t > +3` or `+5`
   (comfortably below the IS +11.03) to "prove" crash-robustness. **Avoided:** SIGN-only (t > 0), Critic-
   ratified, because the 21c label-overlap deflates achievable t and any positive-t bar referencing +11
   is fitting. The SOFT `t > +1.5` echoes robustness without fitting.
2. **Sharpe SUCCESS floor.** Tempted to set net-2× ≥ +0.5/+0.6 (just below IS +0.70). **Avoided:** the
   CONFIRMATION-A verbatim +0.30 DEPLOY floor (<half of +0.70), on the MORE-demanding net-2× object, and
   made edge non-FAIL-able alone.
3. **maxDD floor.** Tempted to set −25% (the IS G-maxdd gate ≈ IS −21.6% + buffer). **Avoided:**
   CONFIRMATION-A's −33% controlled / −45% catastrophic — WIDER than IS to allow the adverse regime,
   verbatim precedent.
4. **β bound.** Tempted to set \|β\| ≤ 0.10 (the IS G1a rolling coverage bound ≈ IS max 0.0705).
   **Avoided:** CONFIRMATION-A's ≤0.15 full-window transfer bound — a break-detector at ~10× the IS β.
5. **Turnover.** Tempted to gate ≤ 70× (just above IS 62×). **Avoided:** kept the 104× geometric ceiling
   as a reported sanity bound, NOT a FAIL trigger.
6. **The selection itself.** Tempted to justify revealing slow-c1 (net-2× +0.70) over fast-c1 (~+0.15)
   with its stronger IS numbers. **Avoided:** anchored purely on the horizon-match principle with the
   explicit counterfactual (horizon-match picks slow-c1 even if its IS Sharpe were the lower), and
   disclosed the fast-c1 alternative + the BLOCK-and-re-register fallback if the Critic finds the anchor
   insufficient (§2).

---

*— Quant Researcher (Opus 4.8, Fable-suspended phase disclosed), MN3 track, 2026-07-11. REVEAL-G
pre-registration — the FIRST-EVER MN3 sealed-holdout reveal, spending the family-G one-forever token
`MN3-G` on the byte-frozen slow-c1 continuous book. Everything frozen before the reveal; holdout sealed;
`MN3-G` unspent as of this document; nothing computed on the holdout; nothing committed to git. Next:
Critic pre-flight (which MUST adjudicate the §0 governance override), then — only on PASS — the single
guarded reveal per §8.*
