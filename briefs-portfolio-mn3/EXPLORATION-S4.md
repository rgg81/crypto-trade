# EXPLORATION-S4 — Amihud liquidity-provision, promoted to a standalone single-sleeve MN construction (MN3; IS-only; pre-registered)

**Track:** MN3 (two-year-holdout market-neutral). **Date:** 2026-07-11. **Author role:** Quant
Researcher. **Stage:** Stage-1 IS design-validation. **IS window:** 2020-01-01 → 2024-06-30 (the
`mn3_split` cutoff `MN3_IS_CUTOFF_MS = 2024-07-01`). **Holdout (2024-07-01 → 2026-06-30) is SEALED
and untouched** — this brief neither reveals nor references any holdout metric; the `mn3_guard`
family token `MN3-H` is NOT spent by this EXPLORATION (Stage-1 is IS-only by construction).

> **MODEL-NOTE (charter deviation, disclosed).** The MN3 charter mandates ALL AGENTS ON FABLE. The
> Fable mandate is **user-suspended for this phase** (Fable-5 rate limit; user direction: "continue
> on Opus"). This brief was authored on **Opus 4.8**, not Fable. Pre-registration integrity is
> unaffected: the construction, gates, throttle, cost stress, falsification arms, decision map, and
> ledger are FROZEN in this document BEFORE any EXPLORATION-S4 backtest runs; who typed the brief did
> not touch any revealed number (nothing has been revealed). This brief goes to a Critic pre-flight
> next, then a QE/QR scored run.

**Freeze statement.** Every construction detail, gate, threshold, throttle constant, cost-stress
multiplier, falsification arm, and decision-map tier below is FROZEN as of this document. Any change
after the Critic pre-flight requires a dated `PLAN-AMENDMENT-NNN` (or an `EXPLORATION-S4-AMENDMENT`
section) recorded BEFORE the scored run — never an in-place edit, never a post-hoc re-gate.

**Provenance.** S4 was the sole survivor of `DIAG-H.md` (born-ensemble family — DEAD, kill-(a):
<2 sleeves passed). S4 PASSED its sleeve gate cleanly and is the FIRST all-weather, crash-robust,
cost-surviving single sleeve the MN/MN3 effort has produced. Per user decision ("go S4 after this"),
it is spun out as its OWN single-sleeve construction. This brief pins S4 to the **DIAG-H scored
implementation** (`analysis/portfolio/mn3_diag_h.py`) EXACTLY, promotes its scoring from the
diagnostic residual-return level to the **real backtest engine** (`blind_engine.run_backtest` +
weight-level beta projection), and adds the two things a standalone construction requires that a
diagnostic sleeve did not: a **Layer-2 per-construction crisis throttle** (AMENDMENT-002 §C) and an
**honest long-side cost stress** (the amendment already flagged S4's long leg as structurally
costlier).

---

## Section 0 — Contamination disclosure (§1.3, reproduced verbatim per charter; S4-specific below)

**Family-H row (PLAN §1.3), verbatim:** *"H born-ensemble — as G, per sleeve [W1: univariate ICs of
constituent feature classes (funding/taker/OI/resid-mom) were measured as MN-v2 IS] — Sealed-as-
achievable with two flags: S1 (carry sleeve) inherits family-A signal knowledge; S2's continuation
SIGN comes from MN-v2 DIAG-C measured over W1–W2."*

**S4-specific contamination read (the honest, narrow truth):**

1. **Amihud liquidity-provision is a GENUINELY NEW mechanism.** It was never probed by the old track
   (vol_low family), never by MN-v2 (carry / coint / crowding / taker / resid-mom), never by any
   MN3 family other than H. No Amihud sort, no liquidity-provision book, and no |ret|/dollar-volume
   signal has ever been evaluated on any window of this dataset — IS or holdout. **The holdout is
   sealed in the only sense achievable and in the STRONG sense for S4 specifically: never evaluated
   for this mechanism, and the mechanism itself is fresh.** Unlike H's S1 (family-A signal knowledge)
   and S2 (DIAG-C-contaminated sign), **S4 carries neither flag** — this is the cleanest sleeve in
   the family on provenance.

2. **S4 emerged from DIAG-H, which is IS-only → NO book-level contamination.** DIAG-H scored S4 on
   IS data (2020-01→2024-06) only; the `mn3_guard` fired with zero holdout reveals (REVEAL-LEDGER
   untouched). No S4 book has ever touched the holdout. Knowing S4's IS regime behavior (+54% CRASH,
   etc.) is IS knowledge, which is permitted; it is the whole point of Stage-1.

3. **Regime-composition knowledge of the holdout LEAKS and is disclosed.** As QR I hold in-head
   knowledge that the holdout is **2025-11→2026-06 crash-heavy, 2026-H1 MANIA-free** (§1.3 self-
   disclosure). **This is the material contamination for S4 and it is confronted head-on:** S4 is
   crash-POSITIVE (+54% IS CRASH bucket), so a naive reader could suspect I am steering a
   crash-hardened book at a known crash-heavy holdout. Four pre-registered defenses (the §1.3 (i)–(iv)
   set) neutralize this: **(i)** market-only regime bucketing (frozen `mn_regimes` rules, §4) scores
   composition mechanically, never narratively; **(ii)** this decision map pre-commits its
   interpretation across bucket compositions BEFORE any reveal; **(iii)** every threshold below is
   coverage- or principle-anchored, NEVER fitted to any revealed draw — and, critically, never fitted
   to S4's known IS +17%/yr or +54% CRASH (the Sharpe floor is the economic-relevance principle
   floor, identical to the v2 template, demonstrably NOT S4's number); **(iv)** the crisis doctrine
   is falsified IS-only, and the holdout map's EDGE read (not mere survival) is the arbiter — a book
   that survives crashes but earns nothing still FAILS. S4's crash-positivity was **measured IS-only
   in DIAG-H and is PREDICTED a-priori by the mechanism** (the illiquidity premium is structurally
   largest when liquidity is scarcest), not reverse-engineered from holdout knowledge.

