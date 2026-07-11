# DIAG-K — event-conditioned 1h liquidity-provision diagnostic (MN3, PLAN §3.5)

**Track:** MN3 (two-year sealed-holdout market-neutral). **Stage:** Stage-1 IS design-validation
(2020-01-01 → 2024-06-30). **Date:** 2026-07-11. **Author role:** Quant Researcher.
**Verdict headline:** **`DEAD (kill b + kill d)`** — mechanical, over-determined; no salvage.
K does **NOT** bank. This is the **LAST diagnostic of the MN3 field**.

> **MODEL-NOTE (charter deviation, disclosed).** The MN3 charter mandates ALL AGENTS ON FABLE.
> The Fable mandate is **user-suspended for this phase** (Fable-5 rate limit; user direction:
> "continue on Opus"). This run — `analysis/portfolio/mn3_diag_k.py`, `tests/test_mn3_diag_k.py`,
> and this write-up — executed on **Opus 4.8**, not Fable. Adversarial standard unchanged: the
> construction, event rule, book, kill criteria, sample floor, and the S4-lesson corrections were
> FROZEN in PLAN §3.5 + PLAN-AMENDMENT-004 BEFORE this run; scoring is mechanical against that
> frozen map; nothing was re-gated or tuned.

---

## 0. Pre-registration header (spec + AMENDMENT-004 reconciliation + S4-lesson + contamination)

**Spec executed (PLAN §3.5, one event rule × one book — no grids):**
- **Universe.** The 219 §5.5-verified-complete 1h symbols (`data/mn3_diag/mn3_1h_verified_complete.json`),
  restricted to the **PIT top-30** by trailing-30d (720h) mean $-volume, ≥30d history to be eligible.
  The 30d volume window **reuses** the disclosed event-definition 30d constant — no new tuning DOF.
- **Event (coverage-anchored).** At hour *h*, `xstd[h]` = cross-sectional std of trailing-4h RAW
  returns across the top-30; a market-wide dispersion event fires when `xstd[h]` exceeds its own
  **trailing-720h (30d) 95th percentile** (past-only, window `x[h−720..h−1]` via `.shift(1)`; fires
  ≈5% of hours BY CONSTRUCTION). **Re-arm:** no new event within **12h** of the last (cluster de-dup).
- **Book (mechanism-fixed, no direction DOF).** At the event close, form quintiles on trailing-4h
  **RESIDUAL** returns across the top-30; **LONG losers / SHORT winners**; enter at the **next 1h
  open**; **hold 4h**; exit. Beta-projected: residual = `r − β[h−1]·r_BTC`, β = `mn_beta.rolling_beta`
  **frozen defaults** (window 270 / min_periods 135 / shrink 0.33 / clip [0,3]) on the 1h grid
  (⇒ ~11-day β window; reuse of the proven module with ZERO new parameters).
- **The four a-priori constants** (95th pct, 30d window, 12h re-arm, 4h formation/hold) are the
  disclosed design DOF and were **NOT scanned**. Additional disclosed DOF (a-priori, not scanned):
  the 30d/≥30d universe volume window (reuses the event 30d constant), the mn_beta frozen defaults,
  and MIN_MEMBERS=20 (≥4 names/leg to form quintiles).

**AMENDMENT-004 §B reconciliation (BINDING — the crisis machine is DEAD).** Kill (c) as originally
frozen referenced machine-CRISIS candles; there is no machine-CRISIS state series and no construction
is ever forced flat. The FRAGILITY SPIRIT is preserved with a **market-only proxy**: K dies if >50% of
aggregate event P&L falls inside **CRASH-bucket candles** (`mn3_regimes` frozen rule: trailing-90c 8h
BTC ≤ −15%). GAP-candle (≥4σ/10% 8h BTC single-move, RATIFIED AMENDMENT-002 §A floor) concentration is
a **SECONDARY informational** read (non-gating). Kills (a),(b),(d) UNCHANGED; sample floor ≥150 UNCHANGED.

**S4-lesson (AMENDMENT-004 §C — BINDING).** EXPLORATION-S4 proved diagnostic residual-return scoring
OVERSTATES tradable edge (a real +17%/yr close-to-close diagnostic collapsed to −2.75%/yr under honest
engine execution). DIAG-K bakes the corrections in **at the diagnostic level**: **next-bar open-to-open
fills** (the book already enters at the next 1h open); **un-fillable names EXCLUDED** (NaN entry open)
and **delisting names FORCE-EXITED** at the last honest fill inside the hold window (no phantom
delisting return); **honest cost** 7.5 bps/side ⇒ 15 bps round-trip per 1.0 gross unit ⇒ the
dollar-neutral gross-2.0 book pays **30 bps round-trip (1×) / 60 bps (2×)**. The **2× twin is a
GROUND-TRUTH re-run** (same code path, cost doubled at source), verified equal to the analytic
`gross − 2·cost` (max|Δ| = 0.00e+00 — a stateless per-event diagnostic has no path-dependence).

