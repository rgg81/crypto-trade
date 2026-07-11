# EXPLORATION-S4 — ENGINEERING RESULTS (Amihud liquidity-provision, engine-level scored promotion)

**Track:** MN3 (two-year sealed-holdout market-neutral). **Stage:** Stage-1 IS design-validation
(2020-01-01 → 2024-06-30). **Date:** 2026-07-11. **Author role:** Quant Researcher (engineering run).
**Verdict headline:** **`TIER = FAIL`** (mechanical, C1-amended decision map). S4 does **NOT** bank.

> **MODEL-NOTE (charter deviation, disclosed).** The MN3 charter mandates ALL AGENTS ON FABLE. The
> Fable mandate is **user-suspended for this phase** (Fable-5 rate limit; user direction: "continue
> on Opus"). This run — the module `analysis/portfolio/mn3_exploration_s4.py`, its test suite, and
> this engineering write-up — was executed on **Opus 4.8**, not Fable. The adversarial standard is
> unchanged: the construction, gates, throttle, cost-stress arms, controls, and the decision map were
> FROZEN in `briefs-portfolio-mn3/EXPLORATION-S4.md` + `EXPLORATION-S4-AMENDMENT-001` (C1–C6) BEFORE
> this run; the scoring is mechanical against that frozen map; nothing was re-gated or tuned.

**Spec executed:** `EXPLORATION-S4.md` §1–§9 + `AMENDMENT-001` C1–C6 (Critic PASS-WITH-CONDITIONS,
persisted in `REVIEW-S4-preflight.md`). The amendment governs where it supersedes the body: the
decision map (C1 SUCCESS exclusivity), the throttle-disposition MECE partition (C2), the G-sample
≥8-names sub-floor (C3), the two-sided placebo null (C4), the reported ETH crash-bucket β (C5),
and the ensemble-orthogonality / CS-A sourcing flags (C6).

**Contamination disclosure (§0, reproduced):** Amihud liquidity-provision is a genuinely-new
mechanism for this dataset — never probed by the old track, MN-v2, or any MN3 family but H; S4
carries neither of family-H's two contamination flags (S1's family-A signal, S2's DIAG-C sign). The
one material in-head leak is regime-composition knowledge of the holdout (crash-heavy 2025-11→2026-06,
mania-free 2026-H1) confronted by the four §1.3 defenses — **irrelevant to this Stage-1 IS-only run,
which reveals nothing.** Holdout SEALED: `mn3_guard_grid(reveal_token=None)` fired on the IS grid;
`REVEAL-LEDGER.md` has **zero** actual `SPENT` lines; `MN3-H` **UNSPENT**. **Nothing committed to git.**

**Reproduce:** `PYTHONUNBUFFERED=1 uv run python analysis/portfolio/mn3_exploration_s4.py`
(full log at `logs/mn3_exploration_s4.log`; ~4.5 min; deterministic).

---

## 0. Parity anchors + engine promotion (the mandated 0-signal-DOF wiring)

The engine promotion is the ONE construction difference vs DIAG-H: the DIAG-H **residual-return**
sleeve (`w·(resid − fund)`, close-to-close, gross 2.0) is lifted to the real backtest engine —
open-to-open fills, **weight-level** BTC minimal-L2 projection, honest fill-price force-exit, honest
cost, the LCDD-z throttle via `gross_scalar_series`. The quintile L/S book is expressed as a
step-signal fed to the engine's `rank_neutral` builder (proven in tests to reproduce the DIAG-H
quintile equal-weight book EXACTLY). **No engine core change.**

| Anchor | Result |
|---|---|
| **ANCHOR-A (diagnostic parity)** | DIAG-H S4 `run_sleeve` reproduced EXACTLY: net-2×-cost **+16.95%/yr**, **19/21** phases positive, turnover **73.7×**, twin_ok, sleeve-gate PASS; halves **+13.9% / +19.5%**; **CRASH +54.0% / MANIA +25.8% / CHOP +7.4%**. Matches the frozen §1.1 object. |
| **ANCHOR-B (engine weight parity)** | Over **215** executed rebals, the un-throttled un-projected engine raw book's long/short sets **== DIAG-H `quintile_book_sim` membership** (each leg equal-weight, within-leg spread 0.0e+00, dollar-neutral), **minus 2 honest fill-price force-exits** — delisting names (e.g. KEEPUSDT) that keep a finite trailing CLOSE-based Amihud but have a NaN OPEN at the fill candle; the engine correctly refuses to trade what it cannot fill. The diagnostic book has no such guard. |