4. **In-head family-A contamination (carried per §1.3, irrelevant to S4's signal but disclosed):** I
   have read PHASE7-CONFIRMATION-A and know A3-1's holdout behavior. S4's signal (Amihud) shares
   nothing with family A's funding sort; the only inheritance is *methodological* (the SCUD throttle
   template and the gate set), which is sanctioned reuse, not signal contamination.

**Killed-at-mechanism families stay closed:** vol_low, pairs-persistence, taker-standalone,
resid-mom-standalone, OI-fade. S4 walks NEAR none of them (liquidity provision is orthogonal to all
five closed mechanisms — DIAG-H's sleeve-correlation matrix confirms S4 is decorrelated from S1/S3).

---

## Section 1 — Frozen construction (pinned to DIAG-H `mn3_diag_h.py` EXACTLY; engine-level promotion)

### 1.1 The S4 object — FROZEN, pinned to the DIAG-H implementation

Every constant below is the DIAG-H module's frozen value (`mn3_diag_h.py` lines 154–182). No tuning.

| Element | Frozen value | DIAG-H source |
|---|---|---|
| **Universe** | PIT top-40 by trailing 30c mean quote-$-volume, ex-stablecoins, ≥270-candle history filter | `build_universe(panel, TOP_N=40)` → `pit_topn_universe(masked, top_n=40, lookback=30, min_periods=10)` with `HIST_MIN_CANDLES=270` mask |
| **Signal (Amihud)** | trailing **30c** mean of **\|ret\| / quote-$-volume**, min **10** finite obs; per-candle component NaN where volume ≤ 0 | `amihud(rets, panel.quote_volume)`, `AMIHUD_W, AMIHUD_MIN = 30, 10` |
| **`ret` convention** | close-to-close pct-change (the panel/`mn_beta` returns convention) | `rets = close.pct_change()` |
| **`$-volume` convention** | `quote_volume` (Binance quote-asset volume) | `panel.quote_volume` |
| **Direction — FROZEN** | **LONG high-Amihud (thin half) / SHORT low-Amihud (most liquid)** | `long_high=True` |
| **Book** | quintile L/S, k = n // 5 per leg, **equal weight 1/k per name**, dollar-neutral | `quintile_book_sim`, `QUINT=5`, `w = ±(1/k)` |
| **Min cross-section** | ≥ **20** valid members (TOP_N//2) per scored candle, else candle skipped | `MIN_MEMBERS = 20` |
| **Beta projection** | `mn_beta.rolling_beta` frozen defaults: ref=BTCUSDT, window **270**, min_periods **135**, shrink λ=**0.33**, clip **[0,3]**, consumed at **[k−1]** | `rolling_beta(panel)`, `beta_lag = beta[:-1]` |
| **Cadence** | weekly rebal = **21** candles; **full 21-phase** equal-weight tranche ensemble (phase-agnostic mean is the ONLY headline; single-phase numbers never load-bearing) | `REBAL=21`, `N_PHASES=21`, `nan_ensemble` |
| **Costs** | **5 bps taker + 2.5 bps slip = 7.5 bps/side** + funding on every leg | `COST_PER_SIDE = 7.5e-4` |
| **Forward horizon (diagnostic IC only)** | forward 21c residual TOTAL return | `FWD_K=21` (not used by the engine book; IC-diagnostic only) |

**Direction is FROZEN and non-negotiable.** LONG high-Amihud / SHORT low-Amihud. A measured opposite
sign (i.e. LONG low-Amihud outperforming) is a **FAIL of the construction**, NEVER a re-orientation
(the S3-C2 / DIAG-C D10 precedent — re-orienting a frozen direction is banned as a covert new trial).

**DIAG-H scored result being promoted (the empirical basis, IS-only):** net-of-2×-cost **+17.0%/yr**,
phase-agnostic median +13.9%, **19/21 phases positive**, H1/H2 sign-stable (**+13.9% / +19.5%**),
**CRASH +54.0% (best-in-crash) / MANIA +25.8% / CHOP +7.4%** (positive every regime), turnover
**74×** (lowest of the four sleeves), GT 2×-cost twin re-run PASS (statelessness proven).

### 1.2 Engine-level promotion (the QE wiring ask — this is the ONE construction difference vs DIAG-H)

DIAG-H scored S4 at the **diagnostic residual-return level**: book P&L = `w · (resid − fund)` where
`resid = rets − β[k−1]·r_BTC` (return-level BTC residualization) and `fund` is per-candle funding.
EXPLORATION-S4 promotes this to the **real backtest engine with weight-level beta projection** — the
same wiring CONFIRMATION-A used, which transferred OOS at ρ(w_proj, w_raw) = 0.976. The QE builds:

1. **Book weights:** the DIAG-H quintile L/S weights EXACTLY (equal-weight 1/k per leg, direction
   `long_high=True`), from the frozen Amihud signal + `build_universe` (§1.1), at every rebal step.
2. **Beta neutralization (weight-level, replacing the diagnostic's return-level residualization):**
   `mn_exploration_a2.apply_beta_neutralization` — BTC-only minimal-L2 projection of the raw quintile
   weights onto `{Σw = 0, Σw·β = 0}`, rolling BTC β from `mn_beta.rolling_beta` (270/135/λ=0.33/
   clip[0,3]); degenerate guard `Σ(β−β̄)² ≤ 1e-12·Σβ²`; collapse guard `Σ|w_proj| < 0.10·g`. This is
   BTC-only, matching DIAG-H's BTC-only residualization (see §1.4 reconciliation R1).
3. **Per-name cap** `|w_i| ≤ 0.10·g`, iterative pro-rata, cap applied last (safety rail — at quintile
   granularity k≈7 each name is ≈7% of gross, so the cap will rarely bind; a binding cap signals a
   universe/projection anomaly to report).
4. **Engine:** `blind_engine.run_backtest` UNCHANGED, weekly `rebal=21`, 21-phase equal-weight tranche
   ensemble, costs 5+2.5 bps/side + funding on every leg (`blind_funding.load_funding`), Layer-2
   throttle wired via the pre-existing `gross_scalar_series` (§2). **No engine code change** —
   throttle is a past-only scalar array, projection is the a2 helper, universe/signal are the mn3
   builders.
5. **Warmup continuity + reproducibility assert:** the ensemble is BUILT on the full IS panel so every
   tranche's rolling β, throttle-z, universe history and warmup are continuously populated; a
   reproducibility assert requires the engine book's realized neutrality to match the DIAG-H
   residual-book neutrality (both ≈ 0 beta) — the load-bearing R1 reconciliation check.

### 1.3 Two-times-cost twin (the load-bearing cost object) + GROUND-TRUTH re-run

The 2× twin is **GROUND-TRUTH** (a full engine re-run at doubled cost, `COST_PER_SIDE = 2×7.5e-4 =
15 bps/side` both legs), NOT analytic — S4's throttle makes the book non-stateless at the gross level
(a throttled book's turnover differs from the un-throttled twin), so an analytic `rets − turnover·Δcost`
twin is inadmissible per the charter (analytic twins are for stateless constructions only). DIAG-H
already proved the 2×-cost twin PASS on the raw sleeve; the engine re-run re-proves it with the
throttle in place.

### 1.4 Reconciliations (DIAG-H implementation vs PLAN §3.2 vs the engine — pinned to DIAG-H)

Where DIAG-H's implementation and PLAN §3.2 differ, I pin to **DIAG-H (the scored object)** and
disclose:

- **R1 — Beta neutralization level.** DIAG-H: return-level BTC residualization (`resid = rets −
  β·r_BTC`). Engine: weight-level BTC minimal-L2 projection (`apply_beta_neutralization`). Both are
  **BTC-only**. The promotion changes the *mechanism* of neutralization (return-scored → weight-
  projected) but not the *target* (BTC-beta-neutral). Load-bearing check: §1.2(5) asserts the engine
  book's realized β ≈ 0 (G1a) matches the diagnostic's near-zero residual β. ETH-neutrality (G1b) is
  MEASURED and gated but NOT projected against (as in A3/CONFIRMATION-A — BTC/ETH co-movement makes
  the BTC projection incidentally ETH-tame; if G1b fails, that is a real finding, not a wiring bug).
- **R2 — Liquidity floor.** DIAG-H `build_universe` applies NO `$3M/8h` floor (top-40-by-$-volume are
  the liquid set already). CONFIRMATION-A's engine `build_universe` DID apply `LIQ_FLOOR_USD =
  $3,000,000`. **I pin to DIAG-H (no floor) to preserve the scored object** — adding a floor would
  remove the thinnest LONG-leg names (exactly S4's edge-carrying cohort) and change the object.
  The `$3M/8h` floor is registered instead as an **informational sensitivity arm (CS-L, §3.4)** —
  does the edge survive if the thinnest un-executable names are removed? — NOT as a change to the
  primary book. Disclosed as a reconciliation.
- **R3 — Weighting scheme.** DIAG-H uses **quintile equal-weight (1/k)**, NOT rank-weight. Preserved
  exactly. (A2/A3's rank-weighting is a different object; S4 stays quintile-equal-weight.)
- **R4 — Funding accounting.** DIAG-H charges funding on the residual stream (`total = resid − fund`);
  the engine charges funding per-leg through `blind_funding`. Equivalent in expectation; the engine
  is the honest per-position version and supersedes the diagnostic shorthand.

---

## Section 2 — Crisis defense: Layer-2 per-construction throttle (AMENDMENT-002 §C; FROZEN)

### 2.0 Why Layer-2 ONLY (no shared crisis machine)

Per `CRISIS-FALSIFY-003.md` and PLAN-AMENDMENT-002: **both shared crisis floors are DEAD by their own
frozen bars.** Layer-1 GAP-only (§A) FAILED (25 distinct CRISIS entries > 16; off-episode 4.1% > 3% —
a violent-candle interrupt that is not sparse enough, and fires on |r| so 7/17 off-episode entries
were *up*-candles, wrong for an MN book). Layer-B DD-from-peak (§B) FAILED terminally (CRISIS
occupancy 12.5% > 8%; S+C 27.6% > 25% — the level-persistence trap partially won). **The surviving,
BINDING crisis doctrine is the AMENDMENT-002 §C per-construction Layer-2 throttle ONLY.** S4 therefore
ships its OWN gross throttle from birth — a SCUD-style scalar on the book's own signal-state — and
carries NO shared crisis machine. There is no `s_gap`, no `s_dd`; the effective gross scalar is the
throttle's own `s_con` (§D `min` composition degenerates to `s_con` when the floors are absent).

### 2.1 The S4 throttle — "Long-Cohort Downside-Dispersion z" (LCDD-z), FROZEN

The exact **structural mirror of the sanctioned A3 SCUD primitive** (`mn_scud.build_scud_throttle`),
re-pointed from the funding book's exposed leg to S4's exposed leg. SCUD read the SHORT cohort's
UPSIDE dispersion (short-squeeze = the funding book's tail). S4's exposed leg is the **LONG thin
cohort**; its tail is a **flight-to-liquidity dump** — the thin names S4 is long getting sold into an
evaporating book. LCDD-z reads that market-structure tail, past-only, NOT the book's own equity (the
A3 principle: z-score the book's own *cohort*, which is sustained-regime-aware, never the book's
realized drawdown, which is self-referential/stateful).

At each candle t:
1. **Long cohort** `L_t` = universe members[t] whose Amihud signal is in the **top q_long = 0.33
   fraction** (highest Amihud = thinnest = the names S4 LONGS — the squeeze-analog exposed leg).
   Require `|L_t| ≥ m_min = 5`; if fewer (early era / infeasible), **forward-fill** the last valid
   indicator value (throttle = 1.0 over pre-live warmup, where the book is flat anyway).
2. **Trailing return** per cohort name: `rᵢ = close_i[t] / close_i[t − h] − 1`, `h = 9` candles
   (3 days, the signal/persistence timescale). Past-only. (Reuse `mn_scud.trailing_h_returns`.)
3. **Downside-dispersion** `D[t] = − P25{ rᵢ : i ∈ L_t }` — the robust LOWER-tail statistic (the
   mirror of SCUD's 75th-percentile UPPER-tail), negated so higher `D` = the thin long cohort is
   selling off harder. Robust to a single delisting/print outlier (vs using the min).
4. **Z-score** over a trailing window `W = 90` candles (30d), `min_periods = 45`:
   `LCDD_z[t] = (D[t] − mean_W(D)) / std_W(D)`, clipped to `[−5, +5]`.

**Throttle scalar — piecewise-linear ramp (reuse `mn_scud.scud_ramp`, IDENTICAL constants):**
- `τ_lo = +0.85` (≈ standard-normal **80th percentile**) — below it, no throttle (scalar = 1.0).
- `τ_hi = +1.65` (≈ standard-normal **95th percentile**) — at/above it, full de-risk (scalar = φ).
- **Floor scalar φ = 0.50** — halve gross in the worst thin-cohort-dump regime (keep the liquidity-
  provision engine ON; a full flatten would surrender the immediacy premium the book exists to
  collect).
- Ramp: `scalar(z) = 1.0 − (1.0 − φ)·clip( (z − τ_lo)/(τ_hi − τ_lo), 0, 1 )`.
- **Release:** automatic and continuous (pure function of `LCDD_z[k−1]`; no separate hysteresis
  state). Consumed at every rebal step **[k−1]**; between rebals the gross is held.

**Constant provenance (coverage/principle-anchored, INHERITED with disclosure — NOT refit).** Every
constant (`q_long=0.33`, `m_min=5`, `h=9`, `W=90`, `min_periods=45`, clip ±5, `τ_lo=+0.85`,
`τ_hi=+1.65`, `φ=0.50`) is carried VERBATIM from the sanctioned A3 SCUD spec (EXPLORATION-A3 §1.1/§1.2;
`mn_scud.py`). τ are standard-normal percentile coverage anchors; W=90/min45 is the track's z-window
convention; φ=0.50 is a round non-fitted de-risk. **The ONLY change from SCUD is the leg (top-0.33
Amihud thin cohort, not bottom-0.33 funding) and the tail direction (P25 downside, not P75 upside)** —
both forced by S4's LONG-thin exposure, not chosen for fit. This is the AMENDMENT-002 §C "inheritable
with disclosure, NOT refit" clause, honored to the letter. Per §3.2, this throttle is the **one new
DOF** EXPLORATION-S4 spends (§8 ledger).

**Neutrality is preserved by construction.** The throttle is a positive scalar `s ∈ [φ,1]` on a
dollar- and beta-neutral book: `Σ(s·w) = s·Σw = 0` and `Σ(s·w)·β = s·0 = 0` EXACTLY. A throttled S4
is a clean positive-scalar multiple of the un-throttled S4 at every rebal — the throttle can NEVER
break neutrality, only scale gross. (The A3 proof, inherited.)

### 2.2 The crash-positivity TENSION — confronted, and turned into the throttle's own falsifier

**The honest hazard, stated up front:** S4 is crash-POSITIVE (IS CRASH +54.0%). A throttle that
fires when the thin cohort dumps could fire during exactly the crashes where S4 PROFITS — cutting
carry instead of clipping a tail. This is the single most important design risk for S4's throttle, and
it is why the throttle carries its OWN pre-registered falsification arm rather than an assumed benefit.
The data decides among three FROZEN dispositions:

- **THROTTLE-HELPS:** maxDD improves by **≥ 2 pp** AND net Sharpe ≥ **0.90×** the un-throttled S4
  Sharpe. → the throttle clips a genuine left-tail (an adverse flight-to-liquidity inversion) at a
  bounded carry cost; it is load-bearing and S4 ships throttled (the headline book).
- **THROTTLE-NEUTRAL:** maxDD within **±2 pp** AND net Sharpe within **±10%** of un-throttled. → the
  throttle is cheap insurance (fires rarely, near-neutral); S4 ships throttled anyway (it is the
  required §C Layer-2 primitive and, being neutrality-preserving and near-costless, it does no harm).
- **THROTTLE-HURTS:** maxDD **worsens** OR net Sharpe **< 0.85×** un-throttled. → the mechanism-
  faithful throttle mis-times S4's crash-positive regime (it fires in S4's *profitable* thin-cohort
  dumps). This is a **disclosed FINDING**, not a construction FAIL: S4 ships **throttle-OFF**, and
  "no effective weekly-cadence Layer-2 defense found for a crash-positive liquidity book" is carried
  as an open Stage-2 design question. (The alpha lives in the Amihud sort, §5.1; the throttle is
  risk-shaping, not the edge — so shipping throttle-off does not remove the edge.)

### 2.3 The throttle's own falsification arm (past-only leak test + IS behavior, §C requirement)

- **Leak battery (mandatory):** corrupt-future positive control on `LCDD_z` (corrupt rows ≥ t ⇒
  `LCDD_z[<t]` bit-identical), decision-lag proof (scalar at fill k uses only data ≤ close[k−1]),
  append-invariance, forward-fill semantics. Reuse the `mn_scud` corrupt-future harness pattern.
- **IS coverage (reported, coverage-anchored expectation):** fraction of rebals with scalar < 1.0
  (expected ~15–25% at τ_lo=80th pct), fraction at full floor scalar = φ (expected ~3–8% at
  τ_hi=95th pct), mean gross scalar over live rebals (expected ~0.90–0.96). A gross departure
  (coverage > 40% or mean scalar < 0.80) signals the thin-cohort dispersion is chronically elevated
  (a distributional mismatch to the SCUD anchors) — REPORT, do not tune.
- **HELPS/NEUTRAL/HURTS forensic (the §2.2 disposition):** within-run comparison of throttled vs
  un-throttled S4 — maxDD delta, Sharpe ratio, and a throttle-active-window mean-return read (are
  throttle-active windows S4's LOSING windows [good] or WINNING windows [bad]?).

---

## Section 3 — Honest long-side cost stress (S4's thin LONG leg is structurally costlier; FROZEN)

**The problem, disclosed (AMENDMENT flagged it):** S4 LONGS the thin half of the top-40 (high-Amihud)
and SHORTS the most liquid half (low-Amihud). The long leg is **structurally more expensive to
execute** — thinner books, wider spreads, more slippage — precisely because it is the illiquidity-
premium harvest. A symmetric cost model understates S4's real execution cost on the leg that carries
the edge. Three stress arms, pre-registered with pass bars:

### 3.1 Arm CS-2× — standard GT twin (load-bearing) — HARD
Full engine re-run at **15 bps/side both legs** (2× base). **Pass bar (`G-2xcost`, §4):** net 2×-cost
Sharpe **> 0 AND ≥ 0.5 × the 1×-cost Sharpe.** (DIAG-H already proved net2× +17.0%/yr POSITIVE on the
raw sleeve; the engine re-run re-proves it with the throttle in place.)

### 3.2 Arm CS-A — asymmetric long-leg stress (the mechanism-faithful thin-name stress) — HARD
Full engine re-run with **asymmetric per-side cost: LONG leg 3× = 22.5 bps/side; SHORT leg 1× =
7.5 bps/side.** Models the thin-name execution premium on the leg that actually pays it. **Pass bar
(`G-coststress`, §4): net Sharpe > 0 AND net annualized return > 0.** This is THE proof that the edge
survives realistic thin-name execution — the load-bearing honest-cost gate for a liquidity-provision
book. The 3× long multiplier is a principle anchor ("the thinner half of the liquid set costs ~3× the
liquid half to cross"), not a fitted number; it is deliberately demanding (a razor-thin edge dies
here).

### 3.3 Arm CS-3× — blunt symmetric over-stress (corroboration) — SOFT
Full engine re-run at **22.5 bps/side both legs** (3× base). **Report bar (`G-3xcost`, SOFT):** net
Sharpe > 0. A conservative sanity read; a book that survives 3× symmetric is cost-robust with margin.
SOFT because 3× on the SHORT (liquid) leg over-penalizes names that are cheap to trade.

### 3.4 Arm CS-L — liquidity-floor sensitivity (informational; ledger-neutral)
Re-run with the CONFIRMATION-A `$3M/8h` liquidity floor applied to the universe (removing the thinnest
names). **Report:** net Sharpe retention vs the no-floor primary. **Disclosure read:** retention ≥
0.50 ⇒ the edge lives in the *executable* thin half (robust); retention < 0.50 ⇒ the edge concentrates
in un-executably-thin names (a real deployability caveat, disclosed, not a pass/fail here since the
floor changes the object — R2). Ledger-neutral (no design choice keys off it).

---

## Section 4 — Full HARD gate set (charter/PLAN set on the S4 book; FROZEN; each with its falsifier)

Evaluated on the **as-shipped book** (throttled, unless §2.2 returns THROTTLE-HURTS ⇒ throttle-off,
disclosed). Neutrality gates use `mn_regimes` frozen buckets (trailing-90c BTC return; CRASH ≤ −15%,
MANIA ≥ +25%, else CHOP; RETURN-candle labels; any bucket n < 30 ⇒ loud N/A-FAIL). β measured by OLS
of book net return on BTC/ETH 8h returns. All thresholds are principle- or relative-anchored — NONE
fitted to S4's known IS numbers.

| # | Gate | Threshold | H/S | Falsifier (what a FAIL means) |
|---|---|---|---|---|
| **G1a** | rolling-270c \|β_BTC\| (book net) | ≤ 0.10 on ≥95% of post-warmup candles **AND** max ≤ 0.20 | **HARD** | the weight projection does not neutralize BTC beta out-of-diagnostic → wiring or β-staleness defect, or the "edge" is BTC beta |
| **G1b** | rolling-270c \|β_ETH\| | ≤ 0.15 on ≥95% **AND** max ≤ 0.25 | **HARD** | BTC-only projection leaves material ETH exposure → not genuinely market-neutral |
| **G2-CRASH** | bucket-conditional \|β_BTC\| in **CRASH** | ≤ 0.15 | **HARD** | S4's +54% CRASH is directional beta, not neutral illiquidity premium — the doctrine's hard crash-neutrality requirement |
| **G2-MANIA** | bucket-conditional \|β_BTC\| in **MANIA** | ≤ 0.15 | **HARD** | the book takes on beta in mania → not all-weather neutral |
| **G3** | net exposure at every rebal (post-projection, cap included) | \|Σw\| ≤ 0.10 × gross | **HARD** | dollar-neutrality violated by cap/projection interaction |
| **G4** | worst-bucket mean net return t-stat (CRASH/MANIA/CHOP) | t > **−1.0** | **HARD** | a regime bucket loses significantly → not all-weather (DIAG-H had all three positive; a significant loss here falsifies durability) |
| **G-sharpe-floor** | net Sharpe (honest 1× cost), as-shipped book | ≥ **+0.35** | **HARD** | below the economic-relevance floor: the net Sharpe after honest cost does not justify the neutralization machinery (principle floor, identical to v2 template — NOT S4's number) |
| **G-2xcost** | net 2×-cost Sharpe (CS-2×) | > **0 AND ≥ 0.5 × 1× Sharpe** | **HARD** | cost-fragile — the edge is a cost mirage |
| **G-coststress** | net Sharpe **AND** net ann return under CS-A (asym long 3×) | both **> 0** | **HARD** | the edge does NOT survive realistic thin-name execution — the S4-specific load-bearing gate |
| **G-maxdd** | as-shipped book maxDD | ≥ **−25%** | **HARD** | draws down like an equity bet — fails the all-weather MN mandate |
| **G-turnover** | ann one-way turnover | ≤ **250×/yr** | **HARD** | cost-fragility ceiling (DIAG-H 74× — expected far under; a blowout signals a churn defect) |
| **G-durable** | sign-stable across IS halves: sign(H1 net) = sign(H2 net), both > 0 | **H1 > 0 AND H2 > 0** | **HARD** | the edge is a one-half artifact, not durable (DIAG-H +13.9%/+19.5% — expected PASS) |
| **G-sample** | scored coverage sized to weekly cadence over 4.5yr IS | span ≥ **4.0 yr** AND ≥ **200 weekly rebals/phase** AND ≥ **12 names/rebal** mean AND every full IS year (2021/22/23) represented | **HARD** | book scored on a truncated window → Sharpe untrustworthy (Rung-4 trade-rate floor, sized to cadence) |
| G5 | bucket P&L concentration | no bucket > 60% of total P&L | SOFT | one regime carries the book — report; sets tier nuance |
| G-sharpe-target | net Sharpe | ≥ **+0.90** | SOFT | the "clean candidate" level (vs the +0.35 floor) |
| G-concentration | single-name share of gross | ≤ 10% of gross | SOFT | structurally satisfied by quintile equal-weight (~7%); a violation signals a universe/cap bug |
| G-3xcost | net Sharpe under CS-3× | > 0 | SOFT | corroborating cost-robustness (§3.3) |

**13 HARD** = {G1a, G1b, G2-CRASH, G2-MANIA, G3, G4, G-sharpe-floor, G-2xcost, G-coststress, G-maxdd,
G-turnover, G-durable, G-sample} — where **G-coststress is the S4-specific addition** to the v2
11-HARD template (the v2 set had one crash contingency and no thin-leg cost gate; S4 splits G2 into
CRASH+MANIA rows and adds G-coststress, netting 13). **4 SOFT** = {G5, G-sharpe-target,
G-concentration, G-3xcost}. The SET is what binds, not the count.

**Floor rationale (principle, NOT DIAG-A/S4-fitted).** `G-sharpe-floor +0.35` and `G-coststress > 0`
encode economic relevance and cost-survival, not S4's revealed +17%/yr. `G-maxdd −25%` encodes "an
all-conditions MN book must not draw down like an equity bet." `G-turnover 250×` is the cost-fragility
ceiling. All identical in spirit to the EXPLORATION-A template so the Critic can audit that no floor
is set just under S4's known number.

---

## Section 5 — Falsification arms (pre-registered NEGATIVE controls; kill-only; ledger-neutral)

### 5.1 The throttle must NOT be the alpha (un-throttled twin) — HARD control
Run S4 with the throttle OFF (`gross_scalar_series ≡ 1.0`). **The un-throttled S4 must ALSO clear
`G-sharpe-floor` and `G-2xcost`.** This proves the edge lives in the **Amihud sort**, and the throttle
only shapes risk. **FALSIFIER:** if the un-throttled book fails the alpha floors but the throttled one
passes, the throttle is manufacturing the "edge" as a covert market-timing overlay → **FAIL** (edge is
the throttle, not the mechanism). (This is also the §2.2 un-throttled reference for HELPS/NEUTRAL/HURTS.)

### 5.2 The beta projection must NOT be smuggling directional beta (shuffled-signal placebo) — HARD control
Run the SAME quintile book + SAME projection + SAME costs on a **cross-sectionally shuffled Amihud
signal** (ranks permuted within each candle's live universe; a fixed seed, pre-registered, disclosed).
The placebo book must be **(i) beta-neutral** (G1a/G1b/G2 pass — proving neutrality is a property of
the projection, not the signal) **AND (ii) zero-edge** (Sharpe 95% CI includes 0). **FALSIFIER:** a
placebo Sharpe reliably > 0 ⇒ the "edge" comes from the projection / universe / cost structure, not
Amihud → **FAIL** (spurious plumbing edge). Report the placebo Sharpe distribution over ≥ 20 shuffles
(pre-registered seeds) so "CI includes 0" is measured, not asserted.

### 5.3 Direction integrity (frozen-sign control) — HARD
Report the LONG-low-Amihud / SHORT-high-Amihud book (the reversed direction). It MUST underperform the
frozen LONG-high direction. **FALSIFIER:** if reversed ≥ frozen, the mechanism is not what the payer
story claims (immediacy demanders in the thin names) → **FAIL**, and — per S3-C2/D10 — the frozen
direction is NEVER re-oriented to chase the reversed sign (re-orientation is a banned covert trial).

### 5.4 Long/short leg attribution (informational)
Report each leg's gross return and each leg's standalone realized β. If one leg carries all the beta
or all the P&L, disclose (a neutral *combined* book can still hide a lopsided leg). Informational; feeds
the Critic's read, not a hard gate.

---

## Section 6 — Frozen decision map (IS design-validation only; NO holdout reveal; mechanical)

Tiers are decided MECHANICALLY on the frozen gates + controls. No post-hoc re-gating. The map is
IS-scoped: the BEST outcome is "IS-design-validated candidate for a FUTURE Stage-2 reveal," NEVER a
deployment or reveal decision (this EXPLORATION spends no token).

| Tier | Condition | Consequence |
|---|---|---|
| **SUCCESS** | ALL 13 HARD pass on the as-shipped book (incl. G2-CRASH, G2-MANIA, G4, G-coststress, G-durable, G-sample) **AND** §5.1 un-throttled twin clears the alpha floors **AND** §5.2 placebo is null (beta-neutral + Sharpe CI ∋ 0) **AND** §5.3 direction sign correct | S4 is an **IS-design-validated, all-weather, cost-surviving market-neutral candidate** — realized beta inside the charter gate in every regime incl. crash, edge in the Amihud sort (not the throttle, not the projection), durable across IS halves, survives thin-name execution. Becomes the **candidate for the family-H (`MN3-H`) holdout reveal** (a FUTURE Stage-2 CONFIRMATION). **NOT a deployment decision, NOT a reveal.** |
| **MARGINAL** | ALL neutrality HARD (G1a,G1b,G2-CRASH,G2-MANIA,G3,G4) pass **AND** §5.2/§5.3 controls clear, **BUT** a PERFORMANCE HARD fails (G-sharpe-floor / G-2xcost / G-coststress / G-maxdd / G-turnover / G-durable / G-sample) — OR the §2.2 throttle disposition is THROTTLE-HURTS (ship throttle-off, disclosed) | Genuinely neutral but not yet a clean candidate (edge too thin, cost-fragile on the thin leg, or draws too deep). Documented; the specific failed floor names the next iteration's target (e.g., faster cadence for durability, a different throttle for the tail). NOT revealed. |
| **FAIL** | ANY neutrality HARD fails (G1a/G1b/G2-CRASH/G2-MANIA/G3/G4) — OR §5.1 un-throttled twin fails the alpha floors (edge is the throttle) — OR §5.2 placebo shows a spurious edge (edge is plumbing) — OR §5.3 direction sign flips (mechanism falsified) | The mechanism or its neutralization is falsified. Localize, document, NOT revealed. A G2-CRASH/MANIA fail specifically means S4's regime performance is directional beta, not neutral illiquidity premium — the doctrine's central falsifier. |

**Per-HARD-gate falsifiers** are enumerated in the §4 table (each row's last column) — the decision map
consumes them; it invents no new threshold.

---

## Section 7 — Holdout governance (shared token; Stage-3 arbiter; ensemble-capstone note)

- **Shared token.** Per PLAN §3.2 anti-gaming rule, S4 is a **re-parameterization of family H** and
  **shares family H's one-forever holdout token `MN3-H`.** A future Stage-2 S4 reveal consumes
  `MN3-H` and thereby **burns family H's ENTIRE holdout budget** — the ensemble path (EXPLORATION-H
  composite, already closed by kill-(a)) and any S1/S2/S3 spin-out die with it. There is exactly one
  `MN3-H` reveal, ever.
- **This EXPLORATION spends NO token.** Stage-1 is IS-only; `mn3_guard` fires with `reveal_token=None`
  and MUST raise on any holdout-window overlap. REVEAL-LEDGER stays at zero spends.
- **Stage-3 is the real arbiter.** Per the charter lifecycle, even a clean Stage-2 `MN3-H` reveal is
  followed by a **six-month forward paper-trade** (recompute architecture, `mn3_paper_*`, pre-
  registered gates) on genuinely-unseen post-2026-06 data — that forward test, not the IS gates here,
  is the deployment arbiter.
- **Ensemble-capstone note (governance CHOICE at Stage-2, flagged now).** DIAG-G (ML cross-sectional
  residual alpha) is in pre-flight (`PREFLIGHT-DIAG-G.md`). **If DIAG-G also banks a family, then
  S4 + G is the born-ensemble the user originally wanted** (H's ensemble doctrine realized as a
  cross-family capstone, §6.3). At Stage-2 the choice is: reveal S4 standalone (burns `MN3-H` only)
  OR wait for G and reveal **S4 + G as `MN3-ENSEMBLE`**, which consumes BOTH `MN3-H` AND `MN3-G`
  tokens atomically (§5.1 guard behavior). This EXPLORATION does not force that choice — it validates
  S4 IS-only so S4 is *ready* to be either a standalone reveal or an ensemble member.

---

## Section 8 — Multiple-testing budget / ledger (minimize DOF — S4 is ONE fixed construction)

- **Family-H ledger opened at 4** (S1–S4, one registered trial per sleeve, spent in DIAG-H).
- **EXPLORATION-S4 spends +1:** promoting S4 to the engine adds **0 signal DOF** (identical Amihud
  sort, direction, universe, cadence — a re-parameterization sharing H's token, per §3.2); the **one
  new DOF is the LCDD-z throttle** (§2.1), a single fixed construction with fully-inherited constants.
  ⇒ **family-H cumulative n_eff → 5.**
- **Cap 8** (PLAN §3.2, one amendment round max). Opening at 5 leaves headroom for at most one
  Critic-mandated variant; a second throttle spec or a signal re-parameterization would be a new trial
  and must be registered.
- **Ledger-neutral (kill-only) arms — spend 0:** the CS-A/CS-3×/CS-L cost-stress arms (§3), the
  un-throttled twin (§5.1), the shuffled placebo (§5.2), the reversed-direction control (§5.3), and
  the leg attribution (§5.4). No design choice may key off any of them; if one ever conditions a
  design choice it converts to a registered trial retroactively (the DIAG-C / AMENDMENT-003 precedent).

---

## Section 9 — QE infrastructure asks + pre-registered expectations

### 9.1 QE build (no engine core change; opt-in scalar + a2 helper + mn3 builders)
1. **Signal/universe:** reuse `mn3_diag_h.build_universe` (top-40, ≥270c, `pit_topn_universe`
   30/10) and `mn3_diag_h.amihud` VERBATIM — the scored object. NO `$3M` floor on the primary (R2).
2. **Book:** DIAG-H quintile L/S weights (equal-weight 1/k, `long_high=True`) → `mn_exploration_a2.
   apply_beta_neutralization` (BTC-only minimal-L2, degenerate + collapse guards) → per-name cap
   0.10·g → `blind_engine.run_backtest` (weekly rebal=21, 21-phase tranche, 5+2.5bps + funding).
3. **Throttle:** new `mn3_scud_s4.py` (or a `mn_scud` extension) implementing LCDD-z (§2.1): cohort =
   **top** q=0.33 of Amihud (not bottom), dispersion = **P25 downside** (not P75 upside), reusing
   `scud_ramp` + `trailing_h_returns` with IDENTICAL τ/W/φ constants; emit a past-only `(T,)`
   `gross_scalar_series`; wire via the existing engine hook (consumed [k−1]).
4. **Twins:** CS-2× / CS-A / CS-3× as full engine re-runs (GROUND-TRUTH; per-side cost vector for the
   asymmetric CS-A); CS-L as a floored-universe re-run.
5. **Controls:** un-throttled twin (scalar≡1.0); shuffled-signal placebo (≥20 pre-registered seeds);
   reversed-direction book.
6. **Leak battery + asserts:** corrupt-future on LCDD-z and the composed scalar; decision-lag [k−1];
   inert-default byte-identity (throttle off ⇒ engine bit-identical); the §1.2(5) reproducibility
   assert (engine book realized β matches DIAG-H residual-book neutrality); `mn3_guard` called BEFORE
   any metric with `reveal_token=None`; `mn3_datacheck` panel health FIRST.
7. **Report:** headline block (Sharpe honest/2×/CS-A/CS-3×, ann vol, maxDD, turnover, ann return,
   phase distribution, 19/21-style positive count); neutrality block (rolling β_BTC/β_ETH fractions +
   max, bucket β_BTC CRASH/MANIA/CHOP with n+se, G3 max|Σw|/gross); regime block (CRASH/MANIA/CHOP
   means + t); IS-halves (H1/H2 sign); throttle block (coverage, mean scalar, HELPS/NEUTRAL/HURTS
   forensic); controls block (un-throttled floors, placebo Sharpe CI, reversed-direction, leg
   attribution); CS-L retention.

### 9.2 Pre-registered expectations (honest ranges; what would falsify) — informational, NOT gates
| Quantity | Point | Range | Basis / what falsifies |
|---|---|---|---|
| Net Sharpe (honest 1×, throttled) | +0.9 | [+0.4, +1.5] | DIAG-H +17%/yr net2× at 74× turnover, 19/21 positive ⇒ decent Sharpe; engine projection + throttle tax subtract; wide band. < +0.35 ⇒ G-sharpe-floor FAIL |
| Net Sharpe (CS-A asym long 3×) | +0.6 | [+0.2, +1.2] | long-leg 3× is the real cost bite; DIAG-H already survived 2× ⇒ expected > 0. ≤ 0 ⇒ G-coststress FAIL (edge not executable) |
| maxDD (throttled) | −16% | [−10%, −25%] | crash-positive + low turnover ⇒ shallow; throttle may shave the adverse tail. ≥ −25% ⇒ G-maxdd FAIL |
| CRASH-bucket \|β_BTC\| | +0.05 | [−0.05, +0.15] | BTC projection should neutralize; +54% CRASH is expected to be premium, not beta. > 0.15 ⇒ G2-CRASH FAIL (the central falsifier) |
| Throttle disposition | NEUTRAL-to-HELPS | — | crash-positivity tension (§2.2); HURTS ⇒ ship throttle-off, disclosed |
| Un-throttled alpha floors | PASS | — | the alpha is in the sort; a fail ⇒ throttle-is-the-alpha FAIL |
| Shuffled placebo Sharpe | ~0 | CI ∋ 0 | neutrality is a projection property, edge is the signal; reliably > 0 ⇒ plumbing-edge FAIL |
| Turnover | ~80× | [60×, 130×] | DIAG-H 74× + throttle transitions; ≫ 250× ⇒ G-turnover FAIL |

**Modal outcome I expect:** the performance floors PASS (DIAG-H's clean sleeve gate transfers); the
discriminating risks are **(a) G2-CRASH/MANIA** (does the engine weight-projection neutralize as well
as the diagnostic residualization — R1), **(b) G-coststress** (does the thin long leg survive 3×
asymmetric cost), and **(c) the throttle disposition** (crash-positivity tension). These three are the
genuine unknowns; the headline Sharpe level is the least discriminating number (the mechanism is
already IS-validated).

---

*— Quant Researcher (Opus 4.8, Fable-limit deviation disclosed), MN3 track, 2026-07-11.
EXPLORATION-S4 pre-registration. Everything frozen before the run; holdout sealed; `MN3-H` token
unspent; nothing committed. Next: Critic pre-flight, then QE/QR scored run.*