**Contamination note (cautionary prior — disclosed).** Event-conditioned liquidity provision is a
**genuinely-new** mechanism for this dataset (never probed by the old track, MN-v2, or any MN3 family),
but it **rhymes with the just-failed S4 liquidity-premium mechanism**: both monetize the immediacy/
liquidity-provision premium. S4 died precisely at the **honest-execution / cost boundary**. The prior
was well-founded: DIAG-K dies at the **same boundary** — the honest 1h cost wall (30/60 bps round-trip)
dwarfs the per-event reversal edge (~12 bps gross). Holdout SEALED (`reveal_token=None`, `mn3_guard_grid`
passed on the IS 1h grid); **MN3-K UNSPENT**; **nothing committed to git**.

**Reproduce:** `PYTHONUNBUFFERED=1 uv run python analysis/portfolio/mn3_diag_k.py`
(log: `logs/mn3_diag_k.log`; deterministic).

**1h-DATA CAVEAT.** IS extent used: **2020-01-01 → 2024-06-30, T=39,432 1h candles, C=219 symbols**
(54 IS months). The DIAG-K universe is the §5.5 gate's 219 verified-complete symbols of 361 scoped
(53 gappy + 89 no-IS-overlap excluded). Mean filled top-30 slots/candle = **27.3** (early-period
thinness from the ≥30d-history + PIT-volume eligibility filters; MIN_MEMBERS=20 gate handled it — all
571 events had ≥20 members). No un-fillable/force-exit contamination survived (S4-lesson honest fills).

---

## 1. Event census

| Metric | Value |
|---|---|
| Raw-event rate (over defined-threshold hours) | **5.7%** (coverage anchor ~5% — by construction) |
| Raw event-hours | 1,893 |
| **De-duped events (12h re-arm)** | **N = 571** |
| First defined threshold | 2020-09-07 (720h xstd + 720h pct warmup) |
| IS months | 54 |
| **Per-month event rate** | **median 11.0**, mean 10.6, min 0, max 28, 8 zero-event months |
| Inter-event gap (h) | median 29, p25 16, p75 69 (re-arm floor 12) |
| Formable-book events (≥20 members, both legs fillable) | 571 / 571 |

Events cluster in stress/mania (max 28/mo) with 8 dead months, but the **median month carries 11
events** — comfortably tradable in frequency terms. Sample floor (≥150) **met** with margin.

---

## 2. Per-event honest quintile spread (S4-corrected)

| Quantity | Mean | Median | Dispersion |
|---|---|---|---|
| GROSS spread (gross-2.0 book) | **+0.1177%** (11.8 bps) | +0.0223% | sd 2.724% |
| NET (1× cost, 30 bps rt) | **−0.1823%** | −0.2777% | — |
| **NET (2× cost, 60 bps rt)** | **−0.4823%** (t = **−4.23**) | −0.5777% | — |

The raw reversal edge is genuine but **tiny (~12 bps mean gross / event)** and heavy-tailed
(sd 272 bps). The honest 1h cost wall (30 bps 1× / 60 bps 2×) **swamps it** — the exact E2/S4 physics:
intraday MN reversal dies behind the cost wall, and dispersion-conditioning at the 95th-pct threshold
does **not** concentrate enough per-event edge to clear it. GT-2× twin == analytic (max|Δ| = 0.00e+00).

---

## 3. Scored kill table (mechanical — K dies if ANY fires)

| Kill | Criterion | Load-bearing numbers | Verdict |
|---|---|---|---|
| **(a)** | median event rate < 4/mo | median **11.0/mo** (N=571, 8 zero-mo) | **not fired** |
| **(b)** | net-2×-cost spread ≤ 0 **OR** half-sign-unstable | mean net2x **−0.4823%** (t −4.23) ≤ 0; H1 −0.1344% (n=233) / H2 −0.7222% (n=338) — both negative (sign-STABLE) | **FIRED** (≤0 clause) |
| **(c)** | >50% of aggregate P&L in CRASH bucket | aggregate net1x = **−104.10%** (negative) → CRASH-share not evaluable-positive; (b) governs | **not fired** |
| **(d)** | post-event IC < 2× unconditional IC | conditional **+0.0630** vs unconditional **+0.0435** → ratio **1.45 < 2.0** | **FIRED** |
| floor | ≥150 events | N=571 | **met** |

**Two independent, over-determined kills (b + d).** Even ignoring cost, the mechanism does not earn
its own family: conditioning lifts the reversal IC only +45%, far below the required 2× — K collapses
into the **closed unconditional resid-mom/reversal family** (see §5).

**Bucket detail (kill c context + the fragility SIGNAL).**

| Bucket | n | net1x mean | net1x sum |
|---|---|---|---|
| CRASH | 52 | **+0.1035%** | **+5.38%** |
| MANIA | 128 | −0.1690% | −21.64% |
| CHOP | 391 | −0.2247% | −87.84% |

Kill (c) is mechanically **not fired** only because the aggregate is negative (kill b already voided the
book). But note the **fragility spirit is empirically present**: CRASH is the **only** bucket with a
positive net-1× mean — the residual, cost-swamped edge such as it is lives in **acute market stress**,
exactly where the all-weather doctrine wants the book quiet. This reinforces DEAD rather than rescuing.
**SECONDARY (non-gating):** 17 GAP-candle events, net1x sum −9.33% (GAP concentration not
evaluable-positive on the negative aggregate).