**The two anchors bracket the finding:** the diagnostic edge is real and faithfully reconstructed
(ANCHOR-A); the engine book is the same object honestly executed (ANCHOR-B). The gap between them
below is therefore a genuine *promotion* effect, not a wiring artifact.

---

## 1. Full scorecard — 13 HARD + 4 SOFT (as-shipped book = **throttle-OFF**, per C2 HURTS)

The §2.2/C2 disposition returned **THROTTLE-HURTS**, so the as-shipped book is the throttle-off
(un-throttled) twin; the performance gates below read on it.

| # | HARD gate | Threshold | Realized | Verdict |
|---|---|---|---|---|
| G1a | rolling-270 \|β_BTC\| ≤0.10 on ≥95% **AND** max ≤0.20 | 95% / 0.20 | **93.3%** / max 0.164 | **FAIL** (fraction sub-clause) |
| G1b | rolling-270 \|β_ETH\| ≤0.15 on ≥95% **AND** max ≤0.25 | 95% / 0.25 | 100.0% / max 0.160 | PASS |
| G2-CRASH | bucket \|β_BTC\| in CRASH ≤0.15 (n≥30) | 0.15 | **0.024** (n=637) | PASS |
| G2-MANIA | bucket \|β_BTC\| in MANIA ≤0.15 (n≥30) | 0.15 | **0.013** (n=912) | PASS |
| G3 | \|Σw\| ≤0.10·gross at every executed rebal | 0.10 | **0.0000** | PASS |
| G4 | worst-bucket mean-return t > −1.0 | −1.0 | −0.82 (CRASH) | PASS |
| G-sharpe-floor | net Sharpe (1× cost) ≥ +0.35 | +0.35 | **+0.180** | **FAIL** |
| G-2xcost | 2× Sharpe >0 AND ≥0.5×(1×) | >0 & ≥0.090 | **+0.059** | **FAIL** |
| G-coststress (CS-A) | net Sharpe **AND** ann return both >0 | >0 / >0 | **−0.001 / −2.75%** | **FAIL** |
| G-maxdd | maxDD ≥ −25% | −25% | **−33.3%** | **FAIL** |
| G-turnover | ann one-way turnover ≤ 250× | 250× | 38.2× | PASS |
| G-durable | H1 net >0 AND H2 net >0 | both >0 | +0.9 bps / **−0.1 bps** | **FAIL** |
| G-sample | ≥4.0yr, ≥200 reb/ph, ≥8 names/reb (C3), yrs 21/22/23 | — | 4.48yr, 233, 15.1, ✓ | PASS |

**HARD: 7/13 pass.** Neutrality HARD {G1a,G1b,G2-CRASH,G2-MANIA,G3,G4}: **5/6** (only G1a fails, on the
tight ≥95% rolling-fraction sub-clause; max β 0.164 is inside the 0.20 cap and every regime-bucket β
is ≤0.024). Performance HARD: 2/7.

| SOFT gate | Threshold | Realized | Verdict |
|---|---|---|---|
| G5 (no bucket >60% of P&L) | 60% | 142.7% (MANIA) | FAIL |
| G-sharpe-target | +0.90 | +0.180 | FAIL |
| G-concentration (single name ≤10% gross) | 10% | 10.0% | FAIL (at the cap; projection amplification pins a name to the 0.10 cap) |
| G-3xcost (3× Sharpe >0) | >0 | −0.132 | FAIL |

---

## 2. Throttle disposition (C2 MECE priority partition) — **THROTTLE-HURTS**