---

## 4. Conditional-vs-unconditional reversal IC (kill d)

`reversal IC = Spearman(−res4, forward-4h residual hold return)` over top-30 members, same window/universe:

| Read | Scope | Mean IC | t |
|---|---|---|---|
| **UNCONDITIONAL** | all 37,477 scored hours | **+0.0435** | +33.1 |
| **CONDITIONAL** | 571 event hours | **+0.0630** | +5.5 |
| ratio | — | **+1.45** | (bar ≥ 2.0) |

The reversal mechanism is **real and strong unconditionally** (IC +0.0435, t=33 — this *is* the closed
resid-mom/reversal-standalone family). Dispersion-conditioning **does** add information (+45%, and the
conditional IC is itself significant at t=5.5) — but not the ≥100% the pre-registered kill (d) demands
to justify K as a distinct family. **Conditioning adds something, not enough** → K reduces to the closed
unconditional family → **kill (d) FIRED**.

---

## 5. Leak battery — ALL PASS

| Check | Result |
|---|---|
| corrupt-future (r4 / xstd / threshold / raw-event flags / res4 rows < t0 bit-identical) | **PASS** |
| injected-leak positive control (sig := forward res_hold → IC ≈ 1) | **PASS** (IC +1.000) |
| decision-lag (res4[h]/event[h] use close ≤ h and β[h−1]; entry at open[h+1]; hold window never feeds the decision) | **PASS** (by construction) |
| past-only β (corrupt returns ≥ t0 → β[:t0] bit-identical) | **PASS** |

Event definition is past-only (30d 95th-pct threshold uses only history ≤ h−1 via `.shift(1)`; the
trailing-4h std at h uses closed bars); the book decides at close[h] and fills at open[h+1] (never the
event candle's own forward window); residual returns use past-only betas. The IC of +0.0435 is a
clean past→future signal (formation ends at close h; hold starts at open h+1 — no overlap).

---

## 6. Mechanical verdict

**DIAG-K = `DEAD (kill b + kill d)`.** Over-determined: (b) the honest net-2×-cost per-event spread is
robustly negative (−48 bps, t −4.23) — the ~12 bps gross reversal edge cannot clear the 30/60 bps 1h
cost wall; (d) event-conditioning lifts the reversal IC only +45% (1.45×), below the 2× bar, so K
collapses into the CLOSED unconditional resid-mom/reversal family. Kill (a) not fired (11/mo median);
sample floor met (571); kill (c) not evaluable-positive (aggregate negative — (b) governs), though the
CRASH-only-positive bucket pattern is an additional fragility signal consistent with DEAD.

**Banking rule (AMENDMENT-004 §C) — stated, moot.** A DIAG-K that survived all four kills would NOT
bank directly; it would trigger a separate **EXPLORATION-K engine-level honest-execution confirmation**
(the S4 reality check: `blind_engine.run_backtest`, weight projection, honest fills) before any candidate
status. DIAG-K did **not** survive; there is nothing to confirm and **nothing to bank**. **MN3-K UNSPENT.**

**Honest fail = good outcome.** As the field's last probe, DIAG-K delivers a clean, over-determined,
leak-checked null: the intraday cross-sectional reversal mechanism is real but (i) already captured by
the closed unconditional family and (ii) uneconomic once the honest 1h cost wall is paid. The S4
cautionary prior held — liquidity-provision theses in this dataset die at the honest-execution boundary.

---

## 7. Deliverable integrity

- **Implemented:** `analysis/portfolio/mn3_diag_k.py` (1h panel loader, event pipeline, honest per-event
  quintile book with force-exit, GT-2× twin, conditional/unconditional IC, GAP secondary, leak battery,
  mechanical scorer) + `tests/test_mn3_diag_k.py` (**19 tests**, all pass; synthetic-data-only).
- **Tests:** `uv run pytest tests/test_mn3_diag_k.py -q` → **19 passed**; mn3 subset
  (`test_mn3_infra` + diag_k + diag_j + crisis) → **78 passed** (namespace grep-ban intact).
- **Lint:** `uv run ruff check` on both touched files → **All checks passed**; `ruff format` applied.
- **Blinding invariants honored:** IS-only (2020-01-01→2024-06-30 via `mn3_split`, guard passed at
  step_ms=1h), holdout SEALED (`reveal_token=None`, MN3-K UNSPENT, zero ledger spends), honest costs
  (7.5 bps/side + GT-2× re-run), S4-lesson honest fills + force-exit, no engine core change, mn3 lowercase
  namespace, **nothing committed to git**.

*— Quant Researcher (Opus 4.8, Fable-suspended phase), MN3 track, 2026-07-11. DIAG-K — the MN3 field's
last probe. Mechanical verdict = DEAD (kill b + d); honest IS null; holdout sealed; MN3-K unspent;
nothing committed.*