- Coverage (scored region, within SCUD anchors — no report-don't-tune mismatch): scalar<1 on **17.6%**
  (anchor ~15–25%), =φ on **7.1%** (anchor ~3–8%), mean scalar **0.943** (anchor ~0.90–0.96).
- **Δmaxdd** = (un-throttled depth 33.34%) − (throttled depth 32.33%) = **+1.02 pp** (throttle made the
  drawdown *slightly* shallower).
- **s** = Sharpe(throttled) / Sharpe(un-throttled) = 0.1222 / 0.1803 = **0.678**.
- C2 priority: **HURTS** (`s = 0.678 < 0.90`) → ship **throttle-OFF**; tier caps at MARGINAL; next-
  iteration target = "a different throttle primitive for the long-thin tail."

**The §2.2 crash-positivity tension is confirmed empirically.** The mechanism-faithful LCDD-z throttle
fires in exactly the thin-cohort dumps where S4 is designed to *earn* the illiquidity premium: it
shaves ~6 bps of Sharpe (0.180→0.122, a 32% carry cut) to buy only ~1 pp of drawdown — the honest
call for a crash-positive book. "No effective weekly-cadence Layer-2 defense found for a crash-positive
liquidity book" is carried as the open Stage-2 design question the brief pre-registered.

---

## 3. Un-throttled twin (§5.1) + cost-stress arms + CS-L

| Arm | Sharpe | ann ret | Note |
|---|---|---|---|
| Un-throttled 1× (as-shipped) | **+0.180** | +1.49% | maxDD −33.3%, turn 38.2× |
| Throttled 1× | +0.122 | +0.26% | maxDD −32.3%, turn 37.4× |
| Un-throttled 2× GT (engine re-run) | **+0.059** | — | < 0.5×(1×) → G-2xcost FAIL |
| Throttled 2× GT | −0.005 | −2.51% | |
| Throttled 3× GT | −0.132 | −5.22% | G-3xcost (SOFT) FAIL |
| **CS-A long-3×/short-1× (HARD)** | **−0.001** | **−2.75%** | as-shipped; **G-coststress FAIL** |
| CS-L $3M floor (informational) | −0.025 | — | retention vs no-floor **−0.21** (<0.50) |

- **§5.1 un-throttled twin does NOT clear the alpha floors** (Sharpe +0.180 < +0.35; 2× +0.059 fails
  G-2xcost). Crucially, this is **NOT** the "throttle-is-the-alpha" FAIL: the throttled book *also*
  fails the floor (+0.122), so the throttle is not manufacturing a covert edge — the edge simply is not
  there after honest execution. (`throttle-is-the-alpha` condition = False.)
- **CS-A (the load-bearing thin-name gate) is the cleanest kill:** modelling the thin long leg at 3×
  execution cost turns the edge net-NEGATIVE (Sharpe −0.001, ann −2.75%). The illiquidity premium does
  not survive realistic thin-name execution. CS-A was computed via a per-leg-turnover reconstruction
  from the genuine engine weight path (`long_turn+short_turn == res.turnover` exactly, unit-tested),
  **validated** against the GT symmetric-2× engine re-run to **3.08e-05** (< the ~2.6e-4 stateless
  drift) — i.e. ground-truth-faithful.
- **CS-L**: applying the $3M/8h floor (removes the thinnest names — R2, changes the object) makes it
  *worse* (Sharpe −0.025), retention −0.21 < 0.50. The (weak) edge is not concentrated in the
  executable thin half; it does not live in the removable un-executable tail either. Informational.

---

## 4. Placebo (§5.2, two-sided C4 null) — **FAIL** (reliably NEGATIVE, not a spurious positive edge)

20 pre-registered shuffle seeds (Amihud ranks permuted within each candle's live universe;
throttle-off; SAME projection + SAME cost):

- Placebo Sharpe over 20 seeds: mean **−1.090**, sd 0.411, **95% CI [−1.270, −0.910]** (min −1.886,
  max −0.417).
- **Two-sided null (C4): FAIL** — the CI excludes 0 on the **negative** side.
- **Beta-neutral: PASS** — max \|β_BTC\| over seeds = 0.004 ≤ 0.20 (neutrality is a projection
  property, holds under a null signal — the §5.2 core check passes).

**Interpretation (disclosed, not re-gated):** the C4 failure is a reliably-**negative** placebo, NOT
the spurious-**positive** plumbing edge that §5.2 primarily guards against. A random weekly-rebalanced
L/S book in this top-40 universe reliably loses ~1.1 Sharpe — the honest cost drag (~38×/yr × 7.5bps
≈ 285 bps/yr) *plus* the moonshot-short-squeeze risk of shorting random thin lottery tokens in a bull
IS window. The real Amihud signal adds **+1.27 Sharpe over the random null** (−1.09 → +0.18) — evidence
the sort *does* carry genuine cross-sectional information (and partly dodges the moonshot risk by
shorting *liquid* names) — but not enough to clear honest cost into positive-Sharpe territory.
**Methodology flag for the Critic/orchestrator:** the frozen two-sided C4 null, applied to a
*net-of-cost* Sharpe, is structurally failed by any costed random book (a zero-edge book centers at
−cost, not 0); a future C4 form may need a gross-return or edge-differential formulation for costed
books. Scored mechanically as FAIL per the frozen rule.

---

## 5. Direction control (§5.3) + leg attribution (§5.4)

- **Direction sign correct (PASS):** frozen (LONG high-Amihud) un-throttled Sharpe **+0.180** >
  reversed (LONG low-Amihud) **−0.407**. The mechanism sign is real; the frozen direction is NOT
  re-oriented (S3-C2/D10 discipline).
- **Leg attribution (throttled):** long thin leg price P&L **+1.296** (Sharpe +0.68); short liquid leg
  **−1.178** (Sharpe −0.74); funding income **+0.129**. The illiquidity-premium LONG leg carries the
  positive P&L; the SHORT-liquid leg bleeds (shorting liquid names that trend up in the 2020–24 bull),
  and honest cost + the short-leg drag net the combined book to ≈0.

---

## 6. Neutrality table

| Measure | β_BTC | β_ETH |
|---|---|---|
| Full-window OLS | +0.021 (se 0.005) | +0.014 (se 0.004) |
| Rolling-270 within level | 93.3% ≤0.10 (max 0.164) | 100.0% ≤0.15 (max 0.160) |
| CRASH bucket (n=637 / n=912) | +0.024 (se 0.007) | **+0.014** (C5) |
| MANIA bucket | +0.013 (se 0.013) | **+0.006** (C5) |
| CHOP bucket | +0.024 (se 0.007) | — |
| G3 net-exposure at executed rebals | \|Σw\|/gross = 0.0000 | — |

**R1 verdict (the brief's central unknown): the weight-level BTC projection neutralizes as well as the
diagnostic's return-level residualization on the gates that matter.** Full-window β_BTC +0.021, and
every regime-bucket β_BTC ≤ 0.024 — G2-CRASH and G2-MANIA (the "central falsifier") PASS decisively;
C5 ETH crash/mania bucket β ≤ 0.014 (no ETH crash-beta leak ahead of the crash-heavy holdout). The
ONLY neutrality miss is G1a's tight ≥95%-within-0.10 rolling-fraction sub-clause (realized 93.3%): the
book is neutral on average and in every regime, but the rolling-270 realized β wanders into
[0.10, 0.164] in ~6.7% of windows. A borderline, honest sub-clause fail — not a directional-beta edge.

---

## 7. 21-phase distribution + IS halves

- Per-phase Sharpe (throttled): min −0.329, p25 −0.135, med **+0.123**, p75 +0.276, max +0.553;
  **positive 14/21**. (Contrast DIAG-H's 19/21 on the diagnostic residual book — the engine promotion
  moves the phase distribution down and widens it.)
- IS halves net (throttled): H1 (2020-01→2022-03) +0.75 bps/cd, H2 (2022-04→2024-06) **−0.25 bps/cd**
  → **G-durable FAIL** (the engine edge is an H1-weighted artifact; the diagnostic's clean
  +13.9%/+19.5% halves do not transfer).

---

## 8. Leak battery — ALL PASS

| Check | Result |
|---|---|
| (a) corrupt-future positive control on the Amihud signal | past bit-identical; future changed |
| (b) corrupt-future on the LCDD-z throttle (u/z/scalar) | past bit-identical; future changed |
| (c) append-invariance (Amihud prefix stable when future candles absent) | PASS |
| (d) inert-default byte-identity (`gross_scalar_series` None ≡ ones) | PASS |
| (e) decision-lag [k−1] (perturb sig[t0] → engine weights[:t0+1] identical) | PASS |
| placebo (its own negative control) | reliably ≠0 → the harness resolves a null |

The LCDD-z throttle inherits the SCUD constants VERBATIM (unit-tested: Q_LONG=Q_SHORT=0.33, m_min=5,
h=9, W=90, min_periods=45, τ_lo=0.85, τ_hi=1.65, φ=0.50); the ONLY changes from SCUD are the leg
(top-0.33 Amihud thin cohort) and the tail (P25 downside), both forced by S4's LONG-thin exposure and
unit-tested for direction.

---

## 9. Mechanical TIER (C1-amended decision map) — **FAIL**

FAIL dominates on any neutrality-HARD or control failure. Here **three independent FAIL conditions**
fire:

1. **A neutrality HARD fails** — G1a (rolling β_BTC fraction 93.3% < 95%).
2. **The placebo is not null** — two-sided C4 CI [−1.27, −0.91] excludes 0.
3. (The un-throttled twin fails the alpha floors, and the disposition is THROTTLE-HURTS — either alone
   would only cap at MARGINAL, but they are moot: FAIL already dominates.)

Even setting G1a and the C4 placebo aside, the result could reach **at best MARGINAL** (every
performance floor fails: Sharpe +0.18 ≪ +0.35, maxDD −33% ≪ −25%, CS-A negative, G-2xcost fails,
G-durable fails; and THROTTLE-HURTS caps at MARGINAL). **SUCCESS was never reachable.** The verdict is
robustly, over-determinedly **FAIL**.

**S4 does NOT bank.** `MN3-H` unspent; holdout sealed; nothing committed.

---

## 10. The finding (honest, one paragraph)

The Amihud liquidity-provision edge is a **diagnostic-level artifact that does not survive honest
engine execution.** DIAG-H's +17%/yr (19/21 positive, best-in-crash +54%) was measured on
**close-to-close residual returns** over a book that includes **un-fillable delisting names** at
**gross 2.0**. Promoted to the honest engine — **open-to-open fills** (the illiquidity premium on
thin names is substantially a close-price bid-ask-bounce that evaporates at honest open fills),
**force-exit of names with no valid fill price** (removing the delisting-return artifacts the
diagnostic booked), **weight-level projection**, and **honest per-side cost** — the net edge collapses
to Sharpe **+0.18** (un-throttled) / **+0.12** (throttled), maxDD deepens to **−33%**, and it dies
under 2× cost, 3× cost, and — decisively — the **asymmetric thin-name cost (CS-A → −2.75%/yr)** that a
liquidity-provision book must actually pay. The mechanism *sign* is genuine (it beats its reverse by
0.59 Sharpe and a random null by 1.27 Sharpe, and the long thin leg does carry a positive premium),
and the weight-projection neutralizes the regime-bucket betas as well as the diagnostic residualization
(R1 holds; G2-CRASH/MANIA pass) — but the tradable, cost-surviving edge is not there. This is exactly
the kind of artifact an engine-level promotion exists to expose.

---

## 11. Path forward (for the next MN3 iteration; carried, not decided here)

1. **The liquidity-provision mechanism is a diagnostic mirage at the honest-execution boundary** —
   before any further Amihud work, a next attempt would have to change the *execution axis*: a longer
   holding horizon (dampen the bid-ask-bounce dependence), a signed premium net of a bounce estimate,
   or a liquid-only sub-universe where fills are honest — NOT a re-tune of the same book.
2. **Throttle:** the LCDD-z (down-only, thin-cohort) primitive HURTS a crash-positive book by design;
   the open Stage-2 question ("a different throttle for the long-thin tail") is now empirically
   grounded — but moot unless a book with real cost-surviving edge appears first.
3. **Methodology (C4):** the two-sided placebo null on a net-of-cost Sharpe is structurally failed by
   any costed random book; recommend a gross-return or edge-differential C4 form for future costed
   explorations (flagged, not acted on).
4. **Ensemble note (C6):** Amihud also enters family G as `amihud30_xz`; since S4 fails IS validation,
   the S4+G ensemble path is irrelevant, but the shared-input decorrelation caveat is recorded.

---

## 12. Deliverable integrity

- **Implemented:** `analysis/portfolio/mn3_exploration_s4.py` (engine promotion, LCDD-z throttle, cost
  arms, controls, scorecard, mechanical tier) + `tests/test_mn3_exploration_s4.py` (11 tests, all pass).
- **Tests:** `uv run pytest tests/test_mn3_exploration_s4.py -q` → **11 passed**.
- **Lint:** `uv run ruff check` on both touched files → **All checks passed**; `ruff format` applied.
- **Blinding invariants honored:** IS-only (2020-01-01→2024-06-30 via `mn3_split`), holdout sealed
  (`reveal_token=None`, zero ledger spends, `MN3-H` unspent), honest costs (5+2.5 bps/side + funding,
  GT 2× re-runs), no engine core change, `pyproject.toml` untouched (mn3 lowercase convention used to
  satisfy ruff), **nothing committed to git**.

*— Quant Researcher (Opus 4.8, Fable-suspended phase), MN3 track, 2026-07-11. EXPLORATION-S4
engineering run. Mechanical TIER = FAIL; honest IS finding; holdout sealed; MN3-H unspent; nothing
committed.*
